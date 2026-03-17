from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q, UniqueConstraint

from src.accounts.models import (
    AccountBaseMixin,
    UserGroup,
)
from src.processes.enums import OwnerRole, OwnerType
from src.processes.models.base import BaseApiNameModel
from src.processes.models.templates.template import Template

UserModel = get_user_model()


class TemplateOwner(
    BaseApiNameModel,
    AccountBaseMixin,
):
    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['template', 'api_name'],
                condition=Q(is_deleted=False),
                name='processes_template_owner_template_api_name_unique',
            ),
            UniqueConstraint(
                fields=['template', 'user', 'role'],
                condition=Q(is_deleted=False, type='user'),
                name='processes_template_owner_user_role_unique',
            ),
            UniqueConstraint(
                fields=['template', 'group', 'role'],
                condition=Q(is_deleted=False, type='group'),
                name='processes_template_owner_group_role_unique',
            ),
        ]
        ordering = ['role', 'type', 'id']

    api_name_prefix = 'owner'
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='owners',
    )
    role = models.CharField(
        max_length=100,
        choices=OwnerRole.choices,
        default=OwnerRole.OWNER,
    )
    type = models.CharField(
        max_length=100,
        choices=OwnerType.choices,
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
