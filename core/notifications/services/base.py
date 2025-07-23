from abc import abstractmethod
from typing import Optional

from pneumatic_backend.notifications.services.exceptions import (
    NotificationServiceError,
)
from pneumatic_backend.notifications.enums import NotificationMethod


class NotificationService:

    ALLOWED_METHODS = []

    def __init__(
        self,
        account_id: int,
        logging: bool = False,
        logo_lg: Optional[str] = None,

    ):
        self.account_id = account_id
        self.logo_lg = logo_lg
        self.logging = logging
        super().__init__()

    def _validate_send(self, method_name: NotificationMethod):
        if method_name not in self.ALLOWED_METHODS:
            raise NotificationServiceError(
                message=f'{method_name} is not allowed notification',
            )

    @abstractmethod
    def _send(self, *args, **kwargs):
        self._validate_send(kwargs['method_name'])

    @abstractmethod
    def _handle_error(self, *args, **kwargs):
        pass
