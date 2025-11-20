from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)

    ROLES = [
        ("ADMIN", "Administrador"),
        ("CAJERO", "Cajero"),
    ]

    rol = models.CharField(max_length=20, choices=ROLES, default="CAJERO")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.username} ({self.rol})"
