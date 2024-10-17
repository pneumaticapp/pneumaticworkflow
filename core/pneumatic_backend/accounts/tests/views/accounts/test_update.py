import pytest
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
    LeaseLevel,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
)
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.accounts.messages import (
    MSG_A_0003
)

pytestmark = pytest.mark.django_db


def test_partial_update__free_plan_name__ok(
    api_client,
    group_mock
):

    # arrange
    logo_lg = 'https://some-site.com/image.jpg'
    logo_sm = 'https://some-site.com/image-2.jpg'
    account = create_test_account(
        logo_lg=logo_lg,
        logo_sm=logo_sm,
        plan=BillingPlanType.FREEMIUM,
    )
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    new_name = 'New name'

    # act
    response = api_client.put(
        '/accounts/account',
        data={
            'name': new_name,
        }
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == account.id
    assert response.data['name'] == new_name
    assert response.data['date_joined'] is not None
    assert response.data['plan_expiration'] is None
    assert response.data['lease_level'] == LeaseLevel.STANDARD
    assert response.data['logo_lg'] == logo_lg
    assert response.data['logo_sm'] == logo_sm

    account.refresh_from_db()
    assert account.name == new_name


def test_partial_update__free_plan_change_logo_lg__validation_error(
    api_client,
):

    # arrange
    logo_lg = 'https://some-site.com/image.jpg'
    account = create_test_account(plan=BillingPlanType.FREEMIUM)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/account',
        data={
            'logo_lg': logo_lg
        }
    )

    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'logo_lg'
    assert response.data['message'] == MSG_A_0003
    assert response.data['details']['reason'] == MSG_A_0003


def test_partial_update__free_plan_change_logo_sm__validation_error(
    api_client,
):
    # arrange
    logo_sm = 'https://some-site.com/image.jpg'
    account = create_test_account(plan=BillingPlanType.FREEMIUM)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/account',
        data={
            'logo_sm': logo_sm
        }
    )

    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'logo_sm'
    assert response.data['message'] == MSG_A_0003
    assert response.data['details']['reason'] == MSG_A_0003


def test_partial_update__tenant__name__ok(
    api_client,
    mocker,
):
    logo_lg = 'https://some-site.com/image.jpg'
    logo_sm = 'https://some-site.com/image-2.jpg'
    account = create_test_account(
        logo_lg=logo_lg,
        logo_sm=logo_sm,
        lease_level=LeaseLevel.TENANT,
        plan=BillingPlanType.PREMIUM
    )
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    new_name = 'New name'
    group_mock = mocker.patch(
        'pneumatic_backend.analytics.mixins.BaseIdentifyMixin.group'
    )

    # act
    response = api_client.put(
        '/accounts/account',
        data={
            'name': new_name,
        }
    )

    assert response.status_code == 200
    assert response.data['id'] == account.id
    assert response.data['name'] == new_name
    assert response.data['date_joined'] is not None
    assert response.data['plan_expiration'] is not None
    assert response.data['lease_level'] == LeaseLevel.TENANT
    assert response.data['logo_lg'] == logo_lg
    assert response.data['logo_sm'] == logo_sm

    account.refresh_from_db()
    assert account.name == new_name
    assert account.logo_lg == logo_lg
    assert account.logo_sm == logo_sm
    group_mock.assert_called_once_with(user=user, account=account)


def test_partial_update__tenant__logo_lg__validation__error(
    api_client,
):
    logo_lg = 'https://some-site.com/image-2.jpg'
    account = create_test_account(
        lease_level=LeaseLevel.TENANT,
        plan=BillingPlanType.PREMIUM
    )
    user = create_test_user(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/account',
        data={
            'logo_lg': logo_lg,
        }
    )

    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'logo_lg'
    assert response.data['message'] == MSG_A_0003
    assert response.data['details']['reason'] == MSG_A_0003


def test_partial_update__tenant__logo_sm__validation__error(
    api_client,
):
    logo_sm = 'https://some-site.com/image-2.jpg'
    account = create_test_account(
        lease_level=LeaseLevel.TENANT,
        plan=BillingPlanType.PREMIUM
    )
    user = create_test_user(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/account',
        data={
            'logo_sm': logo_sm,
        }
    )

    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'logo_sm'
    assert response.data['message'] == MSG_A_0003
    assert response.data['details']['reason'] == MSG_A_0003


def test_partial_update__not_admin__permission_denied(
    api_client,
    group_mock
):

    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
    )
    user = create_test_user(
        account=account,
        is_account_owner=False,
        is_admin=False
    )
    api_client.token_authenticate(user)
    new_name = 'New name'

    # act
    response = api_client.put(
        '/accounts/account',
        data={
            'name': new_name
        }
    )

    # assert
    assert response.status_code == 403


def test_partial_update__fractionalcoo_plan_all_fields__ok(
    api_client,
    group_mock
):

    # arrange
    logo_lg = 'https://some-site.com/image.jpg'
    logo_sm = 'https://some-site.com/image-2.jpg'
    account = create_test_account(
        plan=BillingPlanType.FRACTIONALCOO,
        lease_level=LeaseLevel.STANDARD,
    )
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    new_name = 'New name'

    # act
    response = api_client.put(
        '/accounts/account',
        data={
            'name': new_name,
            'logo_sm': logo_sm,
            'logo_lg': logo_lg
        }
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == account.id
    assert response.data['name'] == new_name
    assert response.data['date_joined'] is not None
    assert response.data['plan_expiration'] is not None
    assert response.data['lease_level'] == LeaseLevel.STANDARD
    assert response.data['logo_lg'] == logo_lg
    assert response.data['logo_sm'] == logo_sm


def test_partial_update__unlimited_plan_all_fields__ok(
    api_client,
    group_mock
):

    # arrange
    logo_lg = 'https://some-site.com/image.jpg'
    logo_sm = 'https://some-site.com/image-2.jpg'
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.STANDARD,
    )
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    new_name = 'New name'

    # act
    response = api_client.put(
        '/accounts/account',
        data={
            'name': new_name,
            'logo_sm': logo_sm,
            'logo_lg': logo_lg
        }
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == account.id
    assert response.data['name'] == new_name
    assert response.data['date_joined'] is not None
    assert response.data['plan_expiration'] is not None
    assert response.data['lease_level'] == LeaseLevel.STANDARD
    assert response.data['logo_lg'] == logo_lg
    assert response.data['logo_sm'] == logo_sm


def test_partial_update__premium_plan_all_fields__ok(
    api_client,
    group_mock
):

    # arrange
    logo_lg = 'https://some-site.com/image.jpg'
    logo_sm = 'https://some-site.com/image-2.jpg'
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    new_name = 'New name'

    # act
    response = api_client.put(
        '/accounts/account',
        data={
            'name': new_name,
            'logo_sm': logo_sm,
            'logo_lg': logo_lg
        }
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == account.id
    assert response.data['name'] == new_name
    assert response.data['date_joined'] is not None
    assert response.data['plan_expiration'] is not None
    assert response.data['lease_level'] == LeaseLevel.STANDARD
    assert response.data['logo_lg'] == logo_lg
    assert response.data['logo_sm'] == logo_sm


def test_partial_update__name__ok(
    api_client,
    group_mock
):

    plan = BillingPlanType.PREMIUM
    logo_lg = 'https://some-site/image.jpg'
    account = create_test_account(
        plan=plan,
        lease_level=LeaseLevel.STANDARD,
        logo_lg=logo_lg
    )
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    new_name = 'New name'
    response = api_client.put(
        '/accounts/account',
        data={
            'name': new_name
        }
    )

    assert response.status_code == 200
    assert response.data['id'] == account.id
    assert response.data['name'] == new_name
    assert response.data['date_joined'] is not None
    assert response.data['plan_expiration'] is not None
    assert response.data['lease_level'] == LeaseLevel.STANDARD
    assert response.data['logo_lg'] == logo_lg
    assert response.data['logo_sm'] is None

    account.refresh_from_db()
    assert account.name == new_name


def test_partial_update__plan__skip(
    api_client,
    group_mock
):

    # arrange
    account = create_test_account(
        plan=BillingPlanType.FREEMIUM
    )
    user = create_test_user(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/account',
        data={'plan':  BillingPlanType.PREMIUM}
    )

    # assert
    assert response.status_code == 200
    account.refresh_from_db()
    assert account.billing_plan == BillingPlanType.FREEMIUM


def test_partial_update__logo_sm_invalid_url__validation_error(
    api_client,
    group_mock,
):

    plan = BillingPlanType.UNLIMITED
    account = create_test_account(
        plan=plan,
    )
    user = create_test_user(account=account)
    api_client.token_authenticate(user)

    response = api_client.put(
        '/accounts/account',
        data={
            'logo_sm': '/some-site/image.jpg'
        }
    )

    assert response.status_code == 400
    message = 'Enter a valid URL.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'logo_sm'
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message


def test_partial_update__logo_lg_invalid_url__validation_error(
    api_client,
    group_mock,
):

    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
    )
    user = create_test_user(account=account)
    api_client.token_authenticate(user)

    response = api_client.put(
        '/accounts/account',
        data={
            'logo_lg': '/some-site/image.jpg'
        }
    )

    assert response.status_code == 400
    message = 'Enter a valid URL.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'logo_lg'
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
