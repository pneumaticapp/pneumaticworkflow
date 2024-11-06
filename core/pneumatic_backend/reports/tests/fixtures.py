from datetime import timedelta
from typing import Optional

from django.contrib.auth import get_user_model
from django.utils import timezone

from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.accounts.models import (
    Account,
    UserInvite,
    AccountSignupData,
)


UserModel = get_user_model()


def create_test_account(
    name: str = 'Test Company',
    plan: BillingPlanType = BillingPlanType.FREEMIUM,
    payment_card_provided: bool = True,
):
    account = Account.objects.create(
        name=name,
        billing_plan=plan,
        plan_expiration=(
            timezone.now() + timedelta(days=1)
            if plan in BillingPlanType.PAYMENT_PLANS else
            None
        ),
        payment_card_provided=payment_card_provided,
    )
    AccountSignupData.objects.create(account=account)
    return account


def create_test_user(
    email: str = 'test@pneumatic.app',
    is_admin: bool = True,
    is_account_owner: bool = False,
    account: Optional[Account] = None,
):
    if account is None:
        account = create_test_account()
    return UserModel.objects.create(
        account=account,
        email=email,
        phone='79999999999',
        is_admin=is_admin,
        is_account_owner=is_account_owner
    )


def create_invited_user(user, email='test1@pneumatic.app'):
    invited_user = UserModel.objects.create(
        account=user.account,
        email=email,
        phone='79999999999',
    )
    UserInvite.objects.create(
        email=email,
        account=user.account,
        invited_user=invited_user,
    )
    return invited_user
