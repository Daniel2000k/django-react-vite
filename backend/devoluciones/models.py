from django.db import models
from django.utils import timezone
from django.conf import settings

from ventas.models import Venta, DetalleVenta
from inventario.models import Producto, Inventario


class Devolucion(models.Model):
    venta = models.ForeignKey(Venta, related_name='devoluciones', on_delete=models.SET_NULL, null=True, blank=True)
    detalle_venta = models.ForeignKey(DetalleVenta, related_name='devoluciones', on_delete=models.SET_NULL, null=True, blank=True)
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True)
    cantidad = models.IntegerField()
    motivo = models.CharField(max_length=250, blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateTimeField(default=timezone.now)

    def __str__(self):
        prod = self.producto.nombre if self.producto else (self.detalle_venta.producto_nombre if self.detalle_venta else 'Sin producto')
        return f"Devolución #{self.id} - {prod} x {self.cantidad}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        # Asegurar producto si no fue pasado
        if not self.producto and self.detalle_venta and self.detalle_venta.producto:
            self.producto = self.detalle_venta.producto

        super().save(*args, **kwargs)

        # Solo crear movimiento la primera vez que se crea la devolución
        if is_new and self.producto and self.cantidad:
            # Crear movimiento de tipo 'ENTRADA' para reingresar el stock
            referencia = f"DEV-{int(self.fecha.timestamp()*1000)}-{self.id}"
            Inventario.objects.create(
                producto=self.producto,
                tipo='ENTRADA',
                cantidad=self.cantidad,
                numero_referencia=referencia,
            )
