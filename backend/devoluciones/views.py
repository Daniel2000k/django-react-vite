from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseForbidden

from .models import Devolucion
from ventas.models import Venta, DetalleVenta
from inventario.models import Producto
from django.http import JsonResponse
from django.db.models import Sum
from django.contrib.auth.decorators import login_required


@login_required(login_url='login')
@user_passes_test(lambda u: u.rol in ["ADMIN", "CAJERO"], login_url='login')
def devoluciones_list(request):
    """
    Mostrar listado de devoluciones. Desde aquí se puede ir a crear una nueva devolucion.
    ADMIN ve todas, CAJERO ve solo las suyas.
    """
    if request.user.rol == "ADMIN":
        devoluciones = Devolucion.objects.select_related('producto', 'usuario', 'venta').order_by('-fecha')
    else:
        # CAJERO: solo ve devoluciones que él registró
        devoluciones = Devolucion.objects.filter(usuario=request.user).select_related('producto', 'usuario', 'venta').order_by('-fecha')
    
    context = {
        'devoluciones': devoluciones,
    }
    return render(request, 'devoluciones/index.html', context)


@login_required(login_url='login')
@user_passes_test(lambda u: u.rol in ["ADMIN", "CAJERO"], login_url='login')
def venta_detalles_api(request, venta_id):
    """API que devuelve los detalles de una venta junto con la cantidad máxima que puede devolverse."""
    venta = Venta.objects.filter(id=venta_id).first()
    if not venta:
        return JsonResponse({'error': 'Venta no encontrada'}, status=404)

    datos = []
    detalles = venta.detalles.select_related('producto').all()
    for d in detalles:
        total_devueltas = Devolucion.objects.filter(detalle_venta=d).aggregate(total=Sum('cantidad'))['total'] or 0
        max_returnable = max(0, d.cantidad - total_devueltas)
        datos.append({
            'detalle_id': d.id,
            'producto_id': d.producto.id if d.producto else None,
            'producto_nombre': d.producto.nombre if d.producto else d.producto_nombre,
            'cantidad_vendida': d.cantidad,
            'cantidad_devuelta': total_devueltas,
            'max_returnable': max_returnable,
        })

    return JsonResponse({'venta_id': venta.id, 'detalles': datos})


@login_required(login_url='login')
@user_passes_test(lambda u: u.rol in ["ADMIN", "CAJERO"], login_url='login')
def ventas_for_devoluciones(request):
    """Mostrar un listado simple de ventas para elegir desde cuál devolver.
    ADMIN ve todas, CAJERO ve solo sus propias ventas.
    """
    if request.user.rol == "ADMIN":
        ventas = Venta.objects.select_related('usuario').order_by('-id')[:200]
    else:
        # CAJERO: solo ve sus propias ventas
        ventas = Venta.objects.filter(usuario=request.user).select_related('usuario').order_by('-id')[:200]
    
    return render(request, 'devoluciones/ventas_list.html', {'ventas': ventas})


@login_required(login_url='login')
@user_passes_test(lambda u: u.rol in ["ADMIN", "CAJERO"], login_url='login')
def devolver_desde_venta(request, venta_id):
    """Página que muestra el detalle de la venta y permite seleccionar productos a devolver.
    POST procesará las cantidades por detalle y creará las devoluciones.
    CAJERO solo puede devolver sus propias ventas.
    """
    venta = get_object_or_404(Venta, id=venta_id)
    
    # CAJERO solo puede devolver sus propias ventas
    if request.user.rol == "CAJERO" and venta.usuario != request.user:
        return HttpResponseForbidden("No tienes permiso para devolver esta venta.")
    
    detalles = venta.detalles.select_related('producto').all()

    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        created = []
        errors = []

        for detalle in detalles:
            key = f'detalle_{detalle.id}'
            if key not in request.POST:
                continue
            try:
                cantidad = int(request.POST.get(key, 0))
            except Exception:
                cantidad = 0

            if cantidad <= 0:
                continue

            # verificar cantidad maxima
            total_devueltas = Devolucion.objects.filter(detalle_venta=detalle).aggregate(total=Sum('cantidad'))['total'] or 0
            max_returnable = detalle.cantidad - total_devueltas
            if cantidad > max_returnable:
                errors.append(f"No se puede devolver {cantidad} de {detalle.producto_nombre or detalle.producto.nombre}. Máximo: {max_returnable}")
                continue

            devol = Devolucion.objects.create(
                venta=venta,
                detalle_venta=detalle,
                producto=detalle.producto,
                cantidad=cantidad,
                motivo=motivo,
                usuario=request.user
            )
            created.append(devol.id)

        if created:
            messages.success(request, f'Devoluciones registradas: {created}')
        if errors:
            for e in errors:
                messages.error(request, e)

        return redirect('devolver_desde_venta', venta_id=venta.id)

    # calcular max por detalle para mostrar
    detalle_info = []
    for d in detalles:
        total_devueltas = Devolucion.objects.filter(detalle_venta=d).aggregate(total=Sum('cantidad'))['total'] or 0
        detalle_info.append({
            'detalle': d,
            'max_returnable': max(0, d.cantidad - total_devueltas),
            'cantidad_devuelta': total_devueltas,
        })

    context = {
        'venta': venta,
        'detalle_info': detalle_info,
    }
    return render(request, 'devoluciones/devolver_desde_venta.html', context)
