import pytest
from django.contrib.auth import get_user_model
from pneumatic_backend.payment.enums import PriceStatus
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
)
from pneumatic_backend.payment.tests.fixtures import (
    create_test_invoice_price,
    create_test_product,
    create_test_recurring_price
)
from pneumatic_backend.payment import messages


UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_products__ok(
    mocker,
    api_client,
):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    product_1 = create_test_product(
        stripe_id='prod_1',
        code='some code',
        name='Prem',
        is_active=True,
        is_subscription=True
    )
    price_1 = create_test_recurring_price(
        product=product_1,
        status=PriceStatus.ACTIVE,
        trial_days=1,
        code='prem_month',
        stripe_id='price_1',
        min_quantity=5,
        max_quantity=1000
    )
    create_test_recurring_price(
        product=product_1,
        status=PriceStatus.INACTIVE,
        code='prem_month_2',
        stripe_id='price_2'
    )
    product_2 = create_test_product(
        stripe_id='prod_2',
        name='Addon',
        code='some code 2',
        is_active=True,
        is_subscription=False
    )
    price_21 = create_test_invoice_price(
        product=product_2,
        status=PriceStatus.ACTIVE,
        code='addon',
        stripe_id='price_21'
    )
    create_test_product(is_active=False)
    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    # act
    response = api_client.get('/payment/products')

    # assert
    assert response.status_code == 200
    data = response.data
    assert len(data) == 2
    product_1_data = data[0]
    assert product_1_data['name'] == product_1.name
    assert product_1_data['code'] == product_1.code
    assert product_1_data['is_subscription'] == product_1.is_subscription
    assert len(product_1_data['prices']) == 1
    price_1_data = product_1_data['prices'][0]
    assert price_1_data['name'] == price_1.name
    assert price_1_data['code'] == price_1.code
    assert price_1_data['max_quantity'] == price_1.max_quantity
    assert price_1_data['min_quantity'] == price_1.min_quantity
    assert price_1_data['price_type'] == price_1.price_type
    assert price_1_data['price'] == price_1.price
    assert price_1_data['trial_days'] == price_1.trial_days
    assert price_1_data['billing_period'] == price_1.billing_period
    product_2_data = data[1]
    assert product_2_data['name'] == product_2.name
    assert product_2_data['code'] == product_2.code
    assert product_2_data['is_subscription'] == product_2.is_subscription
    assert len(product_2_data['prices']) == 1
    price_2_data = product_2_data['prices'][0]
    assert price_2_data['code'] == price_21.code
    assert price_2_data['billing_period'] is None
    assert price_2_data['trial_days'] is None
    assert price_2_data['price_type'] == price_21.price_type


def test_products__archived_price__ok(
    mocker,
    api_client,
):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    product_1 = create_test_product(
        stripe_id='prod_1',
        code='some code',
        name='Prem',
        is_active=True,
        is_subscription=True
    )
    price_1 = create_test_recurring_price(
        product=product_1,
        status=PriceStatus.ARCHIVED,
        trial_days=1,
        code='prem_month',
        stripe_id='price_1',
        min_quantity=10,
        max_quantity=20
    )
    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    # act
    response = api_client.get('/payment/products')

    # assert
    assert response.status_code == 200
    data = response.data
    assert len(data) == 1
    product_1_data = data[0]
    assert product_1_data['name'] == product_1.name
    assert product_1_data['code'] == product_1.code
    assert product_1_data['is_subscription'] == product_1.is_subscription
    assert len(product_1_data['prices']) == 1
    price_1_data = product_1_data['prices'][0]
    assert price_1_data['name'] == price_1.name
    assert price_1_data['code'] == price_1.code
    assert price_1_data['max_quantity'] == price_1.max_quantity
    assert price_1_data['min_quantity'] == price_1.min_quantity
    assert price_1_data['price_type'] == price_1.price_type
    assert price_1_data['price'] == price_1.price
    assert price_1_data['trial_days'] == price_1.trial_days
    assert price_1_data['billing_period'] == price_1.billing_period


def test_products__disable_billing__permission_denied(
    mocker,
    api_client,
):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    product = create_test_product(
        stripe_id='prod_1',
        code='some code',
        name='Prem',
        is_active=True,
        is_subscription=True
    )
    create_test_recurring_price(
        product=product,
        status=PriceStatus.ACTIVE,
        trial_days=1,
        code='prem_month',
        stripe_id='price_1',
        min_quantity=5,
        max_quantity=1000
    )
    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=False
    )

    # act
    response = api_client.get('/payment/products')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == messages.MSG_BL_0021
