from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductoViewSet, InventarioViewSet,
    inventario_dashboard, producto_lista, producto_crear, producto_editar, producto_eliminar, inventario_movimiento,
    proveedor_lista, proveedor_crear,
    # Órdenes y alertas archivadas (ver backend/archived/20251123_orders_alerts)
    proveedor_editar, proveedor_eliminar, proveedor_detalle,
    orden_detalle, orden_editar, orden_cancelar,verificar_codigo_producto,
    verificar_correo_proveedor
)
from .views import api_producto_create
from .views import api_productos_search
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

    # Órdenes de compra y Alertas: archivadas.
    # Si necesitas restaurarlas mueve los archivos desde `backend/archived/20251123_orders_alerts/`
    # y añade las rutas correspondientes aquí.

    # Ventas
    path('ventas/', venta_lista, name='venta_lista'),
    path('ventas/crear/', venta_crear, name='venta_crear'),
    path('ventas/<int:venta_id>/', venta_detalle, name='venta_detalle'),
    # Nueva URL para factura PDF
    path('ventas/<int:venta_id>/factura/', venta_factura_pdf, name='venta_factura_pdf'),  # <-- AGREGADO

    # ⭐ API REST - RUTAS ESPECÍFICAS PRIMERO (antes del router)
    path('api/productos/buscar/', api_productos_search, name='api_productos_search'),
    path('api/productos/crear/', api_producto_create, name='api_producto_create'),
    path('api/', include(router.urls)),
]
