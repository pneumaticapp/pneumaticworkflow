import re
from typing import Any, Dict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage

from src.notifications.clients.base import EmailClient
from src.notifications.models import EmailTemplateModel

UserModel = get_user_model()


class SMTPEmailClient(EmailClient):

    def __init__(self):
        if not settings.EMAIL_BACKEND:
            raise ValueError('EMAIL_BACKEND error')

    def send_email(
        self,
        to: str,
        template_code: str,
        message_data: Dict[str, Any],
        user_id: int,
    ) -> None:
        user = UserModel.objects.select_related('account').get(id=user_id)
        account = user.account
        template = EmailTemplateModel.objects.filter(
            account=account,
            template_type=template_code,
            is_active=True,
        ).first()

        if template:
            subject = self._render_template_string(
                template.subject, message_data,
            )
            html_content = self._render_template_string(
                template.content, message_data,
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
    ):
        subject = f'Pneumatic - {template_code}'
        content_lines = []
        for key, value in message_data.items():
            content_lines.append(f'<p><strong>{key}:</strong> {value}</p>')

        html_content = f"""
        <html>
        <body>
            <h2>Pneumatic</h2>
            <p>Type: {template_code}</p>
            {''.join(content_lines)}
        </body>
        </html>
        """

        return subject, html_content
