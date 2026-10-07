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
    AIAgentAttemptsExceededException,
    AIAgentNameNotUniqueException,
)
from src.ai.messages import MSG_AI_0009, MSG_AI_0010
from src.ai.models import AIAgent, AIAgentAction
from src.ai.services.provider import AIProviderService
from src.ai.services.response import TaskResponseService
from src.ai.services.user_message import TaskUserMessageService
from src.generics.base.service import BaseModelService
from src.generics.exceptions import BaseServiceException
from src.ai.enums import AIAgentActionType
from src.processes.models.workflows.task import Task
from src.processes.serializers.workflows.task import TaskCompleteSerializer
from src.processes.services.events import CommentService
from src.processes.services.exceptions import WorkflowActionServiceException, \
    FieldsetServiceException
from src.processes.services.workflow_action import WorkflowActionService
from src.storage.enums import AccessType, SourceType
from src.storage.services import FileServiceClient

UserModel = get_user_model()


class AIAgentService(BaseModelService):

    def _get_agent_email(self) -> str:

        """ Unique email for the user the agent runs on,
            in the domain of the account owner.

            the owner email 'owner@pizza.com'
            -> 'ai-agent-Hq3kZr9TbVn2Lm7sXy1p@pizza.com' """

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

        """ Creates the agent along with the user it acts on behalf of.
            The user is an admin with all the subscriptions disabled.

            name 'Operator', model 'gpt-4o', provider_id 3
            -> AIAgent 'Operator' with a user 'Operator' (is_ai=True)

            the account already has an agent 'Operator'
            -> AIAgentNameNotUniqueException """

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

        """ Updates the agent and keeps the name and the photo
            of its user in sync.

            name 'Courier'
            -> AIAgent 'Courier', its user gets first_name 'Courier' """

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

        """ Deletes the agent together with the user it runs on.

            an agent 'Operator' -> the agent and its user are deleted """

        with transaction.atomic():
            self.instance.user.delete()
            self.instance.delete()

    def _get_fields_values(
        self,
        task: Task,
        errors_stack: Optional[List[Tuple[dict, str]]] = None,
    ) -> Dict[str, Union[str, List[str]]]:

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
        return response_parser.get_fields_values()

    def _complete_task(self, task: Task, fields_values: dict):

        """ Completes the task with the values the agent returned
            and snoozes the workflow if the next task is delayed.

            fields_values {'phone-1': '+1 202 555 0147'}
            -> the task is completed on behalf of the agent user

            a value the task fields do not accept
            -> ValidationError or WorkflowActionServiceException """

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

    def _create_report_file(
        self,
        text: str,
        filename: str,
    ) -> str:

        """ Uploads the text to the file service as a file
            available to the account only.

            text '# Report', filename 'report.md'
            -> 'https://storage.pneumatic.app/report.md' """

        client = FileServiceClient(user=self.user)
        return client.upload_file_with_attachment(
            file_content=text.encode('utf-8'),
            filename=filename,
            content_type='text/plain',
            account=self.account,
            source_type=SourceType.TASK,
            access_type=AccessType.RESTRICTED,
        )

    def _create_comment(self, task: Task, text: str):

        """ Writes a comment to the task on behalf of the agent user.

            text 'The order is unclear.'
            -> a comment event on the task, its performers are notified """

        service = CommentService(
            user=self.user,
            auth_type=self.auth_type,
            is_superuser=self.is_superuser,
        )
        service.create(
            task=task,
            text=text,
        )

    def _get_report_text(
        self,
        errors_stack: List[Tuple[dict, str]],
    ) -> str:

        """ Markdown report on the attempts to complete the task,
            the values the agent answered with and the error each
            of them failed with.

            a single attempt with the values {'phone-1': 'call me'}
            and the error '- `phone-1`: Value should be a string.'
            ->
            # Complete task attempts

            ## Attempt № 1

            ### Output fields

            - `phone-1`: call me

            ### Validation error

            - `phone-1`: Value should be a string. """

        parts = []
        for number, (fields_values, error) in enumerate(errors_stack, 1):
            fields = '\n'.join(
                f'- `{api_name}`: '
                + (
                    ', '.join(str(item) for item in value)
                    if isinstance(value, (list, tuple)) else str(value)
                )
                for api_name, value in fields_values.items()
            )
            parts.append(
                f'## Attempt № {number}\n\n'
                f'### Output fields\n\n{fields}\n\n'
                f'### Validation error\n\n{error}',
            )
        return '# Complete task attempts\n\n' + '\n\n-------\n\n'.join(parts)

    def _raise_attempt_error(
        self,
        task: Task,
        errors_stack: List[Tuple[dict, str]],
    ):

        """ Reports the failed attempts to complete the task
            and interrupts the agent run.

            errors_stack with the values {'phone-1': 'call me'} and
            the error '- `phone-1`: Value should be a string.'
            -> a report file, a comment with a link to it,
               the action 'error' and
               AIAgentAttemptsExceededException """

        text = self._get_report_text(errors_stack=errors_stack)
        filename = 'report.md'
        url = self._create_report_file(text=text, filename=filename)
        attempts = len(errors_stack)
        self._create_comment(
            task=task,
            text=str(
                MSG_AI_0009(
                    attempts=attempts,
                    report=f'[{filename}]({url})',
                ),
            ),
        )
        message = MSG_AI_0010(attempts=attempts)
        AIAgentAction.objects.create(
            account_id=self.instance.account_id,
            agent_id=self.instance.id,
            task_id=task.id,
            action=AIAgentActionType.ERROR,
            text=f'{message}\n{url}',
        )
        raise AIAgentAttemptsExceededException(message=message)

    def _convert_ex_to_markdown(
        self,
        ex: Union[BaseServiceException, ValidationError],
    ) -> str:

        """ Represent a task completion error as a markdown list:
            "- `field`: message" for field errors and
            "- message" for common errors

            Service exception:
              ex = CompleteDelayedWorkflow()
              result = '- Resume the workflow to complete the task.'

            Validation error for a nested field (api_name):
              ex.detail = {
                'code': 'validation_error',
                'message': 'Value should be a string.',
                'details': {
                  'reason': 'Value should be a string.',
                  'api_name': 'phone-1'
                }
              }
              result = '- `phone-1`: Value should be a string.'

            Validation error for a form field (name):
              ex.detail = {
                'code': 'validation_error',
                'message': 'Expected a dictionary of items.',
                'details': {
                  'reason': 'Expected a dictionary of items.',
                  'name': 'output'
                }
              }
              result = '- `output`: Expected a dictionary of items.'

            Common validation error:
              ex.detail = {
                'code': 'validation_error',
                'message': 'Invalid output.',
                'details': {}
              }
              result = '- Invalid output.'

            Framework fields map:
              ex.detail = {
                'phone-1': ['Value should be a string.'],
                'total-1': ['The value must be a number.']
              }
              result = (
                '- `phone-1`: Value should be a string.\\n'
                '- `total-1`: The value must be a number.'
              ) """

        if not isinstance(ex, ValidationError):
            return f'- {ex}'

        errors: List[Tuple[Optional[str], str]] = []
        detail = ex.detail
        if isinstance(detail, dict):
            message = detail.get('message')
            if isinstance(message, str):
                details = detail.get('details') or {}
                name = details.get('name') or details.get('api_name')
                errors.append((name, message))
            else:
                for name, value in detail.items():
                    values = (
                        value if isinstance(value, (list, tuple))
                        else [value]
                    )
                    for item in values:
                        errors.append((name, str(item)))
        elif isinstance(detail, (list, tuple)):
            errors.extend((None, str(item)) for item in detail)
        if not errors:
            errors.append((None, 'Validation failed.'))
        return '\n'.join(
            f'- `{name}`: {message}' if name else f'- {message}'
            for name, message in errors
        )

    def _attempt_complete_task(
        self,
        task: Task,
        errors_stack: Optional[List[Tuple[dict, str]]] = None,
        attempt: int = 1,
    ) -> Optional[dict]:

        fields_values = self._get_fields_values(
            task=task,
            errors_stack=errors_stack,
        )
        try:
            self._complete_task(task=task, fields_values=fields_values)
        except (
            WorkflowActionServiceException,
            FieldsetServiceException,
            ValidationError,
        ) as ex:
            error = self._convert_ex_to_markdown(ex)
            errors_stack = errors_stack or []
            errors_stack.append((fields_values, error))
            new_attempt = attempt + 1
            if new_attempt > 10:
                self._raise_attempt_error(
                    task=task,
                    errors_stack=errors_stack,
                )
            fields_values = self._attempt_complete_task(
                task=task,
                errors_stack=errors_stack,
                attempt=new_attempt,
            )

        return fields_values

    def complete_task(self, task_id: int):

        """ Fills in the task output with an agent answer, completes
            the task and logs the agent actions.

            task_id 42
            -> the task is completed, the actions 'task_in_progress' and
               'task_completed' with the text '{"phone-1": "+1 202..."}'
               are created """

        task = Task.objects.filter(id=task_id).first()
        AIAgentAction.objects.create(
            account_id=self.instance.account_id,
            agent_id=self.instance.id,
            task_id=task.id,
            action=AIAgentActionType.TASK_IN_PROGRESS,
        )
        fields_values = self._attempt_complete_task(task=task)
        AIAgentAction.objects.create(
            account_id=self.instance.account_id,
            agent_id=self.instance.id,
            task_id=task.id,
            action=AIAgentActionType.TASK_COMPLETED,
            text=json.dumps(fields_values, ensure_ascii=False),
        )

    def reply_to_comment(self, notification_id: int):

        """ Replies to the comment the agent was mentioned in.
            The reply itself is not implemented yet.

            notification_id 7
            -> the notification is read, the action
               'mention_in_progress' is created """

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
