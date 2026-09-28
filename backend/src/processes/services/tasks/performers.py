from django.contrib.auth import get_user_model

from src.accounts.enums import UserStatus
from src.analysis.services import AnalyticService
from src.authentication.enums import AuthTokenType
from src.notifications.tasks import (
    send_new_task_notification,
    send_new_task_websocket,
    send_task_deleted_notification,
)
from src.permissions.enums import PermissionSource
from src.processes.enums import PerformerType
from src.processes.messages.workflow import (
    MSG_PW_0014,
)
from src.processes.models.workflows.task import Task
from src.processes.services.tasks.base import (
    BasePerformersService,
)
from src.processes.services.tasks.exceptions import (
    GroupPerformerServiceException,
    PerformersServiceException,
)
from src.processes.services.tasks.groups import (
    GroupPerformerService,
)
from src.processes.services.workflow_action import (
    WorkflowActionService,
    WorkflowEventService,
)
from src.processes.services.workflow_permissions import (
    WorkflowPermissionService,
)
from src.storage.tasks import (
    schedule_sync_workflow_attachment_permissions,
)
from src.storage.utils import reassign_restricted_permissions_for_task

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

        schedule = user.vacation
        sub_group_id = schedule.substitute_group_id if schedule else None
        if sub_group_id:
            try:
                group_service = GroupPerformerService(
                    user=request_user,
                    task=task,
                    is_superuser=is_superuser,
                    auth_type=auth_type,
                )
                group_service.delete_performer(
                    group_id=sub_group_id,
                    run_actions=False,
                )
                # run_actions=False skips events/notifications, but
                # PERFORMER_GROUP UOP must still be realigned.
                WorkflowPermissionService(
                    task.workflow,
                ).sync_performer_group(
                    group_id=sub_group_id,
                )
            except GroupPerformerServiceException:
                pass

        if task.can_be_completed():
            first_completed = (
                task.taskperformer_set.completed()
                .exclude_directly_deleted()
                .exclude(type=PerformerType.GROUP)
                .first()
            )
            first_completed_user = (
                first_completed.user if first_completed else None
            )
            if first_completed_user is None:
                group_performer = (
                    task.taskperformer_set.completed()
                    .exclude_directly_deleted()
                    .filter(type=PerformerType.GROUP)
                    .first()
                )
                if group_performer and group_performer.group_id:
                    first_completed_user = (
                        group_performer.group.users.first()
                    )
            if first_completed_user is not None:
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
                send_task_deleted_notification.delay(
                    task_id=task.id,
                    recipients=[(user.id, user.email)],
                    account_id=task.account_id,
                )

        remaining_user_ids = (
            task.taskperformer_set
            .exclude_directly_deleted()
            .filter(type=PerformerType.USER)
            .values_list('user_id', flat=True)
        )
        WorkflowPermissionService(task.workflow).sync_view(
            user_ids=remaining_user_ids,
            source_type=PermissionSource.PERFORMER,
            source_id=task.id,
        )

        reassign_restricted_permissions_for_task(
            task=task,
            user=request_user,
        )

        # Sync attachment permissions so removed performer loses file access
        schedule_sync_workflow_attachment_permissions(task.workflow_id)

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
        WorkflowPermissionService(task.workflow).grant_view(
            user=user,
            source_type=PermissionSource.PERFORMER,
            source_id=task.id,
        )
        schedule_sync_workflow_attachment_permissions(task.workflow_id)
        if not task.get_active_delay():
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

        reassign_restricted_permissions_for_task(
            task=task,
            user=request_user,
        )
