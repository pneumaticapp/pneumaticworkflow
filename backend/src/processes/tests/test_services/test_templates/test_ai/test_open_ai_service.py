# ruff: noqa: E501
import json
import pytest
from django.contrib.auth import get_user_model
from requests.exceptions import ConnectionError as RequestsConnectionError

from src.ai.enums import (
    OpenAIPromptTarget,
    OpenAIRole,
)
from src.ai.tests.fixtures import create_test_prompt
from src.authentication.enums import (
    AuthTokenType,
)
from src.processes.enums import (
    OwnerRole,
    ConditionAction,
    OwnerType,
    PerformerType,
    PredicateOperator,
    PredicateType,
)
from src.processes.messages import workflow as messages
from src.processes.models.templates.task import TaskTemplate
from src.processes.services.exceptions import (
    OpenAiLimitTemplateGenerations,
    OpenAiServiceFailed,
    OpenAiServiceUnavailable,
    OpenAiStepsPromptNotExist,
    OpenAiTemplateStepsNotExist,
)
from src.processes.services.templates.ai import (
    OpenAiService,
)
from src.processes.tests.fixtures import (
    create_test_user,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


# === _get_response (legacy text-based) ===


def test_get_response__ci_configuration__return_test_response(mocker):

    # arrange
    description = 'some description'
    prompt = create_test_prompt()
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        None,
    )
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_ORG',
        None,
    )
    user = create_test_user()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )

    test_response = mocker.Mock()
    test_response_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.OpenAiService._test_steps_response',
        return_value=test_response,
    )

    # act
    response = service._get_response(
        user_description=description,
        prompt=prompt,
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
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        'some_key',
    )
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_ORG',
        'some_org',
    )
    user = create_test_user()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    ai_response = 'some ai response'
    call_api_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.BaseAiService._call_responses_api',
        return_value=ai_response,
    )

    # act
    response = service._get_response(
        user_description=description,
        prompt=prompt,
    )

    # assert
    assert response == ai_response
    call_api_mock.assert_called_once()
    payload = call_api_mock.call_args[0][0]
    assert payload['presence_penalty'] == prompt.presence_penalty
    assert payload['frequency_penalty'] == prompt.frequency_penalty


def test_get_response__multiple_messages__uses_ordered_input(mocker):

    # arrange
    description = 'some description'
    prompt = create_test_prompt(messages_count=4)
    message_1 = prompt.messages.filter(order=1).first()
    message_1.role = OpenAIRole.SYSTEM
    message_1.content = 'System 1'
    message_1.save()
    message_2 = prompt.messages.filter(order=2).first()
    message_2.role = OpenAIRole.USER
    message_2.content = 'User 1 {{ user_description }}'
    message_2.save()
    message_3 = prompt.messages.filter(order=3).first()
    message_3.role = OpenAIRole.ASSISTANT
    message_3.content = 'Assistant example'
    message_3.save()
    message_4 = prompt.messages.filter(order=4).first()
    message_4.role = OpenAIRole.SYSTEM
    message_4.content = 'System 2'
    message_4.save()

    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        'some_key',
    )
    user = create_test_user()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    call_api_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.BaseAiService._call_responses_api',
        return_value='ok',
    )

    # act
    service._get_response(
        user_description=description,
        prompt=prompt,
    )

    # assert
    payload = call_api_mock.call_args[0][0]
    assert payload['instructions'] == 'System 1\n\nSystem 2'
    assert payload['input'] == [
        {'role': OpenAIRole.USER, 'content': 'User 1 some description'},
        {'role': OpenAIRole.ASSISTANT, 'content': 'Assistant example'},
    ]


def test_get_response__api_error__raise_exception(mocker):

    # arrange
    description = 'some description'
    prompt = create_test_prompt()
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        'some_key',
    )
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_ORG',
        'some_org',
    )
    user = create_test_user()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    log_exception_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.OpenAiService._log_exception',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'ai.BaseAiService._call_responses_api',
        side_effect=OpenAiServiceUnavailable(),
    )

    # act
    with pytest.raises(OpenAiServiceUnavailable):
        service._get_response(
            user_description=description,
            prompt=prompt,
        )

    # assert
    log_exception_mock.assert_called_once()


# === _get_json_response ===


def test_get_json_response__no_api_key__return_test_response(mocker):

    # arrange
    description = 'some description'
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        None,
    )
    user = create_test_user()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )

    test_response = mocker.Mock()
    test_response_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.OpenAiService._test_response',
        return_value=test_response,
    )

    # act
    response = service._get_json_response(
        user_description=description,
    )

    # assert
    test_response_mock.assert_called_once()
    assert response == test_response


def test_get_json_response__ok__uses_responses_api(mocker):

    # arrange
    description = 'some description'
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        'some_key',
    )
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_ORG',
        'some_org',
    )
    user = create_test_user()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    ai_response = '{"name": "Test", "tasks": []}'
    call_api_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.BaseAiService._call_responses_api',
        return_value=ai_response,
    )

    # act
    response = service._get_json_response(
        user_description=description,
    )

    # assert
    assert response == ai_response
    call_api_mock.assert_called_once()
    payload = call_api_mock.call_args[0][0]
    assert payload['model'] == 'gpt-4.1-mini'
    assert 'instructions' in payload
    assert payload['input'] == description
    assert payload['presence_penalty'] == 0
    assert payload['frequency_penalty'] == 0


def test_get_json_response__prompt_messages__uses_ordered_input(mocker):

    # arrange
    description = 'some description'
    prompt = create_test_prompt(messages_count=3)
    prompt.presence_penalty = 0.7
    prompt.frequency_penalty = -0.4
    prompt.save()
    message_1 = prompt.messages.filter(order=1).first()
    message_1.role = OpenAIRole.SYSTEM
    message_1.content = 'System message'
    message_1.save()
    message_2 = prompt.messages.filter(order=2).first()
    message_2.role = OpenAIRole.ASSISTANT
    message_2.content = 'Assistant example'
    message_2.save()
    message_3 = prompt.messages.filter(order=3).first()
    message_3.role = OpenAIRole.USER
    message_3.content = 'User asks: {{ user_description }}'
    message_3.save()

    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        'some_key',
    )
    user = create_test_user()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    call_api_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.BaseAiService._call_responses_api',
        return_value='{"name":"T","tasks":[]}',
    )

    # act
    service._get_json_response(
        user_description=description,
        prompt=prompt,
    )

    # assert
    payload = call_api_mock.call_args[0][0]
    assert payload['instructions'] == 'System message'
    assert payload['input'] == [
        {'role': OpenAIRole.ASSISTANT, 'content': 'Assistant example'},
        {'role': OpenAIRole.USER, 'content': 'User asks: some description'},
    ]
    assert payload['presence_penalty'] == prompt.presence_penalty
    assert payload['frequency_penalty'] == prompt.frequency_penalty


def test_get_json_response__api_error__raise_exception(mocker):

    # arrange
    description = 'some description'
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        'some_key',
    )
    user = create_test_user()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    mocker.patch(
        'src.processes.services.templates.'
        'ai.BaseAiService._call_responses_api',
        side_effect=OpenAiServiceUnavailable(),
    )

    # act
    with pytest.raises(OpenAiServiceUnavailable):
        service._get_json_response(
            user_description=description,
        )


# === _get_steps_data_from_text (legacy text parsing) ===


def test_get_steps_data_from_text__ok(mocker):

    # arrange
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        'some_key',
    )
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_ORG',
        'some_org',
    )
    user = create_test_user()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
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
            'label': user.name,
        },
    ]

    assert result[1]['number'] == 2
    assert result[1]['name'] == 'Title 2'
    assert result[1]['description'] == 'desc 2'
    assert result[1]['raw_performers'] == [
        {
            'type': PerformerType.USER,
            'source_id': user.id,
            'label': user.name,
        },
    ]
