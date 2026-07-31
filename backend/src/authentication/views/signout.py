from rest_framework.authentication import get_authorization_header
from rest_framework.generics import (
    CreateAPIView,
)

from src.accounts.models import APIKey
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
        is_api_key = request.user.api_keys.filter(
            key_hash=APIKey.hash_key(token),
            is_active=True,
        ).exists()
        if not is_api_key:
            PneumaticToken.expire_token(token)
        return self.response_ok()
