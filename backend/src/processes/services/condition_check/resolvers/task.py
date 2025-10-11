from src.processes.models import Task
from .base import Resolver


class TaskResolver(Resolver):

    def _prepare_args(self):
        task = Task.objects.only('status').get(
            api_name=self._predicate.field,
            workflow_id=self._workflow_id,
        )
        self.field_value = (task.is_completed or task.is_skipped)
