import json

import pytest
import requests as http_requests

from src.ai.enums import (
    OpenAIPromptTarget,
    OpenAIRole,
)
from src.ai.tests.fixtures import create_test_prompt
from src.authentication.enums import AuthTokenType
from src.processes.consts import TEMPLATE_NAME_LENGTH
from src.processes.enums import (
    ConditionAction,
    FieldType,
    PredicateOperator,
    PredicateType,
)
from src.processes.models.templates.task import TaskTemplate
from src.processes.services.exceptions import (
    OpenAiServiceFailed,
    OpenAiServiceUnavailable,
)
from src.processes.services.templates.ai import (
    DEFAULT_TEMPLATE_INSTRUCTION,
    OpenAiService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


# === 3.1 _openai_headers ===


def test_openai_headers__no_org__ok(mocker):

    """API key set, no org."""

    # arrange
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        'test-key-123',
    )
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_ORG',
        '',
    )
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )

    # act
    result = service._openai_headers()

    # assert
    assert result == {
        'Authorization': 'Bearer test-key-123',
        'Content-Type': 'application/json',
    }


def test_openai_headers__with_org__includes_org(mocker):

    """API key and org both set."""

    # arrange
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        'test-key-123',
    )
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_ORG',
        'org-abc',
    )
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )

    # act
    result = service._openai_headers()

    # assert
    assert result == {
        'Authorization': 'Bearer test-key-123',
        'Content-Type': 'application/json',
        'OpenAI-Organization': 'org-abc',
    }


# === 3.2 _test_response ===


def test_test_response__ok__returns_json():

    """Returns valid JSON with expected structure."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )

    # act
    result = service._test_response()

    # assert
    data = json.loads(result)
    assert 'name' in data
    assert 'description' in data
    assert 'kickoff' in data
    assert 'tasks' in data
    assert len(data['tasks']) > 0
    assert 'fields' in data['kickoff']


# === 3.3 _extract_json ===


def test_extract_json__plain__returns_as_is():

    """Plain JSON string without fences."""

    # arrange
    text = '{"name": "test"}'

    # act
    result = OpenAiService._extract_json(text=text)

    # assert
    assert result == '{"name": "test"}'


def test_extract_json__json_fence__extracts():

    """JSON wrapped in ```json fences."""

    # arrange
    text = '```json\n{"name": "test"}\n```'

    # act
    result = OpenAiService._extract_json(text=text)

    # assert
    assert result == '{"name": "test"}'


def test_extract_json__bare_fence__extracts():

    """JSON wrapped in ``` fences (no lang)."""

    # arrange
    text = '```\n{"name": "test"}\n```'

    # act
    result = OpenAiService._extract_json(text=text)

    # assert
    assert result == '{"name": "test"}'


def test_extract_json__whitespace__stripped():

    """Leading/trailing whitespace."""

    # arrange
    text = '  \n  {"name": "test"}  \n  '

    # act
    result = OpenAiService._extract_json(text=text)

    # assert
    assert result == '{"name": "test"}'


# === 3.4 _normalize_field ===


def test_normalize_field__string__ok():

    """Valid string field with all keys."""

    # arrange
    field_data = {
        'order': 2,
        'name': 'Project Name',
        'type': FieldType.STRING,
        'is_required': True,
        'description': 'Name of the project',
        'default': 'My Project',
        'api_name': 'field-project-name',
    }

    # act
    result = OpenAiService._normalize_field(field_data=field_data)

    # assert
    assert result['order'] == 2
    assert result['name'] == 'Project Name'
    assert result['type'] == FieldType.STRING
    assert result['is_required'] is True
    assert result['description'] == 'Name of the project'
    assert result['default'] == 'My Project'
    assert result['api_name'] == 'field-project-name'
    assert 'selections' not in result


def test_normalize_field__bad_type__fallback():

    """Invalid type falls back to string."""

    # arrange
    field_data = {
        'type': 'invalid_type',
        'api_name': 'field-test',
    }

    # act
    result = OpenAiService._normalize_field(field_data=field_data)

    # assert
    assert result['type'] == FieldType.STRING


def test_normalize_field__dropdown__has_sels():

    """Selection field (dropdown) with selections."""

    # arrange
    field_data = {
        'type': FieldType.DROPDOWN,
        'api_name': 'field-priority',
        'selections': [
            {'value': 'High'},
            {'value': 'Low'},
        ],
    }

    # act
    result = OpenAiService._normalize_field(field_data=field_data)

    # assert
    assert result['type'] == FieldType.DROPDOWN
    assert len(result['selections']) == 2
    assert result['selections'][0]['value'] == 'High'
    assert result['selections'][1]['value'] == 'Low'
    assert 'api_name' in result['selections'][0]
    assert 'api_name' in result['selections'][1]


def test_normalize_field__empty_sel__skipped():

    """Selection field with empty selection values."""

    # arrange
    field_data = {
        'type': FieldType.DROPDOWN,
        'api_name': 'field-test',
        'selections': [
            {'value': ''},
            {'value': 'Valid'},
        ],
    }

    # act
    result = OpenAiService._normalize_field(field_data=field_data)

    # assert
    assert len(result['selections']) == 1
    assert result['selections'][0]['value'] == 'Valid'


def test_normalize_field__sel_not_dict__skipped():

    """Selection item is not a dict."""

    # arrange
    field_data = {
        'type': FieldType.DROPDOWN,
        'api_name': 'field-test',
        'selections': [
            'not a dict',
            {'value': 'Valid'},
        ],
    }

    # act
    result = OpenAiService._normalize_field(field_data=field_data)

    # assert
    assert len(result['selections']) == 1
    assert result['selections'][0]['value'] == 'Valid'


def test_normalize_field__str_with_sel__no_sel():

    """Non-selection field ignores selections."""

    # arrange
    field_data = {
        'type': FieldType.STRING,
        'api_name': 'field-test',
        'selections': [
            {'value': 'Should not appear'},
        ],
    }

    # act
    result = OpenAiService._normalize_field(field_data=field_data)

    # assert
    assert 'selections' not in result


def test_normalize_field__no_api_name__generated(mocker):

    """Missing api_name generates one."""

    # arrange
    mocker.patch(
        'src.processes.services.templates.ai.create_api_name',
        return_value='field-generated',
    )
    field_data = {
        'type': FieldType.STRING,
    }

    # act
    result = OpenAiService._normalize_field(field_data=field_data)

    # assert
    assert result['api_name'] == 'field-generated'


def test_normalize_field__long_name__truncated():

    """Name truncated to 50 chars."""

    # arrange
    field_data = {
        'name': 'A' * 100,
        'api_name': 'field-test',
    }

    # act
    result = OpenAiService._normalize_field(field_data=field_data)

    # assert
    assert len(result['name']) == 50


def test_normalize_field__defaults__ok():

    """Default values for missing keys."""

    # arrange
    field_data = {
        'api_name': 'field-test',
    }

    # act
    result = OpenAiService._normalize_field(field_data=field_data)

    # assert
    assert result['order'] == 1
    assert result['name'] == ''
    assert result['type'] == FieldType.STRING
    assert result['description'] == ''
    assert result['default'] == ''


def test_normalize_field__is_req_default__false():

    """is_required default is False."""

    # arrange
    field_data = {
        'api_name': 'field-test',
    }

    # act
    result = OpenAiService._normalize_field(field_data=field_data)

    # assert
    assert result['is_required'] is False


# === 3.5 _get_start_task_condition ===


def test_get_start_task_cond__none__kickoff(mocker):

    """prev_task_api_name is None (kickoff)."""

    # arrange
    mocker.patch(
        'src.processes.services.templates.ai.create_api_name',
        return_value='generated-name',
    )
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )

    # act
    result = service._get_start_task_condition(
        prev_task_api_name=None,
    )

    # assert
    assert result['order'] == 1
    assert result['action'] == ConditionAction.START_TASK
    predicate = result['rules'][0]['predicates'][0]
    assert predicate['field_type'] == PredicateType.KICKOFF
    assert predicate['operator'] == PredicateOperator.COMPLETED
    assert predicate['field'] is None
    assert predicate['value'] is None


def test_get_start_task_cond__task__ok(mocker):

    """prev_task_api_name provided (task)."""

    # arrange
    mocker.patch(
        'src.processes.services.templates.ai.create_api_name',
        return_value='generated-name',
    )
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )

    # act
    result = service._get_start_task_condition(
        prev_task_api_name='task-prev-123',
    )

    # assert
    assert result['order'] == 1
    assert result['action'] == ConditionAction.START_TASK
    predicate = result['rules'][0]['predicates'][0]
    assert predicate['field_type'] == PredicateType.TASK
    assert predicate['operator'] == PredicateOperator.COMPLETED
    assert predicate['field'] == 'task-prev-123'
    assert predicate['value'] is None


# === 3.6 _call_responses_api ===


def test_call_responses_api__ok__returns_text(mocker):

    """Successful response with output_text."""

    # arrange
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        'test-key',
    )
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_ORG',
        '',
    )
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'output': [
            {
                'type': 'message',
                'content': [
                    {
                        'type': 'output_text',
                        'text': 'generated text',
                    },
                ],
            },
        ],
    }
    mock_response.raise_for_status = mocker.Mock()
    post_mock = mocker.patch(
        'src.processes.services.templates.ai.http_requests.post',
        return_value=mock_response,
    )

    # act
    result = service._call_responses_api(
        payload={'model': 'gpt-4.1-mini', 'input': 'test'},
    )

    # assert
    assert result == 'generated text'
    post_mock.assert_called_once_with(
        'https://api.openai.com/v1/responses',
        headers=service._openai_headers(),
        json={'model': 'gpt-4.1-mini', 'input': 'test'},
        timeout=120,
    )


def test_call_responses_api__req_err__unavail(mocker):

    """RequestException raises Unavailable."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    mocker.patch(
        'src.processes.services.templates.ai.http_requests.post',
        side_effect=http_requests.RequestException('conn err'),
    )

    # act
    with pytest.raises(OpenAiServiceUnavailable):
        service._call_responses_api(
            payload={'model': 'gpt-4.1-mini'},
        )


def test_call_responses_api__no_text__failed(mocker):

    """No output_text in response raises Failed."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'output': [
            {
                'type': 'other',
                'content': [],
            },
        ],
    }
    mock_response.raise_for_status = mocker.Mock()
    mocker.patch(
        'src.processes.services.templates.ai.http_requests.post',
        return_value=mock_response,
    )

    # act
    with pytest.raises(OpenAiServiceFailed):
        service._call_responses_api(
            payload={'model': 'gpt-4.1-mini'},
        )


def test_call_responses_api__http_err__unavail(mocker):

    """HTTP error status raises Unavailable."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    mock_response = mocker.Mock()
    mock_response.raise_for_status.side_effect = (
        http_requests.HTTPError('500 Server Error')
    )
    mocker.patch(
        'src.processes.services.templates.ai.http_requests.post',
        return_value=mock_response,
    )

    # act
    with pytest.raises(OpenAiServiceUnavailable):
        service._call_responses_api(
            payload={'model': 'gpt-4.1-mini'},
        )


# === 3.7 _get_response (No tests only) ===


def test_get_response__sys_and_user__payload_ok(mocker):

    """Prompt with system+user messages builds payload."""

    # arrange
    prompt = create_test_prompt(
        messages_count=2,
        target=OpenAIPromptTarget.GET_STEPS,
    )
    msg_1 = prompt.messages.filter(order=1).first()
    msg_1.role = OpenAIRole.SYSTEM
    msg_1.content = 'System instruction'
    msg_1.save()
    msg_2 = prompt.messages.filter(order=2).first()
    msg_2.role = OpenAIRole.USER
    msg_2.content = 'User says: {{ user_description }}'
    msg_2.save()

    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        'test-key',
    )
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_ORG',
        '',
    )
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    call_api_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.BaseAiService._call_responses_api',
        return_value='response text',
    )

    # act
    result = service._get_response(
        prompt=prompt,
        user_description='build a house',
    )

    # assert
    assert result == 'response text'
    call_api_mock.assert_called_once_with(
        {
            'model': prompt.model,
            'input': 'User says: build a house',
            'temperature': prompt.temperature,
            'top_p': prompt.top_p,
            'instructions': 'System instruction',
        },
    )


def test_get_response__presence_penalty__in_payload(mocker):

    """Prompt with presence_penalty in payload."""

    # arrange
    prompt = create_test_prompt(
        target=OpenAIPromptTarget.GET_STEPS,
    )
    prompt.presence_penalty = 0.5
    prompt.save()

    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        'test-key',
    )
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_ORG',
        '',
    )
    account = create_test_account()
    user = create_test_owner(account=account)
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
        prompt=prompt,
        user_description='test',
    )

    # assert
    payload = call_api_mock.call_args[0][0]
    assert payload['presence_penalty'] == 0.5


def test_get_response__freq_penalty__in_payload(mocker):

    """Prompt with frequency_penalty in payload."""

    # arrange
    prompt = create_test_prompt(
        target=OpenAIPromptTarget.GET_STEPS,
    )
    prompt.frequency_penalty = 0.3
    prompt.save()

    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        'test-key',
    )
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_ORG',
        '',
    )
    account = create_test_account()
    user = create_test_owner(account=account)
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
        prompt=prompt,
        user_description='test',
    )

    # assert
    payload = call_api_mock.call_args[0][0]
    assert payload['frequency_penalty'] == 0.3


def test_get_response__svc_failed__logs_raises(mocker):

    """ServiceFailed exception logs and re-raises."""

    # arrange
    prompt = create_test_prompt(
        target=OpenAIPromptTarget.GET_STEPS,
    )
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        'test-key',
    )
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_ORG',
        '',
    )
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    mocker.patch(
        'src.processes.services.templates.'
        'ai.BaseAiService._call_responses_api',
        side_effect=OpenAiServiceFailed(),
    )
    log_exception_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.OpenAiService._log_exception',
    )

    # act
    with pytest.raises(OpenAiServiceFailed):
        service._get_response(
            prompt=prompt,
            user_description='test',
        )

    # assert
    log_exception_mock.assert_called_once_with(
        ex=mocker.ANY,
        prompt=prompt,
        user_description='test',
    )


# === 3.8 _get_json_response (No tests only) ===


def test_get_json_resp__prompt_active__uses_prompt(mocker):

    """Prompt with active messages uses prompt."""

    # arrange
    prompt = create_test_prompt(
        target=OpenAIPromptTarget.GET_TEMPLATE,
        messages_count=2,
    )
    msg_1 = prompt.messages.filter(order=1).first()
    msg_1.role = OpenAIRole.SYSTEM
    msg_1.content = 'Custom system instruction'
    msg_1.save()
    msg_2 = prompt.messages.filter(order=2).first()
    msg_2.role = OpenAIRole.USER
    msg_2.content = 'Custom user: {{ user_description }}'
    msg_2.save()

    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        'test-key',
    )
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    call_api_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.BaseAiService._call_responses_api',
        return_value='{"name": "Test"}',
    )

    # act
    result = service._get_json_response(
        user_description='hire employee',
        prompt=prompt,
    )

    # assert
    assert result == '{"name": "Test"}'
    call_api_mock.assert_called_once_with(
        {
            'model': prompt.model,
            'input': 'Custom user: hire employee',
            'temperature': prompt.temperature,
            'top_p': prompt.top_p,
            'instructions': 'Custom system instruction',
        },
    )


def test_get_json_resp__no_prompt__defaults(mocker):

    """Prompt=None uses default model/instruction."""

    # arrange
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        'test-key',
    )
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    call_api_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.BaseAiService._call_responses_api',
        return_value='{"name": "Test"}',
    )

    # act
    service._get_json_response(
        user_description='onboard new hire',
        prompt=None,
    )

    # assert
    call_api_mock.assert_called_once_with(
        {
            'model': 'gpt-4.1-mini',
            'input': 'onboard new hire',
            'temperature': 0.7,
            'top_p': 1,
            'instructions': DEFAULT_TEMPLATE_INSTRUCTION,
        },
    )


def test_get_json_resp__no_active_msgs__default(mocker):

    """Prompt without active msgs uses default instr."""

    # arrange
    prompt = create_test_prompt(
        target=OpenAIPromptTarget.GET_TEMPLATE,
        messages_count=1,
    )
    msg = prompt.messages.first()
    msg.is_active = False
    msg.save()

    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        'test-key',
    )
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    call_api_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.BaseAiService._call_responses_api',
        return_value='{"name": "Test"}',
    )

    # act
    service._get_json_response(
        user_description='test desc',
        prompt=prompt,
    )

    # assert
    payload = call_api_mock.call_args[0][0]
    assert payload['instructions'] == DEFAULT_TEMPLATE_INSTRUCTION
    assert payload['input'] == 'test desc'


def test_get_json_resp__err_with_prompt__logs(mocker):

    """API error with prompt logs exception."""

    # arrange
    prompt = create_test_prompt(
        target=OpenAIPromptTarget.GET_TEMPLATE,
    )
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        'test-key',
    )
    account = create_test_account()
    user = create_test_owner(account=account)
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
    log_exception_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.OpenAiService._log_exception',
    )

    # act
    with pytest.raises(OpenAiServiceUnavailable):
        service._get_json_response(
            user_description='test',
            prompt=prompt,
        )

    # assert
    log_exception_mock.assert_called_once_with(
        ex=mocker.ANY,
        prompt=prompt,
        user_description='test',
    )


def test_get_json_resp__err_no_prompt__no_log(mocker):

    """API error without prompt does not log."""

    # arrange
    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        'test-key',
    )
    account = create_test_account()
    user = create_test_owner(account=account)
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
    log_exception_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.OpenAiService._log_exception',
    )

    # act
    with pytest.raises(OpenAiServiceUnavailable):
        service._get_json_response(
            user_description='test',
            prompt=None,
        )

    # assert
    assert log_exception_mock.call_count == 0


def test_get_json_resp__presence_pen__in_payload(mocker):

    """Presence_penalty included when set."""

    # arrange
    prompt = create_test_prompt(
        target=OpenAIPromptTarget.GET_TEMPLATE,
    )
    prompt.presence_penalty = 0.6
    prompt.save()

    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        'test-key',
    )
    account = create_test_account()
    user = create_test_owner(account=account)
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
    service._get_json_response(
        user_description='test',
        prompt=prompt,
    )

    # assert
    payload = call_api_mock.call_args[0][0]
    assert payload['presence_penalty'] == 0.6


def test_get_json_resp__freq_pen__in_payload(mocker):

    """Frequency_penalty included when set."""

    # arrange
    prompt = create_test_prompt(
        target=OpenAIPromptTarget.GET_TEMPLATE,
    )
    prompt.frequency_penalty = 0.4
    prompt.save()

    mocker.patch(
        'src.processes.services.templates.ai.settings.OPENAI_API_KEY',
        'test-key',
    )
    account = create_test_account()
    user = create_test_owner(account=account)
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
    service._get_json_response(
        user_description='test',
        prompt=prompt,
    )

    # assert
    payload = call_api_mock.call_args[0][0]
    assert payload['frequency_penalty'] == 0.4


# === 3.12 _get_steps_data_from_text (No tests only) ===


def test_get_steps_data__empty__returns_empty():

    """Empty text returns empty list."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )

    # act
    result = service._get_steps_data_from_text(text='')

    # assert
    assert result == []


def test_get_steps_data__no_pipe__skipped():

    """Lines without pipe are skipped."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )

    # act
    result = service._get_steps_data_from_text(
        text='no pipe here\nanother line',
    )

    # assert
    assert result == []


def test_get_steps_data__multi_pipe__skipped():

    """Lines with multiple pipes are skipped."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )

    # act
    result = service._get_steps_data_from_text(
        text='a|b|c\nd|e|f',
    )

    # assert
    assert result == []


def test_get_steps_data__long_name__truncated():

    """Names truncated to NAME_MAX_LENGTH."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    long_name = 'A' * 500
    text = f'{long_name}|description here'

    # act
    result = service._get_steps_data_from_text(text=text)

    # assert
    assert len(result) == 1
    assert len(result[0]['name']) == TaskTemplate.NAME_MAX_LENGTH


# === 3.14 _parse_template_from_json ===


def test_parse_tmpl_json__ok__full_data(mocker):

    """Valid JSON with tasks and kickoff fields."""

    # arrange
    mocker.patch(
        'src.processes.services.templates.ai.create_api_name',
        return_value='generated-name',
    )
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    data = {
        'name': 'Onboarding',
        'description': 'New hire onboarding',
        'kickoff': {
            'fields': [
                {
                    'api_name': 'field-emp-name',
                    'order': 1,
                    'name': 'Employee Name',
                    'type': 'string',
                    'is_required': True,
                    'description': 'Full name',
                },
            ],
        },
        'tasks': [
            {
                'name': 'Setup accounts',
                'description': 'Create email and Slack',
                'fields': [
                    {
                        'api_name': 'field-email',
                        'order': 1,
                        'name': 'Email',
                        'type': 'string',
                        'is_required': True,
                        'description': 'Work email',
                    },
                ],
            },
        ],
    }
    text = json.dumps(data)

    # act
    result = service._parse_template_from_json(text=text)

    # assert
    assert result['name'] == 'Onboarding'
    assert result['description'] == 'New hire onboarding'
    assert len(result['kickoff']['fields']) == 1
    assert len(result['tasks']) == 1
    assert result['tasks'][0]['number'] == 1
    assert result['tasks'][0]['name'] == 'Setup accounts'
    assert 'fields' in result['tasks'][0]
    assert 'conditions' in result['tasks'][0]


def test_parse_tmpl_json__fenced__ok(mocker):

    """JSON with code fences extracted correctly."""

    # arrange
    mocker.patch(
        'src.processes.services.templates.ai.create_api_name',
        return_value='generated-name',
    )
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    inner = json.dumps({
        'name': 'Fenced',
        'description': '',
        'tasks': [
            {'name': 'Task 1', 'description': 'Do stuff'},
        ],
        'kickoff': {'fields': []},
    })
    text = f'```json\n{inner}\n```'

    # act
    result = service._parse_template_from_json(text=text)

    # assert
    assert result['name'] == 'Fenced'
    assert len(result['tasks']) == 1


def test_parse_tmpl_json__bad_json__raises():

    """Invalid JSON raises JSONDecodeError."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )

    # act
    with pytest.raises(json.JSONDecodeError):
        service._parse_template_from_json(
            text='not valid json {{{',
        )


def test_parse_tmpl_json__not_dict__raises():

    """Data is not a dict raises TypeError."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )

    # act
    with pytest.raises(TypeError):
        service._parse_template_from_json(
            text='[1, 2, 3]',
        )


def test_parse_tmpl_json__long_name__truncated(mocker):

    """Template name truncated to limit."""

    # arrange
    mocker.patch(
        'src.processes.services.templates.ai.create_api_name',
        return_value='generated-name',
    )
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    data = {
        'name': 'X' * 500,
        'description': '',
        'tasks': [],
        'kickoff': {'fields': []},
    }

    # act
    result = service._parse_template_from_json(
        text=json.dumps(data),
    )

    # assert
    assert len(result['name']) == TEMPLATE_NAME_LENGTH


def test_parse_tmpl_json__no_task_fields__omitted(mocker):

    """Task without fields omits fields key."""

    # arrange
    mocker.patch(
        'src.processes.services.templates.ai.create_api_name',
        return_value='generated-name',
    )
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    data = {
        'name': 'Test',
        'description': '',
        'tasks': [
            {'name': 'No fields task', 'description': 'desc'},
        ],
        'kickoff': {'fields': []},
    }

    # act
    result = service._parse_template_from_json(
        text=json.dumps(data),
    )

    # assert
    assert 'fields' not in result['tasks'][0]


def test_parse_tmpl_json__no_tasks__empty(mocker):

    """Empty tasks list returns empty tasks."""

    # arrange
    mocker.patch(
        'src.processes.services.templates.ai.create_api_name',
        return_value='generated-name',
    )
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    data = {
        'name': 'Empty',
        'description': '',
        'tasks': [],
        'kickoff': {'fields': []},
    }

    # act
    result = service._parse_template_from_json(
        text=json.dumps(data),
    )

    # assert
    assert result['tasks'] == []


def test_parse_tmpl_json__no_kickoff__empty(mocker):

    """Empty kickoff returns empty fields."""

    # arrange
    mocker.patch(
        'src.processes.services.templates.ai.create_api_name',
        return_value='generated-name',
    )
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    data = {
        'name': 'No Kickoff',
        'description': '',
        'tasks': [],
    }

    # act
    result = service._parse_template_from_json(
        text=json.dumps(data),
    )

    # assert
    assert result['kickoff'] == {'fields': []}


def test_parse_tmpl_json__multi_tasks__chained(mocker):

    """Multiple tasks chain conditions correctly."""

    # arrange
    call_count = 0
    names = [
        'pred-1', 'cond-1', 'rule-1', 'task-1',
        'pred-2', 'cond-2', 'rule-2', 'task-2',
        'pred-3', 'cond-3', 'rule-3', 'task-3',
    ]

    def fake_api_name(prefix=''):
        nonlocal call_count
        idx = min(call_count, len(names) - 1)
        result = names[idx]
        call_count += 1
        return result

    mocker.patch(
        'src.processes.services.templates.ai.create_api_name',
        side_effect=fake_api_name,
    )
    account = create_test_account()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    data = {
        'name': 'Multi',
        'description': '',
        'tasks': [
            {'name': 'Task A', 'description': 'A'},
            {'name': 'Task B', 'description': 'B'},
            {'name': 'Task C', 'description': 'C'},
        ],
        'kickoff': {'fields': []},
    }

    # act
    result = service._parse_template_from_json(
        text=json.dumps(data),
    )

    # assert
    assert len(result['tasks']) == 3
    assert result['tasks'][0]['number'] == 1
    assert result['tasks'][1]['number'] == 2
    assert result['tasks'][2]['number'] == 3

    # first task condition references kickoff (None)
    first_pred = (
        result['tasks'][0]['conditions'][0]
        ['rules'][0]['predicates'][0]
    )
    assert first_pred['field'] is None
    assert first_pred['field_type'] == PredicateType.KICKOFF

    # second task condition references first task api_name
    second_pred = (
        result['tasks'][1]['conditions'][0]
        ['rules'][0]['predicates'][0]
    )
    assert second_pred['field'] == result['tasks'][0]['api_name']
    assert second_pred['field_type'] == PredicateType.TASK

    # third task condition references second task api_name
    third_pred = (
        result['tasks'][2]['conditions'][0]
        ['rules'][0]['predicates'][0]
    )
    assert third_pred['field'] == result['tasks'][1]['api_name']
    assert third_pred['field_type'] == PredicateType.TASK
