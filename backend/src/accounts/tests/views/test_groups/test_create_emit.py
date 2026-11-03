import pytest

from src.accounts.enums import BillingPlanType
from src.accounts.messages import MSG_A_0039
from src.accounts.models import UserGroup
from src.analysis.events import GroupsAnalyticsEvent
from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_create__groups_endpoint__audit_group_created(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    owner = create_test_owner(account=account)
    api_client.token_authenticate(owner)
    track_group_analytics_mock = mocker.patch(
        'src.analysis.tasks.track_group_analytics.delay',
    )
    send_group_created_mock = mocker.patch(
        'src.notifications.tasks.send_group_created_notification.delay',
    )
    sync_account_file_fields_mock = mocker.patch(
        'src.accounts.services.group.sync_account_file_fields',
    )
    group_created_mock = mocker.patch(
        'src.accounts.services.group.AuditEventService.group_created',
    )

    # act
    response = api_client.post(
        path='/accounts/groups',
        data={'name': 'Sales', 'photo': '', 'users': [owner.id]},
    )

    # assert
    assert response.status_code == 200
    group = UserGroup.objects.get(account=account, name='Sales')
    group_created_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        group=group,
        users_ids=[owner.id],
    )
    track_group_analytics_mock.assert_called_once_with(
        event=GroupsAnalyticsEvent.created,
        user_id=owner.id,
        user_email=owner.email,
        user_first_name=owner.first_name,
        user_last_name=owner.last_name,
        group_photo='',
        group_users=[owner.id],
        account_id=account.id,
        group_id=group.id,
        group_name='Sales',
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        new_users_ids=[owner.id],
        new_photo='',
    )
    send_group_created_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        group_data=mocker.ANY,
    )
    sync_account_file_fields_mock.assert_called_once_with(
        account=account,
        user=owner,
        old_values=[None],
        new_values=[group.photo],
    )


def test_create__foreign_account_user__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    owner = create_test_owner(account=account)
    another_account = create_test_account(plan=BillingPlanType.UNLIMITED)
    another_user = create_test_owner(
        account=another_account,
        email='another@pneumatic.app',
    )
    track_group_analytics_mock = mocker.patch(
        'src.analysis.tasks.track_group_analytics.delay',
    )
    send_group_created_mock = mocker.patch(
        'src.notifications.tasks.send_group_created_notification.delay',
    )
    group_created_mock = mocker.patch(
        'src.accounts.services.group.AuditEventService.group_created',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        path='/accounts/groups',
        data={'name': 'Sales', 'photo': '', 'users': [another_user.id]},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_A_0039
    assert response.data['details']['reason'] == MSG_A_0039
    assert response.data['details']['name'] == 'users'
    assert not UserGroup.objects.filter(account=account).exists()
    group_created_mock.assert_not_called()
    track_group_analytics_mock.assert_not_called()
    send_group_created_mock.assert_not_called()
