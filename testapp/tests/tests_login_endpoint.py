import json
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token

import pytest


@pytest.mark.django_db(transaction=True)
class TestLoginEndpoint:
    client = Client()

    def test_login_successful(self):
        token = self._create_user_token('username', 'password')

        request = self.client.post(
            path=reverse('cklauth:login'),
            data=json.dumps({
                'username': 'username',
                'password': 'password'
            }),
            content_type='application/json'
        )

        content = json.loads(request.content)

        assert request.status_code == status.HTTP_200_OK
        assert content['token'] == token.key

    def test_login_invalid_payload(self):
        request = self.client.post(
            path=reverse('cklauth:login'),
            data=json.dumps({
                'username': 'username'
            }),
            content_type='application/json'
        )

        content = json.loads(request.content)

        assert request.status_code == status.HTTP_400_BAD_REQUEST
        assert content['message'] == {'password': ['This field is required.']}

    def test_login_wrong_password(self):
        token = self._create_user_token('username', 'password')

        request = self.client.post(
            path=reverse('cklauth:login'),
            data=json.dumps({
                'username': 'username',
                'password': 'wrong_password'
            }),
            content_type='application/json'
        )

        content = json.loads(request.content)

        assert request.status_code == status.HTTP_401_UNAUTHORIZED
        assert content['message'] == 'Wrong credentials.'

    def _create_user_token(self, username, password):
        user = User.objects.create_user(
            username=username,
            password=password
        )
        token = Token.objects.create(user=user)

        return token

