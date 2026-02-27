import pytest
from django.conf import settings
from django.utils import timezone

from src.accounts.enums import (
    NotificationType,
)
from src.accounts.models import Notification
from src.notifications.enums import (
    NotificationMethod,
)
from src.notifications.services.websockets import (
    WebSocketService,
)
from src.notifications.tasks import (
    _send_urgent_notification,
)
from src.processes.enums import (
    DirectlyStatus,
    PerformerType,
)
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_guest,
    create_test_user,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_send_urgent_notification__call_services__ok(mocker):

    # arrange
    account = create_test_account(
        logo_lg='https://logo.jpg',
        log_api_requests=True,
    )
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
    )
    user = create_test_user(
        email='t@t.t',
        account=account,
        is_account_owner=False,
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.performers.add(account_owner)
    websocket_service_init_mock = mocker.patch.object(
        WebSocketService,
        attribute='__init__',
        return_value=None,
    )
    websocket_urgent_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_urgent',
    )
    websocket_not_urgent_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_not_urgent',
    )

    # act
    _send_urgent_notification(
        logging=account.log_api_requests,
        author_id=user.id,
        task_ids=[task.id],
        account_id=account.id,
        notification_type=NotificationType.URGENT,
        method_name=NotificationMethod.urgent,
        logo_lg=account.logo_lg,
    )

    # assert
    notification = Notification.objects.get(
        task_id=task.id,
        user_id=account_owner.id,
        author_id=user.id,
        account_id=account.id,
        type=NotificationType.URGENT,
        text=None,
    )
    websocket_service_init_mock.assert_called_once_with(
        logo_lg=account.logo_lg,
        account_id=account.id,
        logging=account.log_api_requests,
    )
    link = f'{settings.FRONTEND_URL}/workflows/{task.id}'
    websocket_urgent_mock.assert_called_once_with(
        user_id=account_owner.id,
        user_email=account_owner.email,
        sync=True,
        notification=notification,
        link=link,
    )
    websocket_not_urgent_mock.assert_not_called()


def test_send_urgent_notification__call_services_with_group__ok(mocker):
    # arrange
    account = create_test_account(
        logo_lg='https://logo.jpg',
        log_api_requests=True,
    )
    create_test_user(
        is_account_owner=True,
        account=account,
    )
    user = create_test_user(
        email='t@t.t',
        account=account,
        is_account_owner=False,
    )
    user_in_group = create_test_user(
        email='t2@t.t',
        account=account,
        is_account_owner=False,
    )
    group = create_test_group(user.account, users=[user_in_group])
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
        directly_status=DirectlyStatus.CREATED,
    )
    websocket_service_init_mock = mocker.patch.object(
        WebSocketService,
        '__init__',
        return_value=None,
    )
    websocket_urgent_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_urgent',
    )
    websocket_not_urgent_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_not_urgent',
    )

    # act
    _send_urgent_notification(
        logging=account.log_api_requests,
        author_id=user.id,
        task_ids=[task.id],
        account_id=account.id,
        notification_type=NotificationType.URGENT,
        method_name=NotificationMethod.urgent,
        logo_lg=account.logo_lg,
    )

    # assert
    notification = Notification.objects.get(
        task_id=task.id,
        user_id=user_in_group.id,
        author_id=user.id,
        account_id=account.id,
        type=NotificationType.URGENT,
        text=None,
    )
    websocket_service_init_mock.assert_called_once_with(
        logo_lg=account.logo_lg,
        account_id=account.id,
        logging=account.log_api_requests,
    )
    link = f'{settings.FRONTEND_URL}/workflows/{task.id}'
    websocket_urgent_mock.assert_called_once_with(
        user_id=user_in_group.id,
        user_email=user_in_group.email,
        sync=True,
        notification=notification,
        link=link,
    )
    websocket_not_urgent_mock.assert_not_called()


def test_send_not_urgent_notification__call_services__ok(mocker):

    # arrange
    account = create_test_account(
        logo_lg='https://logo.jpg',
        log_api_requests=True,
    )
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
    )
    user = create_test_user(
        email='t@t.t',
        account=account,
        is_account_owner=False,
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.performers.add(account_owner)
    websocket_service_init_mock = mocker.patch.object(
        WebSocketService,
        attribute='__init__',
        return_value=None,
    )
    websocket_urgent_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_urgent',
    )
    websocket_not_urgent_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_not_urgent',
    )

    # act
    _send_urgent_notification(
        logging=account.log_api_requests,
        author_id=user.id,
        task_ids=[task.id],
        account_id=account.id,
        notification_type=NotificationType.NOT_URGENT,
        method_name=NotificationMethod.not_urgent,
        logo_lg=account.logo_lg,
    )

    # assert
    notification = Notification.objects.get(
        task_id=task.id,
        user_id=account_owner.id,
        author_id=user.id,
        account_id=account.id,
        type=NotificationType.NOT_URGENT,
        text=None,
    )
    websocket_service_init_mock.assert_called_once_with(
        logo_lg=account.logo_lg,
        account_id=account.id,
        logging=account.log_api_requests,
    )
    link = f'{settings.FRONTEND_URL}/workflows/{task.id}'
    websocket_not_urgent_mock.assert_called_once_with(
        user_id=account_owner.id,
        user_email=account_owner.email,
        sync=True,
        notification=notification,
        link=link,
    )
    websocket_urgent_mock.assert_not_called()


def test_send_urgent_notification_completed_performer__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
    )
    user = create_test_user(
        email='t@t.t',
        account=account,
        is_account_owner=False,
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task=task,
        user=account_owner,
        is_completed=True,
        date_completed=timezone.now(),
    )
    websocket_urgent_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_urgent',
    )
    websocket_not_urgent_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_not_urgent',
    )

    # act
    _send_urgent_notification(
        logging=account.log_api_requests,
        logo_lg=account.logo_lg,
        author_id=user.id,
        task_ids=[task.id],
        account_id=account.id,
        notification_type=NotificationType.URGENT,
        method_name=NotificationMethod.urgent,
    )

    # assert
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=account_owner.id,
        author_id=user.id,
        account_id=account.id,
        type=NotificationType.URGENT,
        text=None,
    ).exists()

    websocket_urgent_mock.assert_not_called()
    websocket_not_urgent_mock.assert_not_called()


def test_send_urgent_notification_deleted_performer__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
    )
    user = create_test_user(
        email='t@t.t',
        account=account,
        is_account_owner=False,
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task=task,
        user=account_owner,
        is_completed=False,
        directly_status=DirectlyStatus.DELETED,
        date_completed=timezone.now(),
    )
    websocket_urgent_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_urgent',
    )
    websocket_not_urgent_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_not_urgent',
    )

    # act
    _send_urgent_notification(
        logging=account.log_api_requests,
        logo_lg=account.logo_lg,
        author_id=user.id,
        task_ids=[task.id],
        account_id=account.id,
        notification_type=NotificationType.URGENT,
        method_name=NotificationMethod.urgent,
    )

    # assert
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=account_owner.id,
        author_id=user.id,
        account_id=account.id,
        type=NotificationType.URGENT,
        text=None,
    ).exists()

    websocket_urgent_mock.assert_not_called()
    websocket_not_urgent_mock.assert_not_called()


def test_send_urgent_notification_guest_performer__skip(mocker):

    # arrange
    account = create_test_account()
    create_test_user(
        is_account_owner=True,
        account=account,
    )
    user = create_test_user(
        email='t@t.t',
        account=account,
        is_account_owner=False,
    )
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task=task,
        user=guest,
    )
    websocket_urgent_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_urgent',
    )
    websocket_not_urgent_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_not_urgent',
    )

    # act
    _send_urgent_notification(
        logging=account.log_api_requests,
        logo_lg=account.logo_lg,
        author_id=user.id,
        task_ids=[task.id],
        account_id=account.id,
        notification_type=NotificationType.URGENT,
        method_name=NotificationMethod.urgent,
    )

    # assert
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=guest.id,
        author_id=user.id,
        account_id=account.id,
        type=NotificationType.URGENT,
        text=None,
    ).exists()

    websocket_urgent_mock.assert_not_called()
    websocket_not_urgent_mock.assert_not_called()


def test_send_urgent_notification__another_task__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
    )
    user = create_test_user(
        email='t@t.t',
        account=account,
        is_account_owner=False,
    )
    workflow = create_test_workflow(user, tasks_count=2, active_task_number=2)
    task_1 = workflow.tasks.get(number=1)
    task_1.performers.add(account_owner)
    task_2 = workflow.tasks.get(number=2)
    task_2.performers.add(account_owner)

    websocket_urgent_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_urgent',
    )
    websocket_not_urgent_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_not_urgent',
    )

    # act
    _send_urgent_notification(
        logging=account.log_api_requests,
        logo_lg=account.logo_lg,
        author_id=user.id,
        task_ids=[task_2.id],
        account_id=account.id,
        notification_type=NotificationType.URGENT,
        method_name=NotificationMethod.urgent,
    )

    # assert
    notification = Notification.objects.get(
        task_id=task_2.id,
        user_id=account_owner.id,
        author_id=user.id,
        account_id=account.id,
        type=NotificationType.URGENT,
        text=None,
    )

    link = f'{settings.FRONTEND_URL}/workflows/{task_2.id}'
    websocket_urgent_mock.assert_called_once_with(
        user_id=account_owner.id,
        user_email=account_owner.email,
        sync=True,
        notification=notification,
        link=link,
    )
    websocket_not_urgent_mock.assert_not_called()
