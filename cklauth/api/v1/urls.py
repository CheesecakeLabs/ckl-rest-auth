from django.conf.urls import url, include

from . import views

urlpatterns = [
    url(r'register/$', views.register, name='register'),
    url(r'login/$', views.login, name='login'),
]
