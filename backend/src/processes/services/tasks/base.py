from abc import abstractmethod
from typing import Optional, Tuple, Union

from django.contrib.auth import get_user_model

from src.accounts.models import UserGroup
from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    DirectlyStatus,
    PerformerType,
)
from src.processes.messages.workflow import (
    MSG_PW_0016,
    MSG_PW_0017,
    MSG_PW_0018,
    MSG_PW_0021,
)
from src.processes.models.templates.template import Template
from src.processes.models.workflows.task import Task, TaskPerformer
from src.processes.services.tasks.exceptions import (
    GroupPerformerServiceException,
    PerformersServiceException,
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
        is_superuser: bool,
        auth_type: AuthTokenType,
    ):
        pass

    @classmethod
    @abstractmethod
    def _delete_actions(
        cls,
        task: Task,
        user: UserModel,
        request_user: UserModel,
        is_superuser: bool,
        auth_type: AuthTokenType,
    ):
        pass

    @classmethod
    def _validate(
        cls,
        task: Task,
        request_user: UserModel,
    ):

        workflow = task.workflow
        if workflow.is_completed:
            raise PerformersServiceException(MSG_PW_0017)
        if not task.is_active:
            raise PerformersServiceException(MSG_PW_0018)

        if not request_user.is_admin:
            raise PerformersServiceException(MSG_PW_0021)
        if not request_user.is_account_owner:
            tempalate_owners_ids = []
            if not workflow.is_legacy_template:
                tempalate_owners_ids = Template.objects.filter(
                    id=workflow.template.id,
                ).get_owners_as_users()
            if request_user.id not in tempalate_owners_ids:
                user_is_task_performer = task.taskperformer_set.filter(
                    user_id=request_user.id,
                ).exclude_directly_deleted().exists()
                if not user_is_task_performer:
                    raise PerformersServiceException(MSG_PW_0021)

    @classmethod
    def _validate_create(
        cls,
        task: Task,
        request_user: UserModel,
    ):
        pass

    @classmethod
    def _get_valid_deleted_task_performer(
        cls,
        task: Task,
        user: UserModel,
    ) -> Optional[TaskPerformer]:
        performers = (
            TaskPerformer.objects.by_task(task.id).exclude_directly_deleted()
        )
        if (
            performers.count() == 1
            and performers.filter(user_id=user.id).exists()
        ):
            raise PerformersServiceException(MSG_PW_0016)
        return performers.filter(user_id=user.id).first()

    @classmethod
    def create_performer(
        cls,
        task: Task,
        current_url: str,
        is_superuser: bool,
        auth_type: AuthTokenType,
        user_key: Union[int, str],
        request_user: UserModel,
        run_actions: bool = True,
    ) -> Tuple[UserModel, TaskPerformer]:

        cls._validate(task=task, request_user=request_user)
        cls._validate_create(task=task, request_user=request_user)
        user = cls._get_user_for_create(
            account_id=request_user.account.id,
            user_key=user_key,
        )
        task_performer, created = TaskPerformer.objects.get_or_create(
            task_id=task.id,
            type=PerformerType.USER,
            user_id=user.id,
            defaults={'directly_status': DirectlyStatus.CREATED},
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
                is_superuser=is_superuser,
                auth_type=auth_type,
            )
        return user, task_performer

    @classmethod
    def delete_performer(
        cls,
        task: Task,
        user_key: Union[int, str],
        request_user: UserModel,
        is_superuser: bool,
        auth_type: AuthTokenType,
        run_actions: bool = True,
    ):

        cls._validate(task=task, request_user=request_user)
        user = cls._get_user_for_delete(
            user_key=user_key,
            account_id=request_user.account_id,
        )
        task_performer = cls._get_valid_deleted_task_performer(
            task=task,
            user=user,
        )
        if task_performer is not None:
            task_performer.directly_status = DirectlyStatus.DELETED
            task_performer.save()
            if run_actions:
                cls._delete_actions(
                    task=task,
                    user=user,
                    request_user=request_user,
                    is_superuser=is_superuser,
                    auth_type=auth_type,
                )


class BasePerformerService2:
    def __init__(
        self,
        user: UserModel,
        task: Task,
        is_superuser: bool,
        auth_type: AuthTokenType.LITERALS,
        instance: Optional[TaskPerformer] = None,
    ):
        self.is_superuser = is_superuser
        self.auth_type = auth_type
        self.instance = instance
        self.user = user
        self.task = task

    def _validate(self):

        workflow = self.task.workflow
        if workflow.is_completed:
            raise GroupPerformerServiceException(MSG_PW_0017)
        if not self.task.is_active:
            raise GroupPerformerServiceException(MSG_PW_0018)

        if not self.user.is_admin:
            raise GroupPerformerServiceException(MSG_PW_0021)
        if not self.user.is_account_owner:
            tempalate_owners_ids = []
            if not workflow.is_legacy_template:
                tempalate_owners_ids = Template.objects.filter(
                    id=workflow.template.id,
                ).get_owners_as_users()
            if self.user.id not in tempalate_owners_ids:
                user_is_task_performer = self.task.taskperformer_set.filter(
                    user_id=self.user.id,
                ).exclude_directly_deleted().exists()
                if not user_is_task_performer:
                    raise GroupPerformerServiceException(MSG_PW_0021)

    def _validate_create(self):
        pass

    def _get_valid_deleted_task_performer(
        self,
        group: UserGroup,
    ) -> Optional[TaskPerformer]:
        performers = (
            TaskPerformer.objects.by_task(
                self.task.id,
            ).exclude_directly_deleted()
        )
        if (
            performers.count() == 1
            and performers.filter(group_id=group.id).exists()
        ):
            raise GroupPerformerServiceException(MSG_PW_0016)
        return performers.filter(group_id=group.id).first()

    @abstractmethod
    def create_performer(self, group: UserGroup) -> None:
        pass

    @abstractmethod
    def delete_performer(
        self,
        group: UserGroup,
        request_user: UserModel,
    ) -> None:
        pass
