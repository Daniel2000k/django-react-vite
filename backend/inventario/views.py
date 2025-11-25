from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test # Se añade user_passes_test
from rest_framework import viewsets
from decimal import Decimal
from django.http import JsonResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.db.models import Sum, Count # Importación necesaria para el dashboard

# IMPORTACIONES ADICIONALES
from accounts.views import es_admin # Importa la función de chequeo de Admin
# FIN IMPORTACIONES ADICIONALES

from .models import (
    Producto, Inventario,
    Proveedor, OrdenCompra, AlertaInventario
)
from ventas.models import Venta, DetalleVenta
from .serializers import ProductoSerializer, InventarioSerializer


# ==================== API ====================

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer


class InventarioViewSet(viewsets.ModelViewSet):
    queryset = Inventario.objects.all()
    serializer_class = InventarioSerializer

@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login')
def api_producto_create(request):
    """API simple para crear un Producto mínimo y opcionalmente un movimiento de Inventario.
    Form data accepted: codigo, nombre, precio_compra, precio_venta, cantidad_inicial (opcional)
    Responde JSON con datos del producto o error.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    codigo = request.POST.get('codigo', '').strip()
    nombre = request.POST.get('nombre', '').strip()
    precio_compra = request.POST.get('precio_compra', '').strip()
    precio_venta = request.POST.get('precio_venta', '').strip()
    cantidad_inicial = request.POST.get('cantidad_inicial', '').strip()

    if not codigo or not nombre:
        return JsonResponse({'error': 'codigo y nombre son obligatorios'}, status=400)

    try:
        codigo_int = int(codigo)
    except ValueError:
        return JsonResponse({'error': 'codigo debe ser numérico'}, status=400)

    # Evitar duplicados por codigo
    if Producto.objects.filter(codigo=codigo_int).exists():
        prod = Producto.objects.get(codigo=codigo_int)
        return JsonResponse({'error': 'Codigo ya existe', 'producto_id': prod.id}, status=400)

    try:
        precio_compra_val = Decimal(precio_compra) if precio_compra else Decimal('0')
        precio_venta_val = Decimal(precio_venta) if precio_venta else precio_compra_val
    except Exception:
        return JsonResponse({'error': 'precio inválido'}, status=400)

    prod = Producto.objects.create(
        codigo=codigo_int,
        nombre=nombre,
        precio_compra=precio_compra_val,
        precio_venta=precio_venta_val,
        stock=0,
        activo=True
    )

    # Crear movimiento de inventario si se envía cantidad_inicial
    if cantidad_inicial:
        try:
            qty = int(cantidad_inicial)
            if qty > 0:
                Inventario.objects.create(
                    producto=prod,
                    tipo='ENTRADA',
                    cantidad=qty,
                    numero_referencia=f'CREAR_PROD-{prod.id}'
                )
        except Exception:
            pass

    return JsonResponse({
        'id': prod.id,
        'codigo': prod.codigo,
        'nombre': prod.nombre,
        'precio_compra': str(prod.precio_compra),
        'precio_venta': str(prod.precio_venta),
        'stock': prod.stock
    })


def api_productos_search(request):
    """Buscar productos por q (GET). Devuelve lista JSON de productos activos que coinciden en nombre o codigo.
    SIN decoradores - endpoint público para búsqueda de productos en ventas"""
    q = request.GET.get('q', '').strip()
    productos = Producto.objects.filter(activo=True)
    if q:
        # Buscar por nombre o por codigo (si q numérico)
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


# ==================== DASHBOARD ====================

@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO: Usando nombre de ruta 'login'
@login_required(login_url='login')
def inventario_dashboard(request):
    """Dashboard simple del home - solo datos básicos"""
    
    # ✅ OPTIMIZACIÓN: select_related para usuario, prefetch_related para detalles
    productos = Producto.objects.filter(activo=True)
    movimientos = Inventario.objects.all().order_by('-fecha')[:10]
    
    total_productos = productos.count()
    # Aseguramos que la importación de Sum se haga al inicio
    stock_total = productos.aggregate(total=Sum('stock'))['total'] or 0
    bajo_stock = productos.filter(stock__lte=5).count()

    context = {
        'productos': productos,
        'movimientos': movimientos,
        'total_productos': total_productos,
        'stock_total': stock_total,
        'bajo_stock': bajo_stock,
    }
    return render(request, 'inventario/dashboard.html', context)
    try:
        filtered = [ (n,u) for (n,u) in request.menu_items if ('orden' not in n.lower() and 'alert' not in n.lower()) ]
    except Exception:
        filtered = None
    if filtered is not None:
        context['menu_items'] = filtered
    return render(request, 'inventario/dashboard.html', context)


# ==================== PRODUCTOS ====================

@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') 
def producto_lista(request):
    # ✅ OPTIMIZACIÓN: Cargar solo productos activos sin queries adicionales
    productos = Producto.objects.filter(activo=True).order_by('nombre')  # Solo productos activos
    return render(request, 'inventario/producto_lista.html', {'productos': productos})


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def producto_crear(request):
    if request.method == 'POST':
        try:
            codigo = request.POST.get('codigo').strip()
            nombre = request.POST.get('nombre').strip()
            precio_compra = request.POST.get('precio_compra').strip()
            precio_venta = request.POST.get('precio_venta').strip()

            if not all([codigo, nombre, precio_compra, precio_venta]):
                messages.error(request, 'Por favor completa todos los campos')
                # Retorna el formulario con los datos ingresados para no perderlos (mejora de UX)
                return render(request, 'inventario/producto_form.html', {
                    'codigo': codigo,
                    'nombre': nombre,
                    'precio_compra': precio_compra,
                    'precio_venta': precio_venta,
                })

            if Producto.objects.filter(codigo=codigo).exists():
                messages.error(request, 'El código ya existe')
                return render(request, 'inventario/producto_form.html', {
                    'nombre': nombre,
                    'precio_compra': precio_compra,
                    'precio_venta': precio_venta,
                })

            Producto.objects.create(
                codigo=int(codigo),
                nombre=nombre,
                precio_compra=float(precio_compra),
                precio_venta=float(precio_venta),
                stock=0
            )
            messages.success(request, f'Producto "{nombre}" creado exitosamente')
            return redirect('producto_lista')

        except ValueError:
            messages.error(request, 'Códigos y precios deben ser números válidos.')
            return render(request, 'inventario/producto_form.html')

    return render(request, 'inventario/producto_form.html')
    
# Esta función helper no necesita el decorador si solo es llamada por AJAX y la vista principal está protegida
def verificar_codigo_producto(request): 
    codigo = request.GET.get('codigo', '').strip()
    existe = Producto.objects.filter(codigo=codigo).exists()
    return JsonResponse({'existe': existe})


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login')
def producto_editar(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre').strip()
            precio_compra = request.POST.get('precio_compra').strip()
            precio_venta = request.POST.get('precio_venta').strip()

            if not all([nombre, precio_compra, precio_venta]):
                messages.error(request, 'Por favor completa todos los campos')
                return render(request, 'inventario/producto_form.html', {
                    'producto': producto,
                    'editar': True,
                    'nombre': nombre,
                    'precio_compra': precio_compra,
                    'precio_venta': precio_venta,
                })

            producto.nombre = nombre
            producto.precio_compra = float(precio_compra)
            producto.precio_venta = float(precio_venta)
            producto.save()
            messages.success(request, f'Producto "{nombre}" actualizado exitosamente')
            return redirect('producto_lista')

        except ValueError:
            messages.error(request, 'Los precios deben ser números válidos.')
            return render(request, 'inventario/producto_form.html', {'producto': producto, 'editar': True})

    return render(request, 'inventario/producto_form.html', {'producto': producto, 'editar': True})


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login')
def producto_eliminar(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        nombre = producto.nombre
        # Eliminar físicamente el producto. Las ventas conservarán el nombre por snapshot en DetalleVenta.
        producto.delete()
        messages.success(request, f'Producto "{nombre}" eliminado correctamente')
        return redirect('producto_lista')
    
    return render(request, 'inventario/producto_confirm_delete.html', {'producto': producto})

# ==================== MOVIMIENTOS ====================

@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def inventario_movimiento(request):
    if request.method == 'POST':
        try:
            producto_id = request.POST.get('producto_id').strip()
            tipo = request.POST.get('tipo').strip()
            cantidad = request.POST.get('cantidad').strip()
            numero_referencia = request.POST.get('numero_referencia').strip()

            productos = Producto.objects.all() # Necesario para render en caso de error

            if not all([producto_id, tipo, cantidad]):
                messages.error(request, 'Por favor completa todos los campos')
                return render(request, 'inventario/movimiento_form.html', {'productos': productos})

            if tipo not in ['ENTRADA', 'SALIDA']:
                messages.error(request, 'Tipo inválido')
                return render(request, 'inventario/movimiento_form.html', {'productos': productos})

            producto = get_object_or_404(Producto, id=int(producto_id))
            cantidad_int = int(cantidad)

            if tipo == 'SALIDA' and (producto.stock - cantidad_int) < 0:
                messages.error(request, f'Stock insuficiente. Stock actual: {producto.stock}')
                return render(request, 'inventario/movimiento_form.html', {'productos': productos})

            # Crear movimiento
            Inventario.objects.create(
                producto=producto,
                tipo=tipo,
                cantidad=cantidad_int,
                numero_referencia=numero_referencia if numero_referencia else None
            )

            messages.success(request, f'{tipo}: {cantidad} unidades de {producto.nombre}')
            return redirect('inventario_dashboard')

        except (ValueError, Producto.DoesNotExist):
            messages.error(request, 'Error al procesar el movimiento. Asegúrate de que los valores sean correctos.')
            return render(request, 'inventario/movimiento_form.html', {'productos': Producto.objects.all()})

    productos = Producto.objects.all()
    return render(request, 'inventario/movimiento_form.html', {'productos': productos})


# ==================== PROVEEDORES ====================

@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def proveedor_lista(request):
    # ✅ OPTIMIZACIÓN: Cargar proveedores sin queries adicionales
    proveedores = Proveedor.objects.all().order_by('nombre')
    return render(request, 'inventario/proveedor_lista.html', {'proveedores': proveedores})


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def proveedor_crear(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        direccion = request.POST.get('direccion', '').strip()
        correo = request.POST.get('correo', '').strip().lower()

        context = {
            'nombre': nombre,
            'telefono': telefono,
            'direccion': direccion,
            'correo': correo
        }
        
        if not all([nombre, telefono, direccion, correo]):
            messages.error(request, "Todos los campos son obligatorios")
            return render(request, 'inventario/proveedor_form.html', context)

        # Validar correo único (case-insensitive)
        if Proveedor.objects.filter(correo__iexact=correo).exists():
            messages.error(request, f"El correo '{correo}' ya está registrado con otro proveedor")
            return render(request, 'inventario/proveedor_form.html', context)

        try:
            Proveedor.objects.create(
                nombre=nombre,
                telefono=telefono,
                direccion=direccion,
                correo=correo
            )
            messages.success(request, f"Proveedor '{nombre}' creado correctamente")
            return redirect('proveedor_lista')
        except Exception as e:
            messages.error(request, f"Error al crear el proveedor: {str(e)}")
            return render(request, 'inventario/proveedor_form.html', context)

    return render(request, 'inventario/proveedor_form.html')
    
# Esta función helper no necesita el decorador si solo es llamada por AJAX y la vista principal está protegida
def verificar_correo_proveedor(request):
    correo = request.GET.get('correo', '').strip().lower()
    existe = Proveedor.objects.filter(correo__iexact=correo).exists()
    return JsonResponse({'existe': existe})

@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def proveedor_editar(request, proveedor_id):
    prov = get_object_or_404(Proveedor, id=proveedor_id)
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        direccion = request.POST.get('direccion', '').strip()
        correo = request.POST.get('correo', '').strip().lower()

        context = {'proveedor': prov, 'editar': True}
        
        if not all([nombre, telefono, direccion, correo]):
            messages.error(request, "Todos los campos son obligatorios")
            return render(request, 'inventario/proveedor_form.html', context)

        # Validar correo único (pero permite el mismo correo del proveedor actual)
        if correo != prov.correo.lower():
            if Proveedor.objects.filter(correo__iexact=correo).exists():
                messages.error(request, f"El correo '{correo}' ya está registrado con otro proveedor")
                return render(request, 'inventario/proveedor_form.html', context)

        try:
            prov.nombre = nombre
            prov.telefono = telefono
            prov.direccion = direccion
            prov.correo = correo
            prov.save()
            messages.success(request, f"Proveedor '{prov.nombre}' actualizado correctamente")
            return redirect('proveedor_lista')
        except Exception as e:
            messages.error(request, f"Error al actualizar el proveedor: {str(e)}")
            return render(request, 'inventario/proveedor_form.html', context)

    return render(request, 'inventario/proveedor_form.html', {'proveedor': prov, 'editar': True})


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def proveedor_eliminar(request, proveedor_id):
    prov = get_object_or_404(Proveedor, id=proveedor_id)
    if request.method == 'POST':
        nombre = prov.nombre
        prov.delete()
        messages.success(request, f"Proveedor '{nombre}' eliminado")
        return redirect('proveedor_lista')
    return render(request, 'inventario/proveedor_confirm_delete.html', {'proveedor': prov})


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def proveedor_detalle(request, proveedor_id):
    prov = get_object_or_404(Proveedor, id=proveedor_id)
    ordenes = prov.ordenes.all().order_by('-fecha_creacion')
    return render(request, 'inventario/proveedor_detalle.html', {'proveedor': prov, 'ordenes': ordenes})


# ==================== ÓRDENES ====================

@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def orden_lista(request):
    # Archived: moved to backend/archived/20251123_orders_alerts/views_archived.py
    # Render a minimal notice template so routes remain available but inform users.
    return render(request, 'inventario/orden_archived_notice.html')


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def orden_crear(request):
    # Archived: moved implementation to archived views file.
    return render(request, 'inventario/orden_archived_notice.html')


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def orden_recibir(request, orden_id):
    # Archived: moved to archived views file.
    return render(request, 'inventario/orden_archived_notice.html')


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def orden_detalle(request, orden_id):
    # Archived: moved to archived views file.
    return render(request, 'inventario/orden_archived_notice.html')


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def orden_editar(request, orden_id):
    # Archived: moved to archived views file.
    return render(request, 'inventario/orden_archived_notice.html')


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def orden_cancelar(request, orden_id):
    # Archived: moved to archived views file.
    return render(request, 'inventario/orden_archived_notice.html')


# ==================== ALERTAS ====================

@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def alertas_lista(request):
    # Archived: moved to backend/archived/20251123_orders_alerts/views_archived.py
    return render(request, 'inventario/alertas_archived_notice.html')


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def alerta_marcar_leida(request, alerta_id):
    # Archived: moved to archived views file.
    return render(request, 'inventario/alertas_archived_notice.html')