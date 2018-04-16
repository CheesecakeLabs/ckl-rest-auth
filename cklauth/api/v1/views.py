import json
from pydoc import locate

import requests
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import ImproperlyConfigured
from django.http import JsonResponse
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.views import APIView

import cklauth.app_settings as settings
from cklauth import constants
from cklauth.models import SocialAccount
from .serializers import RegisterSerializerFactory, LoginSerializer, PasswordResetSerializer


User = get_user_model()
UserSerializer = locate(settings.CKL_REST_AUTH.get('USER_SERIALIZER'))


class AuthError(Exception):
    def __init__(self, message, status):
        self.message = message
        self.status = status


class AuthView(APIView):
    status_code = status.HTTP_200_OK

    def post(self, request):
        try:
            user, token = self.perform_action(request)
        except AuthError as error:
            return JsonResponse(
                {'non_field_errors': [error.message]},
                status=error.status
            )

        return JsonResponse({
            'token': token.key,
            'user': UserSerializer(instance=user).data,
        }, status=self.status_code)

    def perform_action(self, request):
        raise NotImplementedError('The view should implement `perform_login` method')


class RegisterView(AuthView):
    status_code = status.HTTP_201_CREATED

    def perform_action(self, request):
        RegisterSerializer = RegisterSerializerFactory(UserSerializer)

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return serializer.save()


class LoginView(AuthView):
    def perform_action(self, request):
        fields = [settings.CKL_REST_AUTH['LOGIN_FIELD'], 'password']
        serializer = LoginSerializer(data=request.data, fields=fields)

        serializer.is_valid(raise_exception=True)
        login_field = serializer.validated_data[settings.CKL_REST_AUTH['LOGIN_FIELD']]
        password = serializer.validated_data['password']
        user = authenticate(username=login_field, password=password)

        if not user:
            raise AuthError(message='Wrong credentials.', status=status.HTTP_401_UNAUTHORIZED)

        token, _ = Token.objects.get_or_create(user=user)
        return user, token


class SocialAuthView(AuthView):
    def __init__(self, *args, **kwargs):
        platform_settings = settings.CKL_REST_AUTH.get(self.platform, {})
        if not platform_settings:
            raise ImproperlyConfigured(
                'Add {} CLIENT_ID and REDIRECT_URI to settings.'.format(self.platform)
            )

        self.CLIENT_ID = platform_settings.get('CLIENT_ID')
        self.CLIENT_SECRET = platform_settings.get('CLIENT_SECRET')
        self.REDIRECT_URI = platform_settings.get('REDIRECT_URI')

        super().__init__(*args, **kwargs)

    def get_access_token(self, request):
        if request.data.get('access_token'):
            return request.data.get('access_token')

        if not request.data.get('code'):
            raise AuthError(message='Missing auth token.', status=status.HTTP_400_BAD_REQUEST)

        payload = {
            'client_id': self.CLIENT_ID,
            'client_secret': self.CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'redirect_uri': self.REDIRECT_URI,
            'code': request.data['code'],
        }

        response = requests.post(self.token_url, data=payload)

        if response.status_code != status.HTTP_200_OK:
            raise AuthError(message='Bad token.', status=status.HTTP_400_BAD_REQUEST)

        return response.json()['access_token']

    def get_username(self, username, current_username=None, count=0):
        if count == 0:
            current_username = username
        try:
            User.objects.get(username=current_username)
            count = count + 1
            current_username = '{0}_{1}'.format(
                username,
                count
            )
            return self.get_username(
                username=username,
                current_username=current_username,
                count=count
            )
        except User.DoesNotExist:
            return current_username

    def create_user(self, user_info):
        register_info = {
            register_key: user_info.get(provider_key)
            for register_key, provider_key in self.user_info_mapping.items()
        }
        register_info['username'] = self.get_username(
            username='{0}_{1}'.format(
                register_info.get('first_name').lower().replace(" ", "_"),
                register_info.get('last_name').lower().replace(" ", "_")
            )
        )

        serializer = UserSerializer(data=register_info)
        serializer.is_valid(raise_exception=True)

        return User.objects.create_user(**register_info)

    def perform_action(self, request):
        access_token = self.get_access_token(request)
        user_info = self.get_user_info(access_token)

        try:
            # email registered with social account
            social_account = SocialAccount.objects.get(user__email=user_info.get('email'))
            user = social_account.user
            if not getattr(social_account, self.social_account_field):
                setattr(social_account, self.social_account_field, user_info.get('id'))
                social_account.save()
        except SocialAccount.DoesNotExist:
            try:
                # email registered without social account
                user = User.objects.get(email=user_info.get('email'))
                raise AuthError(
                    message='Registered with email.',
                    status=status.HTTP_400_BAD_REQUEST
                )
            except User.DoesNotExist:
                # user and social account don't exist
                user = self.create_user(user_info)

                SocialAccount.objects.create(**{
                    'user': user,
                    self.social_account_field: user_info.get('id')
                })

                self.status_code = status.HTTP_201_CREATED

        token, _ = Token.objects.get_or_create(user=user)
        return user, token


class GoogleAuthView(SocialAuthView):
    platform = 'GOOGLE'
    social_account_field = 'google_id'
    token_url = constants.GOOGLE_TOKEN_URL
    user_info_mapping = {
        'first_name': 'given_name',
        'last_name': 'family_name',
        'email': 'email',
    }

    def get(self, request, format=None):
        payload = {
            'response_type': 'code',
            'client_id': self.CLIENT_ID,
            'redirect_uri': self.REDIRECT_URI,
            'scope': (
                'https://www.googleapis.com/auth/userinfo.profile ',
                'https://www.googleapis.com/auth/userinfo.email'
            ),
            'state': json.dumps(request.query_params),
        }
        request = requests.Request('GET', constants.GOOGLE_AUTH_URL, params=payload).prepare()
        return redirect(request.url)

    def get_user_info(self, access_token):
        response = requests.get(constants.GOOGLE_USER_URL, headers={
            'Authorization': 'Bearer %s' % access_token
        })

        if response.status_code != status.HTTP_200_OK:
            raise AuthError(message='Cannot get user info', status=tatus.HTTP_401_UNAUTHORIZED)

        return response.json()


class FacebookAuthView(SocialAuthView):
    platform = 'FACEBOOK'
    social_account_field = 'facebook_id'
    token_url = constants.FACEBOOK_TOKEN_URL
    user_info_mapping = {
        'first_name': 'first_name',
        'last_name': 'last_name',
        'email': 'email',
    }

    def get(self, request, format=None):
        payload = {
            'response_type': 'code',
            'client_id': self.CLIENT_ID,
            'redirect_uri': self.REDIRECT_URI,
            'state': json.dumps(request.query_params),
            'scope': 'email',
        }
        request = requests.Request('GET', constants.FACEBOOK_AUTH_URL, params=payload).prepare()
        return redirect(request.url)

    def get_user_info(self, access_token):
        response = requests.get(constants.FACEBOOK_USER_URL, headers={
            'Authorization': 'Bearer %s' % access_token
        }, params={
            'fields': {'email,first_name,last_name'}
        })

        if response.status_code != status.HTTP_200_OK:
            raise AuthError(message='Cannot get user info.', status=status.HTTP_401_UNAUTHORIZED)

        return response.json()


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
