from django.urls import include, path

from . import views

urlpatterns = [
    path('register', views.register, name='register'),
    path('login', views.login, name='login'),
    path('password-reset', views.password_reset, name='password-reset'),
    path('google', views.GoogleAuthView.as_view(), name='google'),
    path('facebook', views.FacebookAuthView.as_view(), name='facebook'),
]
