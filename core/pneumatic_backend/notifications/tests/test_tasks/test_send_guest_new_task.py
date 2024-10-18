import pytest
from datetime import timedelta
from pneumatic_backend.processes.tests.fixtures import (
    create_test_workflow,
    create_test_user,
    create_test_guest,
    create_test_account,
)
from pneumatic_backend.notifications.tasks import (
    _send_guest_new_task
)


pytestmark = pytest.mark.django_db


def test_send_guest_new_task__ok(mocker):

    # arrange
    logo_lg = 'https://site.com/logo-lg.jpg'
    account = create_test_account(logo_lg=logo_lg)
    user = create_test_user(account=account)
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.all().first()
    task.due_date = task.date_first_started + timedelta(hours=1)
    task.save(update_fields=['due_date'])
    token = '!@#@wqe1'
    send_email_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.EmailService'
        '.send_guest_new_task'
    )

    # act
    _send_guest_new_task(
        token=token,
        sender_name=user.get_full_name(),
        user_id=guest.id,
        user_email=guest.email,
        task_id=task.id,
        task_name=task.name,
        task_description=task.description,
        task_due_date=task.due_date,
        logo_lg=logo_lg,
    )

    # assert
    send_email_mock.assert_called_once_with(
        token=token,
        sender_name=user.get_full_name(),
        user_id=guest.id,
        user_email=guest.email,
        task_id=task.id,
        task_name=task.name,
        task_description=task.description,
        task_due_date=task.due_date,
        logo_lg=logo_lg,
    )
