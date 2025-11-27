import pytest

from decimal import Decimal

from accounts.models import User
from inventario.models import Producto, Proveedor, OrdenCompra
from ventas.models import Venta, DetalleVenta
from devoluciones.models import Devolucion


@pytest.mark.django_db
def test_rf16_product_creation_and_inventory_movements():
    # create product with zero stock
    prod = Producto.objects.create(codigo=1601, nombre='Prod16', stock=0, precio_compra=Decimal('2.00'), precio_venta=Decimal('5.00'))

    # ENTRADA movement increases stock
    from inventario.models import Inventario
    e = Inventario.objects.create(producto=prod, tipo='ENTRADA', cantidad=5, numero_referencia='ENT-1')
    prod.refresh_from_db()
    assert prod.stock == 5

    # SALIDA movement decreases stock
    s = Inventario.objects.create(producto=prod, tipo='SALIDA', cantidad=3, numero_referencia='SAL-1')
    prod.refresh_from_db()
    assert prod.stock == 2

    # deleting an inventory movement should revert stock
    s.delete()
    prod.refresh_from_db()
    assert prod.stock == 5
