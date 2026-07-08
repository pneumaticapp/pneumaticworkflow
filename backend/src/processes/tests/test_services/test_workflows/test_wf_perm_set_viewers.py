"""
Unit tests for WorkflowPermissionService.set_viewers
and _get_mentioned_sources.
"""

import pytest

from src.accounts.enums import UserGroupType
from src.accounts.models import UserGroup
from src.processes.enums import (
    CommentStatus,
    DirectlyStatus,
    PerformerType,
    WorkflowEventType,
)
from django.contrib.contenttypes.models import ContentType
from src.permissions.enums import PermissionSource
from src.permissions.models import UserObjectPermission
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.models.workflows.task import TaskPerformer
from src.processes.models.workflows.workflow import (
    Workflow as WfModel,
)
from src.processes.services.workflow_permissions import (
    WorkflowPermissionService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)
from src.processes.tests.guardian_helpers import (
    assert_guardian_view,
    assert_guardian_viewer_count,
    assert_no_guardian_view,
)

pytestmark = pytest.mark.django_db


# -- _get_mentioned_sources ----------------------------


def test_get_mentioned_sources__single__returns_tuple():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    event = WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text='Hey [Mentioned User| 999]',
        status=CommentStatus.CREATED,
    )

    # act
    result = WorkflowPermissionService._get_mentioned_sources(
        workflow,
    )

    # assert
    assert result == {
        (999, PermissionSource.MENTION, event.id),
    }


def test_get_mentioned_sources__multiple_comments__all():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    ev1 = WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text='[User A| 10] check this',
        status=CommentStatus.CREATED,
    )
    ev2 = WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text='[User B| 20] and [User C| 30]',
        status=CommentStatus.CREATED,
    )

    # act
    result = WorkflowPermissionService._get_mentioned_sources(
        workflow,
    )

    # assert
    assert (10, PermissionSource.MENTION, ev1.id) in result
    assert (20, PermissionSource.MENTION, ev2.id) in result
    assert (30, PermissionSource.MENTION, ev2.id) in result
    assert len(result) == 3


def test_get_mentioned_sources__deleted__excluded():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text='[Should Not Count| 555]',
        status=CommentStatus.DELETED,
    )

    # act
    result = WorkflowPermissionService._get_mentioned_sources(
        workflow,
    )

    # assert
    assert result == set()


def test_get_mentioned_sources__no_comments__empty():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    result = WorkflowPermissionService._get_mentioned_sources(
        workflow,
    )

    # assert
    assert result == set()


def test_get_mentioned_sources__non_comment__ignored():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    WorkflowEvent.objects.create(
        type=WorkflowEventType.RUN,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text='[Fake Mention| 888]',
    )

    # act
    result = WorkflowPermissionService._get_mentioned_sources(
        workflow,
    )

    # assert
    assert result == set()


def test_get_mentioned_sources__mix_deleted_active__ok():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    ev_active = WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text='[Active| 100]',
        status=CommentStatus.CREATED,
    )
    WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text='[Deleted| 200]',
        status=CommentStatus.DELETED,
    )

    # act
    result = WorkflowPermissionService._get_mentioned_sources(
        workflow,
    )

    # assert
    expected = (100, PermissionSource.MENTION, ev_active.id)
    assert expected in result
    user_ids = {t[0] for t in result}
    assert 200 not in user_ids


# ── set_viewers — GRANT ───────────────────────────────────


def test_set_viewers__grants_to_tmpl_owner():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner, template=template,
    )

    # act
    WorkflowPermissionService(workflow).set_viewers()

    # assert
    assert WorkflowPermissionService(workflow).has_view(owner)
    assert_guardian_view(workflow, owner)


def test_set_viewers__grants_to_direct_performer():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    performer = create_test_not_admin(
        account=account, email='performer@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    template.tasks.first().add_raw_performer(user=performer)
    workflow = create_test_workflow(
        user=owner, template=template,
    )

    # act
    WorkflowPermissionService(workflow).set_viewers()

    # assert
    assert WorkflowPermissionService(workflow).has_view(performer)
    assert_guardian_view(workflow, performer)


def test_set_viewers__grants_to_group_members():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_not_admin(
        account=account, email='member@test.test',
    )
    group = create_test_group(account, users=[member])
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task=task,
        group=group,
        type=PerformerType.GROUP,
    )

    # act
    WorkflowPermissionService(workflow).set_viewers()

    # assert
    assert WorkflowPermissionService(workflow).has_view(member)
    assert_guardian_view(workflow, member)


def test_set_viewers__grants_to_mentioned_user():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    mentioned = create_test_admin(
        account=account, email='mentioned@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text=f'Hey [Mentioned| {mentioned.id}]',
        status=CommentStatus.CREATED,
    )

    # act
    WorkflowPermissionService(workflow).set_viewers()

    # assert
    assert WorkflowPermissionService(workflow).has_view(mentioned)
    assert_guardian_view(workflow, mentioned)


def test_set_viewers__idempotent__no_dups():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    WorkflowPermissionService(workflow).set_viewers()
    WorkflowPermissionService(workflow).set_viewers()

    # assert
    assert WorkflowPermissionService(workflow).has_view(owner)
    assert_guardian_viewer_count(workflow, 1)


# ── set_viewers — REVOKE ──────────────────────────────────


def test_set_viewers__revokes_removed_performer():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    performer = create_test_not_admin(
        account=account, email='performer@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    template.tasks.first().add_raw_performer(user=performer)
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    WorkflowPermissionService(workflow).set_viewers()
    assert WorkflowPermissionService(workflow).has_view(performer)
    task = workflow.tasks.first()
    task.taskperformer_set.filter(user=performer).update(
        directly_status=DirectlyStatus.DELETED,
    )

    # act
    WorkflowPermissionService(workflow).set_viewers()

    # assert
    assert not WorkflowPermissionService(workflow).has_view(performer)
    assert_no_guardian_view(workflow, performer)


def test_set_viewers__revokes_removed_group_member():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_not_admin(
        account=account, email='member@test.test',
    )
    group = create_test_group(account, users=[member])
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task=task,
        group=group,
        type=PerformerType.GROUP,
    )
    WorkflowPermissionService(workflow).set_viewers()
    assert WorkflowPermissionService(workflow).has_view(member)
    group.users.clear()

    # act
    WorkflowPermissionService(workflow).set_viewers()

    # assert
    assert not WorkflowPermissionService(workflow).has_view(member)
    assert_no_guardian_view(workflow, member)


def test_set_viewers__deleted_mention__revokes():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    mentioned = create_test_admin(
        account=account, email='mentioned@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    comment = WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text=f'[Mentioned| {mentioned.id}]',
        status=CommentStatus.CREATED,
    )
    WorkflowPermissionService(workflow).set_viewers()
    assert WorkflowPermissionService(workflow).has_view(mentioned)
    comment.status = CommentStatus.DELETED
    comment.save(update_fields=['status'])

    # act
    WorkflowPermissionService(workflow).set_viewers()

    # assert
    assert not WorkflowPermissionService(workflow).has_view(mentioned)
    assert_no_guardian_view(workflow, mentioned)


def test_set_viewers__manage_not_touched():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    assert WorkflowPermissionService(workflow).has_change(owner)

    # act
    WorkflowPermissionService(workflow).set_viewers()

    # assert
    assert WorkflowPermissionService(workflow).has_change(owner)


def test_set_viewers__deleted_performer__no_view():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    deleted_user = create_test_not_admin(
        account=account, email='deleted@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task=task,
        user=deleted_user,
        type=PerformerType.USER,
        directly_status=DirectlyStatus.DELETED,
    )

    # act
    WorkflowPermissionService(workflow).set_viewers()

    # assert
    assert not WorkflowPermissionService(workflow).has_view(deleted_user)
    assert_no_guardian_view(workflow, deleted_user)


# ── set_viewers — edge cases ──────────────────────────────


def test_set_viewers__no_template__performers_ok():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    workflow.template_id = None
    workflow.save(update_fields=['template_id'])

    # act
    WorkflowPermissionService(workflow).set_viewers()

    # assert
    assert WorkflowPermissionService(workflow).has_view(owner)


def test_set_viewers__deleted_group__no_view():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_not_admin(
        account=account, email='member@test.test',
    )
    group = create_test_group(account, users=[member])
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task=task,
        group=group,
        type=PerformerType.GROUP,
    )
    group.is_deleted = True
    group.save(update_fields=['is_deleted'])

    # act
    WorkflowPermissionService(workflow).set_viewers()

    # assert
    assert not WorkflowPermissionService(workflow).has_view(member)
    assert_no_guardian_view(workflow, member)


def test_set_viewers__performer_and_mentioned__single():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text=f'[Owner| {owner.id}]',
        status=CommentStatus.CREATED,
    )

    # act
    WorkflowPermissionService(workflow).set_viewers()

    # assert
    assert WorkflowPermissionService(workflow).has_view(owner)
    assert_guardian_viewer_count(workflow, 1)


def test_set_viewers__deleted_task__not_counted():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    extra = create_test_not_admin(
        account=account, email='extra@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=2,
    )
    template.tasks.get(number=2).add_raw_performer(extra)
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    task_2 = workflow.tasks.get(number=2)
    task_2.is_deleted = True
    task_2.save(update_fields=['is_deleted'])

    # act
    WorkflowPermissionService(workflow).set_viewers()

    # assert
    assert not WorkflowPermissionService(workflow).has_view(extra)
    assert_no_guardian_view(workflow, extra)


def test_set_viewers__separate_wfs__independent():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user_a = create_test_not_admin(
        account=account, email='a@test.test',
    )
    user_b = create_test_not_admin(
        account=account, email='b@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    template.tasks.first().add_raw_performer(user_a)
    wf_1 = create_test_workflow(
        user=owner, template=template,
    )
    template_2 = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    template_2.tasks.first().add_raw_performer(user_b)
    wf_2 = create_test_workflow(
        user=owner, template=template_2,
    )

    # act
    WorkflowPermissionService(wf_1).set_viewers()
    WorkflowPermissionService(wf_2).set_viewers()

    # assert
    assert WorkflowPermissionService(wf_1).has_view(user_a)
    assert not WorkflowPermissionService(wf_2).has_view(user_a)
    assert not WorkflowPermissionService(wf_1).has_view(user_b)
    assert WorkflowPermissionService(wf_2).has_view(user_b)


def test_set_viewers__revoke_one_wf__no_side_effect():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(
        account=account, email='user@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    template.tasks.first().add_raw_performer(user=user)
    wf_1 = create_test_workflow(
        user=owner, template=template,
    )
    wf_2 = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService(wf_1).set_viewers()
    WorkflowPermissionService(wf_2).grant_view(
        user,
        source_type=PermissionSource.PERFORMER,
        source_id=0,
    )
    task = wf_1.tasks.first()
    task.taskperformer_set.filter(user=user).update(
        directly_status=DirectlyStatus.DELETED,
    )

    # act
    WorkflowPermissionService(wf_1).set_viewers()

    # assert
    assert not WorkflowPermissionService(wf_1).has_view(user)
    assert WorkflowPermissionService(wf_2).has_view(user)


# ── set_viewers — multi-task ──────────────────────────────


def test_set_viewers__performer_on_task_2__has_view():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(
        account=account, email='task2@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=2,
    )
    template.tasks.get(number=2).add_raw_performer(user=user)
    workflow = create_test_workflow(
        user=owner, template=template,
    )

    # act
    WorkflowPermissionService(workflow).set_viewers()

    # assert
    assert WorkflowPermissionService(workflow).has_view(user)
    assert_guardian_view(workflow, user)


def test_set_viewers__removed_from_one__keeps_view():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(
        account=account, email='multi@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=2,
    )
    template.tasks.get(number=1).add_raw_performer(user=user)
    template.tasks.get(number=2).add_raw_performer(user=user)
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    WorkflowPermissionService(workflow).set_viewers()
    task_1 = workflow.tasks.get(number=1)
    task_1.taskperformer_set.filter(user=user).update(
        directly_status=DirectlyStatus.DELETED,
    )

    # act
    WorkflowPermissionService(workflow).set_viewers()

    # assert
    assert WorkflowPermissionService(workflow).has_view(user)
    assert_guardian_view(workflow, user)


def test_set_viewers__removed_from_all__loses_view():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(
        account=account, email='user@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=2,
    )
    template.tasks.get(number=1).add_raw_performer(user=user)
    template.tasks.get(number=2).add_raw_performer(user=user)
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    WorkflowPermissionService(workflow).set_viewers()
    for task in workflow.tasks.all():
        task.taskperformer_set.filter(user=user).update(
            directly_status=DirectlyStatus.DELETED,
        )

    # act
    WorkflowPermissionService(workflow).set_viewers()

    # assert
    assert not WorkflowPermissionService(workflow).has_view(user)
    assert_no_guardian_view(workflow, user)


def test_set_viewers__all_sources__correct_set():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    performer = create_test_not_admin(
        account=account, email='perf@t.t',
    )
    mentioned = create_test_not_admin(
        account=account, email='ment@t.t',
    )
    grp_member = create_test_not_admin(
        account=account, email='grp@t.t',
    )
    group = create_test_group(account, users=[grp_member])
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    template.tasks.first().add_raw_performer(user=performer)
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task=task,
        group=group,
        type=PerformerType.GROUP,
    )
    WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text=f'[User| {mentioned.id}]',
        status=CommentStatus.CREATED,
    )

    # act
    WorkflowPermissionService(workflow).set_viewers()

    # assert
    assert WorkflowPermissionService(workflow).has_view(owner)
    assert WorkflowPermissionService(workflow).has_view(performer)
    assert WorkflowPermissionService(workflow).has_view(mentioned)
    assert WorkflowPermissionService(workflow).has_view(grp_member)


def test_set_viewers__triple_call__no_extra_rows():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)

    ctype = ContentType.objects.get_for_model(WfModel)

    def _view_row_count():
        return UserObjectPermission.objects.filter(
            content_type=ctype,
            object_pk=str(workflow.pk),
            permission__codename='view_workflow',
        ).count()

    # act
    WorkflowPermissionService(workflow).set_viewers()
    count_after_first = _view_row_count()

    WorkflowPermissionService(workflow).set_viewers()
    count_after_second = _view_row_count()

    WorkflowPermissionService(workflow).set_viewers()
    count_after_third = _view_row_count()

    # assert — idempotent: row count stays the same
    assert count_after_first > 0
    assert count_after_first == count_after_second == count_after_third


def test_set_viewers__preserves_view_for_non_performer_manager():
    """Manager with change_workflow but NOT a performer
    should keep view_workflow after set_viewers."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    manager = create_test_admin(
        account=account, email='manager@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService(workflow).grant_change(
        manager,
        source_type=PermissionSource.TEMPLATE_OWNER,
        source_id=0,
    )
    assert WorkflowPermissionService(workflow).has_view(manager)

    # act
    WorkflowPermissionService(workflow).set_viewers()

    # assert
    assert WorkflowPermissionService(workflow).has_view(manager)
    assert WorkflowPermissionService(workflow).has_change(manager)
    assert_guardian_view(workflow, manager)


def test_set_viewers__set_owners_then_set_viewers__manager_keeps_view():
    """After set_owners replaces owners and set_viewers runs,
    remaining managers must keep view_workflow."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(
        account=account, email='admin@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService(workflow).grant_change(
        admin,
        source_type=PermissionSource.TEMPLATE_OWNER,
        source_id=0,
    )

    # act
    WorkflowPermissionService(workflow).set_owners([owner.id, admin.id])
    WorkflowPermissionService(workflow).set_viewers()

    # assert
    assert WorkflowPermissionService(workflow).has_view(admin)
    assert WorkflowPermissionService(workflow).has_change(admin)


def test_set_viewers__personal_group__grants_view():
    """Substitute in personal (vacation) group should get view."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_not_admin(
        account=account, email='sub@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    personal_group = UserGroup.objects.create(
        name='Vacation Sub',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    personal_group.users.add(substitute)
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task=task,
        group=personal_group,
        type=PerformerType.GROUP,
    )

    # act
    WorkflowPermissionService(workflow).set_viewers()

    # assert
    assert WorkflowPermissionService(workflow).has_view(substitute)
    assert_guardian_view(workflow, substitute)


def test_set_viewers__personal_group_removed__revokes():
    """When personal group performer is removed, substitute loses view."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_not_admin(
        account=account, email='sub@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    personal_group = UserGroup.objects.create(
        name='Vacation Sub',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    personal_group.users.add(substitute)
    task = workflow.tasks.first()
    tp = TaskPerformer.objects.create(
        task=task,
        group=personal_group,
        type=PerformerType.GROUP,
    )
    WorkflowPermissionService(workflow).set_viewers()
    assert WorkflowPermissionService(workflow).has_view(substitute)
    tp.directly_status = DirectlyStatus.DELETED
    tp.save(update_fields=['directly_status'])

    # act
    WorkflowPermissionService(workflow).set_viewers()

    # assert
    assert not WorkflowPermissionService(workflow).has_view(substitute)
    assert_no_guardian_view(workflow, substitute)
