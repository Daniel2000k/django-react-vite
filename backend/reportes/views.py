from django.shortcuts import render
from django.db.models import Sum, Count, F, DecimalField
from django.db.models.functions import TruncDay, Coalesce
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test # Se añade user_passes_test
from datetime import date, timedelta
from decimal import Decimal
import json
import csv

# Importación de la función de chequeo de Admin
from accounts.views import es_admin 

from ventas.models import Venta, DetalleVenta
from inventario.models import Producto, Inventario


# ==================== DASHBOARD & GRÁFICAS ====================

@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO: Usando nombre de ruta 'login'
def dashboard(request):
    """Dashboard principal con KPIs y gráficas"""
    hoy = date.today()

    # Ventas últimos 7 días (por fecha)
    inicio_7 = hoy - timedelta(days=6)
    ventas_7_qs = (
        Venta.objects
        .filter(fecha__date__gte=inicio_7)
        .annotate(dia=TruncDay('fecha'))
        .values('dia')
        .annotate(
            total=Coalesce(Sum('total_final', output_field=DecimalField()), Decimal(0)),
            transacciones=Count('id')
        )
        .order_by('dia')
    )

    dias = [v['dia'].strftime('%Y-%m-%d') for v in ventas_7_qs]
    totales_7 = [float(v['total']) for v in ventas_7_qs]

    # Movimientos (Entradas y Salidas) últimos 7 días
    try:
        mov_qs = (
            Inventario.objects
            .filter(fecha__date__gte=inicio_7)
            .annotate(dia=TruncDay('fecha'))
            .values('dia', 'tipo')
            .annotate(total_cant=Coalesce(Sum('cantidad'), 0, output_field=DecimalField()))
            .order_by('dia')
        )

        # Construir diccionarios por día
        dias_mov = sorted(list({m['dia'].strftime('%Y-%m-%d') for m in mov_qs}))
        entradas_map = {d: 0 for d in dias_mov}
        salidas_map = {d: 0 for d in dias_mov}
        for m in mov_qs:
            d = m['dia'].strftime('%Y-%m-%d')
            if m['tipo'] == 'ENTRADA':
                entradas_map[d] += int(m['total_cant'])
            else:
                salidas_map[d] += int(m['total_cant'])

        # Asegurar consistencia con días de ventas
        if len(dias) == 7:
            dias_mov_final = dias
        else:
            dias_mov_final = [(inicio_7 + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]

        entradas = [entradas_map.get(d, 0) for d in dias_mov_final]
        salidas = [salidas_map.get(d, 0) for d in dias_mov_final]

    except Exception as e:
        dias_mov_final = dias or [(inicio_7 + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
        entradas = [0 for _ in dias_mov_final]
        salidas = [0 for _ in dias_mov_final]

    # Top productos últimos 30 días
    inicio_30 = hoy - timedelta(days=30)
    top_qs = (
        DetalleVenta.objects
        .filter(venta__fecha__date__gte=inicio_30)
        .values(prod_name=F('producto__nombre'))
        .annotate(cantidad_vendida=Coalesce(Sum('cantidad'), 0, output_field=DecimalField()))
        .order_by('-cantidad_vendida')[:10]
    )

    nombres_mas_vendidos = [t['prod_name'] for t in top_qs]
    cantidades_mas_vendidas = [int(t['cantidad_vendida']) for t in top_qs]

    # Insights simples
    producto_top = Producto.objects.order_by('-stock').first()
    producto_mas_vendido = top_qs[0]['prod_name'] if top_qs else 'N/A'
    bajo_stock_count = Producto.objects.filter(stock__lte=5).count()
    ventas_hoy = Venta.objects.filter(fecha__date=hoy).aggregate(
        total=Coalesce(Sum('total_final', output_field=DecimalField()), Decimal(0))
    )['total'] or Decimal(0)

    # KPIs
    total_productos = Producto.objects.count()
    stock_total = Producto.objects.aggregate(
        total_stock=Coalesce(Sum('stock'), 0)
    )['total_stock'] or 0
    movimientos = Inventario.objects.all().order_by('-fecha')[:50]

    context = {
        'total_productos': total_productos,
        'stock_total': stock_total,
        'movimientos': movimientos,
        'producto_top': producto_top,
        'producto_mas_vendido': producto_mas_vendido,
        'bajo_stock': bajo_stock_count,
        'ventas_hoy': float(ventas_hoy),
        'nombres_mas_vendidos_json': json.dumps(nombres_mas_vendidos),
        'cantidades_mas_vendidas_json': json.dumps(cantidades_mas_vendidas),
        'dias_json': json.dumps(dias),
        'entradas_json': json.dumps(entradas),
        'salidas_json': json.dumps(salidas),
        'variacion_productos': 0,
    }

    return render(request, 'reportes/dashboard.html', context)


# ==================== REPORTES ESPECÍFICOS ====================

@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO: Usando nombre de ruta 'login'
def ventas_por_periodo(request):
    """Reporte de ventas por período (fecha inicial y final)"""
    fecha_inicio = request.GET.get('fecha_inicio', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
    fecha_fin = request.GET.get('fecha_fin', date.today().strftime('%Y-%m-%d'))

    try:
        fecha_inicio = date.fromisoformat(fecha_inicio)
        fecha_fin = date.fromisoformat(fecha_fin)
    except:
        fecha_inicio = date.today() - timedelta(days=30)
        fecha_fin = date.today()

    # Obtener todas las ventas en el período
    ventas_raw = (
        Venta.objects
        .filter(fecha__date__gte=fecha_inicio, fecha__date__lte=fecha_fin)
        .order_by('fecha')
    )

    # Procesar datos manualmente para agrupar por día
    ventas_dict = {}
    for venta in ventas_raw:
        dia = venta.fecha.date()
        if dia not in ventas_dict:
            ventas_dict[dia] = {
                'dia': dia,
                'total_dia': Decimal(0),
                'num_transacciones': 0,
                'iva_total': Decimal(0),
                'descuentos': Decimal(0)
            }
        ventas_dict[dia]['total_dia'] += venta.total_final or Decimal(0)
        ventas_dict[dia]['num_transacciones'] += 1
        ventas_dict[dia]['iva_total'] += venta.iva_total or Decimal(0)
        ventas_dict[dia]['descuentos'] += venta.descuento_general or Decimal(0)

    ventas = list(ventas_dict.values())

    total_ventas = sum(v['total_dia'] for v in ventas)
    total_transacciones = sum(v['num_transacciones'] for v in ventas)
    total_iva = sum(v['iva_total'] for v in ventas)
    total_descuentos = sum(v['descuentos'] for v in ventas)

    context = {
        'ventas': ventas,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'total_ventas': total_ventas,
        'total_transacciones': total_transacciones,
        'total_iva': total_iva,
        'total_descuentos': total_descuentos,
        'promedio_venta': total_ventas / total_transacciones if total_transacciones > 0 else 0,
    }

    return render(request, 'reportes/ventas_periodo.html', context)


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO: Usando nombre de ruta 'login'
def top_productos(request):
    """Reporte de top 20 productos más vendidos"""
    dias = request.GET.get('dias', 30)
    try:
        dias = int(dias)
    except:
        dias = 30

    fecha_inicio = date.today() - timedelta(days=dias)

    top = (
        DetalleVenta.objects
        .filter(venta__fecha__date__gte=fecha_inicio)
        .values('producto__id', 'producto__nombre')
        .annotate(
            cantidad_vendida=Coalesce(Sum('cantidad'), 0, output_field=DecimalField()),
            total_generado=Coalesce(Sum('subtotal', output_field=DecimalField()), Decimal(0)),
            num_transacciones=Count('venta', distinct=True)
        )
        .order_by('-cantidad_vendida')[:20]
    )

    context = {
        'top': top,
        'dias': dias,
        'fecha_inicio': fecha_inicio,
    }

    return render(request, 'reportes/top_productos.html', context)


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO: Usando nombre de ruta 'login'
def productos_bajo_stock(request):
    """Reporte de productos con bajo stock"""
    threshold = request.GET.get('threshold', 5)
    try:
        threshold = int(threshold)
    except:
        threshold = 5

    productos = (
        Producto.objects
        .filter(stock__lte=threshold)
        .values('id', 'codigo', 'nombre', 'stock', 'precio_venta')
        .order_by('stock')
    )

    context = {
        'productos': productos,
        'threshold': threshold,
        'total': len(productos),
    }

    return render(request, 'reportes/bajo_stock.html', context)


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO: Usando nombre de ruta 'login'
def ventas_por_cajero(request):
    """Reporte de ventas por usuario/cajero"""
    fecha_inicio = request.GET.get('fecha_inicio', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
    fecha_fin = request.GET.get('fecha_fin', date.today().strftime('%Y-%m-%d'))

    try:
        fecha_inicio = date.fromisoformat(fecha_inicio)
        fecha_fin = date.fromisoformat(fecha_fin)
    except:
        fecha_inicio = date.today() - timedelta(days=30)
        fecha_fin = date.today()

    ventas_por_usuario = (
        Venta.objects
        .filter(fecha__date__gte=fecha_inicio, fecha__date__lte=fecha_fin)
        .values(usuario_id=F('usuario__id'), usuario_nombre=F('usuario__username'))
        .annotate(
            total_vendido=Coalesce(Sum('total_final', output_field=DecimalField()), Decimal(0)),
            num_transacciones=Count('id'),
            ticket_promedio=Coalesce(Sum('total_final', output_field=DecimalField()), Decimal(0)) / Count('id')
        )
        .order_by('-total_vendido')
    )

    context = {
        'ventas_por_usuario': ventas_por_usuario,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'total_general': sum(v['total_vendido'] for v in ventas_por_usuario),
    }

    return render(request, 'reportes/ventas_por_cajero.html', context)


# ==================== EXPORTACIÓN ====================

@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login') # CORREGIDO: Usando nombre de ruta 'login'
def export_ventas_csv(request):
    """Exportar ventas a CSV"""
    fecha_inicio = request.GET.get('fecha_inicio', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
    fecha_fin = request.GET.get('fecha_fin', date.today().strftime('%Y-%m-%d'))

    try:
        fecha_inicio = date.fromisoformat(fecha_inicio)
        fecha_fin = date.fromisoformat(fecha_fin)
    except:
        fecha_inicio = date.today() - timedelta(days=30)
        fecha_fin = date.today()

    ventas = (
        Venta.objects
        .filter(fecha__date__gte=fecha_inicio, fecha__date__lte=fecha_fin)
        .select_related('usuario')
        .prefetch_related('detalles')
        .order_by('-fecha')
    )

    # Crear respuesta CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="ventas_{fecha_inicio}_{fecha_fin}.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID Venta', 'Fecha', 'Cajero', 'Producto', 'Cantidad', 'Precio Unitario', 'Subtotal', 'Método Pago', 'IVA', 'Descuento', 'Total Final'])

    for venta in ventas:
        for detalle in venta.detalles.all():
            writer.writerow([
                venta.id,
                venta.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                venta.usuario.username if venta.usuario else 'N/A',
                detalle.producto.nombre,
                detalle.cantidad,
                detalle.precio_unitario,
                detalle.subtotal,
                venta.metodo_pago,
                venta.iva_total,
                venta.descuento_general,
                venta.total_final,
            ])

    return response