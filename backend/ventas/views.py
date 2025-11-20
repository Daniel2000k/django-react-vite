from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Venta, DetalleVenta
from inventario.models import Producto, Inventario
from rest_framework import viewsets # opcional, si se planea usar viewsets aquí
from decimal import Decimal
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.contrib import messages

# Importación de la función de chequeo de Admin/Cajero (aunque usaremos lambda)
from accounts.views import es_admin, es_cajero # Importar las funciones (aunque se usa lambda)


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

    if user.rol == "ADMIN":
        # ADMIN ve TODAS las ventas ordenadas por ID descendente
        ventas = Venta.objects.all().order_by('-id')
    else:
        # CAJERO ve SOLO sus ventas ordenadas por ID descendente
        ventas = Venta.objects.filter(usuario=user).order_by('-id')

    # Nota: Se utiliza 'venta_lista.html' tal como está en el código original.
    return render(request, 'inventario/venta_lista.html', {'ventas': ventas})


@login_required(login_url='login')
@user_passes_test(lambda u: u.rol in ["ADMIN", "CAJERO"], login_url='login')
def venta_crear(request):
    """Crear nueva venta (Solo ADMIN/CAJERO)."""
    productos = Producto.objects.all()

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
            usuario=request.user
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

            # Movimiento de inventario (SALIDA)
            Inventario.objects.create(
                producto=producto,
                tipo="SALIDA",
                cantidad=cantidad,
                numero_referencia=f"VENTA-{venta.id}-{producto.id}"
            )

        messages.success(request, f"Venta #{venta.id} registrada correctamente")
        return redirect('venta_detalle', venta_id=venta.id)

    return render(request, 'inventario/venta_crear.html', {'productos': productos})


@login_required(login_url='login')
@user_passes_test(lambda u: u.rol in ["ADMIN", "CAJERO"], login_url='login')
def venta_detalle(request, venta_id):
    """Ver detalle de una venta, solo si es de ADMIN o si es su propia venta."""
    venta = get_object_or_404(Venta, id=venta_id)
    
    # Restricción adicional: si no es ADMIN, solo puede ver sus propias ventas
    if request.user.rol != "ADMIN" and venta.usuario != request.user:
          messages.error(request, "No tienes permiso para ver esta venta.")
          return redirect('venta_lista')
          
    return render(request, 'inventario/venta_detalle.html', {'venta': venta})


# ==================== FACTURA PDF ====================

@login_required(login_url='login')
@user_passes_test(lambda u: u.rol in ["ADMIN", "CAJERO"], login_url='login') # Añadir restricción de rol
def venta_factura_pdf(request, venta_id):
    """
    Generar factura de venta en PDF.
    Solo accesible por ADMIN o el CAJERO que realizó la venta.
    """
    venta = get_object_or_404(Venta, id=venta_id)

    # Restricción: Solo permite si es ADMIN o si es su propia venta
    if request.user.rol != "ADMIN" and venta.usuario != request.user:
          messages.error(request, "No tienes permiso para generar la factura de esta venta.")
          # Cambiado a HttpResponseForbidden para una respuesta HTTP más apropiada
          return HttpResponseForbidden("No tienes permiso para generar la factura de esta venta.")


    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="factura_{venta.id}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)

    y = 750
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, f"Factura Venta #{venta.id}")
    y -= 40

    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Fecha: {venta.fecha.strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 20
    p.drawString(50, y, f"Cajero: {venta.usuario.username}")
    y -= 20
    p.drawString(50, y, f"Método de pago: {venta.metodo_pago}")
    y -= 30

    # Detalle de productos
    p.drawString(50, y, "Detalle:")
    y -= 20

    for item in venta.detalles.all():
        p.drawString(60, y, f"{item.producto.nombre} x {item.cantidad} @ ${item.precio_unitario} = ${item.subtotal}")
        y -= 20

    y -= 20

    # Totales (SUBTOTAL - DESCUENTO + IVA)
    p.drawString(50, y, f"Subtotal: ${venta.total}")
    y -= 20

    p.drawString(50, y, f"Descuento: -${venta.descuento_general}")
    y -= 20

    p.drawString(50, y, f"IVA ({venta.iva_porcentaje}%): ${venta.iva_total}")
    y -= 30

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, f"TOTAL A PAGAR: ${venta.total_final}")
    y -= 25

    # Monto recibido y cambio
    if venta.metodo_pago == "EFECTIVO":
        p.setFont("Helvetica", 12)
        p.drawString(50, y, f"Monto recibido: ${venta.monto_recibido}")
        y -= 20
        p.drawString(50, y, f"Cambio: ${venta.cambio}")
    
    p.showPage()
    p.save()

    return response

# ==================== MIS VENTAS (Agregado) ====================

@login_required
def mis_ventas(request):
    """
    Vista simple para mostrar solo las ventas realizadas por el usuario actual.
    (Nota: Esta lógica está cubierta por venta_lista para el rol CAJERO).
    """
    ventas = Venta.objects.filter(usuario=request.user).order_by('-fecha')
    return render(request, 'ventas/mis_ventas.html', {"ventas": ventas})