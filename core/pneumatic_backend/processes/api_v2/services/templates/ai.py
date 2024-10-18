import openai
from abc import abstractmethod
from typing import Optional, Union
from django.conf import settings
from django.contrib.auth import get_user_model
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.enums import PerformerType
from pneumatic_backend.processes.api_v2.services.exceptions import (
    OpenAiServiceUnavailable,
    OpenAiServiceFailed,
    OpenAiLimitTemplateGenerations,
    OpenAiTemplateStepsNotExist,
    OpenAiStepsPromptNotExist,
    OpenAiServiceException,
)
from pneumatic_backend.utils.logging import (
    SentryLogLevel,
    capture_sentry_message,
)
from pneumatic_backend.processes.models.templates.task import (
    TaskTemplate,
)
from pneumatic_backend.accounts.services.account import AccountService
from pneumatic_backend.analytics.services import AnalyticService
from pneumatic_backend.processes.api_v2.services.templates.template import (
    TemplateService
)
from pneumatic_backend.ai.models import (
    OpenAiPrompt
)
from pneumatic_backend.processes.utils.common import (
    insert_fields_values_to_text
)
from pneumatic_backend.processes.consts import TEMPLATE_NAME_LENGTH

UserModel = get_user_model()


class BaseAiService:

    def __init__(
        self,
        ident: Union[str, int],
    ):
        self.ident = ident

    @abstractmethod
    def _log_exception(
        self,
        user_description: str,
        prompt: OpenAiPrompt,
        ex: openai.error.OpenAIError,
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

    def _get_response(
        self,
        prompt: OpenAiPrompt,
        user_description: str
    ) -> str:

        if settings.CONFIGURATION_CURRENT not in (
            settings.CONFIGURATION_PROD,
            settings.CONFIGURATION_STAGING
        ):
            return self._test_response()
        openai.api_key = settings.OPENAI_API_KEY
        openai.organization = settings.OPENAI_API_ORG
        messages = []
        for elem in prompt.messages.order_by('order'):
            messages.append(
                {
                    "role": elem.role,
                    "content": insert_fields_values_to_text(
                        text=elem.content,
                        fields_values={'user_description': user_description}
                    )
                }
            )
        try:
            completion = openai.ChatCompletion.create(
                user=f'u{self.ident}',
                model=prompt.model,
                temperature=prompt.temperature,
                top_p=prompt.top_p,
                presence_penalty=prompt.presence_penalty,
                frequency_penalty=prompt.frequency_penalty,
                messages=messages,
            )
        except openai.error.OpenAIError as ex:
            self._log_exception(
                ex=ex,
                prompt=prompt,
                user_description=user_description
            )
            raise OpenAiServiceUnavailable()
        else:
            if not completion.choices:
                self._log(
                    user_description=user_description,
                    message='Response has no choices',
                    prompt=prompt
                )
                raise OpenAiServiceFailed()
            choice = completion.choices[0]
            finish_reason = getattr(choice.message, 'finish_reason', None)
            if finish_reason:
                self._log(
                    prompt=prompt,
                    user_description=user_description,
                    message='Response has finish reason',
                    response_text=finish_reason,
                )
                raise OpenAiServiceFailed()
            return choice.message.content

    def _test_response(self):
        return (
            '1. Prepare equipment and supplies | Gather the necessary '
            'equipment and supplies for honey harvesting, including bee '
            'suits, gloves, smoker, hive tool, brush, and honey jars.\n'
            '2. Choose the right time | Choose a warm and sunny day when '
            'most of the bees are out foraging and the honeycombs are '
            'full of mature honey.\n'
            '3. Smoke the bees | Light the smoker and gently puff smoke '
            'into the hive entrance to calm the bees and make them less '
            'aggressive.\n'
            '4. Remove the supers | Remove the honey supers one by one '
            'from the top of the hive, using the hive tool to scratch the '
            'wax cappings from the honeycomb frames.\n'
            '5. Brush off the bees | Gently brush off any remaining bees '
            'from the frames using a soft brush.\n'
            '6. Transport the supers | Transport the supers to a clean '
            'and dry location for honey extraction.\n'
            '7. Extract the honey | Uncap the honeycomb cells using an '
            'uncapping knife, and then extract the honey using a centrifuge '
            'or honey extractor.\n'
            '8. Strain the honey | Strain the honey to remove any impurities, '
            'such as wax or bee parts.\n'
            '9. Bottle the honey | Pour the honey into clean and sterilized '
            'jars and cap them tightly.\n'
            '10. Label the honey | Label each jar with the date of harvesting,'
            ' the type of honey, and the name and address of the producer.\n'
            '11. Store the honey | Store the honey in a cool and dark place '
            'until it is ready for sale or consumption.'
        )

    @abstractmethod
    def _get_step_data_from_text(
        self,
        number: int,
        name: str,
        description: str
    ) -> dict:
        pass

    def _get_steps_data_from_text(self, text: str) -> list:
        steps_data = [
            step.split('|') for step in text.split('\n')
            if step and step.find('|') > 0
        ]
        tasks_data = []
        for number, step in enumerate(steps_data):
            if len(step) != 2:
                continue
            else:
                limit = TaskTemplate.NAME_MAX_LENGTH
                name = step[0].strip()[:limit]
                description = step[1].strip()
            tasks_data.append(
                self._get_step_data_from_text(
                    number=number+1,
                    name=name,
                    description=description
                )
            )
        return tasks_data


class OpenAiService(BaseAiService):

    def __init__(
        self,
        user: UserModel,
        ident: Union[str, int],
        auth_type: AuthTokenType,
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
        ex: openai.error.OpenAIError,
        level: SentryLogLevel.LITERALS = SentryLogLevel.INFO,
    ):

        capture_sentry_message(
            message=f'Error AI generating template ({self.account.id})',
            data={
                'user_id': self.user.id,
                'user_email': self.user.email,
                'account_id': self.account.id,
                'ex': {
                    'error': ex.error,
                    'code': ex.code,
                    'http_body': ex.http_body,
                    'http_status': ex.http_status,
                    'json_body': ex.json_body,
                    'organization': ex.organization,
                },
                'request': {
                    'user_description': user_description,
                    'prompt': prompt.as_dict()
                }
            },
            level=level
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
                    'text': response_text
                },
                'request': {
                    'user_description': user_description,
                    'prompt': prompt.as_dict()
                }
            },
            level=level
        )

    def _get_step_data_from_text(
        self,
        number: int,
        name: str,
        description: str
    ) -> dict:
        return {
            'number': number,
            'name': name,
            'description': description,
            'raw_performers': [
                {
                    'type': PerformerType.USER,
                    'source_id': self.user.id,
                    'label': self.user.name
                }
            ]
        }

    def _post_template_generation_actions(self, user_description: str):
        account_service = AccountService(
            user=self.user,
            instance=self.account
        )
        account_service.inc_template_generations_count()

    def _get_template_data(self, user_description: str) -> dict:

        """ Generate template data dict from user description """

        if self.account.ai_template_generations_limit_exceeded:
            raise OpenAiLimitTemplateGenerations()
        prompt = OpenAiPrompt.objects.active().target_steps().first()
        if not prompt or not prompt.messages.active().exists():
            raise OpenAiStepsPromptNotExist()

        response_text = self._get_response(
            prompt=prompt,
            user_description=user_description
        )
        initial_tasks_data = self._get_steps_data_from_text(response_text)
        if not initial_tasks_data:
            self._log(
                prompt=prompt,
                user_description=user_description,
                message='Template steps not found',
                response_text=response_text
            )
            raise OpenAiTemplateStepsNotExist()
        initial_data = {
            'name': user_description[:TEMPLATE_NAME_LENGTH],
            'tasks': initial_tasks_data
        }
        template_service = TemplateService(
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type
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
                success=success
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
        ex: openai.error.OpenAIError,
        level: SentryLogLevel.LITERALS = SentryLogLevel.INFO,
    ):

        capture_sentry_message(
            message=f'Error AI gen template from landing ({self.ident})',
            data={
                'ident': self.ident,
                'user-agent': self.user_agent,
                'ex': {
                    'error': ex.error,
                    'code': ex.code,
                    'http_body': ex.http_body,
                    'http_status': ex.http_status,
                    'json_body': ex.json_body,
                    'organization': ex.organization,
                },
                'request': {
                    'user_description': user_description,
                    'prompt': prompt.as_dict()
                }
            },
            level=level
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
                    'text': response_text
                },
                'request': {
                    'user_description': user_description,
                    'prompt': prompt.as_dict()
                }
            },
            level=level
        )

    def _get_step_data_from_text(
        self,
        number: int,
        name: str,
        description: str
    ) -> dict:
        return {
            'number': number,
            'name': name,
            'description': description
        }

    def get_short_template_data(
        self,
        user_description: str
    ):

        """ Generate minimal template data dict from description """

        prompt = OpenAiPrompt.objects.active().target_steps().first()
        if not prompt or not prompt.messages.active().exists():
            raise OpenAiStepsPromptNotExist()

        response_text = self._get_response(
            prompt=prompt,
            user_description=user_description
        )
        initial_tasks_data = self._get_steps_data_from_text(response_text)
        if not initial_tasks_data:
            self._log(
                prompt=prompt,
                user_description=user_description,
                message='Template steps not found',
                response_text=response_text
            )
            raise OpenAiTemplateStepsNotExist()
        return {
            'name': user_description[:TEMPLATE_NAME_LENGTH],
            'tasks': initial_tasks_data
        }
