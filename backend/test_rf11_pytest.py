import pytest
from django.urls import reverse

from accounts.models import User
from inventario.models import Producto


@pytest.mark.django_db
def test_rf11_generate_reports_and_low_stock(client):
    admin = User.objects.create_user(username='admin11', email='admin11@test.com', password='p', rol='ADMIN')
    client.force_login(admin)

    # create one low-stock product
    p = Producto.objects.create(codigo=1111, nombre='ProdLow', stock=2, precio_compra=1.0, precio_venta=2.0)

    # Dashboard and bajo_stock report
    resp = client.get(reverse('reportes:dashboard'))
    assert resp.status_code == 200

    resp2 = client.get(reverse('reportes:productos_bajo_stock') + '?threshold=5')
    assert resp2.status_code == 200
    assert 'ProdLow' in resp2.content.decode('utf-8')
