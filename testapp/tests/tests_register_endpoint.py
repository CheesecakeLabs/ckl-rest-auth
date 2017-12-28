import json
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token

import pytest


@pytest.mark.django_db(transaction=True)
class TestRegisterEndpoint:
    client = Client()

    def test_register_successful(self):
        request = self.client.post(
            path=reverse('cklauth:register'),
            data=json.dumps({
                'username': 'username',
                'email': 'username@email.com',
                'password': 'password'
            }),
            content_type='application/json'
        )

        content = json.loads(request.content)

        assert request.status_code == status.HTTP_201_CREATED
        assert content['message'] == 'Ok.'

        users = User.objects.filter(username='username')

        assert users.count() == 1
        assert Token.objects.filter(user=users.first()).exists() == True

    def test_register_invalid_payload(self):
        request = self.client.post(
            path=reverse('cklauth:register'),
            data=json.dumps({
                'username': 'username',
                'email': 'username@email.com'
            }),
            content_type='application/json'
        )

        content = json.loads(request.content)

        assert request.status_code == status.HTTP_400_BAD_REQUEST
        assert content['message'] == {'password': ['This field is required.']}

    def test_register_username_already_registered(self):
        user = User.objects.create_user(
            username='username',
            email='username@email.com',
            password='password'
        )

        request = self.client.post(
            path=reverse('cklauth:register'),
            data=json.dumps({
                'username': 'username',
                'email': 'username@email.com',
                'password': 'password'
            }),
            content_type='application/json'
        )

        content = json.loads(request.content)

        assert request.status_code == status.HTTP_400_BAD_REQUEST
        assert content['message'] == {'username': ['This username is already in use.']}

