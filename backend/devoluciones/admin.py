from django.contrib import admin
from .models import Devolucion

@admin.register(Devolucion)
class DevolucionAdmin(admin.ModelAdmin):
    list_display = ('id', 'producto', 'cantidad', 'usuario', 'fecha')
    list_filter = ('fecha', 'usuario')
    search_fields = ('producto__nombre', 'motivo')
