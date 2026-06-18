"""
Unit tests for DRF permission classes that use
WorkflowPermissionService (Guardian-based).
"""

import pytest
from unittest.mock import MagicMock

from src.accounts.enums import UserType
from src.processes.enums import (
    CommentStatus,
    DirectlyStatus,
    WorkflowEventType,
)
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.models.workflows.workflow import Workflow
from src.processes.permissions import (
    CommentReactionPermission,
    TaskCommentPermission,
    TaskWorkflowMemberOrViewerPermission,
    TaskWorkflowMemberPermission,
    TaskWorkflowOwnerPermission,
    TemplateFieldsPermission,
    WorkflowCommentPermission,
    WorkflowMemberOrViewerPermission,
    WorkflowMemberPermission,
    WorkflowOwnerPermission,
)
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


def _req(user):
    r = MagicMock()
    r.user = user
    return r


def _vw(**kwargs):
    v = MagicMock()
    v.kwargs = {k: str(val) for k, val in kwargs.items()}
    return v


# ── WorkflowOwnerPermission ──────────────────────────────


def test_wf_owner_perm__account_owner__allowed():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    perm = WorkflowOwnerPermission()

    # act
    result = perm.has_permission(
        _req(owner), _vw(pk=workflow.pk),
    )

    # assert
    assert result is True


def test_wf_owner_perm__admin_manager__allowed():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(
        account=account, email='mgr@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    WorkflowPermissionService.grant_manage(user=admin, workflow=workflow)
    perm = WorkflowOwnerPermission()

    # act
    result = perm.has_permission(
        _req(admin), _vw(pk=workflow.pk),
    )

    # assert
    assert result is True


def test_wf_owner_perm__non_admin__denied():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    non_admin = create_test_not_admin(
        account=account, email='nonadmin@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService.grant_manage(
        user=non_admin, workflow=workflow,
    )
    perm = WorkflowOwnerPermission()

    # act
    result = perm.has_permission(
        _req(non_admin), _vw(pk=workflow.pk),
    )

    # assert
    assert result is False


def test_wf_owner_perm__admin_no_manage__denied():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(
        account=account, email='admin@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    perm = WorkflowOwnerPermission()

    # act
    result = perm.has_permission(
        _req(admin), _vw(pk=workflow.pk),
    )

    # assert
    assert result is False


# ── WorkflowMemberPermission ─────────────────────────────


def test_wf_member_perm__mentioned__allowed():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    mentioned = create_test_not_admin(
        account=account, email='m@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text=f'[User| {mentioned.id}]',
        status=CommentStatus.CREATED,
    )
    WorkflowPermissionService.set_viewers(workflow=workflow)
    perm = WorkflowMemberPermission()

    # act
    result = perm.has_permission(
        _req(mentioned), _vw(pk=workflow.pk),
    )

    # assert
    assert result is True


def test_wf_member_perm__stranger__denied():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    stranger = create_test_not_admin(
        account=account, email='s@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    perm = WorkflowMemberPermission()

    # act
    result = perm.has_permission(
        _req(stranger), _vw(pk=workflow.pk),
    )

    # assert
    assert result is False


def test_wf_member_perm__revoked__still_matches():
    """
    Known gap: WorkflowMemberPermission checks
    Q(tasks__taskperformer__user_id=...) WITHOUT filtering
    directly_status=DELETED. Guardian view is revoked, but
    the Q-based performer check still matches.
    TODO: Fix WorkflowMemberPermission to exclude deleted
    performers, then change this assertion to False.
    """
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    performer = create_test_not_admin(
        account=account, email='p@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    template.tasks.first().add_raw_performer(user=performer)
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    WorkflowPermissionService.set_viewers(workflow=workflow)
    task = workflow.tasks.first()
    task.taskperformer_set.filter(user=performer).update(
        directly_status=DirectlyStatus.DELETED,
    )
    WorkflowPermissionService.set_viewers(workflow=workflow)
    perm = WorkflowMemberPermission()

    # act
    result = perm.has_permission(
        _req(performer), _vw(pk=workflow.pk),
    )

    # assert — matches current behavior (see docstring)
    assert result is True


# ── TaskWorkflowOwnerPermission ───────────────────────────


def test_task_wf_owner__account_owner__allowed():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    perm = TaskWorkflowOwnerPermission()

    # act
    result = perm.has_permission(
        _req(owner), _vw(pk=task.pk),
    )

    # assert
    assert result is True


def test_task_wf_owner__admin_manager__allowed():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(
        account=account, email='admin@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    task = workflow.tasks.first()
    WorkflowPermissionService.grant_manage(user=admin, workflow=workflow)
    perm = TaskWorkflowOwnerPermission()

    # act
    result = perm.has_permission(
        _req(admin), _vw(pk=task.pk),
    )

    # assert
    assert result is True


def test_task_wf_owner__admin_no_manage__denied():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(
        account=account, email='admin@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    perm = TaskWorkflowOwnerPermission()

    # act
    result = perm.has_permission(
        _req(admin), _vw(pk=task.pk),
    )

    # assert
    assert result is False


# ── TaskWorkflowMemberPermission ──────────────────────────


def test_task_wf_member__viewer__allowed():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account, email='v@t.t',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    WorkflowPermissionService.grant_view(user=viewer, workflow=workflow)
    perm = TaskWorkflowMemberPermission()

    # act
    result = perm.has_permission(
        _req(viewer), _vw(pk=task.pk),
    )

    # assert
    assert result is True


def test_task_wf_member__stranger__denied():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    stranger = create_test_not_admin(
        account=account, email='s@t.t',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    perm = TaskWorkflowMemberPermission()

    # act
    result = perm.has_permission(
        _req(stranger), _vw(pk=task.pk),
    )

    # assert
    assert result is False


# ── WorkflowMemberOrViewerPermission ─────────────────────


def test_wf_member_or_viewer__viewer__allowed():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account, email='v@t.t',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService.grant_view(user=viewer, workflow=workflow)
    perm = WorkflowMemberOrViewerPermission()

    # act
    result = perm.has_permission(
        _req(viewer), _vw(pk=workflow.pk),
    )

    # assert
    assert result is True


def test_wf_member_or_viewer__stranger__denied():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    stranger = create_test_not_admin(
        account=account, email='s@t.t',
    )
    wf = create_test_workflow(user=owner, tasks_count=1)
    perm = WorkflowMemberOrViewerPermission()

    # act
    result = perm.has_permission(
        _req(stranger), _vw(pk=wf.pk),
    )

    # assert
    assert result is False


# ── TaskWorkflowMemberOrViewerPermission ──────────────────


def test_task_wf_member_or_viewer__viewer__ok():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account, email='v2@t.t',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    WorkflowPermissionService.grant_view(user=viewer, workflow=workflow)
    perm = TaskWorkflowMemberOrViewerPermission()

    # act
    result = perm.has_permission(
        _req(viewer), _vw(pk=task.pk),
    )

    # assert
    assert result is True


def test_task_wf_member_or_viewer__stranger__denied():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    stranger = create_test_not_admin(
        account=account, email='s2@t.t',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    perm = TaskWorkflowMemberOrViewerPermission()

    # act
    result = perm.has_permission(
        _req(stranger), _vw(pk=task.pk),
    )

    # assert
    assert result is False


# ── TaskCommentPermission ─────────────────────────────────


def test_task_comment__mentioned__allowed():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account, email='v@t.t',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text=f'[User| {viewer.id}]',
        status=CommentStatus.CREATED,
    )
    WorkflowPermissionService.set_viewers(workflow=workflow)
    perm = TaskCommentPermission()

    # act
    result = perm.has_permission(
        _req(viewer), _vw(pk=task.pk),
    )

    # assert
    assert result is True


def test_task_comment__stranger__denied():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    stranger = create_test_not_admin(
        account=account, email='s@t.t',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    perm = TaskCommentPermission()

    # act
    result = perm.has_permission(
        _req(stranger), _vw(pk=task.pk),
    )

    # assert
    assert result is False


# ── WorkflowCommentPermission ─────────────────────────────


def test_wf_comment__mentioned__allowed():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account, email='v@t.t',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text=f'[User| {viewer.id}]',
        status=CommentStatus.CREATED,
    )
    WorkflowPermissionService.set_viewers(workflow=workflow)
    perm = WorkflowCommentPermission()

    # act
    result = perm.has_permission(
        _req(viewer), _vw(pk=workflow.pk),
    )

    # assert
    assert result is True


def test_wf_comment__stranger__denied():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    stranger = create_test_not_admin(
        account=account, email='s@t.t',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    perm = WorkflowCommentPermission()

    # act
    result = perm.has_permission(
        _req(stranger), _vw(pk=workflow.pk),
    )

    # assert
    assert result is False


# ── CommentReactionPermission ─────────────────────────────


def test_reaction__viewer__allowed():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account, email='v@t.t',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    comment = WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text='Hello',
        status=CommentStatus.CREATED,
    )
    WorkflowPermissionService.grant_view(user=viewer, workflow=workflow)
    perm = CommentReactionPermission()

    # act
    result = perm.has_permission(
        _req(viewer), _vw(pk=comment.pk),
    )

    # assert
    assert result is True


def test_reaction__stranger__denied():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    stranger = create_test_not_admin(
        account=account, email='s@t.t',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    comment = WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text='Hello',
        status=CommentStatus.CREATED,
    )
    perm = CommentReactionPermission()

    # act
    result = perm.has_permission(
        _req(stranger), _vw(pk=comment.pk),
    )

    # assert
    assert result is False


# ── TemplateFieldsPermission ──────────────────────────────


def test_tmpl_fields__viewer__allowed():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account, email='v@t.t',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    WorkflowPermissionService.grant_view(user=viewer, workflow=workflow)
    perm = TemplateFieldsPermission()

    # act
    result = perm.has_permission(
        _req(viewer), _vw(pk=template.pk),
    )

    # assert
    assert result is True


def test_tmpl_fields__stranger__denied():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    stranger = create_test_not_admin(
        account=account, email='s@t.t',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    create_test_workflow(user=owner, template=template)
    perm = TemplateFieldsPermission()

    # act
    result = perm.has_permission(
        _req(stranger), _vw(pk=template.pk),
    )

    # assert
    assert result is False


# ══ SECURITY: Account owner bypass ════════════════════════


def test_bypass__wf_owner_perm__no_guardian__ok():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService.set_owners(workflow=workflow, user_ids=[])
    perm = WorkflowOwnerPermission()

    # act
    result = perm.has_permission(
        _req(owner), _vw(pk=workflow.pk),
    )

    # assert
    assert result is True


def test_bypass__wf_member_perm__no_guardian__ok():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService.set_owners(workflow=workflow, user_ids=[])
    WorkflowPermissionService.set_viewers(workflow=workflow)
    perm = WorkflowMemberPermission()

    # act
    result = perm.has_permission(
        _req(owner), _vw(pk=workflow.pk),
    )

    # assert
    assert result is True


def test_bypass__task_wf_owner__no_guardian__ok():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    WorkflowPermissionService.set_owners(workflow=workflow, user_ids=[])
    perm = TaskWorkflowOwnerPermission()

    # act
    result = perm.has_permission(
        _req(owner), _vw(pk=task.pk),
    )

    # assert
    assert result is True


# ══ SECURITY: Guest bypass ════════════════════════════════


def test_guest__wf_member_perm__allowed():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    guest = MagicMock()
    guest.type = UserType.GUEST
    guest.is_account_owner = False
    guest.account_id = account.id
    perm = WorkflowMemberPermission()

    # act
    result = perm.has_permission(
        _req(guest), _vw(pk=workflow.pk),
    )

    # assert
    assert result is True


# ══ SECURITY: Cross-account isolation ═════════════════════


def test_cross_account__viewer__denied_by_filter():
    # arrange
    account_a = create_test_account()
    owner_a = create_test_owner(account=account_a)
    wf_a = create_test_workflow(user=owner_a, tasks_count=1)
    account_b = create_test_account()
    outsider = create_test_owner(
        account=account_b, email='outsider@test.test',
    )
    WorkflowPermissionService.grant_view(user=outsider, workflow=wf_a)

    # act
    qs = Workflow.objects.filter(
        pk=wf_a.pk,
        account_id=outsider.account_id,
    ).filter(
        WorkflowPermissionService.viewer_q(outsider.id),
    )

    # assert
    assert not qs.exists()


def test_cross_account__manager__denied_by_filter():
    # arrange
    account_a = create_test_account()
    owner_a = create_test_owner(account=account_a)
    wf_a = create_test_workflow(user=owner_a, tasks_count=1)
    account_b = create_test_account()
    outsider = create_test_owner(
        account=account_b, email='outsider@test.test',
    )
    WorkflowPermissionService.grant_manage(user=outsider, workflow=wf_a)

    # act
    qs = Workflow.objects.filter(
        pk=wf_a.pk,
        account_id=outsider.account_id,
    ).filter(
        WorkflowPermissionService.manager_q(outsider.id),
    )

    # assert
    assert not qs.exists()


# ══ SECURITY: Non-admin with manage denied ════════════════


def test_non_admin__with_manage__denied():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    regular = create_test_not_admin(
        account=account, email='r@t.t',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService.grant_manage(user=regular, workflow=workflow)
    perm = WorkflowOwnerPermission()

    # act
    result = perm.has_permission(
        _req(regular), _vw(pk=workflow.pk),
    )

    # assert
    assert result is False


# ══ EDGE: Invalid PK ═════════════════════════════════════


def test_wf_owner_perm__invalid_pk__denied():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    perm = WorkflowOwnerPermission()

    # act
    result = perm.has_permission(
        _req(owner), _vw(pk='abc'),
    )

    # assert
    assert result is False


def test_wf_owner_perm__nonexistent_pk__denied():
    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    admin = create_test_admin(
        account=account, email='admin@test.test',
    )
    perm = WorkflowOwnerPermission()

    # act
    result = perm.has_permission(
        _req(admin), _vw(pk=999999),
    )

    # assert
    assert result is False


def test_wf_member_perm__none_pk__denied():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    view = MagicMock()
    view.kwargs = {'pk': None}
    perm = WorkflowMemberPermission()

    # act
    result = perm.has_permission(_req(owner), view)

    # assert
    assert result is False
