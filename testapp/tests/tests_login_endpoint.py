import json

from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token

import pytest


User = get_user_model()


@pytest.mark.django_db(transaction=True)
class TestLoginEndpoint:
    client = Client()

    def test_login_successful(self):
        token = self._create_user_token('username', 'email@ckl.io', 'password')

        request = self.client.post(
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
        assert content['token'] == token.key

    def test_login_invalid_payload(self):
        request = self.client.post(
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

    def test_login_wrong_password(self):
        token = self._create_user_token('username', 'email@ckl.io', 'password')

        request = self.client.post(
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
        assert content['message'] == 'Wrong credentials.'

    @staticmethod
    def _create_user_token(username, email, password):
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        token = Token.objects.create(user=user)

        return token

