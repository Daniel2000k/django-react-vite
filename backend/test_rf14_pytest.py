import pytest
from django.urls import reverse

from accounts.models import User


@pytest.mark.django_db
def test_rf14_register_user_and_prevent_duplicates(client):
    # Successful registration
    resp = client.post(reverse('register'), data={'email': 'r14@test.com', 'username': 'ruser14', 'password': 'password123', 'password_confirm': 'password123'})
    # should redirect to login on success
    assert resp.status_code in (302, 303)
    assert User.objects.filter(email='r14@test.com').exists()

    # Attempt duplicate email - should not create new account
    resp2 = client.post(reverse('register'), data={'email': 'r14@test.com', 'username': 'other14', 'password': 'password456', 'password_confirm': 'password456'})
    assert resp2.status_code == 200
    assert User.objects.filter(email='r14@test.com').count() == 1

    # Attempt duplicate username - should not create new account
    resp3 = client.post(reverse('register'), data={'email': 'new14@test.com', 'username': 'ruser14', 'password': 'password789', 'password_confirm': 'password789'})
    assert resp3.status_code == 200
    assert User.objects.filter(username='ruser14').count() == 1
