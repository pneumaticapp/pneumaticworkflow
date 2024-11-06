from datetime import datetime
from typing import Optional, Dict, Any
from django.conf import settings
from pneumatic_backend.accounts.models import User
from pneumatic_backend.services.tasks import send_email_via_customerio
from pneumatic_backend.accounts.tokens import UnsubscribeEmailToken
from pneumatic_backend.analytics.enums import MailoutType
from pneumatic_backend.notifications.enums import EmailTemplate


class EmailService:

    # TODO: move to notifications app https://my.pneumatic.app/workflows/15592

    @staticmethod
    def _send_email_to_console(
        recipient_email: str,
        template_code: str,
        data: dict
    ):
        print(
            f'''
            -------------------------
            ------EMAIL-MESSAGE------
            To email: {recipient_email}
            Template name: {template_code}
            Message args: {data}
            -------------------------
            '''
        )

    @staticmethod
    def _send_mail(
        user_id: int,
        recipient_email: str,
        template_code: EmailTemplate.LITERALS,
        data: Optional[Dict[str, Any]] = None
    ):

        if not settings.PROJECT_CONF['EMAIL']:
            return

        if settings.CONFIGURATION_CURRENT in (
            settings.CONFIGURATION_DEV,
            settings.CONFIGURATION_TESTING,
        ):
            EmailService._send_email_to_console(
                recipient_email=recipient_email,
                template_code=template_code,
                data=data,
            )
        else:
            send_email_via_customerio.delay(
                user_id=user_id,
                email=recipient_email,
                template_code=template_code,
                dynamic_data=data,
            )

    @staticmethod
    def send_user_deactivated_email(user: User):
        EmailService._send_mail(
            user_id=user.id,
            recipient_email=user.email,
            template_code=EmailTemplate.USER_DEACTIVATED,
            data={
                'logo_lg': user.account.logo_lg,
            }
        )

    @staticmethod
    def send_user_transfer_email(
        email: str,
        invited_by: User,
        token: str,
        user_id: int,
        logo_lg: Optional[str] = None,
    ):
        data = {
            'token':  token,
            'sender_name': invited_by.get_full_name(),
            'company_name': invited_by.account.name,
            'user_id': user_id,
            'logo_lg': logo_lg,
        }
        EmailService._send_mail(
            user_id=user_id,
            recipient_email=email,
            template_code=EmailTemplate.USER_TRANSFER,
            data=data,
        )

    @staticmethod
    def send_verification_email(
        user: User,
        token: str,
        logo_lg: Optional[str] = None,
    ):
        data = {
            'token': token,
            'first_name': user.first_name,
            'logo_lg': logo_lg,
        }
        EmailService._send_mail(
            user_id=user.id,
            recipient_email=user.email,
            template_code=EmailTemplate.ACCOUNT_VERIFICATION,
            data=data,
        )

    @staticmethod
    def send_workflows_digest_email(
        user: User,
        date_from: datetime,
        date_to: datetime,
        digest: Dict[str, Any],
        logo_lg: Optional[str] = None,
    ):
        unsubscribe_token = str(
            UnsubscribeEmailToken.create_token(
                user_id=user.id,
                email_type=MailoutType.WF_DIGEST,
            )
        )

        data = {
            'date_from': date_from.strftime('%d %b'),
            'date_to': date_to.strftime('%d %b, %Y'),
            'unsubscribe_token': unsubscribe_token,
            'logo_lg': logo_lg,
            **digest,
        }
        EmailService._send_mail(
            user_id=user.id,
            recipient_email=user.email,
            template_code=EmailTemplate.WORKFLOWS_DIGEST,
            data=data,
        )

    @staticmethod
    def send_tasks_digest_email(
        user: User,
        date_from: datetime,
        date_to: datetime,
        digest: Dict[str, Any],
        logo_lg: Optional[str] = None,
    ):
        unsubscribe_token = str(
            UnsubscribeEmailToken.create_token(
                user_id=user.id,
                email_type=MailoutType.TASKS_DIGEST,
            )
        )
        data = {
            'date_from': date_from.strftime('%d %b'),
            'date_to': date_to.strftime('%d %b, %Y'),
            'unsubscribe_token': unsubscribe_token,
            'logo_lg': logo_lg,
            **digest,
        }
        EmailService._send_mail(
            user_id=user.id,
            recipient_email=user.email,
            template_code=EmailTemplate.TASKS_DIGEST,
            data=data,
        )
