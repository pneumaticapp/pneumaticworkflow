from typing import Dict
from django.conf import settings
from django.contrib.auth import get_user_model
from firebase_admin import messaging
from firebase_admin.exceptions import (
    InvalidArgumentError,
    FirebaseError,
)
from firebase_admin.messaging import (
    Notification as PushNotification,
    UnregisteredError,
    SenderIdMismatchError,
    Aps,
    APNSPayload,
    APNSConfig as Config,
)

from pneumatic_backend.accounts.enums import UserType
from pneumatic_backend.notifications.enums import (
    NotificationMethod,
)
from pneumatic_backend.notifications import messages
from pneumatic_backend.notifications.models import Device, UserNotifications
from pneumatic_backend.notifications.services.base import (
    NotificationService,
)
from pneumatic_backend.utils.logging import (
    capture_sentry_message,
    SentryLogLevel,
)
from pneumatic_backend.logs.service import AccountLogService
from pneumatic_backend.logs.enums import (
    AccountEventStatus,
)


UserModel = get_user_model()


class PushNotificationService(NotificationService):

    ALLOWED_METHODS = {
        NotificationMethod.new_task,
        NotificationMethod.complete_task,
        NotificationMethod.returned_task,
        NotificationMethod.overdue_task,
        NotificationMethod.mention,
        NotificationMethod.comment,
        NotificationMethod.delay_workflow,
        NotificationMethod.resume_workflow,
        NotificationMethod.due_date_changed,
        NotificationMethod.reaction,
    }

    def _send_to_browsers(
        self,
        title: str,
        body: str,
        user_id: int,
        data: dict,
    ):
        browser_tokens = (
            Device.objects
            .by_user(user_id)
            .active()
            .browser()
            .values_list('token', flat=True)
        )
        for device_token in browser_tokens:
            message = messaging.Message(
                notification=PushNotification(
                    title=title,
                    body=body
                ),
                data=data,
                token=device_token,
            )
            try:
                messaging.send(message)
            except FirebaseError as exception:
                self._handle_error(
                    token=device_token,
                    exception=exception,
                    user_id=user_id,
                    data=data,
                    device='browser'
                )
            else:
                if self.logging:
                    user = UserModel.objects.get(id=user_id)
                    AccountLogService().push_notification(
                        path=f'Push to browser: {user.email}: {data["title"]}',
                        body=data,
                        account_id=user.account_id,
                        status=AccountEventStatus.SUCCESS,
                    )

    def _send_to_apps(
        self,
        title: str,
        body: str,
        user_id: int,
        data: dict,
    ):
        app_tokens = (
            Device.objects
            .by_user(user_id)
            .active()
            .app()
            .values_list('token', flat=True)
        )
        for device_token in app_tokens:
            counter = UserNotifications.objects.get(user_id=user_id)
            counter.count_unread_push_in_ios_app += 1
            counter.save()
            message = messaging.Message(
                notification=PushNotification(
                    title=title,
                    body=body
                ),
                data=data,
                token=device_token,
                apns=Config(
                    payload=APNSPayload(
                        aps=Aps(
                            sound='default',
                            badge=counter.count_unread_push_in_ios_app
                        )
                    )
                )
            )
            try:
                messaging.send(message)
            except FirebaseError as exception:
                self._handle_error(
                    token=device_token,
                    exception=exception,
                    user_id=user_id,
                    data=data,
                    device='app'
                )
            else:
                if self.logging:
                    user = UserModel.objects.get(id=user_id)
                    AccountLogService().push_notification(
                        path=f'Push to app: {user.email}: {data["title"]}',
                        body=data,
                        account_id=user.account_id,
                        status=AccountEventStatus.SUCCESS,
                    )

    def _send(
        self,
        method_name: NotificationMethod.LITERALS,
        user_id: int,
        extra_data: Dict[str, str],
        title: str,
        body: str,
    ):
        self._validate_send(method_name)

        if not settings.PROJECT_CONF['PUSH']:
            return

        data = {
            'method': method_name,
            'title': title,
            'body': body,
            **extra_data
        }
        self._send_to_browsers(
            title=title,
            body=body,
            user_id=user_id,
            data=data
        )
        self._send_to_apps(
            title=title,
            body=body,
            user_id=user_id,
            data=data
        )

    def _handle_error(
        self,
        token: str,
        user_id: int,
        exception: FirebaseError,
        data: dict,
        device: str,
    ):
        user = UserModel.objects.get(id=user_id)
        if self.logging:
            AccountLogService().push_notification(
                path=f'Push to {device} {user.email}: {data["title"]}',
                body=data,
                account_id=user.account_id,
                status=AccountEventStatus.FAILED,
                error={
                    'user_id': user_id,
                    'device_token': token,
                    'message': str(exception),
                    'exception_type': str(type(exception)),
                    'code': str(exception.code),
                    'cause': str(exception.cause),
                    'http_response': str(exception.http_response),
                }
            )
        if (
            isinstance(
                exception,
                (
                    InvalidArgumentError,
                    UnregisteredError,
                    SenderIdMismatchError,
                )
            )
        ):
            Device.objects.delete_by_token(token=token)
        else:
            capture_sentry_message(
                message=f'Push notification sending error. User: {user_id}',
                data={
                    'user': user.email if user else None,
                    'user_id': user_id,
                    'device_token': token,
                    'exception_type': str(type(exception)),
                    'message': str(exception),
                    'code': str(exception.code),
                    'cause': str(exception.cause),
                    'http_response': str(exception.http_response),
                },
                level=SentryLogLevel.ERROR,
            )

    def send_new_task(
        self,
        task_id: int,
        task_name: str,
        workflow_name: str,
        user_id: int,
        **kwargs
    ):
        self._send(
            method_name=NotificationMethod.new_task,
            title=str(messages.MSG_NF_0002),
            body=str(messages.MSG_NF_0011(workflow_name, task_name)),
            extra_data={'task_id': str(task_id)},
            user_id=user_id,
        )

    def send_complete_task(
        self,
        task_id: int,
        task_name: str,
        workflow_name: str,
        user_id: int,
        **kwargs
    ):
        self._send(
            method_name=NotificationMethod.complete_task,
            title=str(messages.MSG_NF_0012),
            body=str(messages.MSG_NF_0011(workflow_name, task_name)),
            extra_data={'task_id': str(task_id)},
            user_id=user_id,
        )

    def send_returned_task(
        self,
        task_id: int,
        task_name: str,
        workflow_name: str,
        user_id: int,
        **kwargs
    ):
        self._send(
            title=str(messages.MSG_NF_0003),
            body=str(messages.MSG_NF_0011(workflow_name, task_name)),
            method_name=NotificationMethod.returned_task,
            extra_data={'task_id': str(task_id)},
            user_id=user_id,
        )

    def send_overdue_task(
        self,
        user_id: int,
        user_type: UserType,
        task_id: int,
        task_name: str,
        workflow_name: str,
        **kwargs
    ):
        if user_type == UserType.USER:
            self._send(
                title=str(messages.MSG_NF_0004),
                body=str(messages.MSG_NF_0011(workflow_name, task_name)),
                method_name=NotificationMethod.overdue_task,
                extra_data={'task_id': str(task_id)},
                user_id=user_id,
            )

    def send_mention(
        self,
        task_id: int,
        user_id: int,
        **kwargs
    ):
        self._send(
            title=str(messages.MSG_NF_0005),
            body='',
            method_name=NotificationMethod.mention,
            extra_data={'task_id': str(task_id)},
            user_id=user_id,
        )

    def send_comment(
        self,
        task_id: int,
        user_id: int,
        **kwargs
    ):
        self._send(
            title=str(messages.MSG_NF_0006),
            body='',
            method_name=NotificationMethod.comment,
            extra_data={'task_id': str(task_id)},
            user_id=user_id,
        )

    def send_delay_workflow(
        self,
        user_id: int,
        task_id: int,
        workflow_name: str,
        author_id: int,
        **kwargs
    ):

        self._send(
            title=str(messages.MSG_NF_0007),
            body=workflow_name,
            method_name=NotificationMethod.delay_workflow,
            extra_data={
                'task_id': str(task_id),
                'author_id': str(author_id),
            },
            user_id=user_id,
        )

    def send_resume_workflow(
        self,
        user_id: int,
        task_id: int,
        workflow_name: str,
        author_id: int,
        **kwargs
    ):
        self._send(
            title=str(messages.MSG_NF_0008),
            body=workflow_name,
            method_name=NotificationMethod.resume_workflow,
            extra_data={
                'task_id': str(task_id),
                'author_id': str(author_id),
            },
            user_id=user_id,
        )

    def send_due_date_changed(
        self,
        task_id: int,
        task_name: str,
        workflow_name: str,
        user_id: int,
        **kwargs
    ):
        self._send(
            title=str(messages.MSG_NF_0009),
            body=str(messages.MSG_NF_0011(workflow_name, task_name)),
            method_name=NotificationMethod.due_date_changed,
            extra_data={'task_id': str(task_id)},
            user_id=user_id,
        )

    def send_reaction(
        self,
        task_id: int,
        user_id: int,
        author_name: str,
        workflow_name: str,
        text: str,
        **kwargs
    ):
        self._send(
            title=author_name,
            body=f'{workflow_name}\n{text}',
            method_name=NotificationMethod.reaction,
            extra_data={
                'task_id': str(task_id),
                'text': text,
                'user_id': str(user_id),
            },
            user_id=user_id,
        )
