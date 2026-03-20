import json
import pytest
from django.contrib.auth import get_user_model

from src.ai.enums import OpenAIPromptTarget
from src.ai.tests.fixtures import create_test_prompt
from src.processes.consts import TEMPLATE_NAME_LENGTH
from src.processes.enums import (
    ConditionAction,
    PredicateOperator,
    PredicateType,
)
from src.processes.messages import workflow as messages
from src.processes.services.exceptions import (
    OpenAiStepsPromptNotExist,
    OpenAiTemplateStepsNotExist,
)
from src.processes.services.templates.ai import (
    AnonOpenAiService,
)
from src.utils.logging import SentryLogLevel

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


# === Legacy text path ===


def test_get_short_template_data__legacy_text_path__ok(mocker):

    # arrange
    description = 'My lovely business process'
    ai_response = (
        '1. Hive inspection|Inspect the beehives to determine which ones '
        'are ready for honey collection.\n'
        '2. Smoke the hive | Use a smoker to calm the bees and make them '
        'less aggressive.'
    )
    prompt = create_test_prompt()
    get_response_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.AnonOpenAiService._get_response',
        return_value=ai_response,
    )
    ip = '168.01.01.8'
    user_agent = 'Some browser'

    service = AnonOpenAiService(
        ident=ip,
        user_agent=user_agent,
    )

    # act
    template_data = service.get_short_template_data(
        user_description=description,
    )

    # assert
    get_response_mock.assert_called_once_with(
        user_description=description,
        prompt=prompt,
    )
    assert template_data['name'] == description
    task_1_data = template_data['tasks'][0]
    assert task_1_data['number'] == 1
    assert task_1_data['name'] == '1. Hive inspection'
    assert task_1_data['api_name']
    assert task_1_data['description'] == (
        'Inspect the beehives to determine which ones '
        'are ready for honey collection.'
    )
    assert len(task_1_data['conditions']) == 1
    task_1_condition = task_1_data['conditions'][0]
    assert task_1_condition['order'] == 1
    assert task_1_condition['action'] == ConditionAction.START_TASK
    assert task_1_condition['api_name']
    assert len(task_1_condition['rules']) == 1
    assert task_1_condition['rules'][0]['api_name']
    assert len(task_1_condition['rules'][0]['predicates']) == 1
    task_1_predicate = task_1_condition['rules'][0]['predicates'][0]
    assert task_1_predicate['field_type'] == PredicateType.KICKOFF
    assert task_1_predicate['operator'] == PredicateOperator.COMPLETED
    assert task_1_predicate['api_name']
    assert task_1_predicate['field'] is None
    assert task_1_predicate['value'] is None

    task_2_data = template_data['tasks'][1]
    assert task_2_data['number'] == 2
    assert task_2_data['name'] == '2. Smoke the hive'
    assert task_2_data['api_name']
    assert task_2_data['description'] == (
        'Use a smoker to calm the bees and '
        'make them less aggressive.'
    )
    assert len(task_2_data['conditions']) == 1
    task_2_condition = task_2_data['conditions'][0]
    assert task_2_condition['order'] == 1
    assert task_2_condition['action'] == ConditionAction.START_TASK
    assert task_2_condition['api_name']
    assert len(task_2_condition['rules']) == 1
    assert task_2_condition['rules'][0]['api_name']
    assert len(task_2_condition['rules'][0]['predicates']) == 1
    task_2_predicate = task_2_condition['rules'][0]['predicates'][0]
    assert task_2_predicate['field_type'] == PredicateType.TASK
    assert task_2_predicate['operator'] == PredicateOperator.COMPLETED
    assert task_2_predicate['api_name']
    assert task_2_predicate['field'] == task_1_data['api_name']
    assert task_2_predicate['value'] is None


# === JSON path with GET_TEMPLATE prompt ===


def test_get_short_template_data__json_path__ok(mocker):

    # arrange
    description = 'My lovely business process'
    create_test_prompt(target=OpenAIPromptTarget.GET_TEMPLATE)
    ai_json = json.dumps({
        'name': 'My Workflow',
        'description': 'A workflow',
        'kickoff': {
            'fields': [
                {
                    'order': 1,
                    'name': 'Input Field',
                    'type': 'string',
                    'is_required': True,
                },
            ],
        },
        'tasks': [
            {
                'number': 1,
                'name': 'First task',
                'description': 'Do the first thing',
                'fields': [
                    {
                        'order': 1,
                        'name': 'Output',
                        'type': 'text',
                    },
                ],
            },
            {
                'number': 2,
                'name': 'Second task',
                'description': 'Do the second thing',
            },
        ],
    })
    get_json_response_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.AnonOpenAiService._get_json_response',
        return_value=ai_json,
    )
    ip = '168.01.01.8'
    user_agent = 'Some browser'

    service = AnonOpenAiService(
        ident=ip,
        user_agent=user_agent,
    )

    # act
    data = service.get_short_template_data(
        user_description=description,
    )

    # assert
    get_json_response_mock.assert_called_once()
    assert data['name'] == 'My Workflow'
    assert len(data['tasks']) == 2
    assert data['tasks'][0]['name'] == 'First task'
    assert data['tasks'][0]['api_name']
    assert 'fields' not in data['tasks'][0]
    assert data['tasks'][1]['name'] == 'Second task'


# === JSON path with no prompt (default instruction) ===


def test_get_short_template_data__no_prompt__uses_default(mocker):

    # arrange
    description = 'My lovely business process'
    ai_json = json.dumps({
        'name': 'Generated',
        'tasks': [
            {
                'number': 1,
                'name': 'Step one',
                'description': 'First step',
            },
        ],
    })
    get_json_response_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.AnonOpenAiService._get_json_response',
        return_value=ai_json,
    )
    ip = '168.01.01.8'
    user_agent = 'Some browser'

    service = AnonOpenAiService(
        ident=ip,
        user_agent=user_agent,
    )

    # act
    data = service.get_short_template_data(
        user_description=description,
    )

    # assert
    get_json_response_mock.assert_called_once_with(
        user_description=description,
        prompt=None,
    )
    assert data['name'] == 'Generated'
    assert len(data['tasks']) == 1


# === Error cases ===


def test_get_short_template_data__legacy_not_steps__raise_exception(mocker):

    # arrange
    description = 'My lovely business process'
    prompt = create_test_prompt()
    response_mock = 'Some response'
    get_response_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.AnonOpenAiService._get_response',
        return_value=response_mock,
    )
    get_tasks_data_from_text_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.AnonOpenAiService._get_steps_data_from_text',
        return_value=[],
    )
    log_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.AnonOpenAiService._log',
    )
    ip = '168.01.01.8'
    user_agent = 'Some browser'

    service = AnonOpenAiService(
        ident=ip,
        user_agent=user_agent,
    )

    # act
    with pytest.raises(OpenAiTemplateStepsNotExist) as ex:
        service.get_short_template_data(
            user_description=description,
        )

    # assert
    get_response_mock.assert_called_once_with(
        user_description=description,
        prompt=prompt,
    )
    get_tasks_data_from_text_mock.assert_called_once_with(response_mock)
    assert ex.value.message == messages.MSG_PW_0045
    log_mock.assert_called_once_with(
        message='Template steps not found',
        user_description=description,
        prompt=prompt,
        response_text=response_mock,
    )


def test_get_short_template_data__json_parse_error__raise_exception(mocker):

    # arrange
    description = 'My lovely business process'
    mocker.patch(
        'src.processes.services.templates.'
        'ai.AnonOpenAiService._get_json_response',
        return_value='broken json {{',
    )
    ip = '168.01.01.8'
    user_agent = 'Some browser'

    service = AnonOpenAiService(
        ident=ip,
        user_agent=user_agent,
    )

    # act
    with pytest.raises(OpenAiTemplateStepsNotExist) as ex:
        service.get_short_template_data(
            user_description=description,
        )

    # assert
    assert ex.value.message == messages.MSG_PW_0045


# === AnonOpenAiService._log_exception (3.17) ===


def test_anon_log_exception__ok__calls_sentry(mocker):

    """

    Calls capture_sentry_message with ident

    """

    # arrange
    ip = '168.01.01.8'
    user_agent = 'Some browser'
    service = AnonOpenAiService(
        ident=ip,
        user_agent=user_agent,
    )
    prompt = create_test_prompt()
    description = 'some description'
    ex = Exception('some error')
    sentry_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.capture_sentry_message',
    )

    # act
    service._log_exception(
        prompt=prompt,
        user_description=description,
        ex=ex,
    )

    # assert
    sentry_mock.assert_called_once_with(
        message=(
            f'Error AI gen template from landing ({ip})'
        ),
        data={
            'ident': ip,
            'user-agent': user_agent,
            'ex': {
                'error': str(ex),
            },
            'request': {
                'user_description': description,
                'prompt': prompt.as_dict(),
            },
        },
        level=SentryLogLevel.INFO,
    )


# === AnonOpenAiService._log (3.18) ===


def test_anon_log__ok__calls_sentry(mocker):

    """

    Calls capture_sentry_message with ident

    """

    # arrange
    ip = '168.01.01.8'
    user_agent = 'Some browser'
    service = AnonOpenAiService(
        ident=ip,
        user_agent=user_agent,
    )
    prompt = create_test_prompt()
    description = 'some description'
    message = 'some message'
    response_text = 'some response'
    sentry_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.capture_sentry_message',
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
            f'Error AI gen template from landing ({ip})'
        ),
        data={
            'ident': ip,
            'user-agent': user_agent,
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


# === AnonOpenAiService._get_step_data_from_text (3.19) ===


def test_anon_get_step_data__ok__no_performer(mocker):

    """

    Returns dict without performers

    """

    # arrange
    ip = '168.01.01.8'
    user_agent = 'Some browser'
    service = AnonOpenAiService(
        ident=ip,
        user_agent=user_agent,
    )
    api_name = 'task-123'
    create_api_name_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.create_api_name',
        return_value=api_name,
    )

    # act
    result = service._get_step_data_from_text(
        number=1,
        name='Task one',
        description='Do something',
        prev_task_api_name=None,
    )

    # assert
    assert result['number'] == 1
    assert result['name'] == 'Task one'
    assert result['api_name'] == api_name
    assert result['description'] == 'Do something'
    assert 'raw_performers' not in result
    assert len(result['conditions']) == 1
    assert create_api_name_mock.call_count == 4


# === get_short_template_data (3.20) — new tests ===


def test_get_short_tmpl__no_tasks_prompt__logs(mocker):

    """

    JSON path empty tasks with prompt logs

    """

    # arrange
    description = 'My lovely business process'
    prompt = create_test_prompt(
        target=OpenAIPromptTarget.GET_TEMPLATE,
    )
    ai_json = json.dumps({
        'name': 'My Workflow',
        'tasks': [],
    })
    response_text = ai_json
    mocker.patch(
        'src.processes.services.templates.'
        'ai.AnonOpenAiService._get_json_response',
        return_value=response_text,
    )
    log_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.AnonOpenAiService._log',
    )
    ip = '168.01.01.8'
    user_agent = 'Some browser'
    service = AnonOpenAiService(
        ident=ip,
        user_agent=user_agent,
    )

    # act
    with pytest.raises(OpenAiTemplateStepsNotExist):
        service.get_short_template_data(
            user_description=description,
        )

    # assert
    log_mock.assert_called_once_with(
        prompt=prompt,
        user_description=description,
        message='Template tasks not found',
        response_text=response_text,
    )


def test_get_short_tmpl__no_tasks_no_prompt__raises(mocker):

    """

    JSON path empty tasks no prompt raises

    """

    # arrange
    description = 'My lovely business process'
    ai_json = json.dumps({
        'name': 'My Workflow',
        'tasks': [],
    })
    mocker.patch(
        'src.processes.services.templates.'
        'ai.AnonOpenAiService._get_json_response',
        return_value=ai_json,
    )
    log_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.AnonOpenAiService._log',
    )
    ip = '168.01.01.8'
    user_agent = 'Some browser'
    service = AnonOpenAiService(
        ident=ip,
        user_agent=user_agent,
    )

    # act
    with pytest.raises(OpenAiTemplateStepsNotExist):
        service.get_short_template_data(
            user_description=description,
        )

    # assert
    assert log_mock.call_count == 0


def test_get_short_tmpl__no_steps_prompt__raises(mocker):

    """

    Steps prompt not exist raises

    """

    # arrange
    description = 'My lovely business process'

    # create steps prompt with active messages so the
    # first condition routes to else (steps) branch
    create_test_prompt()
    ip = '168.01.01.8'
    user_agent = 'Some browser'
    service = AnonOpenAiService(
        ident=ip,
        user_agent=user_agent,
    )

    # mock _get_response to raise the exception
    # simulating the defensive guard behavior
    mocker.patch(
        'src.processes.services.templates.'
        'ai.AnonOpenAiService._get_response',
        side_effect=OpenAiStepsPromptNotExist(),
    )

    # act
    with pytest.raises(OpenAiStepsPromptNotExist):
        service.get_short_template_data(
            user_description=description,
        )


def test_get_short_tmpl__empty_name__defaults(mocker):

    """

    Empty name defaults to user_description

    """

    # arrange
    description = 'My lovely business process'
    ai_json = json.dumps({
        'name': '',
        'tasks': [
            {
                'number': 1,
                'name': 'Step one',
                'description': 'First step',
            },
        ],
    })
    mocker.patch(
        'src.processes.services.templates.'
        'ai.AnonOpenAiService._get_json_response',
        return_value=ai_json,
    )
    ip = '168.01.01.8'
    user_agent = 'Some browser'
    service = AnonOpenAiService(
        ident=ip,
        user_agent=user_agent,
    )

    # act
    data = service.get_short_template_data(
        user_description=description,
    )

    # assert
    assert data['name'] == description[:TEMPLATE_NAME_LENGTH]


def test_get_short_tmpl__tasks__minimal_fields(mocker):

    """

    Tasks stripped to minimal fields

    """

    # arrange
    description = 'My lovely business process'
    create_test_prompt(
        target=OpenAIPromptTarget.GET_TEMPLATE,
    )
    ai_json = json.dumps({
        'name': 'Workflow',
        'tasks': [
            {
                'number': 1,
                'name': 'Task A',
                'description': 'Do A',
                'fields': [
                    {
                        'order': 1,
                        'name': 'Field',
                        'type': 'string',
                    },
                ],
            },
            {
                'number': 2,
                'name': 'Task B',
                'description': 'Do B',
            },
        ],
    })
    mocker.patch(
        'src.processes.services.templates.'
        'ai.AnonOpenAiService._get_json_response',
        return_value=ai_json,
    )
    ip = '168.01.01.8'
    user_agent = 'Some browser'
    service = AnonOpenAiService(
        ident=ip,
        user_agent=user_agent,
    )

    # act
    data = service.get_short_template_data(
        user_description=description,
    )

    # assert
    assert len(data['tasks']) == 2
    task_1 = data['tasks'][0]
    assert set(task_1.keys()) == {
        'number', 'name', 'api_name',
        'description', 'conditions',
    }
    assert task_1['number'] == 1
    assert task_1['name'] == 'Task A'
    assert task_1['description'] == 'Do A'
    assert task_1['api_name']
    assert len(task_1['conditions']) == 1

    task_2 = data['tasks'][1]
    assert set(task_2.keys()) == {
        'number', 'name', 'api_name',
        'description', 'conditions',
    }
    assert task_2['number'] == 2
    assert task_2['name'] == 'Task B'
