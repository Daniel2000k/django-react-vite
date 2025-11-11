
from django.db import models
class Proveedor(models.Model):
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=200)
    correo = models.EmailField()

class Producto(models.Model):#representa el catálogo base: nombre, precio, código, marca, etc. es la ficha tecnica del rpoducto
 # la cantidad actual stock pertenece al prducto pero los movimientos que modifican todo son del inventario
    codigo = models.IntegerField(unique=True)#Define que este campo almacenará números enteros. y el (unique=true) es una restriccion #Esta es una restricción clave. Asegura que no puedan existir dos productos con el mismo código.
    nombre = models.CharField(max_length=100)# La cadena charfield se utiliz para guardar cadenas de texto cortas y la restriccion max lengeth obliga que no tenga mas de 100 caracteres
    descripcion= models.TextField(blank=True, null=True)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=3)# esta cadena se utiliza generalmente para dinero  y restinge max 10 digitos y maximos deciamels despues de la coma
    precio_venta = models.DecimalField(max_digits=10, decimal_places=3)# esta cadena se utiliza generalmente para dinero  y restinge max 10 digitos y maximos deciamels despues de la coma
    stock = models.IntegerField(default= 0)

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    
class Inventario(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="movimientos")
    tipo = models.CharField(max_length=10, choices=[('ENTRADA', 'Entrada'), ('SALIDA', 'Salida')])
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
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
    # Evitar modificar stock si el producto ya está siendo eliminado
        if self.producto_id and Producto.objects.filter(id=self.producto_id).exists():
            if self.tipo == 'ENTRADA':
                self.producto.stock -= self.cantidad
            elif self.tipo == 'SALIDA':
                self.producto.stock += self.cantidad
            self.producto.save()
        super().delete(*args, **kwargs)

