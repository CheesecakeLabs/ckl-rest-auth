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

            # Social defaults
            'GOOGLE': {
                'AUTH_FIELD_GENERATOR': 'cklauth.utils.auth_field_generator',
                'USER_INFO_MAPPING': {
                    'first_name': 'given_name',
                    'last_name': 'family_name',
                    'email': 'email',
                },
                **settings.CKL_REST_AUTH.get('GOOGLE', {}),
            },
            'FACEBOOK': {
                'AUTH_FIELD_GENERATOR': 'cklauth.utils.auth_field_generator',
                'USER_INFO_MAPPING': {
                    'first_name': 'first_name',
                    'last_name': 'last_name',
                    'email': 'email',
                },
                **settings.CKL_REST_AUTH.get('FACEBOOK', {}),
            }
        })
