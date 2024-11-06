import stripe
from stripe.error import (
    CardError,
    StripeError,
)
from datetime import timedelta
from typing import List, Optional
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import (
    MultipleObjectsReturned,
    ObjectDoesNotExist
)
from django.contrib.auth import get_user_model
from pneumatic_backend.payment.services.account import (
    AccountSubscriptionService
)
from pneumatic_backend.payment.stripe import exceptions
from pneumatic_backend.accounts.models import Account
from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.accounts.services import AccountService
from pneumatic_backend.payment.stripe.tokens import ConfirmToken
from pneumatic_backend.payment.stripe.entities import (
    CardDetails,
    PurchaseItem,
    TokenSubscriptionData,
)
from pneumatic_backend.payment.models import Price
from pneumatic_backend.utils.logging import (
    capture_sentry_message,
    SentryLogLevel
)
from pneumatic_backend.payment.stripe.mixins import StripeMixin

UserModel = get_user_model()


class StripeService(StripeMixin):

    """ Performs actions on account subscriptions.
        The account has a master subscription and can have
        tenant subscriptions. Subscription_account indicates
        which tenant's subscription in work now """

    secret = settings.STRIPE_SECRET_KEY

    def __init__(
        self,
        user: UserModel,
        subscription_account: Optional[Account] = None,
        auth_type: AuthTokenType.LITERALS = AuthTokenType.USER,
        is_superuser: bool = False
    ):
        self.user = user
        self.account = user.account
        self.auth_type = auth_type
        self.is_superuser = is_superuser
        stripe.api_key = self.secret

        if subscription_account:
            self.subscription_owner = subscription_account.get_owner()
            self.subscription_account = subscription_account
        else:
            self.subscription_account = self.account
            self.subscription_owner = user

        self.subscription_service = AccountSubscriptionService(
            instance=self.subscription_account,
            user=self.subscription_owner,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )
        self.customer = self._get_or_create_customer()
        self.subscription = self._get_current_subscription()
        self.payment_method = self._get_current_payment_method()

    def _get_or_create_customer(self) -> stripe.Customer:

        customer = None
        if self.account.stripe_id:
            customer = self._get_customer(self.account.stripe_id)
        if not customer:
            account_owner = self.account.get_owner()
            customer = self._get_customer_by_email(account_owner.email)
            if customer:
                # update found customer details
                self.update_customer(customer)
            else:
                customer = stripe.Customer.create(
                    email=account_owner.email,
                    name=self.account.name,
                    phone=account_owner.phone,
                    description=account_owner.name,
                )
            account_service = AccountService(
                user=self.user,
                instance=self.account,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type
            )
            account_service.partial_update(
                stripe_id=customer.id,
                force_save=True
            )
        return customer

    def _get_current_subscription(self) -> Optional[stripe.Subscription]:

        subscription = self._get_subscription_for_account(
            customer=self.customer,
            subscription_account=self.subscription_account
        )
        if self.account.billing_sync:
            if subscription and not self.subscription_account.is_subscribed:
                self.subscription_service.create(
                    details=self.get_subscription_details(subscription),
                    payment_card_provided=self.account.payment_card_provided,
                )
            elif not subscription and self.subscription_account.is_subscribed:
                self.subscription_service.expired(
                    plan_expiration=timezone.now()
                )
        return subscription

    def _get_current_payment_method(
        self,
        *args,
        **kwargs
    ) -> Optional[stripe.PaymentMethod]:

        method = super()._get_current_payment_method(customer=self.customer)
        if self.account.billing_sync:
            if method and not self.account.payment_card_provided:
                self.subscription_service.payment_card_provided(value=True)
            elif not method and self.account.payment_card_provided:
                self.subscription_service.payment_card_provided(value=False)
        return method

    def _get_confirm_token(
        self,
        subscription_data: Optional[TokenSubscriptionData] = None
    ) -> ConfirmToken:

        token = ConfirmToken()
        token['auth_type'] = self.auth_type
        token['is_superuser'] = self.is_superuser
        token['account_id'] = self.account.id
        token['user_id'] = self.user.id
        if subscription_data:
            token['subscription'] = subscription_data
        return token

    def _get_success_url_with_token(
        self,
        url: str,
        subscription_data: Optional[TokenSubscriptionData] = None
    ) -> str:

        """ Add confirm token for identification account """

        token = self._get_confirm_token(subscription_data)
        if url.find('?') > 0:
            return f'{url}&token={token}'
        else:
            return f'{url}?token={token}'

    def _get_checkout_session_url(
        self,
        success_url: str,
        cancel_url: str,
        **kwargs
    ) -> str:

        """ Check if checkout link already exist, prevent duplicate """

        client_reference_id = self._get_idempotency_key(
            stripe_id=self.customer.stripe_id,
            account_id=self.subscription_account.id,
            **kwargs
        )
        open_sessions = stripe.checkout.Session.list(
            customer=self.customer,
            status='open',
        )
        for session in open_sessions:
            if session.client_reference_id == client_reference_id:
                return session.url

        session = stripe.checkout.Session.create(
            customer=self.customer,
            client_reference_id=client_reference_id,
            success_url=success_url,
            cancel_url=cancel_url,
            **kwargs
        )
        return session.url

    def _create_subscription(
        self,
        item: PurchaseItem,
        invoice_items: List[PurchaseItem],
    ):

        """ Create new off-session purchase new subscription
            and additional products """

        if self.subscription_account.trial_ended:
            trial_period_days = None
        else:
            trial_period_days = item.price.trial_days
        add_invoice_items = [
            {
                "price": invoice_item.price.stripe_id,
                "quantity": invoice_item.quantity,
            }
            for invoice_item in invoice_items
        ]
        items = [
            {
                "price": item.price.stripe_id,
                "quantity": item.quantity,
            }
        ]
        self.subscription = stripe.Subscription.create(
            customer=self.customer,
            items=items,
            add_invoice_items=add_invoice_items,
            trial_period_days=trial_period_days,
            idempotency_key=self._get_idempotency_key(
                account_id=self.subscription_account.id,
                items=items,
                add_invoice_items=add_invoice_items,
                trial_period_days=trial_period_days,
                stripe_id=self.subscription_account.stripe_id,
                date=timezone.now().strftime('%Y-%m-%dT%H:%M')
            ),
            metadata={'account_id': self.subscription_account.id},
            description=(
                self.subscription_account.tenant_name
                if self.subscription_account.is_tenant
                else 'Main'
            )
        )
        self.subscription_service.create(
            details=self.get_subscription_details(self.subscription),
            payment_card_provided=True,
        )

    def _update_subscription(
        self,
        item: PurchaseItem,
        invoice_items: List[PurchaseItem],
    ):

        """ Create new off-session purchase updated
            current subscription and purchase additional products """

        current_item = self.subscription['items'].data[0]
        if current_item.price.id == item.price.stripe_id:
            items = [
                {
                    "id": current_item.id,
                    "quantity": item.quantity,
                }
            ]
        else:
            items = [
                {
                    "id": current_item.id,
                    "deleted": True,
                },
                {
                    "price": item.price.stripe_id,
                    "quantity": item.quantity,
                }
            ]
        add_invoice_items = [
            {
                "price": invoice_item.price.stripe_id,
                "quantity": invoice_item.quantity,
            }
            for invoice_item in invoice_items
        ]
        self.subscription = stripe.Subscription.modify(
            id=self.subscription.id,
            items=items,
            add_invoice_items=add_invoice_items,
            trial_end='now',
            metadata={'account_id': self.subscription_account.id},
            description=(
                self.subscription_account.tenant_name
                if self.subscription_account.is_tenant
                else 'Main'
            )
        )
        self.subscription_service.update(
            details=self.get_subscription_details(self.subscription),
        )

    def _create_invoice(self, invoice_items: List[PurchaseItem]):

        """ Create new off-session purchase non-subscription products """

        invoice = stripe.Invoice.create(
            customer=self.customer,
            collection_method='charge_automatically'
        )
        for invoice_item in invoice_items:
            stripe.InvoiceItem.create(
                invoice=invoice,
                customer=self.customer,
                price=invoice_item.price.stripe_id,
                quantity=invoice_item.quantity
            )
        invoice.finalize_invoice()
        try:
            invoice.pay()
        except stripe.error.InvalidRequestError as ex:
            if ex.user_message == 'Invoice is already paid':
                pass
            else:
                raise

    def _off_session_purchase(self, products: List[dict]):

        """ Purchase any products by existent payment card """

        subscription_item = self._get_valid_subscription_item(products)
        invoice_items = self._get_valid_invoice_items(products)

        if subscription_item:
            if self.subscription:
                self._update_subscription(
                    item=subscription_item,
                    invoice_items=invoice_items
                )
            else:
                self._create_subscription(
                    item=subscription_item,
                    invoice_items=invoice_items
                )
        elif invoice_items:
            self._create_invoice(invoice_items)

    def _get_subscription_checkout_link(
        self,
        item: PurchaseItem,
        success_url: str,
        cancel_url: str,
        invoice_items: Optional[list] = None,
    ) -> str:

        """ Returns payment link for purchasing the subscription """

        line_items = [
            {
                "price": item.price.stripe_id,
                "quantity": item.quantity,
            }
        ]
        if invoice_items:
            for invoice_item in invoice_items:
                line_items.append({
                    "price": invoice_item.price.stripe_id,
                    "quantity": invoice_item.quantity,
                })
        subscription_data = {
            'metadata': {'account_id': self.subscription_account.id},
            'description': (
                self.subscription_account.tenant_name
                if self.subscription_account.is_tenant
                else 'Main'
            )
        }
        if item.price.trial_days and not self.subscription_account.trial_ended:
            subscription_data["trial_period_days"] = item.price.trial_days
            trial_days = item.price.trial_days
        else:
            trial_days = None

        success_url_with_token = self._get_success_url_with_token(
            url=success_url,
            subscription_data=TokenSubscriptionData(
                max_users=item.quantity,
                billing_plan=item.price.product.code,
                trial_days=trial_days
            )
        )
        return self._get_checkout_session_url(
            success_url=success_url_with_token,
            cancel_url=cancel_url,
            line_items=line_items,
            mode='subscription',
            allow_promotion_codes=True,
            subscription_data=subscription_data
        )

    def _get_payment_checkout_link(
        self,
        success_url: str,
        cancel_url: str,
        invoice_items: List[PurchaseItem],
    ) -> Optional[str]:

        """ Returns payment link for purchasing non-subscription products """

        if not invoice_items:
            return None
        line_items = []
        for invoice_item in invoice_items:
            line_items.append({
                "price": invoice_item.price.stripe_id,
                "quantity": invoice_item.quantity,
                "adjustable_quantity": {
                    'enabled': True,
                    'maximum': invoice_item.price.max_quantity,
                    'minimum': invoice_item.min_quantity
                }
            })
        return self._get_checkout_session_url(
            success_url=self._get_success_url_with_token(url=success_url),
            cancel_url=cancel_url,
            line_items=line_items,
            mode='payment',
            allow_promotion_codes=True,
        )

    def _get_checkout_link(
        self,
        products: List[dict],
        success_url: str,
        cancel_url: str,
    ) -> Optional[str]:

        """ Returns payment link for purchasing any products """

        subscription_item = self._get_valid_subscription_item(products)
        invoice_items = self._get_valid_invoice_items(products)
        if subscription_item:
            return self._get_subscription_checkout_link(
                item=subscription_item,
                invoice_items=invoice_items,
                success_url=success_url,
                cancel_url=cancel_url,
            )
        elif invoice_items:
            return self._get_payment_checkout_link(
                invoice_items=invoice_items,
                success_url=success_url,
                cancel_url=cancel_url,
            )
        else:
            return None

    def _get_valid_premium_subscription_item(
        self,
        price: Price,
        quantity: int
    ):
        if quantity > price.max_quantity:
            raise exceptions.SubsMaxQuantityReached(
                quantity=price.max_quantity,
                product_name=price.product.name
            )
        if quantity < price.min_quantity:
            raise exceptions.SubsMinQuantityReached(
                quantity=price.min_quantity,
                product_name=price.product.name
            )
        if (
            self.subscription_account.billing_plan == BillingPlanType.PREMIUM
            and quantity < self.subscription_account.max_users
        ):
            raise exceptions.DecreaseSubscription()
        return PurchaseItem(
            price=price,
            quantity=quantity,
            min_quantity=None
        )

    def _get_valid_fractionalcoo_subscription_item(
        self,
        price: Price,
        quantity: int
    ) -> PurchaseItem:

        if quantity > price.max_quantity:
            raise exceptions.SubsMaxQuantityReached(
                quantity=price.max_quantity,
                product_name=price.product.name
            )
        if quantity < price.min_quantity:
            raise exceptions.SubsMinQuantityReached(
                quantity=price.min_quantity,
                product_name=price.product.name
            )
        return PurchaseItem(
            price=price,
            quantity=quantity,
            min_quantity=None
        )

    def _get_valid_unlimited_subscription_item(
        self,
        price: Price,
        quantity: int
    ) -> PurchaseItem:

        if quantity > price.max_quantity:
            raise exceptions.SubsMaxQuantityReached(
                quantity=price.max_quantity,
                product_name=price.product.name
            )
        if quantity < price.min_quantity:
            raise exceptions.SubsMinQuantityReached(
                quantity=price.min_quantity,
                product_name=price.product.name
            )
        return PurchaseItem(
            price=price,
            quantity=quantity,
            min_quantity=None
        )

    def _get_valid_subscription_item(
        self,
        products: List[dict]
    ) -> Optional[PurchaseItem]:

        products_dict = {
            product['code']: product['quantity'] for product in products
        }
        try:
            new_price = Price.objects.subscriptions().active_or_archived(
            ).get(code__in=products_dict.keys())
        except MultipleObjectsReturned:
            raise exceptions.MultipleSubscriptionsNotAllowed()
        except ObjectDoesNotExist:
            return None
        else:
            quantity = products_dict[new_price.code]
            if self.subscription:
                current_price = Price.objects.filter(
                    stripe_id=self.subscription['items'].data[0].price.id
                ).first()
                if current_price.currency != new_price.currency:
                    # Modify subscription to another with another currency
                    raise exceptions.ChangeCurrencyDisallowed()
                # Allow update if account on archived price
                elif (
                    new_price.is_archived
                    and current_price.id != new_price.id
                ):
                    raise exceptions.PurchaseArchivedPrice()
            else:
                if new_price.is_archived:
                    raise exceptions.PurchaseArchivedPrice()

            validate_product_method = getattr(
                self,
                f'_get_valid_{new_price.product.code}_subscription_item',
                None
            )
            if not validate_product_method:
                raise exceptions.UnsupportedPlan()
            return validate_product_method(
                price=new_price,
                quantity=quantity
            )

    def _get_valid_invoice_items(
        self,
        products: List[dict]
    ) -> List[PurchaseItem]:

        invoice_items = []
        if self.subscription:
            current_item = self.subscription['items'].data[0]
        else:
            current_item = None
        for product in products:
            try:
                price = Price.objects.not_subscriptions().active().get(
                    code=product['code']
                )
            except ObjectDoesNotExist:
                pass
            else:
                quantity = product['quantity']
                if quantity > price.max_quantity:
                    raise exceptions.MaxQuantityReached(
                        quantity=price.max_quantity,
                        product_name=price.product.name
                    )
                if quantity < price.min_quantity:
                    raise exceptions.MinQuantityReached(
                        quantity=price.min_quantity,
                        product_name=price.product.name
                    )
                if (
                    current_item
                    and current_item.price.currency != price.currency
                ):
                    # Modify subscription to another with another currency
                    raise exceptions.ChangeCurrencyDisallowed()

                invoice_items.append(
                    PurchaseItem(
                        price=price,
                        quantity=quantity,
                        min_quantity=price.min_quantity
                    )
                )
        return invoice_items

    def _log_stripe_error(
        self,
        ex: stripe.error.StripeError,
        level: SentryLogLevel.LITERALS = SentryLogLevel.ERROR
    ):
        capture_sentry_message(
            message=f'Stripe {level}. Account ({self.account.id})',
            level=level,
            data={
                'account_id': self.account.id,
                'subscription_account_id': self.subscription_account.id,
                'subscription_id': (
                    self.subscription.id
                    if self.subscription else None
                ),
                'stripe_id': self.account.stripe_id,
                'user': {
                    'id': self.user.id,
                    'email': self.user.email,
                },
                'ex': {
                    'cls': ex.__class__,
                    'message': ex.user_message,
                    'code': ex.code,
                    'json_body': ex.json_body
                }
            }
        )

    def update_customer(
        self,
        customer: Optional[stripe.Customer] = None
    ):
        customer = customer or self.customer
        stripe.Customer.modify(
            id=customer.id,
            name=self.account.name,
            phone=self.user.phone,
            description=self.user.name
        )

    def update_subscription_description(self):
        if self.subscription and self.subscription_account.is_tenant:
            stripe.Subscription.modify(
                id=self.subscription.id,
                description=self.subscription_account.tenant_name
            )

    def create_purchase(
        self,
        products: List[dict],
        success_url: str,
        cancel_url: str,
    ) -> Optional[str]:

        """ Each product represents as dict:
            {
              "quantity": int,
              "code": str // valid stripe price code
            } """

        if self.payment_method:
            try:
                self._off_session_purchase(products=products)
            except StripeError as ex:
                if self.subscription:
                    self._log_stripe_error(ex)
                    if isinstance(ex, CardError):
                        raise exceptions.CardError()
                    else:
                        raise exceptions.PaymentError()
                else:
                    self._log_stripe_error(ex, level=SentryLogLevel.WARNING)
                    return self._get_checkout_link(
                        success_url=success_url,
                        cancel_url=cancel_url,
                        products=products
                    )
        else:
            return self._get_checkout_link(
                success_url=success_url,
                cancel_url=cancel_url,
                products=products
            )

    def get_payment_method_checkout_link(
        self,
        success_url: str,
        cancel_url: str,
    ) -> str:

        """ Returns payment link for setup payment method """

        return self._get_checkout_session_url(
            success_url=self._get_success_url_with_token(url=success_url),
            cancel_url=cancel_url,
            mode='setup',
            payment_method_types=['card'],
        )

    def confirm(
        self,
        subscription_data: Optional[TokenSubscriptionData] = None
    ):

        """ Call after payment from stripe hosted page
            Information will be updated from the webhook

            subscription data contains info about subscription changes
            in case of webhook "subscription created" is late, but need
            activate subscription changes immediately """

        data = {
            'payment_card_provided': True,
            'force_save': True
        }

        # If the webhook "subscription created" has not yet been processed
        tmp_plan_expiration = timezone.now() + timedelta(hours=1)
        plan_expiration = self.subscription_account.plan_expiration
        if (
            subscription_data and (
                (plan_expiration and plan_expiration < tmp_plan_expiration)
                or not plan_expiration
            )
        ):
            data['max_users'] = subscription_data['max_users']
            data['plan_expiration'] = tmp_plan_expiration
            data['billing_plan'] = subscription_data['billing_plan']
            data['tmp_subscription'] = True
            if (
                subscription_data['trial_days']
                and not self.subscription_account.trial_ended
            ):
                trial_start = timezone.now()
                data['trial_start'] = trial_start
                data['trial_end'] = trial_start + timedelta(
                    days=subscription_data['trial_days']
                )

        account_service = AccountService(
            instance=self.subscription_account,
            user=self.subscription_account.get_owner(),
            is_superuser=self.is_superuser,
            auth_type=self.auth_type
        )
        account_service.partial_update(**data)

    def increase_subscription(self, quantity: int):

        """ Change current subscription quantity
            without change the "price" """

        if not self.subscription:
            raise exceptions.SubscriptionNotExist()
        current_item = self.subscription['items'].data[0]
        self.subscription = stripe.Subscription.modify(
            id=self.subscription.id,
            items=[
                {
                    "id": current_item.id,
                    "quantity": quantity,
                }
            ],
            trial_end='now',
            metadata={'account_id': self.subscription_account.id},
            description=(
                self.subscription_account.tenant_name
                if self.subscription_account.is_tenant
                else 'Main'
            )
        )
        self.subscription_service.update(
            details=self.get_subscription_details(self.subscription),
        )

    def cancel_subscription(self):

        if self.subscription:
            self.subscription = stripe.Subscription.modify(
                id=self.subscription.id,
                cancel_at_period_end=True
            )
            details = self.get_subscription_details(self.subscription)
            self.subscription_service.cancel(details.plan_expiration)

    def terminate_subscription(self):

        """ Terminate current subscription.
            Prorates a refund based on the amount of time remaining
            in the current bill cycle."""

        if self.subscription:
            self.subscription.cancel()
        # downgrade to fee plan anyway
        self.subscription_service.downgrade_to_free()

    def get_payment_method(self) -> Optional[CardDetails]:
        if self.payment_method:
            return CardDetails(
                last4=self.payment_method.card['last4'],
                brand=self.payment_method.card['brand']
            )
        return None

    def get_customer_portal_link(
        self,
        cancel_url: str,
    ) -> str:
        session = stripe.billing_portal.session.Session.create(
            customer=self.customer,
            return_url=cancel_url,
        )
        return session.url

    def create_off_session_subscription(self, products):

        if not self.payment_method:
            raise exceptions.CardError()
        try:
            self._off_session_purchase(products=products)
        except StripeError as ex:
            self._log_stripe_error(ex)
            if isinstance(ex, CardError):
                raise exceptions.CardError()
            else:
                raise exceptions.PaymentError()
