"""Real validation and throttling outcomes missing from Core HTTP coverage."""

from typing import Any

from _pytest.monkeypatch import MonkeyPatch
from django.core.cache import caches
from django.http import HttpResponse
from django.utils import timezone
import pytest

from src.accounts.enums import BillingPlanType
from src.accounts.models import User
from src.authentication.enums import AuthTokenType
from src.generics.tests.clients import PneumaticApiClient
from src.generics.throttling import CustomSimpleRateThrottle
from src.notifications.models import Device
from src.openapi.tests.http_contracts import HttpContract
from src.processes.models.templates.preset import TemplatePreset
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_template,
    create_test_template_preset,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


QUERY_ERRORS = (
    ('/attachments', {'limit': -1}),
    ('/reports/dashboard/tasks/breakdown', {'now': 'invalid'}),
    ('/reports/dashboard/tasks/by-steps', {'template_id': 'invalid'}),
    ('/reports/dashboard/tasks/overview', {'now': 'invalid'}),
    ('/reports/dashboard/workflows/breakdown', {'now': 'invalid'}),
    ('/reports/dashboard/workflows/by-tasks', {'template_id': 'invalid'}),
    ('/templates/export', {'limit': -1}),
    ('/templates/titles-by-owners', {'limit': -1}),
)


@pytest.fixture(autouse=True)
def validation_environment(settings: Any) -> None:
    settings.PRIVATE_API_CHECK_IP = False
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'AI': True}
    for alias in ('default', 'auth', 'session'):
        caches[alias].clear()


@pytest.fixture
def validation_owner() -> User:
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED, billing_sync=False,
    )
    return create_test_owner(account=account)


def assert_bad_request(response: HttpResponse) -> None:
    assert response.status_code == 400
    assert response['Content-Type'].split(';', 1)[0] == 'application/json'
    assert response.json()


def assert_validation_example(
    contract: HttpContract,
    path: str,
    name: str,
    response: HttpResponse,
    method: str = 'get',
) -> None:
    definition = contract.resolve(
        contract.document['paths'][path][method]['responses']['400'],
    )
    examples = definition['content']['application/json']['examples']
    assert examples[name]['value'] == response.json()


@pytest.mark.parametrize('path,query', QUERY_ERRORS)
def test_query_validation__real_serializers__bad_request(
    contract_api_client: PneumaticApiClient,
    validation_owner: User,
    path: str,
    query: dict,
) -> None:
    contract_api_client.token_authenticate(validation_owner)

    response = contract_api_client.get(path, data=query)

    assert_bad_request(response)


def test_template_steps__invalid_boolean__bad_request(
    contract_api_client: PneumaticApiClient, validation_owner: User,
) -> None:
    template = create_test_template(validation_owner, is_active=True)
    contract_api_client.token_authenticate(validation_owner)

    response = contract_api_client.get(
        f'/templates/{template.id}/steps',
        data={'with_tasks_in_progress': 'invalid'},
    )

    assert_bad_request(response)


def test_workflow_events__invalid_ordering__bad_request(
    contract_api_client: PneumaticApiClient,
    validation_owner: User,
    http_contract: HttpContract,
) -> None:
    workflow = create_test_workflow(validation_owner, tasks_count=1)
    contract_api_client.token_authenticate(validation_owner)

    response = contract_api_client.get(
        f'/workflows/{workflow.id}/events', data={'ordering': 'invalid'},
    )

    assert_bad_request(response)
    assert_validation_example(
        http_contract, '/workflows/{id}/events', 'InvalidOrdering', response,
    )


@pytest.mark.parametrize(
    'action', ['activate-vacation', 'deactivate-vacation'],
)
def test_vacation__invalid_state_or_missing_substitutes__bad_request(
    contract_api_client: PneumaticApiClient,
    validation_owner: User,
    action: str,
) -> None:
    contract_api_client.token_authenticate(validation_owner)

    response = contract_api_client.post(
        f'/accounts/users/{validation_owner.id}/{action}',
        data={}, format='json',
    )

    assert_bad_request(response)
    validation_owner.refresh_from_db()
    assert validation_owner.vacation is None


def test_nested_api_key__too_long_name__bad_request(
    contract_api_client: PneumaticApiClient, validation_owner: User,
) -> None:
    contract_api_client.token_authenticate(validation_owner)

    response = contract_api_client.post(
        f'/accounts/users/{validation_owner.id}/api-keys',
        data={'name': 'k' * 201}, format='json',
    )

    assert_bad_request(response)


def test_device__missing_token__bad_request(
    contract_api_client: PneumaticApiClient,
    validation_owner: User,
    settings: Any,
    http_contract: HttpContract,
) -> None:
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'PUSH': True}
    contract_api_client.token_authenticate(validation_owner)
    before = Device.objects.count()

    response = contract_api_client.post(
        '/notifications/device', data={}, format='json',
    )

    assert_bad_request(response)
    assert_validation_example(
        http_contract, '/notifications/device', 'MissingDeviceToken',
        response, method='post',
    )
    assert Device.objects.count() == before


@pytest.mark.parametrize('action', ['delete', 'default'])
def test_preset__unused_invalid_body__successful_real_service(
    contract_api_client: PneumaticApiClient,
    validation_owner: User,
    action: str,
) -> None:
    template = create_test_template(validation_owner, is_active=True)
    preset = create_test_template_preset(template, validation_owner)
    contract_api_client.token_authenticate(validation_owner)
    path = f'/templates/presets/{preset.id}'
    query = '?ordering=invalid&limit=-1&unused=value'

    response = (
        contract_api_client.delete(
            f'{path}{query}', data=b'{invalid JSON',
            content_type='application/json',
        )
        if action == 'delete'
        else contract_api_client.post(
            f'{path}/default{query}', data=b'{invalid JSON',
            content_type='application/json',
        )
    )

    assert response.status_code == 204
    assert not response.content
    if action == 'delete':
        assert not TemplatePreset.objects.filter(id=preset.id).exists()
    else:
        preset.refresh_from_db()
        assert preset.is_default is True


def test_due_date_delete__ignores_body__clears_real_nullable_field(
    contract_api_client: PneumaticApiClient,
    validation_owner: User,
    mocker: Any,
) -> None:
    workflow = create_test_workflow(validation_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.due_date = timezone.now()
    task.save(update_fields=['due_date'])
    # Dispatch to external notification/websocket workers is the I/O boundary.
    mocker.patch(
        'src.processes.services.tasks.task.send_due_date_changed.delay',
    )
    mocker.patch('src.processes.services.events.send_event_created.delay')
    contract_api_client.token_authenticate(validation_owner)

    response = contract_api_client.delete(
        f'/v2/tasks/{task.id}/due-date?ordering=invalid&limit=-1&unused=value',
        data=b'{invalid JSON',
        content_type='application/json',
    )

    assert response.status_code == 204
    assert not response.content
    task.refresh_from_db()
    assert task.due_date is None


@pytest.mark.parametrize('path,scope,authenticated', [
    ('/services/steps-by-description', '04_services__steps_by_description',
     False),
    ('/templates/ai', '03_processes__template_ai_generation', True),
])
def test_real_throttle__repeated_validation_failure__too_many_requests(
    contract_api_client: PneumaticApiClient,
    validation_owner: User,
    monkeypatch: MonkeyPatch,
    path: str,
    scope: str,
    authenticated: bool,
) -> None:
    monkeypatch.setitem(
        CustomSimpleRateThrottle.THROTTLE_RATES, scope, '1/min',
    )
    if authenticated:
        contract_api_client.token_authenticate(validation_owner)
    method = contract_api_client.post if authenticated else (
        contract_api_client.get
    )

    first = method(path, data={}, format='json')
    second = method(path, data={}, format='json')

    assert_bad_request(first)
    assert second.status_code == 429
    assert second.json()['detail']
    assert int(second['Retry-After']) >= 1


@pytest.mark.parametrize('token_type', [AuthTokenType.USER, AuthTokenType.API])
@pytest.mark.parametrize('operation,scopes', [
    ('invites', ('01_accounts_invites__token',)),
    ('purchase', ('05_payment__purchase__user', '06_payment__purchase__api')),
    ('guest-performer', ('02_processes__create_guest_performer',)),
])
def test_disabled_auth_throttle__configured_rate__still_validates_requests(
    contract_api_client: PneumaticApiClient,
    validation_owner: User,
    monkeypatch: MonkeyPatch,
    token_type: str,
    operation: str,
    scopes: tuple,
) -> None:
    for scope in scopes:
        monkeypatch.setitem(
            CustomSimpleRateThrottle.THROTTLE_RATES, scope, '1/min',
        )
    if operation == 'invites':
        path = '/accounts/invites'
    elif operation == 'purchase':
        path = '/payment/purchase'
    else:
        workflow = create_test_workflow(validation_owner, tasks_count=1)
        task = workflow.tasks.get(number=1)
        path = f'/v2/tasks/{task.id}/create-guest-performer'
    contract_api_client.token_authenticate(
        validation_owner, token_type=token_type,
    )

    first = contract_api_client.post(path, data={}, format='json')
    second = contract_api_client.post(path, data={}, format='json')

    assert_bad_request(first)
    assert_bad_request(second)
