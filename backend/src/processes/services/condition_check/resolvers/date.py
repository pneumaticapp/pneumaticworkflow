import contextlib
from datetime import datetime
from datetime import timezone as tz

from django.db.models import Q

from src.processes.models.workflows.fields import TaskField
from src.processes.services.condition_check.resolvers.base import Resolver


class DateResolver(Resolver):
    def _get_date(self, value):
        if isinstance(value, str):
            with contextlib.suppress(ValueError):
                value = int(value)
        if isinstance(value, int):
            try:
                return datetime.fromtimestamp(value, tz=tz.utc)
            except (ValueError, TypeError):
                pass
        return None

    def _prepare_args(self):
        self.predicate_value = self._get_date(self._predicate.value)
        field = TaskField.objects.get(
            Q(task__workflow_id=self._workflow_id) |
            Q(kickoff__workflow_id=self._workflow_id),
            api_name=self._predicate.field,
        )
        self.field_value = self._get_date(field.value)
