from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from . import models


@admin.register(models.SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = (
        'user',
    )
    readonly_fields = (
        'user_',
        'facebook_id',
        'google_id',
    )
    exclude = (
        'user',
    )
    search_fields = (
        'user__username',
    )

    def user_(self, instance):
        if not instance.user:
            return '-'
        return format_html('<a href="{0}">{1}</a>'.format(
            reverse('admin:auth_user_change', args=[instance.user.id]),
            instance.user.username or instance.user.id
        ))

    user_.allow_tags = True
