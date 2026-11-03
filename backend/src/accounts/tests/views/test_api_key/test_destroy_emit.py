import pytest

from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_api_key,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_destroy__api_keys_endpoint__audit_api_key_revoked(
    mocker,
    api_client,
):

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
    api_client.token_authenticate(owner)

    # act
    response = api_client.delete(f'/accounts/api-keys/{api_key.id}')

    # assert
    assert response.status_code == 204
    api_key_revoked_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        api_key=api_key,
    )


def test_destroy__key_of_another_account__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    other_account = create_test_account(name='Other')
    other_owner = create_test_owner(
        account=other_account,
        email='other@test.test',
    )
    api_key = create_test_api_key(
        user=other_owner,
        name='Other key',
    )
    api_key_revoked_mock = mocker.patch(
        'src.accounts.services.api_key.AuditEventService.api_key_revoked',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.delete(f'/accounts/api-keys/{api_key.id}')

    # assert
    assert response.status_code == 404
    api_key.refresh_from_db()
    assert api_key.is_active is True
    api_key_revoked_mock.assert_not_called()
