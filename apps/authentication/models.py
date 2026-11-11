from django.conf import settings
from django.db import models

from core.models import BaseModel


class SocialProvider(models.TextChoices):
    GOOGLE = 'google', 'Google'
    APPLE = 'apple', 'Apple'


class SocialAccountModel(BaseModel):
    class Meta:
        db_table = 'social_accounts'
        constraints = [
            models.UniqueConstraint(fields=('provider', 'uid'), name='social_accounts_provider_uid_unique'),
        ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='social_accounts')
    provider = models.CharField(max_length=20, choices=SocialProvider.choices)
    # `sub` claim of the provider's id_token; stable, unlike email (Apple private relay, email changes)
    uid = models.CharField(max_length=255)
    email = models.EmailField(blank=True)

    def __str__(self):
        return f'{self.provider}:{self.uid}'
