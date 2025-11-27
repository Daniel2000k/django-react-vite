import pytest

from accounts.models import User
from inventario.models import Proveedor


@pytest.mark.django_db
def test_rf07_proveedor_crud_and_duplicate():
    # crear proveedor
    p = Proveedor.objects.create(nombre='Proveedor A', correo='a@test.com', telefono='1', direccion='X')
    assert p.id

    # editar
    p.nombre = 'Proveedor A+edited'
    p.save()
    p.refresh_from_db()
    assert p.nombre == 'Proveedor A+edited'

    # duplicado (mismo correo) debe lanzar excepción al guardar
    Proveedor.objects.create(nombre='Proveedor B', correo='b@test.com', telefono='2', direccion='Y')
    from django.db import transaction
    # Ensure DB gets rolled back after the expected IntegrityError so the transaction isn't broken
    with pytest.raises(Exception):
        with transaction.atomic():
            Proveedor.objects.create(nombre='Proveedor C', correo='b@test.com', telefono='3', direccion='Z')

    # eliminar
    pid = p.id
    p.delete()
    assert Proveedor.objects.filter(id=pid).count() == 0
