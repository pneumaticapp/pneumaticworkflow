"""
Unit tests for WorkflowPermissionService write/read ops:
set_owners, grant_view, grant_manage, grant_view_bulk,
read helpers, queryset filters, and edge cases.
"""

import pytest

from src.processes.enums import WorkflowStatus
from src.processes.models.workflows.workflow import Workflow
from src.processes.models.workflows.task import Task
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
from src.processes.tests.guardian_helpers import (
    assert_guardian_viewer_count,
)

pytestmark = pytest.mark.django_db


# -- set_owners


def test_set_owners__grants_manage_and_view():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    new_owner = create_test_admin(
        account=account, email='newowner@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner, template=template,
    )

    # act
    WorkflowPermissionService.set_owners(
        workflow=workflow, user_ids=[new_owner.id],
    )

    # assert
    assert WorkflowPermissionService.has_manage(
        user=new_owner, workflow=workflow,
    )
    assert WorkflowPermissionService.has_view(
        user=new_owner, workflow=workflow,
    )


def test_set_owners__replaces_previous():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    new_owner = create_test_admin(
        account=account, email='newowner@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    assert WorkflowPermissionService.has_manage(
        user=owner, workflow=workflow,
    )

    # act
    WorkflowPermissionService.set_owners(
        workflow=workflow, user_ids=[new_owner.id],
    )

    # assert
    assert not WorkflowPermissionService.has_manage(
        user=owner, workflow=workflow,
    )
    assert WorkflowPermissionService.has_manage(
        user=new_owner, workflow=workflow,
    )


def test_set_owners__empty__clears_all():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    assert WorkflowPermissionService.has_manage(
        user=owner, workflow=workflow,
    )

    # act
    WorkflowPermissionService.set_owners(workflow=workflow, user_ids=[])

    # assert
    assert not WorkflowPermissionService.has_manage(
        user=owner, workflow=workflow,
    )
    assert not WorkflowPermissionService.get_owner_ids(workflow=workflow)


def test_set_owners__duplicate_ids__deduped():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    WorkflowPermissionService.set_owners(
        workflow=workflow, user_ids=[owner.id, owner.id, owner.id],
    )

    # assert
    owner_ids = WorkflowPermissionService.get_owner_ids(workflow=workflow)
    assert owner_ids == [owner.id]
    assert WorkflowPermissionService.has_manage(
        user=owner, workflow=workflow,
    )


# -- grant_view_bulk


def test_grant_view_bulk__multiple_users():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user_a = create_test_admin(
        account=account, email='a@test.test',
    )
    user_b = create_test_not_admin(
        account=account, email='b@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    WorkflowPermissionService.grant_view_bulk(
        user_ids=[user_a.id, user_b.id], workflow=workflow,
    )

    # assert
    assert WorkflowPermissionService.has_view(
        user=user_a, workflow=workflow,
    )
    assert WorkflowPermissionService.has_view(
        user=user_b, workflow=workflow,
    )


def test_grant_view_bulk__empty__noop():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    WorkflowPermissionService.grant_view_bulk(user_ids=[], workflow=workflow)

    # assert
    assert WorkflowPermissionService.has_view(user=owner, workflow=workflow)


def test_grant_view_bulk__idempotent():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    WorkflowPermissionService.grant_view_bulk(
        user_ids=[owner.id], workflow=workflow,
    )
    WorkflowPermissionService.grant_view_bulk(
        user_ids=[owner.id], workflow=workflow,
    )

    # assert
    assert_guardian_viewer_count(workflow=workflow, expected_count=1)


# -- grant_view / grant_manage


def test_grant_view__gives_view_not_manage():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(
        account=account, email='user@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    WorkflowPermissionService.grant_view(user=user, workflow=workflow)

    # assert
    assert WorkflowPermissionService.has_view(
        user=user, workflow=workflow,
    )
    assert not WorkflowPermissionService.has_manage(
        user=user, workflow=workflow,
    )


def test_grant_manage__gives_both():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(
        account=account, email='user@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    WorkflowPermissionService.grant_manage(user=user, workflow=workflow)

    # assert
    assert WorkflowPermissionService.has_view(
        user=user, workflow=workflow,
    )
    assert WorkflowPermissionService.has_manage(
        user=user, workflow=workflow,
    )


def test_grant_manage__idempotent():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    WorkflowPermissionService.grant_manage(user=admin, workflow=workflow)
    WorkflowPermissionService.grant_manage(user=admin, workflow=workflow)

    # assert
    assert WorkflowPermissionService.has_manage(
        user=admin, workflow=workflow,
    )
    owner_ids = WorkflowPermissionService.get_owner_ids(workflow=workflow)
    assert owner_ids.count(admin.id) == 1


# -- read helpers


def test_has_view__true_for_viewer():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    result = WorkflowPermissionService.has_view(
        user=owner, workflow=workflow,
    )

    # assert
    assert result is True


def test_has_view__false_for_stranger():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    stranger = create_test_not_admin(
        account=account, email='stranger@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    result = WorkflowPermissionService.has_view(
        user=stranger, workflow=workflow,
    )

    # assert
    assert result is False


def test_has_manage__true_for_manager():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    result = WorkflowPermissionService.has_manage(
        user=owner, workflow=workflow,
    )

    # assert
    assert result is True


def test_has_manage__false_for_viewer_only():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account, email='viewer@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService.grant_view(user=viewer, workflow=workflow)

    # act
    result = WorkflowPermissionService.has_manage(
        user=viewer, workflow=workflow,
    )

    # assert
    assert result is False


def test_get_viewer_ids__returns_all():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    extra = create_test_admin(
        account=account, email='extra@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService.grant_view(user=extra, workflow=workflow)

    # act
    viewer_ids = WorkflowPermissionService.get_viewer_ids(workflow=workflow)

    # assert
    assert owner.id in viewer_ids
    assert extra.id in viewer_ids


def test_get_owner_ids__returns_sorted():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    co_owner = create_test_admin(
        account=account, email='coowner@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService.grant_manage(user=co_owner, workflow=workflow)

    # act
    owner_ids = WorkflowPermissionService.get_owner_ids(workflow=workflow)

    # assert
    assert owner.id in owner_ids
    assert co_owner.id in owner_ids
    assert owner_ids == sorted(owner_ids)


def test_get_owner_ids__empty_when_no_managers():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService.set_owners(workflow=workflow, user_ids=[])

    # act
    owner_ids = WorkflowPermissionService.get_owner_ids(workflow=workflow)

    # assert
    assert not owner_ids


# -- queryset filters (viewer_q / manager_q)


def test_viewer_q__returns_permitted():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    qs = Workflow.objects.filter(
        WorkflowPermissionService.viewer_q(user_id=owner.id),
    )

    # assert
    assert qs.filter(pk=workflow.pk).exists()


def test_viewer_q__excludes_unpermitted():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    outsider = create_test_admin(
        account=account, email='outsider@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    qs = Workflow.objects.filter(
        WorkflowPermissionService.viewer_q(user_id=outsider.id),
    )

    # assert
    assert not qs.filter(pk=workflow.pk).exists()


def test_manager_q__returns_managed():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    qs = Workflow.objects.filter(
        WorkflowPermissionService.manager_q(user_id=owner.id),
    )

    # assert
    assert qs.filter(pk=workflow.pk).exists()


def test_manager_q__excludes_viewer_only():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account, email='viewer@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService.grant_view(user=viewer, workflow=workflow)

    # act
    qs = Workflow.objects.filter(
        WorkflowPermissionService.manager_q(user_id=viewer.id),
    )

    # assert
    assert not qs.filter(pk=workflow.pk).exists()


def test_viewer_q__custom_pk_field():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    qs = Task.objects.filter(
        WorkflowPermissionService.viewer_q(
            user_id=owner.id, pk_field='workflow_id',
        ),
    )

    # assert
    assert qs.filter(workflow=workflow).exists()


def test_viewer_q__no_perms__empty():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    stranger = create_test_not_admin(
        account=account, email='s@t.t',
    )
    create_test_workflow(user=owner, tasks_count=1)

    # act
    qs = Workflow.objects.on_account(account_id=account.id).filter(
        WorkflowPermissionService.viewer_q(user_id=stranger.id),
    )

    # assert
    assert not qs.exists()


def test_manager_q__task_workflow_id_field():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    wf_1 = create_test_workflow(user=owner, tasks_count=1)
    wf_2 = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService.grant_manage(user=admin, workflow=wf_1)

    # act
    qs = Task.objects.on_account(account_id=account.id).filter(
        WorkflowPermissionService.manager_q(
            user_id=admin.id, pk_field='workflow_id',
        ),
    )

    # assert
    wf_ids = set(qs.values_list('workflow_id', flat=True))
    assert wf_1.pk in wf_ids
    assert wf_2.pk not in wf_ids


# -- manage revoke preserves view


def test_set_owners__clears_manage_preserves_view():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    template.tasks.first().add_raw_performer(user=admin)
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    WorkflowPermissionService.set_viewers(workflow=workflow)
    WorkflowPermissionService.grant_manage(user=admin, workflow=workflow)

    # act
    WorkflowPermissionService.set_owners(
        workflow=workflow, user_ids=[owner.id],
    )
    WorkflowPermissionService.set_viewers(workflow=workflow)

    # assert
    assert not WorkflowPermissionService.has_manage(
        user=admin, workflow=workflow,
    )
    assert WorkflowPermissionService.has_view(
        user=admin, workflow=workflow,
    )


def test_set_owners__clears_both_for_non_performer():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService.grant_manage(user=admin, workflow=workflow)

    # act
    WorkflowPermissionService.set_owners(
        workflow=workflow, user_ids=[owner.id],
    )
    WorkflowPermissionService.set_viewers(workflow=workflow)

    # assert
    assert not WorkflowPermissionService.has_manage(
        user=admin, workflow=workflow,
    )
    assert not WorkflowPermissionService.has_view(
        user=admin, workflow=workflow,
    )


# -- permissions persist after completion


def test_view__persists_after_done():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(
        account=account, email='u@t.t',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    template.tasks.first().add_raw_performer(user=user)
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    WorkflowPermissionService.set_viewers(workflow=workflow)
    workflow.status = WorkflowStatus.DONE
    workflow.save(update_fields=['status'])

    # act
    result = WorkflowPermissionService.has_view(
        user=user, workflow=workflow,
    )

    # assert
    assert result is True


def test_manage__persists_after_done():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService.grant_manage(user=owner, workflow=workflow)
    workflow.status = WorkflowStatus.DONE
    workflow.save(update_fields=['status'])

    # act
    result = WorkflowPermissionService.has_manage(
        user=owner, workflow=workflow,
    )

    # assert
    assert result is True


# -- rapid permission toggle


def test_toggle__grant_revoke_grant__view_ok():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(
        account=account, email='u@t.t',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    WorkflowPermissionService.grant_view(user=user, workflow=workflow)
    WorkflowPermissionService.set_viewers(workflow=workflow)

    assert not WorkflowPermissionService.has_view(user=user, workflow=workflow)

    WorkflowPermissionService.grant_view(user=user, workflow=workflow)

    # assert
    assert WorkflowPermissionService.has_view(user=user, workflow=workflow)


def test_toggle__owners_empty_then_restore():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService.grant_manage(user=owner, workflow=workflow)
    WorkflowPermissionService.set_owners(workflow=workflow, user_ids=[])
    assert not WorkflowPermissionService.has_manage(
        user=owner, workflow=workflow,
    )

    # act
    WorkflowPermissionService.set_owners(
        workflow=workflow, user_ids=[owner.id],
    )

    # assert
    assert WorkflowPermissionService.has_manage(
        user=owner, workflow=workflow,
    )


# -- multiple workflows independence


def test_set_owners_on_wf1__no_effect_on_wf2():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    wf_1 = create_test_workflow(user=owner, tasks_count=1)
    wf_2 = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService.grant_manage(user=admin, workflow=wf_1)
    WorkflowPermissionService.grant_manage(user=admin, workflow=wf_2)

    # act
    WorkflowPermissionService.set_owners(
        workflow=wf_1, user_ids=[owner.id],
    )

    # assert
    assert not WorkflowPermissionService.has_manage(
        user=admin, workflow=wf_1,
    )
    assert WorkflowPermissionService.has_manage(
        user=admin, workflow=wf_2,
    )
