from django.db import models
from django.db.models import UniqueConstraint, Q
from pneumatic_backend.processes.models.mixins import RawPerformerMixin
from pneumatic_backend.processes.models.templates.template import Template
from pneumatic_backend.processes.models.templates.task import TaskTemplate
from pneumatic_backend.processes.models.templates.fields import FieldTemplate
from pneumatic_backend.accounts.models import AccountBaseMixin
from pneumatic_backend.processes.models.base import BaseApiNameModel


class RawPerformerTemplate(
    BaseApiNameModel,
    AccountBaseMixin,
    RawPerformerMixin,
):
    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['template', 'api_name'],
                condition=Q(is_deleted=False),
                name='processes_rawperformertemplate_template_api_name_unique',
            )
        ]

    api_name_prefix = 'raw-performer'
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='raw_performers',
    )

    task = models.ForeignKey(
        TaskTemplate,
        on_delete=models.CASCADE,
        related_name='raw_performers'
    )
    field = models.ForeignKey(
        FieldTemplate,
        on_delete=models.CASCADE,
        related_name='raw_performers',
        null=True
    )
