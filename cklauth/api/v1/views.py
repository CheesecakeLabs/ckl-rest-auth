from django.http import JsonResponse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view

from .serializers import RegisterSerializer


@api_view(['POST',])
def register(request):
    serializer = RegisterSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)
    serializer.save()

    return JsonResponse({
        'message': 'Ok.'
    }, status=status.HTTP_201_CREATED)


@api_view(['POST',])
def login(request):
    return JsonResponse({})

