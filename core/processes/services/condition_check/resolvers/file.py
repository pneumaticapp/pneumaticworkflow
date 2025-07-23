from django.db.models import Q

from pneumatic_backend.processes.models import TaskField
from .base import Resolver


class FileResolver(Resolver):
    def _prepare_args(self):
        field = TaskField.objects.get(
            Q(task__workflow_id=self._workflow_id) |
            Q(kickoff__workflow_id=self._workflow_id),
            api_name=self._predicate.field,
        )
        self.field_value = field.attachments.exists() or None
