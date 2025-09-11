from django.contrib.auth import get_user_model
from rest_framework.generics import (
    ListAPIView
)
from src.accounts.permissions import (
    UserIsAdminOrAccountOwner,
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
)
from src.authentication.permissions import PrivateApiPermission
from src.generics.mixins.views import (
    BaseResponseMixin,
)
from src.generics.permissions import (
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
