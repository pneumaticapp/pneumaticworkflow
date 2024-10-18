import pytest
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.api_v2.services.templates.ai import (
    AnonOpenAiService
)
from pneumatic_backend.processes.api_v2.services.exceptions import (
    OpenAiTemplateStepsNotExist,
    OpenAiStepsPromptNotExist,
)
from pneumatic_backend.processes.messages import workflow as messages
from pneumatic_backend.ai.tests.fixtures import create_test_prompt


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
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.AnonOpenAiService._get_response',
        return_value=ai_response
    )
    ip = '168.01.01.8'
    user_agent = 'Some browser'

    service = AnonOpenAiService(
        ident=ip,
        user_agent=user_agent,
    )

    # act
    template_data = service.get_short_template_data(
        user_description=description
    )

    # assert
    get_response_mock.assert_called_once_with(
        user_description=description,
        prompt=prompt
    )

    assert template_data == {
        'name': description,
        'tasks': [
            {
                'number': 1,
                'name': '1. Hive inspection',
                'description': (
                    'Inspect the beehives to determine which ones '
                    'are ready for honey collection.'
                ),
            },
            {
                'number': 2,
                'name': '2. Smoke the hive',
                'description': (
                    'Use a smoker to calm the bees and '
                    'make them less aggressive.'
                )
            }
        ]
    }


def test_get_template_data__not_steps__raise_exception(mocker):

    # arrange
    description = 'My lovely business process'
    prompt = create_test_prompt()
    response_mock = 'Some response'
    get_response_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.AnonOpenAiService._get_response',
        return_value=response_mock
    )
    get_tasks_data_from_text_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.AnonOpenAiService._get_steps_data_from_text',
        return_value=[]
    )
    log_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
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
            user_description=description
        )

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


def test_get_template_data__not_prompt__raise_exception(mocker):

    # arrange
    description = 'My lovely business process'
    get_response_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.AnonOpenAiService._get_response',
    )
    get_tasks_data_from_text_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.AnonOpenAiService._get_steps_data_from_text',
    )
    log_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
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
            user_description=description
        )

    # assert
    get_response_mock.assert_not_called()
    get_tasks_data_from_text_mock.assert_not_called()
    log_mock.assert_not_called()
    assert ex.value.message == messages.MSG_PW_0046
