from abc import ABC, abstractmethod
from typing import Any, Dict

from django.conf import settings
from src.notifications.clients import (
    SMTPEmailClient,
    CustomerIOEmailClient,
)
from src.notifications.enums import EmailClientProvider


class EmailClient(ABC):

    @abstractmethod
    def send_email(
        self,
        to: str,
        template_code: str,
        message_data: Dict[str, Any],
        user_id: int,
    ) -> None:
        pass


def get_email_client() -> EmailClient:
    """Get email client instance."""
    if settings.EMAIL_PROVIDER == EmailClientProvider.CUSTOMERIO:
        return CustomerIOEmailClient()
    return SMTPEmailClient()
