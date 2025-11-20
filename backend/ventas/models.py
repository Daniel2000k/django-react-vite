from django.db import models
from django.utils import timezone
from inventario.models import Producto

# Create your models here.
# ===========================
# VENTA
# ===========================
class Venta(models.Model):
    METODOS_PAGO = [
        ("EFECTIVO", "Efectivo"),
        ("TARJETA", "Tarjeta"),
        ("TRANSFERENCIA", "Transferencia"),
    ]

    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Métodos de pago
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default="EFECTIVO")
    monto_recibido = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cambio = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Descuentos e impuestos (Fase 2)
    descuento_general = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    iva_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=19.0)
    iva_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_final = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    usuario = models.ForeignKey('accounts.User', null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Venta #{self.id} - ${self.total_final}"


# ===========================
# DETALLE DE VENTA
# ===========================
class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"

