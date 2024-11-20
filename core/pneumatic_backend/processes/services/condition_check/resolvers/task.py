from pneumatic_backend.processes.models import Task
from .base import Resolver


class TaskResolver(Resolver):

    def _prepare_args(self):
        task = Task.objects.only('is_completed').get(
            api_name=self._predicate.field,
            workflow_id=self._workflow_id
        )
        self.field_value = task.is_completed
