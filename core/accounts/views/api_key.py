from django.contrib.auth import get_user_model
from rest_framework.generics import (
    ListAPIView
)
from pneumatic_backend.accounts.permissions import (
    UserIsAdminOrAccountOwner,
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
)
from pneumatic_backend.authentication.permissions import PrivateApiPermission
from pneumatic_backend.generics.mixins.views import (
    BaseResponseMixin,
)
from pneumatic_backend.generics.permissions import (
    UserIsAuthenticated,
)


UserModel = get_user_model()


class APIKeyView(
    ListAPIView,
    BaseResponseMixin
):

    permission_classes = (
        PrivateApiPermission,
        UserIsAuthenticated,
        BillingPlanPermission,
        UserIsAdminOrAccountOwner,
        ExpiredSubscriptionPermission,
    )

    def list(self, request, *args, **kwargs):
        return self.response_ok({'token': request.user.apikey.key})
