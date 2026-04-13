import json

import pytest
from django.contrib.auth import get_user_model

from src.ai.enums import (
    OpenAIPromptTarget,
    OpenAIRole,
)
from src.ai.tests.fixtures import create_test_prompt
from src.authentication.enums import AuthTokenType
from src.processes.enums import PerformerType
from src.processes.services.exceptions import (
    OpenAiLimitTemplateGenerations,
    OpenAiServiceUnavailable,
    OpenAiTemplateStepsNotExist,
)
from src.processes.services.templates.ai import (
    OpenAiService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_user,
)
from src.utils.logging import SentryLogLevel

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


# === _get_response (legacy text-based) ===


def test_get_response__no_api_key__raise_exception(mocker):

    # arrange
    description = 'some description'
    prompt = create_test_prompt()
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

    # act
    with pytest.raises(OpenAiServiceUnavailable):
        service._get_response(
            user_description=description,
            prompt=prompt,
        )


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


# === OpenAiService._log_exception (3.9) ===


def test_oa_log_exception__ok__calls_sentry(mocker):

    """Calls capture_sentry_message with data"""

    # arrange
    user = create_test_owner()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    prompt = create_test_prompt()
    description = 'some description'
    exception = Exception('some error')
    sentry_mock = mocker.patch(
        'src.processes.services.templates.ai.'
        'capture_sentry_message',
    )

    # act
    service._log_exception(
        prompt=prompt,
        user_description=description,
        ex=exception,
    )

    # assert
    sentry_mock.assert_called_once_with(
        message=(
            f'Error AI generating template '
            f'({user.account.id})'
        ),
        data={
            'user_id': user.id,
            'user_email': user.email,
            'account_id': user.account.id,
            'ex': {
                'error': str(exception),
            },
            'request': {
                'user_description': description,
                'prompt': prompt.as_dict(),
            },
        },
        level=SentryLogLevel.INFO,
    )


# === OpenAiService._log (3.10) ===


def test_oa_log__ok__calls_sentry(mocker):

    """Calls capture_sentry_message with data"""

    # arrange
    user = create_test_owner()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    prompt = create_test_prompt()
    description = 'some description'
    message = 'some message'
    response_text = 'some response'
    sentry_mock = mocker.patch(
        'src.processes.services.templates.ai.'
        'capture_sentry_message',
    )

    # act
    service._log(
        prompt=prompt,
        user_description=description,
        message=message,
        response_text=response_text,
    )

    # assert
    sentry_mock.assert_called_once_with(
        message=(
            f'Error AI generating template '
            f'({user.account.id})'
        ),
        data={
            'user_id': user.id,
            'user_email': user.email,
            'account_id': user.account.id,
            'message': message,
            'response': {
                'text': response_text,
            },
            'request': {
                'user_description': description,
                'prompt': prompt.as_dict(),
            },
        },
        level=SentryLogLevel.INFO,
    )


def test_oa_log__no_resp_text__ok(mocker):

    """response_text=None included in data"""

    # arrange
    user = create_test_owner()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    prompt = create_test_prompt()
    description = 'some description'
    message = 'some message'
    sentry_mock = mocker.patch(
        'src.processes.services.templates.ai.'
        'capture_sentry_message',
    )

    # act
    service._log(
        prompt=prompt,
        user_description=description,
        message=message,
    )

    # assert
    sentry_mock.assert_called_once_with(
        message=(
            f'Error AI generating template '
            f'({user.account.id})'
        ),
        data={
            'user_id': user.id,
            'user_email': user.email,
            'account_id': user.account.id,
            'message': message,
            'response': {
                'text': None,
            },
            'request': {
                'user_description': description,
                'prompt': prompt.as_dict(),
            },
        },
        level=SentryLogLevel.INFO,
    )


# === OpenAiService._get_step_data_from_text (3.11) ===


def test_oa_get_step_data__ok__has_performer(mocker):

    """Returns dict with performer and condition"""

    # arrange
    user = create_test_owner()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    api_name = 'task-abc-123'
    mocker.patch(
        'src.processes.services.templates.ai.'
        'create_api_name',
        return_value=api_name,
    )

    # act
    result = service._get_step_data_from_text(
        number=1,
        name='Step name',
        description='Step desc',
        prev_task_api_name=None,
    )

    # assert
    assert result['number'] == 1
    assert result['name'] == 'Step name'
    assert result['api_name'] == api_name
    assert result['description'] == 'Step desc'
    assert result['raw_performers'] == [
        {
            'type': PerformerType.USER,
            'source_id': user.id,
            'label': user.name,
        },
    ]
    assert len(result['conditions']) == 1


# === _post_template_generation_actions (3.13) ===


def test_post_tmpl_gen_actions__ok__increments(mocker):

    """Calls inc_template_generations_count"""

    # arrange
    user = create_test_owner()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    mocker.patch.object(
        target=(
            __import__(
                'src.accounts.services.account',
                fromlist=['AccountService'],
            ).AccountService
        ),
        attribute='__init__',
        return_value=None,
    )
    inc_mock = mocker.patch(
        'src.processes.services.templates.ai.'
        'AccountService.inc_template_generations_count',
    )

    # act
    service._post_template_generation_actions(
        user_description='some description',
    )

    # assert
    inc_mock.assert_called_once_with()


# === _get_template_data (3.15) ===


def test_get_tmpl_data__limit__raises(mocker):

    """Limit exceeded raises exception"""

    # arrange
    account = create_test_account()
    account.max_ai_templates_generations = 0
    account.ai_templates_generations = 1
    account.save()
    user = create_test_owner(account=account)
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )

    # act
    with pytest.raises(OpenAiLimitTemplateGenerations):
        service._get_template_data(
            user_description='some description',
        )


def test_get_tmpl_data__tmpl_prompt__ok(mocker):

    """Template prompt exists, JSON path OK"""

    # arrange
    user = create_test_owner()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    create_test_prompt(
        target=OpenAIPromptTarget.GET_TEMPLATE,
    )
    response_text = json.dumps({
        'name': 'Test',
        'description': 'desc',
        'tasks': [
            {
                'name': 'Task 1',
                'description': 'do something',
            },
        ],
        'kickoff': {'fields': []},
    })
    mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._get_json_response',
        return_value=response_text,
    )
    filled_data = {'name': 'Test', 'tasks': []}
    mocker.patch.object(
        target=(
            __import__(
                'src.processes.services.templates.template',
                fromlist=['TemplateService'],
            ).TemplateService
        ),
        attribute='__init__',
        return_value=None,
    )
    fill_mock = mocker.patch(
        'src.processes.services.templates.ai.'
        'TemplateService.fill_template_data',
        return_value=filled_data,
    )
    post_mock = mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._post_template_generation_actions',
    )

    # act
    result = service._get_template_data(
        user_description='some description',
    )

    # assert
    assert result == filled_data
    fill_mock.assert_called_once()
    post_mock.assert_called_once_with(
        'some description',
    )


def test_get_tmpl_data__no_prompts__defaults(mocker):

    """No prompts, JSON path with defaults"""

    # arrange
    user = create_test_owner()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    response_text = json.dumps({
        'name': 'Test',
        'description': 'desc',
        'tasks': [
            {
                'name': 'Task 1',
                'description': 'do something',
            },
        ],
        'kickoff': {'fields': []},
    })
    get_json_mock = mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._get_json_response',
        return_value=response_text,
    )
    filled_data = {'name': 'Test', 'tasks': []}
    mocker.patch.object(
        target=(
            __import__(
                'src.processes.services.templates.template',
                fromlist=['TemplateService'],
            ).TemplateService
        ),
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.processes.services.templates.ai.'
        'TemplateService.fill_template_data',
        return_value=filled_data,
    )
    mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._post_template_generation_actions',
    )

    # act
    service._get_template_data(
        user_description='some description',
    )

    # assert
    get_json_mock.assert_called_once_with(
        user_description='some description',
        prompt=None,
    )


def test_get_tmpl_data__json_err_prompt__logs(mocker):

    """JSON parse error with prompt logs + raises"""

    # arrange
    user = create_test_owner()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    template_prompt = create_test_prompt(
        target=OpenAIPromptTarget.GET_TEMPLATE,
    )
    mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._get_json_response',
        return_value='not valid json',
    )
    log_mock = mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._log',
    )

    # act
    with pytest.raises(OpenAiTemplateStepsNotExist):
        service._get_template_data(
            user_description='some description',
        )

    # assert
    log_mock.assert_called_once_with(
        prompt=template_prompt,
        user_description='some description',
        message='Failed to parse JSON template response',
        response_text='not valid json',
    )


def test_get_tmpl_data__json_err_no_prompt__raises(mocker):

    """JSON parse error no prompt raises no log"""

    # arrange
    user = create_test_owner()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._get_json_response',
        return_value='not valid json',
    )
    log_mock = mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._log',
    )

    # act
    with pytest.raises(OpenAiTemplateStepsNotExist):
        service._get_template_data(
            user_description='some description',
        )

    # assert
    assert log_mock.call_count == 0


def test_get_tmpl_data__no_tasks_prompt__logs(mocker):

    """Empty tasks with prompt logs + raises"""

    # arrange
    user = create_test_owner()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    template_prompt = create_test_prompt(
        target=OpenAIPromptTarget.GET_TEMPLATE,
    )
    response_text = json.dumps({
        'name': 'Test',
        'tasks': [],
        'kickoff': {'fields': []},
    })
    mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._get_json_response',
        return_value=response_text,
    )
    log_mock = mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._log',
    )

    # act
    with pytest.raises(OpenAiTemplateStepsNotExist):
        service._get_template_data(
            user_description='some description',
        )

    # assert
    log_mock.assert_called_once_with(
        prompt=template_prompt,
        user_description='some description',
        message='Template tasks not found',
        response_text=response_text,
    )


def test_get_tmpl_data__no_tasks_no_prompt__raises(mocker):

    """Empty tasks no prompt raises no log"""

    # arrange
    user = create_test_owner()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    response_text = json.dumps({
        'name': 'Test',
        'tasks': [],
        'kickoff': {'fields': []},
    })
    mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._get_json_response',
        return_value=response_text,
    )
    log_mock = mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._log',
    )

    # act
    with pytest.raises(OpenAiTemplateStepsNotExist):
        service._get_template_data(
            user_description='some description',
        )

    # assert
    assert log_mock.call_count == 0


def test_get_tmpl_data__steps_prompt__ok(mocker):

    """Steps prompt path OK"""

    # arrange
    user = create_test_owner()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    create_test_prompt(
        target=OpenAIPromptTarget.GET_STEPS,
    )
    tasks_data = [
        {
            'number': 1,
            'name': 'Step 1',
            'api_name': 'task-1',
            'description': 'desc 1',
        },
    ]
    mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._get_response',
        return_value='Step 1|desc 1',
    )
    mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._get_steps_data_from_text',
        return_value=tasks_data,
    )
    filled_data = {'name': 'Test', 'tasks': tasks_data}
    mocker.patch.object(
        target=(
            __import__(
                'src.processes.services.templates.template',
                fromlist=['TemplateService'],
            ).TemplateService
        ),
        attribute='__init__',
        return_value=None,
    )
    fill_mock = mocker.patch(
        'src.processes.services.templates.ai.'
        'TemplateService.fill_template_data',
        return_value=filled_data,
    )
    mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._post_template_generation_actions',
    )

    # act
    result = service._get_template_data(
        user_description='some description',
    )

    # assert
    assert result == filled_data
    fill_mock.assert_called_once()


def test_get_tmpl_data__steps_empty__logs(mocker):

    """Steps prompt empty steps logs + raises"""

    # arrange
    user = create_test_owner()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    steps_prompt = create_test_prompt(
        target=OpenAIPromptTarget.GET_STEPS,
    )
    mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._get_response',
        return_value='no steps here',
    )
    mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._get_steps_data_from_text',
        return_value=[],
    )
    log_mock = mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._log',
    )

    # act
    with pytest.raises(OpenAiTemplateStepsNotExist):
        service._get_template_data(
            user_description='some description',
        )

    # assert
    log_mock.assert_called_once_with(
        prompt=steps_prompt,
        user_description='some description',
        message='Template steps not found',
        response_text='no steps here',
    )


def test_get_tmpl_data__no_steps_prompt__raises(mocker):

    """No active prompts takes JSON path, empty tasks raises"""

    # arrange
    user = create_test_owner()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    response_text = json.dumps({
        'name': 'Test',
        'tasks': [],
        'kickoff': {'fields': []},
    })
    mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._get_json_response',
        return_value=response_text,
    )

    # act
    with pytest.raises(OpenAiTemplateStepsNotExist):
        service._get_template_data(
            user_description='some description',
        )


def test_get_tmpl_data__empty_name__defaults(mocker):

    """Empty name defaults to user_description"""

    # arrange
    user = create_test_owner()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    response_text = json.dumps({
        'name': '',
        'description': 'desc',
        'tasks': [
            {
                'name': 'Task 1',
                'description': 'do something',
            },
        ],
        'kickoff': {'fields': []},
    })
    mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._get_json_response',
        return_value=response_text,
    )
    mocker.patch.object(
        target=(
            __import__(
                'src.processes.services.templates.template',
                fromlist=['TemplateService'],
            ).TemplateService
        ),
        attribute='__init__',
        return_value=None,
    )
    captured = {}

    def capture_fill(data):
        captured['data'] = data
        return {'name': 'desc', 'tasks': []}

    mocker.patch(
        'src.processes.services.templates.ai.'
        'TemplateService.fill_template_data',
        side_effect=capture_fill,
    )
    mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._post_template_generation_actions',
    )
    description = 'my workflow description'

    # act
    service._get_template_data(
        user_description=description,
    )

    # assert
    assert captured['data']['name'] == description[:200]


def test_get_tmpl_data__ok__fills_and_posts(mocker):

    """Calls fill_template_data and post actions"""

    # arrange
    user = create_test_owner()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    response_text = json.dumps({
        'name': 'Test',
        'description': 'desc',
        'tasks': [
            {
                'name': 'Task 1',
                'description': 'do something',
            },
        ],
        'kickoff': {'fields': []},
    })
    mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._get_json_response',
        return_value=response_text,
    )
    filled_data = {'name': 'Test', 'tasks': []}
    mocker.patch.object(
        target=(
            __import__(
                'src.processes.services.templates.template',
                fromlist=['TemplateService'],
            ).TemplateService
        ),
        attribute='__init__',
        return_value=None,
    )
    fill_mock = mocker.patch(
        'src.processes.services.templates.ai.'
        'TemplateService.fill_template_data',
        return_value=filled_data,
    )
    post_mock = mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._post_template_generation_actions',
    )

    # act
    result = service._get_template_data(
        user_description='some description',
    )

    # assert
    assert result == filled_data
    fill_mock.assert_called_once()
    post_mock.assert_called_once_with(
        'some description',
    )


# === get_template_data (3.16) ===


def test_get_template_data__ok__tracks_analytics(mocker):

    """Success returns data and tracks analytics"""

    # arrange
    user = create_test_owner()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    template_data = {'name': 'Test', 'tasks': []}
    mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._get_template_data',
        return_value=template_data,
    )
    analytics_mock = mocker.patch(
        'src.processes.services.templates.ai.'
        'AnalyticService.template_generation_init',
    )

    # act
    result = service.get_template_data(
        user_description='some description',
    )

    # assert
    assert result == template_data
    analytics_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        description='some description',
        success=True,
    )


def test_get_template_data__err__tracks_fail(mocker):

    """Exception tracks analytics with success=False"""

    # arrange
    user = create_test_owner()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._get_template_data',
        side_effect=OpenAiServiceUnavailable(),
    )
    analytics_mock = mocker.patch(
        'src.processes.services.templates.ai.'
        'AnalyticService.template_generation_init',
    )

    # act
    with pytest.raises(OpenAiServiceUnavailable):
        service.get_template_data(
            user_description='some description',
        )

    # assert
    analytics_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        description='some description',
        success=False,
    )


def test_get_template_data__err__reraises(mocker):

    """Exception re-raised after analytics"""

    # arrange
    user = create_test_owner()
    service = OpenAiService(
        ident=user.id,
        user=user,
        auth_type=AuthTokenType.USER,
    )
    mocker.patch(
        'src.processes.services.templates.ai.'
        'OpenAiService._get_template_data',
        side_effect=OpenAiTemplateStepsNotExist(),
    )
    mocker.patch(
        'src.processes.services.templates.ai.'
        'AnalyticService.template_generation_init',
    )

    # act
    with pytest.raises(OpenAiTemplateStepsNotExist):
        service.get_template_data(
            user_description='some description',
        )
