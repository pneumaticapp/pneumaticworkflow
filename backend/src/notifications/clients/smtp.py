from typing import Any, Dict, Optional, Tuple

from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.template import Context, Template
from django.template.loader import get_template

from src.notifications.clients import EmailClient
from src.notifications.enums import EmailType
from src.notifications.models import EmailTemplateModel


class SMTPEmailClient(EmailClient):

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
        template_code: str,
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
        template_code: str,
        message_data: Dict[str, Any],
    ) -> Tuple[str, str]:
        """Get default template from files or simple fallback."""
        template_name = self._get_template_name_for_code(template_code)

        if template_name:
            try:
                # Use Django template loader for proper inheritance support
                template = get_template(template_name)
                subject = self._get_default_subject(template_code)
                html_content = template.render(message_data)
                return subject, html_content
            except Exception:  # noqa: BLE001
                # Template loading or rendering failed, use fallback
                pass

        # Simple fallback
        return self._get_fallback_template(template_code)

    def _get_template_name_for_code(
        self,
        template_code: str,
    ) -> Optional[str]:
        """Map template code to template name."""
        # Group templates by type
        task_templates = [
            EmailType.NEW_TASK,
            EmailType.TASK_RETURNED,
            EmailType.COMPLETE_TASK,
            EmailType.OVERDUE_TASK,
            EmailType.GUEST_NEW_TASK,
            EmailType.MENTION,
        ]

        auth_templates = [
            EmailType.RESET_PASSWORD,
            EmailType.ACCOUNT_VERIFICATION,
            EmailType.USER_DEACTIVATED,
            EmailType.USER_TRANSFER,
        ]

        digest_templates = [
            EmailType.WORKFLOWS_DIGEST,
            EmailType.TASKS_DIGEST,
            EmailType.UNREAD_NOTIFICATIONS,
        ]

        if template_code in task_templates:
            return 'tasks.html'
        if template_code in auth_templates:
            return 'auth.html'
        if template_code in digest_templates:
            return 'digests.html'
        return 'base.html'

    def _get_default_subject(self, template_code: str) -> str:
        """Get default subject for template code."""
        subjects = {
            EmailType.NEW_TASK: 'New Task Assigned',
            EmailType.TASK_RETURNED: 'Task Returned',
            EmailType.COMPLETE_TASK: 'Task Completed',
            EmailType.OVERDUE_TASK: 'Task Overdue',
            EmailType.GUEST_NEW_TASK: 'New Task Assigned',
            EmailType.MENTION: 'You were mentioned',
            EmailType.RESET_PASSWORD: 'Password Reset Request',
            EmailType.ACCOUNT_VERIFICATION: 'Account Verification',
            EmailType.USER_DEACTIVATED: 'Account Deactivated',
            EmailType.USER_TRANSFER: 'Account Transfer',
            EmailType.WORKFLOWS_DIGEST: 'Workflow Digest',
            EmailType.TASKS_DIGEST: 'Tasks Digest',
            EmailType.UNREAD_NOTIFICATIONS: 'Unread Notifications',
        }

        return subjects.get(template_code, f'Pneumatic - {template_code}')

    def _get_fallback_template(self, template_code: str) -> Tuple[str, str]:
        """Get simple fallback template when no file template exists."""
        subject = self._get_default_subject(template_code)
        html_content = f"""
        <html>
        <body>
            <h2>Pneumatic</h2>
            <p>Template: {template_code}</p>
        </body>
        </html>
        """

        return subject, html_content
