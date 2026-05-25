from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from src.accounts.enums import SourceType
from src.accounts.models import Account
from src.authentication.enums import SSOProvider
from src.generics.models import SoftDeleteModel

UserModel = get_user_model()


class AccessToken(SoftDeleteModel):

    class Meta:
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=['user_id', 'source'],
                condition=(models.Q(is_deleted=False)),
                name='auth_access_token_user_unique',
            ),
        ]

    access_token = models.CharField(max_length=3000)
    refresh_token = models.CharField(max_length=3000)
    expires_in = models.PositiveIntegerField(
        help_text='Seconds before expiration access_token')
    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name='access_tokens',
    )
    source = models.CharField(
        max_length=255,
        choices=SourceType.CHOICES,
    )
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.name} ({self.source})'

    @property
    def is_expired(self) -> bool:
        now = timezone.now()
        exp_date = self.date_updated + timedelta(seconds=self.expires_in - 30)
        return now > exp_date


class SSOConfig(models.Model):

    class Meta:
        unique_together = ('account', 'provider')
        ordering = ['account', 'provider']
        constraints = [
            models.UniqueConstraint(
                fields=['account'],
                condition=models.Q(is_active=True),
                name='unique_active_sso_per_account',
            ),
        ]

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='sso_configurations',
    )
    provider = models.CharField(
        max_length=50,
        choices=SSOProvider.CHOICES,
    )
    domain = models.CharField(max_length=255)
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.account.name} - {self.provider}'
