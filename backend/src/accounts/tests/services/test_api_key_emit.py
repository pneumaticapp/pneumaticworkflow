import pytest

from src.accounts.enums import UserType
from src.accounts.services.api_key import APIKeyService
from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    ApiKeyEvents,
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
    emit_mock = mocker.patch('src.logs.events.services.emit')
    service = APIKeyService(user=owner, auth_type=AuthTokenType.USER)

    # act
    api_key = service.create(name='CI key')

    # assert
    emit_mock.assert_called_once_with(
        ApiKeyEvents.CREATE,
        account_id=account.id,
        actor=Actor(
            id=owner.id,
            email=owner.email,
            user_type=UserType.USER,
        ),
        auth_type=AuthTokenType.USER,
        event_object=EventObject(
            type=EventObjectType.API_KEY,
            id=api_key.id,
        ),
        payload={'name': 'CI key', 'target_user_id': owner.id},
        workflow_id=None,
        task_id=None,
    )


def test_create__key_of_another_user__emit_target_user_id(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_admin(account=account)
    emit_mock = mocker.patch('src.logs.events.services.emit')
    service = APIKeyService(user=owner, auth_type=AuthTokenType.USER)

    # act
    api_key = service.create(name='CI key', target_user=target)

    # assert
    emit_mock.assert_called_once_with(
        ApiKeyEvents.CREATE,
        account_id=account.id,
        actor=Actor(
            id=owner.id,
            email=owner.email,
            user_type=UserType.USER,
        ),
        auth_type=AuthTokenType.USER,
        event_object=EventObject(
            type=EventObjectType.API_KEY,
            id=api_key.id,
        ),
        payload={'name': 'CI key', 'target_user_id': target.id},
        workflow_id=None,
        task_id=None,
    )


def test_create__api_key_auth__emit_api_auth_type(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    emit_mock = mocker.patch('src.logs.events.services.emit')
    service = APIKeyService(user=owner, auth_type=AuthTokenType.API)

    # act
    api_key = service.create(name='CI key')

    # assert
    emit_mock.assert_called_once_with(
        ApiKeyEvents.CREATE,
        account_id=account.id,
        actor=Actor(
            id=owner.id,
            email=owner.email,
            user_type=UserType.USER,
        ),
        auth_type=AuthTokenType.API,
        event_object=EventObject(
            type=EventObjectType.API_KEY,
            id=api_key.id,
        ),
        payload={'name': 'CI key', 'target_user_id': owner.id},
        workflow_id=None,
        task_id=None,
    )


def test_revoke__api_key__emit_api_key_revoke(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_key = create_test_api_key(user=owner, name='To revoke')
    emit_mock = mocker.patch('src.logs.events.services.emit')
    service = APIKeyService(
        user=owner,
        instance=api_key,
        auth_type=AuthTokenType.USER,
    )

    # act
    service.revoke()

    # assert
    emit_mock.assert_called_once_with(
        ApiKeyEvents.REVOKE,
        account_id=account.id,
        actor=Actor(
            id=owner.id,
            email=owner.email,
            user_type=UserType.USER,
        ),
        auth_type=AuthTokenType.USER,
        event_object=EventObject(
            type=EventObjectType.API_KEY,
            id=api_key.id,
        ),
        payload={'name': 'To revoke', 'target_user_id': owner.id},
        workflow_id=None,
        task_id=None,
    )
