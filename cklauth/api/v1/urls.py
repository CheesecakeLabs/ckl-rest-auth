from django.conf.urls import url, include

from . import views

urlpatterns = [
    url('register', views.register, name='register'),
    url('login', views.login, name='login'),
    url('google', views.GoogleAuthView.as_view(), name='google'),
    url('facebook', views.FacebookAuthView.as_view(), name='facebook'),
]
