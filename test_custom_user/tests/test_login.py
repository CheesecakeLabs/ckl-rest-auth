import json

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token


User = get_user_model()


def create_user(alias='1'):
    email = 'email-{}@test.com'.format(alias)
    password = 'secret'
    full_name='Test{} Tester'.format(alias)

    return (
        User.objects.create_user(
            email=email,
            password=password,
            full_name=full_name,
        ),
        {'email': email, 'password': password, 'full_name': full_name}
    )


@pytest.mark.django_db()
def test_login_successful(client, settings):
    user, user_fields = create_user()

    request = client.post(
        path=reverse('cklauth:login'),
        data=json.dumps({
            'email': user_fields['email'],
            'password': user_fields['password'],
        }),
        content_type='application/json'
    )

    content = json.loads(request.content.decode('utf-8'))

    assert request.status_code == status.HTTP_200_OK
    assert content['token'] == Token.objects.get(user=user).key
    assert content['user']['id'] == user.id


@pytest.mark.django_db()
def test_login_invalid_payload(client):
    request = client.post(
        path=reverse('cklauth:login'),
        data=json.dumps({
            'email': 'user@test.com',
        }),
        content_type='application/json'
    )

    content = json.loads(request.content.decode('utf-8'))

    assert request.status_code == status.HTTP_400_BAD_REQUEST
    assert content == {'password': ['This field is required.']}


@pytest.mark.django_db()
def test_login_wrong_password(client):
    _, user_fields = create_user()

    user_fields.update({'password': 'wrong_password'})
    del user_fields['full_name']

    request = client.post(
        path=reverse('cklauth:login'),
        data=json.dumps(user_fields),
        content_type='application/json'
    )

    content = json.loads(request.content.decode('utf-8'))

    assert request.status_code == status.HTTP_401_UNAUTHORIZED
    assert content['non_field_errors'] == ['Wrong credentials.']
