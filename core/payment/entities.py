from typing import Optional
from datetime import datetime
from dataclasses import dataclass
from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.payment.enums import BillingPeriod


@dataclass
class SubscriptionDetails:

    max_users: int
    quantity: int
    billing_plan: BillingPlanType.LITERALS
    billing_period: BillingPeriod.LITERALS
    plan_expiration: Optional[datetime]
    trial_start: Optional[datetime]
    trial_end: Optional[datetime]
