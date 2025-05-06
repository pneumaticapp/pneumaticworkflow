from django.db.models import Q
from decimal import Decimal
from pneumatic_backend.processes.models import TaskField
from .base import Resolver


class NumberResolver(Resolver):
    def _prepare_args(self):
        self.predicate_value = (
            Decimal(self._predicate.value) if self._predicate.value else None
        )
        field = TaskField.objects.get(
            Q(task__workflow_id=self._workflow_id) |
            Q(kickoff__workflow_id=self._workflow_id),
            api_name=self._predicate.field,
        )
        self.field_value = Decimal(field.value) if field.value else None
