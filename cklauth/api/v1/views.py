from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token

from .serializers import RegisterSerializer, LoginSerializer


@api_view(['POST',])
def register(request):
    return JsonResponse({})


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

