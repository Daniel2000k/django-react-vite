from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        # 👇 Solo pedimos email (login principal) + username opcional
        fields = ['id', 'email', 'username', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data.get('username', ''),  # username opcional
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        # Buscar usuario por email y autenticar por username
        try:
            user = User.objects.get(email=email)
            user_auth = authenticate(username=user.username, password=password)
            if user_auth and user_auth.is_active:
                return user_auth
        except User.DoesNotExist:
            pass
        
        raise serializers.ValidationError("Credenciales inválidas.")
