from django.conf import settings

from src.notifications.clients.base import EmailClient
from src.notifications.clients.customerio import CustomerIOEmailClient
from src.notifications.clients.smtp import SMTPEmailClient
from src.notifications.enums import EmailClientProvider


def get_email_client() -> EmailClient:
    """Get email client instance."""
    if settings.EMAIL_PROVIDER == EmailClientProvider.CUSTOMERIO:
        return CustomerIOEmailClient()
    return SMTPEmailClient()
