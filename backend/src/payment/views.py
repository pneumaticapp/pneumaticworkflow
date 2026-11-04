from django.db.models import Prefetch
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from src.accounts.permissions import (
    AccountOwnerPermission,
    DisallowForTenantPermission,
    UserIsAdminOrAccountOwner,
)
from src.generics.mixins.views import (
    CustomViewSetMixin,
)
from src.generics.permissions import UserIsAuthenticated
from src.logs.events import AuditEventService
from src.payment import messages
from src.payment.models import (
    Price,
    Product,
)
from src.payment.serializers import (
    CardSetupSerializer,
    ConfirmSerializer,
    CustomerPortalSerializer,
    ProductSerializer,
    PurchaseSerializer,
)
from src.payment.stripe.exceptions import (
    StripeServiceException,
)
from src.payment.stripe.permissions import (
    StripeWebhookPermission,
)
from src.payment.stripe.service import StripeService
from src.payment.tasks import handle_webhook
from src.payment.throttling import (
    PurchaseApiThrottle,
    PurchaseTokenThrottle,
)
from src.openapi.responses import (
    EMPTY,
    FORBIDDEN,
    TOO_MANY_REQUESTS,
    UNAUTHORIZED,
    VALIDATION_ERROR,
)
from src.openapi.helpers import unpaginated_schema
from src.openapi.internal_serializers import (
    CustomerPortalResponseSerializer,
    PaymentCardResponseSerializer,
    PaymentLinkResponseSerializer,
    SetupLinkResponseSerializer,
)
from src.utils.validation import raise_validation_error


class PaymentViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    action_serializer_classes = {
        'purchase': PurchaseSerializer,
        'confirm': ConfirmSerializer,
        'card_setup': CardSetupSerializer,
        'customer_portal': CustomerPortalSerializer,
        'products': ProductSerializer,
    }

    def get_permissions(self):
        if self.action == 'confirm':
            return ()
        if self.action in {
            'purchase',
            'card_setup',
            'default_payment_method',
            'customer_portal',
        }:
            return (
                UserIsAuthenticated(),
                AccountOwnerPermission(),
                DisallowForTenantPermission(),
            )
        return (
            UserIsAuthenticated(),
            UserIsAdminOrAccountOwner(),
            DisallowForTenantPermission(),
        )

    @property
    def throttle_classes(self):
        if self.action == 'purchase':
            return (
                PurchaseApiThrottle,
                PurchaseTokenThrottle,
            )
        return ()

    @extend_schema(
        tags=['Payment'],
        summary='Purchase products or update a subscription',
        description=(
            'Requires an authenticated account owner on a non-tenant '
            'account and billing synchronization enabled. Product codes '
            'are PRICE codes returned by products; quantity must be >=1. '
            'Returns a checkout payment_link when browser checkout is '
            'needed, or empty 204 when the purchase is applied without '
            'checkout. Uses the configured payment throttle rates.'
        ),
        request=PurchaseSerializer,
        responses={
            200: PaymentLinkResponseSerializer,
            204: EMPTY,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            429: TOO_MANY_REQUESTS,
        },
        examples=[OpenApiExample(
            'Purchase a price from the product catalog',
            value={
                'success_url': 'https://example.com/billing/success',
                'cancel_url': 'https://example.com/billing',
                'products': [{'code': 'price-code-from-products',
                              'quantity': 5}],
            },
            request_only=True,
        )],
    )
    @action(methods=('POST',), detail=False)
    def purchase(self, request):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        if not request.user.account.billing_sync:
            raise_validation_error(message=messages.MSG_BL_0018)
        service = StripeService(
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        try:
            payment_link = service.create_purchase(**slz.validated_data)
        except StripeServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            if payment_link:
                return self.response_ok({'payment_link': payment_link})
            return self.response_ok()

    @extend_schema(
        tags=['Payment'],
        summary='Confirm a completed checkout',
        description=(
            'Supply an authenticated account context and the signed '
            'confirmation token from the checkout return URL. Applies '
            'subscription data encoded in that token. Returns empty 204, '
            'including when billing synchronization is disabled.'
        ),
        auth=[{'tokenAuth': []}],
        parameters=[ConfirmSerializer],
        responses={
            204: EMPTY,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
        },
    )
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
            user=token.user,
        )
        try:
            service.confirm(subscription_data=token.get_subscription_data())
        except StripeServiceException as ex:
            raise_validation_error(message=ex.message)
        return self.response_ok()

    @extend_schema(
        tags=['Payment'],
        summary='Get the payment-card setup checkout URL',
        description=(
            'Requires an authenticated account owner on a non-tenant '
            'account. Redirect the browser to setup_link; success_url and '
            'optional cancel_url control the return locations.'
        ),
        parameters=[CardSetupSerializer],
        responses={
            200: SetupLinkResponseSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    @action(methods=('GET',), detail=False, url_path='card-setup')
    def card_setup(self, request):
        slz = self.get_serializer(data=request.GET)
        slz.is_valid(raise_exception=True)
        service = StripeService(
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        try:
            setup_link = service.get_payment_method_checkout_link(
                **slz.validated_data,
            )
        except StripeServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok({'setup_link': setup_link})

    @unpaginated_schema
    @extend_schema(
        tags=['Payment'],
        summary='List purchasable products and their prices',
        description=(
            'Requires an authenticated admin/account owner on a non-tenant '
            'account. Returns a flat array of active products with active '
            'or archived prices. Use the nested price code in purchase '
            'requests. No pagination is applied.'
        ),
        responses={
            200: ProductSerializer(many=True),
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    @action(methods=('GET',), detail=False)
    def products(self, request):
        qst = Product.objects.prefetch_related(
            Prefetch(
                lookup='prices',
                queryset=Price.objects.active_or_archived(),
            ),
        ).active()
        slz = self.get_serializer(qst, many=True)
        return self.response_ok(slz.data)

    @extend_schema(
        tags=['Payment'],
        summary='Get the default payment card summary',
        description=(
            'Requires an authenticated account owner on a non-tenant '
            'account. Returns card brand and last four digits. If no '
            'payment method exists, returns 404 with an empty body.'
        ),
        responses={
            200: PaymentCardResponseSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: EMPTY,
        },
    )
    @action(methods=('GET',), detail=False, url_path='default-payment-method')
    def default_payment_method(self, request):
        service = StripeService(
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        method_details = service.get_payment_method()
        if method_details:
            return self.response_ok(method_details)
        return self.response_not_found()

    @extend_schema(
        tags=['Payment'],
        summary='Get the Stripe customer portal URL',
        description=(
            'Requires an authenticated account owner on a non-tenant '
            'account. Redirect the browser to link. cancel_url is used as '
            'the portal return URL.'
        ),
        parameters=[CustomerPortalSerializer],
        responses={
            200: CustomerPortalResponseSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    @action(methods=('GET',), detail=False, url_path='customer-portal')
    def customer_portal(self, request):
        slz = self.get_serializer(data=request.GET)
        slz.is_valid(raise_exception=True)
        service = StripeService(
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        try:
            link = service.get_customer_portal_link(
                cancel_url=slz.validated_data['cancel_url'],
            )
        except StripeServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok({'link': link})


class SubscriptionViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):

    permission_classes = (
        UserIsAuthenticated,
        AccountOwnerPermission,
        DisallowForTenantPermission,
    )

    @extend_schema(
        tags=['Payment'],
        summary='Cancel renewal of the account subscription',
        description=(
            'Requires an authenticated account owner on a non-tenant '
            'account and billing synchronization enabled. Sets Stripe '
            'cancel_at_period_end: access lasts until the paid period '
            'expires. Returns empty 204 and audits the cancellation.'
        ),
        request=None,
        responses={
            204: EMPTY,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        },
    )
    @action(methods=('POST',), detail=False)
    def cancel(self, request):
        if not request.user.account.billing_sync:
            raise_validation_error(message=messages.MSG_BL_0018)
        service = StripeService(
            user=request.user,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        try:
            service.cancel_subscription()
        except StripeServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            AuditEventService.subscription_cancelled(
                user=request.user,
                auth_type=request.token_type,
            )
            return self.response_ok()


class StripeViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):

    action_permission_classes = {
        'webhooks': (
            StripeWebhookPermission(),
        ),
    }

    @extend_schema(
        tags=['Payment'],
        summary='Receive a Stripe billing event',
        description=(
            'Provider callback. Queues the Stripe event JSON for asynchronous '
            'processing and acknowledges with empty 204. No Pneumatic '
            'token is required. Staging/production enforce the configured '
            'source-IP allowlist. The current handler does not verify the '
            'Stripe-Signature header; a 204 is not confirmation that the '
            'event has been applied.'
        ),
        auth=[],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string'},
                    'type': {'type': 'string'},
                    'data': {
                        'type': 'object',
                        'properties': {'object': {'type': 'object'}},
                        'additionalProperties': True,
                    },
                },
                'additionalProperties': True,
            },
        },
        responses={204: EMPTY, 401: UNAUTHORIZED, 403: FORBIDDEN},
    )
    @action(methods=('POST',), detail=False)
    def webhooks(self, request):
        handle_webhook.delay(data=request.data)
        return self.response_ok()
