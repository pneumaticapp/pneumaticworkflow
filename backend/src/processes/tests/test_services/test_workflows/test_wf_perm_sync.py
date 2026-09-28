"""Unit tests for WorkflowPermissionService surgical sync API."""

import pytest

from src.permissions.enums import PermissionSource
from src.processes.enums import (
    DirectlyStatus,
    PerformerType,
)
from src.processes.models.workflows.task import TaskPerformer
from src.processes.services.workflow_permissions import (
    WorkflowPermissionService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_not_admin,
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_sync_view__adds_and_removes__ok():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user_a = create_test_not_admin(
        account=account,
        email='a@test.test',
    )
    user_b = create_test_not_admin(
        account=account,
        email='b@test.test',
    )
    workflow = create_test_workflow(user=owner)
    svc = WorkflowPermissionService(workflow)
    svc.sync_view(
        user_ids=[user_a.id, user_b.id],
        source_type=PermissionSource.MENTION,
        source_id=1,
    )

    # act
    added = svc.sync_view(
        user_ids=[user_b.id],
        source_type=PermissionSource.MENTION,
        source_id=1,
    )

    # assert
    assert added == set()
    assert not svc.has_view(user=user_a)
    assert svc.has_view(user=user_b)


def test_sync_view__new_users__returns_added_ids():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(
        account=account,
        email='new@test.test',
    )
    workflow = create_test_workflow(user=owner)
    svc = WorkflowPermissionService(workflow)

    # act
    added = svc.sync_view(
        user_ids=[user.id],
        source_type=PermissionSource.MENTION,
        source_id=42,
    )

    # assert
    assert added == {user.id}
    assert svc.has_view(user=user)


def test_revoke_view__removes_only_source__ok():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(
        account=account,
        email='rev@test.test',
    )
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    svc = WorkflowPermissionService(workflow)
    svc.grant_view(
        user=user,
        source_type=PermissionSource.MENTION,
        source_id=1,
    )
    svc.grant_view(
        user=user,
        source_type=PermissionSource.PERFORMER,
        source_id=task.id,
    )

    # act
    svc.revoke_view(
        source_type=PermissionSource.MENTION,
        source_id=1,
    )

    # assert
    assert svc.has_view(user=user)


def test_set_view_and_change__replaces_owners__ok():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    new_owner = create_test_admin(
        account=account,
        email='owner2@test.test',
    )
    workflow = create_test_workflow(user=owner)
    svc = WorkflowPermissionService(workflow)

    # act
    svc.set_view_and_change(user_ids=[new_owner.id])

    # assert
    assert not svc.has_change(user=owner)
    assert svc.has_change(user=new_owner)
    assert svc.has_view(user=new_owner)


def test_set_view_and_change__empty__clears_change():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    stranger = create_test_not_admin(
        account=account,
        email='str@test.test',
    )
    workflow = create_test_workflow(user=owner)
    svc = WorkflowPermissionService(workflow)
    svc.grant_view(
        user=stranger,
        source_type=PermissionSource.MENTION,
        source_id=1,
    )

    # act
    svc.set_view_and_change(user_ids=[])

    # assert
    assert not svc.has_change(user=owner)
    assert not svc.get_users_with_change()
    assert svc.has_view(user=stranger)


def test_sync_performer_sources__grants_user_performer__ok():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    performer = create_test_not_admin(
        account=account,
        email='perf@test.test',
    )
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task=task,
        type=PerformerType.USER,
        user=performer,
        directly_status=DirectlyStatus.CREATED,
    )
    svc = WorkflowPermissionService(workflow)

    # act
    svc.sync_performer_sources()

    # assert
    assert svc.has_view(user=performer)


def test_sync_performer_sources__revokes_removed_user__ok():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    performer = create_test_not_admin(
        account=account,
        email='gone@test.test',
    )
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    svc = WorkflowPermissionService(workflow)
    svc.grant_view(
        user=performer,
        source_type=PermissionSource.PERFORMER,
        source_id=task.id,
    )

    # act
    svc.sync_performer_sources()

    # assert
    assert not svc.has_view(user=performer)


def test_sync_performer_sources__grants_group_members__ok():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_not_admin(
        account=account,
        email='gm@test.test',
    )
    group = create_test_group(
        account=account,
        users=[member],
    )
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task=task,
        type=PerformerType.GROUP,
        group=group,
        directly_status=DirectlyStatus.CREATED,
    )
    svc = WorkflowPermissionService(workflow)

    # act
    svc.sync_performer_sources()

    # assert
    assert svc.has_view(user=member)


def test_sync_performer_sources__preserves_other_sources__ok():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    mentioned = create_test_not_admin(
        account=account,
        email='mention@test.test',
    )
    substitute = create_test_admin(
        account=account,
        email='vac@test.test',
    )
    legacy = create_test_not_admin(
        account=account,
        email='legacy@test.test',
    )
    workflow = create_test_workflow(user=owner)
    svc = WorkflowPermissionService(workflow)
    svc.grant_view(
        user=mentioned,
        source_type=PermissionSource.MENTION,
        source_id=1,
    )
    svc.grant_view(
        user=substitute,
        source_type=PermissionSource.VACATION,
        source_id=owner.id,
    )
    svc.grant_view(
        user=legacy,
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow.id,
    )

    # act
    svc.sync_performer_sources()

    # assert
    assert svc.has_view(user=mentioned)
    assert svc.has_view(user=substitute)
    assert svc.has_view(user=legacy)


def test_sync_performer_group__on_workflow__syncs_members():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_not_admin(
        account=account,
        email='m1@test.test',
    )
    removed = create_test_not_admin(
        account=account,
        email='m2@test.test',
    )
    group = create_test_group(
        account=account,
        users=[member, removed],
    )
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task=task,
        type=PerformerType.GROUP,
        group=group,
        directly_status=DirectlyStatus.CREATED,
    )
    svc = WorkflowPermissionService(workflow)
    svc.sync_view(
        user_ids=[member.id, removed.id],
        source_type=PermissionSource.PERFORMER_GROUP,
        source_id=group.id,
    )

    # act
    svc.sync_performer_group(
        group_id=group.id,
        member_ids=[member.id],
    )

    # assert
    assert svc.has_view(user=member)
    assert not svc.has_view(user=removed)


def test_sync_performer_group__not_on_workflow__revokes():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_not_admin(
        account=account,
        email='gone_g@test.test',
    )
    group = create_test_group(
        account=account,
        users=[member],
    )
    workflow = create_test_workflow(user=owner)
    svc = WorkflowPermissionService(workflow)
    svc.sync_view(
        user_ids=[member.id],
        source_type=PermissionSource.PERFORMER_GROUP,
        source_id=group.id,
    )

    # act
    svc.sync_performer_group(group_id=group.id)

    # assert
    assert not svc.has_view(user=member)


def test_get_users_with_view__returns_all__ok():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(
        account=account,
        email='v@test.test',
    )
    workflow = create_test_workflow(user=owner)
    svc = WorkflowPermissionService(workflow)
    svc.grant_view(
        user=user,
        source_type=PermissionSource.MENTION,
        source_id=1,
    )

    # act
    viewer_ids = svc.get_users_with_view()

    # assert
    assert user.id in viewer_ids
    assert owner.id in viewer_ids


def test_get_users_with_change_map__batch_sorted__ok():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    other = create_test_admin(
        account=account,
        email='co@test.test',
    )
    workflow_1 = create_test_workflow(user=owner)
    workflow_2 = create_test_workflow(user=owner)
    WorkflowPermissionService(workflow_1).set_view_and_change(
        user_ids=[owner.id, other.id],
    )
    WorkflowPermissionService(workflow_2).set_view_and_change(
        user_ids=[other.id],
    )

    # act
    result = WorkflowPermissionService.get_users_with_change_map(
        workflow_ids=[workflow_1.id, workflow_2.id],
    )

    # assert
    assert result[workflow_1.id] == sorted([owner.id, other.id])
    assert result[workflow_2.id] == [other.id]


def test_get_users_with_change_map__empty_ids__empty_dict():

    # arrange
    workflow_ids = []

    # act
    result = WorkflowPermissionService.get_users_with_change_map(
        workflow_ids=workflow_ids,
    )

    # assert
    assert result == {}
