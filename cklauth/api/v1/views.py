import json
import requests

from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.shortcuts import redirect
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView

from .serializers import RegisterSerializer, LoginSerializer
from cklauth.models import SocialAccount

from .serializers import RegisterSerializer

# Settings
GOOGLE_CLIENT_ID = 'something'
GOOGLE_CLIENT_SECRET = 'something'
GOOGLE_REDIRECT_URI = 'something'
###
GOOGLE_TOKEN_URL = 'https://accounts.google.com/o/oauth2/token'
GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/auth'
GOOGLE_USER_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'

# Settings
FACEBOOK_CLIENT_ID = 'something'
FACEBOOK_CLIENT_SECRET = 'something'
FACEBOOK_REDIRECT_URI = 'something'
###
FACEBOOK_TOKEN_URL = 'https://graph.facebook.com/oauth/access_token'
FACEBOOK_AUTH_URL = 'https://www.facebook.com/v2.12/dialog/oauth?'
FACEBOOK_USER_URL = 'https://graph.facebook.com/v2.11/me'


@api_view(['POST',])
def register(request):
    serializer = RegisterSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)
    serializer.save()

    return JsonResponse({
        'message': 'Ok.'
    }, status=status.HTTP_201_CREATED)


@api_view(['POST',])
def login(request):
    serializer = LoginSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)
    user = authenticate(
        username=serializer.data['username'],
        password=serializer.data['password']
    )

    if user:
        token = Token.objects.get(user=user)

        return JsonResponse({
            'token': token.key
        }, status=status.HTTP_200_OK)

    return JsonResponse({
        'message': 'Wrong credentials.'
    }, status=status.HTTP_401_UNAUTHORIZED)


class GoogleAuthView(APIView):
    permission_classes = []

    AUTH_URL = GOOGLE_AUTH_URL
    TOKEN_URL = GOOGLE_TOKEN_URL
    USER_URL = GOOGLE_USER_URL

    def get(self, request, format=None):
        # Check link below to retrieve info wanted
        # https://developers.google.com/gmail/api/auth/scopes
        payload = {
            'response_type': 'code',
            'client_id': GOOGLE_CLIENT_ID,
            'redirect_uri': GOOGLE_REDIRECT_URI,
            'scope': 'https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email',
            'state': json.dumps(request.query_params),
        }
        request = requests.Request('GET', self.AUTH_URL, params=payload).prepare()
        return redirect(request.url)

    def post(self, request):
        if not request.data.get('code'):
            return JsonResponse({
                'message': 'Missing auth token'
            }, status=status.HTTP_400_BAD_REQUEST)

        payload = {
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'redirect_uri': GOOGLE_REDIRECT_URI,
            'code': request.data['code'],
        }

        response = requests.post(self.TOKEN_URL, data=payload)

        if response.status_code != status.HTTP_200_OK:
            return JsonResponse({
                'message': 'Google bad token'
            }, status=status.HTTP_400_BAD_REQUEST)

        access_token = response.json()['access_token']

        response = requests.get(self.USER_URL, headers={
            'Authorization': 'Bearer %s' % access_token})

        if response.status_code != status.HTTP_200_OK:
            return JsonResponse({
                'message': 'Cannot get google info'
            }, status=status.HTTP_401_UNAUTHORIZED)

        data = response.json()

        try:
            # email registered with social account
            social_account = SocialAccount.objects.get(user__email=data.get('email'))
            user = social_account.user
            if not social_account.google_id:
                social_account.google_id = data.get('id')
                social_account.save()
        except SocialAccount.DoesNotExist:
            try:
                # email registered without social account
                User.objects.get(email=data.get('email'))
                return JsonResponse({
                        'message': 'Registered with email'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                # user and social account don't exist
                username = get_username(
                    username='{0}_{1}'.format(
                        data.get('given_name').lower(),
                        data.get('family_name').lower()
                    )
                )
                user = User.objects.create_user(
                    username=username,
                    email=data.get('email'),
                    first_name=data.get('given_name'),
                    last_name=data.get('family_name'),
                )
                SocialAccount.objects.create(
                    user=user,
                    google_id=data.get('id')
                )

        token = Token.objects.get(user=user)
        return JsonResponse({
            'token': token.key
        }, status=status.HTTP_200_OK)


# https://developers.facebook.com/docs/facebook-login/manually-build-a-login-flow
class FacebookAuthView(APIView):
    permission_classes = []

    AUTH_URL = FACEBOOK_AUTH_URL
    TOKEN_URL = FACEBOOK_TOKEN_URL
    USER_URL = FACEBOOK_USER_URL

    def get_username(self, username, first_name, last_name, count=0):
        user = User.objects.get(username=username)
        if user:
            count = count + 1
            username = '{0}_{1}_{2}'.format(
                first_name.lower(),
                last_name.lower(),
                count
            )
            self.get_username(username=username, first_name=first_name, last_name=last_name, count=count)
        return username

    def get(self, request, format=None):
        payload = {
            'response_type': 'code',
            'client_id': FACEBOOK_CLIENT_ID,
            'redirect_uri': FACEBOOK_REDIRECT_URI,
            'state': json.dumps(request.query_params),
            'scope': 'email',
        }
        request = requests.Request('GET', self.AUTH_URL, params=payload).prepare()
        return redirect(request.url)

    def post(self, request):
        if not request.data.get('code'):
            return JsonResponse({
                'message': 'Missing auth token'
            }, status=status.HTTP_400_BAD_REQUEST)

        payload = {
            'client_id': FACEBOOK_CLIENT_ID,
            'client_secret': FACEBOOK_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'redirect_uri': FACEBOOK_REDIRECT_URI,
            'code': request.data['code'],
        }

        response = requests.post(self.TOKEN_URL, data=payload)

        if response.status_code != status.HTTP_200_OK:
            return JsonResponse({
                'message': 'Facebook bad token'
            }, status=status.HTTP_400_BAD_REQUEST)

        access_token = response.json()['access_token']

        response = requests.get(self.USER_URL, headers={
            'Authorization': 'Bearer %s' % access_token}, params={'fields': {'email', 'first_name', 'last_name'}})

        if response.status_code != status.HTTP_200_OK:
            return JsonResponse({
                'message': 'Cannot get facebook info'
            }, status=status.HTTP_401_UNAUTHORIZED)

        data = response.json()

        try:
            # email registered with social account
            social_account = SocialAccount.objects.get(user__email=data.get('email'))
            user = social_account.user
            if not social_account.google_id:
                social_account.google_id = data.get('id')
                social_account.save()
        except SocialAccount.DoesNotExist:
            try:
                # email registered without social account
                User.objects.get(email=data.get('email'))
                return JsonResponse({
                        'message': 'Registered with email'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                # user and social account don't exist
                username = get_username(
                    username='{0}_{1}'.format(
                        data.get('first_name').lower(),
                        data.get('last_name').lower()
                    )
                )
                user = User.objects.create_user(
                    username=username,
                    email=data.get('email'),
                    first_name=data.get('first_name'),
                    last_name=data.get('last_name'),
                )
                SocialAccount.objects.create(
                    user=user,
                    google_id=data.get('id')
                )

        token = Token.objects.get(user=user)
        return JsonResponse({
            'token': token.key
        }, status=status.HTTP_200_OK)


def get_username(username, current_username=None, count=0):
    user = User.objects.get(username=username)
    if user:
        count = count + 1
        current_username = '{0}_{1}'.format(
            username,
            count
        )
        get_username(username=username, current_username=current_username, count=count)
    return current_username
