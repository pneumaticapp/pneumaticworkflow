from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from src.accounts.enums import UserType
from src.accounts.tokens import (
    ResetPasswordToken,
    UnsubscribeEmailToken,
)
from src.analysis.enums import MailoutType
from src.logs.enums import (
    AccountEventStatus,
)
from src.logs.service import AccountLogService
from src.notifications import messages
from src.notifications.clients import (
    CustomerIOEmailClient,
    EmailClient,
    SMTPEmailClient,
)
from src.notifications.enums import (
    EmailProvider,
    EmailType,
    NotificationMethod,
)
from src.notifications.services.base import (
    NotificationService,
)
from src.processes.utils.common import get_duration_format
from src.services.html_converter import convert_text_to_html

UserModel = get_user_model()


class EmailService(NotificationService):

    def __init__(
        self,
        account_id: int,
        logging: bool = False,
        logo_lg: Optional[str] = None,
    ):
        super().__init__(account_id, logging, logo_lg)
        client_cls = (
            CustomerIOEmailClient
            if settings.EMAIL_PROVIDER == EmailProvider.CUSTOMERIO
            else SMTPEmailClient
        )
        self.client: EmailClient = client_cls(account_id=account_id)

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
        print(  # noqa: T201
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

    def _send_email_via_client(
        self,
        title: str,
        user_id: int,
        user_email: str,
        template_code: str,
        data: Dict[str, Any],
    ):
        self.client.send_email(
            to=user_email,
            template_code=template_code,
            message_data=data,
            user_id=user_id,
        )
        if self.logging:
            AccountLogService().email_message(
                title=f'Email to: {user_email}: {title}',
                request_data=data,
                account_id=self.account_id,
                status=AccountEventStatus.SUCCESS,
                contractor=settings.EMAIL_PROVIDER,
            )

    def _dispatch_email(
        self,
        title: str,
        user_id: int,
        user_email: str,
        template_code: str,
        data: Dict[str, Any],
    ):
        """Dispatch email based on configuration (console or client)."""
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
            self._send_email_via_client(
                title=title,
                user_id=user_id,
                user_email=user_email,
                template_code=template_code,
                data=data,
            )

    def _add_standard_variables(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Add standard variables to email data."""
        now = timezone.now()

        standard_vars = {
            'backend_url': settings.BACKEND_URL,
            'frontend_url': settings.FRONTEND_URL,
            'date': now.strftime('%d %b, %Y'),
            'year': now.strftime('%Y'),
            'logo_lg': data.get('logo_lg', self.logo_lg),
            'logo_sm': data.get('logo_sm', ''),
        }
        return {**standard_vars, **data}

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
        data = self._add_standard_variables(data)
        self._dispatch_email(
            title=title,
            user_id=user_id,
            user_email=user_email,
            template_code=template_code,
            data=data,
        )

    def _send_simple_email(
        self,
        title: str,
        user_id: int,
        user_email: str,
        template_code: str,
        data: Dict[str, Any],
    ):
        """Send email without NotificationMethod validation."""
        data = self._add_standard_variables(data)
        self._dispatch_email(
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
        task_link = (
            f'{settings.FRONTEND_URL}'
            f'/tasks/{task_id}?utm_source=email&utm_campaign=new_task'
        )
        unsubscribe_link = (
            f'{settings.BACKEND_URL}/accounts/unsubscribe/'
            f'{unsubscribe_token}'
        )

        data = {
            'title': "You've been assigned a task",
            'template': template_name,
            'workflow_name': workflow_name,
            'task_name': task_name,
            'due_in': due_in,
            'overdue': overdue,
            'task_description': html_description,
            'task_id': task_id,
            'task_link': task_link,
            'unsubscribe_token': unsubscribe_token,
            'unsubscribe_link': unsubscribe_link,
            'started_by': {
                'name': wf_starter_name,
                'avatar': wf_starter_photo,
            },
        }
        self._send(
            title=str(messages.MSG_NF_0002),
            user_id=user_id,
            user_email=user_email,
            template_code=EmailType.NEW_TASK,
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
        task_link = (
            f'{settings.FRONTEND_URL}'
            f'/tasks/{task_id}?utm_source=email&utm_campaign=returned_task'
        )
        unsubscribe_link = (
            f'{settings.BACKEND_URL}/accounts/unsubscribe/'
            f'{unsubscribe_token}'
        )

        data = {
            'title': 'Task has been returned',
            'template': template_name,
            'workflow_name': workflow_name,
            'task_name': task_name,
            'due_in': due_in,
            'overdue': overdue,
            'task_description': html_description,
            'task_id': task_id,
            'task_link': task_link,
            'unsubscribe_token': unsubscribe_token,
            'unsubscribe_link': unsubscribe_link,
            'started_by': {
                'name': wf_starter_name,
                'avatar': wf_starter_photo,
            },
        }
        self._send(
            title=str(messages.MSG_NF_0003),
            user_id=user_id,
            user_email=user_email,
            template_code=EmailType.TASK_RETURNED,
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
        if token:
            task_link = (
                f'{settings.FRONTEND_URL}/tasks/{task_id}'
                f'?token={token}&utm_source=email&utm_campaign=overdue_task'
            )
        else:
            task_link = (
                f'{settings.FRONTEND_URL}/tasks/{task_id}'
                f'?utm_source=email&utm_campaign=overdue_task'
            )

        self._send(
            title=str(messages.MSG_NF_0004),
            user_id=user_id,
            user_email=user_email,
            template_code=EmailType.OVERDUE_TASK,
            method_name=NotificationMethod.overdue_task,
            data={
                'title': 'Task is overdue',
                'template': template_name,
                'workflow_id': workflow_id,
                'workflow_name': workflow_name,
                'task_id': str(task_id),
                'task_name': task_name,
                'task_link': task_link,
                'template_name': template_name,
                'workflow_starter_id': workflow_starter_id,
                'workflow_starter_first_name': workflow_starter_first_name,
                'workflow_starter_last_name': workflow_starter_last_name,
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
        task_link = (
            f'{settings.FRONTEND_URL}/tasks/{task_id}'
            f'?token={token}&utm_source=email&utm_campaign=guest_new_task'
        )

        data = {
            'token': token,
            'link': task_link,
            'task_link': task_link,
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
            template_code=EmailType.GUEST_NEW_TASK,
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
        unsubscribe_link = (
            f'{settings.BACKEND_URL}/accounts/unsubscribe/'
            f'{unsubscribe_token}'
        )
        notifications_link = (
            f'{settings.FRONTEND_URL}'
            f'/notifications?utm_source=email&utm_campaign=unread'
        )

        self._send(
            title=str(messages.MSG_NF_0013),
            user_id=user_id,
            user_email=user_email,
            template_code=EmailType.UNREAD_NOTIFICATIONS,
            method_name=NotificationMethod.unread_notifications,
            data={
                'user_name': user_first_name,
                'unsubscribe_token': unsubscribe_token,
                'unsubscribe_link': unsubscribe_link,
                'notifications_link': notifications_link,
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
        reset_link = (
            f'{settings.FRONTEND_URL}/auth/reset-password'
            f'?token={token}&utm_source=email&utm_campaign=reset_password'
        )

        self._send(
            title=str(messages.MSG_NF_0014),
            user_id=user_id,
            user_email=user_email,
            template_code=EmailType.RESET_PASSWORD,
            method_name=NotificationMethod.reset_password,
            data={
                'title': 'Forgot Your Password?',
                'content': (
                    '<h2><strong>We got a request to reset your '
                    'Pneumatic account password.</strong></h2>'
                    '<p>A strong password includes eight or more '
                    'characters and a combination of uppercase and '
                    'lowercase letters, numbers and symbols, and is not '
                    'based on words in the dictionary.</p>'
                ),
                'button_text': 'Reset my password',
                'token': token,
                'link': reset_link,
                'reset_link': reset_link,
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
        task_link = (
            f'{settings.FRONTEND_URL}/tasks/{task_id}'
            f'?utm_source=email&utm_campaign=mention'
        )

        self._send(
            title=str(messages.MSG_NF_0005),
            user_id=user_id,
            user_email=user_email,
            template_code=EmailType.MENTION,
            method_name=NotificationMethod.mention,
            data={
                'logo_lg': self.logo_lg,
                'user_first_name': user_first_name,
                'task_id': task_id,
                'task_link': task_link,
                'link': task_link,
            },
        )

    @classmethod
    def send_user_deactivated_email(cls, user):
        """Send user deactivated email."""
        service = cls(
            account_id=user.account_id,
            logo_lg=user.account.logo_lg,
        )
        support_link = f'{settings.FRONTEND_URL}/support'

        service._send_simple_email(
            title='User Deactivated',
            user_id=user.id,
            user_email=user.email,
            template_code=EmailType.USER_DEACTIVATED,
            data={
                'title': 'Account Deactivated',
                'content': (
                    '<p>Your Pneumatic account has been deactivated.</p>'
                    '<p>If you believe this was done in error, please '
                    'contact support.</p>'
                ),
                'button_text': 'Contact Support',
                'link': support_link,
                'logo_lg': user.account.logo_lg,
                'support_link': support_link,
            },
        )

    @classmethod
    def send_user_transfer_email(
        cls,
        email: str,
        invited_by,
        token: str,
        user_id: int,
        logo_lg: Optional[str] = None,
    ):
        """Send user transfer email."""
        service = cls(
            account_id=invited_by.account_id,
            logo_lg=logo_lg,
        )
        transfer_link = (
            f'{settings.BACKEND_URL}/accounts/users/{user_id}/transfer'
            f'?token={token}&utm_source=invite&utm_campaign=transfer'
        )

        data = {
            'title': 'You have been invited!',
            'content': (
                f'<p>{invited_by.get_full_name()} has invited you to '
                f'join {invited_by.account.name} on Pneumatic.</p>'
                '<p>Click the button below to accept the invitation.</p>'
            ),
            'button_text': 'Accept Invitation',
            'token': token,
            'link': transfer_link,
            'transfer_link': transfer_link,
            'sender_name': invited_by.get_full_name(),
            'company_name': invited_by.account.name,
            'logo_lg': logo_lg,
        }
        service._send_simple_email(
            title='User Transfer',
            user_id=user_id,
            user_email=email,
            template_code=EmailType.USER_TRANSFER,
            data=data,
        )

    @classmethod
    def send_verification_email(
        cls,
        user,
        token: str,
        logo_lg: Optional[str] = None,
    ):
        """Send account verification email."""
        service = cls(
            account_id=user.account_id,
            logo_lg=logo_lg,
        )
        verification_link = (
            f'{settings.FRONTEND_URL}/auth/verify'
            f'?token={token}&utm_source=email&utm_campaign=verification'
        )

        data = {
            'title': f'Welcome, {user.first_name}!',
            'content': (
                '<p>Thank you for signing up for Pneumatic. '
                'Please verify your email address to get started.</p>'
            ),
            'button_text': 'Verify Email',
            'token': token,
            'link': verification_link,
            'verification_link': verification_link,
            'first_name': user.first_name,
            'logo_lg': logo_lg,
        }
        service._send_simple_email(
            title='Account Verification',
            user_id=user.id,
            user_email=user.email,
            template_code=EmailType.ACCOUNT_VERIFICATION,
            data=data,
        )

    @classmethod
    def send_workflows_digest_email(
        cls,
        user,
        date_from,
        date_to,
        digest: Dict[str, Any],
        logo_lg: Optional[str] = None,
    ):
        """Send workflows digest email."""
        service = cls(
            account_id=user.account_id,
            logo_lg=logo_lg,
        )
        unsubscribe_token = str(
            UnsubscribeEmailToken.create_token(
                user_id=user.id,
                email_type=MailoutType.WF_DIGEST,
            ),
        )
        unsubscribe_link = (
            f'{settings.BACKEND_URL}/accounts/unsubscribe/'
            f'{unsubscribe_token}'
        )
        workflows_link = (
            f'{settings.FRONTEND_URL}'
            f'/workflows?utm_source=email&utm_campaign=digest'
        )

        data = {
            'title': 'Workflows Digest',
            'date_from': date_from.strftime('%d %b'),
            'date_to': date_to.strftime('%d %b, %Y'),
            'unsubscribe_token': unsubscribe_token,
            'unsubscribe_link': unsubscribe_link,
            'workflows_link': workflows_link,
            **digest,
        }
        service._send_simple_email(
            title='Workflows Digest',
            user_id=user.id,
            user_email=user.email,
            template_code=EmailType.WORKFLOWS_DIGEST,
            data=data,
        )

    @classmethod
    def send_tasks_digest_email(
        cls,
        user,
        date_from,
        date_to,
        digest: Dict[str, Any],
        logo_lg: Optional[str] = None,
    ):
        """Send tasks digest email."""
        service = cls(
            account_id=user.account_id,
            logo_lg=logo_lg,
        )
        unsubscribe_token = str(
            UnsubscribeEmailToken.create_token(
                user_id=user.id,
                email_type=MailoutType.TASKS_DIGEST,
            ),
        )
        unsubscribe_link = (
            f'{settings.BACKEND_URL}/accounts/unsubscribe/'
            f'{unsubscribe_token}'
        )
        tasks_link = (
            f'{settings.FRONTEND_URL}'
            f'/tasks?utm_source=email&utm_campaign=tasks_digest'
        )

        data = {
            'title': 'Tasks Digest',
            'date_from': date_from.strftime('%d %b'),
            'date_to': date_to.strftime('%d %b, %Y'),
            'unsubscribe_token': unsubscribe_token,
            'unsubscribe_link': unsubscribe_link,
            'tasks_link': tasks_link,
            **digest,
        }
        service._send_simple_email(
            title='Tasks Digest',
            user_id=user.id,
            user_email=user.email,
            template_code=EmailType.TASKS_DIGEST,
            data=data,
        )
