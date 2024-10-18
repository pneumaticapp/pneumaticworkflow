from django.contrib.auth import get_user_model
from pneumatic_backend.accounts.enums import UserStatus
from pneumatic_backend.processes.models import Task
from pneumatic_backend.processes.messages.workflow import (
    MSG_PW_0014
)
from pneumatic_backend.processes.services.websocket import WSSender
from pneumatic_backend.notifications.tasks import send_new_task_notification
from pneumatic_backend.processes.api_v2.services.task.base import (
    BasePerformersService,
)
from pneumatic_backend.processes.api_v2.services.task.exceptions import (
    PerformersServiceException
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowEventService
)
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService
)

UserModel = get_user_model()


class TaskPerformersService(BasePerformersService):

    """ Service describes methods for change
        task performers with type 'USER' """

    @classmethod
    def _get_user_for_create(
        cls,
        account_id: int,
        user_key: int,
    ) -> UserModel:
        try:
            return UserModel.objects.get(
                account_id=account_id,
                id=user_key,
                status__in=(UserStatus.ACTIVE, UserStatus.INVITED)
            )
        except UserModel.DoesNotExist:
            raise PerformersServiceException(MSG_PW_0014)

    @classmethod
    def _get_user_for_delete(
        cls,
        account_id: int,
        user_key: int,
    ) -> UserModel:
        try:
            return UserModel.include_inactive.on_account(
                account_id
            ).type_user().by_id(user_key).get()
        except UserModel.DoesNotExist:
            raise PerformersServiceException(MSG_PW_0014)

    @classmethod
    def _delete_actions(
        cls,
        task: Task,
        user: UserModel,
        request_user: UserModel
    ):
        WorkflowEventService.performer_deleted_event(
            user=request_user,
            task=task,
            performer=user
        )
        if task.can_be_completed():
            first_completed_user = task.taskperformer_set.completed(
            ).exclude_directly_deleted().first().user
            service = WorkflowActionService(
                user=first_completed_user,
                is_superuser=False,
                auth_type=AuthTokenType.USER
            )
            service.complete_task(task=task)
        else:
            WSSender.send_removed_task_notification(
                task=task,
                user_ids=(user.id,)
            )

    @classmethod
    def _create_actions(
        cls,
        task: Task,
        user: UserModel,
        request_user: UserModel,
        **kwargs
    ):
        WorkflowEventService.performer_created_event(
            user=request_user,
            task=task,
            performer=user
        )
        if not task.get_active_delay():
            task.workflow.members.add(user)
            if user.account_id == request_user.account_id:
                WSSender.send_new_task_notification(
                    task=task,
                    user_ids=(user.id,)
                )
                if user.id != request_user.id:
                    workflow = task.workflow
                    wf_starter = workflow.workflow_starter
                    wf_starter_name = wf_starter.name if wf_starter else None
                    wf_starter_photo = wf_starter.photo if wf_starter else None
                    send_new_task_notification.delay(
                        logging=request_user.account.log_api_requests,
                        recipients=[(user.id, user.email)],
                        task_id=task.id,
                        task_name=task.name,
                        task_description=task.description,
                        workflow_name=workflow.name,
                        template_name=workflow.get_template_name(),
                        workflow_starter_name=wf_starter_name,
                        workflow_starter_photo=wf_starter_photo,
                        due_date_timestamp=(
                            task.due_date.timestamp()
                            if task.due_date else None
                        ),
                        logo_lg=task.account.logo_lg,
                        is_returned=False,
                    )
