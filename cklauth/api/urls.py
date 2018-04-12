from django.urls import include, path

from cklauth.api.v1 import urls

urlpatterns = [
    path('v1/', include(urls)),
]
