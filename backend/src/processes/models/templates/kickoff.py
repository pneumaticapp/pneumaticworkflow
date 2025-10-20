from django.db import models
from django.db.models import Q, UniqueConstraint

from src.accounts.models import AccountBaseMixin
from src.generics.managers import BaseSoftDeleteManager
from src.generics.models import SoftDeleteModel
from src.processes.models.templates.template import Template
from src.processes.querysets import KickoffQuerySet


class Kickoff(
    SoftDeleteModel,
    AccountBaseMixin,
):

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['template'],
                condition=Q(is_deleted=False),
                name='kickoff_template_unique',
            ),
        ]

    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='kickoff',
        null=True,
    )

    objects = BaseSoftDeleteManager.from_queryset(KickoffQuerySet)()
