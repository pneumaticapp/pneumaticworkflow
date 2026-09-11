import pytest

from src.accounts.services.user import UserService
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_create__admin_adds_user__emit_user_create(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    created = create_test_not_admin(account=account, email='new@test.test')
    create_mock = mocker.patch.object(
        UserService,
        attribute='create',
        return_value=created,
    )
    api_client.token_authenticate(
        owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.6',
    )

    # act
    response = api_client.post(
        '/accounts/users',
        {'email': 'new@test.test', 'is_admin': False},
        HTTP_X_REQUEST_ID='audit-user-create-1',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_CREATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=created.id,
    )
    assert event.payload == {
        'target_email': 'new@test.test',
        'is_admin': False,
    }
    assert event.ip == '10.10.0.6'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-user-create-1'
    assert event.pii == (
        'actor.email',
        'ip',
        'user_agent',
        'payload.target_email',
    )
    create_mock.assert_called_once_with(
        account=account,
        email='new@test.test',
        is_admin=False,
    )


def test_create__not_admin__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    create_mock = mocker.patch.object(UserService, attribute='create')
    api_client.token_authenticate(user)

    # act
    response = api_client.post('/accounts/users', {'email': 'x@test.test'})

    # assert
    assert response.status_code == 403
    assert fake_stream.events == []
    create_mock.assert_not_called()
