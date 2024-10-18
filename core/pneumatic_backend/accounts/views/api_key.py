from django.contrib.auth import get_user_model
from rest_framework.generics import (
    ListAPIView
)
from pneumatic_backend.accounts.permissions import (
    UserIsAdminOrAccountOwner,
    ExpiredSubscriptionPermission,
)
from pneumatic_backend.authentication.permissions import PrivateApiPermission
from pneumatic_backend.generics.mixins.views import (
    BaseResponseMixin,
)
from pneumatic_backend.generics.permissions import (
    UserIsAuthenticated,
    PaymentCardPermission,
)


UserModel = get_user_model()


class APIKeyView(
    ListAPIView,
    BaseResponseMixin
):

    permission_classes = (
        UserIsAuthenticated,
        UserIsAdminOrAccountOwner,
        PrivateApiPermission,
        ExpiredSubscriptionPermission,
        PaymentCardPermission,
    )

    def list(self, request, *args, **kwargs):
        return self.response_ok({'token': request.user.apikey.key})
