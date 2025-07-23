from django.db.models import Q

from pneumatic_backend.processes.models import TaskField
from .base import Resolver


class StringResolver(Resolver):
    def _prepare_args(self):
        self.predicate_value = self._predicate.value
        field = TaskField.objects.get(
            Q(task__workflow_id=self._workflow_id) |
            Q(kickoff__workflow_id=self._workflow_id),
            api_name=self._predicate.field,
        )
        self.field_value = field.value or None
