from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView


urlpatterns = [ # son los enlaces que los ususarios pueden visitar 
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False)),  # Redirige a login por defecto
    path('', include('inventario.urls')),
    
    path('accounts/', include('accounts.urls')),  # 👈 Importante: path completo
]