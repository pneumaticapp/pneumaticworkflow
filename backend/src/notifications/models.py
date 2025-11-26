from django.db import models

from src.accounts.models import Account
from src.notifications.enums import EmailTemplate


class EmailTemplateModel(models.Model):
    """Email templates storage model."""

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='email_templates',
        verbose_name='Account',
    )
    template_type = models.CharField(
        max_length=50,
        choices=[
            (choice, choice) for choice in EmailTemplate.LITERALS.__args__
        ],
        verbose_name='Template type',
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
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated at',
    )

    class Meta:
        verbose_name = 'Email template'
        verbose_name_plural = 'Email templates'
        unique_together = ('account', 'template_type')
        ordering = ['account', 'template_type']

    def __str__(self):
        return f'{self.account.name} - {self.template_type}'
