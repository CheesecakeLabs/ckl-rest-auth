from django.apps import AppConfig
from django.conf import settings


class AuthConfig(AppConfig):
    name = 'cklauth'

    def ready(self):
        setattr(settings, 'CKL_REST_AUTH', {
            'LOGIN_FIELD': 'email',
            'REGISTER_FIELDS': ('username', 'email'),
            'USER_SERIALIZER': 'cklauth.api.v1.serializers.UserSerializer',
            # Override defaults
            **settings.CKL_REST_AUTH,
        })
