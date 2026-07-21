from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework.generics import (
    GenericAPIView,
)

from src.accounts.permissions import (
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
    UserIsAdminOrAccountOwner,
)
from src.accounts.serializers.accounts import (
    AccountPlanSerializer,
    AccountSerializer,
)
from src.accounts.services.account import AccountService
from src.generics.mixins.views import (
    BaseResponseMixin,
)
from src.generics.permissions import (
    UserIsAuthenticated,
)
from src.openapi import (
    ACCESS_ADMIN_BASE,
    ACCESS_AUTH,
    ACCESS_AUTH_BASIC,
    FORBIDDEN,
    UNAUTHORIZED,
    VALIDATION_ERROR,
)

UserModel = get_user_model()


class AccountView(
    GenericAPIView,
    BaseResponseMixin,
):

    serializer_class = AccountSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return (
                UserIsAuthenticated(),
                BillingPlanPermission(),
                ExpiredSubscriptionPermission(),
            )
        return (
            UserIsAuthenticated(),
            BillingPlanPermission(),
            UserIsAdminOrAccountOwner(),
            ExpiredSubscriptionPermission(),
        )

    def get_object(self):
        return self.request.user.account

    @extend_schema(
        tags=['Accounts'],
        summary='Get account',
        description=ACCESS_AUTH,
        responses={
            200: AccountSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.response_ok(serializer.data)

    @extend_schema(
        tags=['Accounts'],
        summary='Update account',
        description=ACCESS_ADMIN_BASE,
        request=AccountSerializer,
        responses={
            200: AccountSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(
            instance=instance,
            data=request.data,
        )
        slz.is_valid(raise_exception=True)
        service = AccountService(
            instance=slz.instance,
            user=self.request.user,
        )
        service.partial_update(**slz.validated_data, force_save=True)
        return self.response_ok(slz.data)


class AccountPlanView(
    GenericAPIView,
    BaseResponseMixin,
):
    permission_classes = (
        UserIsAuthenticated,
        BillingPlanPermission,
    )
    serializer_class = AccountPlanSerializer

    @extend_schema(
        tags=['Accounts'],
        summary='Get account plan',
        description=ACCESS_AUTH_BASIC,
        responses={
            200: AccountPlanSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    def get(self, request, *args, **kwargs):
        account = request.user.account
        serializer = self.get_serializer(account)
        return self.response_ok(serializer.data)
