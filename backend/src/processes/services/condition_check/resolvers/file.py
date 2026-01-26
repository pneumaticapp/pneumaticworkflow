from django.db.models import Q

from src.processes.models.workflows.fields import TaskField
from src.storage.models import Attachment

from .base import Resolver


class FileResolver(Resolver):
    def _prepare_args(self):
        field = TaskField.objects.get(
            Q(task__workflow_id=self._workflow_id) |
            Q(kickoff__workflow_id=self._workflow_id),
            api_name=self._predicate.field,
        )
        self.field_value = Attachment.objects.filter(
            task=field.task,
            workflow_id=self._workflow_id,
        ).exists() or None
