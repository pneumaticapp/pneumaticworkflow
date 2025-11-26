from typing import Optional

from django.conf import settings

from src.notifications.clients.base import EmailClient
from src.notifications.clients.customerio import CustomerIOEmailClient
from src.notifications.clients.smtp import SMTPEmailClient


class EmailClientFactory:
    """Factory for email clients with caching."""

    _instance: Optional[EmailClient] = None

    @classmethod
    def get_client(cls) -> EmailClient:
        """Get email client based on settings."""
        if cls._instance is not None:
            return cls._instance

        client_type = getattr(
            settings,
            'EMAIL_CLIENT_TYPE',
            'customerio',
        ).lower()

        if client_type == 'customerio':
            cls._instance = CustomerIOEmailClient()
        elif client_type == 'smtp':
            cls._instance = SMTPEmailClient()
        else:
            raise ValueError(
                f'Unknown email client type: {client_type}. '
                f'Available: customerio, smtp',
            )

        return cls._instance


def get_email_client() -> EmailClient:
    """Get email client instance."""
    return EmailClientFactory.get_client()
