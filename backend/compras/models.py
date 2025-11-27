from django.db import models
from django.utils import timezone
from django.db.models import SET_NULL
from inventario.models import Producto, Proveedor, Inventario

class Compra(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    fecha = models.DateTimeField(default=timezone.now)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"Compra #{self.id} - {self.proveedor.nombre}"


class DetalleCompra(models.Model):
    compra = models.ForeignKey(Compra, related_name='detalles', on_delete=models.CASCADE)
    # Allow producto to be deleted while preserving historical snapshot
    producto = models.ForeignKey(Producto, on_delete=SET_NULL, null=True, blank=True)
    producto_nombre = models.CharField(max_length=200, null=True, blank=True)
    producto_codigo = models.IntegerField(null=True, blank=True)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def save(self, *args, **kwargs):
        # populate snapshot fields from producto if available
        if self.producto and (not self.producto_nombre or not self.producto_codigo):
            try:
                self.producto_nombre = self.producto.nombre
                self.producto_codigo = self.producto.codigo
            except Exception:
                pass
        super().save(*args, **kwargs)
