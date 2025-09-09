import pytest
from datetime import timedelta
from django.utils import timezone
from pneumatic_backend.notifications.tasks import send_new_task_notification
from pneumatic_backend.notifications.enums import NotificationMethod
from pneumatic_backend.notifications.services.push import (
    PushNotificationService
)


pytestmark = pytest.mark.django_db


def test_send_new_task_notification__call_services__ok(mocker):

    # arrange
    logging = True
    account_logo = 'https://photo.com/logo.jpg'
    wf_starter_photo = 'https://photo.com/my-photo.jpg'
    wf_starter_name = 'Mr. Credo'
    user_email = 'test@test.test'
    is_subscriber = True
    account_id = 123
    user_id = 123123
    template_name = 'Template name'
    workflow_name = 'Workflow name'
    date_now = timezone.now()
    task_id = 123
    task_name = 'Task name'
    due_date = date_now + timedelta(days=1)
    due_date_timestamp = due_date.timestamp()
    task_description = '**Text** 123'

    html_description = '<b>Text</b>'
    convert_text_to_html_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks.'
        'convert_text_to_html',
        return_value=html_description
    )
    text_description = 'Text'
    clear_markdown_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks.'
        'MarkdownService.clear',
        return_value=text_description
    )
    formatted_date = '15 days 6 hours 23 minutes'
    mocker.patch(
        'pneumatic_backend.notifications.tasks.'
        'timezone.now',
        return_value=date_now
    )
    get_duration_format_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks.'
        'get_duration_format',
        return_value=formatted_date
    )
    push_notification_service_mock = mocker.patch.object(
        PushNotificationService,
        attribute='__init__',
        return_value=None
    )
    push_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.push.'
        'PushNotificationService.send_new_task'
    )
    email_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService.send_new_task'
    )
    mocker.patch(
        'pneumatic_backend.notifications.tasks.get_task_data',
        return_value={'id': task_id}
    )

    # act
    send_new_task_notification(
        logging=logging,
        account_id=account_id,
        logo_lg=account_logo,
        recipients=[(user_id, user_email, is_subscriber)],
        task_id=task_id,
        task_name=task_name,
        task_description=task_description,
        workflow_name=workflow_name,
        template_name=template_name,
        workflow_starter_name=wf_starter_name,
        workflow_starter_photo=wf_starter_photo,
        due_date_timestamp=due_date_timestamp,
        is_returned=False
    )

    # assert
    convert_text_to_html_mock.assert_called_once_with(text=task_description)
    clear_markdown_mock.assert_called_once_with(text=task_description)
    get_duration_format_mock.assert_called_once_with(
        duration=due_date - date_now
    )
    push_notification_service_mock.assert_called_once_with(
        logging=logging,
        account_id=account_id,
        logo_lg=account_logo,
    )
    push_notification_mock.assert_called_once_with(
        task_data={'id': task_id},
        task_id=task_id,
        task_name=task_name,
        workflow_name=workflow_name,
        user_id=user_id,
        sync=True,
        user_email=user_email,
        wf_starter_name=wf_starter_name,
        wf_starter_photo=wf_starter_photo,
        template_name=template_name,
        html_description=html_description,
        text_description=text_description,
        due_in=formatted_date,
        overdue=None
    )
    email_notification_mock.assert_called_once_with(
        task_data={'id': task_id},
        task_id=task_id,
        task_name=task_name,
        workflow_name=workflow_name,
        user_id=user_id,
        sync=True,
        user_email=user_email,
        wf_starter_name=wf_starter_name,
        wf_starter_photo=wf_starter_photo,
        template_name=template_name,
        html_description=html_description,
        text_description=text_description,
        due_in=formatted_date,
        overdue=None
    )


def test_send_new_task_notification__external_workflow__ok(api_client, mocker):

    # arrange
    logging = True
    account_logo = 'https://photo.com/logo.jpg'
    wf_starter_photo = None
    wf_starter_name = None
    user_email = 'test@test.test'
    is_subscriber = True
    user_id = 123123
    account_id = 123
    template_name = 'Template name'
    workflow_name = 'Workflow name'

    task_id = 123
    task_name = 'Task name'
    due_date_timestamp = None
    task_description = '**Text** 123'
    html_description = '<b>Text</b>'
    mocker.patch(
        'pneumatic_backend.notifications.tasks.'
        'convert_text_to_html',
        return_value=html_description
    )
    text_description = 'Text'
    mocker.patch(
        'pneumatic_backend.notifications.tasks.'
        'MarkdownService.clear',
        return_value=text_description
    )
    formatted_date = '15 days 6 hours 23 minutes'
    now_date = timezone.now()
    mocker.patch(
        'pneumatic_backend.notifications.tasks.'
        'timezone.now',
        return_value=now_date
    )
    mocker.patch(
        'pneumatic_backend.notifications.tasks.'
        'get_duration_format',
        return_value=formatted_date
    )
    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
    )
    mocker.patch(
        'pneumatic_backend.notifications.tasks.get_task_data',
        return_value={'id': task_id}
    )

    # act
    send_new_task_notification(
        logging=logging,
        account_id=account_id,
        recipients=[(user_id, user_email, is_subscriber)],
        task_id=task_id,
        task_name=task_name,
        task_description=task_description,
        workflow_name=workflow_name,
        template_name=template_name,
        workflow_starter_name=wf_starter_name,
        workflow_starter_photo=wf_starter_photo,
        due_date_timestamp=due_date_timestamp,
        logo_lg=account_logo,
        is_returned=False
    )

    # assert
    assert send_notification_mock.call_count == 2
    send_notification_mock.assert_has_calls([
        mocker.call(
            method_name=NotificationMethod.new_task_websocket,
            user_id=user_id,
            user_email=user_email,
            account_id=account_id,
            task_data={'id': task_id},
            sync=True
        ),
        mocker.call(
            logging=True,
            account_id=account_id,
            method_name=NotificationMethod.new_task,
            user_id=user_id,
            user_email=user_email,
            wf_starter_name='External User',
            wf_starter_photo=None,
            logo_lg=account_logo,
            template_name=template_name,
            workflow_name=workflow_name,
            task_id=task_id,
            task_name=task_name,
            task_data={'id': task_id},
            html_description=html_description,
            text_description=text_description,
            due_in=None,
            overdue=None,
            sync=True
        )
    ])


def test_send_new_task_notification__is_returned__call_services(mocker):

    # arrange
    logging = True
    account_logo = 'https://photo.com/logo.jpg'
    wf_starter_photo = 'https://photo.com/my-photo.jpg'
    wf_starter_name = 'Mr. Credo'
    user_email = 'test@test.test'
    is_subscriber = True
    user_id = 123123
    account_id = 123
    template_name = 'Template name'
    workflow_name = 'Workflow name'

    task_id = 123
    task_name = 'Task name'
    due_date = timezone.now() + timedelta(days=1)
    due_date_timestamp = due_date.timestamp()
    task_description = '**Text** 123'

    html_description = '<b>Text</b>'
    convert_text_to_html_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks.'
        'convert_text_to_html',
        return_value=html_description
    )
    text_description = 'Text'
    clear_markdown_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks.'
        'MarkdownService.clear',
        return_value=text_description
    )
    formatted_date = '15 days 6 hours 23 minutes'
    now_date = timezone.now()
    mocker.patch(
        'pneumatic_backend.notifications.tasks.'
        'timezone.now',
        return_value=now_date
    )
    get_duration_format_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks.'
        'get_duration_format',
        return_value=formatted_date
    )
    push_notification_service_mock = mocker.patch.object(
        PushNotificationService,
        attribute='__init__',
        return_value=None
    )
    push_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.push.'
        'PushNotificationService.send_returned_task'
    )
    email_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService.send_returned_task'
    )
    websocket_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_new_task_websocket'
    )
    mocker.patch(
        'pneumatic_backend.notifications.tasks.get_task_data',
        return_value={'id': task_id}
    )

    # act
    send_new_task_notification(
        logging=logging,
        account_id=account_id,
        logo_lg=account_logo,
        recipients=[(user_id, user_email, is_subscriber)],
        task_id=task_id,
        task_name=task_name,
        task_description=task_description,
        workflow_name=workflow_name,
        template_name=template_name,
        workflow_starter_name=wf_starter_name,
        workflow_starter_photo=wf_starter_photo,
        due_date_timestamp=due_date_timestamp,
        is_returned=True
    )

    # assert
    convert_text_to_html_mock.assert_called_once_with(text=task_description)
    clear_markdown_mock.assert_called_once_with(text=task_description)
    get_duration_format_mock.assert_called_once_with(
        duration=due_date - now_date
    )
    push_notification_service_mock.assert_called_once_with(
        logging=logging,
        account_id=account_id,
        logo_lg=account_logo,
    )
    push_notification_mock.assert_called_once_with(
        task_data={'id': task_id},
        task_id=task_id,
        task_name=task_name,
        workflow_name=workflow_name,
        user_id=user_id,
        sync=True,
        user_email=user_email,
        wf_starter_name=wf_starter_name,
        wf_starter_photo=wf_starter_photo,
        template_name=template_name,
        html_description=html_description,
        text_description=text_description,
        due_in=formatted_date,
        overdue=None
    )
    email_notification_mock.assert_called_once_with(
        task_data={'id': task_id},
        task_id=task_id,
        task_name=task_name,
        workflow_name=workflow_name,
        user_id=user_id,
        sync=True,
        user_email=user_email,
        wf_starter_name=wf_starter_name,
        wf_starter_photo=wf_starter_photo,
        template_name=template_name,
        html_description=html_description,
        text_description=text_description,
        due_in=formatted_date,
        overdue=None
    )
    websocket_notification_mock.assert_called_once_with(
        task_data={'id': task_id},
        user_id=user_id,
        sync=True,
        user_email=user_email
    )


def test_send_new_task_notification__is_returned__ok(mocker):

    # arrange
    logging = True
    account_logo = None
    wf_starter_photo = None
    wf_starter_name = 'Mr. Credo'
    account_id = 132
    user_1_email = 'test_1@test.test'
    is_subscriber_1 = True
    user_1_id = 123
    user_2_email = 'test_2@test.test'
    is_subscriber_2 = True
    user_2_id = 546
    template_name = 'Template name'
    workflow_name = 'Workflow name'

    task_id = 123
    task_name = 'Task name'
    due_date_timestamp = None
    task_description = ''

    convert_text_to_html_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks.'
        'convert_text_to_html'
    )
    clear_markdown_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks.'
        'MarkdownService.clear'
    )
    get_duration_format_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks.'
        'get_duration_format'
    )
    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
    )
    mocker.patch(
        'pneumatic_backend.notifications.tasks.get_task_data',
        return_value={'id': task_id}
    )

    # act
    send_new_task_notification(
        logging=logging,
        account_id=account_id,
        recipients=[
            (user_1_id, user_1_email, is_subscriber_1),
            (user_2_id, user_2_email, is_subscriber_2)
        ],
        task_id=task_id,
        task_name=task_name,
        task_description=task_description,
        workflow_name=workflow_name,
        template_name=template_name,
        workflow_starter_name=wf_starter_name,
        workflow_starter_photo=wf_starter_photo,
        due_date_timestamp=due_date_timestamp,
        logo_lg=account_logo,
        is_returned=False
    )

    # assert
    convert_text_to_html_mock.assert_not_called()
    clear_markdown_mock.assert_not_called()
    get_duration_format_mock.assert_not_called()
    send_notification_mock.has_calls(
        mocker.call(
            logging=logging,
            account_id=account_id,
            method_name=NotificationMethod.returned_task,
            user_id=user_1_id,
            user_email=user_1_email,
            wf_starter_name=wf_starter_name,
            wf_starter_photo=wf_starter_photo,
            logo_lg=account_logo,
            template_name=template_name,
            workflow_name=workflow_name,
            task_id=task_id,
            task_name=task_name,
            task_data={'id': task_id},
            html_description=None,
            text_description=None,
            due_in=None,
            overdue=None,
            sync=True,
        ),
        mocker.call(
            logging=logging,
            account_id=account_id,
            method_name=NotificationMethod.returned_task,
            user_id=user_2_id,
            user_email=user_2_email,
            wf_starter_name=wf_starter_name,
            wf_starter_photo=wf_starter_photo,
            logo_lg=account_logo,
            template_name=template_name,
            workflow_name=workflow_name,
            task_id=task_id,
            task_name=task_name,
            task_data={'id': task_id},
            html_description=None,
            text_description=None,
            due_in=None,
            overdue=None,
            sync=True
        )
    )
