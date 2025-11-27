from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Venta, DetalleVenta
from inventario.models import Producto, Inventario
from django.http import JsonResponse  # opcional, si se planea usar viewsets aquí
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
from decimal import Decimal
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.contrib import messages
from django.core.mail import EmailMessage
from django.conf import settings
from io import BytesIO

# Importación de la función de chequeo de Admin/Cajero (aunque usaremos lambda)
from accounts.views import es_admin, es_cajero  # Importar las funciones (aunque se usa lambda)


# ==================== FUNCIÓN AUXILIAR: GENERAR Y ENVIAR FACTURA ====================

def generar_pdf_factura(venta):
    """Genera el PDF de la factura en memoria y lo retorna"""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    y = 750
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, f"Factura Venta #{venta.id}")
    y -= 40

    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Fecha: {venta.fecha.strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 20
    p.drawString(50, y, f"Cajero: {venta.usuario.email}")
    y -= 20
    p.drawString(50, y, f"Método de pago: {venta.metodo_pago}")
    y -= 20
    p.drawString(50, y, f"Cliente: {venta.email_cliente or 'No registrado'}")
    y -= 30

    p.drawString(50, y, "Detalle:")
    y -= 20

    for item in venta.detalles.all():
        nombre_producto = item.producto.nombre if item.producto else item.producto_nombre
        p.drawString(60, y, f"{nombre_producto} x {item.cantidad} = ${item.subtotal}")
        y -= 20

    y -= 20
    p.drawString(50, y, f"Subtotal: ${venta.total}")
    y -= 20
    p.drawString(50, y, f"Descuento: -${venta.descuento_general}")
    y -= 20
    p.drawString(50, y, f"IVA ({venta.iva_porcentaje}%): ${venta.iva_total}")
    y -= 30

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, f"TOTAL FINAL: ${venta.total_final}")
    y -= 25

    p.showPage()
    p.save()

    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data


def enviar_factura_email(venta):
    """Envía la factura por email al cliente"""
    try:
        # Determinar email destino
        email_destino = venta.email_cliente if venta.email_cliente else venta.usuario.email
        
        if not email_destino:
            print(f"⚠️  No hay email de destino para la venta #{venta.id}")
            return False
        
        # Generar PDF
        pdf_data = generar_pdf_factura(venta)
        
        # Crear email
        asunto = f"📄 Factura de Venta #{venta.id} - Stock Master"
        
        cuerpo = f"""
Estimado cliente,

Le agradecemos su compra. Adjuntamos la factura de su transacción.

📋 DETALLES DE LA VENTA:
- ID de Venta: {venta.id}
- Fecha: {venta.fecha.strftime('%d/%m/%Y %H:%M:%S')}
- Subtotal: ${venta.total:.2f}
- Descuento: -${venta.descuento_general:.2f}
- IVA (19%): ${venta.iva_total:.2f}
- 💰 TOTAL A PAGAR: ${venta.total_final:.2f}
- Método de pago: {venta.metodo_pago}

¡Gracias por su compra!

Saludos,
Stock Master
        """
        
        email = EmailMessage(
            subject=asunto,
            body=cuerpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email_destino],
        )
        
        # Adjuntar PDF
        email.attach(
            f"Factura_Venta_{venta.id}.pdf",
            pdf_data,
            "application/pdf"
        )
        
        # Enviar
        resultado = email.send()
        
        if resultado:
            print(f"✅ Factura enviada exitosamente a {email_destino}")
            return True
        else:
            print(f"⚠️  Email no se envió (send() retornó 0) a {email_destino}")
            return False
            
    except Exception as e:
        print(f"❌ Error enviando factura a {email_destino}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ==================== VENTAS ====================

@login_required(login_url='login')
@user_passes_test(lambda u: u.rol in ["ADMIN", "CAJERO"], login_url='login')
def venta_lista(request):
    """
    Mostrar listado de ventas.
    ADMIN ve TODAS las ventas.
    CAJERO ve SOLO sus ventas (actúa como "Mis Ventas").
    """
    user = request.user

    # ✅ OPTIMIZACIÓN: select_related para usuario reduce N+1 queries
    if user.rol == "ADMIN":
        ventas = Venta.objects.select_related('usuario').order_by('-id')
    else:
        ventas = Venta.objects.filter(usuario=user).select_related('usuario').order_by('-id')

    return render(request, 'inventario/venta_lista.html', {'ventas': ventas})


@login_required(login_url='login')
@user_passes_test(lambda u: u.rol in ["ADMIN", "CAJERO"], login_url='login')
def venta_crear(request):
    """Crear nueva venta (Solo ADMIN/CAJERO)."""

    if request.method == 'POST':
        items = []
        total = Decimal("0")

        # Detectar productos dinámicamente
        for key in request.POST:
            if key.startswith("prod_"):
                prod_id = key.split("_")[1]
                valor = request.POST[key]

                if valor.strip() == "":
                    continue

                try:
                    cantidad = int(valor)
                except ValueError:
                    messages.error(request, "La cantidad debe ser un número entero válido.")
                    return redirect('venta_crear')

                if cantidad <= 0:
                    continue

                try:
                    producto = Producto.objects.get(id=prod_id)
                except Producto.DoesNotExist:
                    messages.error(request, "Producto no encontrado.")
                    return redirect('venta_crear')

                if cantidad > producto.stock:
                    messages.error(request, f"Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}")
                    return redirect('venta_crear')

                subtotal = Decimal(str(producto.precio_venta)) * cantidad
                items.append((producto, cantidad, subtotal))
                total += subtotal

        if not items:
            messages.error(request, "No seleccionaste productos")
            return redirect('venta_crear')

        # Descuento general
        descuento_str = request.POST.get("descuento_general", "").strip()
        try:
            descuento = Decimal(descuento_str if descuento_str else "0")
        except:
            messages.error(request, "El descuento no es un valor válido.")
            return redirect('venta_crear')

        total_con_descuento = total - descuento

        if total_con_descuento < 0:
            messages.error(request, "El descuento no puede superar el total.")
            return redirect('venta_crear')

        # IVA
        iva_porcentaje = Decimal("19")
        iva_total = total_con_descuento * iva_porcentaje / 100

        # Total final
        total_final = total_con_descuento + iva_total

        # Método de pago
        metodo_pago = request.POST.get("metodo_pago")
        monto_str = request.POST.get("monto_recibido", "").strip()
        try:
            monto_recibido = Decimal(monto_str if monto_str else "0")
        except:
            messages.error(request, "El monto recibido no es un valor válido.")
            return redirect('venta_crear')

        if metodo_pago == "EFECTIVO" and monto_recibido < total_final:
            messages.error(request, "El monto recibido es menor al total final.")
            return redirect('venta_crear')

        cambio = (monto_recibido - total_final) if metodo_pago == "EFECTIVO" else Decimal("0")

        # Capturar correo del cliente
        email_cliente = request.POST.get("email_cliente")

        # Crear venta
        venta = Venta.objects.create(
            total=total,
            descuento_general=descuento,
            iva_porcentaje=iva_porcentaje,
            iva_total=iva_total,
            total_final=total_final,
            metodo_pago=metodo_pago,
            monto_recibido=monto_recibido,
            cambio=cambio,
            usuario=request.user,
            email_cliente=email_cliente  # ⬅️ nuevo
        )

        # Guardar detalles + descontar stock
        for producto, cantidad, subtotal in items:
            DetalleVenta.objects.create(
                venta=venta,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio_venta,
                subtotal=subtotal
            )

            Inventario.objects.create(
                producto=producto,
                tipo="SALIDA",
                cantidad=cantidad,
                numero_referencia=f"VENTA-{venta.id}-{producto.id}"
            )

        messages.success(request, f"Venta #{venta.id} registrada correctamente")
        
        # ✅ ENVIAR EMAIL INMEDIATAMENTE DESPUÉS DE CREAR LA VENTA
        enviar_factura_email(venta)
        
        return redirect('venta_detalle', venta_id=venta.id)

    # GET: Mostrar formulario vacío (sin productos estáticos)
    return render(request, 'inventario/venta_crear.html')


@login_required(login_url='login')
@user_passes_test(lambda u: u.rol in ["ADMIN", "CAJERO"], login_url='login')
def venta_detalle(request, venta_id):
    """Ver detalle de una venta, solo si es de ADMIN o si es su propia venta."""
    # ✅ OPTIMIZACIÓN: prefetch_related para detalles y productos evita N+1 queries
    from django.db.models import Prefetch
    venta = get_object_or_404(
        Venta.objects.select_related('usuario').prefetch_related(
            Prefetch('detalles__producto')
        ),
        id=venta_id
    )
    
    if request.user.rol != "ADMIN" and venta.usuario != request.user:
        messages.error(request, "No tienes permiso para ver esta venta.")
        return redirect('venta_lista')
          
    return render(request, 'inventario/venta_detalle.html', {'venta': venta})


# ==================== FACTURA PDF ====================

@login_required(login_url='login')
@user_passes_test(lambda u: u.rol in ["ADMIN", "CAJERO"], login_url='login')
def venta_factura_pdf(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)

    if request.user.rol != "ADMIN" and venta.usuario != request.user:
        return HttpResponseForbidden("No tienes permiso para ver esta factura.")

    pdf_data = generar_pdf_factura(venta)

    response = HttpResponse(pdf_data, content_type="application/pdf")
    response['Content-Disposition'] = f'inline; filename="factura_{venta.id}.pdf"'
    return response


# ==================== MIS VENTAS ====================

@login_required
def mis_ventas(request):
    ventas = Venta.objects.filter(usuario=request.user).order_by('-fecha')
    return render(request, 'ventas/mis_ventas.html', {"ventas": ventas})



#mimimiim
@login_required(login_url='login')
@user_passes_test(lambda u: u.rol in ["ADMIN", "CAJERO"], login_url='login')
@require_GET
def productos_search_json(request):
    """
    GET /ventas/api/productos-search/?q=...
    Devuelve JSON con lista de productos activos que coinciden por nombre o código.
    Limita a 30 resultados.
    """
    q = request.GET.get('q', '').strip()
    productos = Producto.objects.filter(activo=True)

    if q:
        # si q es numérico buscar por código también
        if q.isdigit():
            productos = productos.filter(codigo__icontains=q) | productos.filter(nombre__icontains=q)
        else:
            productos = productos.filter(nombre__icontains=q)

    productos = productos.order_by('nombre')[:30]

    data = [
        {
            'id': p.id,
            'nombre': p.nombre,
            'codigo': p.codigo,
            'precio_venta': float(p.precio_venta),
            'stock': p.stock,
        }
        for p in productos
    ]
    return JsonResponse(data, safe=False)


@login_required(login_url='login')
@user_passes_test(lambda u: u.rol in ["ADMIN", "CAJERO"], login_url='login')
@require_GET
def producto_json(request, producto_id):
    """
    GET /ventas/api/producto/<id>/
    Devuelve JSON con detalle de un producto (para cuando el frontend
    quiera solicitar datos completos de un id concreto).
    """
    try:
        p = Producto.objects.get(id=producto_id, activo=True)
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

    data = {
        'id': p.id,
        'nombre': p.nombre,
        'codigo': p.codigo,
        'precio_venta': float(p.precio_venta),
        'precio_compra': float(p.precio_compra),
        'stock': p.stock,
        'descripcion': getattr(p, 'descripcion', '')  # si existe
    }
    return JsonResponse(data)