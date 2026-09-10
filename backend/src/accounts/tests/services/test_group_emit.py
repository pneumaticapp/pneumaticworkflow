import pytest

from src.accounts.enums import BillingPlanType
from src.accounts.models import UserGroup
from src.accounts.services.group import UserGroupService
from src.analysis.events import GroupsAnalyticsEvent
from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    ActorType,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_create__group__emit_group_create(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_admin(account=account)
    analytics_mock = mocker.patch(
        'src.analysis.tasks.track_group_analytics.delay',
    )
    send_group_created_mock = mocker.patch(
        'src.notifications.tasks.send_group_created_notification.delay',
    )
    sync_account_file_fields_mock = mocker.patch(
        'src.accounts.services.group.sync_account_file_fields',
    )
    emit_mock = mocker.patch('src.accounts.services.group.emit')
    service = UserGroupService(user=owner, auth_type=AuthTokenType.USER)

    # act
    group = service.create(name='Sales', users=[member.id])

    # assert
    emit_mock.assert_called_once_with(
        EventName.GROUP_CREATE,
        account_id=account.id,
        actor=Actor(
            type=ActorType.USER,
            id=owner.id,
            email=owner.email,
        ),
        event_object=EventObject(type=EventObjectType.GROUP, id=group.id),
        payload={'name': 'Sales', 'users_ids': [member.id]},
    )
    analytics_mock.assert_called_once_with(
        event=GroupsAnalyticsEvent.created,
        user_id=owner.id,
        user_email=owner.email,
        user_first_name=owner.first_name,
        user_last_name=owner.last_name,
        group_photo=group.photo,
        group_users=[member.id],
        account_id=account.id,
        group_id=group.id,
        group_name='Sales',
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        new_users_ids=[member.id],
        new_photo=None,
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


def test_partial_update__name_and_users__emit_group_update(mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    owner = create_test_owner(account=account)
    member = create_test_admin(account=account)
    group = create_test_group(account=account, name='Sales')
    analytics_mock = mocker.patch(
        'src.analysis.tasks.track_group_analytics.delay',
    )
    send_group_updated_mock = mocker.patch(
        'src.notifications.tasks.send_group_updated_notification.delay',
    )
    send_new_task_websocket_mock = mocker.patch(
        'src.notifications.tasks.send_new_task_websocket.delay',
    )
    send_task_deleted_mock = mocker.patch(
        'src.notifications.tasks.send_task_deleted_notification.delay',
    )
    emit_mock = mocker.patch('src.accounts.services.group.emit')
    service = UserGroupService(
        user=owner,
        instance=group,
        auth_type=AuthTokenType.USER,
    )

    # act
    service.partial_update(
        name='Support',
        users=[member.id],
        force_save=True,
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.GROUP_UPDATE,
        account_id=account.id,
        actor=Actor(
            type=ActorType.USER,
            id=owner.id,
            email=owner.email,
        ),
        event_object=EventObject(type=EventObjectType.GROUP, id=group.id),
        payload={
            'changed_fields': ['name', 'users'],
            'added_users_ids': [member.id],
            'removed_users_ids': [],
        },
    )
    analytics_mock.assert_called_once_with(
        event=GroupsAnalyticsEvent.updated,
        user_id=owner.id,
        user_email=owner.email,
        user_first_name=owner.first_name,
        user_last_name=owner.last_name,
        group_photo=None,
        group_users=[member.id],
        account_id=account.id,
        group_id=group.id,
        group_name='Support',
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        new_users_ids=[member.id],
        removed_users_ids=[],
        new_name='Support',
        new_photo=None,
    )
    send_group_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        group_data=mocker.ANY,
    )
    # The group performs no task: nobody to tell about the membership.
    send_new_task_websocket_mock.assert_not_called()
    send_task_deleted_mock.assert_not_called()


def test_partial_update__removed_users__emit_removed_users_ids(mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    owner = create_test_owner(account=account)
    member = create_test_admin(account=account)
    group = create_test_group(
        account=account,
        name='Sales',
        users=[member],
    )
    analytics_mock = mocker.patch(
        'src.analysis.tasks.track_group_analytics.delay',
    )
    send_group_updated_mock = mocker.patch(
        'src.notifications.tasks.send_group_updated_notification.delay',
    )
    send_new_task_websocket_mock = mocker.patch(
        'src.notifications.tasks.send_new_task_websocket.delay',
    )
    send_task_deleted_mock = mocker.patch(
        'src.notifications.tasks.send_task_deleted_notification.delay',
    )
    emit_mock = mocker.patch('src.accounts.services.group.emit')
    service = UserGroupService(
        user=owner,
        instance=group,
        auth_type=AuthTokenType.USER,
    )

    # act
    service.partial_update(users=[], force_save=True)

    # assert
    emit_mock.assert_called_once_with(
        EventName.GROUP_UPDATE,
        account_id=account.id,
        actor=Actor(
            type=ActorType.USER,
            id=owner.id,
            email=owner.email,
        ),
        event_object=EventObject(type=EventObjectType.GROUP, id=group.id),
        payload={
            'changed_fields': ['users'],
            'added_users_ids': [],
            'removed_users_ids': [member.id],
        },
    )
    analytics_mock.assert_called_once_with(
        event=GroupsAnalyticsEvent.updated,
        user_id=owner.id,
        user_email=owner.email,
        user_first_name=owner.first_name,
        user_last_name=owner.last_name,
        group_photo=None,
        group_users=[],
        account_id=account.id,
        group_id=group.id,
        group_name=None,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        new_users_ids=[],
        removed_users_ids=[member.id],
        new_name=None,
        new_photo=None,
    )
    send_group_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        group_data=mocker.ANY,
    )
    send_new_task_websocket_mock.assert_not_called()
    send_task_deleted_mock.assert_not_called()


def test_partial_update__name_only__emit_no_membership_change(mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    owner = create_test_owner(account=account)
    member = create_test_admin(account=account)
    group = create_test_group(
        account=account,
        name='Sales',
        users=[member],
    )
    analytics_mock = mocker.patch(
        'src.analysis.tasks.track_group_analytics.delay',
    )
    send_group_updated_mock = mocker.patch(
        'src.notifications.tasks.send_group_updated_notification.delay',
    )
    send_new_task_websocket_mock = mocker.patch(
        'src.notifications.tasks.send_new_task_websocket.delay',
    )
    send_task_deleted_mock = mocker.patch(
        'src.notifications.tasks.send_task_deleted_notification.delay',
    )
    emit_mock = mocker.patch('src.accounts.services.group.emit')
    service = UserGroupService(
        user=owner,
        instance=group,
        auth_type=AuthTokenType.USER,
    )

    # act
    service.partial_update(name='Support', force_save=True)

    # assert
    emit_mock.assert_called_once_with(
        EventName.GROUP_UPDATE,
        account_id=account.id,
        actor=Actor(
            type=ActorType.USER,
            id=owner.id,
            email=owner.email,
        ),
        event_object=EventObject(type=EventObjectType.GROUP, id=group.id),
        payload={
            'changed_fields': ['name'],
            'added_users_ids': [],
            'removed_users_ids': [],
        },
    )
    analytics_mock.assert_called_once_with(
        event=GroupsAnalyticsEvent.updated,
        user_id=owner.id,
        user_email=owner.email,
        user_first_name=owner.first_name,
        user_last_name=owner.last_name,
        group_photo=None,
        group_users=[member.id],
        account_id=account.id,
        group_id=group.id,
        group_name='Support',
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        new_users_ids=None,
        removed_users_ids=None,
        new_name='Support',
        new_photo=None,
    )
    send_group_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        group_data=mocker.ANY,
    )
    send_new_task_websocket_mock.assert_not_called()
    send_task_deleted_mock.assert_not_called()


def test_delete__group__emit_group_delete(mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    owner = create_test_owner(account=account)
    member = create_test_admin(account=account)
    group = create_test_group(
        account=account,
        name='Sales',
        users=[member],
    )
    analytics_mock = mocker.patch(
        'src.analysis.tasks.track_group_analytics.delay',
    )
    send_group_deleted_mock = mocker.patch(
        'src.notifications.tasks.send_group_deleted_notification.delay',
    )
    send_task_deleted_mock = mocker.patch(
        'src.notifications.tasks.send_task_deleted_notification.delay',
    )
    emit_mock = mocker.patch('src.accounts.services.group.emit')
    service = UserGroupService(
        user=owner,
        instance=group,
        auth_type=AuthTokenType.USER,
    )

    # act
    service.delete()

    # assert
    emit_mock.assert_called_once_with(
        EventName.GROUP_DELETE,
        account_id=account.id,
        actor=Actor(
            type=ActorType.USER,
            id=owner.id,
            email=owner.email,
        ),
        event_object=EventObject(type=EventObjectType.GROUP, id=group.id),
        payload={'name': 'Sales', 'users_ids': [member.id]},
    )
    analytics_mock.assert_called_once_with(
        event=GroupsAnalyticsEvent.deleted,
        user_id=owner.id,
        user_email=owner.email,
        user_first_name=owner.first_name,
        user_last_name=owner.last_name,
        group_photo=None,
        group_users=[member.id],
        account_id=account.id,
        group_id=group.id,
        group_name='Sales',
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    send_group_deleted_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        group_data=mocker.ANY,
    )
    send_task_deleted_mock.assert_not_called()


def test_create__groups_endpoint__event_keeps_request_context(
    mocker,
    api_client,
    events_enabled,
    run_on_commit,
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
    analytics_mock = mocker.patch(
        'src.analysis.tasks.track_group_analytics.delay',
    )
    send_group_created_mock = mocker.patch(
        'src.notifications.tasks.send_group_created_notification.delay',
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
    assert event.type == EventName.GROUP_CREATE
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    group = UserGroup.objects.get(account=account, name='Sales')
    assert event.object == EventObject(
        type=EventObjectType.GROUP,
        id=group.id,
    )
    assert event.payload == {'name': 'Sales', 'users_ids': [owner.id]}
    assert event.ip == '10.10.0.11'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-group-1'
    analytics_mock.assert_called_once_with(
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
