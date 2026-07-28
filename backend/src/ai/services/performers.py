import logging
from typing import (
    List,
    Optional,
)

import requests
from django.conf import settings
from django.utils import timezone

from src.ai.clients.chat_completions import (
    RETRYABLE_STATUSES,
    AIClientError,
    AIRequestError,
    ChatCompletionsClient,
)
from src.ai.enums import AITaskRunStatus
from src.ai.models import (
    AIAgent,
    AITaskRun,
)
from src.ai.performers.attachments import (
    extract_content,
    render_attachment,
)
from src.ai.performers.output_fields import (
    OutputField,
    find_blocking_fields,
    is_fillable,
    resolve_output_fields,
)
from src.ai.performers.output_schema import (
    build_output_schema,
    describe_fields,
)
from src.ai.performers.output_translation import (
    IncompleteOutputError,
    to_pneumatic_output,
)
from django.contrib.auth import get_user_model

from src.authentication.enums import AuthTokenType
from src.notifications.tasks import send_ai_left_task_notification
from src.processes.enums import (
    PerformerType,
    TaskStatus,
)
from src.processes.models.workflows.task import (
    Task,
    TaskPerformer,
)
from src.processes.services import exceptions
from src.processes.services.events import WorkflowEventService
from src.processes.services.workflow_action import WorkflowActionService
from src.storage.services.exceptions import (
    FileDownloadException,
    FileServiceConnectionFailedException,
)
from src.storage.services.file_service import FileServiceClient
from src.storage.utils import extract_file_links_from_text

UserModel = get_user_model()

logger = logging.getLogger(__name__)


class AITransientError(Exception):

    """ Provider/network failure worth a Celery retry """


class AttachmentDownloadError(Exception):

    """ An input document exists but could not be downloaded —
        completing the task while silently missing an input is worse
        than leaving it for a human """

    def __init__(self, name: str, status_code):
        super().__init__(f'"{name}" (HTTP {status_code})')
        self.name = name


SYSTEM_SCAFFOLD = (
    'You complete tasks in a business workflow. Read the task below '
    'and produce values for its output fields. Respond with a single '
    'JSON object keyed by field api_name. Use null for optional fields '
    'the task content gives you nothing to fill with. Never invent '
    'facts that are not supported by the task content.'
)


class AIPerformerService:

    """ Executes one AI performer run for a task: claim, gather
        context, call the model, validate, complete the task.

        The failure contract ("never complete a task with a hole in
        it"): the agent completes the task properly, or the run is
        marked left_for_human/failed and the task stays active. """

    def __init__(self, task: Task, agent: AIAgent):
        self.task = task
        self.agent = agent
        self.account = agent.account
        self.last_usage: Optional[dict] = None

    @classmethod
    def load(
        cls,
        task_id: int,
        agent_id: int,
    ) -> Optional['AIPerformerService']:

        """ Returns None (drop silently) when the run is no longer
            relevant: task/agent gone or inactive, agent unassigned,
            or the feature is disabled """

        if not settings.PROJECT_CONF['AI_PERFORMERS']:
            return None
        try:
            task = (
                Task.objects
                .select_related('workflow', 'account')
                .get(id=task_id)
            )
            agent = (
                AIAgent.objects
                .select_related('account')
                .active()
                .get(id=agent_id)
            )
        except (Task.DoesNotExist, AIAgent.DoesNotExist):
            return None
        if not agent.account.ai_performers_enabled:
            return None
        if task.status != TaskStatus.ACTIVE:
            return None
        if task.account_id != agent.account_id:
            return None
        assigned = (
            TaskPerformer.objects
            .by_task(task.id)
            .exclude_directly_deleted()
            .not_completed()
            .filter(type=PerformerType.AI, ai_agent_id=agent.id)
            .exists()
        )
        if not assigned:
            return None
        return cls(task=task, agent=agent)

    def claim(self) -> Optional[AITaskRun]:

        """ get_or_create on (task, agent) plus an atomic
            QUEUED -> RUNNING transition: exactly one worker wins """

        run, _ = AITaskRun.objects.get_or_create(
            task=self.task,
            agent=self.agent,
        )
        claimed = (
            AITaskRun.objects
            .filter(id=run.id, status=AITaskRunStatus.QUEUED)
            .update(status=AITaskRunStatus.RUNNING)
        )
        if not claimed:
            return None
        run.refresh_from_db()
        return run

    def run(self, run: AITaskRun):
        fields = self._resolve_fields()
        blocking = find_blocking_fields(fields)
        if blocking:
            names = ', '.join(f'"{field.name}"' for field in blocking)
            self._leave_for_human(
                run,
                reason=(
                    f'Required fields an AI agent cannot fill: {names}'
                ),
            )
            return

        fillable = [field for field in fields if is_fillable(field)]
        if not fillable:
            # Nothing to produce: complete the task so the workflow
            # moves on
            self._complete_task({})
            self._finish(run, status=AITaskRunStatus.COMPLETED)
            return

        try:
            attachments = self._load_attachments()
        except FileServiceConnectionFailedException as ex:
            self._requeue(run)
            raise AITransientError(str(ex)) from ex
        except AttachmentDownloadError as ex:
            self._leave_for_human(
                run,
                reason=f'Input document could not be downloaded: {ex}',
            )
            return

        try:
            data = self._call_model(fillable, attachments)
        except (requests.Timeout, requests.ConnectionError) as ex:
            self._requeue(run)
            raise AITransientError(str(ex)) from ex
        except AIRequestError as ex:
            if ex.status in RETRYABLE_STATUSES:
                self._requeue(run)
                raise AITransientError(str(ex)) from ex
            self._finish(
                run,
                status=AITaskRunStatus.FAILED,
                reason=str(ex),
            )
            return
        except AIClientError as ex:
            # Truncated/empty/unparseable output: re-running buys the
            # same verdict — don't burn tokens
            self._leave_for_human(run, reason=str(ex))
            return

        try:
            fields_values = to_pneumatic_output(
                fields=fillable,
                data=data,
            )
        except IncompleteOutputError as ex:
            self._leave_for_human(
                run,
                reason='; '.join(ex.problems),
            )
            return

        try:
            self._complete_task(fields_values)
        except exceptions.WorkflowActionServiceException as ex:
            self._leave_for_human(run, reason=str(ex))
            return
        self._finish(run, status=AITaskRunStatus.COMPLETED)

    def mark_failed(self, run: AITaskRun, reason: str):
        self._finish(
            run,
            status=AITaskRunStatus.FAILED,
            reason=reason,
        )

    def _resolve_fields(self) -> List[OutputField]:
        rows = self.task.output.all().prefetch_related('selections')
        raw = [
            {
                'api_name': field.api_name,
                'name': field.name,
                'description': field.description or '',
                'type': field.type,
                'is_required': field.is_required,
                'is_hidden': field.is_hidden,
                'selections': [
                    selection.value
                    for selection in field.selections.all()
                ],
            }
            for field in rows
        ]
        return resolve_output_fields(raw)

    def _system_prompt(self) -> str:
        if self.agent.system_prompt:
            return f'{SYSTEM_SCAFFOLD}\n\n{self.agent.system_prompt}'
        return SYSTEM_SCAFFOLD

    def _load_attachments(self) -> List[dict]:

        """ Downloads and extracts the input documents referenced in
            the task description as file service markdown links.
            Links to other domains never reach the file service
            client — descriptions can contain arbitrary URLs and
            credentials must not follow them """

        if not settings.FILE_SERVICE_URL:
            return []
        links = extract_file_links_from_text(self.task.description or '')
        if not links:
            return []
        client = FileServiceClient(user=self.account.get_owner())
        attachments = []
        for name, file_id in links:
            try:
                data, content_type = client.download_file(file_id)
            except FileDownloadException as ex:
                raise AttachmentDownloadError(
                    name=name,
                    status_code=ex.status_code,
                ) from ex
            attachments.append({
                'name': name,
                **extract_content(
                    name=name,
                    content_type=content_type,
                    data=data,
                ),
            })
        return attachments

    def _user_content(
        self,
        fields: List[OutputField],
        attachments: List[dict],
    ):
        parts = [f'# Task: {self.task.name}']
        if self.task.description:
            parts.append(self.task.description)
        for attachment in attachments:
            parts.append(render_attachment(attachment))
        parts.append(f'## Output fields\n{describe_fields(fields)}')
        parts.append(
            'Respond with a single JSON object keyed by field api_name.',
        )
        text = '\n\n'.join(parts)
        images = [
            attachment for attachment in attachments
            if attachment['kind'] == 'image'
        ]
        if not images:
            # Text-only prompts stay plain strings so models without
            # multimodal input keep working
            return text
        return [
            {'type': 'text', 'text': text},
            *(
                {
                    'type': 'image_url',
                    'image_url': {'url': image['data_url']},
                }
                for image in images
            ),
        ]

    def _call_model(
        self,
        fields: List[OutputField],
        attachments: List[dict],
    ) -> dict:
        client = ChatCompletionsClient(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY,
        )
        try:
            return client.call_model(
                model=self.agent.model_slug,
                user_content=self._user_content(fields, attachments),
                system_prompt=self._system_prompt(),
                temperature=self.agent.temperature,
                max_tokens=self.agent.max_tokens,
                schema=build_output_schema(fields),
            )
        finally:
            # tokens are consumed even when the output is unusable
            self.last_usage = client.last_usage

    def _complete_task(self, fields_values: dict):
        owner = self.account.get_owner()
        service = WorkflowActionService(
            user=owner,
            workflow=self.task.workflow,
            auth_type=AuthTokenType.API,
        )
        service.complete_task_for_ai_agent(
            task=self.task,
            ai_agent=self.agent,
            fields_values=fields_values,
        )

    def _requeue(self, run: AITaskRun):
        AITaskRun.objects.filter(id=run.id).update(
            status=AITaskRunStatus.QUEUED,
            attempts=run.attempts + 1,
        )

    def _leave_for_human(self, run: AITaskRun, reason: str):
        logger.warning(
            'AI run %s left for human: %s', run.id, reason,
        )
        self._finish(
            run,
            status=AITaskRunStatus.LEFT_FOR_HUMAN,
            reason=reason,
        )
        WorkflowEventService.ai_agent_left_event(
            task=self.task,
            ai_agent=self.agent,
            reason=reason,
        )
        recipients = self._left_for_human_recipients()
        if recipients:
            send_ai_left_task_notification.delay(
                logging=self.account.log_api_requests,
                logo_lg=self.account.logo_lg,
                account_id=self.account.id,
                recipients=recipients,
                task_id=self.task.id,
                agent_name=self.agent.name,
                reason=reason,
            )

    def _left_for_human_recipients(self) -> List[tuple]:

        """ Human co-performers of the task; the workflow starter or
            the account owner when the task has none """

        performers_ids = (
            TaskPerformer.objects
            .by_task(self.task.id)
            .exclude_directly_deleted()
            .not_completed()
            .users()
            .values_list('id', flat=True)
        )
        recipients = (
            UserModel.objects
            .get_users_in_performer(performers_ids=performers_ids)
            .order_by('id')
            .user_ids_emails_list()
        )
        if recipients:
            return recipients
        fallback = (
            self.task.workflow.workflow_starter
            or self.account.get_owner()
        )
        if fallback is None:
            return []
        return [(fallback.id, fallback.email)]

    def _finish(
        self,
        run: AITaskRun,
        status: str,
        reason: Optional[str] = None,
    ):
        usage = self.last_usage or {}
        AITaskRun.objects.filter(id=run.id).update(
            status=status,
            reason=reason,
            model_used=usage.get('model') or self.agent.model_slug,
            prompt_tokens=usage.get('prompt_tokens'),
            completion_tokens=usage.get('completion_tokens'),
            attempts=run.attempts + 1,
            date_completed=timezone.now(),
        )
