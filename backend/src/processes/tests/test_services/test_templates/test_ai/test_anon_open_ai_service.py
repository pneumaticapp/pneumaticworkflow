import json
import pytest
from django.contrib.auth import get_user_model

from src.ai.enums import OpenAIPromptTarget
from src.ai.tests.fixtures import create_test_prompt
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
