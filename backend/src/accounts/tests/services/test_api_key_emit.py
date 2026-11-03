import pytest

from src.accounts.services.api_key import APIKeyService
from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_api_key,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_create__api_key__audit_api_key_created(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_key_created_mock = mocker.patch(
        'src.accounts.services.api_key.AuditEventService.api_key_created',
    )
    service = APIKeyService(
        user=owner,
        auth_type=AuthTokenType.USER,
    )

    # act
    api_key = service.create(name='CI key')

    # assert
    assert api_key.user_id == owner.id
    api_key_created_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        api_key=api_key,
    )


def test_create__key_of_another_user__audit_api_key_created(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_admin(account=account)
    api_key_created_mock = mocker.patch(
        'src.accounts.services.api_key.AuditEventService.api_key_created',
    )
    service = APIKeyService(
        user=owner,
        auth_type=AuthTokenType.USER,
    )

    # act
    api_key = service.create(
        name='CI key',
        target_user=target,
    )

    # assert
    assert api_key.user_id == target.id
    api_key_created_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        api_key=api_key,
    )


def test_create__api_key_auth__audit_api_auth_type(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_key_created_mock = mocker.patch(
        'src.accounts.services.api_key.AuditEventService.api_key_created',
    )
    service = APIKeyService(
        user=owner,
        auth_type=AuthTokenType.API,
    )

    # act
    api_key = service.create(name='CI key')

    # assert
    api_key_created_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.API,
        api_key=api_key,
    )


def test_revoke__api_key__audit_api_key_revoked(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_key = create_test_api_key(
        user=owner,
        name='To revoke',
    )
    api_key_revoked_mock = mocker.patch(
        'src.accounts.services.api_key.AuditEventService.api_key_revoked',
    )
    service = APIKeyService(
        user=owner,
        instance=api_key,
        auth_type=AuthTokenType.USER,
    )

    # act
    service.revoke()

    # assert
    api_key.refresh_from_db()
    assert api_key.is_active is False
    api_key_revoked_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        api_key=api_key,
    )
