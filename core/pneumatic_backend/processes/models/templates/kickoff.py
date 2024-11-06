from django.db import models
from django.db.models import UniqueConstraint, Q
from pneumatic_backend.accounts.models import AccountBaseMixin
from pneumatic_backend.generics.managers import BaseSoftDeleteManager
from pneumatic_backend.generics.models import SoftDeleteModel
from pneumatic_backend.processes.querysets import KickoffQuerySet
from pneumatic_backend.processes.models.templates.template import Template


class Kickoff(
    SoftDeleteModel,
    AccountBaseMixin
):

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['template'],
                condition=Q(is_deleted=False),
                name='kickoff_template_unique',
            )
        ]

    description = models.TextField(null=True, blank=True)
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='kickoff',
        null=True
    )

    objects = BaseSoftDeleteManager.from_queryset(KickoffQuerySet)()
