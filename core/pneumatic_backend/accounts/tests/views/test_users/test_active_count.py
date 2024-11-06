import pytest
from pneumatic_backend.accounts.tests.fixtures import (
    create_test_user,
)


pytestmark = pytest.mark.django_db


def test_active_count__standard__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    account_cache = {
        'active_users': 2,
        'tenants_active_users': 1
    }
    get_cached_data_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account'
        '.AccountService.get_cached_data',
        return_value=account_cache
    )

    # act
    response = api_client.get('/accounts/users/active-count')

    # assert
    assert response.status_code == 200
    assert response.data['active_users'] == 2
    assert response.data['tenants_active_users'] == 1
    get_cached_data_mock.assert_called_once_with(
        user.account.id
    )
