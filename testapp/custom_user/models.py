from django.db import models
from django.contrib.auth import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ObjectDoesNotExist


class CustomUserManager(UserManager):
    def _create_user(self, username, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if (not username and settings.CKL_REST_AUTH['LOGIN_FIELD'] == 'username') or \
                (not email and settings.CKL_REST_AUTH['LOGIN_FIELD'] == 'email'):
            raise ValueError('The given {0} must be set'.format(settings.CKL_REST_AUTH['LOGIN_FIELD']))
        email = self.normalize_email(email)
        username = self.model.normalize_username(self.get_username(username=username))
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

    def get_username(self, username, current_username=None, count=0):
        if count == 0:
            current_username = username
        try:
            User.objects.get(username=current_username)
            count = count + 1
            current_username = '{0}_{1}'.format(
                username,
                count
            )
            return self.get_username(username=username, current_username=current_username, count=count)
        except ObjectDoesNotExist:
            return current_username


class User(AbstractUser):
    email = models.EmailField(blank=True, max_length=254, verbose_name='email address', unique=True)

    USERNAME_FIELD = settings.CKL_REST_AUTH['LOGIN_FIELD']
    REQUIRED_FIELDS = ['username'] if settings.CKL_REST_AUTH['LOGIN_FIELD'] == 'email' else ['email']
    objects = CustomUserManager()