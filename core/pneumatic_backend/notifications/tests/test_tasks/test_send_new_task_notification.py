import pytest
from datetime import timedelta
from django.utils import timezone
from pneumatic_backend.notifications.tasks import _send_new_task_notification
from pneumatic_backend.notifications.enums import NotificationMethod

pytestmark = pytest.mark.django_db


def test_send_new_task_notification__call_services(mocker):

    # arrange
    logging = True
    account_logo = 'https://photo.com/logo.jpg'
    wf_starter_photo = 'https://photo.com/my-photo.jpg'
    wf_starter_name = 'Mr. Credo'
    user_email = 'test@test.test'
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
    push_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.push.'
        'PushNotificationService.send_new_task'
    )
    email_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService.send_new_task'
    )

    # act
    _send_new_task_notification(
        logging=logging,
        recipients=[(user_id, user_email)],
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
    convert_text_to_html_mock.assert_called_once_with(text=task_description)
    clear_markdown_mock.assert_called_once_with(text=task_description)
    get_duration_format_mock.assert_called_once_with(
        duration=due_date - date_now
    )
    push_kwargs = {
        'sync': True,
        'user_email': user_email,
        'wf_starter_name': wf_starter_name,
        'wf_starter_photo': wf_starter_photo,
        'logo_lg': account_logo,
        'template_name': template_name,
        'html_description': html_description,
        'text_description': text_description,
        'due_in': formatted_date,
        'overdue': None
    }
    push_notification_mock.assert_called_once_with(
        task_id=task_id,
        task_name=task_name,
        workflow_name=workflow_name,
        user_id=user_id,
        **push_kwargs
    )
    email_kwargs = {
        'text_description': text_description,
        'sync': True
    }
    email_notification_mock.assert_called_once_with(
        user_id=user_id,
        user_email=user_email,
        logo_lg=account_logo,
        template_name=template_name,
        workflow_name=workflow_name,
        task_id=task_id,
        task_name=task_name,
        html_description=html_description,
        wf_starter_name=wf_starter_name,
        wf_starter_photo=wf_starter_photo,
        due_in=formatted_date,
        overdue=None,
        **email_kwargs
    )


def test_send_new_task_notification__external_workflow__ok(api_client, mocker):

    # arrange
    logging = True
    account_logo = 'https://photo.com/logo.jpg'
    wf_starter_photo = None
    wf_starter_name = None
    user_email = 'test@test.test'
    user_id = 123123
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

    # act
    _send_new_task_notification(
        logging=logging,
        recipients=[(user_id, user_email)],
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
    send_notification_mock.assert_called_once_with(
        logging=True,
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
        html_description=html_description,
        text_description=text_description,
        due_in=None,
        overdue=None,
        sync=True
    )


def test_send_new_task_notification__is_returned__call_services(mocker):

    # arrange
    logging = True
    account_logo = 'https://photo.com/logo.jpg'
    wf_starter_photo = 'https://photo.com/my-photo.jpg'
    wf_starter_name = 'Mr. Credo'
    user_email = 'test@test.test'
    user_id = 123123
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
    push_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.push.'
        'PushNotificationService.send_returned_task'
    )
    email_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService.send_returned_task'
    )

    # act
    _send_new_task_notification(
        logging=logging,
        recipients=[(user_id, user_email)],
        task_id=task_id,
        task_name=task_name,
        task_description=task_description,
        workflow_name=workflow_name,
        template_name=template_name,
        workflow_starter_name=wf_starter_name,
        workflow_starter_photo=wf_starter_photo,
        due_date_timestamp=due_date_timestamp,
        logo_lg=account_logo,
        is_returned=True
    )

    # assert
    convert_text_to_html_mock.assert_called_once_with(text=task_description)
    clear_markdown_mock.assert_called_once_with(text=task_description)
    get_duration_format_mock.assert_called_once_with(
        duration=due_date - now_date
    )
    push_kwargs = {
        'sync': True,
        'user_email': user_email,
        'wf_starter_name': wf_starter_name,
        'wf_starter_photo': wf_starter_photo,
        'logo_lg': account_logo,
        'template_name': template_name,
        'text_description': text_description,
        'html_description': html_description,
        'due_in': formatted_date,
        'overdue': None
    }
    push_notification_mock.assert_called_once_with(
        task_id=task_id,
        task_name=task_name,
        workflow_name=workflow_name,
        user_id=user_id,
        **push_kwargs
    )
    email_kwargs = {
        'sync': True
    }
    email_notification_mock.assert_called_once_with(
        user_id=user_id,
        user_email=user_email,
        logo_lg=account_logo,
        template_name=template_name,
        workflow_name=workflow_name,
        task_id=task_id,
        task_name=task_name,
        html_description=html_description,
        text_description=text_description,
        wf_starter_name=wf_starter_name,
        wf_starter_photo=wf_starter_photo,
        due_in=formatted_date,
        overdue=None,
        **email_kwargs
    )


def test_send_new_task_notification__is_returned__ok(mocker):

    # arrange
    logging = True
    account_logo = None
    wf_starter_photo = None
    wf_starter_name = 'Mr. Credo'
    user_1_email = 'test_1@test.test'
    user_1_id = 123
    user_2_email = 'test_2@test.test'
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

    # act
    _send_new_task_notification(
        logging=logging,
        recipients=[(user_1_id, user_1_email), (user_2_id, user_2_email)],
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
            html_description=None,
            text_description=None,
            due_in=None,
            overdue=None,
            sync=True,
        ),
        mocker.call(
            logging=logging,
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
            html_description=None,
            text_description=None,
            due_in=None,
            overdue=None,
            sync=True
        )
    )
