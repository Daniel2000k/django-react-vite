from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib import admin
from django.urls import path,include


urlpatterns = [ # son los enlaces que los ususarios pueden visitar 
    path('admin/', admin.site.urls),
    path('', include('inventario.urls')),
    
    path('accounts/', include('accounts.urls')),  # 👈 Importante: path completo
]