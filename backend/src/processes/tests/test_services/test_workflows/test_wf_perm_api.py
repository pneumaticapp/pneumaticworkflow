"""
API-level tests for Guardian permission enforcement.

Webhook, workflow retrieve, task retrieve, workflow terminate (DELETE).
"""

import pytest

from src.permissions.enums import PermissionSource
from src.processes.services.workflow_permissions import (
    WorkflowPermissionService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_webhook_wf__non_manager__404(api_client):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(
        account=account, email='admin@test.test',
    )
    create_test_workflow(user=owner, tasks_count=1)
    api_client.token_authenticate(admin)

    # act
    resp = api_client.get('/workflows/webhook-example')

    # assert
    assert resp.status_code == 404


def test_webhook_wf__manager__200(api_client):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(
        account=account, email='admin@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService(
        workflow=workflow,
    ).grant_change(
        user=admin,
        source_type=PermissionSource.TEMPLATE_OWNER,
        source_id='0',
    )
    api_client.token_authenticate(admin)

    # act
    resp = api_client.get('/workflows/webhook-example')

    # assert
    assert resp.status_code == 200
    assert resp.data['workflow']['id'] == workflow.id


def test_webhook_task__manager__200(api_client):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    WorkflowPermissionService(
        workflow=workflow,
    ).grant_change(
        user=owner,
        source_type=PermissionSource.TEMPLATE_OWNER,
        source_id='0',
    )
    api_client.token_authenticate(owner)

    # act
    resp = api_client.get('/v2/tasks/webhook-example')

    # assert
    assert resp.status_code == 200


def test_webhook_task__non_manager__404(api_client):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    non_mgr = create_test_admin(account=account)
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    create_test_workflow(user=owner, template=template)
    api_client.token_authenticate(non_mgr)

    # act
    resp = api_client.get('/v2/tasks/webhook-example')

    # assert
    assert resp.status_code == 404


def test_wf_retrieve__viewer__200(api_client):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account, email='v@t.t',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    template.tasks.first().add_raw_performer(viewer)
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    WorkflowPermissionService(workflow).set_viewers()
    api_client.token_authenticate(viewer)

    # act
    resp = api_client.get(f'/workflows/{workflow.id}')

    # assert
    assert resp.status_code == 200
    assert resp.data['id'] == workflow.id


def test_wf_retrieve__stranger__404(api_client):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    stranger = create_test_not_admin(
        account=account, email='s@t.t',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    api_client.token_authenticate(stranger)

    # act
    resp = api_client.get(f'/workflows/{workflow.id}')

    # assert — DRF returns 403 (permission denied)
    # because the queryset finds the workflow (same account)
    # but WorkflowMemberOrViewerPermission denies access.
    assert resp.status_code == 403


def test_task_retrieve__viewer__200(api_client):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account, email='v@t.t',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    template.tasks.first().add_raw_performer(viewer)
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    WorkflowPermissionService(workflow).set_viewers()
    task = workflow.tasks.first()
    api_client.token_authenticate(viewer)

    # act
    resp = api_client.get(f'/v2/tasks/{task.id}')

    # assert
    assert resp.status_code == 200


def test_task_retrieve__stranger__404(api_client):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    stranger = create_test_not_admin(
        account=account, email='s@t.t',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    api_client.token_authenticate(stranger)

    # act
    resp = api_client.get(f'/v2/tasks/{task.id}')

    # assert — 403 from TaskWorkflowMemberOrViewerPermission
    assert resp.status_code == 403


def test_wf_terminate__admin_manager__204(
    mocker,
    api_client,
):
    # arrange
    terminate_workflow_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.terminate_workflow',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    WorkflowPermissionService(
        workflow=workflow,
    ).grant_change(
        user=admin,
        source_type=PermissionSource.TEMPLATE_OWNER,
        source_id='0',
    )
    api_client.token_authenticate(admin)

    # act
    resp = api_client.delete(f'/workflows/{workflow.id}')

    # assert
    assert resp.status_code == 204
    terminate_workflow_mock.assert_called_once_with()


def test_wf_terminate__admin_no_manage__403(
    mocker,
    api_client,
):
    # arrange
    terminate_workflow_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.terminate_workflow',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    api_client.token_authenticate(admin)

    # act
    resp = api_client.delete(f'/workflows/{workflow.id}')

    # assert
    assert resp.status_code == 403
    terminate_workflow_mock.assert_not_called()


def test_wf_terminate__non_admin__403(
    mocker,
    api_client,
):
    # arrange
    terminate_workflow_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.terminate_workflow',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    regular = create_test_not_admin(
        account=account, email='r@t.t',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    WorkflowPermissionService(
        workflow=workflow,
    ).grant_change(
        user=regular,
        source_type=PermissionSource.TEMPLATE_OWNER,
        source_id='0',
    )
    api_client.token_authenticate(regular)

    # act
    resp = api_client.delete(f'/workflows/{workflow.id}')

    # assert
    assert resp.status_code == 403
    terminate_workflow_mock.assert_not_called()
