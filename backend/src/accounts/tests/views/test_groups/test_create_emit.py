import pytest

from src.accounts.enums import BillingPlanType, UserType
from src.accounts.models import UserGroup
from src.accounts.services.exceptions import UserGroupServiceException
from src.accounts.services.group import UserGroupService
from src.analysis.events import GroupsAnalyticsEvent
from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    EventObjectType,
    GroupEvents,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_create__groups_endpoint__event_keeps_request_context(
    mocker,
    api_client,
    fake_stream,
):

    """ The group service has no request: the address, the browser
        and the correlation id come from the middleware context. """

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    owner = create_test_owner(account=account)
    api_client.token_authenticate(
        owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.11',
    )
    track_group_analytics_mock = mocker.patch(
        'src.analysis.tasks.track_group_analytics.delay',
    )
    send_group_created_mock = mocker.patch(
        'src.notifications.tasks.send_group_created_notification.delay',
    )
    sync_account_file_fields_mock = mocker.patch(
        'src.accounts.services.group.sync_account_file_fields',
    )

    # act
    response = api_client.post(
        path='/accounts/groups',
        data={'name': 'Sales', 'photo': '', 'users': [owner.id]},
        HTTP_X_REQUEST_ID='audit-group-1',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == GroupEvents.CREATE
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    group = UserGroup.objects.get(account=account, name='Sales')
    assert event.object == EventObject(
        type=EventObjectType.GROUP,
        id=group.id,
    )
    assert event.payload == {'name': 'Sales', 'users_ids': [owner.id]}
    assert event.ip == '10.10.0.11'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-group-1'
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


def test_create__service_exception__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    owner = create_test_owner(account=account)
    create_mock = mocker.patch.object(
        UserGroupService,
        attribute='create',
        side_effect=UserGroupServiceException('Group error'),
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        path='/accounts/groups',
        data={'name': 'Sales', 'photo': '', 'users': [owner.id]},
    )

    # assert
    assert response.status_code == 400
    assert response.data == {
        'code': ErrorCode.VALIDATION_ERROR,
        'message': 'Group error',
        'details': {},
    }
    assert fake_stream.events == []
    create_mock.assert_called_once_with(
        name='Sales',
        photo='',
        users=[owner.id],
    )
