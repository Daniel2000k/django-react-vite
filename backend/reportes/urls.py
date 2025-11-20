from django.urls import path
from . import views

app_name = "reportes"

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('ventas-periodo/', views.ventas_por_periodo, name='ventas_por_periodo'),
    path('top-productos/', views.top_productos, name='top_productos'),
    path('bajo-stock/', views.productos_bajo_stock, name='productos_bajo_stock'),
    path('ventas-por-cajero/', views.ventas_por_cajero, name='ventas_por_cajero'),
    path('export/ventas-csv/', views.export_ventas_csv, name='export_ventas_csv'),
]
