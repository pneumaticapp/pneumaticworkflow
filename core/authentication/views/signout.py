from django.contrib.auth import get_user_model
from rest_framework.authentication import get_authorization_header
from rest_framework.generics import (
    CreateAPIView,
)
from pneumatic_backend.authentication.permissions import (
    PrivateApiPermission,
)
from pneumatic_backend.authentication.tokens import PneumaticToken
from pneumatic_backend.generics.mixins.views import (
    BaseResponseMixin
)
from pneumatic_backend.generics.permissions import (
    UserIsAuthenticated,
)


UserModel = get_user_model()


class SignOutView(
    CreateAPIView,
    BaseResponseMixin
):

    permission_classes = (UserIsAuthenticated, PrivateApiPermission)

    def post(self, request, *args, **kwargs):
        auth = get_authorization_header(request).split()
        token = auth[1].decode()
        if not request.user.apikey.key == token:
            # API key cannot be expired from logout
            PneumaticToken.expire_token(token)
        return self.response_ok()
