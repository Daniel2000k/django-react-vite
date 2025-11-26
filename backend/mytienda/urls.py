from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView


urlpatterns = [
    path('admin/', admin.site.urls),
    
    #  La URL raíz  incluye las rutas de 'accounts'.
    path('', include('accounts.urls')), 
    
    # Rutas de autenticación 
    path('accounts/', include('accounts.urls')),
    
    # Rutas del inventario
    path('inventario/', include('inventario.urls')),
    
    #Rutas de ventas
    path('ventas/', include('ventas.urls')) ,
    
    #ruta compras
    path('compras/', include('compras.urls')),

    #ruta reportes
    path('reportes/', include('reportes.urls', namespace='reportes')),
]