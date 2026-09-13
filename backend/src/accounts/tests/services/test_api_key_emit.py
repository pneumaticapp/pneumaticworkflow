import pytest

from src.accounts.services.api_key import APIKeyService
from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    ActorType,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
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
