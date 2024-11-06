import pytest
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from pneumatic_backend.authentication.enums import (
    AuthTokenType
)
from pneumatic_backend.accounts.services.exceptions import (
    AccountServiceException
)
from pneumatic_backend.payment.enums import BillingPeriod
from pneumatic_backend.accounts.enums import (
    LeaseLevel,
    UserStatus,
    BillingPlanType,
)
from pneumatic_backend.accounts.services import (
    AccountService
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_guest,
    create_test_user,
    create_invited_user,
    create_test_account,
)
from pneumatic_backend.payment.stripe.service import StripeService
from pneumatic_backend.payment.stripe.exceptions import StripeServiceException


pytestmark = pytest.mark.django_db
UserModel = get_user_model()


def test_create_instance__tenant__premium__ok():

    # arrange
    trial_start = timezone.now() - timedelta(days=30)
    trial_end = timezone.now() - timedelta(days=23)
    trial_ended = True
    payment_card_provided = True
    master_account = create_test_account(
        logo_lg='https://some.logo/image1.png',
        logo_sm='https://some.logo/image2.png',
        max_users=10,
        plan=BillingPlanType.PREMIUM,
        period=BillingPeriod.WEEKLY,
        trial_ended=trial_ended,
        trial_end=trial_end,
        trial_start=trial_start,
        payment_card_provided=payment_card_provided,
        billing_sync=False
    )
    tenant_name = 'test tenant name'
    service = AccountService()

    # act
    tenant_account = service._create_instance(
        tenant_name=tenant_name,
        master_account=master_account
    )

    # assert
    assert tenant_account.is_verified is True
    assert tenant_account.name == 'Company name'
    assert tenant_account.master_account == master_account
    assert tenant_account.tenant_name == tenant_name
    assert tenant_account.lease_level == LeaseLevel.TENANT
    assert tenant_account.logo_lg == master_account.logo_lg
    assert tenant_account.logo_sm == master_account.logo_sm
    assert tenant_account.max_users == master_account.max_users
    assert tenant_account.billing_plan == master_account.billing_plan
    assert tenant_account.billing_period == master_account.billing_period
    assert tenant_account.billing_sync == master_account.billing_sync
    assert tenant_account.plan_expiration == master_account.plan_expiration
    assert tenant_account.trial_start == trial_start
    assert tenant_account.trial_end == trial_end
    assert tenant_account.trial_ended == trial_ended
    assert tenant_account.payment_card_provided == (
        master_account.payment_card_provided
    )


def test_create_instance__tenant__disable_billing_sync__ok():

    # arrange
    trial_start = timezone.now() - timedelta(days=30)
    trial_end = timezone.now() - timedelta(days=23)
    trial_ended = True
    payment_card_provided = True
    master_account = create_test_account(
        logo_lg='https://some.logo/image1.png',
        logo_sm='https://some.logo/image2.png',
        max_users=10,
        plan=BillingPlanType.UNLIMITED,
        period=BillingPeriod.MONTHLY,
        trial_ended=trial_ended,
        trial_end=trial_end,
        trial_start=trial_start,
        payment_card_provided=payment_card_provided,
        billing_sync=False
    )
    tenant_name = 'test tenant name'
    service = AccountService()

    # act
    tenant_account = service._create_instance(
        tenant_name=tenant_name,
        master_account=master_account
    )

    # assert
    assert tenant_account.is_verified is True
    assert tenant_account.name == 'Company name'
    assert tenant_account.master_account == master_account
    assert tenant_account.tenant_name == tenant_name
    assert tenant_account.lease_level == LeaseLevel.TENANT
    assert tenant_account.logo_lg == master_account.logo_lg
    assert tenant_account.logo_sm == master_account.logo_sm
    assert tenant_account.max_users == master_account.max_users
    assert tenant_account.billing_plan == master_account.billing_plan
    assert tenant_account.billing_period == master_account.billing_period
    assert tenant_account.billing_sync is False
    assert tenant_account.plan_expiration == master_account.plan_expiration
    assert tenant_account.trial_start == trial_start
    assert tenant_account.trial_end == trial_end
    assert tenant_account.trial_ended == trial_ended
    assert tenant_account.payment_card_provided == (
        master_account.payment_card_provided
    )


def test_create_instance__tenant__unlimited__ok():

    # arrange

    trial_start = timezone.now() - timedelta(days=30)
    trial_end = timezone.now() - timedelta(days=23)
    trial_ended = True
    payment_card_provided = True
    master_account = create_test_account(
        logo_lg='https://some.logo/image1.png',
        logo_sm='https://some.logo/image2.png',
        max_users=10,
        plan=BillingPlanType.FRACTIONALCOO,
        period=BillingPeriod.WEEKLY,
        trial_ended=trial_ended,
        trial_end=trial_end,
        trial_start=trial_start,
        payment_card_provided=payment_card_provided,
    )
    tenant_name = 'test tenant name'
    service = AccountService()

    # act
    tenant_account = service._create_instance(
        tenant_name=tenant_name,
        master_account=master_account
    )

    # assert
    assert tenant_account.is_verified is True
    assert tenant_account.name == 'Company name'
    assert tenant_account.master_account == master_account
    assert tenant_account.tenant_name == tenant_name
    assert tenant_account.lease_level == LeaseLevel.TENANT
    assert tenant_account.logo_lg == master_account.logo_lg
    assert tenant_account.logo_sm == master_account.logo_sm

    assert tenant_account.max_users == settings.FREEMIUM_MAX_USERS
    assert tenant_account.billing_sync == master_account.billing_sync
    assert tenant_account.billing_plan == BillingPlanType.FREEMIUM
    assert tenant_account.billing_period is None
    assert tenant_account.plan_expiration is None
    assert tenant_account.trial_start is None
    assert tenant_account.trial_end is None
    assert tenant_account.trial_ended is False
    assert tenant_account.payment_card_provided == (
        master_account.payment_card_provided
    )


def test_create_instance__default_name__ok():

    # arrange
    service = AccountService()

    # act
    account = service._create_instance(
        is_verified=False,
        name=None,
    )

    # assert
    assert account.is_verified is False
    assert account.name == 'Company name'
    assert account.master_account is None
    assert account.payment_card_provided is False


def test_create_instance__disable_billing_sync__ok():

    # arrange
    service = AccountService()

    # act
    account = service._create_instance(
        billing_sync=False,
    )

    # assert
    assert account.billing_sync is False


def test_create_related__not_utm__ok():

    # arrange
    account = create_test_account()
    account.accountsignupdata_set.first().delete()
    service = AccountService(instance=account)

    # act
    service._create_related()

    # assert
    signup_data = account.accountsignupdata_set.first()
    assert signup_data.utm_source is None
    assert signup_data.utm_medium is None
    assert signup_data.utm_campaign is None
    assert signup_data.utm_term is None
    assert signup_data.utm_content is None
    assert signup_data.gclid is None


def test_create_related__all_fields__ok():

    # arrange
    account = create_test_account()
    account.accountsignupdata_set.first().delete()
    utm_source = 'some_utm_source'
    utm_medium = 'some_utm_medium'
    utm_campaign = 'some_utm_campaign'
    utm_term = 'some_utm_term'
    utm_content = 'some_utm_content'
    gclid = 'some_gclid'

    service = AccountService(instance=account)

    # act
    service._create_related(
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
        utm_term=utm_term,
        utm_content=utm_content,
        gclid=gclid,
    )

    # assert
    signup_data = account.accountsignupdata_set.first()
    assert signup_data.utm_source == utm_source
    assert signup_data.utm_medium == utm_medium
    assert signup_data.utm_campaign == utm_campaign
    assert signup_data.utm_term == utm_term
    assert signup_data.utm_content == utm_content
    assert signup_data.gclid == gclid


def test_get_cached_data__ok(mocker):

    # arrange
    account = create_test_account()
    account.active_users = 2
    account.tenants_active_users = 3
    account.save(update_fields=['active_users', 'tenants_active_users'])

    get_cache_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account'
        '.AccountService._get_cache',
        return_value=None
    )

    # act
    result = AccountService.get_cached_data(account.id)

    # assert
    assert result == {
        'active_users': 2,
        'tenants_active_users': 3
    }
    get_cache_mock.assert_called_once_with(account.id)


def test_get_cached_data__from_cache__ok(mocker):

    # arrange
    account_id = 456
    account_cache = {
        'active_users': 2,
        'tenants_active_users': 2
    }
    get_cache_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account'
        '.AccountService._get_cache',
        return_value=account_cache
    )

    # act
    result = AccountService.get_cached_data(account_id)

    # assert
    assert result == account_cache
    get_cache_mock.assert_called_once_with(account_id)


def test_get_cached_data__set_account_cache__ok(mocker):

    # arrange
    account = create_test_account()
    account.active_users = 2
    account.save(update_fields=['active_users'])
    account_cache = {'active_users': 2}
    get_cache_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account'
        '.AccountService._get_cache',
        return_value=None
    )
    set_cache_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account'
        '.AccountService._set_cache',
        return_value=account_cache
    )

    # act
    result = AccountService.get_cached_data(account.id)

    # assert
    assert result == account_cache
    get_cache_mock.assert_called_once_with(account.id)
    set_cache_mock.assert_called_once_with(
        key=account.id,
        value=account
    )


def test_get_cached_data__account_not_exists__raise_exception(mocker):
    # arrange
    account_id = -1
    get_cache_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account'
        '.AccountService._get_cache',
        return_value=None
    )
    set_cache_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account'
        '.AccountService._set_cache'
    )

    # act
    with pytest.raises(AccountServiceException) as ex:
        AccountService.get_cached_data(account_id)

    # assert
    get_cache_mock.assert_called_once_with(account_id)
    set_cache_mock.assert_not_called()
    assert ex.value.message == 'Account matching query does not exist.'


def test_update_users_counts__standard__ok(mocker):

    # arrange
    account = create_test_account(lease_level=LeaseLevel.STANDARD)
    user = create_test_user(account=account)
    create_invited_user(user)
    create_test_user(
        account=account,
        email='test@test.test',
        status=UserStatus.INACTIVE
    )
    create_test_guest(account=account)

    # First tenant
    tenant_account_1 = create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=account
    )
    tenant_account_owner_1 = create_test_user(
        account=tenant_account_1,
        email='tenant_owner@test.test'
    )
    create_invited_user(tenant_account_owner_1)
    create_test_user(
        account=tenant_account_1,
        email='inactive@test.test',
        status=UserStatus.INACTIVE
    )
    create_test_guest(account=tenant_account_1)

    # Second tenant
    create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=account
    )
    create_test_user(
        account=tenant_account_1,
        email='tenant_owner2@test.test'
    )

    set_cache_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account'
        '.AccountService._set_cache'
    )
    partial_update_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account'
        '.AccountService.partial_update'
    )
    service = AccountService(
        instance=account,
        user=user
    )

    # act
    service.update_users_counts()

    # assert
    account.refresh_from_db()
    set_cache_mock.assert_called_once_with(
        key=account.id,
        value=account
    )
    partial_update_mock.assert_called_once_with(
        active_users=1,
        tenants_active_users=2,
        force_save=True
    )


def test_update_users_counts__tenant__ok(mocker):

    # arrange
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED
    )
    create_test_user(account=account)
    tenant_account = create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=account
    )
    tenant_account_owner = create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    create_invited_user(tenant_account_owner)
    create_test_user(
        account=tenant_account,
        email='inactive@test.test',
        status=UserStatus.INACTIVE
    )
    create_test_guest(account=tenant_account)

    set_cache_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account'
        '.AccountService._set_cache'
    )
    service = AccountService(
        instance=tenant_account,
        user=tenant_account_owner
    )

    # act
    service.update_users_counts()

    # assert
    account.refresh_from_db()
    assert set_cache_mock.call_count == 2
    set_cache_mock.assert_has_calls([
        mocker.call(
            key=account.id,
            value=account
        ),
        mocker.call(
            key=tenant_account.id,
            value=tenant_account
        )
    ])
    tenant_account.refresh_from_db()
    assert tenant_account.active_users == 1
    account.refresh_from_db()
    assert account.active_users == 1
    assert account.tenants_active_users == 1


def test_update_users_counts__master__ok(mocker):

    # arrange
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED
    )
    account_owner = create_test_user(account=account)
    create_invited_user(account_owner)
    create_test_user(
        account=account,
        email='inactive1@test.test',
        status=UserStatus.INACTIVE
    )
    create_test_guest(
        account=account,
        email='guest1@test.test'
    )

    # First tenant
    tenant_account_1 = create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=account
    )
    tenant_account_owner_1 = create_test_user(
        account=tenant_account_1,
        email='tenant_owner@test.test'
    )
    create_invited_user(tenant_account_owner_1)
    create_test_user(
        account=tenant_account_1,
        email='inactive@test.test',
        status=UserStatus.INACTIVE
    )
    create_test_guest(account=tenant_account_1)

    # Second tenant
    create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=account
    )
    create_test_user(
        account=tenant_account_1,
        email='tenant_owner2@test.test'
    )

    set_cache_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account'
        '.AccountService._set_cache'
    )
    service = AccountService(
        instance=account,
        user=account_owner
    )

    # act
    service.update_users_counts()

    # assert
    account.refresh_from_db()
    set_cache_mock.assert_called_once_with(
        key=account.id,
        value=account
    )
    account.refresh_from_db()
    assert account.active_users == 1
    assert account.tenants_active_users == 2


def test_partial_update__ok(mocker):

    # arrange
    account = create_test_account(
        lease_level=LeaseLevel.STANDARD,
        billing_sync=True
    )
    user = create_test_user(account=account)
    logo_lg = 'http://site.com/logo_lg.img'
    logo_sm = 'http://site.com/logo_sm.img'
    name = 'New account name'
    service = AccountService(
        instance=account,
        user=user,
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    group_mock = mocker.patch(
        'pneumatic_backend.analytics.mixins.BaseIdentifyMixin.group'
    )
    update_stripe_account_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account.'
        'AccountService._update_stripe_account'
    )
    update_tenants_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account.'
        'AccountService._update_tenants'
    )
    identify_users_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account.'
        'AccountService._identify_users'
    )

    # act
    result = service.partial_update(
        name=name,
        logo_lg=logo_lg,
        logo_sm=logo_sm,
        force_save=True
    )

    # assert
    account.refresh_from_db()
    assert result.id == account.id
    assert account.logo_lg == logo_lg
    assert account.logo_sm == logo_sm
    assert account.name == name
    update_tenants_mock.assert_called_once()
    update_stripe_account_mock.assert_called_once_with(
        name=name,
        logo_lg=logo_lg,
        logo_sm=logo_sm,
    )
    identify_users_mock.assert_called_once()
    group_mock.assert_called_once_with(user=user, account=account)


def test_partial_update__disabled_billing_sync__ok(mocker):

    # arrange
    account = create_test_account(
        lease_level=LeaseLevel.STANDARD,
        billing_sync=False
    )
    user = create_test_user(account=account)
    logo_lg = 'http://site.com/logo_lg.img'
    logo_sm = 'http://site.com/logo_sm.img'
    name = 'New account name'
    service = AccountService(
        instance=account,
        user=user,
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    group_mock = mocker.patch(
        'pneumatic_backend.analytics.mixins.BaseIdentifyMixin.group'
    )
    update_stripe_account_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account.'
        'AccountService._update_stripe_account'
    )
    update_tenants_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account.'
        'AccountService._update_tenants'
    )
    identify_users_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account.'
        'AccountService._identify_users'
    )

    # act
    result = service.partial_update(
        name=name,
        logo_lg=logo_lg,
        logo_sm=logo_sm,
        force_save=True
    )

    # assert
    account.refresh_from_db()
    assert result.id == account.id
    assert account.logo_lg == logo_lg
    assert account.logo_sm == logo_sm
    assert account.name == name
    update_tenants_mock.assert_called_once()
    update_stripe_account_mock.assert_not_called()
    identify_users_mock.assert_called_once()
    group_mock.assert_called_once_with(user=user, account=account)


def test_partial_update__disabled_billing__ok(mocker):

    # arrange
    account = create_test_account(lease_level=LeaseLevel.STANDARD)
    user = create_test_user(account=account)
    logo_lg = 'http://site.com/logo_lg.img'
    logo_sm = 'http://site.com/logo_sm.img'
    name = 'New account name'
    service = AccountService(
        instance=account,
        user=user,
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': False}
    group_mock = mocker.patch(
        'pneumatic_backend.analytics.mixins.BaseIdentifyMixin.group'
    )
    update_stripe_account_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account.'
        'AccountService._update_stripe_account'
    )
    update_tenants_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account.'
        'AccountService._update_tenants'
    )
    identify_users_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account.'
        'AccountService._identify_users'
    )

    # act
    result = service.partial_update(
        name=name,
        logo_lg=logo_lg,
        logo_sm=logo_sm,
        force_save=True
    )

    # assert
    account.refresh_from_db()
    assert result.id == account.id
    assert account.logo_lg == logo_lg
    assert account.logo_sm == logo_sm
    assert account.name == name
    update_tenants_mock.assert_called_once()
    update_stripe_account_mock.assert_not_called()
    identify_users_mock.assert_called_once()
    group_mock.assert_called_once_with(user=user, account=account)


def test_update_tenants__premium__ok():

    # arrange
    user = create_test_user()
    max_users = 50
    billing_period = BillingPeriod.DAILY
    plan = BillingPlanType.PREMIUM
    plan_expiration = timezone.now() + timedelta(days=1500)
    trial_start = timezone.now() - timedelta(days=30)
    trial_end = timezone.now() - timedelta(days=23)
    trial_ended = True
    payment_card_provided = True
    logo_lg = 'http://site.com/logo_lg.img'
    logo_sm = 'http://site.com/logo_sm.img'
    account = create_test_account(
        logo_lg=logo_lg,
        logo_sm=logo_sm,
        plan_expiration=plan_expiration,
        max_users=max_users,
        period=billing_period,
        plan=plan,
        trial_ended=trial_ended,
        trial_end=trial_end,
        trial_start=trial_start,
        payment_card_provided=payment_card_provided,
    )
    tenant_account = create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=account
    )
    not_tenant_account_1 = create_test_account(
        lease_level=LeaseLevel.STANDARD,
        master_account=account
    )
    not_tenant_account_2 = create_test_account(
        lease_level=LeaseLevel.TENANT,
    )
    not_tenant_account_3 = create_test_account()
    not_tenant_account_4 = create_test_account(
        lease_level=LeaseLevel.PARTNER,
        master_account=account
    )
    service = AccountService(
        instance=account,
        user=user
    )

    # act
    service._update_tenants()

    # assert
    tenant_account.refresh_from_db()
    assert tenant_account.logo_lg == logo_lg
    assert tenant_account.logo_sm == logo_sm
    assert tenant_account.billing_plan == plan
    assert tenant_account.plan_expiration == plan_expiration
    assert tenant_account.billing_period == billing_period
    assert tenant_account.trial_start == trial_start
    assert tenant_account.trial_end == trial_end
    assert tenant_account.trial_ended == trial_ended
    assert tenant_account.max_users == max_users
    assert tenant_account.payment_card_provided is True

    not_tenant_account_1.refresh_from_db()
    assert not_tenant_account_1.logo_lg is None
    assert not_tenant_account_1.logo_sm is None

    not_tenant_account_2.refresh_from_db()
    assert not_tenant_account_2.logo_lg is None
    assert not_tenant_account_2.logo_sm is None

    not_tenant_account_3.refresh_from_db()
    assert not_tenant_account_3.logo_lg is None
    assert not_tenant_account_3.logo_sm is None

    not_tenant_account_4.refresh_from_db()
    assert not_tenant_account_4.logo_lg is None
    assert not_tenant_account_4.logo_sm is None


@pytest.mark.parametrize(
    'plan',
    (BillingPlanType.UNLIMITED, BillingPlanType.FRACTIONALCOO)
)
def test_update_tenants__unlimited__ok(plan):

    # arrange
    max_users = 50
    billing_period = BillingPeriod.DAILY
    plan_expiration = timezone.now() + timedelta(days=1500)
    trial_start = timezone.now() - timedelta(days=30)
    trial_end = timezone.now() - timedelta(days=23)
    trial_ended = True
    payment_card_provided = True
    logo_lg = 'http://site.com/logo_lg.img'
    logo_sm = 'http://site.com/logo_sm.img'
    master_account = create_test_account(
        logo_lg=logo_lg,
        logo_sm=logo_sm,
        plan_expiration=plan_expiration,
        max_users=max_users,
        period=billing_period,
        plan=plan,
        trial_ended=trial_ended,
        trial_end=trial_end,
        trial_start=trial_start,
        payment_card_provided=payment_card_provided,
    )
    user = create_test_user(account=master_account)
    tenant_account = create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=master_account,

    )
    not_tenant_account_1 = create_test_account(
        lease_level=LeaseLevel.STANDARD,
        master_account=master_account
    )
    not_tenant_account_2 = create_test_account(
        lease_level=LeaseLevel.TENANT,
    )
    not_tenant_account_3 = create_test_account()
    not_tenant_account_4 = create_test_account(
        lease_level=LeaseLevel.PARTNER,
        master_account=master_account
    )
    service = AccountService(
        instance=master_account,
        user=user
    )

    # act
    service._update_tenants()

    # assert
    tenant_account.refresh_from_db()
    assert tenant_account.logo_lg == logo_lg
    assert tenant_account.logo_sm == logo_sm
    assert tenant_account.payment_card_provided is True

    assert tenant_account.billing_plan == BillingPlanType.FREEMIUM
    assert tenant_account.max_users == settings.FREEMIUM_MAX_USERS
    assert tenant_account.billing_period is None
    assert tenant_account.plan_expiration is None
    assert tenant_account.trial_start is None
    assert tenant_account.trial_end is None
    assert tenant_account.trial_ended is False

    not_tenant_account_1.refresh_from_db()
    assert not_tenant_account_1.logo_lg is None
    assert not_tenant_account_1.logo_sm is None

    not_tenant_account_2.refresh_from_db()
    assert not_tenant_account_2.logo_lg is None
    assert not_tenant_account_2.logo_sm is None

    not_tenant_account_3.refresh_from_db()
    assert not_tenant_account_3.logo_lg is None
    assert not_tenant_account_3.logo_sm is None

    not_tenant_account_4.refresh_from_db()
    assert not_tenant_account_4.logo_lg is None
    assert not_tenant_account_4.logo_sm is None


def test_identify_users__premium__ok(mocker):

    # arrange
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() + timedelta(days=1),
        lease_level=LeaseLevel.STANDARD
    )
    user = create_test_user(account=account, is_account_owner=True)
    invited_user = create_test_user(
        account=account,
        email='invited@t.t',
        status=UserStatus.INVITED,
        is_account_owner=False
    )
    create_test_user(
        account=account,
        email='inactive@t.t',
        status=UserStatus.INACTIVE,
        is_account_owner=False
    )
    create_test_guest(
        email='guest@t.t',
        account=account
    )

    another_account = create_test_account(
        lease_level=LeaseLevel.STANDARD,
        master_account=account
    )
    create_test_user(
        account=another_account,
        email='another_user@test.test',
        is_account_owner=True
    )
    create_test_guest(
        email='another_guest@t.t',
        account=another_account
    )

    # tenant accounts
    tenant_account = create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=account
    )
    tenant_user = create_test_user(
        account=tenant_account,
        email='tenant_user@t.t',
        is_account_owner=True,
    )
    tenant_invited_user = create_test_user(
        account=tenant_account,
        email='tenant_invited@t.t',
        status=UserStatus.INVITED,
        is_account_owner=False,
    )
    create_test_user(
        account=tenant_account,
        email='inactive_tenant@t.t',
        status=UserStatus.INACTIVE,
        is_account_owner=False,
    )
    create_test_guest(
        email='guest_tenant@t.t',
        account=tenant_account
    )

    identify_users_mock = mocker.patch(
        'pneumatic_backend.analytics.tasks.identify_users.delay'
    )
    service = AccountService(
        instance=account,
        user=user
    )

    # act
    service._identify_users()

    # assert
    identify_users_mock.assert_called_once_with(
        user_ids=(
            user.id, invited_user.id,
            tenant_user.id, tenant_invited_user.id
        )
    )


def test_identify_users__lease_level_partner__ok(mocker):

    # arrange
    account = create_test_account(
        lease_level=LeaseLevel.PARTNER,
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() + timedelta(days=1)
    )
    user = create_test_user(account=account, is_account_owner=True)
    invited_user = create_test_user(
        account=account,
        email='invited@t.t',
        status=UserStatus.INVITED,
        is_account_owner=False,
    )
    create_test_user(
        account=account,
        email='inactive@t.t',
        status=UserStatus.INACTIVE,
        is_account_owner=False,
    )
    create_test_guest(
        email='guest@t.t',
        account=account
    )

    tenant_account = create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=account
    )
    tenant_user = create_test_user(
        account=tenant_account,
        email='tenant_user@t.t',
        is_account_owner=True,
    )
    tenant_invited_user = create_test_user(
        account=tenant_account,
        email='tenant_invited@t.t',
        status=UserStatus.INVITED,
        is_account_owner=False,
    )
    create_test_user(
        account=tenant_account,
        email='inactive_tenant@t.t',
        status=UserStatus.INACTIVE,
        is_account_owner=False,
    )
    create_test_guest(
        email='guest_tenant@t.t',
        account=tenant_account
    )

    identify_users_mock = mocker.patch(
        'pneumatic_backend.analytics.tasks.identify_users.delay'
    )
    service = AccountService(
        instance=account,
        user=user
    )

    # act
    service._identify_users()

    # assert
    identify_users_mock.assert_called_once_with(
        user_ids=(
            user.id, invited_user.id,
            tenant_user.id, tenant_invited_user.id
        )
    )


def test_identify_users__expired_subscription__not_identify_tenants(mocker):
    # arrange
    account = create_test_account(
        lease_level=LeaseLevel.STANDARD,
        plan=BillingPlanType.PREMIUM,
        plan_expiration=timezone.now() - timedelta(hours=1)
    )
    user = create_test_user(account=account, is_account_owner=True)
    invited_user = create_test_user(
        account=account,
        email='invited@t.t',
        status=UserStatus.INVITED,
        is_account_owner=False
    )
    create_test_user(
        account=account,
        email='inactive@t.t',
        status=UserStatus.INACTIVE,
        is_account_owner=False
    )
    create_test_guest(
        email='guest@t.t',
        account=account
    )

    another_account = create_test_account(
        lease_level=LeaseLevel.STANDARD,
        master_account=account
    )
    create_test_user(
        account=another_account,
        email='another_user@test.test',
        is_account_owner=True
    )
    create_test_guest(
        account=another_account,
        email='another_guest@t.t',
    )

    # tenant accounts
    tenant_account = create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=account
    )
    create_test_user(
        account=tenant_account,
        email='tenant_user@t.t',
        is_account_owner=True
    )

    identify_users_mock = mocker.patch(
        'pneumatic_backend.analytics.tasks.identify_users.delay'
    )
    service = AccountService(
        instance=account,
        user=user
    )

    # act
    service._identify_users()

    # assert
    identify_users_mock.assert_called_once_with(
        user_ids=(user.id, invited_user.id)
    )


def test_identify_users__free_plan__not_identify_tenants(mocker):
    # arrange
    account = create_test_account(
        lease_level=LeaseLevel.STANDARD,
        plan=BillingPlanType.FREEMIUM,
    )
    user = create_test_user(
        account=account,
        is_account_owner=True
    )
    invited_user = create_test_user(
        account=account,
        email='invited@t.t',
        status=UserStatus.INVITED,
        is_account_owner=False
    )
    create_test_user(
        account=account,
        email='inactive@t.t',
        status=UserStatus.INACTIVE,
        is_account_owner=False
    )
    create_test_guest(
        email='guest@t.t',
        account=account
    )

    another_account = create_test_account(
        lease_level=LeaseLevel.STANDARD,
        master_account=account
    )
    create_test_user(
        account=another_account,
        email='another_user@test.test',
        is_account_owner=True
    )
    create_test_guest(
        email='another_guest@t.t',
        account=another_account
    )

    # tenant accounts
    tenant_account = create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=account
    )
    create_test_user(
        account=tenant_account,
        email='tenant_user@t.t',
        is_account_owner=True
    )

    identify_users_mock = mocker.patch(
        'pneumatic_backend.analytics.tasks.identify_users.delay'
    )
    service = AccountService(
        instance=account,
        user=user
    )

    # act
    service._identify_users()

    # assert
    identify_users_mock.assert_called_once_with(
        user_ids=(user.id, invited_user.id)
    )


def test_update_stripe_account__name_changed__ok(mocker):

    # arrange
    account = create_test_account(stripe_id='u123asd')
    user = create_test_user(account=account)
    name = 'New account name'
    is_superuser = True
    auth_type = AuthTokenType.API
    mocker.patch(
        'pneumatic_backend.accounts.services.account.configuration',
        settings.CONFIGURATION_PROD
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    stripe_service_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'update_customer'
    )
    service = AccountService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type
    )

    # act
    service._update_stripe_account(name=name)

    # arrange
    stripe_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    stripe_service_mock.assert_called_once()


def test_update_stripe_account__phone_changed__ok(mocker):

    # arrange
    account = create_test_account(stripe_id='u123asd')
    user = create_test_user(account=account)
    phone = '89995554411'
    is_superuser = True
    auth_type = AuthTokenType.API
    mocker.patch(
        'pneumatic_backend.accounts.services.account.configuration',
        settings.CONFIGURATION_PROD
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    stripe_service_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'update_customer'
    )
    service = AccountService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type
    )

    # act
    service._update_stripe_account(phone=phone)

    # arrange
    stripe_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    stripe_service_mock.assert_called_once()


def test_update_stripe_account__not_stripe_id__skip(mocker):

    # arrange
    account = create_test_account(stripe_id=None)
    user = create_test_user(account=account)
    phone = '89995554411'
    name = 'Company'
    is_superuser = True
    auth_type = AuthTokenType.API
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    stripe_service_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'update_customer'
    )
    service = AccountService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type
    )

    # act
    service._update_stripe_account(phone=phone, name=name)

    # arrange
    stripe_service_init_mock.assert_not_called()
    stripe_service_mock.assert_not_called()


def test_update_stripe_account__tenant__skip(mocker):

    # arrange
    account = create_test_account(
        stripe_id='cus_123',
        lease_level=LeaseLevel.TENANT,

    )
    user = create_test_user(account=account)
    phone = '89995554411'
    name = 'Company'
    is_superuser = True
    auth_type = AuthTokenType.API
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    stripe_service_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'update_customer'
    )
    service = AccountService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type
    )

    # act
    service._update_stripe_account(phone=phone, name=name)

    # arrange
    stripe_service_init_mock.assert_not_called()
    stripe_service_mock.assert_not_called()


def test_update_stripe_account__stripe_exc__log(mocker):

    # arrange
    account = create_test_account(stripe_id='uQ@#QWwe123')
    user = create_test_user(account=account)
    phone = '89995554411'
    name = 'Company'
    is_superuser = True
    auth_type = AuthTokenType.API
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    message = 'message'
    stripe_service_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'update_customer',
        side_effect=StripeServiceException(message)
    )
    log_mock = mocker.patch(
        'pneumatic_backend.accounts.services.account'
        '.capture_sentry_message'
    )
    mocker.patch(
        'pneumatic_backend.accounts.services.account.configuration',
        settings.CONFIGURATION_PROD
    )
    service = AccountService(
        instance=account,
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type
    )

    # act
    service._update_stripe_account(phone=phone, name=name)

    # arrange
    stripe_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    stripe_service_mock.assert_called_once()
    log_mock.assert_called_once()
