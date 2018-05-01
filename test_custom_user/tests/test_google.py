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
        email='user@email.com',
        password='secret',
        full_name='Test Tester',
    )
    SocialAccount.objects.create(
        user=user,
        google_id='114530204813906326950'
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
def mock_google_get(mocker):
    def get(url, *args, **kwargs):
        if url == constants.GOOGLE_USER_URL:
            return MockResponse(
                {
                    'id': '114530204813906326950',
                    'name': 'test tester',
                    'given_name': 'test',
                    'family_name': 'tester',
                    'link': 'https://google.com',
                    'email': 'user@email.com',
                    'picture': 'http://www.qygjxz.com/data/out/179/5235358-picture.jpg',
                    'gender': 'male',
                    'locale': 'pt-BR'
                },
                200
            )
        return requests.get(url, *args, **kwargs)

    mocked_get = mocker.patch.object(requests, 'get', autospec=True)
    mocked_get.side_effect = get
    return mocked_get


@pytest.fixture
def mock_google_post(mocker):
    def post(url, *args, **kwargs):
        if url == constants.GOOGLE_TOKEN_URL:
            return MockResponse(
                {
                    'access_token': (
                        'ya29.GlvOBBTI1jDVMPLRb1v25Dmwa1XdzG4WOrNW_9orJdtxaYQ-1HOgN0pMWGsL-nYgFL4L'
                        'GE46IDZegLnonZDna0VaKCbxPhD1B3-uLX-hMrbgaUXTxfnZCPHBja7T'
                    ),
                    'expires_in': 3600,
                    'id_token': (
                        'eyJhbGciOiJSUzI1NiIsImtpZCI6IjhiYjJmMGNkOGZkYjlkNGE5YTMwZmMyN2U2ZjU3M2UxN'
                        'TdiMzY1NWMifQ.eyJhenAiOiIzMTU5MTQ0NjMxMjUtaDc1aGZqYWFxY3FzaGJwOWdyNjhxbTh'
                        'kMTh2dWE4MW0uYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJhdWQiOiIzMTU5MTQ0NjMx'
                        'MjUtaDc1aGZqYWFxY3FzaGJwOWdyNjhxbThkMTh2dWE4MW0uYXBwcy5nb29nbGV1c2VyY29ud'
                        'GVudC5jb20iLCJzdWIiOiIxMTQ1MzAyMDQ4MTM5MDYzMjY5NTAiLCJoZCI6ImNrbC5pbyIsIm'
                        'VtYWlsIjoicGVkcm9zZXR0aUBja2wuaW8iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiYXRfaGF'
                        'zaCI6IlZTZUx3V3l1XzJaV0N6WUVkdE1YMGciLCJpc3MiOiJhY2NvdW50cy5nb29nbGUuY29t'
                        'IiwiaWF0IjoxNTA2MTA4MTM2LCJleHAiOjE1MDYxMTE3MzZ9.LFkFTICvxpb4bdNP-CGBu0Ec'
                        'gMn3FDFhTl2xTajJdJ7BfwvxzKAZb17u8eEl2d7QWf8TbbN3CQF6892MlMs4WT3OD5hkMxUKL'
                        '8ssX7cWZav__JWi_6IVee3dfVOzhGt_15aYrdq7TOE1gR6F9vEKLf5RcFf5LA0afu4ZEt24p-'
                        'iguMp6JXoS9BdKeCXBBsr4nbTfJPud8qfhso4gpAdjgIQcD3bAfs3C9zvHl5sOfNHSitbsQZK'
                        'XTqlHo-AmzMY9N8jALhjzuEcxJuQu4nSpipO7PWlmcxr9A2G3lfFVVgchEvslFfXqmvIG1HVg'
                        '40H3k2nD8783gKz7UoSo-OKlMN'
                    ),
                    'token_type': 'Bearer'
                },
                200
            )
        return requests.post(url, *args, **kwargs)

    mocked_post = mocker.patch.object(requests, 'post', autospec=True)
    mocked_post.side_effect = post
    return mocked_post


@pytest.mark.django_db
def test_register_with_google(client, mock_google_post, mock_google_get):
    payload = {
        'code': '4/bmqYo8h-LqR_ahQNrFM9w6QjiiacFVdiRaebGt-TR1A#',
    }
    request = client.post(path=reverse('cklauth:google'), data=payload)

    content = json.loads(request.content.decode('utf-8'))

    user = User.objects.get(email='user@email.com')
    token = Token.objects.get(user=user)

    assert request.status_code == status.HTTP_201_CREATED
    assert content['token'] == token.key


@pytest.mark.django_db
def test_login_with_google(client, mock_google_post, mock_google_get):
    token = create_token()

    payload = {
        'code': '4/bmqYo8h-LqR_ahQNrFM9w6QjiiacFVdiRaebGt-TR1A#',
    }
    request = client.post(path=reverse('cklauth:google'), data=payload)

    content = json.loads(request.content.decode('utf-8'))

    assert request.status_code == status.HTTP_200_OK
    assert content['token'] == token.key
