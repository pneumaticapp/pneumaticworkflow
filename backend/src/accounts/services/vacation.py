from typing import List, Set

from django.db.models import Count
from django.contrib.auth import get_user_model
from django.db import transaction

from src.accounts.enums import AbsenceStatus, UserGroupType
from src.accounts.models import UserGroup
from src.notifications.tasks import (
    send_vacation_delegation_notification,
)
from src.processes.enums import (
    DirectlyStatus,
    PerformerType,
    TaskStatus,
)
from src.processes.models.workflows.task import Task, TaskPerformer
from src.processes.models.workflows.workflow import Workflow
from src.processes.services.events import WorkflowEventService

UserModel = get_user_model()

SUBSTITUTE_GROUP_PREFIX = 'Substitutes'


class VacationDelegationService:

    def __init__(self, user: 'UserModel') -> None:
        self.user = user

    @classmethod
    def clear_substitute_groups(
        cls, user: 'UserModel',
    ) -> None:
        """Remove user from all personal (vacation substitute)
        groups. If the group becomes empty after removal,
        auto-deactivate vacation for the group owner.
        """
        with transaction.atomic():
            personal_groups = (
                UserGroup.objects
                .filter(
                    type=UserGroupType.PERSONAL,
                    users=user,
                )
                .annotate(user_count=Count('users'))
                .prefetch_related('vacation_owners')
            )
            owners_to_deactivate = []
            for group in personal_groups:
                group.users.remove(user)
                if group.user_count <= 1:
                    owners_to_deactivate.extend(
                        group.vacation_owners.all(),
                    )
            for owner in owners_to_deactivate:
                cls(owner).deactivate()

    def _notify_substitutes(
        self,
        substitute_user_ids: List[int],
        task_ids: Set[int],
    ) -> None:
        """Send delegation notification to each substitute."""
        if not task_ids:
            return
        substitutes = (
            UserModel.objects
            .filter(id__in=substitute_user_ids)
            .only('id', 'email', 'first_name')
        )
        for sub in substitutes:
            send_vacation_delegation_notification.delay(
                user_id=sub.id,
                user_email=sub.email,
                user_first_name=sub.first_name,
                account_id=self.user.account_id,
                tasks_count=len(task_ids),
                vacation_owner_name=self.user.get_full_name(),
            )

    def activate(
        self,
        substitute_user_ids: List[int],
        absence_status: str = AbsenceStatus.VACATION,
        vacation_start_date=None,
        vacation_end_date=None,
    ) -> None:
        """Activate vacation delegation for the user.

        Creates a personal substitute group, freezes the user's
        task performers, adds the substitute group as a GROUP
        performer on all affected tasks, and mutes notifications.
        """
        with transaction.atomic():
            if (
                self.user.is_absent
                and self.user.vacation_substitute_group
            ):
                self._update_existing(
                    substitute_user_ids=substitute_user_ids,
                    absence_status=absence_status,
                    vacation_start_date=vacation_start_date,
                    vacation_end_date=vacation_end_date,
                )
                return

            self._activate_new(
                substitute_user_ids=substitute_user_ids,
                absence_status=absence_status,
                vacation_start_date=vacation_start_date,
                vacation_end_date=vacation_end_date,
            )

    def _update_existing(
        self,
        substitute_user_ids: List[int],
        absence_status: str,
        vacation_start_date=None,
        vacation_end_date=None,
    ) -> None:
        """Update an already-active vacation delegation."""
        group = self.user.vacation_substitute_group
        group.users.set(substitute_user_ids)

        # Ensure new substitutes have workflow access
        pairs = (
            TaskPerformer.objects
            .filter(group=group)
            .values_list('task_id', 'task__workflow_id')
        )
        task_ids = set()
        wf_ids = set()
        for task_id, wf_id in pairs:
            task_ids.add(task_id)
            wf_ids.add(wf_id)

        self._add_members_bulk(
            wf_ids=wf_ids,
            substitute_user_ids=substitute_user_ids,
        )

        self.user.absence_status = absence_status
        self.user.vacation_start_date = vacation_start_date
        self.user.vacation_end_date = vacation_end_date

        self.user.save(update_fields=[
            'absence_status',
            'vacation_start_date',
            'vacation_end_date',
        ])

        self._notify_substitutes(
            substitute_user_ids=substitute_user_ids,
            task_ids=task_ids,
        )

    def _activate_new(
        self,
        substitute_user_ids: List[int],
        absence_status: str,
        vacation_start_date=None,
        vacation_end_date=None,
    ) -> None:
        """First-time activation of vacation delegation."""

        # 1. Create substitute group
        group = UserGroup.objects.create(
            name=(
                f'{SUBSTITUTE_GROUP_PREFIX}'
                f' {self.user.get_full_name()}'
            ),
            type=UserGroupType.PERSONAL,
            account=self.user.account,
        )
        group.users.set(substitute_user_ids)

        # 2. Freeze personal performers (USER) — bulk
        user_performers = (
            TaskPerformer.objects
            .select_for_update()
            .filter(
                user_id=self.user.id,
                type=PerformerType.USER,
                is_completed=False,
                task__status__in=[
                    TaskStatus.ACTIVE,
                    TaskStatus.DELAYED,
                ],
            )
            .exclude(
                directly_status=DirectlyStatus.DELETED,
            )
            .select_related('task')
        )

        # Collect task_ids before bulk update
        performers_list = list(user_performers)
        task_ids = {p.task_id for p in performers_list}
        performer_ids = [p.id for p in performers_list]

        if performer_ids:
            TaskPerformer.objects.filter(
                id__in=performer_ids,
            ).update(
                directly_status=DirectlyStatus.DELEGATED,
            )

        # Create GROUP performers for substitute group
        group_performers_to_create = [
            TaskPerformer(
                task_id=task_id,
                type=PerformerType.GROUP,
                group=group,
            )
            for task_id in task_ids
        ]
        if group_performers_to_create:
            TaskPerformer.objects.bulk_create(
                group_performers_to_create,
                ignore_conflicts=True,
            )

        # Log delegation events
        for p in performers_list:
            WorkflowEventService.task_delegation_event(
                task=p.task,
                user=self.user,
                substitute_group=group,
            )

        # 3. Handle group tasks (user is member of a
        #    regular group assigned to a task)
        user_group_ids = list(
            self.user.user_groups
            .filter(type=UserGroupType.REGULAR)
            .values_list('id', flat=True),
        )
        # 4. Collect workflow_ids from already-loaded data
        wf_ids = {p.task.workflow_id for p in performers_list}

        if user_group_ids:
            new_task_ids = set(
                TaskPerformer.objects
                .filter(
                    group_id__in=user_group_ids,
                    type=PerformerType.GROUP,
                    task__status__in=[
                        TaskStatus.ACTIVE,
                        TaskStatus.DELAYED,
                    ],
                )
                .exclude(
                    directly_status=DirectlyStatus.DELETED,
                )
                .exclude(task_id__in=task_ids)
                .values_list('task_id', flat=True)
                .distinct(),
            )
            task_ids |= new_task_ids

            if new_task_ids:
                grp_perfs = [
                    TaskPerformer(
                        task_id=tid,
                        type=PerformerType.GROUP,
                        group=group,
                    )
                    for tid in new_task_ids
                ]
                TaskPerformer.objects.bulk_create(
                    grp_perfs,
                    ignore_conflicts=True,
                )
                # Add workflow_ids from group tasks
                wf_ids |= set(
                    Task.objects
                    .filter(id__in=new_task_ids)
                    .values_list('workflow_id', flat=True),
                )

        self._add_members_bulk(
            wf_ids=wf_ids,
            substitute_user_ids=substitute_user_ids,
        )

        # 5. Mute notifications (save originals)
        self.user._saved_notify_about_tasks = (
            self.user.notify_about_tasks
        )
        self.user._saved_is_new_tasks_subscriber = (
            self.user.is_new_tasks_subscriber
        )
        self.user._saved_is_complete_tasks_subscriber = (
            self.user.is_complete_tasks_subscriber
        )
        self.user.notify_about_tasks = False
        self.user.is_new_tasks_subscriber = False
        self.user.is_complete_tasks_subscriber = False

        # 6. Update user status
        self.user.absence_status = absence_status
        self.user.vacation_substitute_group = group
        self.user.vacation_start_date = vacation_start_date
        self.user.vacation_end_date = vacation_end_date

        self.user.save(update_fields=[
            'absence_status',
            'vacation_substitute_group',
            'vacation_start_date',
            'vacation_end_date',
            '_saved_notify_about_tasks',
            '_saved_is_new_tasks_subscriber',
            '_saved_is_complete_tasks_subscriber',
            'notify_about_tasks',
            'is_new_tasks_subscriber',
            'is_complete_tasks_subscriber',
        ])

        self._notify_substitutes(
            substitute_user_ids=substitute_user_ids,
            task_ids=task_ids,
        )

    def deactivate(self) -> None:
        """Deactivate vacation delegation for the user.

        Unfreezes the user's task performers, cascade-deletes
        the substitute group (removing all GROUP performers),
        and restores notification settings.
        """
        with transaction.atomic():
            # 1. Unfreeze performers (only on active tasks)
            TaskPerformer.objects.filter(
                user_id=self.user.id,
                directly_status=DirectlyStatus.DELEGATED,
                task__status__in=[
                    TaskStatus.ACTIVE,
                    TaskStatus.DELAYED,
                ],
            ).update(
                directly_status=DirectlyStatus.NO_STATUS,
            )

            # 2. Delete substitute group performers and group.
            # UserGroup uses soft-delete, so CASCADE won't remove
            # TaskPerformers — delete them explicitly first.
            if self.user.vacation_substitute_group:
                TaskPerformer.objects.filter(
                    group=self.user.vacation_substitute_group,
                ).delete()
                self.user.vacation_substitute_group.delete()

            # 3. Restore notifications
            self._restore_notifications()

            self.user.absence_status = AbsenceStatus.ACTIVE
            self.user.vacation_start_date = None
            self.user.vacation_end_date = None
            self.user.vacation_substitute_group = None
            self.user._saved_notify_about_tasks = None
            self.user._saved_is_new_tasks_subscriber = None
            self.user._saved_is_complete_tasks_subscriber = None
            self.user.save(update_fields=[
                'absence_status',
                'vacation_start_date',
                'vacation_end_date',
                'vacation_substitute_group',
                '_saved_notify_about_tasks',
                '_saved_is_new_tasks_subscriber',
                '_saved_is_complete_tasks_subscriber',
                'notify_about_tasks',
                'is_new_tasks_subscriber',
                'is_complete_tasks_subscriber',
            ])

    def _restore_notifications(self) -> None:
        """Restore notification settings from saved values.

        Falls back to True if saved value is None.
        """
        saved = self.user._saved_notify_about_tasks
        self.user.notify_about_tasks = (
            saved if saved is not None else True
        )
        saved = self.user._saved_is_new_tasks_subscriber
        self.user.is_new_tasks_subscriber = (
            saved if saved is not None else True
        )
        saved = self.user._saved_is_complete_tasks_subscriber
        self.user.is_complete_tasks_subscriber = (
            saved if saved is not None else True
        )

    @staticmethod
    def _add_members_bulk(
        wf_ids: Set[int],
        substitute_user_ids: List[int],
    ) -> None:
        """Bulk-add substitutes to workflow members."""
        members_to_create = [
            Workflow.members.through(
                workflow_id=wf_id,
                user_id=sub_id,
            )
            for wf_id in wf_ids
            for sub_id in substitute_user_ids
        ]
        if members_to_create:
            Workflow.members.through.objects.bulk_create(
                members_to_create,
                ignore_conflicts=True,
            )
