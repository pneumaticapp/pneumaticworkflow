from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.postgres.fields import JSONField
from pneumatic_backend.generics.models import SoftDeleteModel
from pneumatic_backend.accounts.models import AccountBaseMixin
from pneumatic_backend.logs.enums import (
    AccountEventType,
    AccountEventStatus,
    RequestDirection,
)

UserModel = get_user_model()


class AccountEvent(
    SoftDeleteModel,
    AccountBaseMixin,
):

    class Meta:
        ordering = ('-date_created', 'account')

    user = models.ForeignKey(
        UserModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    date_created = models.DateTimeField(auto_now_add=True)
    error = JSONField(blank=True, null=True)
    ip = models.CharField(max_length=50, blank=True, null=True)
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    auth_token = models.CharField(max_length=50, blank=True, null=True)
    scheme = models.CharField(max_length=50, blank=True, null=True)
    method = models.CharField(max_length=100, blank=True, null=True)
    path = models.CharField(max_length=500, blank=True, null=True)
    body = JSONField(blank=True, null=True)
    http_status = models.IntegerField(blank=True, null=True)
    event_type = models.CharField(
        max_length=100,
        choices=AccountEventType.CHOICES,
        default=AccountEventType.API
    )
    direction = models.CharField(
        max_length=100,
        choices=RequestDirection.CHOICES,
        default=RequestDirection.RECEIVED
    )
    contractor = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=100,
        choices=AccountEventStatus.CHOICES,
        default=AccountEventStatus.PENDING
    )

    @property
    def is_sent(self):
        return self.direction == RequestDirection.SENT

    def __str__(self):
        return f'{self.method} {self.path}'
