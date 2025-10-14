from datetime import datetime, timedelta
from django.utils import timezone
from typing import Dict, Optional, Union, Any
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils.dateparse import parse_datetime

from src.notifications.enums import NotificationMethod
from src.notifications.services.base import (
    NotificationService,
)
from customerio import SendEmailRequest, APIClient
from src.analytics.enums import MailoutType
from src.accounts.enums import UserType
from src.services.html_converter import convert_text_to_html
from src.processes.utils.common import get_duration_format
from src.notifications.enums import (
    EmailTemplate,
    cio_template_ids,
)
from src.accounts.tokens import (
    UnsubscribeEmailToken,
    ResetPasswordToken,
)
from src.logs.service import AccountLogService
from src.logs.enums import (
    AccountEventStatus,
)
from src.notifications import messages


UserModel = get_user_model()


class EmailService(NotificationService):

    ALLOWED_METHODS = {
        NotificationMethod.new_task,
        NotificationMethod.returned_task,
        NotificationMethod.overdue_task,
        NotificationMethod.guest_new_task,
        NotificationMethod.unread_notifications,
        NotificationMethod.reset_password,
        NotificationMethod.mention,
    }

    def _send_email_to_console(
        self,
        user_email: str,
        template_code: str,
        data: dict,
    ):
        message_vars = ''
        for key, val in data.items():
            '\n'.join(f'- {key}: {val}')
        print( # noqa: T201
            f"""
            -------------------------
            ------EMAIL-MESSAGE------
            To email: {user_email}
            Template name: {template_code}
            Message args:
            {message_vars}
            -------------------------
            """,
        )

    def _send_email_via_customerio(
        self,
        title: str,
        user_id: int,
        user_email: str,
        template_code: str,
        data: Dict[str, Any],
    ):
        client = APIClient(settings.CUSTOMERIO_TRANSACTIONAL_API_KEY)
        message_id = cio_template_ids[template_code]
        request = SendEmailRequest(
            to=user_email,
            transactional_message_id=message_id,
            message_data=data,
            identifiers={'id': user_id},
        )
        client.send_email(request)
        if self.logging:
            AccountLogService().email_message(
                title=f'Email to: {user_email}: {title}',
                request_data=data,
                account_id=self.account_id,
                status=AccountEventStatus.SUCCESS,
                contractor='Customer.io',
            )

    def _send(
        self,
        title: str,
        user_id: int,
        user_email: str,
        template_code: str,
        method_name: NotificationMethod,
        data: Dict[str, str],
    ):

        self._validate_send(method_name)

        if not settings.PROJECT_CONF['EMAIL']:
            return

        if settings.CONFIGURATION_CURRENT in (
            settings.CONFIGURATION_DEV,
            settings.CONFIGURATION_TESTING,
        ):
            self._send_email_to_console(
                user_email=user_email,
                template_code=template_code,
                data=data,
            )
        else:
            self._send_email_via_customerio(
                title=title,
                user_id=user_id,
                user_email=user_email,
                template_code=template_code,
                data=data,
            )

    def _handle_error(self, *args, **kwargs):
        pass

    def send_new_task(
        self,
        user_id: int,
        user_email: str,
        template_name: str,
        workflow_name: str,
        task_id: int,
        task_name: str,
        html_description: str,
        wf_starter_name: str,
        wf_starter_photo: Optional[str] = None,
        due_in: Optional[str] = None,
        overdue: Optional[str] = None,
        **kwargs,
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
            'logo_lg': self.logo_lg,
            'started_by': {
                'name': wf_starter_name,
                'avatar': wf_starter_photo,
            },
        }
        self._send(
            title=str(messages.MSG_NF_0002),
            user_id=user_id,
            user_email=user_email,
            template_code=EmailTemplate.NEW_TASK,
            method_name=NotificationMethod.new_task,
            data=data,
        )

    def send_returned_task(
        self,
        user_id: int,
        user_email: str,
        template_name: str,
        workflow_name: str,
        task_id: int,
        task_name: str,
        html_description: str,
        wf_starter_name: str,
        wf_starter_photo: Optional[str] = None,
        due_in: Optional[str] = None,
        overdue: Optional[str] = None,
        **kwargs,
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
            'logo_lg': self.logo_lg,
            'started_by': {
                'name': wf_starter_name,
                'avatar': wf_starter_photo,
            },
        }
        self._send(
            title=str(messages.MSG_NF_0003),
            user_id=user_id,
            user_email=user_email,
            template_code=EmailTemplate.TASK_RETURNED,
            method_name=NotificationMethod.returned_task,
            data=data,
        )

    def send_overdue_task(
        self,
        user_id: int,
        user_email: str,
        user_type: UserType.LITERALS,
        workflow_id: int,
        workflow_name: str,
        task_id: int,
        task_name: str,
        template_name: str,
        workflow_starter_id: int,
        workflow_starter_first_name: str,
        workflow_starter_last_name: str,
        token: Optional[str] = None,
        **kwargs,
    ):
        self._send(
            title=str(messages.MSG_NF_0004),
            user_id=user_id,
            user_email=user_email,
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
                'logo_lg': self.logo_lg,
                'user_type': user_type,
                'token': token,
            },
        )

    def send_guest_new_task(
        self,
        user_id: int,
        user_email: str,
        token: str,
        sender_name: str,
        task_id: int,
        task_name: str,
        task_description: str,
        task_due_date: Union[datetime, str, None] = None,
        **kwargs,
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
            'logo_lg': self.logo_lg,
        }
        if task_due_date:
            # floating bug when task_estimated_end_date is string
            if isinstance(task_due_date, str):
                task_due_date = parse_datetime(task_due_date)
            due_in: timedelta = task_due_date - timezone.now()
            formatted_date = get_duration_format(duration=due_in)
            if due_in.total_seconds() > 0:
                data['due_in'] = formatted_date
            else:
                data['overdue'] = formatted_date

        self._send(
            title=str(messages.MSG_NF_0002),
            user_id=user_id,
            user_email=user_email,
            template_code=EmailTemplate.GUEST_NEW_TASK,
            method_name=NotificationMethod.guest_new_task,
            data=data,
        )

    def send_unread_notifications(
        self,
        user_id: int,
        user_email: str,
        user_first_name: str,
        **kwargs,
    ):
        unsubscribe_token = UnsubscribeEmailToken.create_token(
            user_id=user_id,
            email_type=MailoutType.COMMENTS,
        ).__str__()
        self._send(
            title=str(messages.MSG_NF_0013),
            user_id=user_id,
            user_email=user_email,
            template_code=EmailTemplate.UNREAD_NOTIFICATIONS,
            method_name=NotificationMethod.unread_notifications,
            data={
                'user_name': user_first_name,
                'unsubscribe_token': unsubscribe_token,
                'logo_lg': self.logo_lg,
            },
        )

    def send_reset_password(
        self,
        user_id: int,
        user_email: str,
        **kwargs,
    ):

        token = ResetPasswordToken.for_user_id(user_id).__str__()
        self._send(
            title=str(messages.MSG_NF_0014),
            user_id=user_id,
            user_email=user_email,
            template_code=EmailTemplate.RESET_PASSWORD,
            method_name=NotificationMethod.reset_password,
            data={
                'token': token,
                'logo_lg': self.logo_lg,
            },
        )

    def send_mention(
        self,
        task_id: int,
        user_id: int,
        user_email: str,
        user_first_name: str,
        **kwargs,
    ):
        self._send(
            title=str(messages.MSG_NF_0005),
            user_id=user_id,
            user_email=user_email,
            template_code=EmailTemplate.MENTION,
            method_name=NotificationMethod.mention,
            data={
                'logo_lg': self.logo_lg,
                'user_first_name': user_first_name,
                'task_id': task_id,
            },
        )
