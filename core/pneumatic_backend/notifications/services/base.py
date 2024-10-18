from abc import abstractmethod
from pneumatic_backend.notifications.services.exceptions import (
    NotificationServiceError,
)
from pneumatic_backend.notifications.enums import NotificationMethod


class NotificationService:

    ALLOWED_METHODS = []

    def __init__(self, logging: bool = False):
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
