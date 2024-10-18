from typing import Optional
from django.contrib.auth import get_user_model
from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.accounts.models import (
    Account,
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
        payment_card_provided=payment_card_provided,
    )
    AccountSignupData.objects.create(account=account)
    return account


def create_test_user(
    email: str = 'test@pneumatic.app',
    account: Optional[Account] = None,
    is_admin: bool = True,
    is_account_owner: bool = True
):
    account = account or create_test_account()
    return UserModel.objects.create(
        account=account,
        email=email,
        first_name='John',
        last_name='Doe',
        phone='79999999999',
        is_admin=is_admin,
        is_account_owner=is_account_owner
    )
