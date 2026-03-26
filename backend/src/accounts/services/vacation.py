from django.contrib.auth import get_user_model
from django.db import transaction

from src.accounts.enums import AbsenceStatus, UserGroupType
from src.notifications.tasks import (
    send_vacation_delegation_notification,
)
from src.processes.enums import (
    DirectlyStatus,
    PerformerType,
    TaskStatus,
)
from src.processes.models.workflows.task import TaskPerformer


class VacationDelegationService:

    def __init__(self, user):
        self.user = user

    def activate(
        self,
        substitute_user_ids: list,
        absence_status: str = AbsenceStatus.VACATION,
    ):
        """Activate vacation delegation for the user.

        Creates a personal substitute group, freezes the user's
        task performers, adds the substitute group as a GROUP
        performer on all affected tasks, and mutes notifications.
        """
        from src.accounts.models import UserGroup  # noqa: PLC0415
        from src.processes.models.workflows.task import Task  # noqa: PLC0415
        from src.processes.models.workflows.workflow import Workflow  # noqa: PLC0415
        from src.processes.services.events import WorkflowEventService  # noqa: PLC0415

        with transaction.atomic():
            if self.user.is_absent and self.user.vacation_substitute_group:
                group = self.user.vacation_substitute_group
                group.users.set(substitute_user_ids)

                # Ensure new substitutes have workflow access
                task_ids = (
                    TaskPerformer.objects
                    .filter(group=group)
                    .values_list('task_id', flat=True)
                    .distinct()
                )
                wf_ids = (
                    Task.objects
                    .filter(id__in=task_ids)
                    .values_list('workflow_id', flat=True)
                    .distinct()
                )
                for wf_id in wf_ids:
                    for sub_id in substitute_user_ids:
                        Workflow.members.through.objects.get_or_create(
                            workflow_id=wf_id,
                            user_id=sub_id,
                        )

                self.user.absence_status = absence_status
                self.user.save(update_fields=['absence_status'])

                if task_ids:
                    substitutes = get_user_model().objects.filter(
                        id__in=substitute_user_ids,
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

                return

            # 1. Create substitute group
            group = UserGroup.objects.create(
                name=f"Substitutes {self.user.get_full_name()}",
                type=UserGroupType.PERSONAL,
                account=self.user.account,
            )
            group.users.set(substitute_user_ids)

            # 2. Freeze personal performers (USER)
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
            task_ids = set()
            for p in user_performers:
                p.directly_status = DirectlyStatus.DELEGATED
                p.save(update_fields=['directly_status'])
                TaskPerformer.objects.get_or_create(
                    task_id=p.task_id,
                    type=PerformerType.GROUP,
                    group=group,
                )
                task_ids.add(p.task_id)
                WorkflowEventService.task_delegation_event(
                    task=p.task,
                    user=self.user,
                    substitute_group=group,
                )

            # 3. Handle group tasks (user is member of a group
            #    assigned to a task)
            user_group_ids = list(
                self.user.user_groups
                .filter(type=UserGroupType.REGULAR)
                .values_list('id', flat=True),
            )
            if user_group_ids:
                group_performers = (
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
                )
                for gp in group_performers:
                    if gp.task_id not in task_ids:
                        TaskPerformer.objects.get_or_create(
                            task_id=gp.task_id,
                            type=PerformerType.GROUP,
                            group=group,
                        )
                        task_ids.add(gp.task_id)

            # 4. Add substitutes to workflow.members
            wf_ids = (
                Task.objects
                .filter(id__in=task_ids)
                .values_list('workflow_id', flat=True)
                .distinct()
            )
            for wf_id in wf_ids:
                for sub_id in substitute_user_ids:
                    Workflow.members.through.objects.get_or_create(
                        workflow_id=wf_id,
                        user_id=sub_id,
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
            self.user.save()

            if task_ids:
                substitutes = get_user_model().objects.filter(
                    id__in=substitute_user_ids,
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

    def deactivate(self):
        """Deactivate vacation delegation for the user.

        Unfreezes the user's task performers, cascade-deletes
        the substitute group (removing all GROUP performers),
        and restores notification settings.
        """
        with transaction.atomic():
            # 1. Unfreeze performers
            TaskPerformer.objects.filter(
                user_id=self.user.id,
                directly_status=DirectlyStatus.DELEGATED,
            ).update(
                directly_status=DirectlyStatus.NO_STATUS,
            )

            # 2. Delete substitute group (CASCADE)
            if self.user.vacation_substitute_group:
                self.user.vacation_substitute_group.delete()

            # 3. Restore notifications
            self.user.notify_about_tasks = (
                self.user._saved_notify_about_tasks
                if self.user._saved_notify_about_tasks is not None
                else True
            )
            self.user.is_new_tasks_subscriber = (
                self.user._saved_is_new_tasks_subscriber
                if self.user._saved_is_new_tasks_subscriber
                is not None
                else True
            )
            self.user.is_complete_tasks_subscriber = (
                self.user._saved_is_complete_tasks_subscriber
                if self.user._saved_is_complete_tasks_subscriber
                is not None
                else True
            )
            self.user.absence_status = AbsenceStatus.ACTIVE
            self.user.vacation_start_date = None
            self.user.vacation_end_date = None
            self.user.vacation_substitute_group = None
            self.user._saved_notify_about_tasks = None
            self.user._saved_is_new_tasks_subscriber = None
            self.user._saved_is_complete_tasks_subscriber = None
            self.user.save()
