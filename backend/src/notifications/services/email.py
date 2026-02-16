from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from src.accounts.enums import UserType
from src.accounts.tokens import (
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
    email_titles,
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
        NotificationMethod.workflows_digest,
        NotificationMethod.tasks_digest,
        NotificationMethod.user_deactivated,
        NotificationMethod.user_transfer,
        NotificationMethod.verification,
        NotificationMethod.invite,
        NotificationMethod.complete_workflow,
    }

    def _send_email_to_console(
        self,
        user_email: str,
        template_code: str,
        data: dict,
    ):
        message_vars = (
            '\n'.join(f'- {key}: {val}' for key, val in data.items())
        )
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

    def _send(
        self,
        title: str,
        user_id: int,
        user_email: str,
        template_code: EmailType.LITERALS,
        method_name: NotificationMethod.LITERALS,
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
            self._send_email_via_client(
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
        link: str,
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
        unsubscribe_link = (
            f'{settings.BACKEND_URL}/accounts/emails/unsubscribe?token='
            f'{unsubscribe_token}'
        )

        data = {
            'title': email_titles[NotificationMethod.new_task],
            'template': template_name,
            'workflow_name': workflow_name,
            'task_name': task_name,
            'due_in': due_in,
            'overdue': overdue,
            'task_description': html_description,
            'task_id': task_id,
            'link': link,
            'unsubscribe_token': unsubscribe_token,
            'unsubscribe_link': unsubscribe_link,
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
            template_code=EmailType.NEW_TASK,
            method_name=NotificationMethod.new_task,
            data=data,
        )

    def send_complete_workflow(
        self,
        link: str,
        user_id: int,
        user_email: str,
        workflow_name: str,
        **kwargs,
    ):
        data = {
            'title': email_titles[NotificationMethod.complete_workflow],
            'workflow_name': workflow_name,
            'link': link,
            'logo_lg': self.logo_lg,
        }
        self._send(
            title=email_titles[NotificationMethod.complete_workflow],
            user_id=user_id,
            user_email=user_email,
            template_code=EmailType.COMPLETE_WORKFLOW,
            method_name=NotificationMethod.complete_workflow,
            data=data,
        )

    def send_returned_task(
        self,
        link: str,
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
        unsubscribe_link = (
            f'{settings.BACKEND_URL}/accounts/emails/unsubscribe?token='
            f'{unsubscribe_token}'
        )

        data = {
            'title': email_titles[NotificationMethod.returned_task],
            'template': template_name,
            'workflow_name': workflow_name,
            'task_name': task_name,
            'due_in': due_in,
            'overdue': overdue,
            'task_description': html_description,
            'task_id': task_id,
            'link': link,
            'unsubscribe_token': unsubscribe_token,
            'unsubscribe_link': unsubscribe_link,
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
            template_code=EmailType.TASK_RETURNED,
            method_name=NotificationMethod.returned_task,
            data=data,
        )

    def send_overdue_task(
        self,
        link: str,
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

        started_by = {
            'name': (
                f'{workflow_starter_first_name} {workflow_starter_last_name}'
                .strip()
            ),
            'avatar': None,
        }

        self._send(
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
                'link': link,
                'template_name': template_name,
                'workflow_starter_id': workflow_starter_id,
                'workflow_starter_first_name': workflow_starter_first_name,
                'workflow_starter_last_name': workflow_starter_last_name,
                'started_by': started_by,
                'user_type': user_type,
                'token': token,
                'logo_lg': self.logo_lg,
            },
        )

    def send_guest_new_task(
        self,
        link: str,
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
        title = (
            f'{sender_name} {email_titles[NotificationMethod.guest_new_task]} '
            f'{task_name} Task'
        )

        data = {
            'title': title,
            'token': token,
            'user_id': user_id,
            'link': link,
            'task_id': task_id,
            'task_name': task_name,
            'task_description': description,
            'guest_sender_name': sender_name,
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
        link: str,
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
            f'{settings.BACKEND_URL}/accounts/emails/unsubscribe?token='
            f'{unsubscribe_token}'
        )
        content = (
            f'{user_first_name}, work in your company is in full swing. '
            f'Check your recent notifications to be up to date.'
        )

        self._send(
            title=str(messages.MSG_NF_0013),
            user_id=user_id,
            user_email=user_email,
            template_code=EmailType.UNREAD_NOTIFICATIONS,
            method_name=NotificationMethod.unread_notifications,
            data={
                'title': email_titles[NotificationMethod.unread_notifications],
                'content': content,
                'user_name': user_first_name,
                'button_text': 'View Notifications',
                'unsubscribe_token': unsubscribe_token,
                'unsubscribe_link': unsubscribe_link,
                'link': link,
                'logo_lg': self.logo_lg,
            },
        )

    def send_reset_password(
        self,
        link: str,
        token: str,
        user_id: int,
        user_email: str,
        **kwargs,
    ):
        content = 'We got a request to reset your Pneumatic account password.'
        additional_content = (
            'A strong password includes eight or more characters '
            'and a combination of uppercase and lowercase letters, '
            'numbers and symbols, and is not based on words in the dictionary.'
        )

        self._send(
            title=str(messages.MSG_NF_0014),
            user_id=user_id,
            user_email=user_email,
            template_code=EmailType.RESET_PASSWORD,
            method_name=NotificationMethod.reset_password,
            data={
                'title': email_titles[NotificationMethod.reset_password],
                'content': content,
                'additional_content': additional_content,
                'button_text': 'Reset my password',
                'token': token,
                'link': link,
                'logo_lg': self.logo_lg,
            },
        )

    def send_mention(
        self,
        link: str,
        task_id: int,
        user_id: int,
        user_email: str,
        user_first_name: str,
        **kwargs,
    ):
        content = (
            f"{user_first_name}, there's some activity happening. "
            f"Check your mentions to stay updated on your tasks right away."
        )

        self._send(
            title=str(messages.MSG_NF_0005),
            user_id=user_id,
            user_email=user_email,
            template_code=EmailType.MENTION,
            method_name=NotificationMethod.mention,
            data={
                'title': email_titles[NotificationMethod.mention],
                'content': content,
                'logo_lg': self.logo_lg,
                'button_text': 'View Mentions',
                'user_first_name': user_first_name,
                'task_id': task_id,
                'link': link,
            },
        )

    def send_user_deactivated(
        self,
        link: str,
        user_id: int,
        user_email: str,
        **kwargs,
    ):

        self._send(
            title=str(messages.MSG_NF_0015),
            user_id=user_id,
            user_email=user_email,
            template_code=EmailType.USER_DEACTIVATED,
            method_name=NotificationMethod.user_deactivated,
            data={
                'title': email_titles[NotificationMethod.user_deactivated],
                'logo_lg': self.logo_lg,
                'image_url': True,
                'link': link,
            },
        )

    def send_user_transfer(
        self,
        link: str,
        user_id: int,
        user_email: str,
        invited_by_name: str,
        company_name: str,
        token: str,
        **kwargs,
    ):
        """Send user transfer notification."""

        content = (
            "Your User Profile is associated with another Pneumatic account. "
            "By agreeing to this invitation, you permit us to transfer your "
            "User Profile to an invitee's account. This transfer will revoke "
            "your access to your old account."
        )

        self._send(
            title=str(messages.MSG_NF_0016),
            user_id=user_id,
            user_email=user_email,
            template_code=EmailType.USER_TRANSFER,
            method_name=NotificationMethod.user_transfer,
            data={
                'title': (
                    f'{invited_by_name} '
                    f'{email_titles[NotificationMethod.user_transfer]}'
                ),
                'content': content,
                'button_text': 'Transfer My Profile',
                'token': token,
                'link': link,
                'sender_name': invited_by_name,
                'company_name': company_name,
                'user_id': user_id,
                'logo_lg': self.logo_lg,
            },
        )

    def send_verification(
        self,
        link: str,
        user_id: int,
        user_email: str,
        user_first_name: str,
        token: str,
        **kwargs,
    ):
        """Send verification notification."""

        content = (
            'Thank you for signing up for Pneumatic. '
            'Please verify your email address to get started.'
        )

        self._send(
            title=str(messages.MSG_NF_0017),
            user_id=user_id,
            user_email=user_email,
            template_code=EmailType.ACCOUNT_VERIFICATION,
            method_name=NotificationMethod.verification,
            data={
                'title': email_titles[NotificationMethod.verification],
                'content': content,
                'button_text': 'Get Started',
                'token': token,
                'link': link,
                'first_name': user_first_name,
                'logo_lg': self.logo_lg,
            },
        )

    def send_invite(
        self,
        link: str,
        user_id: int,
        user_email: str,
        **kwargs,
    ):

        self._send(
            title=str(messages.MSG_NF_0020),
            user_id=user_id,
            user_email=user_email,
            template_code=EmailType.INVITE,
            method_name=NotificationMethod.invite,
            data={
                'title': email_titles[NotificationMethod.invite],
                'button_text': 'Join Your Team',
                'link': link,
                'logo_lg': self.logo_lg,
                'is_invite': True,
            },
        )

    def send_workflows_digest(
        self,
        link: str,
        user_id: int,
        user_email: str,
        date_from: str,
        date_to: str,
        digest: Dict[str, Any],
        **kwargs,
    ):
        """Send workflows digest notification."""
        unsubscribe_token = str(
            UnsubscribeEmailToken.create_token(
                user_id=user_id,
                email_type=MailoutType.WF_DIGEST,
            ),
        )
        unsubscribe_link = (
            f'{settings.BACKEND_URL}/accounts/emails/unsubscribe?token='
            f'{unsubscribe_token}'
        )

        data = {
            'title': email_titles[NotificationMethod.workflows_digest],
            'date_from': date_from,
            'date_to': date_to,
            'unsubscribe_token': unsubscribe_token,
            'unsubscribe_link': unsubscribe_link,
            'workflows_link': link,
            'logo_lg': self.logo_lg,
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
            **digest,
        }
        self._send(
            title=str(messages.MSG_NF_0018),
            user_id=user_id,
            user_email=user_email,
            template_code=EmailType.WORKFLOWS_DIGEST,
            method_name=NotificationMethod.workflows_digest,
            data=data,
        )

    def send_tasks_digest(
        self,
        link: str,
        user_id: int,
        user_email: str,
        date_from: str,
        date_to: str,
        digest: Dict[str, Any],
        **kwargs,
    ):
        """Send tasks digest notification."""
        unsubscribe_token = str(
            UnsubscribeEmailToken.create_token(
                user_id=user_id,
                email_type=MailoutType.TASKS_DIGEST,
            ),
        )
        unsubscribe_link = (
            f'{settings.BACKEND_URL}/accounts/unsubscribe/'
            f'{unsubscribe_token}'
        )

        data = {
            'title': email_titles[NotificationMethod.tasks_digest],
            'date_from': date_from,
            'date_to': date_to,
            'unsubscribe_token': unsubscribe_token,
            'unsubscribe_link': unsubscribe_link,
            'tasks_link': link,
            'logo_lg': self.logo_lg,
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
            **digest,
        }
        self._send(
            title=str(messages.MSG_NF_0019),
            user_id=user_id,
            user_email=user_email,
            template_code=EmailType.TASKS_DIGEST,
            method_name=NotificationMethod.tasks_digest,
            data=data,
        )
