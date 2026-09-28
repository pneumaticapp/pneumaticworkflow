import pytest

from src.accounts.services.account import AccountService
from src.accounts.services.user_invite import UserInviteService
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_account,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_accept__invited_user__audit_invite_accepted(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invited = create_invited_user(user=owner)
    invite = invited.invite
    create_onboarding_workflows_mock = mocker.patch(
        'src.processes.services.system_workflows.SystemWorkflowService'
        '.create_onboarding_workflows',
    )
    create_activated_workflows_mock = mocker.patch(
        'src.processes.services.system_workflows.SystemWorkflowService'
        '.create_activated_workflows',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user_invite.send_user_updated_notification'
        '.delay',
    )
    users_joined_mock = mocker.patch(
        'src.accounts.services.user_invite.AnalyticService.users_joined',
    )
    identify_mock = mocker.patch.object(
        UserInviteService,
        attribute='identify',
    )
    group_mock = mocker.patch.object(
        UserInviteService,
        attribute='group',
    )
    identify_users_mock = mocker.patch(
        'src.accounts.services.account.identify_users.delay',
    )
    account_group_mock = mocker.patch.object(
        AccountService,
        attribute='group',
    )
    invite_accepted_mock = mocker.patch(
        'src.accounts.services.user_invite.AuditEventService.'
        'invite_accepted',
    )

    # act
    response = api_client.post(
        path=f'/accounts/invites/{invite.id}/accept',
        data={
            'first_name': 'Some',
            'last_name': 'Body',
            'password': 'secret-123',
        },
    )

    # assert
    assert response.status_code == 200
    invite_accepted_mock.assert_called_once_with(
        invited_user=invited,
        invited_by_id=owner.id,
    )
    create_onboarding_workflows_mock.assert_called_once_with()
    create_activated_workflows_mock.assert_called_once_with()
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )
    users_joined_mock.assert_called_once_with(invited)
    identify_mock.assert_called_once_with(invited)
    group_mock.assert_called_once_with(invited)
    identify_users_mock.assert_called_once_with(
        user_ids=(owner.id, invited.id),
    )
    account_group_mock.assert_called_once_with(
        user=invited,
        account=account,
    )
