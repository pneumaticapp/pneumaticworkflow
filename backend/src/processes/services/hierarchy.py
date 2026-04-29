from collections import defaultdict
from typing import Dict, Optional

from src.accounts.models import User
from src.processes.enums import (
    FieldType,
    PerformerType,
    TaskStatus,
)
from src.processes.models.hierarchy import (
    TaskHierarchyContext,
    TaskTemplateHierarchyConfig,
)
from src.processes.models.workflows.fields import (
    FieldSelection,
    TaskField,
)
from src.processes.models.workflows.task import Task
from src.processes.models.workflows.workflow import Workflow
from src.services.markdown import MarkdownService


class HierarchyService:

    """Service encapsulating all JIT hierarchy-spawn logic.

    Responsibilities:
      - Determine whether a completed task needs a hierarchy clone.
      - Create a clone task with the correct depth, fields, and performer.
      - Build the approval-chain-summary variable value."""

    @staticmethod
    def get_config_for_task(
        task: Task,
    ) -> Optional[TaskTemplateHierarchyConfig]:
        """Return hierarchy config if this task's api_name
        links to a TaskTemplate with hierarchy enabled.

        Note: Only valid for root tasks (original api_name).
        Clones have suffixed api_names (e.g. 'task-1-h2')
        and will NOT match — use get_context() instead."""

        try:
            return (
                TaskTemplateHierarchyConfig.objects
                .select_related('task_template')
                .get(
                    task_template__api_name=task.api_name,
                    task_template__template_id=(
                        task.workflow.template_id
                    ),
                    is_deleted=False,
                )
            )
        except TaskTemplateHierarchyConfig.DoesNotExist:
            return None

    @staticmethod
    def get_context(task: Task) -> Optional[TaskHierarchyContext]:
        """Return hierarchy context for a task, if any."""

        try:
            return task.hierarchy_context
        except TaskHierarchyContext.DoesNotExist:
            return None

    @classmethod
    def should_spawn_next(
        cls,
        task: Task,
    ) -> Optional[User]:
        """Check if a hierarchy clone should be created
        after the given task is completed.

        Returns the anchor User if spawn is needed,
        None otherwise. Conditions checked:
          1. Task is in a chain or has hierarchy config
          2. Chain has not reached the depth limit
          3. The anchor performer has a manager"""

        context = cls.get_context(task)
        if context is not None:
            if context.has_reached_limit():
                return None
        else:
            config = cls.get_config_for_task(task)
            if config is None:
                return None

        anchor_user = cls._get_anchor_performer_user(task)
        if anchor_user is None:
            return None

        if anchor_user.manager_id is None:
            return None
        return anchor_user

    @classmethod
    def create_hierarchy_task(
        cls,
        source_task: Task,
        anchor_user: User,
    ) -> Task:
        """Create a cloned task at the next hierarchy depth.

        The clone:
          - Has a unique api_name (suffixed with depth)
          - Copies only fields (output form)
          - Sets anchor_user's manager as the performer
          - Inherits the same parents for correct DAG
          - Is inserted with PENDING status

        Args:
          source_task: the completed task to clone from.
          anchor_user: the USER-type performer whose
            manager becomes the next performer. Obtained
            from should_spawn_next() to avoid extra SQL.

        Must be called inside transaction.atomic() with
        the task locked via select_for_update()."""

        context = cls.get_context(source_task)

        if context is not None:
            current_depth = context.current_depth
            max_depth = context.max_depth
            base_api_name = context.base_api_name
        else:
            config = cls.get_config_for_task(source_task)
            current_depth = 1
            max_depth = (
                config.max_depth if config else None
            )
            base_api_name = source_task.api_name

        next_depth = current_depth + 1
        manager = anchor_user.manager

        # Generate a unique api_name for the clone
        clone_api_name = cls._truncate_api_name(
            base_api_name, f'-h{next_depth}',
        )

        workflow = source_task.workflow

        # Build name with depth indicator
        clone_name = f'{source_task.name} (L{next_depth})'
        clear_description = MarkdownService.clear(
            source_task.description_template,
        )

        clone = Task.objects.create(
            api_name=clone_api_name,
            account=workflow.account,
            workflow=workflow,
            name=clone_name,
            name_template=source_task.name_template,
            description=source_task.description_template,
            description_template=source_task.description_template,
            clear_description=clear_description,
            number=source_task.number,
            require_completion_by_all=False,
            is_urgent=workflow.is_urgent,
            checklists_total=0,
            parents=source_task.parents,
            revert_task=None,
            status=TaskStatus.PENDING,
        )

        # Create hierarchy context for the clone
        TaskHierarchyContext.objects.create(
            task=clone,
            account=workflow.account,
            base_api_name=base_api_name,
            current_depth=next_depth,
            max_depth=max_depth,
        )

        # Also create context for the source if it's the first in the chain
        if context is None:
            TaskHierarchyContext.objects.create(
                task=source_task,
                account=workflow.account,
                base_api_name=base_api_name,
                current_depth=1,
                max_depth=max_depth,
            )

        # Clone output fields (form) and their selections
        cls._clone_fields(
            source_task=source_task,
            target_task=clone,
            workflow=workflow,
            next_depth=next_depth,
        )

        # Set the manager as the sole performer
        clone.add_raw_performer(
            user=manager,
            performer_type=PerformerType.USER,
        )

        return clone

    @classmethod
    def build_approval_chain_summaries(
        cls,
        workflow: Workflow,
    ) -> Dict[str, str]:
        """Build a text summary mapping for all hierarchy chains
        within a workflow. Avoids N+1 using prefetch_related."""

        contexts = (
            TaskHierarchyContext.objects
            .filter(
                task__workflow=workflow,
                is_deleted=False,
            )
            .select_related('task')
            .prefetch_related(
                'task__output',
                'task__raw_performers__user',
            )
            .order_by('base_api_name', 'current_depth')
        )

        grouped_lines = defaultdict(list)

        for ctx in contexts:
            task = ctx.task
            if task.status != TaskStatus.COMPLETED:
                continue

            # Get performer name
            performer_name = cls._get_task_performer_name(task)
            grouped_lines[ctx.base_api_name].append(
                f'**Level {ctx.current_depth}** — {performer_name}:',
            )

            # Fields are prefetch_related, sort them via python
            fields = sorted(
                task.output.all(),
                key=lambda f: (f.order, f.id),
            )
            for field in fields:
                value = field.value or '—'
                line = f'  {field.name}: {value}'
                grouped_lines[
                    ctx.base_api_name
                ].append(line)

            # blank line between levels
            grouped_lines[
                ctx.base_api_name
            ].append('')

        return {
            api_name: '\n'.join(lines).strip()
            for api_name, lines in grouped_lines.items()
        }

    @staticmethod
    def _get_anchor_performer_user(task: Task) -> Optional[User]:
        """Find the anchor USER performer for a hierarchy task.

        In hierarchy tasks the performer is always a single USER
        (the manager chain). We look for a raw_performer with
        type=USER and return the associated user."""

        raw_performer = (
            task.raw_performers
            .filter(type=PerformerType.USER)
            .select_related('user')
            .first()
        )
        if raw_performer and raw_performer.user_id:
            return raw_performer.user
        return None

    @staticmethod
    def _get_task_performer_name(task: Task) -> str:
        """Get a display name for the task's performer.
        Iterates over prefetched raw_performers to avoid N+1 queries."""

        for raw_performer in task.raw_performers.all():
            if raw_performer.type == PerformerType.USER and raw_performer.user:
                return raw_performer.user.name
        return 'Unknown'

    @staticmethod
    def _truncate_api_name(
        base: str,
        suffix: str,
        max_length: int = 200,
    ) -> str:
        """Truncate base so base+suffix fits max_length."""
        result = f'{base}{suffix}'
        if len(result) > max_length:
            overflow = len(result) - max_length
            result = f'{base[:-overflow]}{suffix}'
        return result

    @classmethod
    def _clone_fields(
        cls,
        source_task: Task,
        target_task: Task,
        workflow: Workflow,
        next_depth: int,
    ) -> None:
        """Instead of cloning original fields, append their values to
        the new task's description and create a single 'Approved' checkbox
        field for the manager to fill out."""

        source_fields = sorted(
            source_task.output.all(),
            key=lambda f: (f.order, f.id),
        )

        if source_fields:
            performer_name = cls._get_task_performer_name(source_task)
            header_md = (
                f'\n\n**Data from {source_task.name} ({performer_name}):**'
            )
            header_txt = (
                f'\n\nData from {source_task.name} ({performer_name}):'
            )

            md_lines = [header_md]
            clear_lines = [header_txt]

            for field in source_fields:
                val = field.markdown_value or field.value or '—'
                clear_val = field.clear_value or field.value or '—'
                md_lines.append(f'- **{field.name}**: {val}')
                clear_lines.append(f'- {field.name}: {clear_val}')

            appended_markdown = '\n'.join(md_lines)
            appended_clear = '\n'.join(clear_lines)

            if target_task.description_template:
                target_task.description_template += appended_markdown
            else:
                target_task.description_template = appended_markdown.strip()

            if target_task.clear_description:
                target_task.clear_description += appended_clear
            else:
                target_task.clear_description = appended_clear.strip()

            target_task.save(
                update_fields=['description_template', 'clear_description'],
            )

        # Create the 'Approval' radio field
        approved_api_name = cls._truncate_api_name(
            'approved-field', f'-h{next_depth}',
        )
        approved_field = TaskField.objects.create(
            account=workflow.account,
            workflow=workflow,
            task=target_task,
            api_name=approved_api_name,
            name='Approval',
            type=FieldType.RADIO,
            description='',
            is_required=True,
            order=1,
        )

        FieldSelection.objects.bulk_create([
            FieldSelection(
                field=approved_field,
                api_name=cls._truncate_api_name(
                    'approved-sel', f'-h{next_depth}',
                ),
                value='Approved',
            ),
            FieldSelection(
                field=approved_field,
                api_name=cls._truncate_api_name(
                    'rejected-sel', f'-h{next_depth}',
                ),
                value='Rejected',
            ),
        ])
