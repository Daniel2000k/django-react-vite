from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import viewsets 
from .models import Producto, Inventario
from .serializers import ProductoSerializer, InventarioSerializer

from .models import (
    Producto, Inventario,
    Proveedor, OrdenCompra, AlertaInventario,
    Venta, DetalleVenta  # Nuevos modelos agregados
)



# ==================== VISTAS API (REST) ====================

class ProductoViewSet(viewsets.ModelViewSet):
    """API CRUD para Productos"""
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    
class InventarioViewSet(viewsets.ModelViewSet):
    """API CRUD para Movimientos de Inventario"""
    queryset = Inventario.objects.all()
    serializer_class = InventarioSerializer


# ==================== VISTAS BASADAS EN TEMPLATES ====================

@login_required(login_url='login')
def inventario_dashboard(request):
    """Dashboard principal del inventario"""
    productos = Producto.objects.all()
    movimientos = Inventario.objects.all().order_by('-id')
    
    context = {
        'productos': productos,
        'movimientos': movimientos,
        'total_productos': productos.count(),
        'stock_total': sum([p.stock for p in productos])
    }
    return render(request, 'inventario/dashboard.html', context)


@login_required(login_url='login')
def producto_lista(request):
    """Lista de productos con stock"""
    productos = Producto.objects.all()
    return render(request, 'inventario/producto_lista.html', {'productos': productos})


@login_required(login_url='login')
def producto_crear(request):
    """Crear nuevo producto"""
    if request.method == 'POST':
        try:
            codigo = request.POST.get('codigo').strip()
            nombre = request.POST.get('nombre').strip()
            precio_compra = request.POST.get('precio_compra').strip()
            precio_venta = request.POST.get('precio_venta').strip()
            
            # Validaciones
            if not all([codigo, nombre, precio_compra, precio_venta]):
                messages.error(request, 'Por favor completa todos los campos')
                return render(request, 'inventario/producto_form.html')
            
            if Producto.objects.filter(codigo=codigo).exists():
                messages.error(request, 'El código ya existe')
                return render(request, 'inventario/producto_form.html')
            
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
            messages.error(request, 'Códigos y precios deben ser números')
            return render(request, 'inventario/producto_form.html')
    
    return render(request, 'inventario/producto_form.html')


@login_required(login_url='login')
def inventario_movimiento(request):
    """Crear movimiento de inventario (entrada/salida)"""
    if request.method == 'POST':
        try:
            producto_id = request.POST.get('producto_id').strip()
            tipo = request.POST.get('tipo').strip()
            cantidad = request.POST.get('cantidad').strip()
            numero_referencia = request.POST.get('numero_referencia').strip()
            
            # Validaciones
            if not all([producto_id, tipo, cantidad]):
                messages.error(request, 'Por favor completa todos los campos')
                return render(request, 'inventario/movimiento_form.html', {'productos': Producto.objects.all()})
            
            if tipo not in ['ENTRADA', 'SALIDA']:
                messages.error(request, 'Tipo inválido')
                return render(request, 'inventario/movimiento_form.html', {'productos': Producto.objects.all()})
            
            producto = get_object_or_404(Producto, id=int(producto_id))
            cantidad_int = int(cantidad)
            
            # Validar que no quede negativo en salida
            if tipo == 'SALIDA' and (producto.stock - cantidad_int) < 0:
                messages.error(request, f'Stock insuficiente. Stock actual: {producto.stock}')
                return render(request, 'inventario/movimiento_form.html', {'productos': Producto.objects.all()})
            
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
            messages.error(request, 'Error al procesar el movimiento')
            return render(request, 'inventario/movimiento_form.html', {'productos': Producto.objects.all()})
    
    productos = Producto.objects.all()
    return render(request, 'inventario/movimiento_form.html', {'productos': productos})

# ===========================
# PROVEEDORES
# ===========================

@login_required(login_url='login')
def proveedor_lista(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'inventario/proveedor_lista.html', {'proveedores': proveedores})


@login_required(login_url='login')
def proveedor_crear(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        correo = request.POST.get('correo')

        if not all([nombre, telefono, direccion, correo]):
            messages.error(request, "Todos los campos son obligatorios")
            return redirect('proveedor_crear')

        Proveedor.objects.create(
            nombre=nombre,
            telefono=telefono,
            direccion=direccion,
            correo=correo
        )
        messages.success(request, f"Proveedor '{nombre}' creado correctamente")
        return redirect('proveedor_lista')

    return render(request, 'inventario/proveedor_form.html')

# ----------------------
# PROVEEDOR: editar, borrar, detalle (+historial)
# ----------------------

@login_required(login_url='login')
def proveedor_editar(request, proveedor_id):
    prov = get_object_or_404(Proveedor, id=proveedor_id)
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        correo = request.POST.get('correo')

        if not all([nombre, telefono, direccion, correo]):
            messages.error(request, "Todos los campos son obligatorios")
            return redirect('proveedor_editar', proveedor_id=proveedor_id)

        prov.nombre = nombre
        prov.telefono = telefono
        prov.direccion = direccion
        prov.correo = correo
        prov.save()

        messages.success(request, f"Proveedor '{prov.nombre}' actualizado")
        return redirect('proveedor_lista')

    return render(request, 'inventario/proveedor_form.html', {'proveedor': prov, 'editar': True})


@login_required(login_url='login')
def proveedor_eliminar(request, proveedor_id):
    prov = get_object_or_404(Proveedor, id=proveedor_id)
    if request.method == 'POST':
        nombre = prov.nombre
        prov.delete()
        messages.success(request, f"Proveedor '{nombre}' eliminado")
        return redirect('proveedor_lista')
    return render(request, 'inventario/proveedor_confirm_delete.html', {'proveedor': prov})


@login_required(login_url='login')
def proveedor_detalle(request, proveedor_id):
    prov = get_object_or_404(Proveedor, id=proveedor_id)
    # historial de ordenes asociadas
    ordenes = prov.ordenes.all().order_by('-fecha_creacion')
    return render(request, 'inventario/proveedor_detalle.html', {'proveedor': prov, 'ordenes': ordenes})

# ===========================
# ÓRDENES DE COMPRA
# ===========================

@login_required(login_url='login')
def orden_lista(request):
    ordenes = OrdenCompra.objects.all().order_by('-id')
    return render(request, 'inventario/orden_lista.html', {'ordenes': ordenes})


@login_required(login_url='login')
def orden_crear(request):
    proveedores = Proveedor.objects.all()
    productos = Producto.objects.all()

    if request.method == 'POST':
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

        subtotal = cantidad * costo_unitario

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
            f"Orden creada: {cantidad} unidades de {producto.nombre} para el proveedor {proveedor.nombre}"
        )
        return redirect('orden_lista')

    return render(request, 'inventario/orden_form.html', {
        'proveedores': proveedores,
        'productos': productos
    })


@login_required(login_url='login')
def orden_recibir(request, orden_id):
    orden = get_object_or_404(OrdenCompra, id=orden_id)

    if orden.estado == 'RECIBIDA':
        messages.warning(request, "La orden ya fue marcada como recibida")
        return redirect('orden_lista')

    # MÉTODO DEL MODELO: aumenta stock + crea alerta
    orden.recibir()

    messages.success(
        request,
        f"Orden OC-{orden.id} recibida. Stock actualizado correctamente."
    )
    return redirect('orden_lista')

# ----------------------
# ORDEN: detalle, editar (parcial), cancelar
# ----------------------

@login_required(login_url='login')
def orden_detalle(request, orden_id):
    oc = get_object_or_404(OrdenCompra, id=orden_id)
    return render(request, 'inventario/orden_detalle.html', {'orden': oc})


@login_required(login_url='login')
def orden_editar(request, orden_id):
    oc = get_object_or_404(OrdenCompra, id=orden_id)
    if oc.estado == 'RECIBIDA':
        messages.warning(request, "No se puede editar una orden ya recibida")
        return redirect('orden_detalle', orden_id=orden_id)

    proveedores = Proveedor.objects.all()
    productos = Producto.objects.all()

    if request.method == 'POST':
        proveedor_id = request.POST.get('proveedor')
        producto_id = request.POST.get('producto')
        cantidad = request.POST.get('cantidad')
        costo_unitario = request.POST.get('costo_unitario')

        if not all([proveedor_id, producto_id, cantidad, costo_unitario]):
            messages.error(request, "Por favor completa todos los campos")
            return redirect('orden_editar', orden_id=orden_id)

        oc.proveedor = Proveedor.objects.get(id=proveedor_id)
        oc.producto = Producto.objects.get(id=producto_id)
        oc.cantidad = int(cantidad)
        oc.costo_unitario = float(costo_unitario)
        oc.subtotal = oc.cantidad * oc.costo_unitario
        oc.save()

        messages.success(request, f"Orden OC-{oc.id} actualizada")
        return redirect('orden_detalle', orden_id=orden_id)

    return render(request, 'inventario/orden_form.html', {
        'proveedores': proveedores,
        'productos': productos,
        'editar': True,
        'orden': oc
    })


@login_required(login_url='login')
def orden_cancelar(request, orden_id):
    oc = get_object_or_404(OrdenCompra, id=orden_id)
    if oc.estado == 'RECIBIDA':
        messages.warning(request, "No se puede cancelar una orden ya recibida")
        return redirect('orden_lista')

    if request.method == 'POST':
        oc.estado = 'CANCELADA'
        oc.save()
        messages.success(request, f"Orden OC-{oc.id} cancelada")
        return redirect('orden_lista')

    return render(request, 'inventario/orden_confirm_cancel.html', {'orden': oc})

# ===========================
# ALERTAS DEL SISTEMA
# ===========================

@login_required(login_url='login')
def alertas_lista(request):
    alertas = AlertaInventario.objects.all().order_by('-fecha')
    return render(request, 'inventario/alertas.html', {'alertas': alertas})


@login_required(login_url='login')
def alerta_marcar_leida(request, alerta_id):
    alerta = get_object_or_404(AlertaInventario, id=alerta_id)
    alerta.leida = True
    alerta.save()
    return redirect('alertas_lista')

# ===========================
# VENTAS
# ===========================

@login_required(login_url='login')
def venta_lista(request):
    ventas = Venta.objects.all().order_by('-id')
    return render(request, 'inventario/venta_lista.html', {'ventas': ventas})


@login_required(login_url='login')
def venta_crear(request):
    productos = Producto.objects.all()

    if request.method == 'POST':
        items = []
        total = 0

        for key in request.POST:
            if key.startswith("prod_"):
                prod_id = key.split("_")[1]
                valor = request.POST[key]

                # Si el campo está vacío, lo ignoramos
                if valor.strip() == "":
                    continue

                cantidad = int(valor)

                if cantidad <= 0:
                    continue

                producto = Producto.objects.get(id=prod_id)

                # Validación de stock
                if cantidad > producto.stock:
                    messages.error(request, f"Stock insuficiente para {producto.nombre}")
                    return redirect('venta_crear')

                subtotal = producto.precio_venta * cantidad
                items.append((producto, cantidad, subtotal))
                total += subtotal

        if not items:
            messages.error(request, "No seleccionaste productos")
            return redirect('venta_crear')

        # Crear venta
        venta = Venta.objects.create(
            total=total,
            usuario=request.user
        )

        # Guardar detalles y descontar stock
        for producto, cantidad, subtotal in items:
            DetalleVenta.objects.create(
                venta=venta,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio_venta,
                subtotal=subtotal
            )

            # DESCONTAR STOCK
            Inventario.objects.create(
                producto=producto,
                tipo="SALIDA",
                cantidad=cantidad,
                numero_referencia=f"VENTA-{venta.id}"
            )

        messages.success(request, f"Venta #{venta.id} registrada correctamente")
        return redirect('venta_detalle', venta_id=venta.id)

    return render(request, 'inventario/venta_crear.html', {'productos': productos})


@login_required(login_url='login')
def venta_detalle(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    return render(request, 'inventario/venta_detalle.html', {'venta': venta})
