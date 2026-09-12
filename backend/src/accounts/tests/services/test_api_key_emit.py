import pytest

from src.accounts.services.api_key import APIKeyService
from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    ActorType,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject, to_json
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_api_key,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_create__api_key__emit_api_key_create(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    emit_mock = mocker.patch('src.logs.events.mixins.emit')
    service = APIKeyService(user=owner, auth_type=AuthTokenType.USER)

    # act
    api_key = service.create(name='CI key')

    # assert
    emit_mock.assert_called_once_with(
        EventName.API_KEY_CREATE,
        account_id=account.id,
        actor=Actor(
            type=ActorType.USER,
            id=owner.id,
            email=owner.email,
        ),
        event_object=EventObject(
            type=EventObjectType.API_KEY,
            id=api_key.id,
        ),
        payload={'name': 'CI key', 'target_user_id': owner.id},
    )


def test_create__key_of_another_user__emit_target_user_id(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_admin(account=account)
    emit_mock = mocker.patch('src.logs.events.mixins.emit')
    service = APIKeyService(user=owner, auth_type=AuthTokenType.USER)

    # act
    api_key = service.create(name='CI key', target_user=target)

    # assert
    emit_mock.assert_called_once_with(
        EventName.API_KEY_CREATE,
        account_id=account.id,
        actor=Actor(
            type=ActorType.USER,
            id=owner.id,
            email=owner.email,
        ),
        event_object=EventObject(
            type=EventObjectType.API_KEY,
            id=api_key.id,
        ),
        payload={'name': 'CI key', 'target_user_id': target.id},
    )


def test_create__api_key_auth__emit_api_key_actor_type(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    emit_mock = mocker.patch('src.logs.events.mixins.emit')
    service = APIKeyService(user=owner, auth_type=AuthTokenType.API)

    # act
    api_key = service.create(name='CI key')

    # assert
    emit_mock.assert_called_once_with(
        EventName.API_KEY_CREATE,
        account_id=account.id,
        actor=Actor(
            type=ActorType.API_KEY,
            id=owner.id,
            email=owner.email,
        ),
        event_object=EventObject(
            type=EventObjectType.API_KEY,
            id=api_key.id,
        ),
        payload={'name': 'CI key', 'target_user_id': owner.id},
    )


def test_revoke__api_key__emit_api_key_revoke(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_key = create_test_api_key(user=owner, name='To revoke')
    emit_mock = mocker.patch('src.logs.events.mixins.emit')
    service = APIKeyService(
        user=owner,
        instance=api_key,
        auth_type=AuthTokenType.USER,
    )

    # act
    service.revoke()

    # assert
    emit_mock.assert_called_once_with(
        EventName.API_KEY_REVOKE,
        account_id=account.id,
        actor=Actor(
            type=ActorType.USER,
            id=owner.id,
            email=owner.email,
        ),
        event_object=EventObject(
            type=EventObjectType.API_KEY,
            id=api_key.id,
        ),
        payload={'name': 'To revoke', 'target_user_id': owner.id},
    )


def test_create__api_keys_endpoint__event_has_no_raw_key(
    api_client,
    fake_stream,
):

    """ The whole record written to the stream is checked, not the
        payload alone: a key that reaches a log backend is a key an
        operator of that backend can sign in with. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_client.token_authenticate(
        owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.12',
    )

    # act
    response = api_client.post(
        path='/accounts/api-keys',
        data={'name': 'CI key'},
        HTTP_X_REQUEST_ID='audit-api-key-1',
    )

    # assert
    assert response.status_code == 201
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    record = to_json(event.to_dict())
    assert response.data['token'] not in record
    assert 'token' not in event.payload
    assert event.type == EventName.API_KEY_CREATE
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.API_KEY,
        id=response.data['id'],
    )
    assert event.payload == {
        'name': 'CI key',
        'target_user_id': owner.id,
    }
    assert event.ip == '10.10.0.12'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-api-key-1'


def test_destroy__api_keys_endpoint__event_has_no_raw_key(
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_key = create_test_api_key(user=owner, name='To revoke')
    api_client.token_authenticate(owner)

    # act
    response = api_client.delete(f'/accounts/api-keys/{api_key.id}')

    # assert
    assert response.status_code == 204
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    record = to_json(event.to_dict())
    assert api_key.token not in record
    assert event.type == EventName.API_KEY_REVOKE
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.API_KEY,
        id=api_key.id,
    )
    assert event.payload == {
        'name': 'To revoke',
        'target_user_id': owner.id,
    }
