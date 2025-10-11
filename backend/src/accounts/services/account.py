# ruff: noqa: PLC0415
from typing import Optional
from django.conf import settings
from django.db import transaction
from django.contrib.auth import get_user_model
from src.accounts.models import (
    Account,
    AccountSignupData,
)
from src.analytics.mixins import BaseIdentifyMixin
from src.generics.mixins.services import ClsCacheMixin
from src.generics.base.service import BaseModelService
from src.accounts.services.exceptions import (
    AccountServiceException,
)
from src.accounts.serializers.accounts import (
    AccountCacheSerializer,
)
from src.analytics.tasks import identify_users
from src.accounts.enums import (
    LeaseLevel,
    UserStatus,
    BillingPlanType,
)
from src.utils.logging import (
    capture_sentry_message,
    SentryLogLevel,
)


UserModel = get_user_model()
configuration = settings.CONFIGURATION_CURRENT


class AccountService(
    BaseModelService,
    ClsCacheMixin,
    BaseIdentifyMixin,
):

    cache_timeout = 86400  # day
    cache_key_prefix = 'account'
    serializer_cls = AccountCacheSerializer

    def _create_tenant(
        self,
        master_account: Account,
        tenant_name: str,
    ) -> Account:

        billing_enabled = (
            settings.PROJECT_CONF['BILLING'] and master_account.billing_sync
        )
        account = Account(
            is_verified=True,
            name='Company name',
            billing_sync=master_account.billing_sync,
            master_account=master_account,
            tenant_name=tenant_name,
            lease_level=LeaseLevel.TENANT,
            logo_lg=master_account.logo_lg,
            logo_sm=master_account.logo_sm,
        )
        if master_account.billing_plan == BillingPlanType.PREMIUM:
            account.max_users = master_account.max_users
            account.billing_plan = master_account.billing_plan
            account.billing_period = master_account.billing_period
            account.plan_expiration = master_account.plan_expiration
            account.trial_start = master_account.trial_start
            account.trial_end = master_account.trial_end
            account.trial_ended = master_account.trial_ended
        elif master_account.billing_plan in (
            BillingPlanType.FRACTIONALCOO,
            BillingPlanType.FREEMIUM,
        ):
            account.billing_plan = BillingPlanType.FREEMIUM
        elif master_account.billing_plan == BillingPlanType.UNLIMITED:
            if billing_enabled:
                # Need buy
                account.billing_plan = None
            else:
                account.max_users = master_account.max_users
                account.billing_plan = master_account.billing_plan
                account.billing_period = master_account.billing_period
                account.plan_expiration = master_account.plan_expiration
                account.trial_start = master_account.trial_start
                account.trial_end = master_account.trial_end
                account.trial_ended = master_account.trial_ended
        account.save()
        return account

    def _create_instance(
        self,
        is_verified: bool = True,
        name: Optional[str] = None,
        tenant_name: Optional[str] = None,
        master_account: Optional[Account] = None,
        billing_sync: bool = True,
        **kwargs,
    ) -> Account:

        if master_account:
            self.instance = self._create_tenant(
                master_account=master_account,
                tenant_name=tenant_name,
            )
        else:
            billing_enabled = settings.PROJECT_CONF['BILLING'] and billing_sync
            self.instance = Account(
                is_verified=is_verified,
                name=name or 'Company name',
                billing_sync=billing_sync,
            )
            if not billing_enabled:
                self.instance.billing_plan = BillingPlanType.FREEMIUM
                self.instance.billing_sync = False
            self.instance.save()
        return self.instance

    def _create_related(
        self,
        utm_source: Optional[str] = None,
        utm_medium: Optional[str] = None,
        utm_campaign: Optional[str] = None,
        utm_term: Optional[str] = None,
        utm_content: Optional[str] = None,
        gclid: Optional[str] = None,
        **kwargs,
    ):
        AccountSignupData.objects.create(
            account=self.instance,
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
            utm_term=utm_term,
            utm_content=utm_content,
            gclid=gclid,
        )

    def inc_template_generations_count(self):
        self.partial_update(
            ai_templates_generations=(
                self.instance.ai_templates_generations + 1
            ),
            force_save=True,
        )

    def update_bucket_name(self, bucket_name):
        self.partial_update(
            bucket_name=bucket_name,
            force_save=True,
        )

    def update_users_counts(self):

        """ - If account is "tenant" then triggers the update of active users
            in the master account """

        if self.instance.is_tenant:
            self.partial_update(
                active_users=self.instance.users.active().count(),
                force_save=True,
            )
            service = AccountService(
                instance=self.instance.master_account,
                user=self.instance.master_account.get_owner(),
            )
            service.update_users_counts()
        else:
            self.partial_update(
                active_users=self.instance.users.active().count(),
                tenants_active_users=UserModel.objects.filter(
                    status=UserStatus.ACTIVE,
                    account__lease_level=LeaseLevel.TENANT,
                    account__master_account_id=self.instance.id,
                ).count(),
                force_save=True,
            )

        self._set_cache(
            key=self.instance.id,
            value=self.instance,
        )

    def _update_tenants(self):
        if self.instance.billing_plan == BillingPlanType.PREMIUM:
            self.instance.tenants.only_tenants().update(
                logo_lg=self.instance.logo_lg,
                logo_sm=self.instance.logo_sm,
                max_users=self.instance.max_users,
                billing_plan=self.instance.billing_plan,
                billing_period=self.instance.billing_period,
                plan_expiration=self.instance.plan_expiration,
                trial_start=self.instance.trial_start,
                trial_end=self.instance.trial_end,
                trial_ended=self.instance.trial_ended,
            )
        else:
            self.instance.tenants.only_tenants().update(
                logo_lg=self.instance.logo_lg,
                logo_sm=self.instance.logo_sm,
                billing_sync=self.instance.billing_sync,
            )

    def _identify_users(self):

        """ Identify account and tenant accounts users
            about new company logo (for email campaigns)"""

        if self.instance.is_subscribed:
            user_ids = (
                UserModel.objects.on_account(
                    self.instance.id,
                ).union(
                    UserModel.objects.filter(
                        account__master_account=self.instance,
                        account__lease_level=LeaseLevel.TENANT,
                    ),
                )
            ).order_by('id').only_ids()
        else:
            user_ids = self.instance.users.order_by('id').only_ids()
        identify_users.delay(user_ids=user_ids)

    def _update_stripe_account(
        self,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        **kwargs,
    ):
        if configuration not in {
            settings.CONFIGURATION_STAGING,
            settings.CONFIGURATION_PROD,
        }:
            return

        if (
            self.instance.stripe_id
            and not self.instance.is_tenant
            and (name or phone)
        ):
            from src.payment.stripe.service import StripeService
            from src.payment.stripe.exceptions import (
                StripeServiceException,
            )
            try:
                service = StripeService(
                    user=self.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                )
                service.update_customer()
            except StripeServiceException as ex:
                capture_sentry_message(
                    message='Stripe account update error',
                    level=SentryLogLevel.ERROR,
                    data={
                        'ex': str(ex),
                        'stripe_id': self.instance.stripe_id,
                        'user_id': self.user.id,
                        'name': name,
                        'phone': phone,
                    },
                )

    def partial_update(
        self,
        force_save=False,
        **update_kwargs,
    ) -> Account:

        with transaction.atomic():
            super().partial_update(
                **update_kwargs,
                force_save=force_save,
            )
            self._update_tenants()
            if settings.PROJECT_CONF['BILLING'] and self.instance.billing_sync:
                self._update_stripe_account(**update_kwargs)
            self._identify_users()
            self.group(user=self.user, account=self.instance)
        return self.instance

    @classmethod
    def get_cached_data(cls, account_id: int) -> dict:

        """ Returns account cached data """

        value = cls._get_cache(account_id)
        if value is None:
            try:
                account = Account.objects.get(id=account_id)
            except Account.DoesNotExist as ex:
                raise AccountServiceException(str(ex)) from ex
            else:
                value = cls._set_cache(key=account.id, value=account)
        return value
