from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.accounts.enums import BillingPlanType
from src.payment.enums import BillingPeriod


@dataclass
class SubscriptionDetails:

    max_users: int
    quantity: int
    billing_plan: BillingPlanType.LITERALS
    billing_period: BillingPeriod.LITERALS
    plan_expiration: Optional[datetime]
    trial_start: Optional[datetime]
    trial_end: Optional[datetime]
