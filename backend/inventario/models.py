from django.db import models
from django.utils import timezone

# ===========================
# MODELO PROVEEDOR
# ===========================
class Proveedor(models.Model):
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=200)
    correo = models.EmailField(unique=True)#para la validacion de correo unico

    def __str__(self):
        return self.nombre


# ===========================
# PRODUCTO
# ===========================
class Producto(models.Model):
    codigo = models.IntegerField(unique=True)
    nombre = models.CharField(max_length=100)
    stock = models.IntegerField(default=0)
    precio_compra = models.DecimalField(max_digits=15, decimal_places=3)
    precio_venta = models.DecimalField(max_digits=15, decimal_places=3)
    activo = models.BooleanField(default=True)  # Para desactivar sin eliminar

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
    costo_unitario = models.DecimalField(max_digits=15, decimal_places=3)
    subtotal = models.DecimalField(max_digits=15, decimal_places=3)

    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_recepcion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"OC-{self.id} | {self.producto.nombre} x {self.cantidad}"

    def recibir(self):
        if self.estado != 'RECIBIDA':
            self.producto.stock += self.cantidad
            self.producto.save()
            self.estado = 'RECIBIDA'
            self.fecha_recepcion = timezone.now()
            self.save()
            # Nota: creación de alertas tipo 'COMPRA' desactivada por petición. Si se necesita
            # reactivar, restaurar la llamada a AlertaInventario.objects.create(...)


# ===========================
# MOVIMIENTOS DE INVENTARIO
# ===========================
class Inventario(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="movimientos")
    tipo = models.CharField(max_length=10, choices=[('ENTRADA', 'Entrada'), ('SALIDA', 'Salida')])
    cantidad = models.IntegerField()
    numero_referencia = models.CharField(max_length=20, unique=True, blank=True, null=True)
    fecha = models.DateTimeField(default=timezone.now)

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
