from django.contrib.auth import get_user_model, authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import user_passes_test, login_required
from django.http import HttpResponseForbidden
from accounts.models import User
from .forms import UsuarioForm

# ✅ Importa utilidades extendidas
from .utils import send_verification_email, generate_otp, send_otp_email

User = get_user_model()

# ==================== FUNCIONES DE SOPORTE ====================
def es_admin(user):
    return user.is_authenticated and user.rol == "ADMIN"

def es_cajero(user):
    return user.is_authenticated and user.rol == "CAJERO"

# ==================== REGISTRO ====================
class RegisterTemplateView(View):
    """Vista de registro con doble verificación (enlace + OTP)"""
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('inventario_dashboard')
        return render(request, 'accounts/register.html')

    def post(self, request):
        email = request.POST.get('email', '').strip().lower()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('password_confirm', '').strip()

        # Validaciones básicas
        if not email or not username or not password:
            messages.error(request, 'Por favor completa todos los campos')
            return render(request, 'accounts/register.html')

        if password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'accounts/register.html', {'email': email, 'username': username})

        if len(password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres')
            return render(request, 'accounts/register.html', {'email': email, 'username': username})

        # Verificar duplicados
        if User.objects.filter(email__iexact=email, is_active=True).exists():
            messages.error(request, 'El correo ya está registrado y activo')
            return render(request, 'accounts/register.html', {'username': username})

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'El correo ya está registrado.')
            return render(request, 'accounts/register.html', {'email': email, 'username': username})

        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'El nombre de usuario ya está registrado')
            return render(request, 'accounts/register.html', {'email': email})

        # Crear usuario
        try:
            user = User.objects.create_user(
                email=email,
                username=username,
                password=password,
                is_active=False,
                rol="CAJERO"
            )

            # Enviar enlace de verificación
            send_verification_email(request, user)

            # Generar OTP y guardar en sesión
            otp = generate_otp()
            request.session['otp_code'] = otp
            request.session['otp_user_id'] = user.id
            send_otp_email(user, otp)

            messages.success(
                request,
                f'¡Cuenta creada exitosamente! Se envió un email de verificación y un OTP a {email}. '
                f'Por favor verifica tu email y usa el código OTP para activar tu cuenta.'
            )
            return redirect('verify_otp')
        except Exception as e:
            messages.error(request, f'Error al registrar: {str(e)}')
            return render(request, 'accounts/register.html', {'email': email, 'username': username})

# ==================== LOGIN ====================
class LoginTemplateView(View):
    """Vista de login con OTP"""
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

        user = authenticate(request, email=email, password=password)

        if user is not None:
            # Generar OTP y guardar en sesión
            otp = generate_otp()
            request.session['otp_code'] = otp
            request.session['otp_user_id'] = user.id
            send_otp_email(user, otp)

            messages.info(request, f"Se envió un código OTP a {user.email}. Ingresa el código para continuar.")
            return redirect('verify_otp')
        else:
            messages.error(request, 'Correo o contraseña incorrectos')
            return render(request, 'accounts/login.html', {'email': email})

# ==================== VERIFICAR OTP ====================
def verify_otp(request):
    """Verifica el OTP enviado por email"""
    if request.method == "POST":
        code = request.POST.get("otp")
        session_code = request.session.get("otp_code")
        user_id = request.session.get("otp_user_id")

        if code == session_code and user_id:
            try:
                user = User.objects.get(id=user_id)
                login(request, user, backend='accounts.backends.EmailBackend')


                # limpiar sesión
                request.session.pop("otp_code", None)
                request.session.pop("otp_user_id", None)

                messages.success(request, f"Bienvenido {user.username}, verificación exitosa.")
                if user.rol == "ADMIN":
                    return redirect('/inventario/')
                else:
                    return redirect('/ventas/crear/')
            except User.DoesNotExist:
                messages.error(request, "Usuario no encontrado.")
        else:
            messages.error(request, "Código inválido o expirado.")
    return render(request, "accounts/verify_otp.html")

# ==================== LOGOUT ====================
class LogoutTemplateView(View):
    def get(self, request):
        logout(request)
        messages.success(request, 'Sesión cerrada correctamente')
        return redirect('login')

# ==================== HOME ====================
class HomeTemplateView(View):
    """Vista Home - solo para usuarios autenticados"""
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        return render(request, 'inventario/dashboard.html', {'user': request.user})

# ==================== ADMIN USUARIOS ====================
@user_passes_test(es_admin, login_url='login')
def usuarios_lista(request):
    usuarios = User.objects.all()
    return render(request, "accounts/usuarios_lista.html", {"usuarios": usuarios})

@user_passes_test(es_admin, login_url='login')
def usuario_crear(request):
    if request.method == "POST":
        form = UsuarioForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data['password']:
                user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, 'Usuario creado exitosamente.')
            return redirect("usuarios_lista")
        else:
            messages.error(request, 'Error al crear el usuario.')
    else:
        form = UsuarioForm()
    return render(request, "accounts/usuario_form.html", {"form": form})

@user_passes_test(es_admin, login_url='login')
def usuario_editar(request, usuario_id):
    user = get_object_or_404(User, id=usuario_id)
    if request.method == "POST":
        form = UsuarioForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data['password']:
                user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, 'Usuario editado exitosamente.')
            return redirect("usuarios_lista")
        else:
            messages.error(request, 'Error al editar el usuario.')
    else:
        form = UsuarioForm(instance=user)
    return render(request, "accounts/usuario_form.html", {"form": form, "user_to_edit": user})

@user_passes_test(es_admin, login_url='login')
def usuario_eliminar(request, usuario_id):
    user = get_object_or_404(User, id=usuario_id)
    user.delete()
    messages.warning(request, f'Usuario {user.username} eliminado correctamente.')
    return redirect("usuarios_lista")

# ==================== REDIRECCIÓN POR ROL ====================
@login_required(login_url='login')
def home_redirect(request):
    user = request.user
    if user.rol == "ADMIN":
        return redirect('/inventario/')
    elif user.rol == "CAJERO":
        return redirect('/ventas/crear/')
    else:
        return HttpResponseForbidden("Tu rol no está configurado correctamente.")

# ==================== ACTIVACIÓN POR ENLACE ====================
def activate_account(request, uidb64, token):
    """Activa la cuenta del usuario con el token de verificación"""
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except Exception as e:
        print(f"❌ Error decodificando token: {str(e)}")
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success