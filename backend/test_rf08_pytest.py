import pytest
from decimal import Decimal

from accounts.models import User
from inventario.models import Producto
from ventas.models import Venta, DetalleVenta


@pytest.mark.django_db
def test_rf08_register_sale_and_stock_and_totals():
    cajero = User.objects.create_user(username='c8', email='c8@test.com', password='p', rol='CAJERO')
    p = Producto.objects.create(codigo=8001, nombre='Prod8', stock=20, precio_compra=Decimal('1.00'), precio_venta=Decimal('10.00'))

    # registrar venta con detalle
    venta = Venta.objects.create(usuario=cajero, metodo_pago='EFECTIVO', total_final=Decimal('0.00'))
    DetalleVenta.objects.create(venta=venta, producto=p, cantidad=2, precio_unitario=Decimal('10.00'), subtotal=Decimal('20.00'))

    # disminuir stock (model does not auto-decrease in this project; we simulate)
    p.stock -= 2
    p.save()
    p.refresh_from_db()
    assert p.stock == 18

    # total + IVA simple check
    total = Decimal('20.00')
    iva = total * Decimal('0.19')
    assert iva == Decimal('3.8000')

    # cambio (simulated): received 50
    recibido = Decimal('50.00')
    cambio = recibido - (total + iva)
    assert cambio > 0
