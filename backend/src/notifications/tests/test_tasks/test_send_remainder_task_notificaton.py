import pytest
from django.conf import settings

from src.notifications.services.push import PushNotificationService
from src.notifications.tasks import _send_reminder_task_notification
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_workflow, create_test_template,
)

pytestmark = pytest.mark.django_db


def test_send_reminder_task__call_all_services__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        tasks_count=1,
        reminder_notification=True,
    )
    workflow = create_test_workflow(
        account_owner,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    link = f'{settings.FRONTEND_URL}/tasks'
    get_token_mock = mocker.patch(
        'src.authentication.services.guest_auth.GuestJWTAuthService.'
        'get_str_token',
    )
    send_email_mock = mocker.patch(
        'src.notifications.services.email.EmailService.send_task_reminder',
    )
    push_notification_service_init_mock = mocker.patch.object(
        PushNotificationService,
        attribute='__init__',
        return_value=None,
    )
    send_push_mock = mocker.patch(
        'src.notifications.services.push.'
        'PushNotificationService.send_task_reminder',
    )

    # act
    _send_reminder_task_notification()

    # assert
    send_email_mock.assert_called_once_with(
        link=link,
        task_id=task.id,
        token=None,
        user_id=account_owner.id,
        user_email=account_owner.email,
        user_first_name=account_owner.first_name,
        user_type=account_owner.type,
        count=1,
        sync=True,
    )
    get_token_mock.assert_not_called()
    push_notification_service_init_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )
    send_push_mock.assert_called_once_with(
        link=link,
        task_id=task.id,
        token=None,
        user_id=account_owner.id,
        user_email=account_owner.email,
        user_first_name=account_owner.first_name,
        user_type=account_owner.type,
        count=1,
        sync=True,
    )
