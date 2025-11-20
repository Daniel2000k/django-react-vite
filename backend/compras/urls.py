from django.urls import path
from .views import compra_crear, compra_lista, compra_detalle

urlpatterns = [
    path('', compra_lista, name='compra_lista'),
    path('crear/', compra_crear, name='compra_crear'),
    path('<int:compra_id>/', compra_detalle, name='compra_detalle'),
]
