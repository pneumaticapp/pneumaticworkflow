from typing import Any, Dict
from django.db import models
from django.db.models import UniqueConstraint, Q
from django.contrib.postgres.search import SearchVectorField
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
            )
        ]

    workflow = models.ForeignKey(
        Workflow,
        related_name='kickoff',
        on_delete=models.CASCADE,
    )
    clear_description = models.TextField(
        null=True,
        blank=True,
        help_text='Does not contains markdown'
    )
    search_content = SearchVectorField(null=True)
    objects = BaseSoftDeleteManager()

    def _update_field(self, template: Dict[str, Any]):
        from src.processes.models.workflows\
            .fields import TaskField

        return TaskField.objects.update_or_create(
            kickoff=self,
            template_id=template['id'],
            defaults={
                'name': template['name'],
                'description': template['description'],
                'type': template['type'],
                'is_required': template['is_required'],
                'api_name': template['api_name'],
                'order': template['order'],
                'workflow': self.workflow
            }
        )
