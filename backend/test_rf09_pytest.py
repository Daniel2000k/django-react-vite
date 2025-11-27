import pytest
from decimal import Decimal
from django.urls import reverse

from accounts.models import User
from ventas.models import Venta, DetalleVenta


@pytest.mark.django_db
def test_rf09_generate_and_access_invoice_pdf(client):
    # create a cajero user and sale with a detail
    caj = User.objects.create_user(username='rf09', email='rf09@test.com', password='p', rol='CAJERO')
    venta = Venta.objects.create(usuario=caj, metodo_pago='TARJETA', total_final=Decimal('42.00'))
    DetalleVenta.objects.create(venta=venta, producto=None, producto_nombre='X', producto_codigo='999', cantidad=1, precio_unitario=Decimal('42.00'), subtotal=Decimal('42.00'))

    # logged in as same user should be able to get factura PDF
    client.force_login(caj)
    url = reverse('venta_factura_pdf', args=[venta.id])
    resp = client.get(url)
    assert resp.status_code == 200
    assert 'application/pdf' in resp['Content-Type']
    # venta exists and saved
    assert Venta.objects.filter(id=venta.id).exists()
