from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    
    # Vistas de ventas
    venta_lista, venta_crear, venta_detalle, venta_factura_pdf, mis_ventas,
    producto_json,productos_search_json# <-- ¡AÑADIDA mis_ventas al import!
)

# Inicialización de router si se usa (aunque no se usa en este ejemplo, se mantiene la estructura)
# router = DefaultRouter()
# router.register(r'ventas', VentaViewSet)


urlpatterns = [
# Ventas
    path('', venta_lista, name='venta_lista'),
    path('crear/', venta_crear, name='venta_crear'),
    path('<int:venta_id>/', venta_detalle, name='venta_detalle'),
    # URL para factura PDF
    path('<int:venta_id>/factura/', venta_factura_pdf, name='venta_factura_pdf'),
    
    # NUEVA URL para "Mis Ventas"
    path('mis-ventas/', mis_ventas, name='mis_ventas'), 
     path('api/productos-search/', productos_search_json, name='ventas_productos_search'),
    path('api/producto/<int:producto_id>/', producto_json, name='ventas_producto_json'),

]