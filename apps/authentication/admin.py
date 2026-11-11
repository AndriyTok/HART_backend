from django.contrib import admin

from apps.authentication.models import SocialAccountModel


@admin.register(SocialAccountModel)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'email', 'created_at')
    list_filter = ('provider',)
    search_fields = ('user__email', 'email', 'uid')
    raw_id_fields = ('user',)
