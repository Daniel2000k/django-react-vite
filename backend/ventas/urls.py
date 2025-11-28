from django.urls import path, include
from . import views
# from rest_framework.routers import DefaultRouter # Si no la estás usando, puedes omitirla

# --- IMPORTACIÓN DE VISTAS ---
# Se importan todas las vistas que estás usando en urlpatterns
from .views import (
    # Vistas de ventas
    venta_lista, 
    venta_crear, 
    venta_detalle, 
    venta_factura_pdf, 
    mis_ventas,
    # Vistas API
    producto_json,
    productos_search_json,
    # Vistas de Mercado Pago ⬅️ Importamos las vistas de MP directamente de views
    generar_link_pago,
    pago_exitoso,
    pago_fallido,
    pago_pendiente,
)

# Inicialización de router si se usa (si no usas DRF, puedes comentar/borrar estas líneas)
# router = DefaultRouter()
# router.register(r'ventas', VentaViewSet)


urlpatterns = [
    # ==================== RUTAS DE VENTAS Y GENERALES ====================
    path('', venta_lista, name='venta_lista'),
    path('crear/', venta_crear, name='venta_crear'),
    path('<int:venta_id>/', venta_detalle, name='venta_detalle'),
    
    # URL para factura PDF
    path('<int:venta_id>/factura/', venta_factura_pdf, name='venta_factura_pdf'),
    
    # URL para "Mis Ventas"
    path('mis-ventas/', mis_ventas, name='mis_ventas'), 
    
    # ==================== RUTAS API (JSON) ====================
    path('api/productos-search/', productos_search_json, name='ventas_productos_search'),
    path('api/producto/<int:producto_id>/', producto_json, name='ventas_producto_json'),

    # ==================== RUTAS MERCADO PAGO ====================
    
    # URL que inicia el proceso de generar la preferencia de pago en MP
    path("venta/<int:venta_id>/pago/", generar_link_pago, name="generar_link_pago"),
    
    # URLs de retorno (Back URLs) de Mercado Pago
    path("venta/<int:venta_id>/pago/exitoso/", pago_exitoso, name="pago_exitoso"),
    path("venta/<int:venta_id>/pago/fallido/", pago_fallido, name="pago_fallido"),
    path("venta/<int:venta_id>/pago/pendiente/", pago_pendiente, name="pago_pendiente"),

    # Si usas DRF:
    # path('', include(router.urls)),
]