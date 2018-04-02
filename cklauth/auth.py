from rest_framework.authentication import TokenAuthentication


class TokenAuthSupportQueryString(TokenAuthentication):
    def authenticate(self, request):
        if 'auth_token' in request.query_params and 'HTTP_AUTHORIZATION' not in request.META:
            return self.authenticate_credentials(request.query_params.get('auth_token'))
        else:
            return super(TokenAuthSupportQueryString, self).authenticate(request)
