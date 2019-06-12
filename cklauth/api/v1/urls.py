from django.urls import include, path

from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('social/google/', views.GoogleAuthView.as_view(), name='google'),
    path('social/facebook/', views.FacebookAuthView.as_view(), name='facebook'),
    path('password-reset/', views.password_reset, name='password-reset'),
]
