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


# ==================== DASHBOARD ====================

@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO: Usando nombre de ruta 'login'
def inventario_dashboard(request):
    """Dashboard simple del home - solo datos básicos"""
    
    productos = Producto.objects.filter(activo=True)  # Solo productos activos
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
    # Filtrar elementos del menú para el dashboard: ocultar Órdenes y Alertas
    try:
        filtered = [ (n,u) for (n,u) in request.menu_items if ('orden' not in n.lower() and 'alert' not in n.lower()) ]
    except Exception:
        filtered = None
    if filtered is not None:
        context['menu_items'] = filtered
    return render(request, 'inventario/dashboard.html', context)


# ==================== PRODUCTOS ====================

@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def producto_lista(request):
    productos = Producto.objects.filter(activo=True)  # Solo productos activos
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
        # En lugar de eliminar, desactivar
        producto.activo = False
        producto.save()
        messages.success(request, f'Producto "{nombre}" desactivado exitosamente')
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
    proveedores = Proveedor.objects.all()
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
    ordenes = OrdenCompra.objects.all().order_by('-id')
    return render(request, 'inventario/orden_lista.html', {'ordenes': ordenes})


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def orden_crear(request):
    proveedores = Proveedor.objects.all()
    productos = Producto.objects.all()

    if request.method == 'POST':
        try:
            proveedor_id = request.POST.get('proveedor')
            producto_id = request.POST.get('producto')
            cantidad = request.POST.get('cantidad')
            costo_unitario = request.POST.get('costo_unitario')

            if not all([proveedor_id, producto_id, cantidad, costo_unitario]):
                messages.error(request, "Por favor completa todos los campos")
                return redirect('orden_crear')

            proveedor = Proveedor.objects.get(id=proveedor_id)
            producto = Producto.objects.get(id=producto_id)
            cantidad = int(cantidad)
            costo_unitario = float(costo_unitario)

            if cantidad <= 0 or costo_unitario <= 0:
                 messages.error(request, "La cantidad y el costo deben ser mayores a cero.")
                 return redirect('orden_crear')

            subtotal = Decimal(str(cantidad)) * Decimal(str(costo_unitario))

            OrdenCompra.objects.create(
                proveedor=proveedor,
                producto=producto,
                cantidad=cantidad,
                costo_unitario=costo_unitario,
                subtotal=subtotal,
                estado='PENDIENTE'
            )

            messages.success(
                request,
                f"Orden creada: {cantidad} unidades de {producto.nombre} para {proveedor.nombre}"
            )
            return redirect('orden_lista')
        
        except (ValueError, Proveedor.DoesNotExist, Producto.DoesNotExist):
            messages.error(request, "Error al procesar la orden. Verifique los datos.")
            return redirect('orden_crear')

    return render(request, 'inventario/orden_form.html', {
        'proveedores': proveedores,
        'productos': productos
    })


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def orden_recibir(request, orden_id):
    orden = get_object_or_404(OrdenCompra, id=orden_id)

    if orden.estado == 'RECIBIDA':
        messages.warning(request, "La orden ya fue marcada como recibida")
        return redirect('orden_lista')
    
    # Se añade un chequeo POST por seguridad, aunque el modelo maneja la lógica
    if request.method == 'POST':
        orden.recibir()  # método del modelo (asumiendo que actualiza stock y estado)
        messages.success(request, f"Orden OC-{orden.id} recibida. Stock actualizado.")
        return redirect('orden_lista')

    # Si se accede por GET, se podría redirigir al detalle o lista, o mostrar una confirmación
    return redirect('orden_lista') 


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def orden_detalle(request, orden_id):
    oc = get_object_or_404(OrdenCompra, id=orden_id)
    return render(request, 'inventario/orden_detalle.html', {'orden': oc})


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def orden_editar(request, orden_id):
    oc = get_object_or_404(OrdenCompra, id=orden_id)

    if oc.estado == 'RECIBIDA':
        messages.warning(request, "No se puede editar una orden recibida")
        return redirect('orden_detalle', orden_id=orden_id)

    proveedores = Proveedor.objects.all()
    productos = Producto.objects.all()

    if request.method == 'POST':
        try:
            proveedor_id = request.POST.get('proveedor')
            producto_id = request.POST.get('producto')
            cantidad = request.POST.get('cantidad')
            costo_unitario = request.POST.get('costo_unitario')

            if not all([proveedor_id, producto_id, cantidad, costo_unitario]):
                messages.error(request, "Todos los campos son obligatorios")
                return redirect('orden_editar', orden_id=orden_id)

            oc.proveedor = Proveedor.objects.get(id=proveedor_id)
            oc.producto = Producto.objects.get(id=producto_id)
            oc.cantidad = int(cantidad)
            oc.costo_unitario = float(costo_unitario)
            oc.subtotal = Decimal(str(oc.cantidad)) * Decimal(str(oc.costo_unitario))
            oc.save()

            messages.success(request, f"Orden OC-{oc.id} actualizada")
            return redirect('orden_detalle', orden_id=orden_id)
            
        except (ValueError, Proveedor.DoesNotExist, Producto.DoesNotExist):
            messages.error(request, "Error al actualizar la orden. Verifique los datos.")
            return redirect('orden_editar', orden_id=orden_id)


    return render(request, 'inventario/orden_form.html', {
        'proveedores': proveedores,
        'productos': productos,
        'editar': True,
        'orden': oc
    })


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def orden_cancelar(request, orden_id):
    oc = get_object_or_404(OrdenCompra, id=orden_id)

    if oc.estado == 'RECIBIDA':
        messages.warning(request, "No se puede cancelar una orden recibida")
        return redirect('orden_lista')

    if request.method == 'POST':
        oc.estado = 'CANCELADA'
        oc.save()
        messages.success(request, f"Orden OC-{oc.id} cancelada")
        return redirect('orden_lista')

    return render(request, 'inventario/orden_confirm_cancel.html', {'orden': oc})


# ==================== ALERTAS ====================

@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def alertas_lista(request):
    alertas = AlertaInventario.objects.all().order_by('-fecha')
    return render(request, 'inventario/alertas.html', {'alertas': alertas})


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO
def alerta_marcar_leida(request, alerta_id):
    alerta = get_object_or_404(AlertaInventario, id=alerta_id)
    
    # Se añade un chequeo POST simple
    if request.method == 'POST':
        alerta.leida = True
        alerta.save()
        return redirect('alertas_lista')
    
    # Opcional: si es GET, se podría redirigir directamente o forzar el POST en el template.
    return redirect('alertas_lista')