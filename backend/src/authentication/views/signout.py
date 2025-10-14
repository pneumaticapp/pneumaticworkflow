from django.contrib.auth import get_user_model
from rest_framework.authentication import get_authorization_header
from rest_framework.generics import (
    CreateAPIView,
)

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

UserModel = get_user_model()


class SignOutView(
    CreateAPIView,
    BaseResponseMixin,
):

    permission_classes = (UserIsAuthenticated, PrivateApiPermission)

    def post(self, request, *args, **kwargs):
        auth = get_authorization_header(request).split()
        token = auth[1].decode()
        if request.user.apikey.key != token:
            # API key cannot be expired from logout
            PneumaticToken.expire_token(token)
        return self.response_ok()
