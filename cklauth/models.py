from django.db import models
from django.contrib.auth.models import User


class SocialAccount(models.Model):
    user = models.OneToOneField(User, related_name='social_account', on_delete=models.CASCADE)
    facebook_id = models.CharField(max_length=100, null=True, blank=True)
    google_id = models.CharField(max_length=100, null=True, blank=True)

