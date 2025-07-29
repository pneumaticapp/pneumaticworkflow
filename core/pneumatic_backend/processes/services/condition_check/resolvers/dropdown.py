from django.db.models import Q

from pneumatic_backend.processes.models import TaskField
from .base import Resolver


class DropdownResolver(Resolver):
    def _prepare_args(self):
        field = TaskField.objects.get(
            Q(task__workflow_id=self._workflow_id) |
            Q(kickoff__workflow_id=self._workflow_id),
            api_name=self._predicate.field,
        )
        selected = list(field.selections.selected().values_list(
            'api_name',
            flat=True,
        ))
        self.field_value = selected[0] if selected else None
        self.predicate_value = self._predicate.value
