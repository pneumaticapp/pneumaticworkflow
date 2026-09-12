import pytest

from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_system_template,
)

pytestmark = pytest.mark.django_db


def test_fill__library_template__emit_template_library_fill(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    system_template = create_test_system_template(
        name='Clients requests processing',
        template={
            'name': 'Clients requests processing',
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'Checking data',
                },
            ],
        },
    )
    api_client.token_authenticate(
        owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.25',
    )
    library_template_opened_mock = mocker.patch(
        'src.processes.services.templates.template.'
        'AnalyticService.library_template_opened',
    )

    # act
    response = api_client.post(
        f'/templates/system/{system_template.id}/fill',
        HTTP_X_REQUEST_ID='audit-template-25',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TEMPLATE_LIBRARY_FILL
    assert event.category == EventCategory.ACTIVITY
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.SYSTEM_TEMPLATE,
        id=system_template.id,
    )
    assert event.payload == {'name': 'Clients requests processing'}
    assert event.ip == '10.10.0.25'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-template-25'
    library_template_opened_mock.assert_called_once_with(
        user=owner,
        sys_template=system_template,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )


def test_fill__inactive_library_template__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    system_template = create_test_system_template(
        name='Clients requests processing',
        is_active=False,
    )
    api_client.token_authenticate(owner)
    library_template_opened_mock = mocker.patch(
        'src.processes.services.templates.template.'
        'AnalyticService.library_template_opened',
    )

    # act
    response = api_client.post(
        f'/templates/system/{system_template.id}/fill',
    )

    # assert
    assert response.status_code == 404
    assert fake_stream.events == []
    library_template_opened_mock.assert_not_called()
