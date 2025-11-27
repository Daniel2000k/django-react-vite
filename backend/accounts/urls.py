from django.urls import path
from .views import (
    # Vistas API
    activate_account,
    
    # Vistas de Autenticación con Templates
    RegisterTemplateView, LoginTemplateView, LogoutTemplateView, HomeTemplateView,
    
    # Vistas de Gestión de Usuarios (Admin)
    usuarios_lista, usuario_crear, usuario_editar, usuario_eliminar,
    
    # 💡 NUEVA VISTA
    home_redirect # Se importa la nueva función de redirección
)

urlpatterns = [
    
    
    # ==================== RUTAS TEMPLATES (Autenticación) ====================
    # Vistas basadas en clases para manejar el flujo de autenticación con renderizado HTML.
    
    # 💡 RUTA PRINCIPAL (CORRECCIÓN): 
    path('', home_redirect, name='root'), 
    
    # Login, logout, register (Existentes)
    path('register/', RegisterTemplateView.as_view(), name='register'),
    path('login/', LoginTemplateView.as_view(), name='login'),
    path('logout/', LogoutTemplateView.as_view(), name='logout'),
    
    # Home según rol (Se mantiene explícitamente)
    path('home/', home_redirect, name='home'), 
    
    # ==================== RUTAS TEMPLATES (Gestión de Usuarios - Admin) ====================
    # Vistas basadas en funciones protegidas con @user_passes_test(es_admin).
    path("usuarios/", usuarios_lista, name="usuarios_lista"),
    path("usuarios/crear/", usuario_crear, name="usuario_crear"),
    path("usuarios/editar/<int:usuario_id>/", usuario_editar, name="usuario_editar"),
    path("usuarios/eliminar/<int:usuario_id>/", usuario_eliminar, name="usuario_eliminar"),
    path("activate/<uidb64>/<token>/", activate_account, name="activate"),

]