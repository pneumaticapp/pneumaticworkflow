from django.db import models
from django.db.models import Q, UniqueConstraint

from src.accounts.models import AccountBaseMixin
from src.generics.managers import BaseSoftDeleteManager
from src.generics.models import SoftDeleteModel
from src.processes.models.workflows.workflow import Workflow


class KickoffValue(
    SoftDeleteModel,
    AccountBaseMixin,
):

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['workflow'],
                condition=Q(is_deleted=False),
                name='kickoff_value_workflow_unique',
            ),
        ]

    workflow = models.ForeignKey(
        Workflow,
        related_name='kickoff',
        on_delete=models.CASCADE,
    )
    clear_description = models.TextField(
        null=True,
        blank=True,
        help_text='Does not contains markdown',
    )
    objects = BaseSoftDeleteManager()
