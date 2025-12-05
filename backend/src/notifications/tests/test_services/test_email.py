from datetime import timedelta

import pytest
from django.conf import settings
from django.utils import timezone

from src.accounts.enums import UserType
from src.analysis.enums import MailoutType
from src.logs.enums import AccountEventStatus
from src.notifications import messages
from src.notifications.enums import (
    EmailProvider,
    EmailType,
    NotificationMethod,
    email_titles,
)
from src.notifications.services.email import (
    EmailService,
)
from src.notifications.services.exceptions import (
    NotificationServiceError,
)

pytestmark = pytest.mark.django_db


def test_send_email_via_client__ok(mocker):

    # arrange
    template_id = 1
    template_code = 'new_task'
    mocker.patch(
        'src.notifications.clients.customerio.cio_template_ids',
        {template_code: template_id},
    )
    api_key = '!@#'

    customerio_settings_mock = mocker.patch(
        'src.notifications.clients.customerio.settings',
    )
    customerio_settings_mock.CUSTOMERIO_TRANSACTIONAL_API_KEY = api_key

    settings_mock = mocker.patch(
        'src.notifications.services.email.settings',
    )
    settings_mock.CUSTOMERIO_TRANSACTIONAL_API_KEY = api_key
    settings_mock.EMAIL_PROVIDER = EmailProvider.CUSTOMERIO

    client_mock = mocker.Mock()
    api_client_mock = mocker.patch(
        'src.notifications.clients.customerio.APIClient',
        return_value=client_mock,
    )
    request_mock = mocker.Mock()
    send_email_request_mock = mocker.patch(
        'src.notifications.clients.customerio.SendEmailRequest',
        return_value=request_mock,
    )

    user_id = 1
    email = 'test@pneumatic.app'
    data = {'test': 'data'}
    create_account_log_mock = mocker.patch(
        'src.notifications.services.email.AccountLogService'
        '.email_message',
    )
    logo_lg = 'https://logo.jpg'
    logging = False
    title = 'Title test'
    account_id = 123

    service = EmailService(
        logo_lg=logo_lg,
        logging=logging,
        account_id=account_id,
    )

    # act
    service._send_email_via_client(
        title=title,
        user_id=user_id,
        user_email=email,
        template_code=template_code,
        data=data,
    )

    # assert
    api_client_mock.assert_called_once_with(api_key)

    send_email_request_mock.assert_called_once_with(
        to=email,
        transactional_message_id=template_id,
        message_data=data,
        identifiers={'id': user_id},
    )
    client_mock.send_email.assert_called_once_with(request_mock)
    create_account_log_mock.assert_not_called()


def test_send_email_via_client__enable_logging__ok(mocker):

    # arrange
    template_id = 1
    template_code = 'new_task'
    mocker.patch(
        'src.notifications.clients.customerio.cio_template_ids',
        {template_code: template_id},
    )
    api_key = '!@#'

    customerio_settings_mock = mocker.patch(
        'src.notifications.clients.customerio.settings',
    )
    customerio_settings_mock.CUSTOMERIO_TRANSACTIONAL_API_KEY = api_key

    settings_mock = mocker.patch(
        'src.notifications.services.email.settings',
    )
    settings_mock.CUSTOMERIO_TRANSACTIONAL_API_KEY = api_key
    settings_mock.EMAIL_PROVIDER = EmailProvider.CUSTOMERIO

    client_mock = mocker.Mock()
    api_client_mock = mocker.patch(
        'src.notifications.clients.customerio.APIClient',
        return_value=client_mock,
    )
    request_mock = mocker.Mock()
    send_email_request_mock = mocker.patch(
        'src.notifications.clients.customerio.SendEmailRequest',
        return_value=request_mock,
    )

    create_account_log_mock = mocker.patch(
        'src.notifications.services.email.AccountLogService'
        '.email_message',
    )
    user_id = 1
    email = 'test@pneumatic.app'
    data = {'test': 'data'}

    logo_lg = 'https://logo.jpg'
    logging = True
    title = 'Title test'
    account_id = 123

    service = EmailService(
        logo_lg=logo_lg,
        logging=logging,
        account_id=account_id,
    )

    # act
    service._send_email_via_client(
        title=title,
        user_id=user_id,
        user_email=email,
        template_code=template_code,
        data=data,
    )

    # assert
    api_client_mock.assert_called_once_with(api_key)
    send_email_request_mock.assert_called_once_with(
        to=email,
        transactional_message_id=template_id,
        message_data=data,
        identifiers={'id': user_id},
    )
    client_mock.send_email.assert_called_once_with(request_mock)
    create_account_log_mock.assert_called_once_with(
        title=f'Email to: {email}: {title}',
        request_data=data,
        account_id=account_id,
        status=AccountEventStatus.SUCCESS,
        contractor=EmailProvider.CUSTOMERIO,
    )


def test_send__dev_environment__console_print(mocker):

    # arrange
    fixed_now = timezone.now()
    mocker.patch(
        'src.notifications.services.email.timezone.now',
        return_value=fixed_now,
    )
    settings_mock = mocker.patch(
        'src.notifications.services.email.settings',
    )
    settings_mock.BACKEND_URL = settings.BACKEND_URL
    settings_mock.FRONTEND_URL = settings.FRONTEND_URL
    send_to_console_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send_email_to_console',
    )
    send_email_via_client_mock = mocker.patch(
        'src.notifications.services.email.EmailService.'
        '_send_email_via_client',
    )
    user_id = 1
    email = 'john@cena.com'
    data = {'some': 'data'}
    settings_mock.CONFIGURATION_CURRENT = settings.CONFIGURATION_DEV
    settings_mock.CONFIGURATION_DEV = settings.CONFIGURATION_DEV
    settings_mock.PROJECT_CONF = {'EMAIL': True}

    logo_lg = 'https://logo.jpg'
    logging = False
    title = 'Title test'
    account_id = 123

    service = EmailService(
        logo_lg=logo_lg,
        logging=logging,
        account_id=account_id,
    )

    # act
    service._send(
        title=title,
        user_id=user_id,
        user_email=email,
        template_code=EmailType.OVERDUE_TASK,
        method_name=NotificationMethod.overdue_task,
        data=data,
    )

    # assert
    send_to_console_mock.assert_called_with(
        user_email=email,
        template_code=EmailType.OVERDUE_TASK,
        data={'some': 'data'},
    )
    send_email_via_client_mock.assert_not_called()


def test_send__prod_environment__send_email(mocker):

    # arrange
    fixed_now = timezone.now()
    mocker.patch(
        'src.notifications.services.email.timezone.now',
        return_value=fixed_now,
    )
    settings_mock = mocker.patch(
        'src.notifications.services.email.settings',
    )
    settings_mock.BACKEND_URL = settings.BACKEND_URL
    settings_mock.FRONTEND_URL = settings.FRONTEND_URL
    send_to_console_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send_email_to_console',
    )
    send_email_via_client_mock = mocker.patch(
        'src.notifications.services.email.EmailService.'
        '_send_email_via_client',
    )
    user_id = 1
    email = 'john@cena.com'
    data = {'some': 'data'}
    settings_mock.CONFIGURATION_CURRENT = settings.CONFIGURATION_PROD
    settings_mock.CONFIGURATION_PROD = settings.CONFIGURATION_PROD
    settings_mock.PROJECT_CONF = {'EMAIL': True}
    logo_lg = 'https://logo.jpg'
    logging = False
    title = 'Title test'
    account_id = 123

    service = EmailService(
        logo_lg=logo_lg,
        logging=logging,
        account_id=account_id,
    )

    # act
    service._send(
        title=title,
        user_id=user_id,
        user_email=email,
        template_code=EmailType.OVERDUE_TASK,
        method_name=NotificationMethod.overdue_task,
        data=data,
    )

    # assert
    send_to_console_mock.assert_not_called()
    send_email_via_client_mock.assert_called_with(
        title=title,
        user_id=user_id,
        user_email=email,
        template_code=EmailType.OVERDUE_TASK,
        data={'some': 'data'},
    )


def test_send__not_allowed_method__raise_exception(mocker):

    # arrange
    mocker.patch(
        'src.notifications.services.email.'
        'EmailService.ALLOWED_METHODS',
        {NotificationMethod.new_task},
    )
    send_to_console_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send_email_to_console',
    )
    send_email_via_client_mock = mocker.patch(
        'src.notifications.services.email.EmailService.'
        '_send_email_via_client',
    )
    settings_mock = mocker.patch(
        'src.notifications.services.email.settings',
    )
    settings_mock.PROJECT_CONF = {'EMAIL': True}
    user_id = 1
    email = 'john@cena.com'
    data = {'some': 'data'}
    logo_lg = 'https://logo.jpg'
    logging = False
    title = 'Title test'
    account_id = 123

    service = EmailService(
        logo_lg=logo_lg,
        logging=logging,
        account_id=account_id,
    )

    # act
    with pytest.raises(NotificationServiceError) as ex:
        service._send(
            title=title,
            user_id=user_id,
            user_email=email,
            template_code=EmailType.OVERDUE_TASK,
            method_name=NotificationMethod.overdue_task,
            data=data,
        )

    # assert
    assert ex.value.message == (
        f'{NotificationMethod.overdue_task} is not allowed notification'
    )
    send_to_console_mock.assert_not_called()
    send_email_via_client_mock.assert_not_called()


def test_send__disable_email__skip(mocker):

    # arrange
    settings_mock = mocker.patch(
        'src.notifications.services.email.settings',
    )
    send_to_console_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send_email_to_console',
    )
    send_email_via_client_mock = mocker.patch(
        'src.notifications.services.email.EmailService.'
        '_send_email_via_client',
    )
    user_id = 1
    email = 'john@cena.com'
    data = {'some': 'data'}
    settings_mock.CONFIGURATION_CURRENT = settings.CONFIGURATION_PROD
    settings_mock.CONFIGURATION_PROD = settings.CONFIGURATION_PROD
    settings_mock.PROJECT_CONF = {'EMAIL': False}
    logo_lg = 'https://logo.jpg'
    logging = False
    title = 'Title test'
    account_id = 123

    service = EmailService(
        logo_lg=logo_lg,
        logging=logging,
        account_id=account_id,
    )

    # act
    service._send(
        title=title,
        user_id=user_id,
        user_email=email,
        template_code=EmailType.OVERDUE_TASK,
        method_name=NotificationMethod.overdue_task,
        data=data,
    )

    # assert
    send_to_console_mock.assert_not_called()
    send_email_via_client_mock.assert_not_called()


def test_send_overdue_task__type_user__ok(mocker):

    # arrange
    fixed_now = timezone.now()
    mocker.patch(
        'src.notifications.services.email.timezone.now',
        return_value=fixed_now,
    )
    send_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send',
    )
    user_id = 12
    task_id = 11
    task_name = 'task name'
    workflow_id = 1
    workflow_name = 'workflow name'
    workflow_starter_id = 11
    workflow_starter_first_name = 'first name'
    workflow_starter_last_name = 'last name'
    template_name = 'template'
    user_email = 'john@cena.com'
    user_type = UserType.USER
    logo_lg = 'https://site.com/logo-lg.jpg'
    logging = False
    account_id = 123

    service = EmailService(
        logo_lg=logo_lg,
        logging=logging,
        account_id=account_id,
    )

    # act
    service.send_overdue_task(
        user_id=user_id,
        user_type=user_type,
        task_id=task_id,
        user_email=user_email,
        task_name=task_name,
        workflow_id=workflow_id,
        workflow_name=workflow_name,
        workflow_starter_id=workflow_starter_id,
        workflow_starter_first_name=workflow_starter_first_name,
        workflow_starter_last_name=workflow_starter_last_name,
        template_name=template_name,
    )

    # assert
    send_mock.assert_called_once_with(
        title=str(messages.MSG_NF_0004),
        user_id=user_id,
        user_email=user_email,
        template_code=EmailType.OVERDUE_TASK,
        method_name=NotificationMethod.overdue_task,
        data={
            'title': email_titles[NotificationMethod.overdue_task],
            'template': template_name,
            'workflow_id': workflow_id,
            'workflow_name': workflow_name,
            'task_id': str(task_id),
            'task_name': task_name,
            'link': f'{settings.FRONTEND_URL}/tasks/{task_id}',
            'template_name': template_name,
            'workflow_starter_id': workflow_starter_id,
            'workflow_starter_first_name': workflow_starter_first_name,
            'workflow_starter_last_name': workflow_starter_last_name,
            'started_by': {
                'name': (
                    f'{workflow_starter_first_name} '
                    f'{workflow_starter_last_name}'
                ).strip(),
                'avatar': None,
            },
            'user_type': UserType.USER,
            'token': None,
            'logo_lg': logo_lg,
        },
    )


def test_send_overdue_task__type_guest__ok(mocker):

    # arrange
    fixed_now = timezone.now()
    mocker.patch(
        'src.notifications.services.email.timezone.now',
        return_value=fixed_now,
    )
    send_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send',
    )
    user_id = 12
    task_id = 11
    task_name = 'task name'
    workflow_id = 1
    workflow_name = 'workflow name'
    workflow_starter_id = 11
    workflow_starter_first_name = 'first name'
    workflow_starter_last_name = 'last name'
    template_name = 'template'
    user_email = 'john@cena.com'
    user_type = UserType.GUEST
    logo_lg = 'https://site.com/logo-lg.jpg'
    token = '!@#'
    logging = False
    account_id = 123

    service = EmailService(
        logo_lg=logo_lg,
        logging=logging,
        account_id=account_id,
    )

    # act
    service.send_overdue_task(
        user_id=user_id,
        user_type=user_type,
        task_id=task_id,
        user_email=user_email,
        task_name=task_name,
        workflow_id=workflow_id,
        workflow_name=workflow_name,
        workflow_starter_id=workflow_starter_id,
        workflow_starter_first_name=workflow_starter_first_name,
        workflow_starter_last_name=workflow_starter_last_name,
        template_name=template_name,
        token=token,
    )

    # assert
    send_mock.assert_called_once_with(
        title=str(messages.MSG_NF_0004),
        user_id=user_id,
        user_email=user_email,
        template_code=EmailType.OVERDUE_TASK,
        method_name=NotificationMethod.overdue_task,
        data={
            'title': email_titles[NotificationMethod.overdue_task],
            'template': template_name,
            'workflow_id': workflow_id,
            'workflow_name': workflow_name,
            'task_id': str(task_id),
            'task_name': task_name,
            'link': (
                f'{settings.FRONTEND_URL}/guest-task/{task_id}'
                f'?token={token}&utm_campaign=guestUser&utm_term={user_id}'
            ),
            'template_name': template_name,
            'workflow_starter_id': workflow_starter_id,
            'workflow_starter_first_name': workflow_starter_first_name,
            'workflow_starter_last_name': workflow_starter_last_name,
            'started_by': {
                'name': (
                    f'{workflow_starter_first_name} '
                    f'{workflow_starter_last_name}'
                ).strip(),
                'avatar': None,
            },
            'user_type': UserType.GUEST,
            'token': token,
            'logo_lg': logo_lg,
        },
    )


def test_send_guest_new_task__due_in__ok(mocker):

    # arrange
    fixed_now = timezone.now()
    mocker.patch(
        'src.notifications.services.email.timezone.now',
        return_value=fixed_now,
    )
    token = '!@#sadd1'
    sender_name = 'Joe'
    recipient_id = 1233
    user_email = 'guest@guest.guest'
    task_id = 11
    task_name = 'Task name'
    task_description = 'Some markdown description'
    duration = timedelta(hours=1)
    task_due_date = fixed_now + duration

    html_description = '<div>text</div>'
    html_service_mock = mocker.patch(
        'src.notifications.services.email.convert_text_to_html',
        return_value=html_description,
    )
    send_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send',
    )
    formatted_task_due_in = '1 hour'
    get_duration_format_mock = mocker.patch(
        'src.notifications.services.email.get_duration_format',
        return_value=formatted_task_due_in,
    )
    logo_lg = 'https://logo.jpg'
    logging = False
    account_id = 123

    service = EmailService(
        logo_lg=logo_lg,
        logging=logging,
        account_id=account_id,
    )

    # act
    service.send_guest_new_task(
        token=token,
        user_id=recipient_id,
        sender_name=sender_name,
        user_email=user_email,
        task_id=task_id,
        task_name=task_name,
        task_description=task_description,
        task_due_date=task_due_date,
    )

    # assert
    html_service_mock.assert_called_once_with(task_description)
    get_duration_format_mock.assert_called_once()
    task_link = (
        f'{settings.FRONTEND_URL}/guest-task/{task_id}'
        f'?token={token}&utm_campaign=guestUser&utm_term={recipient_id}'
    )
    title = (
        f'{sender_name} {email_titles[NotificationMethod.guest_new_task]} '
        f'{task_name} Task'
    )
    send_mock.assert_called_once_with(
        title=str(messages.MSG_NF_0002),
        user_id=recipient_id,
        user_email=user_email,
        template_code=EmailType.GUEST_NEW_TASK,
        method_name=NotificationMethod.guest_new_task,
        data={
            'title': title,
            'token': token,
            'user_id': recipient_id,
            'link': task_link,
            'task_id': task_id,
            'task_name': task_name,
            'task_description': html_description,
            'guest_sender_name': sender_name,
            'logo_lg': logo_lg,
            'due_in': formatted_task_due_in,
        },
    )


def test_send_guest_new_task__overdue__ok(mocker):

    # arrange
    fixed_now = timezone.now()
    mocker.patch(
        'src.notifications.services.email.timezone.now',
        return_value=fixed_now,
    )
    token = '!@#sadd1'
    sender_name = 'Joe'
    recipient_id = 1233
    user_email = 'guest@guest.guest'
    task_id = 11
    task_name = 'Task name'
    task_description = 'Some markdown description'
    due_in = timedelta(hours=1)
    task_due_date = fixed_now - due_in

    html_description = '<div>text</div>'
    html_service_mock = mocker.patch(
        'src.notifications.services.email.convert_text_to_html',
        return_value=html_description,
    )
    send_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send',
    )
    formatted_task_due_in = '1 hour'
    get_duration_format_mock = mocker.patch(
        'src.notifications.services.email.get_duration_format',
        return_value=formatted_task_due_in,
    )
    logo_lg = None
    logging = False
    account_id = 123

    service = EmailService(
        logo_lg=logo_lg,
        logging=logging,
        account_id=account_id,
    )

    # act
    service.send_guest_new_task(
        token=token,
        sender_name=sender_name,
        user_id=recipient_id,
        user_email=user_email,
        task_id=task_id,
        task_name=task_name,
        task_description=task_description,
        task_due_date=task_due_date,
    )

    # assert
    html_service_mock.assert_called_once_with(task_description)
    get_duration_format_mock.assert_called_once()
    task_link = (
        f'{settings.FRONTEND_URL}/guest-task/{task_id}'
        f'?token={token}&utm_campaign=guestUser&utm_term={recipient_id}'
    )
    title = (
        f'{sender_name} {email_titles[NotificationMethod.guest_new_task]} '
        f'{task_name} Task'
    )
    send_mock.assert_called_once_with(
        title=str(messages.MSG_NF_0002),
        user_id=recipient_id,
        user_email=user_email,
        template_code=EmailType.GUEST_NEW_TASK,
        method_name=NotificationMethod.guest_new_task,
        data={
            'title': title,
            'token': token,
            'user_id': recipient_id,
            'link': task_link,
            'task_id': task_id,
            'task_name': task_name,
            'task_description': html_description,
            'guest_sender_name': sender_name,
            'logo_lg': None,
            'overdue': formatted_task_due_in,
        },
    )


@pytest.mark.parametrize(
    'task_due_date',
    (
        '2000-02-15T15:49:56.564519Z',
        '2023-04-11T00:00:00Z',
    ),
)
def test_send_guest_new_task__task_due_date__is_str__ok(
    task_due_date,
    mocker,
):

    # arrange
    fixed_now = timezone.now()
    mocker.patch(
        'src.notifications.services.email.timezone.now',
        return_value=fixed_now,
    )
    token = '!@#sadd1'
    sender_name = 'Joe'
    recipient_id = 1233
    user_email = 'guest@guest.guest'
    task_id = 11
    task_name = 'Task name'
    task_description = 'Some markdown description'

    html_description = '<div>text</div>'
    html_service_mock = mocker.patch(
        'src.notifications.services.email.convert_text_to_html',
        return_value=html_description,
    )
    send_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send',
    )
    formatted_task_due_in = '1 hour'
    get_duration_format_mock = mocker.patch(
        'src.notifications.services.email.get_duration_format',
        return_value=formatted_task_due_in,
    )
    logo_lg = 'https://logo.jpg'
    logging = False
    account_id = 123

    service = EmailService(
        logo_lg=logo_lg,
        logging=logging,
        account_id=account_id,
    )

    # act
    service.send_guest_new_task(
        token=token,
        user_id=recipient_id,
        sender_name=sender_name,
        user_email=user_email,
        task_id=task_id,
        task_name=task_name,
        task_description=task_description,
        task_due_date=task_due_date,
    )

    # assert
    html_service_mock.assert_called_once_with(task_description)
    get_duration_format_mock.assert_called_once()
    task_link = (
        f'{settings.FRONTEND_URL}/guest-task/{task_id}'
        f'?token={token}&utm_campaign=guestUser&utm_term={recipient_id}'
    )
    title = (
        f'{sender_name} {email_titles[NotificationMethod.guest_new_task]} '
        f'{task_name} Task'
    )
    send_mock.assert_called_once_with(
        title=str(messages.MSG_NF_0002),
        user_id=recipient_id,
        user_email=user_email,
        template_code=EmailType.GUEST_NEW_TASK,
        method_name=NotificationMethod.guest_new_task,
        data={
            'title': title,
            'token': token,
            'user_id': recipient_id,
            'link': task_link,
            'task_id': task_id,
            'task_name': task_name,
            'task_description': html_description,
            'guest_sender_name': sender_name,
            'logo_lg': logo_lg,
            'overdue': formatted_task_due_in,
        },
    )


def test_send_unread_notifications__ok(mocker):

    # arrange
    fixed_now = timezone.now()
    mocker.patch(
        'src.notifications.services.email.timezone.now',
        return_value=fixed_now,
    )
    recipient_id = 1233
    user_email = 'guest@guest.guest'
    recipient_first_name = 'John'

    send_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send',
    )
    unsubscribe_token = '!@#sadd1'
    unsubscribe_token_mock = mocker.patch(
        'src.notifications.services.email.'
        'UnsubscribeEmailToken.create_token',
        return_value=unsubscribe_token,
    )
    logo_lg = None
    logging = False
    account_id = 123

    service = EmailService(
        logo_lg=logo_lg,
        logging=logging,
        account_id=account_id,
    )

    # act
    service.send_unread_notifications(
        user_id=recipient_id,
        user_first_name=recipient_first_name,
        user_email=user_email,
    )

    # assert
    unsubscribe_token_mock.assert_called_once_with(
        user_id=recipient_id,
        email_type=MailoutType.COMMENTS,
    )
    unsubscribe_link = (
        f'{settings.BACKEND_URL}/accounts/emails/unsubscribe?token='
        f'{unsubscribe_token}'
    )
    notifications_link = (
        f'{settings.FRONTEND_URL}'
        '?utm_source=notifications&utm_campaign=unread_notifications'
    )
    content = (
        f'{recipient_first_name}, work in your company is in full swing. '
        f'Check your recent notifications to be up to date.'
    )
    send_mock.assert_called_once_with(
        title=str(messages.MSG_NF_0013),
        user_id=recipient_id,
        user_email=user_email,
        template_code=EmailType.UNREAD_NOTIFICATIONS,
        method_name=NotificationMethod.unread_notifications,
        data={
            'title': email_titles[NotificationMethod.unread_notifications],
            'content': content,
            'user_name': recipient_first_name,
            'button_text': 'View Notifications',
            'unsubscribe_token': unsubscribe_token,
            'unsubscribe_link': unsubscribe_link,
            'notifications_link': notifications_link,
            'link': notifications_link,
            'logo_lg': None,
        },
    )


def test_send_new_task__ok(mocker):

    # arrange
    fixed_now = timezone.now()
    mocker.patch(
        'src.notifications.services.email.timezone.now',
        return_value=fixed_now,
    )
    recipient_id = 1233
    user_email = 'guest@guest.guest'
    task_id = 11
    task_name = 'Task name'
    template_name = 'Template name'
    workflow_name = 'Workflow name'
    html_description = '<div>text</div>'
    wf_starter_name = 'Some wf starter'
    wf_starter_photo = 'https://site.com/photo.jpg'
    due_in = '15 days 6 hours 23 minutes'
    overdue = '6 hours 1 minutes'

    unsubscribe_token = '123123'
    create_unsubscribe_token_mock = mocker.patch(
        'src.notifications.services.email.'
        'UnsubscribeEmailToken.create_token',
        return_value=unsubscribe_token,
    )
    send_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send',
    )
    logo_lg = 'https://logo.jpg'
    logging = False
    account_id = 123

    service = EmailService(
        logo_lg=logo_lg,
        logging=logging,
        account_id=account_id,
    )

    # act
    service.send_new_task(
        user_id=recipient_id,
        user_email=user_email,
        template_name=template_name,
        workflow_name=workflow_name,
        task_id=task_id,
        task_name=task_name,
        html_description=html_description,
        text_description='text description',
        wf_starter_name=wf_starter_name,
        wf_starter_photo=wf_starter_photo,
        due_in=due_in,
        overdue=overdue,
        sync=True,
    )

    # assert
    task_link = f'{settings.FRONTEND_URL}/tasks/{task_id}'
    unsubscribe_link = (
        f'{settings.BACKEND_URL}/accounts/emails/unsubscribe?token='
        f'{unsubscribe_token}'
    )
    send_mock.assert_called_once_with(
        title=str(messages.MSG_NF_0002),
        user_id=recipient_id,
        user_email=user_email,
        template_code=EmailType.NEW_TASK,
        method_name=NotificationMethod.new_task,
        data={
            'title': email_titles[NotificationMethod.new_task],
            'template': template_name,
            'workflow_name': workflow_name,
            'task_name': task_name,
            'due_in': due_in,
            'overdue': overdue,
            'task_description': html_description,
            'task_id': task_id,
            'link': task_link,
            'unsubscribe_token': unsubscribe_token,
            'unsubscribe_link': unsubscribe_link,
            'started_by': {
                'name': wf_starter_name,
                'avatar': wf_starter_photo,
            },
            'logo_lg': logo_lg,
        },
    )
    create_unsubscribe_token_mock.assert_called_once_with(
        user_id=recipient_id,
        email_type=MailoutType.NEW_TASK,
    )


def test_send_returned_task__ok(mocker):

    # arrange
    fixed_now = timezone.now()
    mocker.patch(
        'src.notifications.services.email.timezone.now',
        return_value=fixed_now,
    )
    recipient_id = 1233
    user_email = 'guest@guest.guest'
    task_id = 11
    task_name = 'Task name'
    template_name = 'Template name'
    workflow_name = 'Workflow name'
    html_description = '<div>text</div>'
    wf_starter_name = 'Some wf starter'
    wf_starter_photo = 'https://site.com/photo.jpg'
    due_in = '15 days 6 hours 23 minutes'
    overdue = '6 hours 1 minutes'

    unsubscribe_token = '123123'
    create_unsubscribe_token_mock = mocker.patch(
        'src.notifications.services.email.'
        'UnsubscribeEmailToken.create_token',
        return_value=unsubscribe_token,
    )
    send_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send',
    )
    logo_lg = 'https://logo.jpg'
    logging = False
    account_id = 123

    service = EmailService(
        logo_lg=logo_lg,
        logging=logging,
        account_id=account_id,
    )

    # act
    service.send_returned_task(
        user_id=recipient_id,
        user_email=user_email,
        template_name=template_name,
        workflow_name=workflow_name,
        task_id=task_id,
        task_name=task_name,
        html_description=html_description,
        text_description='text description',
        wf_starter_name=wf_starter_name,
        wf_starter_photo=wf_starter_photo,
        due_in=due_in,
        overdue=overdue,
        sync=True,
    )

    # assert
    task_link = f'{settings.FRONTEND_URL}/tasks/{task_id}'
    unsubscribe_link = (
        f'{settings.BACKEND_URL}/accounts/emails/unsubscribe?token='
        f'{unsubscribe_token}'
    )
    send_mock.assert_called_once_with(
        title=str(messages.MSG_NF_0003),
        user_id=recipient_id,
        user_email=user_email,
        template_code=EmailType.TASK_RETURNED,
        method_name=NotificationMethod.returned_task,
        data={
            'title': email_titles[NotificationMethod.returned_task],
            'template': template_name,
            'workflow_name': workflow_name,
            'task_name': task_name,
            'due_in': due_in,
            'overdue': overdue,
            'task_description': html_description,
            'task_id': task_id,
            'link': task_link,
            'unsubscribe_token': unsubscribe_token,
            'unsubscribe_link': unsubscribe_link,
            'started_by': {
                'name': wf_starter_name,
                'avatar': wf_starter_photo,
            },
            'logo_lg': logo_lg,
        },
    )
    create_unsubscribe_token_mock.assert_called_once_with(
        user_id=recipient_id,
        email_type=MailoutType.NEW_TASK,
    )


def test_send_reset_password__ok(mocker):

    # arrange
    fixed_now = timezone.now()
    mocker.patch(
        'src.notifications.services.email.timezone.now',
        return_value=fixed_now,
    )
    recipient_id = 1233
    user_email = 'test@user.com'
    token = '!@#sadd1'
    reset_password_token_mock = mocker.patch(
        'src.notifications.services.email.'
        'ResetPasswordToken.for_user_id',
        return_value=token,
    )
    send_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send',
    )
    logo_lg = 'https://logo.jpg'
    logging = False
    account_id = 123

    service = EmailService(
        logo_lg=logo_lg,
        logging=logging,
        account_id=account_id,
    )

    # act
    service.send_reset_password(
        user_id=recipient_id,
        user_email=user_email,
    )

    # assert
    reset_password_token_mock.assert_called_once_with(recipient_id)
    reset_link = (
        f'{settings.FRONTEND_URL}/auth/reset-password?token={token}'
    )
    send_mock.assert_called_once_with(
        title=str(messages.MSG_NF_0014),
        user_id=recipient_id,
        user_email=user_email,
        template_code=EmailType.RESET_PASSWORD,
        method_name=NotificationMethod.reset_password,
        data={
            'title': email_titles[NotificationMethod.reset_password],
            'content': (
                'We got a request to reset your Pneumatic account password.'
            ),
            'additional_content': (
                'A strong password includes eight or more characters '
                'and a combination of uppercase and lowercase letters, '
                'numbers and symbols, and is not based on words in the '
                'dictionary.'
            ),
            'button_text': 'Reset my password',
            'token': token,
            'link': reset_link,
            'reset_link': reset_link,
            'logo_lg': logo_lg,
        },
    )


def test_send_mention__ok(mocker):

    # arrange
    fixed_now = timezone.now()
    mocker.patch(
        'src.notifications.services.email.timezone.now',
        return_value=fixed_now,
    )
    user_id = 1233
    task_id = 3321
    user_email = 'test@user.com'
    user_first_name = 'John'
    send_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send',
    )
    logo_lg = 'https://logo.jpg'
    logging = False
    account_id = 123

    service = EmailService(
        logo_lg=logo_lg,
        logging=logging,
        account_id=account_id,
    )

    # act
    service.send_mention(
        task_id=task_id,
        user_id=user_id,
        user_email=user_email,
        user_first_name=user_first_name,
    )

    # assert
    task_link = f'{settings.FRONTEND_URL}/tasks/{task_id}'
    content = (
        f"{user_first_name}, there's some activity happening. "
        f"Check your mentions to stay updated on your tasks right away."
    )
    send_mock.assert_called_once_with(
        title=str(messages.MSG_NF_0005),
        user_id=user_id,
        user_email=user_email,
        template_code=EmailType.MENTION,
        method_name=NotificationMethod.mention,
        data={
            'title': email_titles[NotificationMethod.mention],
            'content': content,
            'logo_lg': logo_lg,
            'button_text': 'View Mentions',
            'user_first_name': user_first_name,
            'task_id': task_id,
            'link': task_link,
        },
    )


def test_send_user_deactivated_email__ok(mocker):

    # arrange
    user_mock = mocker.Mock()
    user_mock.id = 123
    user_mock.email = 'test@user.com'
    user_mock.account_id = 456
    user_mock.account.logo_lg = 'https://logo.jpg'

    settings_mock = mocker.patch(
        'src.notifications.services.email.settings',
    )
    settings_mock.FRONTEND_URL = settings.FRONTEND_URL

    send_simple_email_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send',
    )

    logo_lg = user_mock.account.logo_lg
    service = EmailService(
        account_id=user_mock.account_id,
        logo_lg=logo_lg,
    )

    # act
    service.send_user_deactivated(
        user_id=user_mock.id,
        user_email=user_mock.email,
    )

    # assert
    send_simple_email_mock.assert_called_once_with(
        title=str(messages.MSG_NF_0015),
        user_id=user_mock.id,
        user_email=user_mock.email,
        template_code=EmailType.USER_DEACTIVATED,
        method_name=NotificationMethod.user_deactivated,
        data={
            'title': email_titles[NotificationMethod.user_deactivated],
            'logo_lg': logo_lg,
        },
    )


def test_send_user_transfer_email__ok(mocker):

    # arrange
    email = 'transfer@test.com'
    token = 'transfer_token_123'
    user_id = 789
    logo_lg = 'https://company-logo.jpg'

    invited_by_mock = mocker.Mock()
    invited_by_mock.get_full_name.return_value = 'John Doe'
    invited_by_mock.account.name = 'Test Company'

    settings_mock = mocker.patch(
        'src.notifications.services.email.settings',
    )
    settings_mock.BACKEND_URL = settings.BACKEND_URL

    send_simple_email_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send',
    )

    service = EmailService(
        account_id=123,
        logo_lg=logo_lg,
    )

    # act
    service.send_user_transfer(
        user_id=user_id,
        user_email=email,
        invited_by_name=invited_by_mock.get_full_name(),
        company_name=invited_by_mock.account.name,
        token=token,
    )

    # assert
    transfer_link = (
        f'{settings.BACKEND_URL}/accounts/users/{user_id}/transfer'
        f'?token={token}&utm_source=invite&utm_campaign=transfer'
    )
    content = (
        "Your User Profile is associated with another Pneumatic account. "
        "By agreeing to this invitation, you permit us to transfer your "
        "User Profile to an invitee's account. This transfer will revoke "
        "your access to your old account."
    )
    send_simple_email_mock.assert_called_once_with(
        title=str(messages.MSG_NF_0016),
        user_id=user_id,
        user_email=email,
        template_code=EmailType.USER_TRANSFER,
        method_name=NotificationMethod.user_transfer,
        data={
            'title': (
                f'{invited_by_mock.get_full_name()} '
                f'{email_titles[NotificationMethod.user_transfer]}'
            ),
            'content': content,
            'button_text': 'Transfer My Profile',
            'token': token,
            'link': transfer_link,
            'transfer_link': transfer_link,
            'sender_name': invited_by_mock.get_full_name(),
            'company_name': invited_by_mock.account.name,
            'user_id': user_id,
            'logo_lg': logo_lg,
        },
    )


def test_send_verification_email__ok(mocker):

    # arrange
    user_mock = mocker.Mock()
    user_mock.id = 456
    user_mock.email = 'verify@test.com'
    user_mock.first_name = 'Jane'

    token = 'verification_token_456'
    logo_lg = 'https://verify-logo.jpg'

    settings_mock = mocker.patch(
        'src.notifications.services.email.settings',
    )
    settings_mock.FRONTEND_URL = settings.FRONTEND_URL

    send_simple_email_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send',
    )

    # act
    service = EmailService(account_id=123, logo_lg=logo_lg)
    service.send_verification(
        user_id=user_mock.id,
        user_email=user_mock.email,
        user_first_name=user_mock.first_name,
        token=token,
    )

    # assert
    verification_link = (
        f'{settings.FRONTEND_URL}/auth/verification?token={token}'
    )
    send_simple_email_mock.assert_called_once_with(
        title=str(messages.MSG_NF_0017),
        user_id=user_mock.id,
        user_email=user_mock.email,
        template_code=EmailType.ACCOUNT_VERIFICATION,
        method_name=NotificationMethod.verification,
        data={
            'title': email_titles[NotificationMethod.verification],
            'content': (
                'Thank you for signing up for Pneumatic. '
                'Please verify your email address to get started.'
            ),
            'button_text': 'Get Started',
            'token': token,
            'link': verification_link,
            'first_name': user_mock.first_name,
            'logo_lg': logo_lg,
        },
    )


def test_send_workflows_digest_email__ok(mocker):

    # arrange
    user_mock = mocker.Mock()
    user_mock.id = 789
    user_mock.email = 'digest@test.com'
    user_mock.account_id = 123

    logo_lg = 'https://digest-logo.jpg'

    date_from = timezone.now().date() - timedelta(days=7)
    date_to = timezone.now().date()
    digest_data = {
        'workflows_count': 5,
        'completed_workflows': 3,
        'active_workflows': 2,
    }

    unsubscribe_token = 'unsubscribe_token_123'
    create_unsubscribe_token_mock = mocker.patch(
        'src.notifications.services.email.'
        'UnsubscribeEmailToken.create_token',
        return_value=unsubscribe_token,
    )

    settings_mock = mocker.patch(
        'src.notifications.services.email.settings',
    )
    settings_mock.BACKEND_URL = settings.BACKEND_URL
    settings_mock.FRONTEND_URL = settings.FRONTEND_URL

    send_simple_email_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send',
    )

    service = EmailService(
        account_id=user_mock.account_id,
        logo_lg=logo_lg,
    )

    # act
    service.send_workflows_digest(
        user_id=user_mock.id,
        user_email=user_mock.email,
        date_from=date_from,
        date_to=date_to,
        digest=digest_data,
    )

    # assert
    unsubscribe_link = (
        f'{settings.BACKEND_URL}/accounts/emails/unsubscribe?token='
        f'{unsubscribe_token}'
    )
    workflows_link = (
        f'{settings.FRONTEND_URL}'
        f'/workflows?utm_source=email&utm_campaign=digest'
    )

    create_unsubscribe_token_mock.assert_called_once_with(
        user_id=user_mock.id,
        email_type=MailoutType.WF_DIGEST,
    )

    send_simple_email_mock.assert_called_once_with(
        title=str(messages.MSG_NF_0018),
        user_id=user_mock.id,
        user_email=user_mock.email,
        template_code=EmailType.WORKFLOWS_DIGEST,
        method_name=NotificationMethod.workflows_digest,
        data={
            'title': email_titles[NotificationMethod.workflows_digest],
            'date_from': date_from.strftime('%d %b'),
            'date_to': date_to.strftime('%d %b, %Y'),
            'unsubscribe_token': unsubscribe_token,
            'unsubscribe_link': unsubscribe_link,
            'workflows_link': workflows_link,
            'link': workflows_link,
            'logo_lg': logo_lg,
            'is_tasks_digest': False,
            'status_labels': {
                'started': 'Started',
                'in_progress': 'In Progress',
                'overdue': 'Overdue',
                'completed': 'Completed',
            },
            'base_link': f'{settings.FRONTEND_URL}/workflows',
            'status_queries': {
                'started': '?type=running',
                'in_progress': '?type=running',
                'overdue': '?type=running&sorting=overdue',
                'completed': '?type=done',
            },
            'template_query_param': 'templates',
            'workflows_count': 5,
            'completed_workflows': 3,
            'active_workflows': 2,
        },
    )


def test_send_tasks_digest_email__ok(mocker):

    # arrange
    user_mock = mocker.Mock()
    user_mock.id = 456
    user_mock.email = 'tasks@test.com'
    user_mock.account_id = 789

    logo_lg = 'https://tasks-logo.jpg'

    date_from = timezone.now().date() - timedelta(days=7)
    date_to = timezone.now().date()
    digest_data = {
        'tasks_count': 10,
        'completed_tasks': 7,
        'overdue_tasks': 1,
    }

    unsubscribe_token = 'tasks_unsubscribe_456'
    create_unsubscribe_token_mock = mocker.patch(
        'src.notifications.services.email.'
        'UnsubscribeEmailToken.create_token',
        return_value=unsubscribe_token,
    )

    settings_mock = mocker.patch(
        'src.notifications.services.email.settings',
    )
    settings_mock.BACKEND_URL = settings.BACKEND_URL
    settings_mock.FRONTEND_URL = settings.FRONTEND_URL

    send_simple_email_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send',
    )

    service = EmailService(
        account_id=user_mock.account_id,
        logo_lg=logo_lg,
    )

    # act
    service.send_tasks_digest(
        user_id=user_mock.id,
        user_email=user_mock.email,
        date_from=date_from,
        date_to=date_to,
        digest=digest_data,
    )

    # assert
    unsubscribe_link = (
        f'{settings.BACKEND_URL}/accounts/unsubscribe/{unsubscribe_token}'
    )
    tasks_link = (
        f'{settings.FRONTEND_URL}'
        f'/tasks?utm_source=email&utm_campaign=tasks_digest'
    )

    create_unsubscribe_token_mock.assert_called_once_with(
        user_id=user_mock.id,
        email_type=MailoutType.TASKS_DIGEST,
    )

    send_simple_email_mock.assert_called_once_with(
        title=str(messages.MSG_NF_0019),
        user_id=user_mock.id,
        user_email=user_mock.email,
        template_code=EmailType.TASKS_DIGEST,
        method_name=NotificationMethod.tasks_digest,
        data={
            'title': email_titles[NotificationMethod.tasks_digest],
            'date_from': date_from.strftime('%d %b'),
            'date_to': date_to.strftime('%d %b, %Y'),
            'unsubscribe_token': unsubscribe_token,
            'unsubscribe_link': unsubscribe_link,
            'tasks_link': tasks_link,
            'link': tasks_link,
            'logo_lg': logo_lg,
            'is_tasks_digest': True,
            'status_labels': {
                'started': 'Launched',
                'in_progress': 'Ongoing',
                'overdue': 'Overdue',
                'completed': 'Completed',
            },
            'base_link': f'{settings.FRONTEND_URL}/tasks',
            'status_queries': {
                'started': '',
                'in_progress': '',
                'overdue': '?sorting=overdue',
                'completed': '',
            },
            'template_query_param': 'template',
            'tasks_count': 10,
            'completed_tasks': 7,
            'overdue_tasks': 1,
        },
    )


def test_send_user_transfer_email__no_logo__ok(mocker):

    # arrange
    email = 'transfer@test.com'
    token = 'transfer_token_123'
    user_id = 789
    logo_lg = None

    invited_by_mock = mocker.Mock()
    invited_by_mock.get_full_name.return_value = 'John Doe'
    invited_by_mock.account.name = 'Test Company'

    settings_mock = mocker.patch(
        'src.notifications.services.email.settings',
    )
    settings_mock.BACKEND_URL = settings.BACKEND_URL

    send_simple_email_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send',
    )

    service = EmailService(
        account_id=123,
        logo_lg=logo_lg,
    )

    # act
    service.send_user_transfer(
        user_id=user_id,
        user_email=email,
        invited_by_name=invited_by_mock.get_full_name(),
        company_name=invited_by_mock.account.name,
        token=token,
    )

    # assert
    transfer_link = (
        f'{settings.BACKEND_URL}/accounts/users/{user_id}/transfer'
        f'?token={token}&utm_source=invite&utm_campaign=transfer'
    )
    content = (
        "Your User Profile is associated with another Pneumatic account. "
        "By agreeing to this invitation, you permit us to transfer your "
        "User Profile to an invitee's account. This transfer will revoke "
        "your access to your old account."
    )
    send_simple_email_mock.assert_called_once_with(
        title=str(messages.MSG_NF_0016),
        user_id=user_id,
        user_email=email,
        template_code=EmailType.USER_TRANSFER,
        method_name=NotificationMethod.user_transfer,
        data={
            'title': (
                f'{invited_by_mock.get_full_name()} '
                f'{email_titles[NotificationMethod.user_transfer]}'
            ),
            'content': content,
            'button_text': 'Transfer My Profile',
            'token': token,
            'link': transfer_link,
            'transfer_link': transfer_link,
            'sender_name': invited_by_mock.get_full_name(),
            'company_name': invited_by_mock.account.name,
            'user_id': user_id,
            'logo_lg': None,
        },
    )


def test_send_verification_email__no_logo__ok(mocker):

    # arrange
    user_mock = mocker.Mock()
    user_mock.id = 456
    user_mock.email = 'verify@test.com'
    user_mock.first_name = 'Jane'

    token = 'verification_token_456'
    logo_lg = None

    settings_mock = mocker.patch(
        'src.notifications.services.email.settings',
    )
    settings_mock.FRONTEND_URL = settings.FRONTEND_URL

    send_simple_email_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send',
    )

    # act
    service = EmailService(account_id=123, logo_lg=logo_lg)
    service.send_verification(
        user_id=user_mock.id,
        user_email=user_mock.email,
        user_first_name=user_mock.first_name,
        token=token,
    )

    # assert
    verification_link = (
        f'{settings.FRONTEND_URL}/auth/verification?token={token}'
    )
    send_simple_email_mock.assert_called_once_with(
        title=str(messages.MSG_NF_0017),
        user_id=user_mock.id,
        user_email=user_mock.email,
        template_code=EmailType.ACCOUNT_VERIFICATION,
        method_name=NotificationMethod.verification,
        data={
            'title': email_titles[NotificationMethod.verification],
            'content': (
                'Thank you for signing up for Pneumatic. '
                'Please verify your email address to get started.'
            ),
            'button_text': 'Get Started',
            'token': token,
            'link': verification_link,
            'first_name': user_mock.first_name,
            'logo_lg': None,
        },
    )


def test_send_workflows_digest_email__empty_digest__ok(mocker):

    # arrange
    user_mock = mocker.Mock()
    user_mock.id = 789
    user_mock.email = 'digest@test.com'
    user_mock.account_id = 123

    logo_lg = 'https://digest-logo.jpg'

    date_from = timezone.now().date() - timedelta(days=7)
    date_to = timezone.now().date()
    digest_data = {}

    unsubscribe_token = 'unsubscribe_token_123'
    mocker.patch(
        'src.notifications.services.email.'
        'UnsubscribeEmailToken.create_token',
        return_value=unsubscribe_token,
    )

    settings_mock = mocker.patch(
        'src.notifications.services.email.settings',
    )
    settings_mock.BACKEND_URL = settings.BACKEND_URL
    settings_mock.FRONTEND_URL = settings.FRONTEND_URL

    send_simple_email_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send',
    )

    service = EmailService(
        account_id=user_mock.account_id,
        logo_lg=logo_lg,
    )

    # act
    service.send_workflows_digest(
        user_id=user_mock.id,
        user_email=user_mock.email,
        date_from=date_from,
        date_to=date_to,
        digest=digest_data,
    )

    # assert
    unsubscribe_link = (
        f'{settings.BACKEND_URL}/accounts/emails/unsubscribe?token='
        f'{unsubscribe_token}'
    )
    workflows_link = (
        f'{settings.FRONTEND_URL}'
        f'/workflows?utm_source=email&utm_campaign=digest'
    )

    send_simple_email_mock.assert_called_once_with(
        title=str(messages.MSG_NF_0018),
        user_id=user_mock.id,
        user_email=user_mock.email,
        template_code=EmailType.WORKFLOWS_DIGEST,
        method_name=NotificationMethod.workflows_digest,
        data={
            'title': email_titles[NotificationMethod.workflows_digest],
            'date_from': date_from.strftime('%d %b'),
            'date_to': date_to.strftime('%d %b, %Y'),
            'unsubscribe_token': unsubscribe_token,
            'unsubscribe_link': unsubscribe_link,
            'workflows_link': workflows_link,
            'link': workflows_link,
            'logo_lg': logo_lg,
            'is_tasks_digest': False,
            'status_labels': {
                'started': 'Started',
                'in_progress': 'In Progress',
                'overdue': 'Overdue',
                'completed': 'Completed',
            },
            'base_link': f'{settings.FRONTEND_URL}/workflows',
            'status_queries': {
                'started': '?type=running',
                'in_progress': '?type=running',
                'overdue': '?type=running&sorting=overdue',
                'completed': '?type=done',
            },
            'template_query_param': 'templates',
        },
    )


def test_send_tasks_digest_email__empty_digest__ok(mocker):

    # arrange
    user_mock = mocker.Mock()
    user_mock.id = 456
    user_mock.email = 'tasks@test.com'
    user_mock.account_id = 789

    logo_lg = None

    date_from = timezone.now().date() - timedelta(days=7)
    date_to = timezone.now().date()
    digest_data = {}

    unsubscribe_token = 'tasks_unsubscribe_456'
    mocker.patch(
        'src.notifications.services.email.'
        'UnsubscribeEmailToken.create_token',
        return_value=unsubscribe_token,
    )

    settings_mock = mocker.patch(
        'src.notifications.services.email.settings',
    )
    settings_mock.BACKEND_URL = settings.BACKEND_URL
    settings_mock.FRONTEND_URL = settings.FRONTEND_URL

    send_simple_email_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send',
    )

    service = EmailService(
        account_id=user_mock.account_id,
        logo_lg=logo_lg,
    )

    # act
    service.send_tasks_digest(
        user_id=user_mock.id,
        user_email=user_mock.email,
        date_from=date_from,
        date_to=date_to,
        digest=digest_data,
    )

    # assert
    unsubscribe_link = (
        f'{settings.BACKEND_URL}/accounts/unsubscribe/{unsubscribe_token}'
    )
    tasks_link = (
        f'{settings.FRONTEND_URL}'
        f'/tasks?utm_source=email&utm_campaign=tasks_digest'
    )

    send_simple_email_mock.assert_called_once_with(
        title=str(messages.MSG_NF_0019),
        user_id=user_mock.id,
        user_email=user_mock.email,
        template_code=EmailType.TASKS_DIGEST,
        method_name=NotificationMethod.tasks_digest,
        data={
            'title': email_titles[NotificationMethod.tasks_digest],
            'date_from': date_from.strftime('%d %b'),
            'date_to': date_to.strftime('%d %b, %Y'),
            'unsubscribe_token': unsubscribe_token,
            'unsubscribe_link': unsubscribe_link,
            'tasks_link': tasks_link,
            'link': tasks_link,
            'logo_lg': None,
            'is_tasks_digest': True,
            'status_labels': {
                'started': 'Launched',
                'in_progress': 'Ongoing',
                'overdue': 'Overdue',
                'completed': 'Completed',
            },
            'base_link': f'{settings.FRONTEND_URL}/tasks',
            'status_queries': {
                'started': '',
                'in_progress': '',
                'overdue': '?sorting=overdue',
                'completed': '',
            },
            'template_query_param': 'template',
        },
    )


def test_send_simple_email__ok(mocker):

    # arrange
    title = 'Test Email'
    user_id = 123
    user_email = 'test@example.com'
    template_code = EmailType.RESET_PASSWORD
    method_name = NotificationMethod.reset_password
    data = {'test': 'data'}

    send_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService._send',
    )

    logo_lg = 'https://logo.jpg'
    logging = False
    account_id = 456

    service = EmailService(
        logo_lg=logo_lg,
        logging=logging,
        account_id=account_id,
    )

    # act
    service._send(
        title=title,
        user_id=user_id,
        user_email=user_email,
        template_code=template_code,
        method_name=method_name,
        data=data,
    )

    # assert
    send_mock.assert_called_once_with(
        title=title,
        user_id=user_id,
        user_email=user_email,
        template_code=template_code,
        method_name=method_name,
        data=data,
    )


def test_send_email_to_console__ok(mocker):

    # arrange
    user_email = 'console@test.com'
    template_code = EmailType.NEW_TASK
    data = {'task_name': 'Test Task', 'workflow_name': 'Test Workflow'}

    print_mock = mocker.patch('builtins.print')

    logo_lg = 'https://logo.jpg'
    logging = False
    account_id = 123

    service = EmailService(
        logo_lg=logo_lg,
        logging=logging,
        account_id=account_id,
    )

    # act
    service._send_email_to_console(
        user_email=user_email,
        template_code=template_code,
        data=data,
    )

    # assert
    print_mock.assert_called_once()
    call_args = print_mock.call_args[0][0]
    assert 'EMAIL-MESSAGE' in call_args
    assert user_email in call_args
    assert template_code in call_args
