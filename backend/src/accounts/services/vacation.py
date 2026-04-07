from typing import List, Set

from django.contrib.auth import get_user_model
from django.db import transaction

from src.accounts.enums import AbsenceStatus, UserGroupType
from src.accounts.models import UserGroup, UserVacation
from src.notifications.tasks import (
    send_vacation_delegation_notification,
)
from src.processes.enums import (
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
                user.user_groups
                .filter(
                    type=UserGroupType.PERSONAL,
                    is_deleted=False,
                )
                .prefetch_related('vacation_owners')
            )
            owners_to_deactivate = []
            for group in personal_groups:
                group.users.remove(user)
                if not group.users.exists():
                    owners_to_deactivate.extend(
                        [v.user for v in group.vacation_owners.all()],
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
        with transaction.atomic():
            vacation = (
                UserVacation.objects
                .filter(user=self.user)
                .select_related('substitute_group')
                .first()
            )

            if vacation and vacation.substitute_group_id:
                self._update_existing(
                    vacation=vacation,
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
        vacation: 'UserVacation',
        substitute_user_ids: List[int],
        absence_status: str,
        vacation_start_date=None,
        vacation_end_date=None,
    ) -> None:
        group = vacation.substitute_group
        group.users.set(substitute_user_ids)

        pairs = (
            TaskPerformer.objects
            .filter(
                group=group,
                is_completed=False,
                task__status__in=[
                    TaskStatus.ACTIVE,
                    TaskStatus.DELAYED,
                ],
            )
            .exclude_directly_deleted()
            .values_list('task_id', 'task__workflow_id')
        )
        task_ids = set()
        wf_ids = set()
        for task_id, wf_id in pairs:
            task_ids.add(task_id)
            wf_ids.add(wf_id)

        # Create missing group performers for user's direct tasks
        user_performers = list(
            TaskPerformer.objects
            .filter(
                user_id=self.user.id,
                type=PerformerType.USER,
                is_completed=False,
                task__status__in=[
                    TaskStatus.ACTIVE,
                    TaskStatus.DELAYED,
                ],
            )
            .exclude_directly_deleted()
            .exclude(task_id__in=task_ids)
            .select_related('task'),
        )
        new_direct_task_ids = {p.task_id for p in user_performers}
        if new_direct_task_ids:
            TaskPerformer.objects.bulk_create(
                [
                    TaskPerformer(
                        task_id=tid,
                        type=PerformerType.GROUP,
                        group=group,
                    )
                    for tid in new_direct_task_ids
                ],
                ignore_conflicts=True,
            )
            task_ids |= new_direct_task_ids
            wf_ids |= {p.task.workflow_id for p in user_performers}
            for p in user_performers:
                WorkflowEventService.task_delegation_event(
                    task=p.task,
                    user=self.user,
                    substitute_group=group,
                )

        # Create missing group performers for user's regular
        # group tasks
        user_group_ids = list(
            self.user.user_groups
            .filter(type=UserGroupType.REGULAR)
            .values_list('id', flat=True),
        )
        if user_group_ids:
            new_group_task_ids = set(
                TaskPerformer.objects
                .filter(
                    group_id__in=user_group_ids,
                    type=PerformerType.GROUP,
                    is_completed=False,
                    task__status__in=[
                        TaskStatus.ACTIVE,
                        TaskStatus.DELAYED,
                    ],
                )
                .exclude_directly_deleted()
                .exclude(task_id__in=task_ids)
                .values_list('task_id', flat=True)
                .distinct(),
            )
            if new_group_task_ids:
                TaskPerformer.objects.bulk_create(
                    [
                        TaskPerformer(
                            task_id=tid,
                            type=PerformerType.GROUP,
                            group=group,
                        )
                        for tid in new_group_task_ids
                    ],
                    ignore_conflicts=True,
                )
                task_ids |= new_group_task_ids
                new_group_tasks = list(
                    Task.objects.filter(
                        id__in=new_group_task_ids,
                    ),
                )
                wf_ids |= {
                    t.workflow_id for t in new_group_tasks
                }
                for task in new_group_tasks:
                    WorkflowEventService.task_delegation_event(
                        task=task,
                        user=self.user,
                        substitute_group=group,
                    )

        self._add_members_bulk(
            wf_ids=wf_ids,
            substitute_user_ids=substitute_user_ids,
        )

        self.user.absence_status = absence_status
        self.user.save(update_fields=['absence_status'])

        vacation.start_date = vacation_start_date
        vacation.end_date = vacation_end_date
        vacation.save(update_fields=['start_date', 'end_date'])

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
        group = UserGroup.objects.create(
            name=(
                f'{SUBSTITUTE_GROUP_PREFIX}'
                f' {self.user.get_full_name()}'
            ),
            type=UserGroupType.PERSONAL,
            account=self.user.account,
        )
        group.users.set(substitute_user_ids)

        # Do not freeze users (DirectlyStatus.DELEGATED removed).
        # Just create substitute performers alongside the user's performers
        user_performers = (
            TaskPerformer.objects
            .filter(
                user_id=self.user.id,
                type=PerformerType.USER,
                is_completed=False,
                task__status__in=[
                    TaskStatus.ACTIVE,
                    TaskStatus.DELAYED,
                ],
            )
            .exclude_directly_deleted()
            .select_related('task')
        )

        performers_list = list(user_performers)
        task_ids = {p.task_id for p in performers_list}

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

        for p in performers_list:
            WorkflowEventService.task_delegation_event(
                task=p.task,
                user=self.user,
                substitute_group=group,
            )

        user_group_ids = list(
            self.user.user_groups
            .filter(type=UserGroupType.REGULAR)
            .values_list('id', flat=True),
        )
        wf_ids = {p.task.workflow_id for p in performers_list}

        if user_group_ids:
            new_task_ids = set(
                TaskPerformer.objects
                .filter(
                    group_id__in=user_group_ids,
                    type=PerformerType.GROUP,
                    is_completed=False,
                    task__status__in=[
                        TaskStatus.ACTIVE,
                        TaskStatus.DELAYED,
                    ],
                )
                .exclude_directly_deleted()
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
                new_tasks = list(
                    Task.objects.filter(id__in=new_task_ids),
                )
                wf_ids |= {t.workflow_id for t in new_tasks}
                for task in new_tasks:
                    WorkflowEventService.task_delegation_event(
                        task=task,
                        user=self.user,
                        substitute_group=group,
                    )

        self._add_members_bulk(
            wf_ids=wf_ids,
            substitute_user_ids=substitute_user_ids,
        )

        self.user.absence_status = absence_status
        self.user.save(update_fields=[
            'absence_status',
        ])

        UserVacation.objects.update_or_create(
            user=self.user,
            defaults={
                'substitute_group': group,
                'start_date': vacation_start_date,
                'end_date': vacation_end_date,
            },
        )

        self._notify_substitutes(
            substitute_user_ids=substitute_user_ids,
            task_ids=task_ids,
        )

    def deactivate(self) -> None:
        with transaction.atomic():
            vacation = (
                UserVacation.objects
                .filter(user=self.user)
                .select_related('substitute_group')
                .first()
            )
            if not vacation:
                return

            # Delete substitute group performers and group.
            substitute_group = vacation.substitute_group
            if substitute_group:
                TaskPerformer.objects.filter(
                    group=substitute_group,
                ).delete()
                substitute_group.delete()

            self.user.absence_status = AbsenceStatus.ACTIVE
            self.user.save(update_fields=['absence_status'])
            vacation.delete()

    @staticmethod
    def _add_members_bulk(
        wf_ids: Set[int],
        substitute_user_ids: List[int],
    ) -> None:
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
