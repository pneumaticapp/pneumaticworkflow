import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from pneumatic_backend.accounts.enums import (
    LeaseLevel,
    BillingPlanType,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.accounts.services import (
    AccountService
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
)
from pneumatic_backend.accounts.services.convert_account import (
    AccountLLConverter
)
from pneumatic_backend.payment.stripe.service import StripeService


pytestmark = pytest.mark.django_db
UserModel = get_user_model()


class TestAccountLLConverter:

    @pytest.mark.parametrize(
        'pair',
        (
            (LeaseLevel.TENANT, LeaseLevel.STANDARD),
            (LeaseLevel.TENANT, LeaseLevel.PARTNER),
            (LeaseLevel.STANDARD, LeaseLevel.TENANT),
            (LeaseLevel.STANDARD, LeaseLevel.PARTNER),
            (LeaseLevel.PARTNER, LeaseLevel.STANDARD),
            (LeaseLevel.PARTNER, LeaseLevel.TENANT),
        )
    )
    def test_handle__different_lease_level__ok(
        self,
        mocker,
        pair
    ):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        prev, new = pair
        method_mock = mocker.patch(
            'pneumatic_backend.accounts.services.convert_account'
            f'.AccountLLConverter._{prev}_to_{new}'
        )
        service = AccountLLConverter(
            user=user,
            instance=account
        )

        # act
        service.handle(prev=prev, new=new)

        # assert
        method_mock.assert_called_once()

    def test_handle__same_lease_level__not_call(
        self,
    ):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        prev = new = LeaseLevel.TENANT
        service = AccountLLConverter(
            user=user,
            instance=account
        )

        # act
        service.handle(prev=prev, new=new)

    def test_update_master_account_user_counts__ok(
        self,
        mocker,
    ):

        # arrange
        master_account = create_test_account(
            lease_level=LeaseLevel.PARTNER
        )
        master_account_owner = create_test_user(
            account=master_account,
            email='master@test.test'
        )
        tenant_account = create_test_account(
            name='tenant',
            lease_level=LeaseLevel.TENANT,
            master_account=master_account
        )
        tenant_user = create_test_user(account=tenant_account)

        init_mock = mocker.patch.object(
            AccountService,
            attribute='__init__',
            return_value=None
        )
        update_users_counts_mock = mocker.patch(
            'pneumatic_backend.accounts.services.AccountService.'
            'update_users_counts'
        )

        service = AccountLLConverter(
            user=tenant_user,
            instance=tenant_account
        )

        # act
        service._update_master_account_user_counts()

        # assert
        init_mock.assert_called_once_with(
            user=master_account_owner,
            instance=master_account
        )
        update_users_counts_mock.assert_called_once()

    def test_standard_to_tenant__premium__ok(
        self,
        mocker,
    ):

        # arrange
        logo_lg = 'https://another/image.jpg'
        logo_sm = 'https://another/image-2.jpg'
        plan = BillingPlanType.PREMIUM
        max_users = 100
        trial_start = timezone.now()
        plan_expiration = timezone.now() + timedelta(days=7)
        trial_ended = False
        payment_card_provided = False
        master_account = create_test_account(
            logo_lg=logo_lg,
            logo_sm=logo_sm,
            plan=plan,
            max_users=max_users,
            lease_level=LeaseLevel.PARTNER,
            plan_expiration=plan_expiration,
            trial_start=trial_start,
            trial_end=plan_expiration,
            trial_ended=trial_ended,
            payment_card_provided=payment_card_provided,
        )
        create_test_user(
            account=master_account,
            email='master@test.test'
        )
        tenant_account = create_test_account(
            name='tenant',
            plan=BillingPlanType.FREEMIUM,
            lease_level=LeaseLevel.TENANT,
            master_account=master_account
        )
        tenant_user = create_test_user(account=tenant_account)
        settings_mock = mocker.patch(
            'pneumatic_backend.accounts.services.convert_account.settings'
        )
        settings_mock.PROJECT_CONF = {'BILLING': True}
        update_master_account_user_counts_mock = mocker.patch(
            'pneumatic_backend.accounts.services.convert_account'
            '.AccountLLConverter._update_master_account_user_counts'
        )
        init_mock = mocker.patch.object(
            AccountService,
            attribute='__init__',
            return_value=None
        )
        partial_update_mock = mocker.patch(
            'pneumatic_backend.accounts.services.AccountService.partial_update'
        )
        increase_plan_users_mock = mocker.patch(
            'pneumatic_backend.payment.tasks.increase_plan_users.delay'
        )
        stripe_service_init_mock = mocker.patch.object(
            StripeService,
            attribute='__init__',
            return_value=None
        )
        create_off_session_subscription_mock = mocker.patch(
            'pneumatic_backend.payment.stripe.service.StripeService.'
            'create_off_session_subscription'
        )
        service = AccountLLConverter(
            user=tenant_user,
            instance=tenant_account
        )

        # act
        service._standard_to_tenant()

        # assert
        update_master_account_user_counts_mock.assert_called_once()
        init_mock.assert_called_once_with(
            user=tenant_user,
            instance=tenant_account
        )
        partial_update_mock.assert_called_once_with(
            logo_lg=logo_lg,
            logo_sm=logo_sm,
            max_users=max_users,
            billing_plan=plan,
            billing_period=master_account.billing_period,
            plan_expiration=plan_expiration,
            trial_start=trial_start,
            trial_end=plan_expiration,
            trial_ended=trial_ended,
            payment_card_provided=payment_card_provided,
            force_save=True
        )
        increase_plan_users_mock.assert_called_once_with(
            account_id=master_account.id,
            increment=False,
            is_superuser=True,
            auth_type=AuthTokenType.USER
        )
        stripe_service_init_mock.assert_not_called()
        create_off_session_subscription_mock.assert_not_called()

    def test_standard_to_tenant__unlimited__ok(
        self,
        mocker,
    ):

        # arrange
        logo_lg = 'https://another/image.jpg'
        logo_sm = 'https://another/image-2.jpg'
        plan = BillingPlanType.UNLIMITED
        max_users = 100
        trial_start = timezone.now() - timedelta(days=30)
        trial_end = timezone.now() - timedelta(days=23)
        plan_expiration = timezone.now() + timedelta(days=30)
        trial_ended = True
        payment_card_provided = True
        master_account = create_test_account(
            logo_lg=logo_lg,
            logo_sm=logo_sm,
            plan=plan,
            max_users=max_users,
            lease_level=LeaseLevel.PARTNER,
            plan_expiration=plan_expiration,
            trial_start=trial_start,
            trial_end=trial_end,
            trial_ended=trial_ended,
            payment_card_provided=payment_card_provided
        )
        create_test_user(
            account=master_account,
            email='admin@test.test',
            is_account_owner=False
        )
        master_account_owner = create_test_user(
            account=master_account,
            email='master@test.test',
            is_account_owner=True
        )
        tenant_account = create_test_account(
            name='tenant',
            plan=BillingPlanType.FREEMIUM,
            lease_level=LeaseLevel.TENANT,
            master_account=master_account
        )
        tenant_user = create_test_user(account=tenant_account)
        settings_mock = mocker.patch(
            'pneumatic_backend.accounts.services.convert_account.settings'
        )
        settings_mock.PROJECT_CONF = {'BILLING': True}
        update_master_account_user_counts_mock = mocker.patch(
            'pneumatic_backend.accounts.services.convert_account'
            '.AccountLLConverter._update_master_account_user_counts'
        )
        init_mock = mocker.patch.object(
            AccountService,
            attribute='__init__',
            return_value=None
        )
        partial_update_mock = mocker.patch(
            'pneumatic_backend.accounts.services.AccountService.partial_update'
        )
        increase_plan_users_mock = mocker.patch(
            'pneumatic_backend.payment.tasks.increase_plan_users.delay'
        )
        stripe_service_init_mock = mocker.patch.object(
            StripeService,
            attribute='__init__',
            return_value=None
        )
        create_off_session_subscription_mock = mocker.patch(
            'pneumatic_backend.payment.stripe.service.StripeService.'
            'create_off_session_subscription'
        )
        service = AccountLLConverter(
            user=tenant_user,
            instance=tenant_account
        )

        # act
        service._standard_to_tenant()

        # assert
        update_master_account_user_counts_mock.assert_called_once()
        init_mock.assert_called_once_with(
            user=tenant_user,
            instance=tenant_account
        )
        partial_update_mock.assert_called_once_with(
            logo_lg=logo_lg,
            logo_sm=logo_sm,
            max_users=max_users,
            billing_plan=plan,
            billing_period=master_account.billing_period,
            plan_expiration=plan_expiration,
            trial_start=trial_start,
            trial_end=trial_end,
            trial_ended=trial_ended,
            payment_card_provided=payment_card_provided,
            force_save=True
        )
        increase_plan_users_mock.assert_not_called()
        stripe_service_init_mock.assert_called_once_with(
            user=master_account_owner,
            subscription_account=tenant_account,
            is_superuser=True,
            auth_type=AuthTokenType.USER
        )
        create_off_session_subscription_mock.assert_called_once_with(
            products=[
                {
                    'code': 'unlimited_month',
                    'quantity': 1
                }
            ]
        )

    @pytest.mark.parametrize('plan', BillingPlanType.PAYMENT_PLANS)
    def test_standard_to_tenant__disable_billing__skip_call_stripe(
        self,
        plan,
        mocker,
    ):

        # arrange
        logo_lg = 'https://another/image.jpg'
        logo_sm = 'https://another/image-2.jpg'
        max_users = 100
        trial_start = timezone.now() - timedelta(days=30)
        trial_end = timezone.now() - timedelta(days=23)
        plan_expiration = timezone.now() + timedelta(days=30)
        trial_ended = True
        payment_card_provided = True
        master_account = create_test_account(
            logo_lg=logo_lg,
            logo_sm=logo_sm,
            plan=plan,
            max_users=max_users,
            lease_level=LeaseLevel.PARTNER,
            plan_expiration=plan_expiration,
            trial_start=trial_start,
            trial_end=trial_end,
            trial_ended=trial_ended,
            payment_card_provided=payment_card_provided
        )
        create_test_user(
            account=master_account,
            email='admin@test.test',
            is_account_owner=False
        )
        create_test_user(
            account=master_account,
            email='master@test.test',
            is_account_owner=True
        )
        tenant_account = create_test_account(
            name='tenant',
            plan=BillingPlanType.FREEMIUM,
            lease_level=LeaseLevel.TENANT,
            master_account=master_account
        )
        tenant_user = create_test_user(account=tenant_account)
        settings_mock = mocker.patch(
            'pneumatic_backend.accounts.services.convert_account.settings'
        )
        settings_mock.PROJECT_CONF = {'BILLING': False}
        update_master_account_user_counts_mock = mocker.patch(
            'pneumatic_backend.accounts.services.convert_account'
            '.AccountLLConverter._update_master_account_user_counts'
        )
        init_mock = mocker.patch.object(
            AccountService,
            attribute='__init__',
            return_value=None
        )
        partial_update_mock = mocker.patch(
            'pneumatic_backend.accounts.services.AccountService.partial_update'
        )
        increase_plan_users_mock = mocker.patch(
            'pneumatic_backend.payment.tasks.increase_plan_users.delay'
        )
        stripe_service_init_mock = mocker.patch.object(
            StripeService,
            attribute='__init__',
            return_value=None
        )
        create_off_session_subscription_mock = mocker.patch(
            'pneumatic_backend.payment.stripe.service.StripeService.'
            'create_off_session_subscription'
        )
        service = AccountLLConverter(
            user=tenant_user,
            instance=tenant_account
        )

        # act
        service._standard_to_tenant()

        # assert
        update_master_account_user_counts_mock.assert_called_once()
        init_mock.assert_called_once_with(
            user=tenant_user,
            instance=tenant_account
        )
        partial_update_mock.assert_called_once_with(
            logo_lg=logo_lg,
            logo_sm=logo_sm,
            max_users=max_users,
            billing_plan=plan,
            billing_period=master_account.billing_period,
            plan_expiration=plan_expiration,
            trial_start=trial_start,
            trial_end=trial_end,
            trial_ended=trial_ended,
            payment_card_provided=payment_card_provided,
            force_save=True
        )
        increase_plan_users_mock.assert_not_called()
        stripe_service_init_mock.assert_not_called()
        create_off_session_subscription_mock.assert_not_called()
