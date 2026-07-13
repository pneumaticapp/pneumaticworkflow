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
from src.permissions.enums import PermissionSource
from src.processes.queries import (
    WorkflowPermissionQuery,
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
    WorkflowPermissionService(workflow=workflow).grant_change(
        user=admin,
        source_type=PermissionSource.TEMPLATE_OWNER,
        source_id=0,
    )
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
    WorkflowPermissionService(workflow=workflow).grant_change(
        user=non_admin,
        source_type=PermissionSource.TEMPLATE_OWNER,
        source_id=0,
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


def test_wf_member_perm__mentioned__allowed():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    mentioned = create_test_not_admin(
        account=account, email='m@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    comment = WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text=f'[User| {mentioned.id}]',
        status=CommentStatus.CREATED,
    )
    WorkflowPermissionService(workflow).grant_view(
        user=mentioned,
        source_type=PermissionSource.MENTION,
        source_id=comment.id,
    )
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


def test_wf_member_perm__deleted_performer__denied():
    """
    After performer removal (directly_status=DELETED) and
    sync_performer_sources recalculation, the performer must lose access.
    Both the Q-based check and Guardian view are revoked.
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
    WorkflowPermissionService(workflow).sync_performer_sources()
    task = workflow.tasks.first()
    task.taskperformer_set.filter(user=performer).update(
        directly_status=DirectlyStatus.DELETED,
    )
    WorkflowPermissionService(workflow).sync_performer_sources()
    perm = WorkflowMemberPermission()

    # act
    result = perm.has_permission(
        _req(performer), _vw(pk=workflow.pk),
    )

    # assert
    assert result is False


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
    WorkflowPermissionService(workflow=workflow).grant_change(
        user=admin,
        source_type=PermissionSource.TEMPLATE_OWNER,
        source_id=0,
    )
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


def test_task_wf_member__viewer__allowed():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account, email='v@t.t',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    WorkflowPermissionService(workflow=workflow).grant_view(
        user=viewer,
        source_type=PermissionSource.PERFORMER,
        source_id=0,
    )
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


def test_wf_member_or_viewer__viewer__allowed():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account, email='v@t.t',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService(workflow=workflow).grant_view(
        user=viewer,
        source_type=PermissionSource.PERFORMER,
        source_id=0,
    )
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


def test_task_wf_member_or_viewer__viewer__ok():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account, email='v2@t.t',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    WorkflowPermissionService(workflow=workflow).grant_view(
        user=viewer,
        source_type=PermissionSource.PERFORMER,
        source_id=0,
    )
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


def test_task_comment__mentioned__allowed():
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
        text=f'[User| {viewer.id}]',
        status=CommentStatus.CREATED,
    )
    WorkflowPermissionService(workflow).grant_view(
        user=viewer,
        source_type=PermissionSource.MENTION,
        source_id=comment.id,
    )
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


def test_wf_comment__mentioned__allowed():
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
        text=f'[User| {viewer.id}]',
        status=CommentStatus.CREATED,
    )
    WorkflowPermissionService(workflow).grant_view(
        user=viewer,
        source_type=PermissionSource.MENTION,
        source_id=comment.id,
    )
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
    WorkflowPermissionService(workflow=workflow).grant_view(
        user=viewer,
        source_type=PermissionSource.PERFORMER,
        source_id=0,
    )
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
    WorkflowPermissionService(workflow=workflow).grant_view(
        user=viewer,
        source_type=PermissionSource.PERFORMER,
        source_id=0,
    )
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
    WorkflowPermissionService(workflow).set_view_and_change(user_ids=[])
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
    WorkflowPermissionService(workflow).set_view_and_change(user_ids=[])
    WorkflowPermissionService(workflow).sync_performer_sources()
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
    WorkflowPermissionService(workflow).set_view_and_change(user_ids=[])
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
    WorkflowPermissionService(workflow=wf_a).grant_view(
        user=outsider,
        source_type=PermissionSource.PERFORMER,
        source_id=0,
    )

    # act
    qs = Workflow.objects.filter(
        pk=wf_a.pk,
        account_id=outsider.account_id,
    ).filter(
        WorkflowPermissionQuery.viewer_q(outsider.id),
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
    WorkflowPermissionService(workflow=wf_a).grant_change(
        user=outsider,
        source_type=PermissionSource.TEMPLATE_OWNER,
        source_id=0,
    )

    # act
    qs = Workflow.objects.filter(
        pk=wf_a.pk,
        account_id=outsider.account_id,
    ).filter(
        WorkflowPermissionQuery.change_q(outsider.id),
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
    WorkflowPermissionService(workflow=workflow).grant_change(
        user=regular,
        source_type=PermissionSource.TEMPLATE_OWNER,
        source_id=0,
    )
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


# ══ SECURITY: Deleted performers denied ═══════════════════


def test_task_wf_member__deleted_performer__denied():
    """TaskWorkflowMemberPermission denies deleted performer."""
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
    WorkflowPermissionService(workflow).sync_performer_sources()
    task = workflow.tasks.first()
    task.taskperformer_set.filter(user=performer).update(
        directly_status=DirectlyStatus.DELETED,
    )
    WorkflowPermissionService(workflow).sync_performer_sources()
    perm = TaskWorkflowMemberPermission()

    # act
    result = perm.has_permission(
        _req(performer), _vw(pk=task.pk),
    )

    # assert
    assert result is False


def test_task_comment__deleted_performer__denied():
    """TaskCommentPermission denies deleted performer."""
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
    WorkflowPermissionService(workflow).sync_performer_sources()
    task = workflow.tasks.first()
    task.taskperformer_set.filter(user=performer).update(
        directly_status=DirectlyStatus.DELETED,
    )
    WorkflowPermissionService(workflow).sync_performer_sources()
    perm = TaskCommentPermission()

    # act
    result = perm.has_permission(
        _req(performer), _vw(pk=task.pk),
    )

    # assert
    assert result is False


def test_wf_comment__deleted_performer__denied():
    """WorkflowCommentPermission denies deleted performer."""
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
    WorkflowPermissionService(workflow).sync_performer_sources()
    task = workflow.tasks.first()
    task.taskperformer_set.filter(user=performer).update(
        directly_status=DirectlyStatus.DELETED,
    )
    WorkflowPermissionService(workflow).sync_performer_sources()
    perm = WorkflowCommentPermission()

    # act
    result = perm.has_permission(
        _req(performer), _vw(pk=workflow.pk),
    )

    # assert
    assert result is False


def test_reaction__deleted_performer__denied():
    """CommentReactionPermission denies deleted performer."""
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
    WorkflowPermissionService(workflow).sync_performer_sources()
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
    task.taskperformer_set.filter(user=performer).update(
        directly_status=DirectlyStatus.DELETED,
    )
    WorkflowPermissionService(workflow).sync_performer_sources()
    perm = CommentReactionPermission()

    # act
    result = perm.has_permission(
        _req(performer), _vw(pk=comment.pk),
    )

    # assert
    assert result is False
