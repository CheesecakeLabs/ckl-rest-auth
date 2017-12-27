from django.conf.urls import url, include

from cklauth.api import urls

app_name = 'cklauth'
urlpatterns = [
    url(r'api/', include(urls))
]
