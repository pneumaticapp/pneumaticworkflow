from typing import Any, Dict, Tuple

from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.template import Context, Template
from django.template.loader import get_template

from src.notifications.clients import EmailClient
from src.notifications.enums import EmailType
from src.notifications.models import EmailTemplateModel


class SMTPEmailClient(EmailClient):

    DEFAULT_TEMPLATE_TASKS = 'tasks.html'
    DEFAULT_TEMPLATE_AUTH = 'auth.html'
    DEFAULT_TEMPLATE_DIGESTS = 'digests.html'

    DEFAULT_TEMPLATE_BY_TYPE = {
        EmailType.NEW_TASK: DEFAULT_TEMPLATE_TASKS,
        EmailType.TASK_RETURNED: DEFAULT_TEMPLATE_TASKS,
        EmailType.OVERDUE_TASK: DEFAULT_TEMPLATE_TASKS,
        EmailType.GUEST_NEW_TASK: DEFAULT_TEMPLATE_TASKS,
        EmailType.MENTION: DEFAULT_TEMPLATE_AUTH,
        EmailType.UNREAD_NOTIFICATIONS: DEFAULT_TEMPLATE_AUTH,
        EmailType.RESET_PASSWORD: DEFAULT_TEMPLATE_AUTH,
        EmailType.ACCOUNT_VERIFICATION: DEFAULT_TEMPLATE_AUTH,
        EmailType.USER_DEACTIVATED: DEFAULT_TEMPLATE_AUTH,
        EmailType.USER_TRANSFER: DEFAULT_TEMPLATE_AUTH,
        EmailType.WORKFLOWS_DIGEST: DEFAULT_TEMPLATE_DIGESTS,
        EmailType.TASKS_DIGEST: DEFAULT_TEMPLATE_DIGESTS,
        EmailType.INVITE: DEFAULT_TEMPLATE_AUTH,
    }

    def __init__(self, account_id: int):
        super().__init__(account_id)
        self.connection = get_connection(fail_silently=False)

    def __del__(self):
        """Close connection when instance is destroyed."""
        if hasattr(self, 'connection') and self.connection:
            self.connection.close()

    def send_email(
        self,
        to: str,
        template_code: EmailType.LITERALS,
        message_data: Dict[str, Any],
        user_id: int,
    ) -> None:
        # Find template that includes this template_code in email_types
        template = EmailTemplateModel.objects.filter(
            account_id=self.account_id,
            email_types__contains=[template_code],
            is_active=True,
        ).first()

        if template:
            subject = self._render_template_string(
                template.subject,
                message_data,
            )
            html_content = self._render_template_string(
                template.content,
                message_data,
            )
        else:
            subject, html_content = self._get_default_template(
                template_code,
                self.DEFAULT_TEMPLATE_BY_TYPE.get(template_code),
                message_data,
            )

        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to],
            connection=self.connection,
        )
        email.content_subtype = 'html'
        email.send()

    def _render_template_string(
        self,
        template_string: str,
        context: Dict[str, Any],
    ) -> str:
        template = Template(template_string)
        return template.render(Context(context))

    def _get_default_template(
        self,
        template_code: EmailType.LITERALS,
        template_name: str,
        message_data: Dict[str, Any],
    ) -> Tuple[str, str]:
        """Get default template from files."""
        try:
            # Use Django template loader for proper inheritance support
            template = get_template(template_name)
            subject = self._get_default_subject(template_code, message_data)
            html_content = template.render(message_data)
            return subject, html_content
        except Exception:  # noqa: BLE001
            # Template loading or rendering failed, use fallback
            pass
        return self._get_fallback_template(template_code, message_data)

    def _get_default_subject(
        self,
        template_code: EmailType.LITERALS,
        message_data: Dict[str, Any],
    ) -> str:
        """Get default subject for template code."""

        task_types_with_workflow_name = {
            EmailType.NEW_TASK,
            EmailType.TASK_RETURNED,
            EmailType.OVERDUE_TASK,
        }

        if template_code in task_types_with_workflow_name:
            workflow_name = message_data.get('workflow_name', '')
            if workflow_name:
                return workflow_name

        subjects = {
            EmailType.NEW_TASK: 'New Task Assigned',
            EmailType.TASK_RETURNED: 'Task Returned',
            EmailType.OVERDUE_TASK: 'Task Overdue',
            EmailType.GUEST_NEW_TASK: 'New Task Assigned',
            EmailType.MENTION: 'You have been mentioned on Pneumatic',
            EmailType.RESET_PASSWORD: 'Password Reset',
            EmailType.ACCOUNT_VERIFICATION: 'Account Verification',
            EmailType.USER_DEACTIVATED: 'Your account was deactivated',
            EmailType.USER_TRANSFER: 'Account Transfer',
            EmailType.WORKFLOWS_DIGEST: 'Workflow Digest',
            EmailType.TASKS_DIGEST: 'Tasks Digest',
            EmailType.UNREAD_NOTIFICATIONS: 'Unread Notifications',
            EmailType.INVITE: 'Join your team :busts_in_silhouette:',
        }

        return subjects.get(template_code, f'Pneumatic - {template_code}')

    def _get_fallback_template(
            self,
            template_code: EmailType.LITERALS,
            message_data: Dict[str, Any],
    ) -> Tuple[str, str]:
        """Get simple fallback template when no file template exists."""
        subject = self._get_default_subject(template_code, message_data)
        html_content = f"""
        <html>
        <body>
            <h2>Pneumatic</h2>
            <p>Email notification</p>
            <p>Template: {template_code}</p>
        </body>
        </html>
        """
        return subject, html_content
