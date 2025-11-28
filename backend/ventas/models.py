from django.db import models
from inventario.models import Producto

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

    # Descuentos e impuestos
    descuento_general = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    iva_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=19.0)
    iva_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_final = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Usuario cajero que realiza la venta
    usuario = models.ForeignKey('accounts.User', null=True, on_delete=models.SET_NULL)

    # Email del cliente para factura electrónica
    email_cliente = models.EmailField(null=True, blank=True)

    # Campos para integración con Mercado Pago
    estado_pago = models.CharField(max_length=20, default="pendiente")
    mp_payment_id = models.CharField(max_length=50, blank=True, null=True)
    mp_preference_id = models.CharField(max_length=50, blank=True, null=True)
    mp_link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Venta #{self.id} - ${self.total_final}"


# ===========================
# DETALLE DE VENTA
# ===========================
class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True)
    producto_nombre = models.CharField(max_length=200, blank=True, default='')
    producto_codigo = models.CharField(max_length=50, blank=True, default='')
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)

    def save(self, *args, **kwargs):
        if self.producto:
            if not self.producto_nombre:
                self.producto_nombre = self.producto.nombre
            if not self.producto_codigo:
                self.producto_codigo = str(self.producto.codigo)
        super().save(*args, **kwargs)

    def __str__(self):
        nombre = self.producto.nombre if self.producto else self.producto_nombre
        return f"{nombre} x {self.cantidad}"
