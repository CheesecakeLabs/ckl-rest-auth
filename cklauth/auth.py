from django.contrib.auth import get_user_model, settings
from rest_framework.authentication import TokenAuthentication


User = get_user_model()


class TokenAuthSupportQueryString(TokenAuthentication):
    def authenticate(self, request):
        if 'auth_token' in request.query_params and 'HTTP_AUTHORIZATION' not in request.META:
            return self.authenticate_credentials(request.query_params.get('auth_token'))
        else:
            return super(TokenAuthSupportQueryString, self).authenticate(request)


class EmailOrUsernameModelBackend(object):
    def authenticate(self, request=None, username=None, password=None):
        kwargs = {settings.CKL_REST_AUTH['LOGIN_FIELD']: username}
        try:
            user = User.objects.filter(**kwargs).order_by('id')[0]
            if user.check_password(password):
                return user
        except IndexError:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
