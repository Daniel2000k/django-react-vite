import pytest
from django.urls import reverse

from accounts.models import User


@pytest.mark.django_db
def test_rf13_login_success_and_failures(client):
    # create user
    u = User.objects.create_user(username='u13', email='u13@test.com', password='pw13', rol='CAJERO')

    # successful login should redirect
    resp = client.post(reverse('login'), data={'email': 'u13@test.com', 'password': 'pw13'})
    assert resp.status_code in (302, 303)

    # incorrect password -> renders with status 200 (no redirect)
    resp2 = client.post(reverse('login'), data={'email': 'u13@test.com', 'password': 'wrong'})
    assert resp2.status_code == 200

    # non-existent user -> status 200 and no redirect
    resp3 = client.post(reverse('login'), data={'email': 'doesnotexist@test.com', 'password': 'x'})
    assert resp3.status_code == 200
