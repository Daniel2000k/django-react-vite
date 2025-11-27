import pytest
from decimal import Decimal

from accounts.models import User
from inventario.models import Producto, Inventario
from ventas.models import Venta, DetalleVenta
from devoluciones.models import Devolucion


@pytest.mark.django_db
def test_rf12_register_return_updates_stock_and_inventory():
    u = User.objects.create_user(username='r12', email='r12@test.com', password='p', rol='CAJERO')
    p = Producto.objects.create(codigo=1211, nombre='ProdReturn', stock=5, precio_compra=Decimal('2.00'), precio_venta=Decimal('5.00'))

    venta = Venta.objects.create(usuario=u, metodo_pago='EFECTIVO', total_final=Decimal('10.00'))
    detalle = DetalleVenta.objects.create(venta=venta, producto=p, cantidad=2, precio_unitario=Decimal('5.00'), subtotal=Decimal('10.00'))

    dev = Devolucion.objects.create(venta=venta, detalle_venta=detalle, producto=p, cantidad=1, motivo='defect', usuario=u)

    # Devolucion should create an Inventario ENTRADA and increment stock
    inv = Inventario.objects.filter(producto=p, tipo='ENTRADA').last()
    assert inv is not None
    assert inv.cantidad == 1

    p.refresh_from_db()
    assert p.stock == 6
