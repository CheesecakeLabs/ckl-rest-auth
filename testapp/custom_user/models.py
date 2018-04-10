from django.db import models
from django.contrib.auth import settings
from django.contrib.auth.models import AbstractUser, UserManager

from cklauth.api.v1 import views


class CustomUserManager(UserManager):
    def _create_user(self, username, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if (not username and settings.CKL_REST_AUTH == 'username') or \
                (not email and settings.CKL_REST_AUTH == 'email'):
            raise ValueError('The given {0} must be set'.format(settings.CKL_REST_AUTH))
        email = self.normalize_email(email)
        username = self.model.normalize_username(views.get_username(username=username))
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        user = self._create_user(
            email=email,
            username=username,
            password=password
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save(using=self._db)
        return user


class CustomUser(AbstractUser):
    email = models.EmailField(blank=True, max_length=254, verbose_name='email address', unique=True)

    USERNAME_FIELD = settings.CKL_REST_AUTH
    REQUIRED_FIELDS = ['username'] if settings.CKL_REST_AUTH == 'email' else ['email']
    objects = CustomUserManager()
