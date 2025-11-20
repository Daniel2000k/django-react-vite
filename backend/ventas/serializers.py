from rest_framework import serializers
from .models import Venta, DetalleVenta
from inventario.serializers import ProductoSerializer


# ===========================
# DETALLE DE VENTA SERIALIZER
# ===========================
class DetalleVentaSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    producto_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = DetalleVenta
        fields = ['id', 'producto', 'producto_id', 'cantidad', 'precio_unitario', 'subtotal']

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0")
        return value

    def validate_precio_unitario(self, value):
        if value < 0:
            raise serializers.ValidationError("El precio unitario no puede ser negativo")
        return value


# ===========================
# VENTA SERIALIZER
# ===========================
class VentaSerializer(serializers.ModelSerializer):
    detalles = DetalleVentaSerializer(many=True, read_only=True)
    usuario = serializers.StringRelatedField(read_only=True)
    fecha_formateada = serializers.SerializerMethodField()

    class Meta:
        model = Venta
        fields = [
            'id',
            'fecha',
            'fecha_formateada',
            'total',
            'metodo_pago',
            'monto_recibido',
            'cambio',
            'descuento_general',
            'iva_porcentaje',
            'iva_total',
            'total_final',
            'usuario',
            'detalles'
        ]
        read_only_fields = ['id', 'fecha', 'usuario', 'detalles']

    def get_fecha_formateada(self, obj):
        """Retorna la fecha en formato legible"""
        return obj.fecha.strftime("%d/%m/%Y %H:%M:%S")

    def validate_descuento_general(self, value):
        if value < 0:
            raise serializers.ValidationError("El descuento no puede ser negativo")
        return value

    def validate_monto_recibido(self, value):
        if value < 0:
            raise serializers.ValidationError("El monto recibido no puede ser negativo")
        return value

    def validate_iva_porcentaje(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("El porcentaje de IVA debe estar entre 0 y 100")
        return value


# ===========================
# VENTA CREAR SERIALIZER (para POST)
# ===========================
class VentaCrearSerializer(serializers.Serializer):
    """Serializer para crear ventas con detalles"""
    metodo_pago = serializers.ChoiceField(
        choices=['EFECTIVO', 'TARJETA', 'TRANSFERENCIA'],
        default='EFECTIVO'
    )
    monto_recibido = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    descuento_general = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    iva_porcentaje = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=19.0)
    detalles = DetalleVentaSerializer(many=True)

    def validate_detalles(self, value):
        if not value:
            raise serializers.ValidationError("Debe agregar al menos un producto")
        return value
