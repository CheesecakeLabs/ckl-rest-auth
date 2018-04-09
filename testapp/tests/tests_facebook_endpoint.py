import json
import mock
import pytest

from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model, settings
from rest_framework import status
from rest_framework.authtoken.models import Token

from cklauth import constants
from cklauth.models import SocialAccount

User = get_user_model()


###
# Mock Requests
###
def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if args[0] == constants.FACEBOOK_USER_URL:
        return MockResponse(
            {
                "name": "test test2",
                "email": "email@ckl.io",
                "first_name": "test",
                "last_name": "test2",
                "id": "2024821427134319"
            },
            200
        )

    return MockResponse({}, 404)


def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, text, status_code):
            self.text = text
            self.status_code = status_code

        def json(self):
            return self.text

    if args[0] == constants.FACEBOOK_TOKEN_URL:
        return MockResponse(
            {
                "access_token": "bh1n65vu87q59lkcz3asu2omfs1nje",
                "expires_in": 3600,
                "token_type": "Bearer"
            },
            200
        )
    return MockResponse({}, 404)


@pytest.mark.django_db(transaction=True)
class TestLoginEndpoint:
    client = Client()

    def test_register_with_facebook(self):
        mock.patch('requests.post', side_effect=mocked_requests_post).start()
        patch = mock.patch('requests.get', side_effect=mocked_requests_get).start()
        payload = {
            'code': '4/bmqYo8h-LqR_ahQNrFM9w6QjiiacFVdiRaebGt-TR1A#',
        }
        request = self.client.post(path=reverse('cklauth:facebook'), data=payload)
        patch.stop()

        content = json.loads(request.content.decode('utf-8'))

        user = User.objects.first()
        token = Token.objects.get(user=user)

        assert request.status_code == status.HTTP_201_CREATED
        assert content['token'] == token.key

    def test_login_with_facebook(self):
        token = self._create_user_token('test_test2', 'email@ckl.io', 'password')
        mock.patch('requests.post', side_effect=mocked_requests_post).start()
        patch = mock.patch('requests.get', side_effect=mocked_requests_get).start()
        payload = {
            'code': '4/bmqYo8h-LqR_ahQNrFM9w6QjiiacFVdiRaebGt-TR1A#',
        }
        request = self.client.post(path=reverse('cklauth:facebook'), data=payload)
        patch.stop()

        content = json.loads(request.content.decode('utf-8'))

        assert request.status_code == status.HTTP_200_OK
        assert content['token'] == token.key

    @staticmethod
    def _create_user_token(username, email, password):
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        SocialAccount.objects.create(
            user=user,
            facebook_id='2024821427134319'
        )
        token = Token.objects.create(user=user)

        return token

