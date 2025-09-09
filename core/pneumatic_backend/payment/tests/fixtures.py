from typing import Optional
from pneumatic_backend.payment.models import Price, Product
from pneumatic_backend.payment.enums import (
    PriceType,
    BillingPeriod,
    PriceStatus,
)


def create_test_product(
    stripe_id: str = 'prod_1N8JnDBM2UVM1VfGDN6IsDDg',
    is_active: bool = True,
    name: str = 'Premium',
    is_subscription: bool = True,
    code: str = 'premium',

) -> Product:

    return Product.objects.create(
        name=name,
        is_subscription=is_subscription,
        is_active=is_active,
        stripe_id=stripe_id,
        code=code
    )


def create_test_recurring_price(
    trial_days: Optional[int] = 0,
    status: PriceStatus.LITERALS = PriceStatus.ACTIVE,
    name: str = 'Premium monthly',
    code: str = 'premium_monthly',
    stripe_id: str = 'price_1N8JnDBM2UVM1VfGDN6IsDDg',
    product: Optional[Product] = None,
    price: int = 10000,
    currency: str = 'usd',
    min_quantity: int = 0,
    max_quantity: int = 9999,
    period: BillingPeriod.LITERALS = BillingPeriod.MONTHLY,
) -> Price:

    if product is None:
        product = create_test_product(
            stripe_id='prod_1N8JnDBM2UVM1VfGDN6IsDDg1',
            is_subscription=True
        )
    return Price.objects.create(
        product=product,
        status=status,
        name=name,
        code=code,
        stripe_id=stripe_id,
        max_quantity=max_quantity,
        min_quantity=min_quantity,
        price_type=PriceType.RECURRING,
        price=price,
        trial_days=trial_days,
        billing_period=period,
        currency=currency
    )


def create_test_invoice_price(
    status: PriceStatus.LITERALS = PriceStatus.ACTIVE,
    name: str = 'Setup addon',
    code: str = 'addon',
    stripe_id: str = 'price_11wdsDBM2UVM1VfGDN6IsDDg',
    product: Optional[Product] = None,
    price: int = 1000,
    currency: str = 'usd',
    min_quantity: int = 0,
    max_quantity: int = 1
) -> Price:

    if product is None:
        product = create_test_product(is_subscription=False)
    return Price.objects.create(
        product=product,
        status=status,
        name=name,
        code=code,
        stripe_id=stripe_id,
        max_quantity=max_quantity,
        min_quantity=min_quantity,
        price_type=PriceType.ONE_TIME,
        price=price,
        currency=currency
    )
