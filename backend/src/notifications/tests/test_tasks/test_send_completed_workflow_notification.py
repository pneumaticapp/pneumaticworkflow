import pytest
from django.conf import settings

from src.accounts.enums import NotificationType
from src.accounts.models import Notification
from src.accounts.serializers.notifications import \
    NotificationWorkflowSerializer
from src.notifications.enums import NotificationMethod
from src.notifications.services.push import PushNotificationService
from src.notifications.tasks import _send_completed_workflow_notification
from src.processes.enums import DirectlyStatus, PerformerType, TaskStatus
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_guest,
    create_test_group,
    create_test_not_admin,
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_send_completed_workflow__call_all_services__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        account_owner,
        tasks_count=1,
    )
    link = f'{settings.FRONTEND_URL}/workflows/{workflow.id}'
    logging = True
    send_email_mock = mocker.patch(
        'src.notifications.services.email.EmailService.send_complete_workflow',
    )
    push_notification_service_init_mock = mocker.patch.object(
        PushNotificationService,
        attribute='__init__',
        return_value=None,
    )
    send_push_mock = mocker.patch(
        'src.notifications.services.push.'
        'PushNotificationService.send_complete_workflow',
    )

    # act
    _send_completed_workflow_notification(
        logging=logging,
        workflow_id=workflow.id,
    )

    # assert
    notification = Notification.objects.get(
        user_id=account_owner.id,
        account_id=account.id,
        type=NotificationType.COMPLETE_WORKFLOW,
    )
    send_email_mock.assert_called_once_with(
        link=link,
        user_id=account_owner.id,
        user_email=account_owner.email,
        workflow_name=workflow.name,
        workflow_id=workflow.id,
        notification=notification,
        sync=True,
    )
    push_notification_service_init_mock.assert_called_once_with(
        logging=logging,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )
    send_push_mock.assert_called_once_with(
        link=link,
        workflow_id=workflow.id,
        workflow_name=workflow.name,
        user_id=account_owner.id,
        user_email=account_owner.email,
        notification=notification,
        sync=True,
    )


@pytest.mark.parametrize('status', (TaskStatus.SKIPPED, TaskStatus.PENDING))
def test_send_completed_workflow__not_active_task__skip(
    mocker,
    status,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        account_owner,
        tasks_count=1,
    )
    workflow.tasks.filter(number=1).update(status=status)
    logging = False
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_completed_workflow_notification(
        logging=logging,
        workflow_id=workflow.id,
    )

    # assert
    assert not Notification.objects.filter(
        account_id=account.id,
        type=NotificationType.COMPLETE_WORKFLOW,
    ).exists()
    send_notification_mock.assert_not_called()


@pytest.mark.parametrize(
    'status',
    (
        TaskStatus.ACTIVE,
        TaskStatus.COMPLETED,
        TaskStatus.DELAYED,
    ),
)
def test_send_completed_workflow__active_task__ok(
    mocker,
    status,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        account_owner,
        tasks_count=1,
    )
    workflow.tasks.filter(number=1).update(status=status)
    logging = False
    link = f'{settings.FRONTEND_URL}/workflows/{workflow.id}'
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_completed_workflow_notification(
        logging=logging,
        workflow_id=workflow.id,
    )

    # assert
    notification = Notification.objects.get(
        user_id=account_owner.id,
        account_id=account.id,
        type=NotificationType.COMPLETE_WORKFLOW,
    )
    send_notification_mock.assert_called_once_with(
        logging=logging,
        logo_lg=None,
        user_id=account_owner.id,
        user_email=account_owner.email,
        account_id=account.id,
        notification=notification,
        method_name=NotificationMethod.complete_workflow,
        workflow_id=workflow.id,
        workflow_name=workflow.name,
        link=link,
        sync=True,
    )


def test_send_completed_another_workflow__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(
        user=account_owner,
        tasks_count=1,
    )
    another_workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )

    logging = False
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )
    link = f'{settings.FRONTEND_URL}/workflows/{workflow.id}'

    # act
    _send_completed_workflow_notification(
        logging=logging,
        workflow_id=workflow.id,
    )

    # assert
    assert not Notification.objects.filter(
        workflow_json=NotificationWorkflowSerializer(
            instance=another_workflow,
        ).data,
        account_id=account.id,
        user_id=user.id,
        type=NotificationType.COMPLETE_WORKFLOW,
    ).exists()

    notification = Notification.objects.get(
        workflow_json=NotificationWorkflowSerializer(instance=workflow).data,
        user_id=account_owner.id,
        account_id=account.id,
        type=NotificationType.COMPLETE_WORKFLOW,
    )
    send_notification_mock.assert_called_once_with(
        logging=logging,
        logo_lg=None,
        user_id=account_owner.id,
        user_email=account_owner.email,
        account_id=account.id,
        notification=notification,
        method_name=NotificationMethod.complete_workflow,
        workflow_id=workflow.id,
        workflow_name=workflow.name,
        link=link,
        sync=True,
    )


def test_send_completed_workflow__one_user_on_multiple_tasks__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        account_owner,
        tasks_count=3,
        active_task_number=3,
    )
    workflow.tasks.filter(number=2).update(status=TaskStatus.ACTIVE)
    link = f'{settings.FRONTEND_URL}/workflows/{workflow.id}'
    logging = True
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_completed_workflow_notification(
        logging=logging,
        workflow_id=workflow.id,
    )

    # assert
    notification = Notification.objects.get(
        user_id=account_owner.id,
        account_id=account.id,
        type=NotificationType.COMPLETE_WORKFLOW,
    )
    send_notification_mock.assert_called_once_with(
        logging=logging,
        logo_lg=None,
        user_id=account_owner.id,
        user_email=account_owner.email,
        account_id=account.id,
        notification=notification,
        method_name=NotificationMethod.complete_workflow,
        workflow_id=workflow.id,
        workflow_name=workflow.name,
        link=link,
        sync=True,
    )


def test_send_completed_workflow__directly_deleted_performer_user__skip(
    mocker,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(
        account_owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.performers.clear()
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.USER,
        user_id=user.id,
        directly_status=DirectlyStatus.DELETED,
    )

    logging = True
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_completed_workflow_notification(
        logging=logging,
        workflow_id=workflow.id,
    )

    # assert
    assert not Notification.objects.filter(
        account_id=account.id,
        type=NotificationType.COMPLETE_WORKFLOW,
    ).exists()
    send_notification_mock.assert_not_called()


def test_send_completed_workflow__directly_deleted_performer_group__skip(
    mocker,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    group = create_test_group(account=account, users=[user])
    workflow = create_test_workflow(
        account_owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.performers.clear()
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
        directly_status=DirectlyStatus.DELETED,
    )

    logging = True
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_completed_workflow_notification(
        logging=logging,
        workflow_id=workflow.id,
    )

    # assert
    assert not Notification.objects.filter(
        account_id=account.id,
        type=NotificationType.COMPLETE_WORKFLOW,
    ).exists()
    send_notification_mock.assert_not_called()


def test_send_completed_workflow__two_performers_on_same_task__ok(
    mocker,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    user_1 = create_test_admin(account=account)
    user_2 = create_test_not_admin(account=account)
    workflow = create_test_workflow(
        account_owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.performers.clear()
    task.performers.add(user_1)
    task.performers.add(user_2)
    TaskPerformer.objects.filter(task=task).update(is_completed=True)
    link = f'{settings.FRONTEND_URL}/workflows/{workflow.id}'
    logging = True
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_completed_workflow_notification(
        logging=logging,
        workflow_id=workflow.id,
    )

    # assert
    notification_1 = Notification.objects.get(
        user_id=user_1.id,
        account_id=account.id,
        type=NotificationType.COMPLETE_WORKFLOW,
    )
    notification_2 = Notification.objects.get(
        user_id=user_2.id,
        account_id=account.id,
        type=NotificationType.COMPLETE_WORKFLOW,
    )
    assert send_notification_mock.call_count == 2
    send_notification_mock.assert_has_calls(
        [
            mocker.call(
                logging=logging,
                logo_lg=None,
                user_id=user_1.id,
                user_email=user_1.email,
                account_id=account.id,
                notification=notification_1,
                method_name=NotificationMethod.complete_workflow,
                workflow_id=workflow.id,
                workflow_name=workflow.name,
                link=link,
                sync=True,
            ),
            mocker.call(
                logging=logging,
                logo_lg=None,
                user_id=user_2.id,
                user_email=user_2.email,
                account_id=account.id,
                notification=notification_2,
                method_name=NotificationMethod.complete_workflow,
                workflow_id=workflow.id,
                workflow_name=workflow.name,
                link=link,
                sync=True,
            ),
        ],
        any_order=True,
    )


def test_send_completed_workflow__two_performers_on_different_tasks__ok(
    mocker,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    user_1 = create_test_not_admin(account=account)
    user_2 = create_test_admin(account=account)
    workflow = create_test_workflow(
        account_owner,
        tasks_count=2,
        active_task_number=2,
    )
    task_1 = workflow.tasks.get(number=1)
    task_1.performers.set([user_1])

    task_2 = workflow.tasks.get(number=2)
    task_2.performers.set([user_2])
    link = f'{settings.FRONTEND_URL}/workflows/{workflow.id}'
    logging = True
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_completed_workflow_notification(
        logging=logging,
        workflow_id=workflow.id,
    )

    # assert
    notification_1 = Notification.objects.get(
        user_id=user_1.id,
        account_id=account.id,
        type=NotificationType.COMPLETE_WORKFLOW,
    )
    notification_2 = Notification.objects.get(
        user_id=user_2.id,
        account_id=account.id,
        type=NotificationType.COMPLETE_WORKFLOW,
    )
    send_notification_mock.assert_has_calls(
        [
            mocker.call(
                logging=logging,
                logo_lg=None,
                user_id=user_1.id,
                user_email=user_1.email,
                account_id=account.id,
                notification=notification_1,
                method_name=NotificationMethod.complete_workflow,
                workflow_id=workflow.id,
                workflow_name=workflow.name,
                link=link,
                sync=True,
            ),
            mocker.call(
                logging=logging,
                logo_lg=None,
                user_id=user_2.id,
                user_email=user_2.email,
                account_id=account.id,
                notification=notification_2,
                method_name=NotificationMethod.complete_workflow,
                workflow_id=workflow.id,
                workflow_name=workflow.name,
                link=link,
                sync=True,
            ),
        ],
        any_order=True,
    )


def test_send_completed_workflow__performer_guest__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(
        account_owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.performers.clear()
    task.performers.add(guest)
    logging = True
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_completed_workflow_notification(
        logging=logging,
        workflow_id=workflow.id,
    )

    # assert
    assert not Notification.objects.filter(
        account_id=account.id,
        type=NotificationType.COMPLETE_WORKFLOW,
    ).exists()
    send_notification_mock.assert_not_called()


def test_send_completed_workflow__performer_group__ok(
    mocker,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    user_1 = create_test_admin(account=account)
    user_2 = create_test_not_admin(account=account)
    group = create_test_group(account, users=[user_1, user_2])
    workflow = create_test_workflow(
        account_owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.performers.clear()
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
    )
    link = f'{settings.FRONTEND_URL}/workflows/{workflow.id}'
    logging = False
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_completed_workflow_notification(
        logging=logging,
        workflow_id=workflow.id,
    )

    # assert
    notification_1 = Notification.objects.get(
        user_id=user_1.id,
        account_id=account.id,
        type=NotificationType.COMPLETE_WORKFLOW,
    )
    notification_2 = Notification.objects.get(
        user_id=user_2.id,
        account_id=account.id,
        type=NotificationType.COMPLETE_WORKFLOW,
    )
    assert send_notification_mock.call_count == 2
    send_notification_mock.assert_has_calls(
        [
            mocker.call(
                logging=logging,
                logo_lg=None,
                user_id=user_1.id,
                user_email=user_1.email,
                account_id=account.id,
                notification=notification_1,
                method_name=NotificationMethod.complete_workflow,
                workflow_id=workflow.id,
                workflow_name=workflow.name,
                link=link,
                sync=True,
            ),
            mocker.call(
                logging=logging,
                logo_lg=None,
                user_id=user_2.id,
                user_email=user_2.email,
                account_id=account.id,
                notification=notification_2,
                method_name=NotificationMethod.complete_workflow,
                workflow_id=workflow.id,
                workflow_name=workflow.name,
                link=link,
                sync=True,
            ),
        ],
        any_order=True,
    )
