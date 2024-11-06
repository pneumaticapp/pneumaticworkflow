import openai.error
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.models import TaskTemplate
from pneumatic_backend.processes.enums import PerformerType
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
)
from pneumatic_backend.authentication.enums import (
    AuthTokenType
)
from pneumatic_backend.processes.api_v2.services.templates.ai import (
    OpenAiService
)
from pneumatic_backend.ai.enums import (
    OpenAIRole,
    OpenAiModel,
)
from pneumatic_backend.processes.api_v2.services.exceptions import (
    OpenAiServiceUnavailable,
    OpenAiServiceFailed,
    OpenAiLimitTemplateGenerations,
    OpenAiTemplateStepsNotExist,
    OpenAiStepsPromptNotExist,
)
from pneumatic_backend.processes.messages import workflow as messages
from pneumatic_backend.ai.tests.fixtures import create_test_prompt


UserModel = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'conf', (
        settings.CONFIGURATION_TESTING,
        settings.CONFIGURATION_DEV
    )
)
def test_get_response__ci_configuration__return_test_response(mocker, conf):

    # arrange
    description = 'some description'
    prompt = create_test_prompt()
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.settings.CONFIGURATION_CURRENT',
        conf
    )
    user = create_test_user()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER
    )

    test_response = mocker.Mock()
    test_response_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.OpenAiService._test_response',
        return_value=test_response
    )

    # act
    response = service._get_response(
        user_description=description,
        prompt=prompt
    )

    # assert
    test_response_mock.assert_called_once()
    assert response == test_response


def test_get_response__ok(mocker):

    # arrange
    description = 'some description'
    prompt = create_test_prompt(messages_count=2)
    message_2 = prompt.messages.filter(order=2).first()
    message_2.content = 'Second message'
    message_2.role = OpenAIRole.SYSTEM
    message_2.save()

    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.settings.CONFIGURATION_CURRENT',
        settings.CONFIGURATION_PROD
    )
    user = create_test_user()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER
    )
    ai_response = 'some ai response'
    message_mock = mocker.Mock(
        content=ai_response,
        finish_reason=None
    )
    choice_mock = mocker.Mock(
        message=message_mock
    )
    completion_mock = mocker.Mock(
        choices=[choice_mock]
    )
    create_completion_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.openai.ChatCompletion.create',
        return_value=completion_mock
    )

    # act
    response = service._get_response(
        user_description=description,
        prompt=prompt
    )

    # assert
    assert response == ai_response
    create_completion_mock.assert_called_once_with(
        model=prompt.model,
        temperature=prompt.temperature,
        top_p=prompt.top_p,
        presence_penalty=prompt.presence_penalty,
        frequency_penalty=prompt.frequency_penalty,
        user=f'u{user.id}',
        messages=[
            {
                "role": OpenAIRole.USER,
                "content": f'Some {description} text'
            },
            {
                "role": message_2.role,
                "content": message_2.content
            }
        ]
    )


def test_get_response__openai_error__raise_exception(mocker):

    # arrange
    description = 'some description'
    prompt = create_test_prompt()
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.settings.CONFIGURATION_CURRENT',
        settings.CONFIGURATION_PROD
    )
    user = create_test_user()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER
    )
    log_exception_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.OpenAiService._log_exception',
    )
    error = openai.error.RateLimitError()
    create_completion_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.openai.ChatCompletion.create',
        side_effect=error
    )

    # act
    with pytest.raises(OpenAiServiceUnavailable) as ex:
        service._get_response(
            user_description=description,
            prompt=prompt
        )

    # assert
    create_completion_mock.assert_called_once_with(
        model=prompt.model,
        temperature=prompt.temperature,
        top_p=prompt.top_p,
        presence_penalty=prompt.presence_penalty,
        frequency_penalty=prompt.frequency_penalty,
        user=f'u{user.id}',
        messages=[
            {
                "role": OpenAIRole.USER,
                "content": f'Some {description} text'
            }
        ]
    )
    log_exception_mock.assert_called_once_with(
        ex=error,
        user_description=description,
        prompt=prompt
    )
    assert ex.value.message == messages.MSG_PW_0042


def test_get_response__not_completion_choices__raise_exception(mocker):

    # arrange
    description = 'some description'
    prompt = create_test_prompt()
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.settings.CONFIGURATION_CURRENT',
        settings.CONFIGURATION_PROD
    )
    user = create_test_user()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER
    )
    log_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.OpenAiService._log',
    )
    completion_mock = mocker.Mock(
        choices=[]
    )
    create_completion_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.openai.ChatCompletion.create',
        return_value=completion_mock
    )

    # act
    with pytest.raises(OpenAiServiceFailed) as ex:
        service._get_response(
            user_description=description,
            prompt=prompt
        )

    # assert
    create_completion_mock.assert_called_once()
    log_mock.assert_called_once_with(
        message='Response has no choices',
        user_description=description,
        prompt=prompt
    )
    assert ex.value.message == messages.MSG_PW_0043


def test_get_response__finish_reason__raise_exception(mocker):

    # arrange
    description = 'some description'
    prompt = create_test_prompt()
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.settings.CONFIGURATION_CURRENT',
        settings.CONFIGURATION_PROD
    )
    user = create_test_user()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER
    )
    log_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.OpenAiService._log',
    )
    finish_reason = 'Some finish'
    message_mock = mocker.Mock(
        finish_reason=finish_reason
    )
    choice_mock = mocker.Mock(
        message=message_mock
    )
    completion_mock = mocker.Mock(
        choices=[choice_mock]
    )
    create_completion_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.openai.ChatCompletion.create',
        return_value=completion_mock
    )

    # act
    with pytest.raises(OpenAiServiceFailed) as ex:
        service._get_response(
            user_description=description,
            prompt=prompt
        )

    # assert
    create_completion_mock.assert_called_once()
    log_mock.assert_called_once_with(
        message='Response has finish reason',
        response_text=finish_reason,
        user_description=description,
        prompt=prompt
    )
    assert ex.value.message == messages.MSG_PW_0043


def test_get_steps_data_from_text__ok(mocker):

    # arrange
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.settings.CONFIGURATION_CURRENT',
        settings.CONFIGURATION_PROD
    )
    user = create_test_user()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER
    )
    text = 'prefix text\nTitle 1 | desc 1\n Title 2|desc 2\npostfix text'

    # act
    result = service._get_steps_data_from_text(text=text)

    # assert
    assert len(result) == 2
    assert result[0]['number'] == 1
    assert result[0]['name'] == 'Title 1'
    assert result[0]['description'] == 'desc 1'
    assert result[0]['raw_performers'] == [
        {
            'type': PerformerType.USER,
            'source_id': user.id,
            'label': user.name
        }
    ]

    assert result[1]['number'] == 2
    assert result[1]['name'] == 'Title 2'
    assert result[1]['description'] == 'desc 2'
    assert result[1]['raw_performers'] == [
        {
            'type': PerformerType.USER,
            'source_id': user.id,
            'label': user.name
        }
    ]


def test_get_steps_data_from_text__limit_task_name__ok(mocker):

    # arrange
    user = create_test_user()
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.settings.CONFIGURATION_CURRENT',
        settings.CONFIGURATION_PROD
    )
    limit = TaskTemplate.NAME_MAX_LENGTH
    task_name = 'o' * (limit + 1)
    text = f'{task_name} | desc'

    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER
    )

    # act
    result = service._get_steps_data_from_text(text=text)

    # assert
    assert len(result[0]['name']) == limit


def test_get_steps_data_from_text__not_delimiter__skip(mocker):

    # arrange
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.settings.CONFIGURATION_CURRENT',
        settings.CONFIGURATION_PROD
    )
    user = create_test_user()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER
    )
    text = 'Title desc'

    # act
    result = service._get_steps_data_from_text(text=text)

    # assert
    assert len(result) == 0


def test_get_post_template_generation_actions__ok(mocker):

    # arrange
    description = 'text'
    inc_template_generations_count_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.AccountService.inc_template_generations_count'
    )
    user = create_test_user()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER
    )

    # act
    service._post_template_generation_actions(
        user_description=description
    )

    # assert
    inc_template_generations_count_mock.assert_called_once()


def test_get_template_data__model_gpt4__ok(mocker):

    # arrange
    user = create_test_user()
    prompt = create_test_prompt(
        model=OpenAiModel.GPT_4,
        content=(
            'Generate a business process description consisting of '
            'unnumbered steps with meaningful names where each step is '
            'on a new line and has the following structure: step name | step '
            'description.Based on the following input: {{user_description}}'
        )
    )
    description = 'By milk'
    ai_response = (
        '1. Hive inspection|Inspect the beehives to determine which ones '
        'are ready for honey collection.\n'
        '2. Smoke the hive | Use a smoker to calm the bees and make them '
        'less aggressive.'
    )
    get_response_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.OpenAiService._get_response',
        return_value=ai_response
    )
    post_template_generation_actions_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.OpenAiService._post_template_generation_actions',
    )
    task_api_name = 'some-api-name'
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.template.'
        'create_api_name',
        return_value=task_api_name
    )
    template_generation_init_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.AnalyticService.template_generation_init'
    )

    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER
    )

    # act
    template_data = service.get_template_data(user_description=description)

    # assert
    get_response_mock.assert_called_once_with(
        user_description=description,
        prompt=prompt
    )
    post_template_generation_actions_mock.assert_called_once_with(
        description
    )
    template_generation_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        description=description,
        success=True
    )
    assert template_data == {
        'name': description,
        'wf_name_template': None,
        'description': '',
        'is_active': False,
        'finalizable': True,
        'is_public': False,
        'template_owners': [user.id],
        'tasks_count': 2,
        'performers_count': 1,
        'kickoff': {
            'description': '',
            'fields': []
        },
        'tasks': [
            {
                'number': 1,
                'name': '1. Hive inspection',
                'api_name': task_api_name,
                'description': (
                    'Inspect the beehives to determine which ones '
                    'are ready for honey collection.'
                ),
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                        'label': user.name
                    }
                ],
            },
            {
                'number': 2,
                'name': '2. Smoke the hive',
                'api_name': task_api_name,
                'description': (
                    'Use a smoker to calm the bees and '
                    'make them less aggressive.'
                ),
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                        'label': user.name
                    }
                ],
            }
        ]
    }


def test_get_template_data_model_gpt3__ok(mocker):

    # arrange
    user = create_test_user()
    prompt = create_test_prompt()
    description = 'My lovely business process'
    ai_response = (
        '1. Hive inspection|Inspect the beehives to determine which ones '
        'are ready for honey collection.\n'
        '2. Smoke the hive | Use a smoker to calm the bees and make them '
        'less aggressive.'
    )
    get_response_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.OpenAiService._get_response',
        return_value=ai_response
    )
    post_template_generation_actions_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.OpenAiService._post_template_generation_actions',
    )
    task_api_name = 'some-api-name'
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.template.'
        'create_api_name',
        return_value=task_api_name
    )
    template_generation_init_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.AnalyticService.template_generation_init'
    )
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER
    )

    # act
    template_data = service.get_template_data(user_description=description)

    # assert
    get_response_mock.assert_called_once_with(
        user_description=description,
        prompt=prompt
    )
    post_template_generation_actions_mock.assert_called_once_with(
        description
    )
    template_generation_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        description=description,
        success=True
    )

    assert template_data == {
        'name': description,
        'wf_name_template': None,
        'description': '',
        'is_active': False,
        'finalizable': True,
        'is_public': False,
        'template_owners': [user.id],
        'tasks_count': 2,
        'performers_count': 1,
        'kickoff': {
            'description': '',
            'fields': []
        },
        'tasks': [
            {
                'number': 1,
                'name': '1. Hive inspection',
                'api_name': task_api_name,
                'description': (
                    'Inspect the beehives to determine which ones '
                    'are ready for honey collection.'
                ),
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                        'label': user.name
                    }
                ],
            },
            {
                'number': 2,
                'name': '2. Smoke the hive',
                'api_name': task_api_name,
                'description': (
                    'Use a smoker to calm the bees and '
                    'make them less aggressive.'
                ),
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                        'label': user.name
                    }
                ],
            }
        ]
    }


def test_get_template_data__limit_exceeded__raise_exception(mocker):

    # arrange
    user = create_test_user()
    account = user.account
    account.ai_templates_generations = 10
    account.max_ai_templates_generations = 10
    account.save(
        update_fields=[
            'ai_templates_generations',
            'max_ai_templates_generations'
        ]
    )

    description = 'My lovely business process'
    get_response_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.OpenAiService._get_response',
    )
    template_generation_init_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.AnalyticService.template_generation_init'
    )

    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER
    )

    # act
    with pytest.raises(OpenAiLimitTemplateGenerations) as ex:
        service.get_template_data(user_description=description)

    # assert
    get_response_mock.assert_not_called()
    assert ex.value.message == messages.MSG_PW_0044
    template_generation_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        description=description,
        success=False
    )


def test_get_template_data__not_prompt__raise_exception(mocker):

    # arrange
    user = create_test_user()
    description = 'My lovely business process'
    get_response_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.OpenAiService._get_response',
    )
    template_generation_init_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.AnalyticService.template_generation_init'
    )
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER
    )

    # act
    with pytest.raises(OpenAiStepsPromptNotExist) as ex:
        service.get_template_data(user_description=description)

    # assert
    get_response_mock.assert_not_called()
    assert ex.value.message == messages.MSG_PW_0046
    template_generation_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        description=description,
        success=False
    )


def test_get_template_data__not_prompt_message__raise_exception(mocker):

    # arrange
    user = create_test_user()
    description = 'My lovely business process'
    create_test_prompt(messages_count=0)
    get_response_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.OpenAiService._get_response',
    )
    template_generation_init_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.AnalyticService.template_generation_init'
    )
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER
    )

    # act
    with pytest.raises(OpenAiStepsPromptNotExist) as ex:
        service.get_template_data(user_description=description)

    # assert
    get_response_mock.assert_not_called()
    assert ex.value.message == messages.MSG_PW_0046
    template_generation_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        description=description,
        success=False
    )


def test_get_template_data__not_steps__raise_exception(mocker):

    # arrange
    user = create_test_user()
    description = 'My lovely business process'
    prompt = create_test_prompt()
    response_mock = 'Some response'
    get_response_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.OpenAiService._get_response',
        return_value=response_mock
    )
    get_tasks_data_from_text_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.OpenAiService._get_steps_data_from_text',
        return_value=[]
    )
    log_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.OpenAiService._log',
    )
    template_generation_init_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.AnalyticService.template_generation_init'
    )

    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER
    )

    # act
    with pytest.raises(OpenAiTemplateStepsNotExist) as ex:
        service.get_template_data(user_description=description)

    # assert
    get_response_mock.assert_called_once_with(
        user_description=description,
        prompt=prompt
    )
    get_tasks_data_from_text_mock.assert_called_once_with(response_mock)
    assert ex.value.message == messages.MSG_PW_0045
    log_mock.assert_called_once_with(
        message='Template steps not found',
        user_description=description,
        prompt=prompt,
        response_text=response_mock
    )
    template_generation_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        description=description,
        success=False
    )
