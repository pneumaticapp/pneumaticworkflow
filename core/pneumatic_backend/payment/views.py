from django.db.models import Prefetch
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from pneumatic_backend.payment.permissions import (
    ProjectBillingPermission
)
from pneumatic_backend.accounts.permissions import (
    AccountOwnerPermission,
    UserIsAdminOrAccountOwner
)
from pneumatic_backend.generics.mixins.views import (
    CustomViewSetMixin,
)
from pneumatic_backend.payment.serializers import (
    PurchaseSerializer,
    ConfirmSerializer,
    CardSetupSerializer,
    ProductSerializer,
    CustomerPortalSerializer,
)
from pneumatic_backend.utils.validation import raise_validation_error
from pneumatic_backend.generics.permissions import UserIsAuthenticated
from pneumatic_backend.accounts.permissions import DisallowForTenantPermission
from pneumatic_backend.payment.models import (
    Price,
    Product
)
from pneumatic_backend.payment.tasks import handle_webhook
from pneumatic_backend.payment.services.exceptions import (
    AccountServiceException
)
from pneumatic_backend.payment.services.account import (
    AccountSubscriptionService
)
from pneumatic_backend.payment.stripe.service import StripeService
from pneumatic_backend.payment.stripe.exceptions import (
    StripeServiceException,
)
from pneumatic_backend.payment import messages
from pneumatic_backend.payment.throttling import (
    PurchaseApiThrottle,
    PurchaseTokenThrottle
)
from pneumatic_backend.payment.stripe.permissions import (
    StripeWebhookPermission
)


class PaymentViewSet(
    CustomViewSetMixin,
    GenericViewSet
):
    action_serializer_classes = {
        'purchase': PurchaseSerializer,
        'confirm': ConfirmSerializer,
        'card_setup': CardSetupSerializer,
        'customer_portal': CustomerPortalSerializer,
        'products': ProductSerializer
    }

    def get_permissions(self):
        if self.action == 'confirm':
            return (ProjectBillingPermission(),)
        elif self.action in {
            'purchase',
            'card_setup',
            'default_payment_method',
            'customer_portal',
        }:
            return (
                ProjectBillingPermission(),
                UserIsAuthenticated(),
                AccountOwnerPermission(),
                DisallowForTenantPermission(),
            )
        else:
            return (
                ProjectBillingPermission(),
                UserIsAuthenticated(),
                UserIsAdminOrAccountOwner(),
                DisallowForTenantPermission(),
            )

    @property
    def throttle_classes(self):
        if self.action == 'purchase':
            return (
                PurchaseApiThrottle,
                PurchaseTokenThrottle
            )
        else:
            return ()

    @action(methods=('POST',), detail=False)
    def purchase(self, request):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        if not request.user.account.billing_sync:
            raise_validation_error(message=messages.MSG_BL_0018)
        service = StripeService(
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser
        )
        try:
            payment_link = service.create_purchase(**slz.validated_data)
        except StripeServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            if payment_link:
                return self.response_ok({'payment_link': payment_link})
            return self.response_ok()

    @action(methods=('GET',), detail=False)
    def confirm(self, request):
        slz = self.get_serializer(data=request.GET)
        slz.is_valid(raise_exception=True)
        if not request.user.account.billing_sync:
            return self.response_ok()
        token = slz.validated_data['token']
        service = StripeService(
            auth_type=token['auth_type'],
            is_superuser=token['is_superuser'],
            user=token.user
        )
        try:
            service.confirm(subscription_data=token.get_subscription_data())
        except StripeServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()

    @action(methods=('GET',), detail=False, url_path='card-setup')
    def card_setup(self, request):
        slz = self.get_serializer(data=request.GET)
        slz.is_valid(raise_exception=True)
        service = StripeService(
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser
        )
        try:
            setup_link = service.get_payment_method_checkout_link(
                **slz.validated_data
            )
        except StripeServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok({'setup_link': setup_link})

    @action(methods=('GET',), detail=False)
    def products(self, request):
        qst = Product.objects.prefetch_related(
            Prefetch(
                lookup='prices',
                queryset=Price.objects.active_or_archived()
            )
        ).active()
        slz = self.get_serializer(qst, many=True)
        return self.response_ok(slz.data)

    @action(methods=('GET',), detail=False, url_path='default-payment-method')
    def default_payment_method(self, request):
        service = StripeService(
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser
        )
        method_details = service.get_payment_method()
        if method_details:
            return self.response_ok(method_details)
        return self.response_not_found()

    @action(methods=('GET',), detail=False, url_path='customer-portal')
    def customer_portal(self, request):
        slz = self.get_serializer(data=request.GET)
        slz.is_valid(raise_exception=True)
        service = StripeService(
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser
        )
        try:
            link = service.get_customer_portal_link(
                cancel_url=slz.validated_data['cancel_url']
            )
        except StripeServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok({'link': link})


class SubscriptionViewSet(
    CustomViewSetMixin,
    GenericViewSet
):

    permission_classes = (
        ProjectBillingPermission,
        UserIsAuthenticated,
        AccountOwnerPermission,
        DisallowForTenantPermission,
    )

    @action(methods=('POST',), detail=False)
    def cancel(self, request):
        if not request.user.account.billing_sync:
            raise_validation_error(message=messages.MSG_BL_0018)
        service = StripeService(
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser
        )
        try:
            service.cancel_subscription()
        except StripeServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok()

    @action(methods=('POST',), detail=False, url_path='downgrade-to-free')
    def downgrade_to_free(self, request):
        if not request.user.account.billing_sync:
            raise_validation_error(message=messages.MSG_BL_0018)
        service = AccountSubscriptionService(
            instance=request.user.account,
            user=request.user,
            is_superuser=request.is_superuser,
        )
        try:
            service.downgrade_to_free()
        except AccountServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()


class StripeViewSet(
    CustomViewSetMixin,
    GenericViewSet
):

    action_permission_classes = {
        'webhooks': (
            ProjectBillingPermission(),
            StripeWebhookPermission(),
        ),
    }

    @action(methods=('POST',), detail=False)
    def webhooks(self, request):
        handle_webhook.delay(data=request.data)
        return self.response_ok()
