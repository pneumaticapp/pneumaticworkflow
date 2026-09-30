import json
import string
from typing import Dict, List, Optional, Union, Tuple
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils.crypto import get_random_string
from rest_framework.exceptions import ValidationError

from src.accounts.enums import NotificationStatus
from src.accounts.models import Notification
from src.accounts.services.user import UserService
from src.ai.exceptions import (
    AIAgentNameNotUniqueException,
)
from src.ai.models import AIAgent, AIAgentAction
from src.ai.services.provider import AIProviderService
from src.ai.services.response import TaskResponseService
from src.ai.services.user_message import TaskUserMessageService
from src.generics.base.service import BaseModelService
from src.ai.enums import AIAgentActionType
from src.processes.models.workflows.task import Task
from src.processes.serializers.workflows.task import TaskCompleteSerializer
from src.processes.services.exceptions import WorkflowActionServiceException, \
    FieldsetServiceException
from src.processes.services.workflow_action import WorkflowActionService

UserModel = get_user_model()


class AIAgentService(BaseModelService):

    def _get_agent_email(self) -> str:
        domain = self.account.get_owner().email.split('@')[1]
        salt = get_random_string(
            length=20,
            allowed_chars=string.ascii_letters + string.digits,
        )
        email = f'ai-agent-{salt}@{domain}'
        if UserModel.include_inactive.filter(email=email).exists():
            return self._get_agent_email()
        return email

    def _create_instance(
        self,
        name: str,
        model: str,
        system_prompt: str,
        is_active: bool = True,
        photo: Optional[str] = None,
        provider_id: Optional[int] = None,
        **kwargs,
    ):
        user_service = UserService(
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
        )
        with transaction.atomic():
            agent_user = user_service.create(
                account=self.account,
                email=self._get_agent_email(),
                first_name=name,
                photo=photo,
                is_admin=True,
                is_ai=True,
                is_tasks_digest_subscriber=False,
                is_digest_subscriber=False,
                is_newsletters_subscriber=False,
                is_special_offers_subscriber=False,
                is_new_tasks_subscriber=False,
                is_complete_tasks_subscriber=False,
                is_comments_mentions_subscriber=False,
            )
            try:
                self.instance = AIAgent.objects.create(
                    account=self.account,
                    name=name,
                    model=model,
                    is_active=is_active,
                    system_prompt=system_prompt,
                    photo=photo,
                    provider_id=provider_id,
                    user=agent_user,
                )
            except IntegrityError as ex:
                raise AIAgentNameNotUniqueException from ex
        return self.instance

    def partial_update(
        self,
        force_save=True,
        **update_kwargs,
    ) -> AIAgent:
        user_update = {}
        if 'name' in update_kwargs:
            user_update['first_name'] = update_kwargs['name']
        if 'photo' in update_kwargs:
            user_update['photo'] = update_kwargs['photo']
        with transaction.atomic():
            if user_update:
                UserService(
                    user=self.user,
                    instance=self.instance.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                ).partial_update(**user_update)
            try:
                result = super().partial_update(
                    force_save=force_save,
                    **update_kwargs,
                )
            except IntegrityError as ex:
                raise AIAgentNameNotUniqueException from ex
        return result

    def delete(self) -> None:
        with transaction.atomic():
            self.instance.user.delete()
            self.instance.delete()

    def _get_fields_values(
        self,
        task: Task,
    ) -> Tuple[Dict[str, Union[str, List[str]]], str]:

        message_service = TaskUserMessageService(task=task)
        user_message = message_service.get_user_message()
        system_message = message_service.get_system_message(
            system_prompt=self.instance.system_prompt,
        )
        AIAgentAction.objects.create(
            account_id=self.instance.account_id,
            agent_id=self.instance.id,
            task_id=task.id,
            action=AIAgentActionType.AI_REQUEST,
            text=user_message,
        )
        provider_service = AIProviderService(
            user=self.user,
            instance=self.instance.provider,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
        )
        raw_response = provider_service.get_completion(
            system_message=system_message,
            user_message=user_message,
            model=self.instance.model,
            agent=self.instance,
            task=task,
        )
        AIAgentAction.objects.create(
            account_id=self.instance.account_id,
            agent_id=self.instance.id,
            task_id=task.id,
            action=AIAgentActionType.AI_RESPONSE,
            text=raw_response,
        )
        response_parser = TaskResponseService(
            task=task,
            text=raw_response,
            user=self.user,
        )
        fields_values = response_parser.get_fields_values()
        return fields_values, raw_response

    def _complete_task(self, task: Task, fields_values: dict):
        serializer = TaskCompleteSerializer(data=fields_values)
        serializer.is_valid(raise_exception=True)
        service = WorkflowActionService(
            workflow=task.workflow,
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
        )
        service.complete_task_for_user(
            task=task,
            fields_values=fields_values,
        )
        service.check_delay_workflow()

    def _attempt_complete_task(
        self,
        task: Task,
        errors_stack = None,
        attempt: int = 1,
    ):
        fields_values, raw_response = self._get_fields_values(task)
        try:
            self._complete_task(task=task, fields_values=fields_values)
        except (
            WorkflowActionServiceException,
            FieldsetServiceException,
            ValidationError,
        ) as ex:
            # Создать AIAgentAction - ошибка валидации при попытке завершить задачу, вписать attempt, fields_values и ex в событие
            new_attempt = attempt + 1
            if new_attempt > 10:
                # Создать AIAgentAction - превышен лимит попыток
                # Создать комментарий СommentService.create(...) - превышен лимит попыток (создать отдельный метод, т.к он понадобится далее)
            self._attempt_complete_task(
                task=task,
                errors_stack=errors_stack,
                attempt=new_attempt,
            )

    def complete_task(self, task_id: int):
        task = Task.objects.filter(id=task_id).first()
        AIAgentAction.objects.create(
            account_id=self.instance.account_id,
            agent_id=self.instance.id,
            task_id=task.id,
            action=AIAgentActionType.TASK_IN_PROGRESS,
        )
        self._attempt_complete_task(task=task)
        AIAgentAction.objects.create(
            account_id=self.instance.account_id,
            agent_id=self.instance.id,
            task_id=task.id,
            action=AIAgentActionType.TASK_COMPLETED,
            text=json.dumps(fields_values, ensure_ascii=False),
        )

    def reply_to_comment(self, notification_id: int):

        notification = Notification.objects.filter(id=notification_id).first()
        if notification:
            notification.status = NotificationStatus.READ
            notification.save(update_fields=['status'])
            AIAgentAction.objects.create(
                account_id=notification.account_id,
                agent_id=self.instance.id,
                task=notification.task,
                action=AIAgentActionType.MENTION_IN_PROGRESS,
                notification_id=notification_id,
            )
