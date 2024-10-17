from os import environ
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.models import Task
from pneumatic_backend.processes.api_v2.services.task.exceptions import (
    PerformersServiceException
)
from pneumatic_backend.processes.api_v2.services.task.base import (
    BasePerformersService,
)
from pneumatic_backend.accounts.services.guests import GuestService
from pneumatic_backend.processes.messages.workflow import (
    MSG_PW_0014,
    MSG_PW_0015,
)
from pneumatic_backend.authentication.services import (
    GuestJWTAuthService
)
from pneumatic_backend.analytics.services import AnalyticService
from pneumatic_backend.notifications.tasks import (
    send_guest_new_task,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowEventService,
)
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService
)


UserModel = get_user_model()


class GuestPerformersService(BasePerformersService):

    """ Service describes methods for change
        task performers with type 'GUEST' """

    MAX_GUEST_PERFORMERS = environ.get('MAX_GUEST_PERFORMERS', 30)

    @classmethod
    def _get_user_for_create(
        cls,
        account_id: int,
        user_key: str,
    ) -> UserModel:
        return GuestService.get_or_create(
            email=user_key,
            account_id=account_id
        )

    @classmethod
    def _get_user_for_delete(
        cls,
        account_id: int,
        user_key: str,
    ) -> UserModel:
        try:
            user = UserModel.guests_objects.get(
                email=user_key,
                account_id=account_id
            )
        except UserModel.DoesNotExist:
            raise PerformersServiceException(MSG_PW_0014)
        else:
            return user

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
        GuestJWTAuthService.deactivate_task_guest_cache(
            task_id=task.id,
            user_id=user.id
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

    @classmethod
    def _validate_create(
        cls,
        task: Task,
        request_user: UserModel
    ):
        guest_performers = task.taskperformer_set.guests(
        ).exclude_directly_deleted()
        if guest_performers.count() == cls.MAX_GUEST_PERFORMERS:
            raise PerformersServiceException(MSG_PW_0015)

    @classmethod
    def _create_actions(
        cls,
        task: Task,
        user: UserModel,
        request_user: UserModel,
        current_url: str,
        is_superuser: bool
    ):
        WorkflowEventService.performer_created_event(
            user=request_user,
            task=task,
            performer=user,
        )
        send_guest_new_task.delay(
            token=GuestJWTAuthService.get_str_token(
                task_id=task.id,
                user_id=user.id,
                account_id=user.account.id
            ),
            sender_name=request_user.get_full_name(),
            user_id=user.id,
            user_email=user.email,
            task_id=task.id,
            task_name=task.name,
            task_description=task.description,
            task_due_date=task.due_date,
            logo_lg=user.account.logo_lg,
        )
        GuestJWTAuthService.activate_task_guest_cache(
            task_id=task.id,
            user_id=user.id
        )
        AnalyticService.users_guest_invite_sent(
            invite_from=request_user,
            invite_to=user,
            current_url=current_url,
            is_superuser=is_superuser
        )
        AnalyticService.users_guest_invited(
            invite_to=user,
            is_superuser=is_superuser
        )
