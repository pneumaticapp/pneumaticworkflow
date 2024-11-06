import stripe
from django.conf import settings
from django.db import transaction
from pneumatic_backend.accounts.models import Account
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.payment.enums import (
    PriceType,
    PriceStatus,
)
from pneumatic_backend.payment.models import (
    Product,
    Price,
)
from pneumatic_backend.payment.services.account import (
    AccountSubscriptionService
)
from pneumatic_backend.payment.stripe.mixins import StripeMixin
from pneumatic_backend.payment.stripe.exceptions import (
    AccountNotFound,
    AccountOwnerNotFound,
    StripeServiceException,
    WebhookServiceException,
)
from pneumatic_backend.utils.logging import (
    capture_sentry_message,
    SentryLogLevel
)
from pneumatic_backend.accounts.services import UserService


class WebhookService(StripeMixin):

    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    secret = settings.STRIPE_SECRET_KEY

    def __init__(self):
        stripe.api_key = self.secret

    def _get_valid_webhook_account_by_stripe_id(
        self,
        stripe_id: str
    ) -> Account:

        """ Check that requested account and account owner exists
            Return master or tenant account for a given subscription """

        account = self._get_account(stripe_id)
        if not account:
            raise AccountNotFound(stripe_id=stripe_id)
        account_owner = account.get_owner()
        if not account_owner:
            raise AccountOwnerNotFound(account_id=account.id)
        return account

    def _get_valid_webhook_account_by_subs(
        self,
        subscription: stripe.Subscription
    ) -> Account:

        """ Check that requested account and account owner exists
            Return master or tenant account for a given subscription """

        webhook_account = self._get_valid_webhook_account_by_stripe_id(
            stripe_id=subscription.customer
        )
        subscription_account = self._get_account_for_subscription(
            account=webhook_account,
            subscription=subscription
        )
        if not subscription_account:
            raise AccountNotFound(subs_id=subscription.id)
        subs_acc_owner = subscription_account.get_owner()
        if not subs_acc_owner:
            raise AccountOwnerNotFound(account_id=subscription_account.id)
        return subscription_account

    def _payment_method_attached(self, event: stripe.Event):

        """ Occurs whenever a new payment method
            is attached to a customer. """

        method = self._get_payment_method(event.data['object']['id'])
        customer = self._get_customer(method.customer)
        self._set_default_payment_method(
            method=method,
            customer=customer,
        )

    def _customer_subscription_created(self, event: stripe.Event):

        """ Occurs whenever a customer is signed up for a new plan. """

        subs_stripe_id = event.data['object']['id']
        subscription = self._get_subscription_by_id(subs_stripe_id)
        subscription_account = self._get_valid_webhook_account_by_subs(
            subscription
        )
        if subscription_account.billing_sync:
            subscription_details = self.get_subscription_details(subscription)
            subscription_service = AccountSubscriptionService(
                instance=subscription_account,
                user=subscription_account.get_owner(),
                auth_type=AuthTokenType.WEBHOOK
            )
            subscription_service.create(
                details=subscription_details,
                payment_card_provided=True
            )

    def _customer_subscription_updated(self, event: stripe.Event):

        """ Occurs whenever a subscription changes
            (e.g., switching from one plan to another,
            or changing the status from trial to active or cancel). """

        subs_stripe_id = event.data['object']['id']
        subscription = self._get_subscription_by_id(subs_stripe_id)
        subscription_account = self._get_valid_webhook_account_by_subs(
            subscription
        )
        if subscription_account.billing_sync:
            subscription_service = AccountSubscriptionService(
                instance=subscription_account,
                user=subscription_account.get_owner(),
                auth_type=AuthTokenType.WEBHOOK
            )
            if event.data['object']['cancel_at']:
                plan_expiration = self._get_aware_datetime_from_timestamp(
                    event.data['object']['cancel_at']
                )
                subscription_service.cancel(plan_expiration)
            else:
                subscription_service.update(
                    details=self.get_subscription_details(subscription),
                )

    def _customer_subscription_deleted(self, event: stripe.Event):

        """ Occurs whenever a customer’s subscription
            cancel immediately. """

        subs_stripe_id = event.data['object']['id']
        subscription = self._get_subscription_by_id(subs_stripe_id)
        subscription_account = self._get_valid_webhook_account_by_subs(
            subscription
        )
        if subscription_account.billing_sync:
            subscription_service = AccountSubscriptionService(
                instance=subscription_account,
                user=subscription_account.get_owner(),
                auth_type=AuthTokenType.WEBHOOK
            )
            plan_expiration = self._get_aware_datetime_from_timestamp(
                event.data['object']['ended_at']
            )
            subscription_service.expired(plan_expiration)

    def _product_created(self, event: stripe.Event):

        """ Occurs whenever a product is created. """

        stripe_id = event.data['object']['id']
        name = event.data['object']['name']
        Product.objects.create(
            stripe_id=stripe_id,
            name=name,
            is_active=event.data['object']['active'],
            is_subscription=False,
            code=self._get_product_code(
                stripe_id=stripe_id,
                name=name
            )
        )

    def _product_updated(self, event: stripe.Event):

        """ Occurs whenever a product is updated. """

        stripe_id = event.data['object']['id']
        Product.objects.filter(stripe_id=stripe_id).update(
            name=event.data['object']['name'],
            is_active=event.data['object']['active']
        )

    def _product_deleted(self, event: stripe.Event):

        """ Occurs whenever a product is deleted. """

        stripe_id = event.data['object']['id']
        Price.objects.filter(product__stripe_id=stripe_id).delete()
        Product.objects.filter(stripe_id=stripe_id).delete()

    def _price_created(self, event: stripe.Event):

        """ Occurs whenever a price is created. """

        self._create_price(event.data['object'])

    def _price_updated(self, event: stripe.Event):

        """ Occurs whenever a price is updated. """

        product_stripe_id = event.data['object']['product']
        product = Product.objects.get(stripe_id=product_stripe_id)
        price_stripe_id = event.data['object']['id']
        if event.data['object']['type'] == PriceType.RECURRING:
            billing_period = event.data['object']['recurring']['interval']
            name = f"{product.name} {billing_period}"
            price_type = PriceType.RECURRING
            trial_days = event.data['object']['recurring']['trial_period_days']
        else:
            billing_period = None
            name = product.name
            price_type = PriceType.ONE_TIME
            trial_days = None

        price = Price.objects.filter(stripe_id=price_stripe_id).first()
        if event.data['object']['active']:
            if price.is_archived:
                status = PriceStatus.ARCHIVED
            else:
                status = PriceStatus.ACTIVE
        else:
            status = PriceStatus.INACTIVE
        Price.objects.filter(stripe_id=price_stripe_id).update(
            name=name,
            status=status,
            price_type=price_type,
            price=event.data['object']['unit_amount'],
            trial_days=trial_days,
            billing_period=billing_period,
            currency=event.data['object']['currency']
        )

    def _price_deleted(self, event: stripe.Event):

        """ Occurs whenever a price is deleted. """

        stripe_id = event.data['object']['id']
        Price.objects.filter(stripe_id=stripe_id).delete()

    def _customer_updated(self, event: stripe.Event):

        stripe_id = event.data['object']['id']
        account = self._get_valid_webhook_account_by_stripe_id(stripe_id)
        if account.billing_sync:
            account_owner = account.users.filter(
                is_account_owner=True,
                email=event.data['object']['email']
            ).first()
            if not account_owner:
                raise AccountOwnerNotFound(
                    account_id=account.id,
                    customer_email=event.data['object']['email'],
                    owner_email=account.get_owner().email
                )
            service = UserService(
                auth_type=AuthTokenType.WEBHOOK,
                instance=account_owner
            )
            service.partial_update(
                phone=event.data['object']['phone'],
                force_save=True
            )

    def handle(self, data: dict):
        try:
            event = stripe.Event.construct_from(
                values=data,
                key=self.secret
            )
        except ValueError:
            raise WebhookServiceException('Invalid payload')
        else:
            handler_name = f"_{event.type.replace('.', '_')}"
            handler = getattr(self, handler_name, None)
            if handler:
                with transaction.atomic():
                    try:
                        handler(event)
                    except (
                        WebhookServiceException,
                        StripeServiceException
                    ) as ex:
                        capture_sentry_message(
                            message=ex.message,
                            level=SentryLogLevel.ERROR,
                            data={
                                'event_type': event.type,
                                **ex.details
                            }
                        )
                        raise
            else:
                capture_sentry_message(
                    message='Webhook handler not found',
                    level=SentryLogLevel.ERROR,
                    data={
                        'event_id': event.id,
                        'event_type': event.type,
                    }
                )
