from django.urls import include, path

from cklauth.api import urls

urlpatterns = [
    path('api/', include((urls, 'cklauth'), namespace='cklauth')),
    path('', include('django.contrib.auth.urls')),
]
