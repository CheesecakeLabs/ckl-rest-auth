import json

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token


User = get_user_model()


@pytest.mark.django_db(transaction=True)
class TestLoginEndpoint:
    @staticmethod
    def _create_user(username, email, password):
        return User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

    def test_login_successful(self, client):
        user = self._create_user('username', 'email@ckl.io', 'password')

        request = client.post(
            path=reverse('cklauth:login'),
            data=json.dumps({
                'username': 'username',
                'email': 'email@ckl.io',
                'password': 'password'
            }),
            content_type='application/json'
        )

        content = json.loads(request.content.decode('utf-8'))

        assert request.status_code == status.HTTP_200_OK
        assert content['token'] == Token.objects.get(user=user).key
        assert content['user']['id'] == user.id

    def test_login_invalid_payload(self, client):
        request = client.post(
            path=reverse('cklauth:login'),
            data=json.dumps({
                'username': 'username',
                'email': 'email@ckl.io'
            }),
            content_type='application/json'
        )

        content = json.loads(request.content.decode('utf-8'))

        assert request.status_code == status.HTTP_400_BAD_REQUEST
        assert content == {'password': ['This field is required.']}

    def test_login_wrong_password(self, client):
        _ = self._create_user('username', 'email@ckl.io', 'password')

        request = client.post(
            path=reverse('cklauth:login'),
            data=json.dumps({
                'username': 'username',
                'email': 'email@ckl.io',
                'password': 'wrong_password'
            }),
            content_type='application/json'
        )

        content = json.loads(request.content.decode('utf-8'))

        assert request.status_code == status.HTTP_401_UNAUTHORIZED
        assert content['non_field_errors'] == ['Wrong credentials.']
