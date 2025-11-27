import pytest

from inventario.models import Producto


@pytest.mark.django_db
def test_producto_create():
    # Create a product and ensure it is saved and string repr works
    p = Producto.objects.create(
        codigo=999999,
        nombre='TEST_PRODUCT',
        precio_compra=1.0,
        precio_venta=2.0,
        stock=5,
    )

    assert Producto.objects.filter(codigo=999999).exists()
    # __str__ returns name and code
    assert 'TEST_PRODUCT' in str(p)
