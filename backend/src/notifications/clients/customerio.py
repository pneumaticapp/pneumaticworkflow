from typing import Any, Dict

from customerio import APIClient, SendEmailRequest
from django.conf import settings

from src.notifications.clients.base import EmailClient
from src.notifications.enums import cio_template_ids


class CustomerIOEmailClient(EmailClient):

    def __init__(self):
        self.client = APIClient(settings.CUSTOMERIO_TRANSACTIONAL_API_KEY)

    def send_email(
        self,
        to: str,
        template_code: str,
        message_data: Dict[str, Any],
        user_id: int,
    ) -> None:
        request = SendEmailRequest(
            to=to,
            transactional_message_id=cio_template_ids[template_code],
            message_data=message_data,
            identifiers={'id': user_id},
        )
        self.client.send_email(request)
