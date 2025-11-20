from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductoViewSet, InventarioViewSet,
    inventario_dashboard, producto_lista, producto_crear, producto_editar, producto_eliminar, inventario_movimiento,
    proveedor_lista, proveedor_crear,
    orden_lista, orden_crear, orden_recibir,
    alertas_lista, alerta_marcar_leida,
    proveedor_editar, proveedor_eliminar, proveedor_detalle,
    orden_detalle, orden_editar, orden_cancelar,verificar_codigo_producto,
    verificar_correo_proveedor
)
from ventas.views import (
    venta_lista, venta_crear, venta_detalle, venta_factura_pdf
)

router = DefaultRouter()
router.register(r'productos', ProductoViewSet, basename='api_producto')
router.register(r'movimientos', InventarioViewSet, basename='api_inventario')

urlpatterns = [
    # ===== VISTAS (HTML) =====
    path('', inventario_dashboard, name='inventario_dashboard'),

    # Productos
    path('productos/', producto_lista, name='producto_lista'),
    path('productos/crear/', producto_crear, name='producto_crear'),
    path('productos/<int:producto_id>/editar/', producto_editar, name='producto_editar'),
    path('productos/<int:producto_id>/eliminar/', producto_eliminar, name='producto_eliminar'),
    path('productos/verificar-codigo/', verificar_codigo_producto, name='verificar_codigo_producto'),

    # Movimientos
    path('movimientos/', inventario_movimiento, name='inventario_movimiento'),

    # Proveedores
    path('proveedores/', proveedor_lista, name='proveedor_lista'),
    path('proveedores/crear/', proveedor_crear, name='proveedor_crear'),
   
    path('proveedores/verificar-correo/', verificar_correo_proveedor, name='verificar_correo_proveedor'),
   
    # Proveedores: editar, eliminar, detalle
    path('proveedores/editar/<int:proveedor_id>/', proveedor_editar, name='proveedor_editar'),
    path('proveedores/eliminar/<int:proveedor_id>/', proveedor_eliminar, name='proveedor_eliminar'),
    path('proveedores/<int:proveedor_id>/', proveedor_detalle, name='proveedor_detalle'),

    # Órdenes de compra
    path('ordenes/', orden_lista, name='orden_lista'),
    path('ordenes/crear/', orden_crear, name='orden_crear'),
    path('ordenes/recibir/<int:orden_id>/', orden_recibir, name='orden_recibir'),
    # Ordenes: detalle, editar, cancelar
    path('ordenes/<int:orden_id>/', orden_detalle, name='orden_detalle'),
    path('ordenes/editar/<int:orden_id>/', orden_editar, name='orden_editar'),
    path('ordenes/cancelar/<int:orden_id>/', orden_cancelar, name='orden_cancelar'),

    # Alertas
    path('alertas/', alertas_lista, name='alertas_lista'),
    path('alertas/leida/<int:alerta_id>/', alerta_marcar_leida, name='alerta_marcar_leida'),

    # Ventas
    path('ventas/', venta_lista, name='venta_lista'),
    path('ventas/crear/', venta_crear, name='venta_crear'),
    path('ventas/<int:venta_id>/', venta_detalle, name='venta_detalle'),
    # Nueva URL para factura PDF
    path('ventas/<int:venta_id>/factura/', venta_factura_pdf, name='venta_factura_pdf'),  # <-- AGREGADO

    # API REST
    path('api/', include(router.urls)),
]
