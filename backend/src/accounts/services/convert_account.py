from typing import Optional
from django.conf import settings
from django.contrib.auth import get_user_model
from src.accounts.enums import (
    LeaseLevel,
    BillingPlanType,
)
from src.accounts.models import Account
from src.accounts.services import AccountService
from src.authentication.enums import AuthTokenType
from src.payment.tasks import (
    increase_plan_users,
)
from src.payment.stripe.service import StripeService


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
        billing_enabled = (
            settings.PROJECT_CONF['BILLING'] and master_account.billing_sync
        )
        update_kwargs = {
            'logo_lg': master_account.logo_lg,
            'logo_sm': master_account.logo_sm,
            'max_users': master_account.max_users,
            'force_save': True
        }
        if master_account.billing_plan == BillingPlanType.PREMIUM:
            update_kwargs['max_users'] = master_account.max_users
            update_kwargs['billing_plan'] = master_account.billing_plan
            update_kwargs['billing_period'] = master_account.billing_period
            update_kwargs['plan_expiration'] = master_account.plan_expiration
            update_kwargs['trial_start'] = master_account.trial_start
            update_kwargs['trial_end'] = master_account.trial_end
            update_kwargs['trial_ended'] = master_account.trial_ended
        elif master_account.billing_plan in (
            BillingPlanType.FRACTIONALCOO,
            BillingPlanType.FREEMIUM
        ):
            update_kwargs['billing_plan'] = BillingPlanType.FREEMIUM
        elif master_account.billing_plan == BillingPlanType.UNLIMITED:
            if billing_enabled:
                # Need buy
                update_kwargs['billing_plan'] = None
            else:
                update_kwargs['max_users'] = master_account.max_users
                update_kwargs['billing_plan'] = master_account.billing_plan
                update_kwargs['billing_period'] = master_account.billing_period
                update_kwargs['plan_expiration'] = (
                    master_account.plan_expiration
                )
                update_kwargs['trial_start'] = master_account.trial_start
                update_kwargs['trial_end'] = master_account.trial_end
                update_kwargs['trial_ended'] = master_account.trial_ended

        service.partial_update(**update_kwargs)
        if (
            update_kwargs['billing_plan'] == BillingPlanType.PREMIUM
            and billing_enabled
        ):
            increase_plan_users.delay(
                account_id=master_account.id,
                increment=False,
                is_superuser=True,
                auth_type=AuthTokenType.USER
            )
        elif update_kwargs['billing_plan'] is None:
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
