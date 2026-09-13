import pytest

from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.services.exceptions import OpenAiServiceException
from src.processes.services.templates.ai import OpenAiService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_ai__template_generated__emit_template_ai_generate(
    mocker,
    api_client,
    fake_stream,
    settings,
):

    """ No template exists yet and the description is text the user
        typed: the event has no object id and no payload. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    description = 'Hire a new sales manager'
    open_ai_service_init_mock = mocker.patch.object(
        OpenAiService,
        attribute='__init__',
        return_value=None,
    )
    get_template_data_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.OpenAiService.get_template_data',
        return_value={'name': 'Hiring'},
    )
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'AI': True}
    api_client.token_authenticate(
        owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.22',
    )

    # act
    response = api_client.post(
        path='/templates/ai',
        data={'description': description},
        HTTP_X_REQUEST_ID='audit-template-22',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TEMPLATE_AI_GENERATE
    assert event.category == EventCategory.ACTIVITY
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.TEMPLATE,
        id=None,
    )
    assert event.payload == {}
    assert event.ip == '10.10.0.22'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-template-22'
    assert event.pii == ('actor.email', 'ip', 'user_agent')
    open_ai_service_init_mock.assert_called_once_with(
        ident=owner.id,
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    get_template_data_mock.assert_called_once_with(
        user_description=description,
    )


def test_ai__service_exception__no_event(
    mocker,
    api_client,
    fake_stream,
    settings,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    description = 'Hire a new sales manager'
    open_ai_service_init_mock = mocker.patch.object(
        OpenAiService,
        attribute='__init__',
        return_value=None,
    )
    error_message = 'OpenAI is not available'
    get_template_data_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.OpenAiService.get_template_data',
        side_effect=OpenAiServiceException(message=error_message),
    )
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'AI': True}
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        path='/templates/ai',
        data={'description': description},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == error_message
    assert response.data['details'] == {}
    assert fake_stream.events == []
    open_ai_service_init_mock.assert_called_once_with(
        ident=owner.id,
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    get_template_data_mock.assert_called_once_with(
        user_description=description,
    )


def test_ai__description_null__no_event(
    mocker,
    api_client,
    fake_stream,
    settings,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    open_ai_service_init_mock = mocker.patch.object(
        OpenAiService,
        attribute='__init__',
        return_value=None,
    )
    get_template_data_mock = mocker.patch(
        'src.processes.services.templates.'
        'ai.OpenAiService.get_template_data',
    )
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'AI': True}
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        path='/templates/ai',
        data={'description': None},
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be null.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'description'
    assert response.data['details']['reason'] == message
    assert fake_stream.events == []
    open_ai_service_init_mock.assert_not_called()
    get_template_data_mock.assert_not_called()
