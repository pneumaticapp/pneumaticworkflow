"""Real HTTP exchanges for callbacks, webhook management and account plans."""

from hashlib import sha256
import hmac
import json
from time import time

from django.core.cache import caches
from django.http import HttpResponse
import pytest

from src.accounts.enums import BillingPlanType
from src.accounts.models import User
from src.generics.tests.clients import PneumaticApiClient
from src.payment.stripe.permissions import StripeWebhookPermission
from src.payment.tests.fixtures import (
    create_test_invoice_price,
    create_test_product,
    create_test_recurring_price,
)
from src.processes.enums import TaskStatus, WorkflowStatus
from src.processes.tests.fixtures import (
    create_test_not_admin,
    create_test_owner,
    create_test_workflow,
)
from src.webhooks.enums import HookEvent
from src.webhooks.models import WebHook

pytestmark = pytest.mark.django_db

TARGET = 'https://example.test/webhook'
EVENT = HookEvent.WORKFLOW_STARTED
MANAGEMENT_CASES = [
    ('get', '/webhooks/events'),
    ('get', f'/webhooks/events/{EVENT}'),
    ('post', f'/webhooks/events/{EVENT}/subscribe'),
    ('post', f'/webhooks/events/{EVENT}/unsubscribe'),
    ('post', '/webhooks/subscribe'),
    ('post', '/webhooks/unsubscribe'),
]


@pytest.fixture(autouse=True)
def misc_contract_environment(settings) -> None:
    settings.PRIVATE_API_CHECK_IP = False
    settings.CUSTOMERIO_WEBHOOK_API_KEY = 'local-contract-webhook-key'
    settings.CUSTOMERIO_WEBHOOK_API_VERSION = 'v0'
    for alias in ('default', 'auth', 'session'):
        caches[alias].clear()


@pytest.fixture
def misc_owner() -> User:
    return create_test_owner()


def customerio_request(
    client: PneumaticApiClient, settings: object, payload: dict, **extra,
) -> HttpResponse:
    raw = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    timestamp = str(int(time()))
    signature = hmac.new(
        settings.CUSTOMERIO_WEBHOOK_API_KEY.encode('utf-8'),
        f'v0:{timestamp}:'.encode() + raw,
        sha256,
    ).hexdigest()
    return client.post(
        '/analytics/customerio/webhooks',
        data=raw,
        content_type='application/json',
        HTTP_X_CIO_TIMESTAMP=timestamp,
        HTTP_X_CIO_SIGNATURE=signature,
        **extra,
    )


@pytest.mark.parametrize('metric,subscribed', [
    ('unsubscribed', False), ('subscribed', True),
])
def test_customerio__real_signature__updates_subscription(
    contract_api_client, settings, misc_owner, metric, subscribed,
) -> None:
    misc_owner.is_newsletters_subscriber = not subscribed
    misc_owner.save(update_fields=['is_newsletters_subscriber'])
    response = customerio_request(
        contract_api_client, settings,
        {
            'metric': metric,
            'data': {'identifiers': {'id': str(misc_owner.id)}},
        },
    )
    assert response.status_code == 200
    assert response.json() == {}
    misc_owner.refresh_from_db()
    assert misc_owner.is_newsletters_subscriber is subscribed


def test_customerio__signed_invalid_structure__bad_request(
    contract_api_client, settings,
) -> None:
    response = customerio_request(contract_api_client, settings, {})
    assert response.status_code == 400
    assert not response.content


@pytest.mark.parametrize('authenticated,status', [(False, 401), (True, 403)])
def test_customerio__bad_signature__permission_error(
    contract_api_client, misc_owner, authenticated, status,
) -> None:
    if authenticated:
        contract_api_client.token_authenticate(misc_owner)
    response = contract_api_client.post(
        '/analytics/customerio/webhooks',
        data={'metric': 'unsubscribed'}, format='json',
        HTTP_X_CIO_TIMESTAMP='1767225600',
        HTTP_X_CIO_SIGNATURE='invalid',
    )
    assert response.status_code == status


@pytest.mark.parametrize('billing_plan', [
    BillingPlanType.FREEMIUM, BillingPlanType.PREMIUM,
])
def test_account_plan__real_cached_account__success(
    contract_api_client, misc_owner, billing_plan,
) -> None:
    account = misc_owner.account
    account.billing_plan = billing_plan
    account.plan_expiration = None
    account.save(update_fields=['billing_plan', 'plan_expiration'])
    contract_api_client.token_authenticate(misc_owner)
    response = contract_api_client.get('/v2/accounts/plan')
    assert response.status_code == 200
    assert response.json()['billing_plan'] == billing_plan
    assert response.json()['active_users'] == account.active_users


def test_account_plan__unauthenticated__unauthorized(
    contract_api_client,
) -> None:
    assert contract_api_client.get('/v2/accounts/plan').status_code == 401


def test_account_plan__missing_billing_plan__forbidden(
    contract_api_client, misc_owner,
) -> None:
    misc_owner.account.billing_plan = None
    misc_owner.account.save(update_fields=['billing_plan'])
    contract_api_client.token_authenticate(misc_owner)
    assert contract_api_client.get('/v2/accounts/plan').status_code == 403


@pytest.mark.parametrize('completed', [False, True])
def test_task_webhook_example__real_full_workflow__success(
    contract_api_client, misc_owner, completed,
) -> None:
    workflow = create_test_workflow(user=misc_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    if completed:
        task.status = TaskStatus.COMPLETED
        task.save(update_fields=['status'])
    contract_api_client.token_authenticate(misc_owner)
    response = contract_api_client.get(
        '/v2/tasks/webhook-example',
        data={
            'status': TaskStatus.COMPLETED if completed else TaskStatus.ACTIVE,
            'ordering': '-date_started',
        },
    )
    assert response.status_code == 200
    value = response.json()
    assert value['task']['workflow']['id'] == workflow.id
    assert value['task']['workflow']['template']['id'] == workflow.template_id
    assert 'template_name' not in value['task']['workflow']
    assert value['hook']['event'] == (
        HookEvent.TASK_COMPLETED if completed else HookEvent.TASK_RETURNED
    )


def test_task_webhook_example__no_tasks__not_found(
    contract_api_client, misc_owner,
) -> None:
    contract_api_client.token_authenticate(misc_owner)
    response = contract_api_client.get('/v2/tasks/webhook-example')
    assert response.status_code == 404
    assert not response.content


@pytest.mark.parametrize('authenticated,status', [(False, 401), (True, 403)])
def test_task_webhook_example__permissions__error(
    contract_api_client, misc_owner, authenticated, status,
) -> None:
    if authenticated:
        misc_owner.account.billing_plan = None
        misc_owner.account.save(update_fields=['billing_plan'])
        contract_api_client.token_authenticate(misc_owner)
    response = contract_api_client.get('/v2/tasks/webhook-example')
    assert response.status_code == status


@pytest.mark.parametrize('query', [
    {'status': 'unknown'}, {'ordering': 'unknown'},
])
def test_task_webhook_example__invalid_filter__bad_request(
    contract_api_client, misc_owner, query,
) -> None:
    contract_api_client.token_authenticate(misc_owner)
    response = contract_api_client.get(
        '/v2/tasks/webhook-example', data=query,
    )
    assert response.status_code == 400


@pytest.mark.parametrize('status', [
    WorkflowStatus.RUNNING, WorkflowStatus.DONE,
])
def test_workflow_webhook_example__real_workflow__success(
    contract_api_client, misc_owner, status,
) -> None:
    workflow = create_test_workflow(
        user=misc_owner, tasks_count=1, status=status,
    )
    contract_api_client.token_authenticate(misc_owner)
    response = contract_api_client.get(
        '/workflows/webhook-example',
        data={'status': status, 'ordering': '-date_created'},
    )
    assert response.status_code == 200
    assert response.json()['workflow']['id'] == workflow.id
    assert response.json()['hook']['event'] == (
        HookEvent.WORKFLOW_COMPLETED if status == WorkflowStatus.DONE
        else HookEvent.WORKFLOW_STARTED
    )


@pytest.mark.parametrize('query', [
    {'status': 'unknown'}, {'ordering': 'unknown'},
    {'status': WorkflowStatus.DELAYED},
])
def test_workflow_webhook_example__invalid_filter__bad_request(
    contract_api_client, misc_owner, query,
) -> None:
    contract_api_client.token_authenticate(misc_owner)
    response = contract_api_client.get(
        '/workflows/webhook-example', data=query,
    )
    assert response.status_code == 400


def test_workflow_webhook_example__no_workflows__not_found(
    contract_api_client, misc_owner,
) -> None:
    contract_api_client.token_authenticate(misc_owner)
    response = contract_api_client.get('/workflows/webhook-example')
    assert response.status_code == 404
    assert not response.content


@pytest.mark.parametrize('authenticated,status', [(False, 401), (True, 403)])
def test_workflow_webhook_example__permissions__error(
    contract_api_client, misc_owner, authenticated, status,
) -> None:
    if authenticated:
        misc_owner.account.billing_plan = None
        misc_owner.account.save(update_fields=['billing_plan'])
        contract_api_client.token_authenticate(misc_owner)
    response = contract_api_client.get('/workflows/webhook-example')
    assert response.status_code == status


def test_webhook_events__real_models__subscribe_retrieve_unsubscribe(
    contract_api_client, misc_owner,
) -> None:
    contract_api_client.token_authenticate(misc_owner)
    listing = contract_api_client.get('/webhooks/events')
    assert listing.status_code == 200
    assert {item['event'] for item in listing.json()} == HookEvent.VALUES
    assert all(item['url'] is None for item in listing.json())
    absent = contract_api_client.get(f'/webhooks/events/{EVENT}')
    assert absent.status_code == 200
    assert absent.json() == {'url': None}
    subscribed = contract_api_client.post(
        f'/webhooks/events/{EVENT}/subscribe',
        data={'url': TARGET}, format='json',
    )
    assert subscribed.status_code == 204
    hook = WebHook.objects.get(account=misc_owner.account, event=EVENT)
    assert hook.target == TARGET
    actual = contract_api_client.get(f'/webhooks/events/{EVENT}')
    assert actual.status_code == 200
    assert actual.json() == {'url': TARGET}
    unsubscribed = contract_api_client.post(
        f'/webhooks/events/{EVENT}/unsubscribe',
    )
    assert unsubscribed.status_code == 204
    assert not WebHook.objects.filter(pk=hook.pk).exists()


def test_webhooks__all_events__real_subscribe_and_unsubscribe(
    contract_api_client, misc_owner,
) -> None:
    contract_api_client.token_authenticate(misc_owner)
    subscribed = contract_api_client.post(
        '/webhooks/subscribe', data={'url': TARGET}, format='json',
    )
    assert subscribed.status_code == 204
    assert set(WebHook.objects.filter(account=misc_owner.account).values_list(
        'event', flat=True,
    )) == HookEvent.VALUES
    unsubscribed = contract_api_client.post('/webhooks/unsubscribe')
    assert unsubscribed.status_code == 204
    assert not WebHook.objects.filter(account=misc_owner.account).exists()


@pytest.mark.parametrize('method,path', MANAGEMENT_CASES)
@pytest.mark.parametrize('authenticated,status', [(False, 401), (True, 403)])
def test_webhook_management__permissions__error(
    contract_api_client, misc_owner, method, path, authenticated, status,
) -> None:
    if authenticated:
        member = create_test_not_admin(account=misc_owner.account)
        contract_api_client.token_authenticate(member)
    response = getattr(contract_api_client, method)(
        path, data={'url': TARGET},
    )
    assert response.status_code == status


@pytest.mark.parametrize('method,suffix', [
    ('get', ''), ('post', '/subscribe'), ('post', '/unsubscribe'),
])
def test_webhook_event__unknown_event__not_found(
    contract_api_client, misc_owner, method, suffix,
) -> None:
    contract_api_client.token_authenticate(misc_owner)
    response = getattr(contract_api_client, method)(
        f'/webhooks/events/unknown-event{suffix}', data={'url': TARGET},
    )
    assert response.status_code == 404


@pytest.mark.parametrize('path', [
    '/webhooks/subscribe', f'/webhooks/events/{EVENT}/subscribe',
])
def test_webhooks__invalid_target__bad_request(
    contract_api_client, misc_owner, path,
) -> None:
    contract_api_client.token_authenticate(misc_owner)
    response = contract_api_client.post(path, data={'url': 'invalid'})
    assert response.status_code == 400


def test_webhook_buffer__real_cache__push_list_clear(
    contract_api_client,
) -> None:
    payload = {'event': EVENT, 'workflow_id': 123}
    added = contract_api_client.post(
        '/webhooks/buffer', data=payload, format='json',
    )
    assert added.status_code == 204
    listing = contract_api_client.get('/webhooks/buffer')
    assert listing.status_code == 200
    assert listing.json() == [payload]
    cleared = contract_api_client.post('/webhooks/buffer/clear')
    assert cleared.status_code == 204
    assert contract_api_client.get('/webhooks/buffer').json() == []


@pytest.mark.parametrize('payload', [None, 'payload', False, 42, ['value']])
def test_webhook_buffer__json_values__array_response(
    contract_api_client, payload,
) -> None:
    captured = contract_api_client.post(
        '/webhooks/buffer', data=json.dumps(payload),
        content_type='application/json',
    )
    assert captured.status_code == 204
    listing = contract_api_client.get('/webhooks/buffer')
    assert listing.status_code == 200
    assert listing.json() == [payload]


@pytest.mark.parametrize('method,path', [
    ('get', '/webhooks/buffer'),
    ('post', '/webhooks/buffer'),
    ('post', '/webhooks/buffer/clear'),
])
@pytest.mark.parametrize('authenticated,status', [(False, 401), (True, 403)])
def test_webhook_buffer__production__permission_error(
    contract_api_client, settings, misc_owner,
    method, path, authenticated, status,
) -> None:
    settings.CONFIGURATION_CURRENT = settings.CONFIGURATION_PROD
    if authenticated:
        contract_api_client.token_authenticate(misc_owner)
    response = getattr(contract_api_client, method)(path)
    assert response.status_code == status


def test_stripe_webhook__real_body__queued(
    contract_api_client, mocker,
) -> None:
    queued = mocker.patch('src.payment.views.handle_webhook.delay')
    payload = {
        'id': 'evt_contract', 'type': 'customer.subscription.updated',
        'data': {'object': {'id': 'sub_contract'}},
    }
    response = contract_api_client.post(
        '/payment/stripe/webhooks', data=payload, format='json',
    )
    assert response.status_code == 204
    queued.assert_called_once_with(data=payload)


@pytest.mark.parametrize('authenticated,status', [(False, 401), (True, 403)])
def test_stripe_webhook__non_allowlisted_ip__permission_error(
    contract_api_client, mocker, settings, misc_owner, authenticated, status,
) -> None:
    mocker.patch.object(
        StripeWebhookPermission, 'configuration', settings.CONFIGURATION_PROD,
    )
    mocker.patch.object(
        StripeWebhookPermission, 'whitelist', ['192.0.2.1'],
    )
    if authenticated:
        contract_api_client.token_authenticate(misc_owner)
    response = contract_api_client.post(
        '/payment/stripe/webhooks', data={}, format='json',
        HTTP_X_REAL_IP='192.0.2.2',
    )
    assert response.status_code == status


def test_payment_products__real_catalog__success(
    contract_api_client, misc_owner,
) -> None:
    recurring = create_test_recurring_price()
    addon = create_test_product(
        code='addon', stripe_id='prod_addon', is_subscription=False,
    )
    one_time = create_test_invoice_price(product=addon, code='one-time')
    create_test_product(
        code='inactive', stripe_id='prod_inactive', is_active=False,
    )
    contract_api_client.token_authenticate(misc_owner)
    response = contract_api_client.get('/payment/products')
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 2
    codes = {price['code'] for product in products
             for price in product['prices']}
    assert codes == {recurring.code, one_time.code}


@pytest.mark.parametrize('authenticated,status', [(False, 401), (True, 403)])
def test_payment_products__permissions__error(
    contract_api_client, misc_owner, authenticated, status,
) -> None:
    if authenticated:
        member = create_test_not_admin(account=misc_owner.account)
        contract_api_client.token_authenticate(member)
    assert contract_api_client.get('/payment/products').status_code == status
