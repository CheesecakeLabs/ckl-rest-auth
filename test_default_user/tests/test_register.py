import json

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token


User = get_user_model()


@pytest.mark.django_db()
def test_register_successful(client):
    request = client.post(
        path=reverse('cklauth:register'),
        data=json.dumps({
            'username': 'username',
            'email': 'email@email.com',
            'password': 'password'
        }),
        content_type='application/json'
    )

    content = json.loads(request.content.decode('utf-8'))

    assert request.status_code == status.HTTP_201_CREATED

    user = User.objects.get(username='username')
    assert content['token'] == Token.objects.get(user=user).key
    assert content['user']['id'] == user.id


@pytest.mark.django_db()
def test_register_invalid_payload(client):
    request = client.post(
        path=reverse('cklauth:register'),
        data=json.dumps({
            'username': 'username',
            'email': 'email@email.com'
        }),
        content_type='application/json'
    )

    content = json.loads(request.content.decode('utf-8'))

    assert request.status_code == status.HTTP_400_BAD_REQUEST
    assert content == {'password': ['This field is required.']}


@pytest.mark.django_db()
def test_register_username_already_registered(client, settings):
    user = User.objects.create_user(
        username='username',
        email='email@email.com',
        password='password'
    )

    request = client.post(
        path=reverse('cklauth:register'),
        data=json.dumps({
            'username': 'username',
            'email': 'email@email.com',
            'password': 'password'
        }),
        content_type='application/json'
    )

    content = json.loads(request.content.decode('utf-8'))

    assert request.status_code == status.HTTP_400_BAD_REQUEST
    assert settings.CKL_REST_AUTH['LOGIN_FIELD'] in content.keys()


@pytest.mark.django_db()
def test_register_additional_fields(client, settings):
    setattr(settings, 'CKL_REST_AUTH', {
        **settings.CKL_REST_AUTH,
        'REGISTER_FIELDS': ('username', 'email', 'first_name', 'last_name'),
    })

    # Reload serializers to make sure the updated settings are applied
    import cklauth.api.v1.serializers
    from imp import reload
    reload(cklauth.api.v1.serializers)


    request = client.post(
        path=reverse('cklauth:register'),
        data=json.dumps({
            'username': 'username',
            'email': 'email@email.com',
            'password': 'password',
            'first_name': 'CKL',
            'last_name': 'Auth',
        }),
        content_type='application/json'
    )

    content = json.loads(request.content.decode('utf-8'))

    assert request.status_code == status.HTTP_201_CREATED

    user = User.objects.get(username='username')
    assert content['token'] == Token.objects.get(user=user).key
    assert content['user']['id']  == user.id
    assert user.first_name == 'CKL'
    assert user.last_name == 'Auth'
