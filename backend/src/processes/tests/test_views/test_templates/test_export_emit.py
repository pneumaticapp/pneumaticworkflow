import pytest

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
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test_export__no_filters__emit_template_export(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    create_test_template(user=owner, is_active=True, tasks_count=1)
    api_client.token_authenticate(owner)
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    response = api_client.get('/templates/export')

    # assert
    assert response.status_code == 200
    emit_mock.assert_called_once_with(
        EventName.TEMPLATE_EXPORT,
        account_id=account.id,
        actor=Actor(
            type=ActorType.USER,
            id=owner.id,
            email=owner.email,
        ),
        event_object=EventObject(type=EventObjectType.TEMPLATE),
        payload={'filters': {'is_active': None, 'is_public': None}},
        workflow_id=None,
        task_id=None,
        request=mocker.ANY,
    )


def test_export__filters__emit_the_filters_of_the_request(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    create_test_template(user=owner, is_active=True, tasks_count=1)
    api_client.token_authenticate(owner)
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    response = api_client.get(
        '/templates/export?is_active=true&ordering=name',
    )

    # assert
    assert response.status_code == 200
    emit_mock.assert_called_once_with(
        EventName.TEMPLATE_EXPORT,
        account_id=account.id,
        actor=Actor(
            type=ActorType.USER,
            id=owner.id,
            email=owner.email,
        ),
        event_object=EventObject(type=EventObjectType.TEMPLATE),
        payload={
            'filters': {
                'is_active': True,
                'is_public': None,
                'ordering': 'name',
            },
        },
        workflow_id=None,
        task_id=None,
        request=mocker.ANY,
    )


def test_export__first_page__emit_template_export(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    create_test_template(user=owner, is_active=True, tasks_count=1)
    api_client.token_authenticate(owner)
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    response = api_client.get('/templates/export?limit=10&offset=0')

    # assert
    assert response.status_code == 200
    emit_mock.assert_called_once_with(
        EventName.TEMPLATE_EXPORT,
        account_id=account.id,
        actor=Actor(
            type=ActorType.USER,
            id=owner.id,
            email=owner.email,
        ),
        event_object=EventObject(type=EventObjectType.TEMPLATE),
        payload={
            'filters': {
                'is_active': None,
                'is_public': None,
                'limit': 10,
                'offset': 0,
            },
        },
        workflow_id=None,
        task_id=None,
        request=mocker.ANY,
    )


def test_export__next_page__no_event(
    mocker,
    api_client,
):

    """ One event per export: a page after the first one is the same
        export read further, not a new one. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    create_test_template(user=owner, is_active=True, tasks_count=1)
    api_client.token_authenticate(owner)
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    response = api_client.get('/templates/export?limit=10&offset=10')

    # assert
    assert response.status_code == 200
    emit_mock.assert_not_called()


def test_export__filters__event_keeps_request_context(
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    create_test_template(user=owner, is_active=True, tasks_count=1)
    api_client.token_authenticate(
        owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.16',
    )

    # act
    response = api_client.get(
        '/templates/export?is_active=true',
        HTTP_X_REQUEST_ID='audit-template-4',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TEMPLATE_EXPORT
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(type=EventObjectType.TEMPLATE)
    assert event.payload == {
        'filters': {'is_active': True, 'is_public': None},
    }
    assert event.ip == '10.10.0.16'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-template-4'
    assert event.pii == ('actor.email', 'ip', 'user_agent')
