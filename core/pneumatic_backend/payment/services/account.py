from datetime import datetime
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.contrib.auth import get_user_model

from pneumatic_backend.analytics.services import AnalyticService
from pneumatic_backend.accounts.services import AccountService
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
)
from pneumatic_backend.accounts.models import Account
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.analytics.mixins import BaseIdentifyMixin
from pneumatic_backend.payment.services.exceptions import (
    DowngradeException
)
from pneumatic_backend.payment.entities import (
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

        plan_changed = (
            details.plan_expiration != self.instance.plan_expiration
            or details.billing_period != self.instance.billing_period
            or details.billing_plan != self.instance.billing_plan
            or details.max_users != self.instance.max_users
            or details.quantity != self.instance.accounts_count
            or details.trial_start != self.instance.trial_start
            or details.trial_end != self.instance.trial_end
        )
        return plan_changed

    def _create(
        self,
        details: SubscriptionDetails,
        payment_card_provided: bool,
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
            'payment_card_provided': payment_card_provided,
            'tmp_subscription': False,
            'force_save': True
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
        payment_card_provided: bool,
    ):

        """ Create account subscription """

        plan_changed = self._plan_changed(details)
        if plan_changed:
            self._create(
                details=details,
                payment_card_provided=payment_card_provided,
            )

    def _update(
        self,
        details: SubscriptionDetails
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
            is_superuser=self.is_superuser
        )
        account_service.partial_update(
            billing_plan=details.billing_plan,
            billing_period=details.billing_period,
            plan_expiration=details.plan_expiration,
            max_users=details.max_users,
            payment_card_provided=True,
            tmp_subscription=False,
            trial_ended=True,
            force_save=True
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
            is_superuser=self.is_superuser
        )
        account_service.partial_update(
            plan_expiration=plan_expiration,
            trial_ended=True,
            force_save=True
        )

    def cancel(self, plan_expiration: datetime):

        """ Cancel a subscription it remains active and then
            expires at the end of the current bill cycle. """

        self.expired(plan_expiration)
        AnalyticService.subscription_canceled(self.user)

    def downgrade_to_free(self):

        """ Downgrade to free plan if current plan expired """

        # TODO the method does not decrease the number of active
        #  users according to the freemium limit

        account = self.instance
        if account.is_free:
            return
        if not account.is_expired:
            raise DowngradeException()
        with transaction.atomic():
            active_templates = account.active_templates
            if account.active_templates > account.max_active_templates:
                account.template_set.update(is_active=False)
                active_templates = 0
            else:
                active_paid_templates = account.get_active_paid_templates()
                count = active_paid_templates.count()
                active_paid_templates.update(is_active=False)
                active_templates -= count

            account_service = AccountService(
                instance=self.instance,
                user=self.user,
                auth_type=self.auth_type,
                is_superuser=self.is_superuser
            )
            data = {
                'billing_plan': BillingPlanType.FREEMIUM,
                'billing_period': None,
                'plan_expiration': None,
                'active_templates': active_templates,
                'max_users': settings.FREEMIUM_MAX_USERS,
                'trial_ended': True,
                'force_save': True
            }
            account_service.partial_update(**data)
            AnalyticService.subscription_canceled(self.user)

    def payment_card_provided(self, value: bool):
        account_service = AccountService(
            instance=self.instance,
            user=self.user,
            auth_type=self.auth_type,
            is_superuser=self.is_superuser,
        )
        account_service.partial_update(
            payment_card_provided=value,
            force_save=True
        )
        self.identify(self.user)
