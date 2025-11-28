import os
import re
from typing import Any, Dict, Optional, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage

from src.notifications.clients import EmailClient
from src.notifications.enums import EmailTemplate
from src.notifications.models import EmailTemplateModel

UserModel = get_user_model()


class SMTPEmailClient(EmailClient):

    def send_email(
        self,
        to: str,
        template_code: str,
        message_data: Dict[str, Any],
        user_id: int,
    ) -> None:
        user = UserModel.objects.select_related('account').get(id=user_id)

        # Find template that includes this template_code in template_types
        template = EmailTemplateModel.objects.filter(
            account=user.account,
            template_types__contains=[template_code],
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
        )
        email.content_subtype = 'html'
        email.send()

    def _render_template_string(
        self,
        template_string: str,
        context: Dict[str, Any],
    ) -> str:
        def replace_var(match):
            var_name = match.group(1).strip()
            return str(context.get(var_name, f'{{{{{var_name}}}}}'))

        return re.sub(r'\{\{\s*(\w+)\s*\}\}', replace_var, template_string)

    def _get_default_template(
        self,
        template_code: str,
        message_data: Dict[str, Any],
    ) -> Tuple[str, str]:
        """Get default template from files or simple fallback."""
        template_file = self._get_template_file_for_code(template_code)

        if template_file and os.path.exists(template_file):
            try:
                with open(template_file, encoding='utf-8') as f:
                    html_content = f.read()

                # Set default subject based on template type
                subject = self._get_default_subject(template_code)

                # Render template with data
                html_content = self._render_template_string(
                    html_content, message_data,
                )

                return subject, html_content
            except OSError:
                # File reading failed, use fallback
                pass

        # Simple fallback
        return self._get_fallback_template(template_code)

    def _get_template_file_for_code(
        self,
        template_code: str,
    ) -> Optional[str]:
        """Map template code to template file."""
        base_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'templates',
        )

        # Group templates by type
        task_templates = [
            EmailTemplate.NEW_TASK,
            EmailTemplate.TASK_RETURNED,
            EmailTemplate.COMPLETE_TASK,
            EmailTemplate.OVERDUE_TASK,
            EmailTemplate.GUEST_NEW_TASK,
            EmailTemplate.MENTION,
        ]

        auth_templates = [
            EmailTemplate.RESET_PASSWORD,
            EmailTemplate.ACCOUNT_VERIFICATION,
            EmailTemplate.USER_DEACTIVATED,
            EmailTemplate.USER_TRANSFER,
        ]

        digest_templates = [
            EmailTemplate.WORKFLOWS_DIGEST,
            EmailTemplate.TASKS_DIGEST,
            EmailTemplate.UNREAD_NOTIFICATIONS,
        ]

        if template_code in task_templates:
            return os.path.join(base_path, 'task_notifications.html')
        if template_code in auth_templates:
            return os.path.join(base_path, 'auth_notifications.html')
        if template_code in digest_templates:
            return os.path.join(base_path, 'digest_notifications.html')
        return os.path.join(base_path, 'base.html')

    def _get_default_subject(self, template_code: str) -> str:
        """Get default subject for template code."""
        subjects = {
            EmailTemplate.NEW_TASK: 'New Task Assigned',
            EmailTemplate.TASK_RETURNED: 'Task Returned',
            EmailTemplate.COMPLETE_TASK: 'Task Completed',
            EmailTemplate.OVERDUE_TASK: 'Task Overdue',
            EmailTemplate.GUEST_NEW_TASK: 'New Task Assigned',
            EmailTemplate.MENTION: 'You were mentioned',
            EmailTemplate.RESET_PASSWORD: 'Password Reset Request',
            EmailTemplate.ACCOUNT_VERIFICATION: 'Account Verification',
            EmailTemplate.USER_DEACTIVATED: 'Account Deactivated',
            EmailTemplate.USER_TRANSFER: 'Account Transfer',
            EmailTemplate.WORKFLOWS_DIGEST: 'Workflow Digest',
            EmailTemplate.TASKS_DIGEST: 'Tasks Digest',
            EmailTemplate.UNREAD_NOTIFICATIONS: 'Unread Notifications',
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
