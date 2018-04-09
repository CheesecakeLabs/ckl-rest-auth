from django.urls import include, path

from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('password_reset/', views.password_reset, name='password_reset'),
]
