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


class SignOutView(
    CreateAPIView,
    BaseResponseMixin,
):

    permission_classes = (UserIsAuthenticated, PrivateApiPermission)

    def post(self, request, *args, **kwargs):
        auth = get_authorization_header(request).split()
        token = auth[1].decode()

        # API key tokens should not be expired on logout
        if request.token_type != AuthTokenType.API:
            PneumaticToken.expire_token(token)
        return self.response_ok()
