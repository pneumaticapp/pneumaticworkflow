from django.db import models
from django.db.models import UniqueConstraint, Q
from django.contrib.auth import get_user_model

from pneumatic_backend.processes.enums import OwnerType
from pneumatic_backend.accounts.models import (
    AccountBaseMixin,
    UserGroup
)
from pneumatic_backend.processes.models.base import (
    BaseApiNameModel
)
from pneumatic_backend.processes.models import Template


UserModel = get_user_model()


class TemplateOwner(
    BaseApiNameModel,
    AccountBaseMixin
):
    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['template', 'api_name'],
                condition=Q(is_deleted=False),
                name='processes_template_owner_template_api_name_unique',
            )
        ]
        ordering = ['type']

    api_name_prefix = 'owner'
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='owners',
    )
    type = models.CharField(
        max_length=100,
        choices=OwnerType.choices
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
