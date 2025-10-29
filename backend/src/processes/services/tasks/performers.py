from django.contrib.auth import get_user_model

from src.accounts.enums import UserStatus
from src.analysis.services import AnalyticService
from src.authentication.enums import AuthTokenType
from src.notifications.tasks import (
    send_new_task_notification,
    send_new_task_websocket,
    send_removed_task_notification,
)
from src.processes.enums import PerformerType
from src.processes.messages.workflow import (
    MSG_PW_0014,
)
from src.processes.models.workflows.task import Task
from src.processes.services.tasks.base import (
    BasePerformersService,
)
from src.processes.services.tasks.exceptions import (
    PerformersServiceException,
)
from src.processes.services.workflow_action import (
    WorkflowActionService,
    WorkflowEventService,
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
                status__in=(UserStatus.ACTIVE, UserStatus.INVITED),
            )
        except UserModel.DoesNotExist as ex:
            raise PerformersServiceException(MSG_PW_0014) from ex

    @classmethod
    def _get_user_for_delete(
        cls,
        account_id: int,
        user_key: int,
    ) -> UserModel:
        try:
            return UserModel.include_inactive.on_account(
                account_id,
            ).type_user().by_id(user_key).get()
        except UserModel.DoesNotExist as ex:
            raise PerformersServiceException(MSG_PW_0014) from ex

    @classmethod
    def _delete_actions(
        cls,
        task: Task,
        user: UserModel,
        request_user: UserModel,
        is_superuser: bool,
        auth_type: AuthTokenType,
    ):
        WorkflowEventService.performer_deleted_event(
            user=request_user,
            task=task,
            performer=user,
        )
        AnalyticService.task_performer_deleted(
            user=request_user,
            performer=user,
            task=task,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )
        if task.can_be_completed():
            first_completed_user = (
                task.taskperformer_set.completed()
                .exclude_directly_deleted()
                .exclude(type=PerformerType.GROUP)
                .first().user
            )
            if first_completed_user is None:
                group = (
                    task.taskperformer_set.completed()
                    .exclude_directly_deleted()
                    .filter(type=PerformerType.GROUP)
                    .first()
                    .group
                )
                first_completed_user = group.users.first().user
            service = WorkflowActionService(
                workflow=task.workflow,
                user=first_completed_user,
                is_superuser=False,
                auth_type=AuthTokenType.USER,
            )
            service.complete_task(task=task)
        else:
            task_performers = (
                UserModel.objects
                .get_users_taskperformer_groups(task=task)
                .user_ids_set()
            )
            if user.id not in task_performers:
                send_removed_task_notification.delay(
                    task_id=task.id,
                    recipients=[(user.id, user.email)],
                    account_id=task.account_id,
                )

    @classmethod
    def _create_actions(
        cls,
        task: Task,
        user: UserModel,
        request_user: UserModel,
        is_superuser: bool,
        auth_type: AuthTokenType,
        **kwargs,
    ):
        WorkflowEventService.performer_created_event(
            user=request_user,
            task=task,
            performer=user,
        )
        AnalyticService.task_performer_created(
            user=request_user,
            performer=user,
            task=task,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )
        if not task.get_active_delay():
            task.workflow.members.add(user)
            task_performer_users = (
                UserModel.objects
                .get_users_taskperformer_groups(task=task)
                .user_ids_set()
            )
            if (
                user.account_id == request_user.account_id
                and user.id not in task_performer_users
            ):
                if user.id == request_user.id:
                    send_new_task_websocket.delay(
                        logging=task.account.log_api_requests,
                        task_id=task.id,
                        recipients=[
                            (
                                user.id,
                                user.email,
                                user.is_new_tasks_subscriber,
                            ),
                        ],
                        account_id=task.account_id,
                    )
                else:
                    workflow = task.workflow
                    wf_starter = workflow.workflow_starter
                    wf_starter_name = wf_starter.name if wf_starter else None
                    wf_starter_photo = wf_starter.photo if wf_starter else None
                    recipients = [(
                        user.id,
                        user.email,
                        user.is_new_tasks_subscriber,
                    )]
                    send_new_task_notification.delay(
                        logging=request_user.account.log_api_requests,
                        account_id=request_user.account_id,
                        recipients=recipients,
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
