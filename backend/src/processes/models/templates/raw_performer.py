from django.db import models
from django.db.models import Q, UniqueConstraint

from src.accounts.models import AccountBaseMixin
from src.processes.models.base import BaseApiNameModel
from src.processes.models.mixins import RawPerformerMixin
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.templates.task import TaskTemplate
from src.processes.models.templates.template import Template


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
            ),
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
        related_name='raw_performers',
    )
    field = models.ForeignKey(
        FieldTemplate,
        on_delete=models.CASCADE,
        related_name='raw_performers',
        null=True,
    )
