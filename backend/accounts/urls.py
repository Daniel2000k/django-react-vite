from django.urls import path
from .views import (
    RegisterView, LoginView, UserView,
    RegisterTemplateView, LoginTemplateView, LogoutTemplateView, HomeTemplateView
)

urlpatterns = [
    # ==================== RUTAS API (REST) ====================
    path('api/register/', RegisterView.as_view(), name='api_register'),
    path('api/login/', LoginView.as_view(), name='api_login'),
    path('api/user/', UserView.as_view(), name='api_user'),
    
    # ==================== RUTAS TEMPLATES ====================
    path('register/', RegisterTemplateView.as_view(), name='register'),
    path('login/', LoginTemplateView.as_view(), name='login'),
    path('logout/', LogoutTemplateView.as_view(), name='logout'),
    path('home/', HomeTemplateView.as_view(), name='home'),
]
