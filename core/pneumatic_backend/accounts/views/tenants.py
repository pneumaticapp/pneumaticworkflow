from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import transaction
from rest_framework.mixins import (
    ListModelMixin,
    DestroyModelMixin,
)
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from pneumatic_backend.analytics.services import AnalyticService
from pneumatic_backend.accounts.permissions import (
    UserIsAdminOrAccountOwner,
    SubscriptionPermission,
    MasterAccountPermission,
    MasterAccountAccessPermission,
)
from pneumatic_backend.generics.permissions import (
    UserIsAuthenticated,
    PaymentCardPermission,
)
from pneumatic_backend.generics.mixins.views import (
    CustomViewSetMixin,
)
from pneumatic_backend.accounts.models import Account
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
)
from pneumatic_backend.accounts.serializers.tenant import TenantSerializer
from pneumatic_backend.accounts.filters import TenantsFilterSet
from pneumatic_backend.authentication.services import AuthService
from pneumatic_backend.generics.filters import PneumaticFilterBackend
from pneumatic_backend.accounts.services import (
    AccountService,
    UserService,
)
from pneumatic_backend.accounts.services.exceptions import (
    AccountServiceException,
    UserServiceException
)
from pneumatic_backend.utils.validation import raise_validation_error
from pneumatic_backend.processes.api_v2.services.system_workflows import (
    SystemWorkflowService
)
from pneumatic_backend.payment.stripe.service import StripeService
from pneumatic_backend.payment.stripe.exceptions import StripeServiceException
from pneumatic_backend.payment.tasks import (
    increase_plan_users,
)

UserModel = get_user_model()


class TenantsViewSet(
    CustomViewSetMixin,
    DestroyModelMixin,
    ListModelMixin,
    GenericViewSet
):
    filter_backends = [PneumaticFilterBackend]
    action_filterset_classes = {
        'list': TenantsFilterSet
    }
    serializer_class = TenantSerializer

    def get_permissions(self):
        if self.action in (
            'list',
            'create',
            'count'
        ):
            return (
                UserIsAuthenticated(),
                UserIsAdminOrAccountOwner(),
                MasterAccountPermission(),
                SubscriptionPermission(),
                PaymentCardPermission(),
            )
        else:
            return (
                UserIsAuthenticated(),
                UserIsAdminOrAccountOwner(),
                MasterAccountAccessPermission(),
                SubscriptionPermission(),
                PaymentCardPermission(),
            )

    def get_queryset(self):
        return self.request.user.account.tenants.only_tenants()

    def perform_destroy(self, instance: Account):
        master_account = self.request.user.account
        with transaction.atomic():
            if (
                master_account.billing_plan != BillingPlanType.PREMIUM
                and master_account.billing_sync
                and settings.PROJECT_CONF['BILLING']
            ):
                try:
                    stripe_service = StripeService(
                        user=self.request.user,
                        subscription_account=instance,
                        is_superuser=self.request.is_superuser,
                        auth_type=self.request.token_type,
                    )
                    stripe_service.cancel_subscription()
                except StripeServiceException as ex:
                    raise_validation_error(message=ex.message)
            instance.delete()
            account_service = AccountService(
                instance=master_account,
                user=self.request.user,
                is_superuser=self.request.is_superuser,
                auth_type=self.request.token_type,
            )
            account_service.update_users_counts()
            if (
                master_account.billing_plan == BillingPlanType.PREMIUM
                and master_account.billing_sync
                and settings.PROJECT_CONF['BILLING']
            ):
                increase_plan_users.delay(
                    account_id=master_account.id,
                    is_superuser=self.request.is_superuser,
                    auth_type=self.request.token_type,
                )

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance=instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        new_tenant_name = serializer.validated_data.get('tenant_name')
        old_tenant_name = instance.tenant_name
        with (transaction.atomic()):
            instance = serializer.save()
            if (
                new_tenant_name is not None
                and new_tenant_name != old_tenant_name
                and instance.billing_sync
                and settings.PROJECT_CONF['BILLING']
            ):
                try:
                    stripe_service = StripeService(
                        user=self.request.user,
                        subscription_account=instance,
                        is_superuser=self.request.is_superuser,
                        auth_type=self.request.token_type,
                    )
                    stripe_service.update_subscription_description()
                except StripeServiceException as ex:
                    raise_validation_error(message=ex.message)
            return self.response_ok(serializer.data)

    def create(self, request, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        account_service = AccountService(
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        user_service = UserService(
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        master_account = request.user.account
        with transaction.atomic():
            try:
                tenant_account = account_service.create(
                    tenant_name=slz.validated_data['tenant_name'],
                    master_account=master_account,
                )
                tenant_user = user_service.create_tenant_account_owner(
                    tenant_account=tenant_account,
                    master_account=master_account
                )
                account_service.user = tenant_user
                account_service.update_users_counts()
            except (AccountServiceException, UserServiceException) as ex:
                raise_validation_error(message=ex.message)
            else:
                service = SystemWorkflowService(user=tenant_user)
                service.create_onboarding_templates()
                service.create_activated_templates()
                if (
                    settings.PROJECT_CONF['BILLING']
                    and master_account.billing_sync
                ):
                    if master_account.billing_plan == BillingPlanType.PREMIUM:
                        increase_plan_users.delay(
                            account_id=master_account.id,
                            is_superuser=request.is_superuser,
                            auth_type=request.token_type,
                        )
                    else:
                        try:
                            stripe_service = StripeService(
                                user=request.user,
                                subscription_account=tenant_account,
                                is_superuser=request.is_superuser,
                                auth_type=request.token_type,
                            )
                            stripe_service.create_off_session_subscription(
                                products=[
                                    {
                                        'code': 'unlimited_month',
                                        'quantity': 1
                                    }
                                ]
                            )
                        except StripeServiceException as ex:
                            raise_validation_error(message=ex.message)

                AnalyticService.tenants_added(
                    master_user=request.user,
                    tenant_account=tenant_account,
                    is_superuser=request.is_superuser,
                    auth_type=request.token_type
                )
        response_slz = self.serializer_class(instance=tenant_account)
        return self.response_ok(response_slz.data)

    @action(methods=('GET',), detail=True)
    def token(self, request, **kwargs):
        tenant_account = self.get_object()
        account_owner = tenant_account.get_owner()
        token = AuthService.get_auth_token(
            user=account_owner,
            user_agent=request.headers.get(
                'User-Agent',
                request.META.get('HTTP_USER_AGENT')
            ),
            user_ip=request.META.get('HTTP_X_REAL_IP'),
            superuser_mode=True,
        )
        AnalyticService.tenants_accessed(
            master_user=request.user,
            tenant_account=tenant_account,
            is_superuser=request.is_superuser,
            auth_type=request.token_type
        )
        return self.response_ok({'token': token})

    @action(methods=('GET',), detail=False)
    def count(self, request, **kwargs):
        return self.response_ok({
            'count': self.get_queryset().count()
        })
