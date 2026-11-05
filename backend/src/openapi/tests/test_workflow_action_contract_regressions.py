"""Workflow action contracts use real services and resulting model state."""

from datetime import timedelta
from typing import Any

from django.core.cache import caches
from django.utils import timezone
import pytest
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from src.accounts.enums import BillingPlanType
from src.accounts.models import User
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.generics.tests.clients import PneumaticApiClient
from src.openapi.tests.http_contracts import HttpContract
from src.processes.enums import PerformerType, TaskStatus, WorkflowStatus
from src.processes.models.workflows.task import Task, TaskPerformer
from src.processes.models.workflows.workflow import Workflow
from src.processes.services.workflow_action import WorkflowActionService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_guest,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)


OPERATIONS = (
    ('delete', '/workflows/{id}', '204'),
    ('post', '/workflows/{id}/resume', '200'),
)
MOCKED_WORKFLOW_ACTION_CASES = (
    'src/processes/tests/test_views/test_workflow/test_delete.py'
    '::test_delete__service_exception__validation_error',
    'src/processes/tests/test_views/test_workflow/test_resume.py'
    '::test_resume__service_exception__validation_error',
)
ACTION_ROUTES = tuple((method, path) for method, path, _success in OPERATIONS)


@pytest.fixture
def workflow_action_environment(
    settings: Any, mocker: Any, db: None,
) -> None:
    settings.PRIVATE_API_CHECK_IP = False
    for alias in ('default', 'auth', 'session'):
        caches[alias].clear()
    # Replace only delivery to external workers, retaining events and services.
    for name in (
        'send_task_deleted_notification',
        'send_delayed_workflow_notification',
        'send_resumed_workflow_notification',
        'send_new_task_notification',
        'send_new_task_websocket',
        'send_completed_workflow_notification',
        'send_task_completed_websocket',
        'send_task_completed_notification',
        'send_task_completed_webhook',
        'send_workflow_completed_webhook',
    ):
        mocker.patch(f'src.processes.services.workflow_action.{name}.delay')
    mocker.patch('src.processes.services.events.send_event_created.delay')
    mocker.patch(
        'src.storage.tasks.sync_workflow_attachment_permissions.delay',
    )


@pytest.fixture
def workflow_action_owner(
    contract_api_client: PneumaticApiClient,
    workflow_action_environment: None,
) -> User:
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED, billing_sync=False,
    )
    owner = create_test_owner(account=account)
    contract_api_client.token_authenticate(owner)
    return owner


@pytest.mark.parametrize('body', [
    b'', b'{invalid JSON', b'null', b'{"unused": true}',
])
def test_delete__real_service__soft_deletes_tasks_and_revokes_guest_access(
    contract_api_client: PneumaticApiClient,
    workflow_action_owner: User,
    body: bytes,
) -> None:
    owner = workflow_action_owner
    workflow = create_test_workflow(owner, tasks_count=2)
    tasks = list(workflow.tasks.order_by('number'))
    guest = create_test_guest(account=owner.account)
    TaskPerformer.objects.create(
        task=tasks[0], user=guest, type=PerformerType.USER,
    )
    authentication = GuestJWTAuthService()
    token = authentication.get_validated_token(authentication.get_str_token(
        user_id=guest.id, task_id=tasks[0].id, account_id=owner.account_id,
    ))
    assert authentication.get_cached_user(token).id == guest.id

    response = contract_api_client.delete(
        f'/workflows/{workflow.id}?ordering=invalid&limit=-1', data=body,
        content_type='application/json',
    )

    assert response.status_code == 204
    assert not response.content
    workflow.refresh_from_db()
    assert workflow.is_deleted is True
    assert not Workflow.objects.filter(id=workflow.id).exists()
    for task in tasks:
        task.refresh_from_db()
        assert task.is_deleted is True
    assert not Task.objects.filter(id__in=[task.id for task in tasks]).exists()
    with pytest.raises(AuthenticationFailed):
        authentication.get_cached_user(token)
    workflow.template.refresh_from_db()
    guest.refresh_from_db()
    owner.refresh_from_db()
    assert workflow.template.is_deleted is False
    assert guest.is_deleted is False
    assert owner.is_deleted is False


@pytest.mark.parametrize('status,body', [
    (WorkflowStatus.RUNNING, b''),
    (WorkflowStatus.RUNNING, b'{invalid JSON'),
    (WorkflowStatus.DELAYED, b'null'),
    (WorkflowStatus.DELAYED, b'{invalid JSON'),
    (WorkflowStatus.DONE, b'{"unused": true}'),
])
def test_resume__real_service__restores_state_and_ignores_unused_body(
    contract_api_client: PneumaticApiClient,
    workflow_action_owner: User,
    status: int,
    body: bytes,
) -> None:
    owner = workflow_action_owner
    workflow = create_test_workflow(owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    service = WorkflowActionService(user=owner, workflow=workflow)
    if status == WorkflowStatus.DELAYED:
        service.force_delay_workflow(timezone.now() + timedelta(days=1))
    elif status == WorkflowStatus.DONE:
        service.force_complete_workflow()
    workflow.refresh_from_db()
    task.refresh_from_db()
    assert workflow.status == status
    previous_status_updated = workflow.status_updated
    previous_date_started = task.date_started
    previous_events = workflow.events.count()
    delay = task.get_active_delay()
    if status == WorkflowStatus.DELAYED:
        assert task.status == TaskStatus.DELAYED
        assert delay is not None
    if status == WorkflowStatus.DONE:
        assert workflow.date_completed is not None

    response = contract_api_client.post(
        f'/workflows/{workflow.id}/resume', data=body,
        content_type='application/json',
    )

    assert response.status_code == 200
    workflow.refresh_from_db()
    task.refresh_from_db()
    assert workflow.status == WorkflowStatus.RUNNING
    assert workflow.date_completed is None
    assert task.status == TaskStatus.ACTIVE
    payload = response.json()
    assert payload['id'] == workflow.id
    assert payload['status'] == WorkflowStatus.RUNNING
    assert payload['date_completed_tsp'] is None
    assert payload['tasks'][0]['id'] == task.id
    assert payload['tasks'][0]['status'] == TaskStatus.ACTIVE
    assert payload['tasks'][0]['delay'] is None
    if status == WorkflowStatus.DELAYED:
        delay.refresh_from_db()
        assert delay.end_date is not None
        assert delay.end_date >= delay.start_date
        assert task.date_started >= previous_date_started
    elif status == WorkflowStatus.RUNNING:
        assert workflow.status_updated == previous_status_updated
        assert task.date_started == previous_date_started
        assert workflow.events.count() == previous_events
        repeated = contract_api_client.post(
            f'/workflows/{workflow.id}/resume', data=body,
            content_type='application/json',
        )
        assert repeated.status_code == 200
        assert repeated.json() == payload
        assert workflow.events.count() == previous_events


def test_resume__skip_for_starter__advances_with_real_services(
    contract_api_client: PneumaticApiClient,
    workflow_action_owner: User,
) -> None:
    owner = workflow_action_owner
    template = create_test_template(owner, is_active=True, tasks_count=2)
    first_template_task = template.tasks.get(number=1)
    first_template_task.skip_for_starter = True
    first_template_task.require_completion_by_all = True
    first_template_task.save(update_fields=[
        'skip_for_starter', 'require_completion_by_all',
    ])
    workflow = create_test_workflow(owner, template=template)
    first = workflow.tasks.get(number=1)
    second = workflow.tasks.get(number=2)
    WorkflowActionService(user=owner, workflow=workflow).force_delay_workflow(
        timezone.now() + timedelta(days=1),
    )
    delay = first.get_active_delay()

    response = contract_api_client.post(f'/workflows/{workflow.id}/resume')

    assert response.status_code == 200
    workflow.refresh_from_db()
    first.refresh_from_db()
    second.refresh_from_db()
    delay.refresh_from_db()
    assert workflow.status == WorkflowStatus.RUNNING
    assert workflow.date_completed is None
    assert first.status == TaskStatus.SKIPPED
    assert second.status == TaskStatus.ACTIVE
    assert second.date_started is not None
    assert delay.end_date is not None
    tasks = {row['id']: row for row in response.json()['tasks']}
    assert set(tasks) == {second.id}
    assert tasks[second.id]['status'] == TaskStatus.ACTIVE


@pytest.mark.parametrize('method,path', ACTION_ROUTES)
def test_workflow_action__missing_resource__real_not_found(
    contract_api_client: PneumaticApiClient,
    workflow_action_owner: User,
    method: str,
    path: str,
) -> None:
    response = getattr(contract_api_client, method)(
        path.format(id=2147483647),
    )

    assert response.status_code == 404
    assert isinstance(response.json()['detail'], str)


@pytest.mark.parametrize('method,path', ACTION_ROUTES)
def test_workflow_action__unauthenticated__denies_before_mutation(
    contract_api_client: PneumaticApiClient,
    workflow_action_owner: User,
    method: str,
    path: str,
) -> None:
    workflow = create_test_workflow(workflow_action_owner, tasks_count=1)
    contract_api_client.credentials()

    response = getattr(contract_api_client, method)(
        path.format(id=workflow.id),
    )

    assert response.status_code == 401
    workflow.refresh_from_db()
    assert workflow.is_deleted is False
    assert workflow.status == WorkflowStatus.RUNNING
    assert workflow.tasks.count() == 1


@pytest.mark.parametrize('denial', ['non_owner', 'no_plan', 'expired'])
@pytest.mark.parametrize('method,path', ACTION_ROUTES)
def test_workflow_action__permissions__denies_before_mutation(
    contract_api_client: PneumaticApiClient,
    workflow_action_environment: None,
    method: str,
    path: str,
    denial: str,
) -> None:
    account = create_test_account(
        plan=None if denial == 'no_plan' else BillingPlanType.UNLIMITED,
        plan_expiration=(
            timezone.now() - timedelta(days=1) if denial == 'expired' else None
        ),
        billing_sync=False,
    )
    owner = create_test_owner(account=account)
    caller = create_test_admin(
        account=account, email='unrelated-admin@example.test',
    ) if denial == 'non_owner' else owner
    workflow = create_test_workflow(owner, tasks_count=1)
    contract_api_client.token_authenticate(caller)

    response = getattr(contract_api_client, method)(
        path.format(id=workflow.id),
    )

    assert response.status_code == 403
    workflow.refresh_from_db()
    assert workflow.is_deleted is False
    assert workflow.status == WorkflowStatus.RUNNING
    assert workflow.tasks.count() == 1


@pytest.mark.parametrize('method,path,success', OPERATIONS)
def test_workflow_action__schema__omits_unreachable_bad_request_and_body(
    http_contract: HttpContract, method: str, path: str, success: str,
) -> None:
    operation = http_contract.document['paths'][path][method]

    assert set(operation['responses']) == {success, '401', '403', '404'}
    assert 'requestBody' not in operation


@pytest.mark.parametrize('case', MOCKED_WORKFLOW_ACTION_CASES)
def test_workflow_action__mocked_error__excluded_from_contract_registry(
    pytestconfig: Any, case: str,
) -> None:
    assert case not in pytestconfig._api_contract_cases
