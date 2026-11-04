from drf_spectacular.utils import extend_schema
from rest_framework.authentication import get_authorization_header
from rest_framework.generics import (
    CreateAPIView,
)

from src.authentication.enums import AuthTokenType
from src.authentication.permissions import (
    PrivateApiPermission,
)
from src.authentication.tokens import PneumaticToken
from src.generics.mixins.views import (
    BaseResponseMixin,
)
from src.generics.permissions import (
    UserIsAuthenticated,
)
from src.logs.events import AuditEventService
from src.openapi.responses import EMPTY, FORBIDDEN, UNAUTHORIZED


class SignOutView(
    CreateAPIView,
    BaseResponseMixin,
):

    permission_classes = (UserIsAuthenticated, PrivateApiPermission)

    @extend_schema(
        tags=['Auth'],
        summary='Sign out the current session',
        description=(
            'Requires a non-guest authenticated user and private API '
            'source-IP restrictions. Removes the opaque Bearer session '
            'token from the Pneumatic cache and records logout. API keys '
            'and separately issued JWTs are not revoked by this operation. '
            'When PRIVATE_API_CHECK_IP is enabled, API keys are rejected '
            'even from an allowlisted IP.'
        ),
        request=None,
        responses={204: EMPTY, 401: UNAUTHORIZED, 403: FORBIDDEN},
    )
    def post(self, request, *args, **kwargs):
        auth = get_authorization_header(request).split()
        token = auth[1].decode()

        # API key tokens should not be expired on logout
        if request.token_type != AuthTokenType.API:
            PneumaticToken.expire_token(token)
        AuditEventService.user_logged_out(
            user=request.user,
            auth_type=request.token_type,
        )
        return self.response_ok()
