from django.contrib.auth import get_user_model
from rest_framework.generics import (
    GenericAPIView,
)
from src.accounts.permissions import (
    UserIsAdminOrAccountOwner,
    ExpiredSubscriptionPermission,
    BillingPlanPermission,
)
from src.accounts.services import AccountService
from src.accounts.serializers.accounts import (
    AccountSerializer,
    AccountPlanSerializer,
)
from src.generics.mixins.views import (
    BaseResponseMixin,
)
from src.generics.permissions import (
    UserIsAuthenticated,
)

UserModel = get_user_model()


class AccountView(
    GenericAPIView,
    BaseResponseMixin
):

    serializer_class = AccountSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return (
                UserIsAuthenticated(),
                BillingPlanPermission(),
                ExpiredSubscriptionPermission(),
            )
        else:
            return (
                UserIsAuthenticated(),
                BillingPlanPermission(),
                UserIsAdminOrAccountOwner(),
                ExpiredSubscriptionPermission(),
            )

    def get_object(self):
        return self.request.user.account

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.response_ok(serializer.data)

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(
            instance=instance,
            data=request.data
        )
        slz.is_valid(raise_exception=True)
        service = AccountService(
            instance=slz.instance,
            user=self.request.user
        )
        service.partial_update(**slz.validated_data, force_save=True)
        return self.response_ok(slz.data)


class AccountPlanView(
    GenericAPIView,
    BaseResponseMixin
):
    permission_classes = (
        UserIsAuthenticated,
        BillingPlanPermission,
    )
    serializer_class = AccountPlanSerializer

    def get(self, request, *args, **kwargs):
        account = request.user.account
        serializer = self.get_serializer(account)
        return self.response_ok(serializer.data)
