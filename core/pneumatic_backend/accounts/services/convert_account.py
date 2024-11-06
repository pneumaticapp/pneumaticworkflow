# pylint:disable=unnecessary-pass
from typing import Optional
from django.conf import settings
from django.contrib.auth import get_user_model
from pneumatic_backend.accounts.enums import (
    LeaseLevel,
    BillingPlanType,
)
from pneumatic_backend.accounts.models import Account
from pneumatic_backend.accounts.services import AccountService
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.payment.tasks import (
    increase_plan_users,
)
from pneumatic_backend.payment.stripe.service import StripeService


UserModel = get_user_model()


class AccountLLConverter:

    """ Account Lease level converter """

    def __init__(
        self,
        instance: Account,
        user: Optional[UserModel] = None,
    ):
        self.user = user
        self.instance = instance

    def _update_master_account_user_counts(self):

        master_account = self.instance.master_account
        service = AccountService(
            instance=master_account,
            user=master_account.get_owner()
        )
        service.update_users_counts()

    def _standard_to_partner(self):

        """ Set shared partner properties to tenants.
            Implemented in AccountService partial_update method """

        pass

    def _standard_to_tenant(self):

        """ Set shared properties from partner
            If account have subscription - it ignored.
            if you need cancel prev subscription - this is done manually """

        self._update_master_account_user_counts()
        service = AccountService(
            instance=self.instance,
            user=self.user
        )
        master_account = self.instance.master_account
        service.partial_update(
            logo_lg=master_account.logo_lg,
            logo_sm=master_account.logo_sm,
            max_users=master_account.max_users,
            billing_plan=master_account.billing_plan,
            billing_period=master_account.billing_period,
            plan_expiration=master_account.plan_expiration,
            trial_start=master_account.trial_start,
            trial_end=master_account.trial_end,
            trial_ended=master_account.trial_ended,
            payment_card_provided=master_account.payment_card_provided,
            force_save=True
        )
        if master_account.billing_sync and settings.PROJECT_CONF['BILLING']:
            if master_account.billing_plan == BillingPlanType.PREMIUM:
                increase_plan_users.delay(
                    account_id=master_account.id,
                    increment=False,
                    is_superuser=True,
                    auth_type=AuthTokenType.USER
                )
            else:
                stripe_service = StripeService(
                    user=master_account.get_owner(),
                    subscription_account=self.instance,
                    is_superuser=True,
                    auth_type=AuthTokenType.USER
                )
                stripe_service.create_off_session_subscription(
                    products=[
                        {
                            'code': 'unlimited_month',
                            'quantity': 1
                        }
                    ]
                )

    def _tenant_to_partner(self):
        pass

    def _tenant_to_standard(self):
        pass

    def _partner_to_standard(self):
        pass

    def _partner_to_tenant(self):
        pass

    def handle(
        self,
        prev: LeaseLevel.LITERALS,
        new: LeaseLevel.LITERALS
    ):

        if prev != new:
            getattr(self, f'_{prev}_to_{new}')()
