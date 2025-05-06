from django.contrib.auth import get_user_model
from pneumatic_backend.processes.api_v2.services.task.base import (
    BasePerformerService2
)
from pneumatic_backend.accounts.models import UserGroup
from pneumatic_backend.analytics.services import AnalyticService
from pneumatic_backend.processes.models import (
    TaskPerformer
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.api_v2.services.task.exceptions import (
    GroupPerformerServiceException
)
from pneumatic_backend.processes.enums import DirectlyStatus
from pneumatic_backend.processes.messages.workflow import MSG_PW_0082
from pneumatic_backend.processes.enums import PerformerType
from pneumatic_backend.processes.services.websocket import WSSender
from pneumatic_backend.notifications.tasks import send_new_task_notification
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowEventService
)
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService
)


UserModel = get_user_model()


class GroupPerformerService(BasePerformerService2):
    def _get_group(
        self,
        group_id: int,
    ) -> UserModel:
        try:
            return UserGroup.objects.get(
                account_id=self.user.account_id,
                id=group_id
            )
        except UserGroup.DoesNotExist:
            raise GroupPerformerServiceException(MSG_PW_0082)

    def create_performer(
        self,
        group_id: int,
        run_actions: bool = True,
    ) -> None:
        self._validate()
        self._validate_create()
        group = self._get_group(group_id=group_id)
        task_performer, created = TaskPerformer.objects.get_or_create(
            task_id=self.task.id,
            type=PerformerType.GROUP,
            group_id=group.id,
            defaults={'directly_status': DirectlyStatus.CREATED}
        )
        if task_performer.directly_status == DirectlyStatus.DELETED:
            task_performer.directly_status = DirectlyStatus.CREATED
            task_performer.save()
            created = True
        if created and run_actions:
            self._create_group_actions(group=group)

    def delete_performer(
        self,
        group_id: int,
        run_actions: bool = True
    ) -> None:
        self._validate()
        group = self._get_group(group_id=group_id)
        task_performer = self._get_valid_deleted_task_performer(group=group)
        if task_performer is not None:
            task_performer.directly_status = DirectlyStatus.DELETED
            task_performer.save()
            if run_actions:
                self._delete_group_actions(group=group)

    def _delete_group_actions(self, group: UserGroup) -> None:
        WorkflowEventService.performer_group_deleted_event(
            user=self.user,
            task=self.task,
            performer=group
        )
        AnalyticService.task_group_performer_deleted(
            user=self.user,
            performer=group,
            task=self.task,
            auth_type=self.auth_type,
            is_superuser=self.is_superuser
        )
        if self.task.can_be_completed():
            first_completed_user = (
                self.task.taskperformer_set.completed()
                .exclude_directly_deleted()
                .exclude(type=PerformerType.GROUP)
                .first().user
            )
            if first_completed_user is None:
                group = (
                    self.task.taskperformer_set.completed()
                    .exclude_directly_deleted()
                    .filter(type=PerformerType.GROUP)
                    .first()
                    .group
                )
                first_completed_user = group.users.first().user
            service = WorkflowActionService(
                user=first_completed_user,
                workflow=self.task.workflow,
                is_superuser=False,
                auth_type=AuthTokenType.USER
            )
            service.complete_task(task=self.task)
        else:
            group_users_ids = set(group.users.values_list('id', flat=True))
            task_performer_ids = (
                UserModel.objects
                .get_users_task_except_group(
                    task=self.task,
                    exclude_group=group
                )
                .exclude_directly_deleted()
                .user_ids_set()
            )
            new_users_performers_ids = tuple(
                group_users_ids - task_performer_ids
            )
            WSSender.send_removed_task_notification(
                task=self.task,
                user_ids=new_users_performers_ids
            )

    def _create_group_actions(self, group: UserGroup) -> None:
        WorkflowEventService.performer_group_created_event(
            user=self.user,
            task=self.task,
            performer=group
        )
        AnalyticService.task_group_performer_created(
            user=self.user,
            performer=group,
            task=self.task,
            auth_type=self.auth_type,
            is_superuser=self.is_superuser
        )
        group_users = set(group.users.values_list('id', flat=True))
        task_performer_users = (
            UserModel.objects
            .get_users_task_except_group(
                task=self.task,
                exclude_group=group
            ).exclude_directly_deleted()
            .user_ids_set()
        )
        users = group_users - task_performer_users
        if users and not self.task.get_active_delay():
            self.task.workflow.members.add(*users)
            users_in_account = UserModel.objects.get_users_in_account(
                account_id=self.user.account_id,
                user_ids=users
            )
            user_ids_to_notify = users_in_account.only_ids()
            if user_ids_to_notify:
                WSSender.send_new_task_notification(
                    task=self.task,
                    user_ids=user_ids_to_notify
                )
            recipients = (
                users_in_account
                .exclude(id=self.user.id)
                .user_ids_emails_list()
            )
            if recipients:
                workflow = self.task.workflow
                wf_starter = workflow.workflow_starter
                wf_starter_name = wf_starter.name if wf_starter else None
                wf_starter_photo = wf_starter.photo if wf_starter else None

                send_new_task_notification.delay(
                    logging=self.user.account.log_api_requests,
                    account_id=self.user.account_id,
                    recipients=recipients,
                    task_id=self.task.id,
                    task_name=self.task.name,
                    task_description=self.task.description,
                    workflow_name=workflow.name,
                    template_name=workflow.get_template_name(),
                    workflow_starter_name=wf_starter_name,
                    workflow_starter_photo=wf_starter_photo,
                    due_date_timestamp=(
                        self.task.due_date.timestamp()
                        if self.task.due_date else None
                    ),
                    logo_lg=self.task.account.logo_lg,
                    is_returned=False,
                )
