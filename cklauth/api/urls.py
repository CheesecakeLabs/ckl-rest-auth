from django.conf.urls import url, include

from cklauth.api.v1 import urls

urlpatterns = [
    url(r'v1/', include(urls)),
]
