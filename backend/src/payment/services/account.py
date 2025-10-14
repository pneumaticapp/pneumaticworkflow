from datetime import datetime
from django.utils import timezone
from django.contrib.auth import get_user_model

from src.analytics.services import AnalyticService
from src.accounts.services.account import AccountService
from src.accounts.enums import (
    BillingPlanType,
)
from src.accounts.models import Account
from src.authentication.enums import AuthTokenType
from src.analytics.mixins import BaseIdentifyMixin
from src.payment.entities import (
    SubscriptionDetails,
)
UserModel = get_user_model()


class AccountSubscriptionService(BaseIdentifyMixin):

    def __init__(
        self,
        instance: Account,
        user: UserModel,
        is_superuser: bool = False,
        auth_type: AuthTokenType.LITERALS = AuthTokenType.USER,
    ):
        self.instance = instance
        self.user = user
        self.is_superuser = is_superuser
        self.auth_type = auth_type

    def _plan_changed(self, details: SubscriptionDetails) -> bool:

        """ Skip updating if webhook already processes """

        return (
            details.plan_expiration != self.instance.plan_expiration
            or details.billing_period != self.instance.billing_period
            or details.billing_plan != self.instance.billing_plan
            or details.max_users != self.instance.max_users
            or details.quantity != self.instance.accounts_count
            or details.trial_start != self.instance.trial_start
            or details.trial_end != self.instance.trial_end
        )

    def _create(
        self,
        details: SubscriptionDetails,
    ):
        if self.instance.tmp_subscription:
            # The webhook is late and a temporary subscription is active now
            prev_trial_end = None
        else:
            prev_trial_end = self.instance.trial_end

        account_service = AccountService(
            instance=self.instance,
            user=self.user,
            auth_type=self.auth_type,
            is_superuser=self.is_superuser,
        )
        data = {
            'billing_plan': details.billing_plan,
            'billing_period': details.billing_period,
            'plan_expiration': details.plan_expiration,
            'max_users': details.max_users,
            'tmp_subscription': False,
            'force_save': True,
        }
        if not self.instance.trial_ended:
            data['trial_start'] = details.trial_start
            data['trial_end'] = details.trial_end
        account_service.partial_update(**data)

        AnalyticService.subscription_created(self.user)
        if not prev_trial_end and data.get('trial_end'):
            AnalyticService.trial_subscription_created(self.user)

        self.identify(self.user)

    def create(
        self,
        details: SubscriptionDetails,
    ):

        """ Create account subscription """

        plan_changed = self._plan_changed(details)
        if plan_changed:
            self._create(
                details=details,
            )

    def _update(
        self,
        details: SubscriptionDetails,
    ):
        convert_trial = (
            not self.instance.trial_ended
            and self.instance.billing_plan in BillingPlanType.PAYMENT_PLANS
            and details.billing_plan in BillingPlanType.PAYMENT_PLANS
            and self.instance.trial_end
            and self.instance.trial_end > timezone.now()
        )
        account_service = AccountService(
            instance=self.instance,
            user=self.user,
            auth_type=self.auth_type,
            is_superuser=self.is_superuser,
        )
        account_service.partial_update(
            billing_plan=details.billing_plan,
            billing_period=details.billing_period,
            plan_expiration=details.plan_expiration,
            max_users=details.max_users,
            tmp_subscription=False,
            trial_ended=True,
            force_save=True,
        )

        if convert_trial:
            AnalyticService.subscription_converted(self.user)
        else:
            AnalyticService.subscription_updated(self.user)
        self.identify(self.user)

    def update(
        self,
        details: SubscriptionDetails,
    ):

        """ Update existent account subscription """

        plan_changed = self._plan_changed(details)
        if plan_changed:
            self._update(details=details)

    def expired(self, plan_expiration: datetime):

        """ Subscription is expired immediately """

        account_service = AccountService(
            instance=self.instance,
            user=self.user,
            auth_type=self.auth_type,
            is_superuser=self.is_superuser,
        )
        account_service.partial_update(
            plan_expiration=plan_expiration,
            trial_ended=True,
            force_save=True,
        )

    def cancel(self, plan_expiration: datetime):

        """ Cancel a subscription it remains active and then
            expires at the end of the current bill cycle. """

        self.expired(plan_expiration)
        AnalyticService.subscription_canceled(self.user)
