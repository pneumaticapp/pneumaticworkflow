from src.processes.enums import PredicateOperator
from src.processes.models.workflows.task import Task

from .base import Resolver


class TaskResolver(Resolver):

    def _prepare_args(self):
        task = Task.objects.only('status').get(
            api_name=self._predicate.field,
            workflow_id=self._workflow_id,
        )
        if self._predicate.operator == PredicateOperator.SKIPPED:
            self.field_value = task.is_skipped
        else:
            self.field_value = task.is_completed
