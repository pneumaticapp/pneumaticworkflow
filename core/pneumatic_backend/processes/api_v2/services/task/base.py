from abc import abstractmethod
from typing import Optional, Union, Tuple
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.models import (
    Task,
    TaskPerformer
)
from pneumatic_backend.processes.enums import (
    DirectlyStatus,
    WorkflowStatus
)
from pneumatic_backend.processes.api_v2.services.task.exceptions import (
    PerformersServiceException
)
from pneumatic_backend.processes.messages.workflow import (
    MSG_PW_0016,
    MSG_PW_0017,
    MSG_PW_0018,
    MSG_PW_0021,
)


UserModel = get_user_model()


class BasePerformersService:

    @classmethod
    @abstractmethod
    def _get_user_for_create(
        cls,
        account_id: int,
        user_key: Union[int, str],
    ) -> UserModel:
        pass

    @classmethod
    @abstractmethod
    def _get_user_for_delete(
        cls,
        account_id: int,
        user_key: Union[int, str],
    ) -> UserModel:
        pass

    @classmethod
    @abstractmethod
    def _create_actions(
        cls,
        task: Task,
        user: UserModel,
        request_user: UserModel,
        current_url: str,
        is_superuser: bool
    ):
        pass

    @classmethod
    @abstractmethod
    def _delete_actions(
        cls,
        task: Task,
        user: UserModel,
        request_user: UserModel
    ):
        pass

    @classmethod
    def _validate(
        cls,
        task: Task,
        request_user: UserModel
    ):

        workflow = task.workflow
        if workflow.status in WorkflowStatus.END_STATUSES:
            raise PerformersServiceException(MSG_PW_0017)
        if task.number != workflow.current_task:
            raise PerformersServiceException(MSG_PW_0018)

        if not request_user.is_admin:
            raise PerformersServiceException(MSG_PW_0021)
        if not request_user.is_account_owner:
            request_user_is_template_owner = False
            if not workflow.is_legacy_template:
                request_user_is_template_owner = (
                    workflow.template.template_owners.filter(
                        id=request_user.id
                    ).exists()
                )
            if not request_user_is_template_owner:
                user_is_task_performer = task.taskperformer_set.filter(
                    user_id=request_user.id
                ).exclude_directly_deleted().exists()
                if not user_is_task_performer:
                    raise PerformersServiceException(MSG_PW_0021)

    @classmethod
    def _validate_create(
        cls,
        task: Task,
        request_user: UserModel
    ):
        pass

    @classmethod
    def _get_valid_deleted_task_performer(
        cls,
        task: Task,
        user: UserModel
    ) -> Optional[TaskPerformer]:

        performers_ids = list(
            TaskPerformer.objects.by_task(
                task.id
            ).exclude_directly_deleted().user_ids()
        )
        if len(performers_ids) == 1 and user.id == performers_ids[0]:
            raise PerformersServiceException(MSG_PW_0016)
        return TaskPerformer.objects.filter(
            task_id=task.id,
            user_id=user.id,
        ).first()

    @classmethod
    def create_performer(
        cls,
        task: Task,
        current_url: str,
        is_superuser: bool,
        user_key: Union[int, str],
        request_user: UserModel,
        run_actions: bool = True,
    ) -> Tuple[UserModel, TaskPerformer]:

        cls._validate(task=task, request_user=request_user)
        cls._validate_create(task=task, request_user=request_user)
        user = cls._get_user_for_create(
            account_id=request_user.account.id,
            user_key=user_key
        )
        task_performer, created = TaskPerformer.objects.get_or_create(
            task_id=task.id,
            user_id=user.id,
            defaults={'directly_status': DirectlyStatus.CREATED}
        )
        if task_performer.directly_status == DirectlyStatus.DELETED:
            task_performer.directly_status = DirectlyStatus.CREATED
            task_performer.save()
            created = True
        if created and run_actions:
            cls._create_actions(
                task=task,
                user=user,
                request_user=request_user,
                current_url=current_url,
                is_superuser=is_superuser
            )
        return user, task_performer

    @classmethod
    def delete_performer(
        cls,
        task: Task,
        user_key: Union[int, str],
        request_user: UserModel,
        run_actions: bool = True
    ):

        cls._validate(task=task, request_user=request_user)
        user = cls._get_user_for_delete(
            user_key=user_key,
            account_id=request_user.account_id
        )
        task_performer = cls._get_valid_deleted_task_performer(
            task=task,
            user=user
        )
        if task_performer is not None:
            task_performer.directly_status = DirectlyStatus.DELETED
            task_performer.save()
            if run_actions:
                cls._delete_actions(
                    task=task,
                    user=user,
                    request_user=request_user
                )
