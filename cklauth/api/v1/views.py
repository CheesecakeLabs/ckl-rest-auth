import json
from pydoc import locate

import requests
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.http import JsonResponse
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.views import APIView

from cklauth import constants
from cklauth.models import SocialAccount
from .serializers import RegisterSerializerFactory, LoginSerializer, PasswordResetSerializer


User = get_user_model()
UserSerializer = locate(settings.CKL_REST_AUTH.get('USER_SERIALIZER'))


@api_view(['POST',])
def register(request):
    RegisterSerializer = RegisterSerializerFactory(UserSerializer)

    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user, token = serializer.save()

    return JsonResponse({
        'token': token.key,
        'user': UserSerializer(instance=user).data,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST',])
def login(request):
    fields = [settings.CKL_REST_AUTH['LOGIN_FIELD'], 'password']
    serializer = LoginSerializer(data=request.data, fields=fields)

    serializer.is_valid(raise_exception=True)
    username = serializer.validated_data[settings.CKL_REST_AUTH['LOGIN_FIELD']]
    password = serializer.validated_data['password']
    user = authenticate(username=username, password=password)

    if user:
        token, _ = Token.objects.get_or_create(user=user)

        return JsonResponse({
            'token': token.key,
            'user': UserSerializer(instance=user).data,
        }, status=status.HTTP_200_OK)

    return JsonResponse({
        'non_field_errors': ['Wrong credentials.']
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST',])
def password_reset(request):
    serializer = PasswordResetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    form = PasswordResetForm(serializer.validated_data)
    if form.is_valid():
        form.save(
            from_email=settings.CKL_REST_AUTH.get('FROM_EMAIL'),
            email_template_name='registration/password_reset_email.html',
            request=request
        )

    return JsonResponse(request.data, status=status.HTTP_200_OK)


class GoogleAuthView(APIView):
    permission_classes = []

    def get(self, request, format=None):
        # Check link below to retrieve info wanted
        # https://developers.google.com/gmail/api/auth/scopes
        payload = {
            'response_type': 'code',
            'client_id': settings.CKL_REST_AUTH.get('GOOGLE', {}).get('CLIENT_ID'),
            'redirect_uri': settings.CKL_REST_AUTH.get('GOOGLE', {}).get('REDIRECT_URI'),
            'scope': (
                'https://www.googleapis.com/auth/userinfo.profile ',
                'https://www.googleapis.com/auth/userinfo.email'
            ),
            'state': json.dumps(request.query_params),
        }
        request = requests.Request('GET', constants.GOOGLE_AUTH_URL, params=payload).prepare()
        return redirect(request.url)

    def post(self, request):
        if not request.data.get('access_token'):
            if not request.data.get('code'):
                return JsonResponse({
                    'message': 'Missing auth token'
                }, status=status.HTTP_400_BAD_REQUEST)

            payload = {
                'client_id': settings.CKL_REST_AUTH.get('GOOGLE', {}).get('CLIENT_ID'),
                'client_secret': settings.CKL_REST_AUTH.get('GOOGLE', {}).get('CLIENT_SECRET'),
                'grant_type': 'authorization_code',
                'redirect_uri': settings.CKL_REST_AUTH.get('GOOGLE', {}).get('REDIRECT_URI'),
                'code': request.data['code'],
            }

            response = requests.post(constants.GOOGLE_TOKEN_URL, data=payload)

            if response.status_code != status.HTTP_200_OK:
                return JsonResponse({
                    'message': 'Google bad token'
                }, status=status.HTTP_400_BAD_REQUEST)

            access_token = response.json()['access_token']
        else:
            access_token = request.data.get('access_token')

        response = requests.get(constants.GOOGLE_USER_URL, headers={
            'Authorization': 'Bearer %s' % access_token
        })

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
                        data.get('given_name').lower().replace(" ", "_"),
                        data.get('family_name').lower().replace(" ", "_")
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
                token = Token.objects.create(user=user)
                return JsonResponse({
                    'token': token.key
                }, status=status.HTTP_201_CREATED)

        token = Token.objects.get(user=user)
        return JsonResponse({
            'token': token.key
        }, status=status.HTTP_200_OK)


# https://developers.facebook.com/docs/facebook-login/manually-build-a-login-flow
class FacebookAuthView(APIView):
    permission_classes = []

    def get(self, request, format=None):
        payload = {
            'response_type': 'code',
            'client_id': settings.CKL_REST_AUTH.get('FACEBOOK', {}).get('CLIENT_ID'),
            'redirect_uri': settings.CKL_REST_AUTH.get('FACEBOOK', {}).get('REDIRECT_URI'),
            'state': json.dumps(request.query_params),
            'scope': 'email',
        }
        request = requests.Request('GET', constants.FACEBOOK_AUTH_URL, params=payload).prepare()
        return redirect(request.url)

    def post(self, request):
        if not request.data.get('access_token'):
            if not request.data.get('code'):
                return JsonResponse({
                    'message': 'Missing auth token'
                }, status=status.HTTP_400_BAD_REQUEST)

            payload = {
                'client_id': settings.CKL_REST_AUTH.get('FACEBOOK', {}).get('CLIENT_ID'),
                'client_secret': settings.CKL_REST_AUTH.get('FACEBOOK', {}).get('CLIENT_SECRET'),
                'grant_type': 'authorization_code',
                'redirect_uri': settings.CKL_REST_AUTH.get('FACEBOOK', {}).get('REDIRECT_URI'),
                'code': request.data['code'],
            }

            response = requests.post(constants.FACEBOOK_TOKEN_URL, data=payload)

            if response.status_code != status.HTTP_200_OK:
                return JsonResponse({
                    'message': 'Facebook bad token'
                }, status=status.HTTP_400_BAD_REQUEST)

            access_token = response.json()['access_token']
        else:
            access_token = request.data.get('access_token')

        response = requests.get(constants.FACEBOOK_USER_URL, headers={
            'Authorization': 'Bearer %s' % access_token
        }, params={
            'fields': {'email,first_name,last_name'}
        })

        if response.status_code != status.HTTP_200_OK:
            return JsonResponse({
                'message': 'Cannot get facebook info'
            }, status=status.HTTP_401_UNAUTHORIZED)

        data = response.json()

        try:
            # email registered with social account
            social_account = SocialAccount.objects.get(user__email=data.get('email'))
            user = social_account.user
            if not social_account.facebook_id:
                social_account.facebook_id = data.get('id')
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
                        data.get('first_name').lower().replace(" ", "_"),
                        data.get('last_name').lower().replace(" ", "_")
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
                    facebook_id=data.get('id')
                )
                token = Token.objects.create(user=user)
                return JsonResponse({
                    'token': token.key
                }, status=status.HTTP_201_CREATED)

        token = Token.objects.get(user=user)
        return JsonResponse({
            'token': token.key
        }, status=status.HTTP_200_OK)


def get_username(username, current_username=None, count=0):
    if count == 0:
        current_username = username
    try:
        User.objects.get(username=current_username)
        count = count + 1
        current_username = '{0}_{1}'.format(
            username,
            count
        )
        return get_username(username=username, current_username=current_username, count=count)
    except User.DoesNotExist:
        return current_username
