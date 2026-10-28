import pytest

from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_partial_update__name_changed__audit_update_kwargs(
    mocker,
    api_client,
    group_mock,
):

    # arrange
    account = create_test_account(name='Old name')
    owner = create_test_owner(account=account)
    identify_users_mock = mocker.patch(
        'src.accounts.services.account.identify_users.delay',
    )
    account_updated_mock = mocker.patch(
        'src.accounts.views.accounts.AuditEventService.account_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        '/accounts/account',
        data={'name': 'New name', 'logo_lg': None},
        format='json',
    )

    # assert
    assert response.status_code == 200
    account_updated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        account=account,
        update_kwargs={'name': 'New name', 'logo_lg': None},
    )
    group_mock.assert_called_once_with(user=owner, account=account)
    identify_users_mock.assert_called_once_with(user_ids=(owner.id,))


def test_partial_update__same_values__audit_update_kwargs(
    mocker,
    api_client,
    group_mock,
):

    """ A request that arrived is an update, whatever it sent. """

    # arrange
    account = create_test_account(name='Same name')
    owner = create_test_owner(account=account)
    identify_users_mock = mocker.patch(
        'src.accounts.services.account.identify_users.delay',
    )
    account_updated_mock = mocker.patch(
        'src.accounts.views.accounts.AuditEventService.account_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        '/accounts/account',
        data={'name': 'Same name'},
        format='json',
    )

    # assert
    assert response.status_code == 200
    account_updated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        account=account,
        update_kwargs={'name': 'Same name'},
    )
    group_mock.assert_called_once_with(user=owner, account=account)
    identify_users_mock.assert_called_once_with(user_ids=(owner.id,))


def test_partial_update__not_admin__audit_not_called(
    mocker,
    api_client,
    group_mock,
):

    # arrange
    account = create_test_account(name='Old name')
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    identify_users_mock = mocker.patch(
        'src.accounts.services.account.identify_users.delay',
    )
    account_updated_mock = mocker.patch(
        'src.accounts.views.accounts.AuditEventService.account_updated',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/account',
        data={'name': 'New name'},
        format='json',
    )

    # assert
    assert response.status_code == 403
    account_updated_mock.assert_not_called()
    group_mock.assert_not_called()
    identify_users_mock.assert_not_called()
