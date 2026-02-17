import pytest
from firebase_admin.exceptions import (
    FirebaseError,
    InvalidArgumentError,
)
from firebase_admin.messaging import (
    Notification as PushNotification,
)
from firebase_admin.messaging import (
    SenderIdMismatchError,
    UnregisteredError,
)

from src.accounts.enums import UserType
from src.logs.enums import AccountEventStatus
from src.logs.service import AccountLogService
from src.notifications.enums import NotificationMethod
from src.notifications.models import Device, UserNotifications
from src.notifications.services.exceptions import (
    NotificationServiceError,
)
from src.notifications.services.push import (
    PushNotificationService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_guest,
    create_test_user,
    create_test_owner,
)
from src.utils.logging import SentryLogLevel
from src.notifications import messages


pytestmark = pytest.mark.django_db


class TestPushNotificationService:

    def test_send__ok(self, mocker):

        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_user(account=account)
        method_name = 'test_method_name'
        title = 'test title'
        body = 'body message'
        extra_data = {'extra': 'extra'}
        settings_mock = mocker.patch(
            'src.notifications.services.push.settings',
        )
        settings_mock.PROJECT_CONF = {'PUSH': True}
        mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService.ALLOWED_METHODS',
            {method_name},
        )
        send_to_browsers_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._send_to_browsers',
        )
        send_to_apps_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._send_to_apps',
        )
        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )
        handle_error_mock = mocker.patch.object(service, '_handle_error')

        # act
        service._send(
            title=title,
            body=body,
            method_name=method_name,
            extra_data=extra_data,
            user_id=user.id,
            user_email=user.email,
        )

        # assert
        handle_error_mock.assert_not_called()
        send_to_browsers_mock.assert_called_once_with(
            title=title,
            body=body,
            user_id=user.id,
            user_email=user.email,
            data={
                'method': method_name,
                'title': title,
                'body': body,
                **extra_data,
            },
        )
        send_to_apps_mock.assert_called_once_with(
            title=title,
            body=body,
            user_id=user.id,
            user_email=user.email,
            data={
                'method': method_name,
                'title': title,
                'body': body,
                **extra_data,
            },
        )

    def test_send__not_allowed_method__raise_error(self, mocker):

        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_user(account=account)
        title = 'test title'
        body = 'body message'
        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )
        settings_mock = mocker.patch(
            'src.notifications.services.push.settings',
        )
        settings_mock.PROJECT_CONF = {'PUSH': True}
        handle_error_mock = mocker.patch.object(service, '_handle_error')
        send_to_browsers_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._send_to_browsers',
        )
        send_to_apps_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._send_to_apps',
        )

        # act
        with pytest.raises(NotificationServiceError) as ex:
            service._send(
                title=title,
                body=body,
                method_name='error',
                user_id=user.id,
                user_email=user.email,
                extra_data={},
            )

        # assert
        assert ex.value.message == 'error is not allowed notification'
        handle_error_mock.assert_not_called()
        send_to_browsers_mock.assert_not_called()
        send_to_apps_mock.assert_not_called()

    def test_send__disable_push__skip(self, mocker):

        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_user(account=account)
        method_name = 'test_method_name'
        body = 'body_param_text'
        title = 'test title'
        extra_data = {'extra': 'extra'}
        settings_mock = mocker.patch(
            'src.notifications.services.push.settings',
        )
        settings_mock.PROJECT_CONF = {'PUSH': False}
        mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService.ALLOWED_METHODS',
            {method_name},
        )
        send_to_browsers_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._send_to_browsers',
        )
        send_to_apps_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._send_to_apps',
        )
        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )

        # act
        service._send(
            title=title,
            body=body,
            method_name=method_name,
            extra_data=extra_data,
            user_id=user.id,
            user_email=user.email,
        )

        # assert
        send_to_browsers_mock.assert_not_called()
        send_to_apps_mock.assert_not_called()

    def test_send_to_browsers__ok(
        self,
        mocker,
    ):
        # arrange

        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_user(account=account)
        device = Device.objects.create(
            user=user,
            token='token',
            is_app=False,
        )
        title = 'test title'
        body = 'test body'
        data = {'title': title, 'extra': 'extra'}

        push_notification = PushNotification(title=title, body=body)
        push_notification_mock = mocker.patch(
            'src.notifications.services.push.PushNotification',
            return_value=push_notification,
        )

        message_mock = mocker.Mock()
        create_message_mock = mocker.patch(
            'src.notifications.services.push.messaging.Message',
            return_value=message_mock,
        )
        send_mock = mocker.patch(
            'src.notifications.services.push.messaging.send',
            return_value='msg_id',
        )
        log_service_init_mock = mocker.patch.object(
            AccountLogService,
            attribute='__init__',
            return_value=None,
        )
        log_push_mock = mocker.patch(
            'src.notifications.services.push.AccountLogService'
            '.push_notification',
        )
        handle_error_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._handle_error',
        )
        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )

        # act
        service._send_to_browsers(
            title=title,
            body=body,
            user_id=user.id,
            user_email=user.email,
            data=data,
        )

        # assert
        push_notification_mock.assert_called_once_with(
            title=title,
            body=body,
        )
        create_message_mock.assert_called_once_with(
            data=data,
            notification=push_notification,
            token=device.token,
        )
        handle_error_mock.assert_not_called()
        send_mock.assert_called_once_with(message_mock)
        log_service_init_mock.assert_not_called()
        log_push_mock.assert_not_called()

    def test_send_to_browsers__enable_logging__ok(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=True,
        )
        user = create_test_user(account=account)
        device = Device.objects.create(
            user=user,
            token='token',
            is_app=False,
        )
        title = 'test title'
        body = 'test body'
        data = {'title': title, 'extra': 'extra'}

        push_notification = PushNotification(title=title, body=body)
        push_notification_mock = mocker.patch(
            'src.notifications.services.push.PushNotification',
            return_value=push_notification,
        )

        message_mock = mocker.Mock()
        create_message_mock = mocker.patch(
            'src.notifications.services.push.messaging.Message',
            return_value=message_mock,
        )
        send_mock = mocker.patch(
            'src.notifications.services.push.messaging.send',
            return_value='msg_id',
        )
        log_service_init_mock = mocker.patch.object(
            AccountLogService,
            attribute='__init__',
            return_value=None,
        )
        log_push_mock = mocker.patch(
            'src.notifications.services.push.AccountLogService'
            '.push_notification',
        )
        handle_error_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._handle_error',
        )
        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )

        # act
        service._send_to_browsers(
            title=title,
            body=body,
            user_id=user.id,
            user_email=user.email,
            data=data,
        )

        # assert
        push_notification_mock.assert_called_once_with(
            title=title,
            body=body,
        )
        create_message_mock.assert_called_once_with(
            data=data,
            notification=push_notification,
            token=device.token,
        )
        handle_error_mock.assert_not_called()
        send_mock.assert_called_once_with(message_mock)
        log_service_init_mock.assert_called_once()
        log_push_mock.assert_called_once_with(
            title=f'Push to browser: {user.email}: {data["title"]}',
            request_data=data,
            account_id=account.id,
            status=AccountEventStatus.SUCCESS,
        )

    def test_send_to_browsers__not_browser_device__skip(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_user(account=account)
        Device.objects.create(user=user, token='token', is_app=True)
        title = 'test title'
        body = 'test body'
        data = {'title': title, 'extra': 'extra'}

        create_message_mock = mocker.patch(
            'src.notifications.services.push.messaging.Message',
        )
        handle_error_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._handle_error',
        )

        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )

        # act
        service._send_to_browsers(
            title=title,
            body=body,
            user_id=user.id,
            user_email=user.email,
            data=data,
        )

        # assert
        create_message_mock.assert_not_called()
        handle_error_mock.assert_not_called()

    def test_send_to_browsers__error_response__call_handle_error(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_user(account=account)
        device = Device.objects.create(
            user=user,
            token='token',
            is_app=False,
        )
        title = 'test title'
        body = 'test body'
        data = {'title': title, 'extra': 'extra'}

        push_notification = PushNotification(title=title, body=body)
        push_notification_mock = mocker.patch(
            'src.notifications.services.push.PushNotification',
            return_value=push_notification,
        )

        message_mock = mocker.Mock()
        create_message_mock = mocker.patch(
            'src.notifications.services.push.messaging.Message',
            return_value=message_mock,
        )
        exception = FirebaseError(message='Error', code=13)
        send_mock = mocker.patch(
            'src.notifications.services.push.messaging.send',
            side_effect=exception,
        )
        log_service_init_mock = mocker.patch.object(
            AccountLogService,
            attribute='__init__',
            return_value=None,
        )
        log_push_mock = mocker.patch(
            'src.notifications.services.push.AccountLogService'
            '.push_notification',
        )
        handle_error_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._handle_error',
        )
        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )

        # act
        service._send_to_browsers(
            title=title,
            body=body,
            user_id=user.id,
            user_email=user.email,
            data=data,
        )

        # assert
        create_message_mock.assert_called_once_with(
            data=data,
            notification=push_notification,
            token=device.token,
        )
        push_notification_mock.assert_called_once_with(
            title=title,
            body=body,
        )
        send_mock.assert_called_once_with(message_mock)
        handle_error_mock.assert_called_once_with(
            token=device.token,
            exception=exception,
            user_id=user.id,
            user_email=user.email,
            data=data,
            device='browser',
        )
        log_service_init_mock.assert_not_called()
        log_push_mock.assert_not_called()

    def test_send_to_apps__enable_logging__ok(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=True,
        )
        user = create_test_user(account=account)
        counter = UserNotifications.objects.create(
            user=user,
            count_unread_push_in_ios_app=1,
        )
        device = Device.objects.create(user=user, token='token', is_app=True)
        title = 'test title'
        body = 'test body'
        data = {
            'extra': 'extra',
            'title': 'title',
        }

        push_notification = PushNotification(title=title, body=body)
        push_notification_mock = mocker.patch(
            'src.notifications.services.push.PushNotification',
            return_value=push_notification,
        )
        config_mock = mocker.Mock()
        apns_config_mock = mocker.patch(
            'src.notifications.services.push.Config',
            return_value=config_mock,
        )
        message_mock = mocker.Mock()
        create_message_mock = mocker.patch(
            'src.notifications.services.push.messaging.Message',
            return_value=message_mock,
        )
        send_mock = mocker.patch(
            'src.notifications.services.push.messaging.send',
            return_value='msg_id',
        )
        log_service_init_mock = mocker.patch.object(
            AccountLogService,
            attribute='__init__',
            return_value=None,
        )
        log_push_mock = mocker.patch(
            'src.notifications.services.push.AccountLogService'
            '.push_notification',
        )
        handle_error_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._handle_error',
        )
        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )

        # act
        service._send_to_apps(
            title=title,
            body=body,
            user_id=user.id,
            user_email=user.email,
            data=data,
        )

        # assert
        push_notification_mock.assert_called_once_with(
            title=title,
            body=body,
        )
        create_message_mock.assert_called_once_with(
            data=data,
            notification=push_notification,
            token=device.token,
            apns=config_mock,
        )
        handle_error_mock.assert_not_called()
        send_mock.assert_called_once_with(message_mock)
        apns_config_mock.assert_called_once()
        counter.refresh_from_db()
        assert counter.count_unread_push_in_ios_app == 2
        log_service_init_mock.assert_called_once()
        log_push_mock.assert_called_once_with(
            title=f'Push to app: {user.email}: {data["title"]}',
            request_data=data,
            account_id=account.id,
            status=AccountEventStatus.SUCCESS,
        )

    def test_send_to_apps__ok(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_user(account=account)
        counter = UserNotifications.objects.create(
            user=user,
            count_unread_push_in_ios_app=1,
        )
        device = Device.objects.create(user=user, token='token', is_app=True)
        title = 'test title'
        body = 'test body'
        data = {'title': title, 'extra': 'extra'}

        push_notification = PushNotification(title=title, body=body)
        push_notification_mock = mocker.patch(
            'src.notifications.services.push.PushNotification',
            return_value=push_notification,
        )
        config_mock = mocker.Mock()
        apns_config_mock = mocker.patch(
            'src.notifications.services.push.Config',
            return_value=config_mock,
        )
        message_mock = mocker.Mock()
        create_message_mock = mocker.patch(
            'src.notifications.services.push.messaging.Message',
            return_value=message_mock,
        )
        send_mock = mocker.patch(
            'src.notifications.services.push.messaging.send',
            return_value='msg_id',
        )
        log_service_init_mock = mocker.patch.object(
            AccountLogService,
            attribute='__init__',
            return_value=None,
        )
        log_push_mock = mocker.patch(
            'src.notifications.services.push.AccountLogService'
            '.push_notification',
        )
        handle_error_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._handle_error',
        )

        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )

        # act
        service._send_to_apps(
            title=title,
            body=body,
            user_id=user.id,
            user_email=user.email,
            data=data,
        )

        # assert
        push_notification_mock.assert_called_once_with(
            title=title,
            body=body,
        )
        create_message_mock.assert_called_once_with(
            data=data,
            notification=push_notification,
            token=device.token,
            apns=config_mock,
        )
        handle_error_mock.assert_not_called()
        send_mock.assert_called_once_with(message_mock)
        apns_config_mock.assert_called_once()
        counter.refresh_from_db()
        assert counter.count_unread_push_in_ios_app == 2
        log_service_init_mock.assert_not_called()
        log_push_mock.assert_not_called()

    def test_send_to_apps__not_app_device__skip(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_user(account=account)
        Device.objects.create(user=user, token='token', is_app=False)
        title = 'test title'
        body = 'test body'
        data = {'title': title, 'extra': 'extra'}

        create_message_mock = mocker.patch(
            'src.notifications.services.push.messaging.Message',
        )
        log_service_init_mock = mocker.patch.object(
            AccountLogService,
            attribute='__init__',
            return_value=None,
        )
        log_push_mock = mocker.patch(
            'src.notifications.services.push.AccountLogService'
            '.push_notification',
        )
        handle_error_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._handle_error',
        )

        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )

        # act
        service._send_to_apps(
            title=title,
            body=body,
            user_id=user.id,
            user_email=user.email,
            data=data,
        )

        # assert
        create_message_mock.assert_not_called()
        handle_error_mock.assert_not_called()
        log_service_init_mock.assert_not_called()
        log_push_mock.assert_not_called()

    def test_send_to_apps__error_response__call_handle_error(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_user(account=account)
        UserNotifications.objects.create(user=user)
        device = Device.objects.create(user=user, token='token', is_app=True)
        title = 'test title'
        body = 'test body'
        data = {'title': title, 'extra': 'extra'}

        push_notification = PushNotification(title=title, body=body)
        push_notification_mock = mocker.patch(
            'src.notifications.services.push.PushNotification',
            return_value=push_notification,
        )
        config_mock = mocker.Mock()
        apns_config_mock = mocker.patch(
            'src.notifications.services.push.Config',
            return_value=config_mock,
        )
        message_mock = mocker.Mock()
        create_message_mock = mocker.patch(
            'src.notifications.services.push.messaging.Message',
            return_value=message_mock,
        )
        exception = FirebaseError(message='Error', code=13)
        send_mock = mocker.patch(
            'src.notifications.services.push.messaging.send',
            side_effect=exception,
        )
        log_service_init_mock = mocker.patch.object(
            AccountLogService,
            attribute='__init__',
            return_value=None,
        )
        log_push_mock = mocker.patch(
            'src.notifications.services.push.AccountLogService'
            '.push_notification',
        )
        handle_error_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._handle_error',
        )

        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )

        # act
        service._send_to_apps(
            title=title,
            body=body,
            user_id=user.id,
            user_email=user.email,
            data=data,
        )

        # assert
        push_notification_mock.assert_called_once_with(
            title=title,
            body=body,
        )
        create_message_mock.assert_called_once_with(
            data=data,
            notification=push_notification,
            token=device.token,
            apns=config_mock,
        )
        send_mock.assert_called_once_with(message_mock)
        handle_error_mock.assert_called_once_with(
            token=device.token,
            exception=exception,
            user_id=user.id,
            user_email=user.email,
            data=data,
            device='app',
        )
        apns_config_mock.assert_called_once()
        log_service_init_mock.assert_not_called()
        log_push_mock.assert_not_called()

    @pytest.mark.parametrize(
        'exception', (
            InvalidArgumentError(message='invalid token'),
            UnregisteredError(message='unregistered token'),
            SenderIdMismatchError(message='unregistered token'),
        ),
    )
    def test_handle_error__broken_token__delete_device(
        self,
        exception,
        mocker,
    ):
        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_user(account=account)
        device = Device(
            user=user,
            token='token',
        )
        device.save()
        broken_device = Device(
            user=user,
            token='broken token',
        )
        broken_device.save()
        log_service_init_mock = mocker.patch.object(
            AccountLogService,
            attribute='__init__',
            return_value=None,
        )
        log_push_mock = mocker.patch(
            'src.notifications.services.push.AccountLogService'
            '.push_notification',
        )
        data = mocker.Mock()
        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )

        # act
        service._handle_error(
            token=broken_device.token,
            exception=exception,
            user_id=user.id,
            user_email=user.email,
            data=data,
            device='browser',
        )

        # assert
        assert not Device.objects.filter(token=broken_device.token).exists()
        log_service_init_mock.assert_not_called()
        log_push_mock.assert_not_called()

    def test_handle_error__firebase_error__capture_sentry(self, mocker):
        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_user(account=account)
        device = Device(
            user=user,
            token='token',
        )
        device.save()
        broken_device = Device(
            user=user,
            token='broken token',
        )
        broken_device.save()
        message = 'Error'
        code = 400
        response_mock = mocker.Mock()
        exception = FirebaseError(
            code=code,
            message=message,
            http_response=response_mock,
            cause=None,
        )
        capture_sentry_message = mocker.patch(
            'src.notifications.services.push.'
            'capture_sentry_message',
        )
        log_service_init_mock = mocker.patch.object(
            AccountLogService,
            attribute='__init__',
            return_value=None,
        )
        log_push_mock = mocker.patch(
            'src.notifications.services.push.AccountLogService'
            '.push_notification',
        )
        data = {
            'title': 'Some title',
        }

        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )

        # act
        service._handle_error(
            token=broken_device.token,
            exception=exception,
            user_id=user.id,
            user_email=user.email,
            data=data,
            device='browser',
        )

        # assert
        capture_sentry_message.assert_called_once_with(
            message=f'Push notification sending error. User: {user.id}',
            data={
                'user_email': user.email,
                'user_id': user.id,
                'device_token': broken_device.token,
                'exception_type': str(type(exception)),
                'message': message,
                'code': str(code),
                'cause': str(None),
                'http_response': str(response_mock),
            },
            level=SentryLogLevel.ERROR,
        )
        assert Device.objects.filter(token=broken_device.token).exists()
        log_service_init_mock.assert_not_called()
        log_push_mock.assert_not_called()

    def test_handle_error__enable_logging__create_account_log(self, mocker):
        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=True,
        )
        user = create_test_user(account=account)
        Device.objects.create(
            user=user,
            token='token',
        )
        broken_device = Device(
            user=user,
            token='broken token',
        )
        broken_device.save()
        message = 'Error'
        code = 400
        response_mock = mocker.Mock()
        exception = FirebaseError(
            code=code,
            message=message,
            http_response=response_mock,
            cause=None,
        )
        capture_sentry_message = mocker.patch(
            'src.notifications.services.push.'
            'capture_sentry_message',
        )
        log_service_init_mock = mocker.patch.object(
            AccountLogService,
            attribute='__init__',
            return_value=None,
        )
        log_push_mock = mocker.patch(
            'src.notifications.services.push.AccountLogService'
            '.push_notification',
        )
        data = {'title': 'Some title'}
        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )

        # act
        service._handle_error(
            token=broken_device.token,
            exception=exception,
            user_id=user.id,
            user_email=user.email,
            data=data,
            device='browser',
        )

        # assert
        capture_sentry_message.assert_called_once()
        assert Device.objects.filter(token=broken_device.token).exists()
        log_service_init_mock.assert_called_once()
        log_push_mock.assert_called_once_with(
            title=f'Push to browser {user.email}: {data["title"]}',
            request_data=data,
            account_id=user.account_id,
            status=AccountEventStatus.FAILED,
            response_data={
                'user_id': user.id,
                'user_email': user.email,
                'device_token': broken_device.token,
                'message': message,
                'exception_type': str(type(exception)),
                'code': str(code),
                'cause': str(None),
                'http_response': str(response_mock),
            },
        )

    def test_send_new_task(self, mocker):

        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_user(account=account)
        task_name = 'Task'
        workflow_name = 'Workflow'
        text_description = 'text description'
        send_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._send',
        )
        link = 'http://localhost/tasks/1'
        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )

        # act
        service.send_new_task(
            link=link,
            task_id=1,
            task_name=task_name,
            workflow_name=workflow_name,
            user_id=user.id,
            user_email=user.email,
            text_description=text_description,
            sync=True,
        )

        # assert
        send_mock.assert_called_once_with(
            method_name=NotificationMethod.new_task,
            title='You have a new task',
            body=f'Workflow: {workflow_name}\nTask: {task_name}',
            extra_data={'task_id': '1', 'link': link},
            user_id=user.id,
            user_email=user.email,
        )

    def test_send_returned_task(self, mocker):

        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_user(account=account)
        task_name = 'Task'
        workflow_name = 'Workflow'
        text_description = 'text description'
        send_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._send',
        )
        link = 'http://localhost/tasks/1'
        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )

        # act
        service.send_returned_task(
            link=link,
            task_id=1,
            task_name=task_name,
            workflow_name=workflow_name,
            user_id=user.id,
            user_email=user.email,
            text_description=text_description,
            sync=True,
        )

        # assert
        send_mock.assert_called_once_with(
            method_name=NotificationMethod.returned_task,
            title='Task was returned',
            body=f'Workflow: {workflow_name}\nTask: {task_name}',
            extra_data={'task_id': '1', 'link': link},
            user_id=user.id,
            user_email=user.email,
        )

    def test_send_overdue_task__user__ok(self, mocker):

        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_user(account=account)

        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )
        send_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._send',
        )
        task_name = 'Task'
        workflow_name = 'Workflow'
        link = 'http://localhost/tasks/1'

        # act
        service.send_overdue_task(
            link=link,
            task_id=1,
            task_name=task_name,
            workflow_name=workflow_name,
            user_id=user.id,
            user_email=user.email,
            user_type=UserType.USER,
        )

        # assert
        send_mock.assert_called_once_with(
            title='Your task is overdue',
            body=f'Workflow: {workflow_name}\nTask: {task_name}',
            method_name=NotificationMethod.overdue_task,
            extra_data={'task_id': '1', 'link': link},
            user_id=user.id,
            user_email=user.email,
        )

    def test_send_overdue_task__guest__not_send(self, mocker):

        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_user(account=account)
        guest = create_test_guest(account=user.account)
        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )

        send_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._send',
        )
        link = 'http://localhost/tasks/1'

        # act
        service.send_overdue_task(
            link=link,
            task_id=1,
            task_name='Task',
            workflow_name='Workflow',
            user_id=guest.id,
            user_email=user.email,
            user_type=UserType.GUEST,
        )

        # assert
        send_mock.assert_not_called()

    def test_send_complete_task(self, mocker):

        # arrange

        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_user(account=account)

        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )

        send_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._send',
        )
        task_name = 'Task'
        workflow_name = 'Workflow'
        link = 'http://localhost/tasks/1'

        # act
        service.send_complete_task(
            link=link,
            task_id=1,
            task_name=task_name,
            workflow_name=workflow_name,
            user_id=user.id,
            user_email=user.email,
            sync=True,
        )

        # assert
        send_mock.assert_called_once_with(
            method_name=NotificationMethod.complete_task,
            title='Task was completed',
            body=f'Workflow: {workflow_name}\nTask: {task_name}',
            extra_data={'task_id': '1', 'link': link},
            user_id=user.id,
            user_email=user.email,
        )

    def test_send_mention(self, mocker):

        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_user(account=account)
        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )
        send_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._send',
        )
        link = 'http://localhost/tasks/1'

        # act
        service.send_mention(
            link=link,
            task_id=1,
            user_id=user.id,
            user_email=user.email,
        )

        # assert
        send_mock.assert_called_once_with(
            title='You have been mentioned',
            body='',
            method_name=NotificationMethod.mention,
            extra_data={'task_id': '1', 'link': link},
            user_id=user.id,
            user_email=user.email,
        )

    def test_send_comment(self, mocker):

        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_user(account=account)
        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )
        send_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._send',
        )
        link = 'http://localhost/tasks/1'

        # act
        service.send_comment(
            link=link,
            task_id=1,
            user_id=user.id,
            user_email=user.email,
        )

        # assert
        send_mock.assert_called_once_with(
            title='You have a new comment',
            body='',
            method_name=NotificationMethod.comment,
            extra_data={'task_id': '1', 'link': link},
            user_id=user.id,
            user_email=user.email,
        )

    def test_send_delay_workflow__ok(self, mocker):

        # arrange
        workflow_name = 'Workflow'
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_user(account=account)
        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )
        send_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._send',
        )
        link = 'http://localhost/workflows/1'

        # act
        service.send_delay_workflow(
            user_id=user.id,
            user_email=user.email,
            task_id=1,
            workflow_id=3,
            workflow_name=workflow_name,
            link=link,
        )

        # assert
        send_mock.assert_called_once_with(
            method_name=NotificationMethod.delay_workflow,
            title='Workflow was snoozed',
            body=workflow_name,
            extra_data={
                'workflow_id': '3',
                'task_id': '1',
                'link': link,
            },
            user_id=user.id,
            user_email=user.email,
        )

    def test_send_resume_workflow__ok(self, mocker):

        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_user(account=account)
        workflow_name = 'Workflow'
        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )
        send_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._send',
        )
        link = 'http://localhost/workflows/1'

        # act
        service.send_resume_workflow(
            link=link,
            user_id=user.id,
            user_email=user.email,
            task_id=1,
            workflow_id=3,
            workflow_name=workflow_name,
        )

        # assert
        send_mock.assert_called_once_with(
            method_name=NotificationMethod.resume_workflow,
            title='Workflow was resumed',
            body=workflow_name,
            extra_data={
                'workflow_id': '3',
                'task_id': '1',
                'link': link,
            },
            user_id=user.id,
            user_email=user.email,
        )

    def test_send_due_date_changed(self, mocker):

        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_user(account=account)
        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )
        send_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._send',
        )
        task_name = 'Task'
        workflow_name = 'Workflow'
        link = 'http://localhost/tasks/1'

        # act
        service.send_due_date_changed(
            link=link,
            task_id=1,
            task_name=task_name,
            workflow_name=workflow_name,
            user_id=user.id,
            user_email=user.email,
        )

        # assert
        send_mock.assert_called_once_with(
            method_name=NotificationMethod.due_date_changed,
            title='Task due date was changed',
            body=f'Workflow: {workflow_name}\nTask: {task_name}',
            extra_data={'task_id': '1', 'link': link},
            user_id=user.id,
            user_email=user.email,
        )

    def test_send_reaction(self, mocker):

        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_user(account=account)
        reaction_user = create_test_user(
            account=account,
            email='t@t.t',
            is_account_owner=False,
            first_name='author',
            last_name='message',
        )
        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )
        send_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._send',
        )
        text = ':dumb face:'
        workflow_name = 'some name'
        link = 'http://localhost/tasks/1'

        # act
        service.send_reaction(
            task_id=1,
            user_id=user.id,
            user_email=user.email,
            author_name=reaction_user.name,
            workflow_name=workflow_name,
            text=text,
            link=link,
        )

        # assert
        send_mock.assert_called_once_with(
            title=reaction_user.name,
            body=f'{workflow_name}\n{text}',
            method_name=NotificationMethod.reaction,
            extra_data={
                'link': link,
                'task_id': '1',
                'text': text,
                'user_id': str(user.id),
            },
            user_id=user.id,
            user_email=user.email,
        )

    def test_send_complete_workflow(self, mocker):

        # arrange
        account = create_test_account(
            logo_lg='https://logo.com',
            log_api_requests=False,
        )
        user = create_test_owner(account=account)
        service = PushNotificationService(
            account_id=account.id,
            logo_lg=account.logo_lg,
            logging=account.log_api_requests,
        )
        send_mock = mocker.patch(
            'src.notifications.services.push.'
            'PushNotificationService._send',
        )
        workflow_id = 3
        workflow_name = 'some name'
        link = f'http://localhost/workflows/{workflow_id}'

        # act
        service.send_complete_workflow(
            link=link,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            user_id=user.id,
            user_email=user.email,
        )

        # assert
        send_mock.assert_called_once_with(
            method_name=NotificationMethod.complete_workflow,
            title=str(messages.MSG_NF_0021),
            body=workflow_name,
            extra_data={
                'link': link,
                'workflow_id': str(workflow_id),
            },
            user_id=user.id,
            user_email=user.email,
        )
