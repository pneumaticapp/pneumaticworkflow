from datetime import datetime, timedelta
from django.utils import timezone
from typing import Dict, Optional, Union, Any
from django.contrib.auth import get_user_model
from django.conf import settings
from pneumatic_backend.notifications.enums import NotificationMethod
from pneumatic_backend.notifications.services.base import (
    NotificationService,
)
from customerio import SendEmailRequest, APIClient
from pneumatic_backend.analytics.enums import MailoutType
from pneumatic_backend.accounts.enums import UserType
from pneumatic_backend.services.html_converter import convert_text_to_html
from pneumatic_backend.processes.utils.common import get_duration_format
from pneumatic_backend.notifications.enums import (
    EmailTemplate,
    cio_template_ids,
)
from pneumatic_backend.accounts.tokens import (
    UnsubscribeEmailToken,
    ResetPasswordToken,
)
UserModel = get_user_model()


class EmailService(NotificationService):

    ALLOWED_METHODS = {
        NotificationMethod.new_task,
        NotificationMethod.returned_task,
        NotificationMethod.overdue_task,
        NotificationMethod.guest_new_task,
        NotificationMethod.unread_notifications,
        NotificationMethod.reset_password,
    }

    @staticmethod
    def _send_email_to_console(
        recipient_email: str,
        template_code: str,
        data: dict
    ):
        message_vars = ''
        for key, val in data.items():
            '\n'.join(f'- {key}: {val}')
        print(
            f'''
            -------------------------
            ------EMAIL-MESSAGE------
            To email: {recipient_email}
            Template name: {template_code}
            Message args:
            {message_vars}
            -------------------------
            '''
        )

    @staticmethod
    def _send_email_via_customerio(
        user_id: int,
        recipient_email: str,
        template_code: str,
        data: Dict[str, Any],
    ):
        client = APIClient(settings.CUSTOMERIO_TRANSACTIONAL_API_KEY)
        message_id = cio_template_ids[template_code]
        request = SendEmailRequest(
            to=recipient_email,
            transactional_message_id=message_id,
            message_data=data,
            identifiers={'id': user_id}
        )
        client.send_email(request)

    def _send(
        self,
        user_id: int,
        recipient_email: str,
        template_code: str,
        method_name: NotificationMethod,
        data: Dict[str, str],
    ):

        self._validate_send(method_name)

        if not settings.PROJECT_CONF['EMAIL']:
            return

        if settings.CONFIGURATION_CURRENT in (
            settings.CONFIGURATION_DEV,
            settings.CONFIGURATION_TESTING
        ):
            self._send_email_to_console(
                recipient_email=recipient_email,
                template_code=template_code,
                data=data,
            )
        else:
            self._send_email_via_customerio(
                user_id=user_id,
                recipient_email=recipient_email,
                template_code=template_code,
                data=data
            )

    def _handle_error(self, *args, **kwargs):
        pass

    def send_new_task(
        self,
        user_id: int,
        user_email: str,
        logo_lg: Optional[str],
        template_name: str,
        workflow_name: str,
        task_id: int,
        task_name: str,
        html_description: str,
        wf_starter_name: str,
        wf_starter_photo: Optional[str] = None,
        due_in: Optional[str] = None,
        overdue: Optional[str] = None,
        **kwargs
    ):

        unsubscribe_token = UnsubscribeEmailToken.create_token(
            user_id=user_id,
            email_type=MailoutType.NEW_TASK,
        ).__str__()

        data = {
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
        self._send(
            user_id=user_id,
            recipient_email=user_email,
            template_code=EmailTemplate.NEW_TASK,
            method_name=NotificationMethod.new_task,
            data=data
        )

    def send_returned_task(
        self,
        user_id: int,
        user_email: str,
        logo_lg: Optional[str],
        template_name: str,
        workflow_name: str,
        task_id: int,
        task_name: str,
        html_description: str,
        wf_starter_name: str,
        wf_starter_photo: Optional[str] = None,
        due_in: Optional[str] = None,
        overdue: Optional[str] = None,
        **kwargs
    ):

        unsubscribe_token = UnsubscribeEmailToken.create_token(
            user_id=user_id,
            email_type=MailoutType.NEW_TASK,
        ).__str__()

        data = {
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
        self._send(
            user_id=user_id,
            recipient_email=user_email,
            template_code=EmailTemplate.TASK_RETURNED,
            method_name=NotificationMethod.returned_task,
            data=data
        )

    def send_overdue_task(
        self,
        user_id: int,
        user_type: UserType.LITERALS,
        user_email: str,
        workflow_id: int,
        workflow_name: str,
        task_id: int,
        task_name: str,
        template_name: str,
        workflow_starter_id: int,
        workflow_starter_first_name: str,
        workflow_starter_last_name: str,
        logo_lg: Optional[str] = None,
        token: Optional[str] = None,
        **kwargs
    ):
        self._send(
            user_id=user_id,
            recipient_email=user_email,
            template_code=EmailTemplate.OVERDUE_TASK,
            method_name=NotificationMethod.overdue_task,
            data={
                'workflow_id': workflow_id,
                'workflow_name': workflow_name,
                'task_id': str(task_id),
                'task_name': task_name,
                'template_name': template_name,
                'workflow_starter_id': workflow_starter_id,
                'workflow_starter_first_name': workflow_starter_first_name,
                'workflow_starter_last_name': workflow_starter_last_name,
                'logo_lg': logo_lg,
                'user_type': user_type,
                'token': token,
            }
        )

    def send_guest_new_task(
        self,
        token: str,
        sender_name: str,
        user_id: int,
        user_email: str,
        task_id: int,
        task_name: str,
        task_description: str,
        task_due_date: Union[datetime, str, None] = None,
        logo_lg: Optional[str] = None,
        **kwargs
    ):
        description = (
            convert_text_to_html(task_description)
            if task_description else None
        )
        data = {
            'token': token,
            'user_id': user_id,
            'task_id': task_id,
            'task_name': task_name,
            'task_description': description,
            'sender_name': sender_name,
            'logo_lg': logo_lg
        }
        if task_due_date:
            # floating bug when task_estimated_end_date is string
            if isinstance(task_due_date, str):
                from django.utils.dateparse import parse_datetime
                task_due_date = parse_datetime(task_due_date)
            due_in: timedelta = task_due_date - timezone.now()
            formatted_date = get_duration_format(duration=due_in)
            if due_in.total_seconds() > 0:
                data['due_in'] = formatted_date
            else:
                data['overdue'] = formatted_date

        self._send(
            user_id=user_id,
            recipient_email=user_email,
            template_code=EmailTemplate.GUEST_NEW_TASK,
            method_name=NotificationMethod.guest_new_task,
            data=data,
        )

    def send_unread_notifications(
        self,
        user_id: int,
        user_first_name: str,
        user_email: str,
        logo_lg: Optional[str] = None,
        **kwargs
    ):
        unsubscribe_token = UnsubscribeEmailToken.create_token(
            user_id=user_id,
            email_type=MailoutType.COMMENTS,
        ).__str__()
        self._send(
            user_id=user_id,
            recipient_email=user_email,
            template_code=EmailTemplate.UNREAD_NOTIFICATIONS,
            method_name=NotificationMethod.unread_notifications,
            data={
                'user_name': user_first_name,
                'unsubscribe_token': unsubscribe_token,
                'logo_lg': logo_lg
            }
        )

    def send_reset_password(
        self,
        user_id: int,
        user_email: str,
        logo_lg: Optional[str] = None,
        **kwargs
    ):

        token = ResetPasswordToken.for_user_id(user_id).__str__()
        self._send(
            user_id=user_id,
            recipient_email=user_email,
            template_code=EmailTemplate.RESET_PASSWORD,
            method_name=NotificationMethod.reset_password,
            data={
                'token': token,
                'logo_lg': logo_lg,
            }
        )
