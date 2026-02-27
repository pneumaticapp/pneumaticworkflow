from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q, UniqueConstraint

from src.accounts.models import (
    AccountBaseMixin,
    UserGroup,
)
from src.processes.enums import StarterType
from src.processes.models.base import BaseApiNameModel
from src.processes.models.templates.template import Template

UserModel = get_user_model()


class TemplateStarter(
    BaseApiNameModel,
    AccountBaseMixin,
):
    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['template', 'api_name'],
                condition=Q(is_deleted=False),
                name='processes_template_starter_template_api_name_unique',
            ),
        ]
        ordering = ['type', 'id']

    api_name_prefix = 'starter'
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='starters',
    )
    type = models.CharField(
        max_length=100,
        choices=StarterType.choices,
    )
    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        null=True,
    )
    group = models.ForeignKey(
        UserGroup,
        on_delete=models.CASCADE,
        null=True,
    )
