import pytest
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
    SourceType,
)
from pneumatic_backend.accounts.tests.fixtures import (
    create_test_user,
    create_invited_user,
    create_test_owner,
    create_test_account
)
from pneumatic_backend.accounts.services import (
    UserInviteService
)


pytestmark = pytest.mark.django_db


def test_toggle_admin__upgrade_to_admin__ok(
    identify_mock,
    api_client
):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account, is_admin=True)
    invited = create_invited_user(user, is_admin=False)
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/accounts/users/{invited.id}/toggle-admin'
    )

    # assert
    assert response.status_code == 204
    invited.refresh_from_db()
    assert invited.is_admin is True
    identify_mock.assert_called_once_with(invited)


def test_toggle_admin__downgrade_admin__ok(
    identify_mock,
    api_client
):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(is_admin=True, account=account)
    invited = create_invited_user(user, is_admin=True)
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/accounts/users/{invited.id}/toggle-admin'
    )

    # assert
    assert response.status_code == 204
    invited.refresh_from_db()
    assert invited.is_admin is False
    identify_mock.assert_called_once_with(invited)


def test_toggle_admin__downgrade_for_account_owner__not_found(
    identify_mock,
    api_client
):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    account_owner = create_test_owner(account=account)
    invited = create_invited_user(account_owner, is_admin=True)
    api_client.token_authenticate(invited)

    # act
    response = api_client.post(
        f'accounts/users/{account_owner.id}/toggle-admin'
    )

    # assert
    assert response.status_code == 404
    identify_mock.assert_not_called()


@pytest.mark.parametrize('is_account_owner', (True, False))
def test_toggle_admin__downgrade_transferred_user__ok(
    identify_mock,
    api_client,
    is_account_owner
):

    # arrange
    account_1 = create_test_account(name='transfer from')
    account_2 = create_test_account(
        name='transfer to',
        plan=BillingPlanType.PREMIUM
    )
    user_to_transfer = create_test_user(
        account=account_1,
        email='user_to_transfer@test.test',
        is_account_owner=is_account_owner
    )
    account_2_owner = create_test_user(
        account=account_2,
        is_account_owner=True,
        email='owner@test.test'
    )
    current_url = 'some_url'
    service = UserInviteService(
        request_user=account_2_owner,
        current_url=current_url
    )
    service.invite_user(
        email=user_to_transfer.email,
        invited_from=SourceType.EMAIL
    )
    account_2_new_user = account_2.users.get(email=user_to_transfer.email)
    api_client.token_authenticate(account_2_owner)

    # act
    response = api_client.post(
        f'/accounts/users/{account_2_new_user.id}/toggle-admin'
    )

    # assert
    assert response.status_code == 204
    account_2_new_user.refresh_from_db()
    assert account_2_new_user.is_admin is False
