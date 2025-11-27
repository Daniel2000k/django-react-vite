"""
Comando para limpiar registros de usuarios inactivos que no completaron verificación.
Uso: python manage.py cleanup_inactive_users --days=7
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import User

class Command(BaseCommand):
    help = 'Elimina usuarios inactivos que no completaron verificación después de N días'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Eliminar usuarios inactivos más antiguos de N días (default: 7)'
        )

    def handle(self, *args, **options):
        days = options['days']
        fecha_limite = timezone.now() - timedelta(days=days)

        # Buscar usuarios inactivos creados hace más de N días
        usuarios_antiguos = User.objects.filter(
            is_active=False,
            date_joined__lt=fecha_limite
        )

        cantidad = usuarios_antiguos.count()

        if cantidad == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ No hay usuarios inactivos para eliminar (más antiguos de {days} días)'
                )
            )
            return

        # Mostrar información antes de eliminar
        self.stdout.write(
            self.style.WARNING(
                f'\n⚠️  Se van a eliminar {cantidad} usuarios inactivos más antiguos de {days} días:'
            )
        )

        for usuario in usuarios_antiguos:
            self.stdout.write(f'   - {usuario.email} (creado: {usuario.date_joined})')

        # Confirmar antes de eliminar
        confirmacion = input('\n¿Deseas continuar? (s/n): ')

        if confirmacion.lower() != 's':
            self.stdout.write(self.style.ERROR('\n❌ Operación cancelada'))
            return

        # Eliminar
        usuarios_antiguos.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ {cantidad} usuarios inactivos eliminados correctamente'
            )
        )
