from django.conf import settings


CKL_REST_AUTH = {
    'LOGIN_FIELD': 'email',
    'REGISTER_FIELDS': ('username', 'email'),
    'USER_SERIALIZER': 'cklauth.api.v1.serializers.UserSerializer',
    # Override defaults
    **settings.CKL_REST_AUTH,
}
