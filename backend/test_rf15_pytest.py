import pytest
from django.urls import reverse
from decimal import Decimal

from accounts.models import User
from inventario.models import Producto, Proveedor, Inventario
from compras.models import Compra, DetalleCompra


@pytest.mark.django_db
def test_rf15_create_purchase_receive_and_list(client):
    admin = User.objects.create_user(username='adm15', email='adm15@test.com', password='p', rol='ADMIN')
    client.force_login(admin)

    prov = Proveedor.objects.create(nombre='Prov15', telefono='t', direccion='d', correo='prov15@test.com')
    prod = Producto.objects.create(codigo=1501, nombre='Prod15', stock=0, precio_compra=Decimal('2.00'), precio_venta=Decimal('5.00'))

    # create compra via POST
    url = reverse('compra_crear')
    data = {
        'proveedor': str(prov.id),
        'producto_id[]': [str(prod.id)],
        'cantidad[]': ['4'],
        'precio_unitario[]': ['2.00']
    }
    resp = client.post(url, data=data)
    assert resp.status_code in (302, 303)

    # Compra created
    assert Compra.objects.exists()
    compra = Compra.objects.first()
    assert compra.total == Decimal('8.00')

    # inventory entry created and product stock updated
    inv = Inventario.objects.filter(producto=prod, tipo='ENTRADA').last()
    assert inv is not None
    prod.refresh_from_db()
    assert prod.stock == 4

    # list view should include the compra representation
    resp_list = client.get(reverse('compra_lista'))
    assert resp_list.status_code == 200
    assert f"Compra #{compra.id}" in resp_list.content.decode('utf-8')
