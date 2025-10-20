import pytest
from django.contrib.auth import get_user_model

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


def test_get_short_template_data__ok(mocker):

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


def test_get_template_data__not_steps__raise_exception(mocker):

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


def test_get_template_data__not_prompt__raise_exception(mocker):

    # arrange
    description = 'My lovely business process'
    get_response_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.AnonOpenAiService._get_response',
    )
    get_tasks_data_from_text_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.AnonOpenAiService._get_steps_data_from_text',
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
    with pytest.raises(OpenAiStepsPromptNotExist) as ex:
        service.get_short_template_data(
            user_description=description,
        )

    # assert
    get_response_mock.assert_not_called()
    get_tasks_data_from_text_mock.assert_not_called()
    log_mock.assert_not_called()
    assert ex.value.message == messages.MSG_PW_0046
