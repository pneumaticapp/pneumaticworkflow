from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import UniqueConstraint, Q

from pneumatic_backend.generics.managers import BaseSoftDeleteManager
from pneumatic_backend.generics.models import SoftDeleteModel
from pneumatic_backend.notifications.querysets import DeviceQuerySet


UserModel = get_user_model()


class Device(SoftDeleteModel):

    class Meta:
        verbose_name = 'Firebase device'
        constraints = [
            UniqueConstraint(
                fields=['token'],
                condition=Q(is_deleted=False),
                name='device_token_unique',
            ),
        ]

    token = models.TextField()
    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        db_index=True,
    )
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(
        verbose_name='Device, OS and browser info',
        blank=True,
        null=True
    )
    is_app = models.BooleanField(
        default=False,
        help_text='Indicates that the device is an Android or IOS application'
    )
    objects = BaseSoftDeleteManager.from_queryset(DeviceQuerySet)()

    def __str__(self):
        return (
            f'{self.__class__.__name__} for {self.user or "unknown user"}'
        )


class UserNotifications(SoftDeleteModel):

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['user'],
                condition=Q(is_deleted=False),
                name='usernotifications_user_unique',
            ),
        ]

    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name='user_notifications'
    )
    count_unread_push_in_ios_app = models.PositiveIntegerField(default=0)
