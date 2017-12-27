from django.http import JsonResponse
from django.contrib.auth import authenticate

from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view


@api_view(['POST',])
def register(request):
    return JsonResponse({})


@api_view(['POST',])
def login(request):
    return JsonResponse({})

