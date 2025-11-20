from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Backend de autenticación personalizado que permite login con email
    """
    def authenticate(self, request, username=None, email=None, password=None, **kwargs):
        try:
            # Intenta autenticar con email si se proporciona
            if email:
                user = User.objects.get(email__iexact=email)
            elif username:
                user = User.objects.get(username__iexact=username)
            else:
                return None
            
            # Verifica la contraseña
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except User.DoesNotExist:
            return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
