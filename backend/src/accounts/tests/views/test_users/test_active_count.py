import pytest
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
)


pytestmark = pytest.mark.django_db


def test_active_count__standard__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    account_cache = {
        'active_users': 2,
        'tenants_active_users': 1,
    }
    get_cached_data_mock = mocker.patch(
        'src.accounts.services.account'
        '.AccountService.get_cached_data',
        return_value=account_cache,
    )

    # act
    response = api_client.get('/accounts/users/active-count')

    # assert
    assert response.status_code == 200
    assert response.data['active_users'] == 2
    assert response.data['tenants_active_users'] == 1
    get_cached_data_mock.assert_called_once_with(
        user.account.id,
    )


def test_active_count__not_admin__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    create_test_user(
        account=account,
        is_account_owner=True,
        is_admin=True,
    )
    user = create_test_user(
        account=account,
        is_admin=False,
        is_account_owner=False,
        email='test+1@test.test',
    )
    api_client.token_authenticate(user)
    account_cache = {
        'active_users': 2,
        'tenants_active_users': 1,
    }
    get_cached_data_mock = mocker.patch(
        'src.accounts.services.account'
        '.AccountService.get_cached_data',
        return_value=account_cache,
    )

    # act
    response = api_client.get('/accounts/users/active-count')

    # assert
    assert response.status_code == 200
    assert response.data['active_users'] == 2
    assert response.data['tenants_active_users'] == 1
    get_cached_data_mock.assert_called_once_with(
        user.account.id,
    )
