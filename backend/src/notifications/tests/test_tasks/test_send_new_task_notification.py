from datetime import timedelta

import pytest
from django.utils import timezone

from src.notifications.enums import NotificationMethod
from src.notifications.services.push import (
    PushNotificationService,
)
from src.notifications.tasks import _send_new_task_notification
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_send_new_task_notification__external_workflow__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    template = create_test_template(user=owner, tasks_count=1)
    workflow = create_test_workflow(user=owner, template=template)
    task = workflow.tasks.get(number=1)
    task.description = 'some text'
    task.save()
    html_description = '<b>Text</b>'
    mocker.patch(
        'src.notifications.tasks.'
        'convert_text_to_html',
        return_value=html_description,
    )
    text_description = 'Text'
    mocker.patch(
        'src.notifications.tasks.'
        'MarkdownService.clear',
        return_value=text_description,
    )
    formatted_date = '15 days 6 hours 23 minutes'
    now_date = timezone.now()
    mocker.patch(
        'src.notifications.tasks.'
        'timezone.now',
        return_value=now_date,
    )
    mocker.patch(
        'src.notifications.tasks.'
        'get_duration_format',
        return_value=formatted_date,
    )
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )
    task_data = {'id': task.id}
    mocker.patch(
        'src.processes.models.workflows.'
        'task.Task.get_data_for_list',
        return_value=task_data,
    )
    recipients = [
        (user.id, user.email, True),
    ]

    # act
    _send_new_task_notification(
        logging=False,
        account_id=account.id,
        logo_lg=None,
        recipients=recipients,
        task_id=task.id,
        task_name=task.name,
        task_description=task.description,
        workflow_name=workflow.name,
        template_name=template.name,
        workflow_starter_name=owner.name,
        workflow_starter_photo=owner.photo,
        due_date_timestamp=None,
        is_returned=False,
    )

    # assert
    link = f'http://localhost/tasks/{task.id}'
    send_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        method_name=NotificationMethod.new_task,
        user_id=user.id,
        user_email=user.email,
        wf_starter_name=owner.name,
        wf_starter_photo=owner.photo,
        logo_lg=None,
        template_name=template.name,
        workflow_name=workflow.name,
        task_id=task.id,
        task_name=task.name,
        task_data=task_data,
        html_description=html_description,
        text_description=text_description,
        due_in=None,
        overdue=None,
        link=link,
        sync=True,
    )


def test_send_new_task_notification__is_returned_true__call_services(mocker):

    # arrange
    logging = True
    logo_lg = 'https://photo.com/logo.jpg'
    photo = 'https://photo.com/my-photo.jpg'
    task_description = '**Text** 123'

    html_description = '<b>Text</b>'
    account = create_test_account(
        logo_lg=logo_lg,
        log_api_requests=logging,
    )
    owner = create_test_owner(account=account, photo=photo)
    user = create_test_admin(account=account)
    template = create_test_template(user=owner, tasks_count=1)
    workflow = create_test_workflow(user=owner, template=template)
    task = workflow.tasks.get(number=1)
    now_date = timezone.now()
    task.due_date = now_date + timedelta(days=1)
    task.description = task_description
    due_date_timestamp = task.due_date.timestamp()
    task.save()

    convert_text_to_html_mock = mocker.patch(
        'src.notifications.tasks.'
        'convert_text_to_html',
        return_value=html_description,
    )
    text_description = 'Text'
    clear_markdown_mock = mocker.patch(
        'src.notifications.tasks.'
        'MarkdownService.clear',
        return_value=text_description,
    )
    formatted_date = '15 days 6 hours 23 minutes'
    mocker.patch(
        'src.notifications.tasks.'
        'timezone.now',
        return_value=now_date,
    )
    get_duration_format_mock = mocker.patch(
        'src.notifications.tasks.'
        'get_duration_format',
        return_value=formatted_date,
    )
    push_notification_service_mock = mocker.patch.object(
        PushNotificationService,
        attribute='__init__',
        return_value=None,
    )
    push_notification_mock = mocker.patch(
        'src.notifications.services.push.'
        'PushNotificationService.send_returned_task',
    )
    email_notification_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService.send_returned_task',
    )
    task_data = {'id': task.id}
    mocker.patch(
        'src.processes.models.workflows.'
        'task.Task.get_data_for_list',
        return_value=task_data,
    )
    recipients = [
        (user.id, user.email, True),
    ]
    # act
    _send_new_task_notification(
        logging=logging,
        account_id=account.id,
        logo_lg=logo_lg,
        recipients=recipients,
        task_id=task.id,
        task_name=task.name,
        task_description=task.description,
        workflow_name=workflow.name,
        template_name=template.name,
        workflow_starter_name=owner.name,
        workflow_starter_photo=owner.photo,
        due_date_timestamp=due_date_timestamp,
        is_returned=True,
    )

    # assert
    convert_text_to_html_mock.assert_called_once_with(text=task_description)
    clear_markdown_mock.assert_called_once_with(text=task_description)
    get_duration_format_mock.assert_called_once_with(
        duration=task.due_date - now_date,
    )
    push_notification_service_mock.assert_called_once_with(
        logging=logging,
        account_id=account.id,
        logo_lg=logo_lg,
    )
    link = f'http://localhost/tasks/{task.id}'
    push_notification_mock.assert_called_once_with(
        task_data=task_data,
        task_id=task.id,
        task_name=task.name,
        workflow_name=workflow.name,
        user_id=user.id,
        sync=True,
        user_email=user.email,
        wf_starter_name=owner.name,
        wf_starter_photo=owner.photo,
        template_name=template.name,
        html_description=html_description,
        text_description=text_description,
        due_in=formatted_date,
        overdue=None,
        link=link,
    )
    email_notification_mock.assert_called_once_with(
        task_data=task_data,
        task_id=task.id,
        task_name=task.name,
        workflow_name=workflow.name,
        user_id=user.id,
        sync=True,
        user_email=user.email,
        wf_starter_name=owner.name,
        wf_starter_photo=owner.photo,
        template_name=template.name,
        html_description=html_description,
        text_description=text_description,
        due_in=formatted_date,
        overdue=None,
        link=link,
    )


def test_send_new_task_notification__is_returned_false__call_services(mocker):

    # arrange
    logging = True
    logo_lg = 'https://photo.com/logo.jpg'
    photo = 'https://photo.com/my-photo.jpg'
    task_description = '**Text** 123'

    html_description = '<b>Text</b>'
    account = create_test_account(
        logo_lg=logo_lg,
        log_api_requests=logging,
    )
    owner = create_test_owner(account=account, photo=photo)
    user = create_test_admin(account=account)
    template = create_test_template(user=owner, tasks_count=1)
    workflow = create_test_workflow(user=owner, template=template)
    task = workflow.tasks.get(number=1)
    now_date = timezone.now()
    task.due_date = now_date + timedelta(days=1)
    task.description = task_description
    due_date_timestamp = task.due_date.timestamp()
    task.save()

    convert_text_to_html_mock = mocker.patch(
        'src.notifications.tasks.'
        'convert_text_to_html',
        return_value=html_description,
    )
    text_description = 'Text'
    clear_markdown_mock = mocker.patch(
        'src.notifications.tasks.'
        'MarkdownService.clear',
        return_value=text_description,
    )
    formatted_date = '15 days 6 hours 23 minutes'
    mocker.patch(
        'src.notifications.tasks.'
        'timezone.now',
        return_value=now_date,
    )
    get_duration_format_mock = mocker.patch(
        'src.notifications.tasks.'
        'get_duration_format',
        return_value=formatted_date,
    )
    push_notification_service_mock = mocker.patch.object(
        PushNotificationService,
        attribute='__init__',
        return_value=None,
    )
    push_notification_mock = mocker.patch(
        'src.notifications.services.push.'
        'PushNotificationService.send_new_task',
    )
    email_notification_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService.send_new_task',
    )
    task_data = {'id': task.id}
    mocker.patch(
        'src.processes.models.workflows.'
        'task.Task.get_data_for_list',
        return_value=task_data,
    )
    recipients = [
        (user.id, user.email, True),
    ]

    # act
    _send_new_task_notification(
        logging=logging,
        account_id=account.id,
        logo_lg=logo_lg,
        recipients=recipients,
        task_id=task.id,
        task_name=task.name,
        task_description=task.description,
        workflow_name=workflow.name,
        template_name=template.name,
        workflow_starter_name=owner.name,
        workflow_starter_photo=owner.photo,
        due_date_timestamp=due_date_timestamp,
        is_returned=False,
    )

    # assert
    convert_text_to_html_mock.assert_called_once_with(text=task_description)
    clear_markdown_mock.assert_called_once_with(text=task_description)
    get_duration_format_mock.assert_called_once_with(
        duration=task.due_date - now_date,
    )
    push_notification_service_mock.assert_called_once_with(
        logging=logging,
        account_id=account.id,
        logo_lg=logo_lg,
    )
    link = f'http://localhost/tasks/{task.id}'
    push_notification_mock.assert_called_once_with(
        task_data=task_data,
        task_id=task.id,
        task_name=task.name,
        workflow_name=workflow.name,
        user_id=user.id,
        sync=True,
        user_email=user.email,
        wf_starter_name=owner.name,
        wf_starter_photo=owner.photo,
        template_name=template.name,
        html_description=html_description,
        text_description=text_description,
        due_in=formatted_date,
        overdue=None,
        link=link,
    )
    email_notification_mock.assert_called_once_with(
        task_data=task_data,
        task_id=task.id,
        task_name=task.name,
        workflow_name=workflow.name,
        user_id=user.id,
        sync=True,
        user_email=user.email,
        wf_starter_name=owner.name,
        wf_starter_photo=owner.photo,
        template_name=template.name,
        html_description=html_description,
        text_description=text_description,
        due_in=formatted_date,
        overdue=None,
        link=link,
    )


@pytest.mark.parametrize(
    'value', (
        (True, NotificationMethod.returned_task),
        (False, NotificationMethod.new_task),
    ),
)
def test_send_new_task_notification__ok(mocker, value):

    # arrange
    is_returned, method_name = value
    logging = True
    account_logo = None
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    template = create_test_template(user=owner, tasks_count=1)
    workflow = create_test_workflow(user=owner, template=template)
    task = workflow.tasks.get(number=1)
    convert_text_to_html_mock = mocker.patch(
        'src.notifications.tasks.'
        'convert_text_to_html',
    )
    clear_markdown_mock = mocker.patch(
        'src.notifications.tasks.'
        'MarkdownService.clear',
    )
    get_duration_format_mock = mocker.patch(
        'src.notifications.tasks.'
        'get_duration_format',
    )
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )
    task_data = {'id': task.id}
    mocker.patch(
        'src.processes.models.workflows.'
        'task.Task.get_data_for_list',
        return_value=task_data,
    )
    recipients = [
        (owner.id, owner.email, True),
        (user.id, user.email, True),
    ]

    # act
    _send_new_task_notification(
        logging=logging,
        account_id=account.id,
        recipients=recipients,
        task_id=task.id,
        task_name=task.name,
        task_description=task.description,
        workflow_name=workflow.name,
        template_name=template.name,
        workflow_starter_name=owner.name,
        workflow_starter_photo=owner.photo,
        due_date_timestamp=None,
        logo_lg=account_logo,
        is_returned=is_returned,
    )

    # assert
    convert_text_to_html_mock.assert_not_called()
    clear_markdown_mock.assert_not_called()
    get_duration_format_mock.assert_not_called()
    link = f'http://localhost/tasks/{task.id}'
    send_notification_mock.assert_has_calls(
        [
            mocker.call(
                logging=logging,
                account_id=account.id,
                method_name=method_name,
                user_id=owner.id,
                user_email=owner.email,
                wf_starter_name=owner.name,
                wf_starter_photo=owner.photo,
                logo_lg=account_logo,
                template_name=template.name,
                workflow_name=workflow.name,
                task_id=task.id,
                task_name=task.name,
                task_data=task_data,
                html_description=None,
                text_description=None,
                due_in=None,
                overdue=None,
                link=link,
                sync=True,
            ),
            mocker.call(
                logging=logging,
                account_id=account.id,
                method_name=method_name,
                user_id=user.id,
                user_email=user.email,
                wf_starter_name=owner.name,
                wf_starter_photo=owner.photo,
                logo_lg=account_logo,
                template_name=template.name,
                workflow_name=workflow.name,
                task_id=task.id,
                task_name=task.name,
                task_data=task_data,
                html_description=None,
                text_description=None,
                due_in=None,
                overdue=None,
                link=link,
                sync=True,
            ),
        ],
    )


def test_send_new_task_notification__unsubscribed__not_send(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(
        account=account,
        is_new_tasks_subscriber=False,
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    html_description = '<b>Text</b>'
    mocker.patch(
        'src.notifications.tasks.'
        'convert_text_to_html',
        return_value=html_description,
    )
    text_description = 'Text'
    mocker.patch(
        'src.notifications.tasks.'
        'MarkdownService.clear',
        return_value=text_description,
    )
    formatted_date = '15 days 6 hours 23 minutes'
    now_date = timezone.now()
    mocker.patch(
        'src.notifications.tasks.'
        'timezone.now',
        return_value=now_date,
    )
    mocker.patch(
        'src.notifications.tasks.'
        'get_duration_format',
        return_value=formatted_date,
    )
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )
    task_data = {'id': task.id}
    mocker.patch(
        'src.processes.models.workflows.'
        'task.Task.get_data_for_list',
        return_value=task_data,
    )
    recipients = [
        (user.id, user.email, user.is_new_tasks_subscriber),
    ]

    # act
    _send_new_task_notification(
        logging=False,
        account_id=account.id,
        logo_lg=None,
        recipients=recipients,
        task_id=task.id,
        task_name=task.name,
        task_description=task.description,
        workflow_name=workflow.name,
        template_name=workflow.template.name,
        workflow_starter_name=owner.name,
        workflow_starter_photo=owner.photo,
        due_date_timestamp=None,
        is_returned=False,
    )

    # assert
    send_notification_mock.assert_not_called()


def test_send_new_task_notification__task_data__ok(mocker):

    # arrange
    logging = True
    account_logo = None
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    template = create_test_template(user=owner, tasks_count=1)
    workflow = create_test_workflow(user=owner, template=template)
    task = workflow.tasks.get(number=1)
    convert_text_to_html_mock = mocker.patch(
        'src.notifications.tasks.'
        'convert_text_to_html',
    )
    clear_markdown_mock = mocker.patch(
        'src.notifications.tasks.'
        'MarkdownService.clear',
    )
    get_duration_format_mock = mocker.patch(
        'src.notifications.tasks.'
        'get_duration_format',
    )
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )
    task_data = {'id': task.id}
    get_data_for_list_mock = mocker.patch(
        'src.processes.models.workflows.'
        'task.Task.get_data_for_list',
    )

    # act
    _send_new_task_notification(
        logging=logging,
        account_id=account.id,
        recipients=[(user.id, user.email, True)],
        task_id=task.id,
        task_name=task.name,
        task_description=task.description,
        workflow_name=workflow.name,
        template_name=template.name,
        workflow_starter_name=owner.name,
        workflow_starter_photo=owner.photo,
        due_date_timestamp=None,
        logo_lg=account_logo,
        is_returned=False,
        task_data=task_data,
    )

    # assert
    convert_text_to_html_mock.assert_not_called()
    clear_markdown_mock.assert_not_called()
    get_duration_format_mock.assert_not_called()
    get_data_for_list_mock.assert_not_called()
    link = f'http://localhost/tasks/{task.id}'
    send_notification_mock.assert_called_once_with(
        logging=logging,
        account_id=account.id,
        method_name=NotificationMethod.new_task,
        user_id=user.id,
        user_email=user.email,
        wf_starter_name=owner.name,
        wf_starter_photo=owner.photo,
        logo_lg=account_logo,
        template_name=template.name,
        workflow_name=workflow.name,
        task_id=task.id,
        task_name=task.name,
        task_data=task_data,
        html_description=None,
        text_description=None,
        due_in=None,
        overdue=None,
        link=link,
        sync=True,
    )
