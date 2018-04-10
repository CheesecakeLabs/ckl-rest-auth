import json
import mock
import pytest

from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
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

    if args[0] == constants.GOOGLE_USER_URL:
        return MockResponse(
            {
                "id": "114530204813906326950",
                "name": "test test2",
                "given_name": "test",
                "family_name": "test2",
                "link": "https://google.com",
                "email": "email@ckl.io",
                "picture": "http://www.qygjxz.com/data/out/179/5235358-picture.jpg",
                "gender": "male",
                "locale": "pt-BR"
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

    if args[0] == constants.GOOGLE_TOKEN_URL:
        return MockResponse(
            {
                "access_token": "ya29.GlvOBBTI1jDVMPLRb1v25Dmwa1XdzG4WOrNW_9orJdtxaYQ-1HOgN0pMWGsL-nYgFL4LGE46IDZegLnonZDna0VaKCbxPhD1B3-uLX-hMrbgaUXTxfnZCPHBja7T",
                "expires_in": 3600,
                "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjhiYjJmMGNkOGZkYjlkNGE5YTMwZmMyN2U2ZjU3M2UxNTdiMzY1NWMifQ.eyJhenAiOiIzMTU5MTQ0NjMxMjUtaDc1aGZqYWFxY3FzaGJwOWdyNjhxbThkMTh2dWE4MW0uYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJhdWQiOiIzMTU5MTQ0NjMxMjUtaDc1aGZqYWFxY3FzaGJwOWdyNjhxbThkMTh2dWE4MW0uYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJzdWIiOiIxMTQ1MzAyMDQ4MTM5MDYzMjY5NTAiLCJoZCI6ImNrbC5pbyIsImVtYWlsIjoicGVkcm9zZXR0aUBja2wuaW8iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiYXRfaGFzaCI6IlZTZUx3V3l1XzJaV0N6WUVkdE1YMGciLCJpc3MiOiJhY2NvdW50cy5nb29nbGUuY29tIiwiaWF0IjoxNTA2MTA4MTM2LCJleHAiOjE1MDYxMTE3MzZ9.LFkFTICvxpb4bdNP-CGBu0EcgMn3FDFhTl2xTajJdJ7BfwvxzKAZb17u8eEl2d7QWf8TbbN3CQF6892MlMs4WT3OD5hkMxUKL8ssX7cWZav__JWi_6IVee3dfVOzhGt_15aYrdq7TOE1gR6F9vEKLf5RcFf5LA0afu4ZEt24p-iguMp6JXoS9BdKeCXBBsr4nbTfJPud8qfhso4gpAdjgIQcD3bAfs3C9zvHl5sOfNHSitbsQZKXTqlHo-AmzMY9N8jALhjzuEcxJuQu4nSpipO7PWlmcxr9A2G3lfFVVgchEvslFfXqmvIG1HVg40H3k2nD8783gKz7UoSo-OKlMN",
                "token_type": "Bearer"
            }
            ,
            200
        )
    return MockResponse({}, 404)


@pytest.mark.django_db(transaction=True)
class TestLoginEndpoint:
    client = Client()

    def test_register_with_google(self):
        mock.patch('requests.post', side_effect=mocked_requests_post).start()
        patch = mock.patch('requests.get', side_effect=mocked_requests_get).start()
        payload = {
            'code': '4/bmqYo8h-LqR_ahQNrFM9w6QjiiacFVdiRaebGt-TR1A#',
        }
        request = self.client.post(path=reverse('cklauth:google'), data=payload)
        patch.stop()

        content = json.loads(request.content.decode('utf-8'))

        user = User.objects.first()
        token = Token.objects.get(user=user)

        assert request.status_code == status.HTTP_201_CREATED
        assert content['token'] == token.key

    def test_login_with_google(self):
        token = self._create_user_token('test_test2', 'email@ckl.io', 'password')
        mock.patch('requests.post', side_effect=mocked_requests_post).start()
        patch = mock.patch('requests.get', side_effect=mocked_requests_get).start()
        payload = {
            'code': '4/bmqYo8h-LqR_ahQNrFM9w6QjiiacFVdiRaebGt-TR1A#',
        }
        request = self.client.post(path=reverse('cklauth:google'), data=payload)
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
            google_id='114530204813906326950'
        )
        token = Token.objects.create(user=user)

        return token

