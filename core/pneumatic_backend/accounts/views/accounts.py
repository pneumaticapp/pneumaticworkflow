from django.contrib.auth import get_user_model
from rest_framework.generics import (
    GenericAPIView,
)
from pneumatic_backend.accounts.permissions import (
    UserIsAdminOrAccountOwner,
    ExpiredSubscriptionPermission,
)
from pneumatic_backend.accounts.services import AccountService
from pneumatic_backend.accounts.serializers.accounts import (
    AccountSerializer,
    AccountPlanSerializer,
)
from pneumatic_backend.generics.mixins.views import (
    BaseResponseMixin,
)
from pneumatic_backend.generics.permissions import (
    UserIsAuthenticated,
    PaymentCardPermission,
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
                ExpiredSubscriptionPermission(),
            )
        else:
            return (
                UserIsAuthenticated(),
                UserIsAdminOrAccountOwner(),
                ExpiredSubscriptionPermission(),
                PaymentCardPermission(),
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
    permission_classes = (UserIsAuthenticated,)
    serializer_class = AccountPlanSerializer

    def get(self, request, *args, **kwargs):
        account = request.user.account
        serializer = self.get_serializer(account)
        return self.response_ok(serializer.data)
