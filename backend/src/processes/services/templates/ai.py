# ruff: noqa: E501
import json
import re
from abc import abstractmethod
from typing import Optional, Union

import requests as http_requests
from django.conf import settings
from django.contrib.auth import get_user_model

from src.accounts.services.account import AccountService
from src.ai.models import (
    OpenAiPrompt,
)
from src.analysis.services import AnalyticService
from src.authentication.enums import AuthTokenType
from src.processes.consts import TEMPLATE_NAME_LENGTH
from src.processes.enums import (
    ConditionAction,
    FieldType,
    PerformerType,
    PredicateOperator,
    PredicateType,
)
from src.processes.models.templates.task import TaskTemplate
from src.processes.services.exceptions import (
    OpenAiLimitTemplateGenerations,
    OpenAiServiceException,
    OpenAiServiceFailed,
    OpenAiServiceUnavailable,
    OpenAiStepsPromptNotExist,
    OpenAiTemplateStepsNotExist,
)
from src.processes.services.templates.template import (
    TemplateService,
)
from src.processes.utils.common import (
    create_api_name,
    insert_fields_values_to_text,
)
from src.utils.logging import (
    SentryLogLevel,
    capture_sentry_message,
)

UserModel = get_user_model()

# Fallback system prompt used when no active OpenAiPrompt
# with target GET_TEMPLATE is configured in Django Admin.
DEFAULT_TEMPLATE_INSTRUCTION = """You are a workflow template designer.
Your job is to design workflow templates based on user descriptions of their business processes.
Each template consists of a kickoff form and tasks.
You must return ONLY valid JSON (no markdown, no code fences, no explanation) matching this structure:

{
  "name": str,
  "description": str,
  "tasks": [
    {
      "number": int,
      "name": str,
      "description": str,
      "fields": [
        {
          "api_name": str,
          "order": int,
          "name": str,
          "type": str,
          "is_required": bool,
          "description": str,
          "default": str,
          "selections": [
            {
              "value": str
            }
          ]
        }
      ]
    }
  ],
  "kickoff": {
    "fields": [
      {
        "api_name": str,
        "order": int,
        "name": str,
        "type": str,
        "is_required": bool,
        "description": str,
        "default": str,
        "selections": [
          {
            "value": str
          }
        ]
      }
    ]
  }
}

Field types: "string", "text", "radio", "checkbox", "date", "url", "dropdown", "file", "user", "number".
The "selections" array must ONLY be included for "radio", "checkbox", and "dropdown" field types.
For all other field types, omit "selections" entirely.

Every field MUST have an "api_name". Use kebab-case prefixed with "field-", derived from the field name, e.g., "field-project-name", "field-priority-level".
The api_name must be unique across all fields in the template.

Task descriptions can reference values of kickoff fields or previous task output fields using the syntax {{api_name}}.
For example, if a kickoff field has "api_name": "field-project-name", a task description can include {{field-project-name}} to reference its value.
Include such variable references in task descriptions where it is relevant and useful.

Design kickoff fields to capture the information needed to start the workflow.
Design task output fields to capture information produced during each task.
Include fields and kickoff fields where they add value to the process.
Each task should have a clear name and a description explaining what needs to be done.
If the user description implies conditional logic (e.g., "if X then skip Y"), note it in the task descriptions.

Given a user description of a business process, generate a workflow template JSON as per the structure above."""

VALID_FIELD_TYPES = {c[0] for c in FieldType.CHOICES}
SELECTION_FIELD_TYPES = FieldType.TYPES_WITH_SELECTIONS


class BaseAiService:

    def __init__(
        self,
        ident: Union[str, int],
    ):
        self.ident = ident

    OPENAI_RESPONSES_URL = 'https://api.openai.com/v1/responses'

    @abstractmethod
    def _log_exception(
        self,
        user_description: str,
        prompt: OpenAiPrompt,
        ex: Exception,
        level: SentryLogLevel.LITERALS = SentryLogLevel.ERROR,
    ):
        pass

    @abstractmethod
    def _log(
        self,
        user_description: str,
        prompt: OpenAiPrompt,
        message: str,
        level: SentryLogLevel.LITERALS = SentryLogLevel.ERROR,
        response_text: Optional[str] = None,
    ):
        pass

    def _openai_headers(self):
        headers = {
            'Authorization': f'Bearer {settings.OPENAI_API_KEY}',
            'Content-Type': 'application/json',
        }
        if settings.OPENAI_API_ORG:
            headers['OpenAI-Organization'] = settings.OPENAI_API_ORG
        return headers

    def _call_responses_api(self, payload):
        """Call OpenAI Responses API and return the output text."""
        try:
            resp = http_requests.post(
                self.OPENAI_RESPONSES_URL,
                headers=self._openai_headers(),
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
        except http_requests.RequestException as ex:
            raise OpenAiServiceUnavailable(str(ex)) from ex

        data = resp.json()
        # Extract text from the response output
        for item in data.get('output', []):
            if item.get('type') == 'message':
                for content in item.get('content', []):
                    if content.get('type') == 'output_text':
                        return content.get('text', '')
        raise OpenAiServiceFailed

    def _get_response(
        self,
        prompt: OpenAiPrompt,
        user_description: str,
    ) -> str:

        if not settings.OPENAI_API_KEY:
            raise OpenAiServiceUnavailable

        # Build instructions and input from prompt messages
        instructions = None
        user_input = user_description
        for elem in prompt.messages.order_by('order'):
            content = insert_fields_values_to_text(
                text=elem.content,
                fields_values={'user_description': user_description},
            )
            if elem.role == 'system':
                instructions = content
            elif elem.role == 'user':
                user_input = content

        payload = {
            'model': prompt.model,
            'input': user_input,
            'temperature': prompt.temperature,
            'top_p': prompt.top_p,
        }
        if instructions:
            payload['instructions'] = instructions
        if prompt.presence_penalty:
            payload['presence_penalty'] = prompt.presence_penalty
        if prompt.frequency_penalty:
            payload['frequency_penalty'] = (
                prompt.frequency_penalty
            )

        try:
            return self._call_responses_api(payload)
        except (OpenAiServiceUnavailable, OpenAiServiceFailed) as ex:
            self._log_exception(
                ex=ex,
                prompt=prompt,
                user_description=user_description,
            )
            raise

    def _get_json_response(
        self,
        user_description: str,
        prompt: Optional[OpenAiPrompt] = None,
    ) -> str:

        if not settings.OPENAI_API_KEY:
            return self._test_response()

        if prompt and prompt.messages.active().exists():
            instructions = None
            user_input = user_description
            for elem in prompt.messages.order_by('order'):
                content = insert_fields_values_to_text(
                    text=elem.content,
                    fields_values={
                        'user_description': user_description,
                    },
                )
                if elem.role == 'system':
                    instructions = content
                elif elem.role == 'user':
                    user_input = content
        else:
            instructions = DEFAULT_TEMPLATE_INSTRUCTION
            user_input = user_description

        model = prompt.model if prompt else 'gpt-4.1-mini'

        payload = {
            'model': model,
            'input': user_input,
            'temperature': prompt.temperature if prompt else 0.7,
            'top_p': prompt.top_p if prompt else 1,
        }
        if instructions:
            payload['instructions'] = instructions
        if prompt and prompt.presence_penalty:
            payload['presence_penalty'] = (
                prompt.presence_penalty
            )
        if prompt and prompt.frequency_penalty:
            payload['frequency_penalty'] = (
                prompt.frequency_penalty
            )

        try:
            return self._call_responses_api(payload)
        except (OpenAiServiceUnavailable, OpenAiServiceFailed) as ex:
            if prompt:
                self._log_exception(
                    ex=ex,
                    prompt=prompt,
                    user_description=user_description,
                )
            raise

    def _test_response(self):
        return json.dumps({
            'name': 'Honey Harvesting',
            'description': 'Process for harvesting honey from beehives.',
            'kickoff': {
                'fields': [
                    {
                        'api_name': 'field-hive-location',
                        'order': 1,
                        'name': 'Hive Location',
                        'type': 'string',
                        'is_required': True,
                        'description': 'Location of the beehive',
                    },
                    {
                        'api_name': 'field-harvest-type',
                        'order': 2,
                        'name': 'Harvest Type',
                        'type': 'radio',
                        'is_required': True,
                        'description': 'Type of harvest',
                        'selections': [
                            {'value': 'Full harvest'},
                            {'value': 'Partial harvest'},
                        ],
                    },
                ],
            },
            'tasks': [
                {
                    'number': 1,
                    'name': 'Inspect hive',
                    'description': (
                        'Inspect the beehive at {{field-hive-location}}'
                        ' to determine readiness for honey collection.'
                    ),
                    'fields': [
                        {
                            'api_name': 'field-hive-condition',
                            'order': 1,
                            'name': 'Hive Condition',
                            'type': 'dropdown',
                            'is_required': True,
                            'description': 'Current condition of the hive',
                            'selections': [
                                {'value': 'Excellent'},
                                {'value': 'Good'},
                                {'value': 'Needs attention'},
                            ],
                        },
                    ],
                },
                {
                    'number': 2,
                    'name': 'Smoke the bees',
                    'description': (
                        'Use a smoker to calm the bees and '
                        'make them less aggressive.'
                    ),
                },
                {
                    'number': 3,
                    'name': 'Extract honey',
                    'description': (
                        'Extract the honey from the hive frames.'
                    ),
                    'fields': [
                        {
                            'api_name': 'field-quantity-extracted',
                            'order': 1,
                            'name': 'Quantity Extracted',
                            'type': 'number',
                            'is_required': True,
                            'description': 'Amount of honey in kg',
                        },
                    ],
                },
                {
                    'number': 4,
                    'name': 'Bottle and label',
                    'description': (
                        'Bottle the honey and label each jar.'
                    ),
                },
            ],
        })

    def _get_start_task_condition(self, prev_task_api_name: str) -> dict:
        if prev_task_api_name is None:
            predicate = {
                'field_type': PredicateType.KICKOFF,
                'operator': PredicateOperator.COMPLETED,
                'api_name': create_api_name('predicate'),
                'field': None,
                'value': None,
            }
        else:
            predicate = {
                'field_type': PredicateType.TASK,
                'operator': PredicateOperator.COMPLETED,
                'api_name': create_api_name('predicate'),
                'field': prev_task_api_name,
                'value': None,
            }
        return {
            'order': 1,
            'action': ConditionAction.START_TASK,
            'api_name': create_api_name('condition'),
            'rules': [
                {
                    'api_name': create_api_name('rule'),
                    'predicates': [predicate],
                },
            ],
        }

    @abstractmethod
    def _get_step_data_from_text(
        self,
        number: int,
        name: str,
        description: str,
        prev_task_api_name: Optional[str],
    ) -> dict:
        pass

    def _get_steps_data_from_text(self, text: str) -> list:
        steps_data = [
            step.split('|') for step in text.split('\n')
            if step and step.find('|') > 0
        ]
        tasks_data = []
        prev_task_api_name = None
        for number, step in enumerate(steps_data):
            if len(step) != 2:
                continue
            limit = TaskTemplate.NAME_MAX_LENGTH
            name = step[0].strip()[:limit]
            description = step[1].strip()
            task_data = self._get_step_data_from_text(
                number=number + 1,
                name=name,
                description=description,
                prev_task_api_name=prev_task_api_name,
            )
            prev_task_api_name = task_data['api_name']
            tasks_data.append(task_data)
        return tasks_data

    @staticmethod
    def _extract_json(text: str) -> str:
        text = text.strip()
        match = re.search(
            r'```(?:json)?\s*([\s\S]*?)```',
            text,
        )
        if match:
            return match.group(1).strip()
        return text

    @staticmethod
    def _normalize_field(field_data: dict) -> dict:
        field_type = field_data.get('type', FieldType.STRING)
        if field_type not in VALID_FIELD_TYPES:
            field_type = FieldType.STRING
        normalized = {
            'order': field_data.get('order', 1),
            'name': field_data.get('name', '')[:50],
            'type': field_type,
            'is_required': bool(field_data.get('is_required', False)),
            'description': field_data.get('description', ''),
            'default': field_data.get('default', ''),
            'api_name': field_data.get('api_name') or create_api_name('field'),
        }
        if field_type in SELECTION_FIELD_TYPES:
            raw_selections = field_data.get('selections', [])
            selections = []
            for sel in raw_selections:
                value = sel.get('value', '') if isinstance(sel, dict) else ''
                if value:
                    selections.append({
                        'value': value,
                        'api_name': create_api_name('selection'),
                    })
            if selections:
                normalized['selections'] = selections
        return normalized

    def _parse_template_from_json(self, text: str) -> dict:
        json_str = self._extract_json(text)
        data = json.loads(json_str)
        if not isinstance(data, dict):
            raise TypeError(
                f'Expected JSON object,'
                f' got {type(data).__name__}',
            )
        template_name = data.get('name', '')[:TEMPLATE_NAME_LENGTH]
        description = data.get('description', '')

        kickoff_data = data.get('kickoff', {})
        kickoff_fields = []
        for field_data in kickoff_data.get('fields', []):
            kickoff_fields.append(self._normalize_field(field_data))

        tasks_data = []
        prev_task_api_name = None
        raw_tasks = data.get('tasks', [])

        for idx, raw_task in enumerate(raw_tasks):
            limit = TaskTemplate.NAME_MAX_LENGTH
            task_name = raw_task.get('name', '')[:limit]
            task_description = raw_task.get('description', '')
            task_api_name = create_api_name('task')

            task_fields = []
            for field_data in raw_task.get('fields', []):
                task_fields.append(self._normalize_field(field_data))

            condition = self._get_start_task_condition(
                prev_task_api_name,
            )

            task_data = {
                'number': idx + 1,
                'name': task_name,
                'api_name': task_api_name,
                'description': task_description,
                'conditions': [condition],
            }

            if task_fields:
                task_data['fields'] = task_fields

            tasks_data.append(task_data)
            prev_task_api_name = task_api_name

        return {
            'name': template_name,
            'description': description,
            'kickoff': {
                'fields': kickoff_fields,
            },
            'tasks': tasks_data,
        }


class OpenAiService(BaseAiService):

    def __init__(
        self,
        user: UserModel,
        ident: Union[str, int],
        auth_type: AuthTokenType.LITERALS,
        is_superuser: bool = False,
    ):
        self.user = user
        self.account = self.user.account
        self.auth_type = auth_type
        self.is_superuser = is_superuser
        super().__init__(ident=ident)

    def _log_exception(
        self,
        prompt: OpenAiPrompt,
        user_description: str,
        ex: Exception,
        level: SentryLogLevel.LITERALS = SentryLogLevel.INFO,
    ):

        capture_sentry_message(
            message=f'Error AI generating template ({self.account.id})',
            data={
                'user_id': self.user.id,
                'user_email': self.user.email,
                'account_id': self.account.id,
                'ex': {
                    'error': str(ex),
                },
                'request': {
                    'user_description': user_description,
                    'prompt': prompt.as_dict(),
                },
            },
            level=level,
        )

    def _log(
        self,
        prompt: OpenAiPrompt,
        user_description: str,
        message: str,
        level: SentryLogLevel.LITERALS = SentryLogLevel.INFO,
        response_text: Optional[str] = None,
    ):
        capture_sentry_message(
            message=f'Error AI generating template ({self.account.id})',
            data={
                'user_id': self.user.id,
                'user_email': self.user.email,
                'account_id': self.account.id,
                'message': message,
                'response': {
                    'text': response_text,
                },
                'request': {
                    'user_description': user_description,
                    'prompt': prompt.as_dict(),
                },
            },
            level=level,
        )

    def _get_step_data_from_text(
        self,
        number: int,
        name: str,
        description: str,
        prev_task_api_name: Optional[str],
    ) -> dict:
        return {
            'number': number,
            'name': name,
            'api_name': create_api_name(prefix='task'),
            'description': description,
            'raw_performers': [
                {
                    'type': PerformerType.USER,
                    'source_id': self.user.id,
                    'label': self.user.name,
                },
            ],
            'conditions': [
                self._get_start_task_condition(prev_task_api_name),
            ],
        }

    def _post_template_generation_actions(self, user_description: str):
        account_service = AccountService(
            user=self.user,
            instance=self.account,
        )
        account_service.inc_template_generations_count()

    def _get_template_data(self, user_description: str) -> dict:

        """ Generate template data dict from user description """

        if self.account.ai_template_generations_limit_exceeded:
            raise OpenAiLimitTemplateGenerations

        template_prompt = (
            OpenAiPrompt.objects.active().target_template().first()
        )
        steps_prompt = (
            OpenAiPrompt.objects.active().target_steps().first()
        )

        if template_prompt or not (
            steps_prompt
            and steps_prompt.messages.active().exists()
        ):
            response_text = self._get_json_response(
                user_description=user_description,
                prompt=template_prompt,
            )
            try:
                initial_data = self._parse_template_from_json(
                    response_text,
                )
            except (json.JSONDecodeError, KeyError, TypeError) as ex:
                if template_prompt:
                    self._log(
                        prompt=template_prompt,
                        user_description=user_description,
                        message='Failed to parse JSON template response',
                        response_text=response_text,
                    )
                raise OpenAiTemplateStepsNotExist from ex
            if not initial_data.get('tasks'):
                if template_prompt:
                    self._log(
                        prompt=template_prompt,
                        user_description=user_description,
                        message='Template tasks not found',
                        response_text=response_text,
                    )
                raise OpenAiTemplateStepsNotExist
        else:
            if not steps_prompt or not (
                steps_prompt.messages.active().exists()
            ):
                raise OpenAiStepsPromptNotExist
            response_text = self._get_response(
                prompt=steps_prompt,
                user_description=user_description,
            )
            initial_tasks_data = self._get_steps_data_from_text(
                response_text,
            )
            if not initial_tasks_data:
                self._log(
                    prompt=steps_prompt,
                    user_description=user_description,
                    message='Template steps not found',
                    response_text=response_text,
                )
                raise OpenAiTemplateStepsNotExist
            initial_data = {
                'name': user_description[:TEMPLATE_NAME_LENGTH],
                'tasks': initial_tasks_data,
            }

        if not initial_data.get('name'):
            initial_data['name'] = user_description[:TEMPLATE_NAME_LENGTH]

        template_service = TemplateService(
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
        )

        data = template_service.fill_template_data(initial_data)
        self._post_template_generation_actions(user_description)
        return data

    def get_template_data(self, user_description: str) -> dict:
        success = True
        try:
            template_data = self._get_template_data(user_description)
        except OpenAiServiceException:
            success = False
            raise
        else:
            return template_data
        finally:
            AnalyticService.template_generation_init(
                user=self.user,
                auth_type=self.auth_type,
                is_superuser=self.is_superuser,
                description=user_description,
                success=success,
            )


class AnonOpenAiService(BaseAiService):

    """ Represents methods for generating template for anonymous user """

    def __init__(
        self,
        ident: Union[str, int],
        user_agent: str,
    ):
        self.ident = ident
        self.user_agent = user_agent
        super().__init__(ident=ident)

    def _log_exception(
        self,
        prompt: OpenAiPrompt,
        user_description: str,
        ex: Exception,
        level: SentryLogLevel.LITERALS = SentryLogLevel.INFO,
    ):

        capture_sentry_message(
            message=f'Error AI gen template from landing ({self.ident})',
            data={
                'ident': self.ident,
                'user-agent': self.user_agent,
                'ex': {
                    'error': str(ex),
                },
                'request': {
                    'user_description': user_description,
                    'prompt': prompt.as_dict(),
                },
            },
            level=level,
        )

    def _log(
        self,
        prompt: OpenAiPrompt,
        user_description: str,
        message: str,
        level: SentryLogLevel.LITERALS = SentryLogLevel.INFO,
        response_text: Optional[str] = None,
    ):
        capture_sentry_message(
            message=f'Error AI gen template from landing ({self.ident})',
            data={
                'ident': self.ident,
                'user-agent': self.user_agent,
                'message': message,
                'response': {
                    'text': response_text,
                },
                'request': {
                    'user_description': user_description,
                    'prompt': prompt.as_dict(),
                },
            },
            level=level,
        )

    def _get_step_data_from_text(
        self,
        number: int,
        name: str,
        description: str,
        prev_task_api_name: Optional[str],
    ) -> dict:
        return {
            'number': number,
            'name': name,
            'api_name': create_api_name(prefix='task'),
            'description': description,
            'conditions': [
                self._get_start_task_condition(prev_task_api_name),
            ],
        }

    def get_short_template_data(
        self,
        user_description: str,
    ):

        """ Generate minimal template data dict from description """

        template_prompt = (
            OpenAiPrompt.objects.active().target_template().first()
        )
        steps_prompt = (
            OpenAiPrompt.objects.active().target_steps().first()
        )

        if template_prompt or not (
            steps_prompt
            and steps_prompt.messages.active().exists()
        ):
            response_text = self._get_json_response(
                user_description=user_description,
                prompt=template_prompt,
            )
            try:
                parsed = self._parse_template_from_json(response_text)
            except (json.JSONDecodeError, KeyError, TypeError) as ex:
                if template_prompt:
                    self._log(
                        prompt=template_prompt,
                        user_description=user_description,
                        message='Failed to parse JSON template response',
                        response_text=response_text,
                    )
                raise OpenAiTemplateStepsNotExist from ex
            if not parsed.get('tasks'):
                if template_prompt:
                    self._log(
                        prompt=template_prompt,
                        user_description=user_description,
                        message='Template tasks not found',
                        response_text=response_text,
                    )
                raise OpenAiTemplateStepsNotExist
            tasks = []
            for task in parsed['tasks']:
                tasks.append({
                    'number': task['number'],
                    'name': task['name'],
                    'api_name': task['api_name'],
                    'description': task.get('description', ''),
                    'conditions': task.get('conditions', []),
                })
            return {
                'name': (
                    parsed.get('name')
                    or user_description[:TEMPLATE_NAME_LENGTH]
                ),
                'tasks': tasks,
            }

        if not steps_prompt or not (
            steps_prompt.messages.active().exists()
        ):
            raise OpenAiStepsPromptNotExist
        response_text = self._get_response(
            prompt=steps_prompt,
            user_description=user_description,
        )
        initial_tasks_data = self._get_steps_data_from_text(
            response_text,
        )
        if not initial_tasks_data:
            self._log(
                prompt=steps_prompt,
                user_description=user_description,
                message='Template steps not found',
                response_text=response_text,
            )
            raise OpenAiTemplateStepsNotExist
        return {
            'name': user_description[:TEMPLATE_NAME_LENGTH],
            'tasks': initial_tasks_data,
        }
