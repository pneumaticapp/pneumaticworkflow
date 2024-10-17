import pytest
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from pneumatic_backend.accounts.enums import UserType
from pneumatic_backend.notifications.enums import (
    NotificationMethod,
    EmailTemplate,
)
from pneumatic_backend.notifications.services.email import (
    EmailService
)
from pneumatic_backend.notifications.services.exceptions import (
    NotificationServiceError,
)
from pneumatic_backend.analytics.enums import MailoutType


pytestmark = pytest.mark.django_db


def test_send_email_via_customerio(mocker):

    # arrange
    template_id = 1
    template_code = 'new_task'
    mocker.patch(
        'pneumatic_backend.notifications.services.email.cio_template_ids',
        {template_code: template_id}
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.settings'
    )
    api_key = '!@#'
    settings_mock.CUSTOMERIO_TRANSACTIONAL_API_KEY = api_key

    client_mock = mocker.Mock()
    api_client_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.APIClient',
        return_value=client_mock
    )
    request_mock = mocker.Mock()
    send_email_request_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.SendEmailRequest',
        return_value=request_mock
    )

    user_id = 1
    email = 'test@pneumatic.app'
    data = {'test': 'data'}
    service = EmailService()

    # act
    service._send_email_via_customerio(
        user_id=user_id,
        recipient_email=email,
        template_code=template_code,
        data=data,
    )

    # assert
    api_client_mock.assert_called_once_with(api_key)

    send_email_request_mock.assert_called_once_with(
        to=email,
        transactional_message_id=template_id,
        message_data=data,
        identifiers={'id': user_id}
    )
    client_mock.send_email.assert_called_once_with(request_mock)


def test_send__dev_environment__console_print(mocker):

    # arrange
    settings_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.settings'
    )
    send_to_console_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService._send_email_to_console'
    )
    send_via_customerio_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.EmailService.'
        '_send_email_via_customerio'
    )
    user_id = 1
    email = 'john@cena.com'
    data = {'some': 'data'}
    settings_mock.CONFIGURATION_CURRENT = settings.CONFIGURATION_DEV
    settings_mock.CONFIGURATION_DEV = settings.CONFIGURATION_DEV
    settings_mock.PROJECT_CONF = {'EMAIL': True}
    service = EmailService()

    # act
    service._send(
        user_id=user_id,
        recipient_email=email,
        template_code=EmailTemplate.OVERDUE_TASK,
        method_name=NotificationMethod.overdue_task,
        data=data
    )

    # assert
    send_to_console_mock.assert_called_with(
        recipient_email=email,
        template_code=EmailTemplate.OVERDUE_TASK,
        data=data,
    )
    send_via_customerio_mock.assert_not_called()


def test_send__prod_environment__send_email(mocker):

    # arrange
    settings_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.settings'
    )
    send_to_console_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService._send_email_to_console'
    )
    send_via_customerio_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.EmailService.'
        '_send_email_via_customerio'
    )
    user_id = 1
    email = 'john@cena.com'
    data = {'some': 'data'}
    settings_mock.CONFIGURATION_CURRENT = settings.CONFIGURATION_PROD
    settings_mock.CONFIGURATION_PROD = settings.CONFIGURATION_PROD
    settings_mock.PROJECT_CONF = {'EMAIL': True}
    service = EmailService()

    # act
    service._send(
        user_id=user_id,
        recipient_email=email,
        template_code=EmailTemplate.OVERDUE_TASK,
        method_name=NotificationMethod.overdue_task,
        data=data
    )

    # assert
    send_to_console_mock.assert_not_called()
    send_via_customerio_mock.assert_called_with(
        user_id=user_id,
        recipient_email=email,
        template_code=EmailTemplate.OVERDUE_TASK,
        data=data,
    )


def test_send__not_allowed_method__raise_exception(mocker):

    # arrange
    mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService.ALLOWED_METHODS',
        {NotificationMethod.new_task}
    )
    send_to_console_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService._send_email_to_console'
    )
    send_via_customerio_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.EmailService.'
        '_send_email_via_customerio'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.settings'
    )
    settings_mock.PROJECT_CONF = {'EMAIL': True}
    user_id = 1
    email = 'john@cena.com'
    data = {'some': 'data'}
    service = EmailService()

    # act
    with pytest.raises(NotificationServiceError) as ex:
        service._send(
            user_id=user_id,
            recipient_email=email,
            template_code=EmailTemplate.OVERDUE_TASK,
            method_name=NotificationMethod.overdue_task,
            data=data
        )

    # assert
    assert ex.value.message == (
        f'{NotificationMethod.overdue_task} is not allowed notification'
    )
    send_to_console_mock.assert_not_called()
    send_via_customerio_mock.assert_not_called()


def test_send__disable_email__skip(mocker):

    # arrange
    settings_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.settings'
    )
    send_to_console_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService._send_email_to_console'
    )
    send_via_customerio_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.EmailService.'
        '_send_email_via_customerio'
    )
    user_id = 1
    email = 'john@cena.com'
    data = {'some': 'data'}
    settings_mock.CONFIGURATION_CURRENT = settings.CONFIGURATION_PROD
    settings_mock.CONFIGURATION_PROD = settings.CONFIGURATION_PROD
    settings_mock.PROJECT_CONF = {'EMAIL': False}
    service = EmailService()

    # act
    service._send(
        user_id=user_id,
        recipient_email=email,
        template_code=EmailTemplate.OVERDUE_TASK,
        method_name=NotificationMethod.overdue_task,
        data=data
    )

    # assert
    send_to_console_mock.assert_not_called()
    send_via_customerio_mock.assert_not_called()


def test_send_overdue_task__type_user__ok(mocker):

    # arrange
    send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService._send'
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
    service = EmailService()

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
        logo_lg=logo_lg,
    )

    # assert
    send_mock.assert_called_once_with(
        user_id=user_id,
        recipient_email=user_email,
        template_code=EmailTemplate.OVERDUE_TASK,
        method_name=NotificationMethod.overdue_task,
        data={
            'task_id': str(task_id),
            'task_name': task_name,
            'workflow_id': workflow_id,
            'workflow_name': workflow_name,
            'workflow_starter_id': workflow_starter_id,
            'workflow_starter_first_name': workflow_starter_first_name,
            'workflow_starter_last_name': workflow_starter_last_name,
            'template_name': template_name,
            'logo_lg': logo_lg,
            'user_type': UserType.USER,
            'token': None
        }
    )


def test_send_overdue_task__type_guest__ok(mocker):

    # arrange
    send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService._send'
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
    service = EmailService()
    token = '!@#'

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
        logo_lg=logo_lg,
        token=token
    )

    # assert
    send_mock.assert_called_once_with(
        user_id=user_id,
        recipient_email=user_email,
        template_code=EmailTemplate.OVERDUE_TASK,
        method_name=NotificationMethod.overdue_task,
        data={
            'task_id': str(task_id),
            'task_name': task_name,
            'workflow_id': workflow_id,
            'workflow_name': workflow_name,
            'workflow_starter_id': workflow_starter_id,
            'workflow_starter_first_name': workflow_starter_first_name,
            'workflow_starter_last_name': workflow_starter_last_name,
            'template_name': template_name,
            'logo_lg': logo_lg,
            'user_type': UserType.GUEST,
            'token': token
        }
    )


def test_send_guest_new_task__due_in__ok(mocker):

    # arrange
    token = '!@#sadd1'
    sender_name = 'Joe'
    recipient_id = 1233
    recipient_email = 'guest@guest.guest'
    task_id = 11
    task_name = 'Task name'
    task_description = 'Some markdown description'
    duration = timedelta(hours=1)
    task_due_date = timezone.now() + duration
    logo_lg = 'https://site.com/logo-lg.jpg'

    html_description = '<div>text</div>'
    html_service_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.convert_text_to_html',
        return_value=html_description
    )
    send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService._send'
    )
    formatted_task_due_in = '1 hour'
    get_duration_format_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.get_duration_format',
        return_value=formatted_task_due_in,
    )
    service = EmailService()

    # act
    service.send_guest_new_task(
        token=token,
        user_id=recipient_id,
        sender_name=sender_name,
        user_email=recipient_email,
        task_id=task_id,
        task_name=task_name,
        task_description=task_description,
        task_due_date=task_due_date,
        logo_lg=logo_lg,
    )

    # assert
    html_service_mock.assert_called_once_with(task_description)
    get_duration_format_mock.assert_called_once()
    send_mock.assert_called_once_with(
        user_id=recipient_id,
        recipient_email=recipient_email,
        template_code=EmailTemplate.GUEST_NEW_TASK,
        method_name=NotificationMethod.guest_new_task,
        data={
            'token': token,
            'user_id': recipient_id,
            'task_id': task_id,
            'task_name': task_name,
            'task_description': html_description,
            'sender_name': sender_name,
            'logo_lg': logo_lg,
            'due_in': formatted_task_due_in
        }
    )


def test_send_guest_new_task__overdue__ok(mocker):

    # arrange
    token = '!@#sadd1'
    sender_name = 'Joe'
    recipient_id = 1233
    recipient_email = 'guest@guest.guest'
    task_id = 11
    task_name = 'Task name'
    task_description = 'Some markdown description'
    due_in = timedelta(hours=1)
    task_due_date = timezone.now() - due_in
    logo_lg = None

    html_description = '<div>text</div>'
    html_service_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.convert_text_to_html',
        return_value=html_description
    )
    send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService._send'
    )
    formatted_task_due_in = '1 hour'
    get_duration_format_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.get_duration_format',
        return_value=formatted_task_due_in,
    )
    service = EmailService()

    # act
    service.send_guest_new_task(
        token=token,
        sender_name=sender_name,
        user_id=recipient_id,
        user_email=recipient_email,
        task_id=task_id,
        task_name=task_name,
        task_description=task_description,
        task_due_date=task_due_date,
        logo_lg=logo_lg,
    )

    # assert
    html_service_mock.assert_called_once_with(task_description)
    get_duration_format_mock.assert_called_once()
    send_mock.assert_called_once_with(
        user_id=recipient_id,
        recipient_email=recipient_email,
        template_code=EmailTemplate.GUEST_NEW_TASK,
        method_name=NotificationMethod.guest_new_task,
        data={
            'token': token,
            'user_id': recipient_id,
            'task_id': task_id,
            'task_name': task_name,
            'task_description': html_description,
            'sender_name': sender_name,
            'logo_lg': None,
            'overdue': formatted_task_due_in
        }
    )


@pytest.mark.parametrize(
    'task_due_date',
    (
        '2000-02-15T15:49:56.564519Z',
        '2023-04-11T00:00:00Z',
    )
)
def test_send_guest_new_task__task_due_date__is_str__ok(
    task_due_date,
    mocker
):

    # arrange
    token = '!@#sadd1'
    sender_name = 'Joe'
    recipient_id = 1233
    recipient_email = 'guest@guest.guest'
    task_id = 11
    task_name = 'Task name'
    task_description = 'Some markdown description'
    logo_lg = 'https://site.com/logo-lg.jpg'

    html_description = '<div>text</div>'
    html_service_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.convert_text_to_html',
        return_value=html_description
    )
    send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService._send'
    )
    formatted_task_due_in = '1 hour'
    get_duration_format_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.get_duration_format',
        return_value=formatted_task_due_in,
    )
    service = EmailService()

    # act
    service.send_guest_new_task(
        token=token,
        user_id=recipient_id,
        sender_name=sender_name,
        user_email=recipient_email,
        task_id=task_id,
        task_name=task_name,
        task_description=task_description,
        task_due_date=task_due_date,
        logo_lg=logo_lg,
    )

    # assert
    html_service_mock.assert_called_once_with(task_description)
    get_duration_format_mock.assert_called_once()
    send_mock.assert_called_once_with(
        user_id=recipient_id,
        recipient_email=recipient_email,
        template_code=EmailTemplate.GUEST_NEW_TASK,
        method_name=NotificationMethod.guest_new_task,
        data={
            'token': token,
            'user_id': recipient_id,
            'task_id': task_id,
            'task_name': task_name,
            'task_description': html_description,
            'sender_name': sender_name,
            'logo_lg': logo_lg,
            'overdue': formatted_task_due_in
        }
    )


def test_send_unread_notifications__ok(mocker):

    # arrange
    recipient_id = 1233
    recipient_email = 'guest@guest.guest'
    recipient_first_name = 'John'
    logo_lg = None

    send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService._send'
    )
    unsubscribe_token = '!@#sadd1'
    unsubscribe_token_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'UnsubscribeEmailToken.create_token',
        return_value=unsubscribe_token
    )
    service = EmailService()

    # act
    service.send_unread_notifications(
        user_id=recipient_id,
        user_first_name=recipient_first_name,
        user_email=recipient_email,
        logo_lg=logo_lg,
    )

    # assert
    unsubscribe_token_mock.assert_called_once_with(
        user_id=recipient_id,
        email_type=MailoutType.COMMENTS,
    )
    send_mock.assert_called_once_with(
        user_id=recipient_id,
        recipient_email=recipient_email,
        template_code=EmailTemplate.UNREAD_NOTIFICATIONS,
        method_name=NotificationMethod.unread_notifications,
        data={
            'user_name': recipient_first_name,
            'unsubscribe_token': unsubscribe_token,
            'logo_lg': logo_lg
        }
    )


def test_send_new_task__ok(mocker):

    # arrange
    recipient_id = 1233
    recipient_email = 'guest@guest.guest'
    task_id = 11
    task_name = 'Task name'
    template_name = 'Template name'
    workflow_name = 'Workflow name'
    logo_lg = 'https://site.com/logo-lg.jpg'
    html_description = '<div>text</div>'
    wf_starter_name = 'Some wf starter'
    wf_starter_photo = 'https://site.com/photo.jpg'
    due_in = '15 days 6 hours 23 minutes'
    overdue = '6 hours 1 minutes'

    unsubscribe_token = '123123'
    create_unsubscribe_token_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'UnsubscribeEmailToken.create_token',
        return_value=unsubscribe_token
    )
    send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService._send'
    )
    service = EmailService()

    # act
    service.send_new_task(
        user_id=recipient_id,
        user_email=recipient_email,
        logo_lg=logo_lg,
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
        sync=True
    )

    # assert
    send_mock.assert_called_once_with(
        user_id=recipient_id,
        recipient_email=recipient_email,
        template_code=EmailTemplate.NEW_TASK,
        method_name=NotificationMethod.new_task,
        data={
            'template': template_name,
            'workflow_name': workflow_name,
            'task_name': task_name,
            'due_in': due_in,
            'overdue': overdue,
            'task_description': html_description,
            'task_id': task_id,
            'unsubscribe_token': unsubscribe_token,
            'logo_lg': logo_lg,
            'started_by': {
                'name': wf_starter_name,
                'avatar': wf_starter_photo,
            }
        }
    )
    create_unsubscribe_token_mock.assert_called_once_with(
        user_id=recipient_id,
        email_type=MailoutType.NEW_TASK,
    )


def test_send_returned_task__ok(mocker):

    # arrange
    recipient_id = 1233
    recipient_email = 'guest@guest.guest'
    task_id = 11
    task_name = 'Task name'
    template_name = 'Template name'
    workflow_name = 'Workflow name'
    logo_lg = 'https://site.com/logo-lg.jpg'
    html_description = '<div>text</div>'
    wf_starter_name = 'Some wf starter'
    wf_starter_photo = 'https://site.com/photo.jpg'
    due_in = '15 days 6 hours 23 minutes'
    overdue = '6 hours 1 minutes'

    unsubscribe_token = '123123'
    create_unsubscribe_token_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'UnsubscribeEmailToken.create_token',
        return_value=unsubscribe_token
    )
    send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService._send'
    )
    service = EmailService()

    # act
    service.send_returned_task(
        user_id=recipient_id,
        user_email=recipient_email,
        logo_lg=logo_lg,
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
        sync=True
    )

    # assert
    send_mock.assert_called_once_with(
        user_id=recipient_id,
        recipient_email=recipient_email,
        template_code=EmailTemplate.TASK_RETURNED,
        method_name=NotificationMethod.returned_task,
        data={
            'template': template_name,
            'workflow_name': workflow_name,
            'task_name': task_name,
            'due_in': due_in,
            'overdue': overdue,
            'task_description': html_description,
            'task_id': task_id,
            'unsubscribe_token': unsubscribe_token,
            'logo_lg': logo_lg,
            'started_by': {
                'name': wf_starter_name,
                'avatar': wf_starter_photo,
            }
        }
    )
    create_unsubscribe_token_mock.assert_called_once_with(
        user_id=recipient_id,
        email_type=MailoutType.NEW_TASK,
    )


def test_send_reset_password__ok(mocker):

    # arrange
    recipient_id = 1233
    recipient_email = 'test@user.com'
    logo_lg = 'https://site.com/logo-lg.jpg'
    token = '!@#sadd1'
    reset_password_token_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'ResetPasswordToken.for_user_id',
        return_value=token
    )
    send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService._send'
    )
    service = EmailService()

    # act
    service.send_reset_password(
        user_id=recipient_id,
        user_email=recipient_email,
        logo_lg=logo_lg,
    )

    # assert
    reset_password_token_mock.assert_called_once_with(recipient_id)
    send_mock.assert_called_once_with(
        user_id=recipient_id,
        recipient_email=recipient_email,
        template_code=EmailTemplate.RESET_PASSWORD,
        method_name=NotificationMethod.reset_password,
        data={
            'token': token,
            'logo_lg': logo_lg,
        }
    )
