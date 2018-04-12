from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

from cklauth.auth import TokenAuthSupportQueryString


@api_view(['GET',])
@authentication_classes((TokenAuthSupportQueryString,))
@permission_classes((IsAuthenticated,))
def get_authenticated_dogs(request):
    return JsonResponse({
        'dogs': [{'name': 'Maya'}, {'name': 'Tuniko'}]
    }, status=status.HTTP_200_OK)
