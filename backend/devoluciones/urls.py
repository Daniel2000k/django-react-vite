from django.urls import path
from . import views

urlpatterns = [
    path('', views.devoluciones_list, name='devoluciones_list'),
    path('api/venta/<int:venta_id>/detalles/', views.venta_detalles_api, name='venta_detalles_api'),
    path('ventas/', views.ventas_for_devoluciones, name='ventas_for_devoluciones'),
    path('ventas/<int:venta_id>/devolver/', views.devolver_desde_venta, name='devolver_desde_venta'),
    # Aquí puedes agregar más rutas para devoluciones
]
