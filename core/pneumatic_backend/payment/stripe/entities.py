from typing import Optional
from typing_extensions import TypedDict
from dataclasses import dataclass
from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.payment.models import Price


@dataclass
class PurchaseItem:

    price: Price
    quantity: int
    min_quantity: Optional[int]


class TokenSubscriptionData(TypedDict):

    max_users: int
    billing_plan: BillingPlanType.LITERALS
    trial_days: Optional[int]


class CardDetails(TypedDict):

    last4: str
    brand: str
