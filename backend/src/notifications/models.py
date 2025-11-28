from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q, UniqueConstraint

from src.accounts.models import Account
from src.generics.managers import BaseSoftDeleteManager
from src.generics.models import SoftDeleteModel
from src.notifications.enums import EmailTemplate
from src.notifications.querysets import DeviceQuerySet

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
        null=True,
    )
    is_app = models.BooleanField(
        default=False,
        help_text='Indicates that the device is an Android or IOS application',
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
        related_name='user_notifications',
    )
    count_unread_push_in_ios_app = models.PositiveIntegerField(default=0)


class EmailTemplateModel(models.Model):
    """Email templates storage model."""

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='email_templates',
        verbose_name='Account',
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Template name',
    )
    template_types = ArrayField(
        models.CharField(
            max_length=50,
            choices=[
                (choice, choice) for choice in EmailTemplate.LITERALS.__args__
            ],
        ),
        verbose_name='Template types',
        help_text='Email types that use this template',
    )
    subject = models.CharField(
        max_length=255,
        verbose_name='Subject',
        help_text='Use variables: {{variable_name}}',
    )
    content = models.TextField(
        verbose_name='Content',
        help_text='HTML template with variables: {{variable_name}}',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active',
    )

    class Meta:
        verbose_name = 'Email template'
        verbose_name_plural = 'Email templates'
        ordering = ['account', 'name']

    def __str__(self):
        return f'{self.account.name} - {self.name}'

    def get_template_types_display(self):
        """Return comma-separated list of template types."""
        return ', '.join(self.template_types) if self.template_types else ''
