from django.contrib.auth import get_user_model, authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views import View
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from .serializers import RegisterSerializer, LoginSerializer

# ✅ Obtiene el modelo de usuario configurado en AUTH_USER_MODEL
User = get_user_model()


# ==================== VISTAS BASADAS EN TEMPLATES ====================

class RegisterTemplateView(View):
    """Vista de registro con template HTML"""
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, 'accounts/register.html')
    
    def post(self, request):
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('password_confirm', '').strip()
        
        # Validaciones
        if not email or not username or not password:
            messages.error(request, 'Por favor completa todos los campos')
            return render(request, 'accounts/register.html')
        
        if password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'accounts/register.html')
        
        if len(password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres')
            return render(request, 'accounts/register.html')
        
        # Verificar si el usuario ya existe
        if User.objects.filter(email=email).exists():
            messages.error(request, 'El correo ya está registrado')
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El usuario ya está registrado')
            return render(request, 'accounts/register.html')
        
        # Crear usuario
        try:
            user = User.objects.create_user(
                email=email,
                username=username,
                password=password
            )
            login(request, user)
            messages.success(request, f'¡Bienvenido {username}!')
            return redirect('home')
        except Exception as e:
            messages.error(request, f'Error al registrar: {str(e)}')
            return render(request, 'accounts/register.html')


class LoginTemplateView(View):
    """Vista de login con template HTML"""
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, 'accounts/login.html')
    
    def post(self, request):
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not email or not password:
            messages.error(request, 'Por favor completa todos los campos')
            return render(request, 'accounts/login.html')
        
        # Autenticar usando el correo
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'¡Bienvenido de vuelta {user.username}!')
                return redirect('home')
            else:
                messages.error(request, 'Contraseña incorrecta')
                return render(request, 'accounts/login.html')
        except User.DoesNotExist:
            messages.error(request, 'El correo no está registrado')
            return render(request, 'accounts/login.html')


class LogoutTemplateView(View):
    """Vista de logout"""
    def get(self, request):
        logout(request)
        messages.success(request, 'Sesión cerrada correctamente')
        return redirect('login')


class HomeTemplateView(View):
    """Vista Home - solo para usuarios autenticados"""
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        return render(request, 'accounts/home.html', {
            'user': request.user
        })


# ==================== VISTAS API (REST) ====================

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data

        refresh = RefreshToken.for_user(user)
        return Response({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            },
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        })


class UserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.emailA
        })

