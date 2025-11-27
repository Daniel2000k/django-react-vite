import pytest

from accounts.models import User


@pytest.mark.django_db
def test_rf10_user_creation_and_roles():
    u = User.objects.create_user(username='u10', email='u10@test.com', password='p', rol='ADMIN')
    assert u.email == 'u10@test.com'
    assert u.rol == 'ADMIN'

    # change role
    u.rol = 'CAJERO'
    u.save()
    u.refresh_from_db()
    assert u.rol == 'CAJERO'


@pytest.mark.django_db
def test_rf10_access_control_for_admin_views(client):
    # normal user should not access admin-only pages
    normal = User.objects.create_user(username='normal10', email='n10@test.com', password='p', rol='CAJERO')
    client.force_login(normal)

    from django.urls import reverse
    # proveedor_crear is admin-only
    resp = client.get(reverse('proveedor_crear'))
    # redirected to login or not allowed
    assert resp.status_code in (302, 403)

    # admin can access
    admin = User.objects.create_user(username='admin10', email='a10@test.com', password='p', rol='ADMIN')
    client.force_login(admin)
    resp2 = client.get(reverse('proveedor_crear'))
    assert resp2.status_code == 200
