from rest_framework.decorators import action

from src.accounts.enums import SourceType
from src.authentication.permissions import SSOPermission
from src.authentication.services.auth0 import Auth0Service
from src.authentication.views.base_sso import BaseSSOViewSet
from src.logs.events import AuditEventService
from src.utils.logging import (
    SentryLogLevel,
    capture_sentry_message,
)


class Auth0ViewSet(BaseSSOViewSet):

    permission_classes = (SSOPermission,)
    service_class = Auth0Service

    @action(methods=('GET',), detail=False)
    def logout(self, *args, **kwargs):
        capture_sentry_message(
            message='Auth0 logout request',
            data=self.request.GET,
            level=SentryLogLevel.INFO,
        )
        target = None
        if self.request.user.is_authenticated:
            target = self.request.user
        AuditEventService.user_logged_out_by_provider(
            target=target,
            source=SourceType.AUTH0,
        )
        return self.response_ok()
