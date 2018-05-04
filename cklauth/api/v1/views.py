import json
from pydoc import locate

import requests
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import ImproperlyConfigured
from django.http import JsonResponse
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from cklauth import constants
from cklauth.models import SocialAccount
from .serializers import RegisterSerializerFactory, LoginSerializer, PasswordResetSerializer


User = get_user_model()


class AuthError(Exception):
    def __init__(self, message, status):
        self.message = message
        self.status = status


class AuthView(APIView):
    status_code = status.HTTP_200_OK
    permission_classes = (AllowAny, )

    def post(self, request):
        try:
            user, token = self.perform_action(request)
        except AuthError as error:
            return JsonResponse(
                {'non_field_errors': [error.message]},
                status=error.status
            )

        UserSerializer = locate(settings.CKL_REST_AUTH.get('USER_SERIALIZER'))
        return JsonResponse({
            'token': token.key,
            'user': UserSerializer(instance=user).data,
        }, status=self.status_code)

    def perform_action(self, request):
        raise NotImplementedError('The view should implement `perform_login` method')


class RegisterView(AuthView):
    status_code = status.HTTP_201_CREATED

    def perform_action(self, request):
        UserSerializer = locate(settings.CKL_REST_AUTH.get('USER_SERIALIZER'))
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
        self.USER_INFO_MAPPING = platform_settings.get('USER_INFO_MAPPING')
        self.AUTH_FIELD_GENERATOR = platform_settings.get('AUTH_FIELD_GENERATOR')

        super().__init__(*args, **kwargs)

    def validate_response(self, response):
        if response.status_code != status.HTTP_200_OK:
            raise AuthError(message='Bad token.', status=status.HTTP_400_BAD_REQUEST)

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

        self.validate_response(response)

        return response.json()['access_token']

    def create_user(self, user_info, extra_fields={}):
        register_info = {
            register_key: (
                provider_key(user_info)
                if callable(provider_key)
                else user_info.get(provider_key)
            )
            for register_key, provider_key in self.USER_INFO_MAPPING.items()
        }

        if self.AUTH_FIELD_GENERATOR:
            auth_field_generator = locate(self.AUTH_FIELD_GENERATOR)
            register_info[User.USERNAME_FIELD] = auth_field_generator(register_info)

        register_info.update(extra_fields)

        UserSerializer = locate(settings.CKL_REST_AUTH.get('USER_SERIALIZER'))
        serializer = UserSerializer(data=register_info)
        serializer.is_valid(raise_exception=True)

        return User.objects.create_user(**serializer.data)

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
                extra_fields = request.data.get('user_extra_fields', {})
                user = self.create_user(user_info, extra_fields)

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
            raise AuthError(message='Cannot get user info', status=status.HTTP_401_UNAUTHORIZED)

        return response.json()

    def validate_response(self, response):
        if response.status_code != status.HTTP_200_OK:
            raise AuthError(message=response.json(), status=response.status_code)


class FacebookAuthView(SocialAuthView):
    platform = 'FACEBOOK'
    social_account_field = 'facebook_id'
    token_url = constants.FACEBOOK_TOKEN_URL

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
@permission_classes((AllowAny, ))
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
