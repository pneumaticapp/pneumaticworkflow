from src.processes.enums import TaskStatus
from src.processes.models.hierarchy import TaskHierarchyContext
from src.processes.models.workflows.task import Task

from .base import Resolver


class TaskResolver(Resolver):

    def _prepare_args(self):
        task = Task.objects.only('status').get(
            api_name=self._predicate.field,
            workflow_id=self._workflow_id,
        )

        has_active_hierarchy = TaskHierarchyContext.objects.filter(
            task__workflow_id=self._workflow_id,
            base_api_name=self._predicate.field,
            task__status__in=[
                TaskStatus.PENDING,
                TaskStatus.ACTIVE,
                TaskStatus.DELAYED,
            ],
        ).exists()

        self.field_value = (
            (task.is_completed or task.is_skipped)
            and not has_active_hierarchy
        )
