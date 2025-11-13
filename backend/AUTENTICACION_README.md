# Configuración de Autenticación Django - Login y Register

## Descripción

Este proyecto implementa un sistema completo de autenticación en Django con:
- ✅ **Login** y **Register** por correo electrónico
- ✅ **Validaciones** de datos (correo único, contraseña confirmada, etc.)
- ✅ **Templates HTML** con diseño responsivo
- ✅ **API REST** con JWT para frontend externo
- ✅ **Redirección automática** a página Home después de autenticarse

## Estructura de Archivos

```
backend/
├── accounts/
│   ├── models.py           # Modelo de Usuario personalizado
│   ├── views.py            # Vistas de Template + API
│   ├── urls.py             # Rutas de autenticación
│   ├── serializers.py      # Serializadores DRF
│   └── migrations/
├── templates/
│   └── accounts/
│       ├── base.html       # Template base (navbar, estilos)
│       ├── login.html      # Página de login
│       ├── register.html   # Página de registro
│       └── home.html       # Página de inicio (solo autenticados)
└── mytienda/
    ├── settings.py         # Configuración de Django
    └── urls.py             # URLs principales
```

## Rutas Disponibles

### 🔐 Autenticación con Templates (HTML)
```
GET  /accounts/register/     → Formulario de registro
POST /accounts/register/     → Guardar nuevo usuario
GET  /accounts/login/        → Formulario de login
POST /accounts/login/        → Validar credenciales
GET  /accounts/home/         → Página inicio (autenticado)
GET  /accounts/logout/       → Cerrar sesión
```

### 📡 API REST (JSON)
```
POST /accounts/api/register/ → Registrar usuario (JSON)
POST /accounts/api/login/    → Login (JSON)
GET  /accounts/api/user/     → Obtener usuario actual
```

## Instalación y Configuración

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Crear archivo `.env` en la carpeta `backend/`
```env
SECRET_KEY=tu-secret-key-seguro
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost:5432/mitienda
```

### 3. Ejecutar migraciones
```bash
cd backend
python manage.py migrate
```

### 4. Crear superusuario (opcional)
```bash
python manage.py createsuperuser
```

### 5. Ejecutar servidor
```bash
python manage.py runserver
```

Accede a: http://localhost:8000/accounts/login/

## Flujo de Autenticación

### 📝 Registro
1. Usuario ingresa: **email**, **usuario**, **contraseña**
2. Sistema valida:
   - Correo no duplicado
   - Usuario no duplicado
   - Contraseña mínimo 6 caracteres
   - Contraseñas coinciden
3. Usuario se crea en BD
4. Se inicia sesión automáticamente
5. Redirige a → `/accounts/home/`

### 🔓 Login
1. Usuario ingresa: **email** y **contraseña**
2. Sistema busca usuario por email
3. Valida la contraseña
4. Si es válido, inicia sesión
5. Redirige a → `/accounts/home/`

### 🏠 Home
- Solo accesible si está autenticado
- Muestra información del usuario
- Botón para cerrar sesión

## Características del Template

✨ **Base.html**
- Navegación con usuario actual
- Sistema de mensajes (éxito/error)
- Estilos modernos con gradientes
- Responsive design

✨ **Login.html**
- Campos: correo, contraseña
- Validación en el formulario
- Link a registro

✨ **Register.html**
- Campos: correo, usuario, contraseña x2
- Validaciones en client + server
- Link a login

✨ **Home.html**
- Información del usuario
- Botón cerrar sesión
- Diseño limpio y centrado

## Cómo Usar la API REST

### Registrar usuario (JSON)
```bash
curl -X POST http://localhost:8000/accounts/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@example.com",
    "username": "usuario123",
    "password": "contraseña123"
  }'
```

### Login (JSON)
```bash
curl -X POST http://localhost:8000/accounts/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@example.com",
    "password": "contraseña123"
  }'
```

### Obtener usuario actual (con token JWT)
```bash
curl -X GET http://localhost:8000/accounts/api/user/ \
  -H "Authorization: Bearer TU_ACCESS_TOKEN"
```

## Mensajes y Validaciones

### ✅ Mensajes de Éxito
- "¡Bienvenido [usuario]!" → Registro exitoso
- "¡Bienvenido de vuelta [usuario]!" → Login exitoso
- "Sesión cerrada correctamente" → Logout

### ❌ Mensajes de Error
- "Por favor completa todos los campos"
- "Las contraseñas no coinciden"
- "La contraseña debe tener al menos 6 caracteres"
- "El correo ya está registrado"
- "El usuario ya está registrado"
- "El correo no está registrado"
- "Contraseña incorrecta"

## Seguridad

✔️ **Contraseñas:** Hasheadas con PBKDF2
✔️ **CSRF:** Token CSRF en formularios
✔️ **SQL Injection:** Protegido por ORM Django
✔️ **Validación:** Server-side + Client-side
✔️ **Sesiones:** Django Sessions

## Próximos Pasos

1. **Frontend React**: Conectar con la API REST
2. **Email Verification**: Validar correo al registrarse
3. **Recuperar Contraseña**: Reset password por email
4. **2FA**: Autenticación de dos factores
5. **Perfil de Usuario**: Editar información personal

## Troubleshooting

**❓ Error: "No such table: accounts_user"**
```bash
python manage.py migrate
```

**❓ Error: "csrf_token not found"**
- Asegúrate de tener `{% csrf_token %}` en los formularios POST

**❓ El login no funciona**
- Verifica que el usuario fue creado: `python manage.py shell`
- Comprueba que el correo es único

**❓ Templates no se encuentran**
- Verifica que `TEMPLATES['DIRS']` en settings.py apunta a `BASE_DIR / 'templates'`

---

**Autor:** Configuración de Autenticación Django
**Fecha:** 2024
