from django.urls import path
from .views import verify_otp

from .views import (
    activate_account,
    RegisterTemplateView, LoginTemplateView, LogoutTemplateView,
    HomeTemplateView, 
    usuarios_lista, usuario_crear, usuario_editar, usuario_eliminar,
    home_redirect,ForgotPasswordView, ResetPasswordView,
)

urlpatterns = [
    path('', home_redirect, name='root'),
    path('register/', RegisterTemplateView.as_view(), name='register'),
    path('login/', LoginTemplateView.as_view(), name='login'),
    path('logout/', LogoutTemplateView.as_view(), name='logout'),

    # Forgot y Reset (TU FLUJO PERSONALIZADO)
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot_password"),
    path("reset-password/<str:token>/", ResetPasswordView.as_view(), name="reset_password"),

    path('home/', home_redirect, name='home'),

    # Admin
    path("usuarios/", usuarios_lista, name="usuarios_lista"),
    path("usuarios/crear/", usuario_crear, name="usuario_crear"),
    path("usuarios/editar/<int:usuario_id>/", usuario_editar, name="usuario_editar"),
    path("usuarios/eliminar/<int:usuario_id>/", usuario_eliminar, name="usuario_eliminar"),

    path("activate/<uidb64>/<token>/", activate_account, name="activate"),

    # OTP
    path('verify-otp/', verify_otp, name='verify_otp'),
]
