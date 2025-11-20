from django.contrib.auth import get_user_model, authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404 
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views import View
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from django.contrib.auth.decorators import user_passes_test, login_required # Se añade login_required
from django.http import HttpResponseForbidden # Se añade HttpResponseForbidden
from .serializers import RegisterSerializer, LoginSerializer
# Importación del formulario (asumiendo que está en el mismo paquete de la app)
from .forms import UsuarioForm 

# ✅ Obtiene el modelo de usuario configurado en AUTH_USER_MODEL
User = get_user_model()


# ==================== Funciones de soporte (Decoradores) ====================

def es_admin(user):
    """Verifica si el usuario tiene el rol de ADMIN."""
    # Asume que el modelo de usuario tiene un campo 'rol'
    return user.is_authenticated and user.rol == "ADMIN"

def es_cajero(user):
    """Verifica si el usuario tiene el rol de CAJERO."""
    return user.is_authenticated and user.rol == "CAJERO"


# ==================== VISTAS BASADAS EN TEMPLATES (Auth & Base) ====================

class RegisterTemplateView(View):
    """Vista de registro con template HTML"""
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('inventario_dashboard')
        return render(request, 'accounts/register.html')
    
    def post(self, request):
        email = request.POST.get('email', '').strip().lower()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('password_confirm', '').strip()
        
        # Validaciones
        if not email or not username or not password:
            messages.error(request, 'Por favor completa todos los campos')
            return render(request, 'accounts/register.html')
        
        if password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'accounts/register.html', {
                'email': email,
                'username': username
            })
        
        if len(password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres')
            return render(request, 'accounts/register.html', {
                'email': email,
                'username': username
            })
        
        # Verificar si el usuario ya existe
        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'El correo ya está registrado')
            return render(request, 'accounts/register.html', {
                'username': username
            })
        
        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'El usuario ya está registrado')
            return render(request, 'accounts/register.html', {
                'email': email
            })
        
        # Crear usuario
        try:
            # Se asume que create_user maneja el campo 'rol' o tiene un valor predeterminado
            user = User.objects.create_user(
                email=email,
                username=username,
                password=password
            )
            # NO autologueamos, dejamos que el usuario haga login manualmente
            messages.success(request, f'¡Cuenta creada exitosamente! Por favor inicia sesión con tus credenciales.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error al registrar: {str(e)}')
            return render(request, 'accounts/register.html', {
                'email': email,
                'username': username
            })


class LoginTemplateView(View):
    """Vista de login con template HTML"""
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('inventario_dashboard')
        return render(request, 'accounts/login.html')
    
    def post(self, request):
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '').strip()
        
        if not email or not password:
            messages.error(request, 'Por favor completa todos los campos')
            return render(request, 'accounts/login.html')
        
        # Autenticar usando el backend personalizado
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido de vuelta {user.username}!')
            # 💡 MODIFICACIÓN: Redirección basada en el rol del usuario
            if user.rol == "ADMIN":
                return redirect('/inventario/') # Redirige a la URL del dashboard/inventario
            else:
                return redirect('/ventas/crear/') # Redirige a la URL de creación de ventas para Cajeros
        else:
            messages.error(request, 'Correo o contraseña incorrectos')
            return render(request, 'accounts/login.html', {
                'email': email
            })


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
        return render(request, 'inventario/dashboard.html', {
            'user': request.user
        })


# ==================== VISTAS BASADAS EN TEMPLATES (Gestión de Usuarios - Admin) ====================

@user_passes_test(es_admin, login_url='login') 
def usuarios_lista(request):
    """Lista todos los usuarios (Solo Admin)."""
    usuarios = User.objects.all()
    return render(request, "accounts/usuarios_lista.html", {"usuarios": usuarios})

@user_passes_test(es_admin, login_url='login') 
def usuario_crear(request):
    """Permite crear un nuevo usuario (Solo Admin)."""
    if request.method == "POST":
        form = UsuarioForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Se encripta la contraseña si se proporciona
            if form.cleaned_data['password']: 
                user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, 'Usuario creado exitosamente.')
            return redirect("usuarios_lista")
        else:
            messages.error(request, 'Error al crear el usuario. Por favor revisa el formulario.')
    else:
        form = UsuarioForm()
    return render(request, "accounts/usuario_form.html", {"form": form})

@user_passes_test(es_admin, login_url='login') 
def usuario_editar(request, usuario_id):
    """Permite editar un usuario existente (Solo Admin)."""
    user = get_object_or_404(User, id=usuario_id)
    if request.method == "POST":
        # Se pasa la instancia para editar
        form = UsuarioForm(request.POST, instance=user) 
        if form.is_valid():
            user = form.save(commit=False)
            # Se actualiza la contraseña solo si se proporciona una nueva
            if form.cleaned_data['password']: 
                user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, 'Usuario editado exitosamente.')
            return redirect("usuarios_lista")
        else:
            messages.error(request, 'Error al editar el usuario. Por favor revisa el formulario.')
    else:
        # Se inicializa el formulario con los datos del usuario
        form = UsuarioForm(instance=user) 
    return render(request, "accounts/usuario_form.html", {"form": form, "user_to_edit": user})

@user_passes_test(es_admin, login_url='login') 
def usuario_eliminar(request, usuario_id):
    """Elimina un usuario (Solo Admin)."""
    user = get_object_or_404(User, id=usuario_id)
    user.delete()
    messages.warning(request, f'Usuario {user.username} eliminado correctamente.')
    return redirect("usuarios_lista")


# ==================== VISTAS API (REST) ====================

class RegisterView(generics.CreateAPIView):
    """API para registrar un nuevo usuario."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    # Permiso para que cualquiera pueda registrarse
    permission_classes = [permissions.AllowAny] 


class LoginView(APIView):
    """API para obtener tokens de autenticación (Login)."""
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data.get('user')
        
        if user:
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
        else:
            # Este caso no debería ocurrir si el serializer valida correctamente
            return Response({"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)


class UserView(APIView):
    """API para obtener los datos del usuario autenticado."""
    # Requiere que el usuario esté autenticado con un token JWT válido
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            # Se añade el rol para información del API
            "rol": getattr(user, 'rol', 'N/A') 
        })
        
# ==================== NUEVA FUNCIÓN DE REDIRECCIÓN ====================

@login_required(login_url='login')
def home_redirect(request):
    """Redirige al home según el rol del usuario."""
    user = request.user

    if user.rol == "ADMIN":
        return redirect('/inventario/')
    elif user.rol == "CAJERO":
        return redirect('/ventas/crear/')
    else:
        # Responde con un error 403 Forbidden si el rol no coincide
        return HttpResponseForbidden("Tu rol no está configurado correctamente.")