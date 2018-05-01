import json
import mock

import pytest
import requests
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token

from cklauth import constants
from cklauth.models import SocialAccount

User = get_user_model()


def create_token():
    user = User.objects.create_user(
        email='user@test.com',
        password='secret',
        full_name='Test Tester',
    )
    SocialAccount.objects.create(
        user=user,
        facebook_id='114530204813906326950'
    )
    token = Token.objects.create(user=user)

    return token


class MockResponse:
    def __init__(self, content, status_code):
        self.content = content
        self.status_code = status_code

    def json(self):
        return self.content


@pytest.fixture
def mock_facebook_get(mocker):
    def get(url, *args, **kwargs):
        if url == constants.FACEBOOK_USER_URL:
            return MockResponse(
                {
                    'name': 'Test Tester',
                    'email': 'user@test.com',
                    'first_name': 'test',
                    'last_name': 'tester',
                    'id': '2024821427134319'
                },
                200
            )
        return requests.get(url, *args, **kwargs)

    mocked_get = mocker.patch.object(requests, 'get', autospec=True)
    mocked_get.side_effect = get
    return mocked_get


@pytest.fixture
def mock_facebook_post(mocker):
    def post(url, *args, **kwargs):
        if url == constants.FACEBOOK_TOKEN_URL:
            return MockResponse(
                {
                    'access_token': 'bh1n65vu87q59lkcz3asu2omfs1nje',
                    'expires_in': 3600,
                    'token_type': 'Bearer'
                },
                200
            )
        return requests.post(url, *args, **kwargs)

    mocked_post = mocker.patch.object(requests, 'post', autospec=True)
    mocked_post.side_effect = post
    return mocked_post


@pytest.mark.django_db
def test_register_with_facebook(client, mock_facebook_post, mock_facebook_get):
    payload = {
        'code': '4/bmqYo8h-LqR_ahQNrFM9w6QjiiacFVdiRaebGt-TR1A#',
    }
    request = client.post(path=reverse('cklauth:facebook'), data=payload)

    content = json.loads(request.content.decode('utf-8'))

    user = User.objects.first()
    token = Token.objects.get(user=user)

    assert request.status_code == status.HTTP_201_CREATED
    assert content['token'] == token.key


@pytest.mark.django_db
def test_login_with_facebook(client, mock_facebook_post, mock_facebook_get):
    token = create_token()

    payload = {
        'code': '4/bmqYo8h-LqR_ahQNrFM9w6QjiiacFVdiRaebGt-TR1A#',
    }
    request = client.post(path=reverse('cklauth:facebook'), data=payload)

    content = json.loads(request.content.decode('utf-8'))

    assert request.status_code == status.HTTP_200_OK
    assert content['token'] == token.key
