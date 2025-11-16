from django.db import models
from django.utils import timezone

# ===========================
# MODELO PROVEEDOR
# ===========================
class Proveedor(models.Model):
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=200)
    correo = models.EmailField()

    def __str__(self):
        return self.nombre


# ===========================
# PRODUCTO (TU MISMO MODELO)
# ===========================
class Producto(models.Model):
    codigo = models.IntegerField(unique=True)
    nombre = models.CharField(max_length=100)
    stock = models.IntegerField(default=0)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=3)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=3)

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


# ===========================
# ORDEN DE COMPRA
# ===========================
class OrdenCompra(models.Model):
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('RECIBIDA', 'Recibida'),
        ('CANCELADA', 'Cancelada')
    )

    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name="ordenes")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="ordenes_compra")

    cantidad = models.IntegerField()
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=3)
    subtotal = models.DecimalField(max_digits=12, decimal_places=3)

    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_recepcion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"OC-{self.id} | {self.producto.nombre} x {self.cantidad}"

    # CUANDO SE MARCA COMO RECIBIDA, AUMENTA STOCK
    def recibir(self):
        if self.estado != 'RECIBIDA':
            self.producto.stock += self.cantidad
            self.producto.save()
            self.estado = 'RECIBIDA'
            self.fecha_recepcion = timezone.now()
            self.save()

            # CREAR ALERTA
            AlertaInventario.objects.create(
                tipo="COMPRA",
                titulo=f"Orden de compra OC-{self.id} recibida",
                mensaje=f"Se agregaron {self.cantidad} unidades de {self.producto.nombre}.",
                producto=self.producto,
                orden_compra=self
            )


# ===========================
# MOVIMIENTOS DE INVENTARIO (TU MODELO ORIGINAL)
# ===========================
class Inventario(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="movimientos")
    tipo = models.CharField(max_length=10, choices=[('ENTRADA', 'Entrada'), ('SALIDA', 'Salida')])
    cantidad = models.IntegerField()
    numero_referencia = models.CharField(max_length=20, unique=True, blank=True, null=True)

    def __str__(self):
        return f"{self.tipo} - {self.producto.nombre} ({self.cantidad})"

    def save(self, *args, **kwargs):
        if self.tipo == 'ENTRADA':
            self.producto.stock += self.cantidad
        elif self.tipo == 'SALIDA':
            self.producto.stock -= self.cantidad
        self.producto.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.producto_id and Producto.objects.filter(id=self.producto_id).exists():
            if self.tipo == 'ENTRADA':
                self.producto.stock -= self.cantidad
            elif self.tipo == 'SALIDA':
                self.producto.stock += self.cantidad
            self.producto.save()
        super().delete(*args, **kwargs)


# ===========================
# VENTA Y DETALLE DE VENTA (NUEVOS MODELOS)
# ===========================
class Venta(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    usuario = models.ForeignKey('accounts.User', null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Venta #{self.id} - ${self.total}"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"


# ===========================
# ALERTAS
# ===========================
class AlertaInventario(models.Model):
    TIPOS = (
        ('COMPRA', 'Compra'),
        ('STOCK_MINIMO', 'Stock mínimo')
    )

    tipo = models.CharField(max_length=20, choices=TIPOS)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()

    fecha = models.DateTimeField(default=timezone.now)
    leida = models.BooleanField(default=False)

    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True)
    orden_compra = models.ForeignKey(OrdenCompra, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.titulo} - {self.fecha.date()}"