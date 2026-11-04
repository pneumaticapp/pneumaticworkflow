"""Real missing-resource lookups and gates that deny before object lookup."""

from django.contrib.auth import get_user_model
import pytest

from src.accounts.enums import BillingPlanType, LeaseLevel
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.processes.enums import PresetType
from src.processes.models.workflows.task import TaskPerformer
from src.processes.services.events import WorkflowEventService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_guest,
    create_test_owner,
    create_test_template,
    create_test_template_preset,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db
UserModel = get_user_model()
MISSING_ID = 2147483647

NOT_FOUND_OPERATIONS = (
    ('get', '/accounts/groups/{id}', {}),
    ('put', '/accounts/groups/{id}', {'name': 'Missing group'}),
    ('delete', '/accounts/groups/{id}', {}),
    ('post', '/accounts/invites/{id}/accept', {'password': 'Password-123'}),
    ('get', '/accounts/users/{id}', {}),
    ('patch', '/accounts/users/{id}', {'first_name': 'Missing user'}),
    ('post', '/accounts/users/{id}/activate-vacation', {}),
    ('post', '/accounts/users/{id}/deactivate-vacation', {}),
    ('get', '/accounts/users/{id}/api-keys', {}),
    ('post', '/datasets/{id}/items', [{'value': 'New item', 'order': 0}]),
    ('get', '/reports/dashboard/tasks/by-steps', {
        'template_id': MISSING_ID, 'now': True,
    }),
    ('get', '/templates/{id}/fields', {}),
    ('post', '/templates/{id}/preset', {
        'name': 'Missing template preset',
        'type': PresetType.PERSONAL, 'fields': [],
    }),
    ('get', '/templates/{id}/presets', {}),
    ('post', '/templates/{id}/run', {'name': 'Missing template workflow'}),
    ('post', '/templates/system/{id}/fill', {}),
    ('post', '/v2/tasks/{id}/complete', {'output': {}}),
    ('delete', '/v2/tasks/{id}/due-date', {}),
    ('post', '/v2/tasks/{id}/revert', {'comment': 'Missing task'}),
    ('post', '/v2/tasks/checklists/{id}/mark', {'selection_id': 1}),
    ('post', '/v2/tasks/checklists/{id}/unmark', {'selection_id': 1}),
)

PRESET_OPERATIONS = (
    ('put', '/templates/presets/{id}'),
    ('patch', '/templates/presets/{id}'),
    ('delete', '/templates/presets/{id}'),
    ('post', '/templates/presets/{id}/default'),
)
COMMENT_OPERATIONS = (
    ('patch', '/workflows/comments/{id}'),
    ('delete', '/workflows/comments/{id}'),
    ('post', '/workflows/comments/{id}/create-reaction'),
    ('post', '/workflows/comments/{id}/delete-reaction'),
    ('post', '/workflows/comments/{id}/watched'),
)
PUBLIC_OPERATIONS = (
    ('get', '/templates/public'),
    ('post', '/templates/public/run'),
)
TENANT_OPERATIONS = (
    ('patch', '/tenants/{id}'),
    ('delete', '/tenants/{id}'),
    ('get', '/tenants/{id}/token'),
)


@pytest.fixture
def missing_resource_owner(contract_api_client) -> UserModel:
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED, billing_sync=False,
    )
    owner = create_test_owner(account=account)
    contract_api_client.token_authenticate(owner)
    return owner


@pytest.mark.parametrize('method,path,payload', NOT_FOUND_OPERATIONS)
def test_missing_resource__real_lookup__not_found(
    contract_api_client, missing_resource_owner, method, path, payload,
) -> None:
    response = getattr(contract_api_client, method)(
        path.format(id=MISSING_ID), data=payload, format='json',
    )

    assert response.status_code == 404
    assert set(response.json()) == {'detail'}


@pytest.mark.parametrize('scope', ['missing', 'foreign', 'deleted'])
@pytest.mark.parametrize('method,path', PRESET_OPERATIONS)
def test_inaccessible_preset__permission_gate__forbidden(
    contract_api_client, missing_resource_owner, method, path, scope,
) -> None:
    owner = missing_resource_owner
    preset_id = MISSING_ID
    if scope != 'missing':
        author = owner if scope == 'deleted' else create_test_owner(
            account=create_test_account(billing_sync=False),
            email='foreign-preset-owner@example.test',
        )
        template = create_test_template(author, is_active=True, tasks_count=1)
        preset = create_test_template_preset(template, author)
        preset_id = preset.id
        if scope == 'deleted':
            preset.delete()

    response = getattr(contract_api_client, method)(
        path.format(id=preset_id),
        data={'name': 'Updated', 'type': PresetType.PERSONAL, 'fields': []},
        format='json',
    )

    assert response.status_code == 403


@pytest.mark.parametrize('scope', [
    'missing', 'foreign', 'deleted', 'noncomment',
])
@pytest.mark.parametrize('method,path', COMMENT_OPERATIONS)
def test_inaccessible_comment__permission_gate__forbidden(
    contract_api_client, missing_resource_owner, method, path, scope,
) -> None:
    owner = missing_resource_owner
    comment_id = MISSING_ID
    if scope != 'missing':
        author = owner if scope != 'foreign' else create_test_owner(
            account=create_test_account(billing_sync=False),
            email='foreign-comment-owner@example.test',
        )
        workflow = create_test_workflow(author, tasks_count=1)
        task = workflow.tasks.first()
        if scope == 'noncomment':
            event = WorkflowEventService.task_started_event(
                task=task, after_create_actions=False,
            )
        else:
            event = WorkflowEventService.comment_created_event(
                text='Contract comment', task=task, user=author,
                after_create_actions=False,
            )
        comment_id = event.id
        if scope == 'deleted':
            event.delete()

    response = getattr(contract_api_client, method)(
        path.format(id=comment_id),
        data={'text': 'Updated', 'value': 'like'}, format='json',
    )

    assert response.status_code == 403


@pytest.mark.parametrize('state', ['deleted', 'inactive'])
@pytest.mark.parametrize('method,path', PUBLIC_OPERATIONS)
def test_unavailable_public_template__real_token__unauthorized(
    contract_api_client, missing_resource_owner, method, path, state,
) -> None:
    template = create_test_template(
        missing_resource_owner, is_active=True, is_public=True, tasks_count=1,
    )
    token = template.public_id
    if state == 'deleted':
        template.delete()
    else:
        template.is_active = False
        template.save(update_fields=['is_active'])
    contract_api_client.credentials(
        HTTP_X_PUBLIC_AUTHORIZATION=f'Token {token}',
    )

    response = getattr(contract_api_client, method)(
        path, data={'fields': {}}, format='json',
    )

    assert response.status_code == 401


@pytest.mark.parametrize('scope', ['missing', 'foreign', 'deleted'])
@pytest.mark.parametrize('method,path', TENANT_OPERATIONS)
def test_inaccessible_tenant__master_access_gate__forbidden(
    contract_api_client, missing_resource_owner, method, path, scope,
) -> None:
    owner = missing_resource_owner
    tenant_id = MISSING_ID
    if scope != 'missing':
        master = owner.account if scope == 'deleted' else create_test_account(
            plan=BillingPlanType.UNLIMITED, billing_sync=False,
        )
        tenant = create_test_account(
            master_account=master, lease_level=LeaseLevel.TENANT,
            plan=BillingPlanType.UNLIMITED, billing_sync=False,
        )
        tenant_id = tenant.id
        if scope == 'deleted':
            tenant.delete()

    response = getattr(contract_api_client, method)(
        path.format(id=tenant_id),
        data={'tenant_name': 'Updated tenant'}, format='json',
    )

    assert response.status_code == 403


@pytest.mark.parametrize('level', [LeaseLevel.STANDARD, LeaseLevel.PARTNER])
@pytest.mark.parametrize('method,path', TENANT_OPERATIONS)
def test_related_non_tenant__queryset_scope__not_found(
    contract_api_client, missing_resource_owner, method, path, level,
) -> None:
    account = create_test_account(
        master_account=missing_resource_owner.account, lease_level=level,
        plan=BillingPlanType.UNLIMITED, billing_sync=False,
    )
    create_test_owner(account=account, email='related-owner@example.test')
    related = missing_resource_owner.account.tenants
    assert related.filter(id=account.id).exists()
    assert not missing_resource_owner.account.tenants.only_tenants().filter(
        id=account.id,
    ).exists()

    response = getattr(contract_api_client, method)(
        path.format(id=account.id),
        data={'tenant_name': 'Updated tenant'}, format='json',
    )

    assert response.status_code == 404


@pytest.mark.parametrize('scope', ['missing', 'foreign', 'deleted'])
def test_inaccessible_workflow_comment__permission_gate__forbidden(
    contract_api_client, missing_resource_owner, scope,
) -> None:
    workflow_id = MISSING_ID
    if scope != 'missing':
        owner = (
            missing_resource_owner if scope == 'deleted'
            else create_test_owner(
                account=create_test_account(billing_sync=False),
                email='foreign-workflow-owner@example.test',
            )
        )
        workflow = create_test_workflow(owner, tasks_count=1)
        workflow_id = workflow.id
        if scope == 'deleted':
            workflow.delete()

    response = contract_api_client.post(
        f'/workflows/{workflow_id}/comment',
        data={'text': 'Missing workflow'}, format='json',
    )

    assert response.status_code == 403


def test_guest_workflow_comment__missing_workflow__forbidden(
    contract_api_client, missing_resource_owner,
) -> None:
    owner = missing_resource_owner
    guest = create_test_guest(account=owner.account)
    workflow = create_test_workflow(owner, tasks_count=1)
    task = workflow.tasks.first()
    TaskPerformer.objects.create(task=task, user=guest)
    token = GuestJWTAuthService.get_str_token(
        task_id=task.id, user_id=guest.id, account_id=owner.account_id,
    )
    contract_api_client.credentials(HTTP_X_GUEST_AUTHORIZATION=token)
    accessible = contract_api_client.get(f'/v2/tasks/{task.id}')
    assert accessible.status_code == 200

    response = contract_api_client.post(
        f'/workflows/{MISSING_ID}/comment',
        data={'text': 'Missing workflow'}, format='json',
    )

    assert response.status_code == 403


@pytest.mark.parametrize('method,path', (
    *PRESET_OPERATIONS,
    *COMMENT_OPERATIONS,
    *PUBLIC_OPERATIONS,
    ('post', '/workflows/{id}/comment'),
))
def test_permission_gated_operation__response_schema_omits_unreachable_404(
    http_contract, method, path,
) -> None:
    responses = http_contract.document['paths'][path][method]['responses']
    assert '404' not in responses
