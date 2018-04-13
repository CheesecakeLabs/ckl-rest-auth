from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework.authtoken.models import Token

import cklauth.app_settings as settings


User = get_user_model()


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class UserSerializer(DynamicFieldsModelSerializer):
    username = serializers.CharField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message='This username is already in use.'
            )
        ]
    )
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message='This email is already in use.'
            )
        ]
    )

    class Meta:
        model = User
        fields = settings.CKL_REST_AUTH.get('REGISTER_FIELDS') + ['id']


def RegisterSerializerFactory(user_serializer=UserSerializer):
    class RegisterSerializer(user_serializer):
        password = serializers.CharField(
            required=True
        )

        class Meta(user_serializer.Meta):
            fields = user_serializer.Meta.fields + ['password']

        def create(self, validated_data):
            user = User.objects.create_user(**validated_data)
            token = Token.objects.create(user=user)

            return user, token

    return RegisterSerializer


class LoginSerializer(DynamicFieldsModelSerializer):
    username = serializers.CharField(required=True)
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'password'
        )


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
