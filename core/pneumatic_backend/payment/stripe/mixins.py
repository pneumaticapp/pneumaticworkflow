import json
from hashlib import sha1
from datetime import datetime
from typing import Optional, Tuple

import pytz
import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import ObjectDoesNotExist
from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.payment.enums import PriceType, PriceStatus
from pneumatic_backend.payment.entities import (
    SubscriptionDetails,
)
from pneumatic_backend.payment.models import (
    Product,
    Price,
)
from pneumatic_backend.accounts.models import Account
from pneumatic_backend.utils.salt import get_salt
from pneumatic_backend.payment.stripe import exceptions
from pneumatic_backend.utils.logging import (
    capture_sentry_message,
    SentryLogLevel
)


UserModel = get_user_model()


class StripeMixin:

    active_subscription_status = {'active', 'trialing', 'past_due'}

    def _get_customer(self, stripe_id: str) -> Optional[stripe.Customer]:
        try:
            return stripe.Customer.retrieve(id=stripe_id)
        except stripe.error.InvalidRequestError:
            return None

    def _get_customer_by_email(self, email: str) -> Optional[stripe.Customer]:
        result = stripe.Customer.search(query=f"email:'{email}'")
        customer = None
        if len(result['data']):
            customer = result['data'][0]
        return customer

    def _get_subscription_by_id(self, stripe_id: str) -> stripe.Subscription:
        return stripe.Subscription.retrieve(id=stripe_id)

    def _get_payment_method(self, stripe_id: str) -> stripe.PaymentMethod:
        return stripe.PaymentMethod.retrieve(id=stripe_id)

    def _get_account(self, stripe_id: str) -> Optional[Account]:
        return Account.objects.filter(
            stripe_id=stripe_id
        ).exclude_tenants().first()

    def _get_subscription_for_account(
        self,
        customer: stripe.Customer,
        subscription_account: Account
    ) -> Optional[stripe.Subscription]:

        """ Return subscription for a given account """

        for elem in stripe.Subscription.list(customer=customer):
            try:
                account_id = elem.metadata.get('account_id')
                if (
                    not subscription_account.is_tenant
                    and account_id is None
                    and elem.status in self.active_subscription_status
                ):
                    # Main account subscription without metadata
                    return elem
                elif (
                    int(account_id) == subscription_account.id
                    and elem.status in self.active_subscription_status
                ):
                    # Main or tenant account subscription with metadata
                    return elem
            except (ValueError, TypeError):
                # not number account_id
                capture_sentry_message(
                    message='Invalid subscription metadata',
                    level=SentryLogLevel.ERROR,
                    data={
                        'sub_id': elem.id,
                        'is_tenant': subscription_account.is_tenant,
                        'status': elem.status,
                        'account_id': elem.metadata.get('account_id')
                    }
                )
                continue
        return None

    def _get_account_for_subscription(
        self,
        account: Account,
        subscription: stripe.Subscription
    ) -> Account:

        """ Return account for a given subscription """

        try:
            account_id = subscription.metadata.get('account_id')
            if account_id is None:
                return account
            else:
                account_id = int(account_id)
                if account_id == account.id:
                    return account
                else:
                    return account.tenants.only_tenants().get(id=account_id)
        except (ValueError, TypeError, ObjectDoesNotExist):
            raise exceptions.NotFoundAccountForSubscription(
                account_id=account.id,
                subs_metadata=subscription.metadata
            )

    def get_subscription_details(
        self,
        subscription: stripe.Subscription
    ) -> Optional[SubscriptionDetails]:

        trial_start = self._get_aware_datetime_from_timestamp(
            subscription['trial_start']
        )
        trial_end = self._get_aware_datetime_from_timestamp(
            subscription['trial_end']
        )
        plan_expiration = self._get_aware_datetime_from_timestamp(
            subscription['current_period_end']
        )
        price_data = subscription['items'].data[0].price
        try:
            price = Price.objects.select_related('product').get(
                stripe_id=price_data.id
            )
        except Price.DoesNotExist:
            price = self._create_price(price_data)
        if price.product.code == BillingPlanType.PREMIUM:
            max_users = subscription['quantity']
        else:
            max_users = 1000
        return SubscriptionDetails(
            quantity=subscription['quantity'],
            max_users=max_users,
            billing_plan=price.product.code,
            billing_period=price.billing_period,
            plan_expiration=plan_expiration,
            trial_start=trial_start,
            trial_end=trial_end,
        )

    def _set_default_payment_method(
        self,
        customer: stripe.Customer,
        method: Optional[stripe.PaymentMethod] = None
    ) -> Optional[stripe.PaymentMethod]:

        if not method:
            methods = stripe.PaymentMethod.list(customer=customer)
            if len(methods.data):
                method = methods.data[0]
        if method:
            customer['invoice_settings']['default_payment_method'] = method.id
            customer.save()
            for subscription in stripe.Subscription.list(customer=customer):
                subscription['default_payment_method'] = method.id
                subscription.save()
        return method

    def _get_current_payment_method(
        self,
        customer: stripe.Customer,
    ) -> Optional[stripe.PaymentMethod]:

        """ Returns default or first found payment method """

        method_id = customer['invoice_settings']['default_payment_method']
        if method_id:
            method = self._get_payment_method(method_id)
        else:
            method = self._set_default_payment_method(customer=customer)
        return method

    def _get_normalized_code(self, raw_code: str) -> str:
        return raw_code.replace(' ', '_').lower()

    def _get_aware_datetime_from_timestamp(
        self,
        value: Optional[int] = None
    ) -> Optional[datetime]:
        if not value:
            return None
        tz = pytz.timezone(settings.TIME_ZONE)
        return datetime.fromtimestamp(value, tz=tz)

    def _create_price(self, data: stripe.Price) -> Price:

        product = Product.objects.get(stripe_id=data.product)
        price_stripe_id = data.id
        if data.type == PriceType.RECURRING:
            billing_period = data.recurring['interval']
            name = f"{product.name} {billing_period}"
            max_quantity = 9999
            price_type = PriceType.RECURRING
            trial_days = data.recurring['trial_period_days']
            code = self._get_price_code(
                stripe_id=price_stripe_id,
                code_parts=(product.name, billing_period)
            )
        else:
            billing_period = None
            name = product.name
            max_quantity = 1
            price_type = PriceType.ONE_TIME
            trial_days = None
            code = self._get_price_code(
                stripe_id=price_stripe_id,
                code_parts=(product.name,)
            )
        if data.active:
            status = PriceStatus.ACTIVE
        else:
            status = PriceStatus.INACTIVE

        return Price.objects.create(
            product=product,
            status=status,
            name=name,
            code=code,
            stripe_id=data.id,
            max_quantity=max_quantity,
            min_quantity=0,
            price_type=price_type,
            price=data.unit_amount,
            trial_days=trial_days,
            billing_period=billing_period,
            currency=data.currency
        )

    def _get_price_code(
        self,
        stripe_id: str,
        code_parts: Tuple
    ) -> str:

        """ Not change code for existent prices.
            If exists price with the same code make unique hash """

        instance = Price.objects.filter(stripe_id=stripe_id).first()
        if instance:
            return instance.code
        else:
            code = self._get_normalized_code('_'.join(code_parts))
            another_price = Price.objects.filter(code=code).first()
            if another_price:
                code = f'{code}_{get_salt(6, exclude=("upper",))}'
            return code

    def _get_product_code(
        self,
        stripe_id: str,
        name: str
    ) -> str:

        """ Not change code for existent product.
            If exists product with the same code make unique hash """

        instance = Product.objects.filter(stripe_id=stripe_id).first()
        if instance:
            return instance.code
        else:
            code = self._get_normalized_code(name)
            another_product = Product.objects.filter(code=code).first()
            if another_product:
                return f'{code}_{get_salt(6, exclude=("upper",))}'
            else:
                return code

    def _get_idempotency_key(self, **kwargs) -> str:
        str_value = json.dumps(kwargs, sort_keys=True, ensure_ascii=True)
        return sha1(str_value.encode()).hexdigest()
