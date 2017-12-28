from django.http import JsonResponse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view

from .serializers import RegisterSerializer


@api_view(['POST',])
def register(request):
    data = JSONParser().parse(request)
    serializer = RegisterSerializer(data=data)

    if serializer.is_valid():
        serializer.save()

        return JsonResponse({
            'message': 'Ok.'
        }, status=status.HTTP_201_CREATED)

    return JsonResponse({
        'message': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST',])
def login(request):
    return JsonResponse({})

