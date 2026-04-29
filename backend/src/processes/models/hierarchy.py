from django.db import models

from src.accounts.models import AccountBaseMixin
from src.generics.models import SoftDeleteModel


class TaskTemplateHierarchyConfig(
    SoftDeleteModel,
    AccountBaseMixin,
):

    """Configuration for hierarchical approval on a TaskTemplate.

    Linked 1:1 via unique FK to TaskTemplate.
    Presence of a row means the step uses hierarchical routing.
    Existing models (Task, TaskTemplate) are NOT modified."""

    class Meta:
        ordering = ['id']

    task_template = models.OneToOneField(
        'processes.TaskTemplate',
        on_delete=models.CASCADE,
        related_name='hierarchy_config',
    )
    max_depth = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=(
            'Maximum number of hierarchy levels. '
            'NULL means unlimited (up to system limit).'
        ),
    )

    def __str__(self) -> str:
        depth = self.max_depth or 'unlimited'
        return (
            f'HierarchyConfig('
            f'task_template={self.task_template_id}, '
            f'max_depth={depth})'
        )


class TaskHierarchyContext(
    SoftDeleteModel,
    AccountBaseMixin,
):

    """Runtime context for a dynamically spawned hierarchy task.

    Linked 1:1 via unique FK to Task.
    Presence of a row means the task is part of a hierarchy chain."""

    SYSTEM_MAX_DEPTH = 50

    class Meta:
        ordering = ['current_depth']

    task = models.OneToOneField(
        'processes.Task',
        on_delete=models.CASCADE,
        related_name='hierarchy_context',
    )
    base_api_name = models.CharField(
        max_length=200,
        help_text=(
            'api_name of the original TaskTemplate step. '
            'Used to group clones and for frontend mapping.'
        ),
    )
    current_depth = models.PositiveIntegerField(
        help_text='Current depth in the hierarchy chain (1-based).',
    )
    max_depth = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=(
            'Max depth copied from config. '
            'NULL means unlimited (up to SYSTEM_MAX_DEPTH).'
        ),
    )

    @property
    def effective_max_depth(self) -> int:
        """Return the actual limit, falling back to system max."""
        if self.max_depth is not None:
            return self.max_depth
        return self.SYSTEM_MAX_DEPTH

    def has_reached_limit(self) -> bool:
        return self.current_depth >= self.effective_max_depth

    def __str__(self) -> str:
        return (
            f'HierarchyCtx(task={self.task_id}, '
            f'depth={self.current_depth}/{self.max_depth})'
        )
