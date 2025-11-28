import random
import hashlib
from urllib.parse import urlencode

from django.core.mail import send_mail, EmailMultiAlternatives
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse


# ==========================
# 🔐 OTP (One-Time Password)
# ==========================

def generate_otp():
    """Genera un código OTP de 6 dígitos"""
    return str(random.randint(100000, 999999))


def send_otp_email(user, code):
    """Envía el OTP al correo del usuario"""
    subject = "🔐 Tu código de verificación"
    message = f"Hola {user.username}, tu código OTP es: {code}. Válido por 5 minutos."
    send_mail(
        subject,
        message,
        "stockmaster255@gmail.com",  # remitente fijo Gmail
        [user.email],
        fail_silently=False,
    )


# ==========================
# 👤 Gravatar
# ==========================

def get_gravatar(email, size=200):
    """Devuelve la URL de Gravatar a partir de un email."""
    if not email:
        return None  # evita error si el email es None

    # Normaliza el email
    normalized_email = email.strip().lower()

    # Genera el hash MD5 del correo
    email_hash = hashlib.md5(normalized_email.encode('utf-8')).hexdigest()

    # Construye la URL completa
    params = urlencode({'d': 'retro', 's': str(size)})
    gravatar_url = f"https://www.gravatar.com/avatar/{email_hash}?{params}"

    return gravatar_url


# ==========================
# 📧 Email de verificación
# ==========================

def send_verification_email(request, user):
    """Envía email de verificación usando Gmail como remitente"""
    try:
        current_site = get_current_site(request)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        activation_url = f"http://{current_site.domain}{reverse('activate', args=[uid, token])}"

        subject = "🔐 Verifica tu cuenta en Stock Master"

        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    background-color: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    padding: 40px;
                    margin: 0 auto;
                }}
                .header {{
                    text-align: center;
                    border-bottom: 2px solid #2563eb;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    color: #2563eb;
                    margin: 0;
                }}
                .content {{
                    color: #333;
                    line-height: 1.6;
                }}
                .button {{
                    display: inline-block;
                    background: #2563eb;
                    color: white;
                    padding: 12px 30px;
                    border-radius: 6px;
                    text-decoration: none;
                    margin: 20px 0;
                    font-weight: bold;
                }}
                .button:hover {{
                    background: #1e40af;
                }}
                .footer {{
                    text-align: center;
                    border-top: 1px solid #e5e5e5;
                    padding-top: 20px;
                    margin-top: 30px;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 Stock Master</h1>
                </div>
                <div class="content">
                    <p>¡Hola <strong>{user.username}</strong>! 👋</p>
                    <p>Gracias por registrarte en <strong>Stock Master</strong>. Para completar tu registro y activar tu cuenta, haz clic en el botón de abajo:</p>
                    <center>
                        <a href="{activation_url}" class="button">✅ Verificar Mi Cuenta</a>
                    </center>
                    <p>O copia este enlace en tu navegador:</p>
                    <p style="word-break: break-all; background-color: #f0f0f0; padding: 10px; border-radius: 4px; font-size: 12px;">{activation_url}</p>
                    <p><strong>⏰ Este enlace expira en 24 horas.</strong></p>
                    <p>Si no creaste esta cuenta, ignora este mensaje.</p>
                </div>
                <div class="footer">
                    <p>Stock Master © 2025. Todos los derechos reservados.</p>
                    <p>Si tienes problemas, contacta a nuestro equipo de soporte.</p>
                </div>
            </div>
        </body>
        </html>
        """

        email = EmailMultiAlternatives(
            subject=subject,
            body=f"Verifica tu cuenta en Stock Master: {activation_url}",
            from_email="stockmaster255@gmail.com",  # 🔒 remitente fijo Gmail
            to=[user.email],
        )
        email.attach_alternative(html_message, "text/html")

        # Cabeceras extra para mejorar entrega en Outlook
        email.extra_headers = {
            "Reply-To": "stockmaster255@gmail.com",
            "X-Mailer": "Django",
        }

        resultado = email.send()

        if resultado:
            print(f"✅ Email de verificación enviado a {user.email}")
            return True
        else:
            print(f"❌ Email de verificación no se envió a {user.email}")
            return False

    except Exception as e:
        print(f"❌ Error enviando email de verificación: {str(e)}")
        return False

# ==========================
def send_password_reset_email(request, user, token_obj):
    """
    Envía el correo con el enlace de recuperación de contraseña.
    Recibe:
        - request
        - user: usuario que solicita el cambio
        - token_obj: instancia del modelo PasswordResetToken
    """
    try:
        current_site = get_current_site(request)

        # ✅ URL correcta usando el token del objeto, sin uidb64
        reset_url = f"http://{current_site.domain}{reverse('reset_password', args=[token_obj.token])}"

        subject = "🔒 Recuperación de contraseña - Stock Master"

        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    background-color: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    padding: 40px;
                    margin: 0 auto;
                }}
                .header {{
                    text-align: center;
                    border-bottom: 2px solid #2563eb;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    color: #2563eb;
                    margin: 0;
                }}
                .content {{
                    color: #333;
                    line-height: 1.6;
                }}
                .button {{
                    display: inline-block;
                    background: #2563eb;
                    color: white;
                    padding: 12px 30px;
                    border-radius: 6px;
                    text-decoration: none;
                    margin: 20px 0;
                    font-weight: bold;
                }}
                .button:hover {{
                    background: #1e40af;
                }}
                .footer {{
                    text-align: center;
                    border-top: 1px solid #e5e5e5;
                    padding-top: 20px;
                    margin-top: 30px;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔒 Recuperación de contraseña</h1>
                </div>
                <div class="content">
                    <p>Hola <strong>{user.username}</strong>,</p>
                    <p>Hemos recibido una solicitud para restablecer tu contraseña en 
                    <strong>Stock Master</strong>.</p>

                    <p>Haz clic en el siguiente botón para crear una nueva contraseña:</p>

                    <center>
                        <a href="{reset_url}" class="button">🔐 Restablecer Contraseña</a>
                    </center>

                    <p>O copia este enlace en tu navegador:</p>
                    <p style="word-break: break-all; background-color: #f0f0f0; padding: 10px; border-radius: 4px; font-size: 12px;">
                        {reset_url}
                    </p>

                    <p><strong>⏰ El enlace expira en 1 hora.</strong></p>
                    <p>Si no solicitaste este cambio, puedes ignorar este mensaje.</p>
                </div>

                <div class="footer">
                    <p>Stock Master © 2025</p>
                </div>
            </div>
        </body>
        </html>
        """

        email = EmailMultiAlternatives(
            subject=subject,
            body=f"Restablece tu contraseña aquí: {reset_url}",
            from_email="stockmaster255@gmail.com",
            to=[user.email],
        )

        email.attach_alternative(html_message, "text/html")

        resultado = email.send()

        if resultado:
            print(f"✅ Email de recuperación enviado a {user.email}")
            return True
        else:
            print(f"❌ Email de recuperación NO se envió a {user.email}")
            return False

    except Exception as e:
        print(f"❌ Error al enviar email de recuperación: {str(e)}")
        return False