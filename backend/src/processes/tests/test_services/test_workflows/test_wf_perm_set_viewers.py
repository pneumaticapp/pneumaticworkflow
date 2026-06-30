"""
Unit tests for WorkflowPermissionService.set_viewers
and _get_mentioned_user_ids.
"""

import pytest

from src.processes.enums import (
    CommentStatus,
    DirectlyStatus,
    PerformerType,
    WorkflowEventType,
)
from src.processes.models.workflows.event import WorkflowEvent
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
    create_test_template,
    create_test_workflow,
)
from src.processes.tests.guardian_helpers import (
    assert_guardian_view,
    assert_guardian_viewer_count,
    assert_no_guardian_view,
)

pytestmark = pytest.mark.django_db


# ── _get_mentioned_user_ids ───────────────────────────────


def test_get_mentioned_ids__single__returns_id():
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
        text='Hey [Mentioned User| 999]',
        status=CommentStatus.CREATED,
    )

    # act
    result = WorkflowPermissionService._get_mentioned_user_ids(
        workflow,
    )

    # assert
    assert result == {999}


def test_get_mentioned_ids__multiple_comments__all():
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
        text='[User A| 10] check this',
        status=CommentStatus.CREATED,
    )
    WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text='[User B| 20] and [User C| 30]',
        status=CommentStatus.CREATED,
    )

    # act
    result = WorkflowPermissionService._get_mentioned_user_ids(
        workflow,
    )

    # assert
    assert result == {10, 20, 30}


def test_get_mentioned_ids__deleted__excluded():
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
    result = WorkflowPermissionService._get_mentioned_user_ids(
        workflow,
    )

    # assert
    assert result == set()


def test_get_mentioned_ids__no_comments__empty():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    result = WorkflowPermissionService._get_mentioned_user_ids(
        workflow,
    )

    # assert
    assert result == set()


def test_get_mentioned_ids__non_comment__ignored():
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
    result = WorkflowPermissionService._get_mentioned_user_ids(
        workflow,
    )

    # assert
    assert result == set()


def test_get_mentioned_ids__mix_deleted_active__ok():
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
    result = WorkflowPermissionService._get_mentioned_user_ids(
        workflow,
    )

    # assert
    assert 100 in result
    assert 200 not in result


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
    WorkflowPermissionService.set_viewers(workflow=workflow)

    # assert
    assert WorkflowPermissionService.has_view(user=owner, workflow=workflow)
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
    WorkflowPermissionService.set_viewers(workflow=workflow)

    # assert
    assert WorkflowPermissionService.has_view(
        user=performer, workflow=workflow,
    )
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
    WorkflowPermissionService.set_viewers(workflow=workflow)

    # assert
    assert WorkflowPermissionService.has_view(
        user=member, workflow=workflow,
    )
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
    WorkflowPermissionService.set_viewers(workflow=workflow)

    # assert
    assert WorkflowPermissionService.has_view(
        user=mentioned, workflow=workflow,
    )
    assert_guardian_view(workflow, mentioned)


def test_set_viewers__idempotent__no_dups():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    WorkflowPermissionService.set_viewers(workflow=workflow)
    WorkflowPermissionService.set_viewers(workflow=workflow)

    # assert
    assert WorkflowPermissionService.has_view(user=owner, workflow=workflow)
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
    WorkflowPermissionService.set_viewers(workflow=workflow)
    assert WorkflowPermissionService.has_view(
        user=performer, workflow=workflow,
    )
    task = workflow.tasks.first()
    task.taskperformer_set.filter(user=performer).update(
        directly_status=DirectlyStatus.DELETED,
    )

    # act
    WorkflowPermissionService.set_viewers(workflow=workflow)

    # assert
    assert not WorkflowPermissionService.has_view(
        user=performer, workflow=workflow,
    )
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
    WorkflowPermissionService.set_viewers(workflow=workflow)
    assert WorkflowPermissionService.has_view(
        user=member, workflow=workflow,
    )
    group.users.clear()

    # act
    WorkflowPermissionService.set_viewers(workflow=workflow)

    # assert
    assert not WorkflowPermissionService.has_view(
        user=member, workflow=workflow,
    )
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
    WorkflowPermissionService.set_viewers(workflow=workflow)
    assert WorkflowPermissionService.has_view(
        user=mentioned, workflow=workflow,
    )
    comment.status = CommentStatus.DELETED
    comment.save(update_fields=['status'])

    # act
    WorkflowPermissionService.set_viewers(workflow=workflow)

    # assert
    assert not WorkflowPermissionService.has_view(
        user=mentioned, workflow=workflow,
    )
    assert_no_guardian_view(workflow, mentioned)


def test_set_viewers__manage_not_touched():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    assert WorkflowPermissionService.has_manage(
        user=owner, workflow=workflow,
    )

    # act
    WorkflowPermissionService.set_viewers(workflow=workflow)

    # assert
    assert WorkflowPermissionService.has_manage(
        user=owner, workflow=workflow,
    )


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
    WorkflowPermissionService.set_viewers(workflow=workflow)

    # assert
    assert not WorkflowPermissionService.has_view(
        user=deleted_user, workflow=workflow,
    )
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
    WorkflowPermissionService.set_viewers(workflow=workflow)

    # assert
    assert WorkflowPermissionService.has_view(user=owner, workflow=workflow)


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
    WorkflowPermissionService.set_viewers(workflow=workflow)

    # assert
    assert not WorkflowPermissionService.has_view(
        user=member, workflow=workflow,
    )
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
    WorkflowPermissionService.set_viewers(workflow=workflow)

    # assert
    assert WorkflowPermissionService.has_view(user=owner, workflow=workflow)
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
    WorkflowPermissionService.set_viewers(workflow=workflow)

    # assert
    assert not WorkflowPermissionService.has_view(
        user=extra, workflow=workflow,
    )
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
    WorkflowPermissionService.set_viewers(workflow=wf_1)
    WorkflowPermissionService.set_viewers(workflow=wf_2)

    # assert
    assert WorkflowPermissionService.has_view(user=user_a, workflow=wf_1)
    assert not WorkflowPermissionService.has_view(user=user_a, workflow=wf_2)
    assert not WorkflowPermissionService.has_view(user=user_b, workflow=wf_1)
    assert WorkflowPermissionService.has_view(user=user_b, workflow=wf_2)


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
    WorkflowPermissionService.set_viewers(workflow=wf_1)
    WorkflowPermissionService.grant_view(user=user, workflow=wf_2)
    task = wf_1.tasks.first()
    task.taskperformer_set.filter(user=user).update(
        directly_status=DirectlyStatus.DELETED,
    )

    # act
    WorkflowPermissionService.set_viewers(workflow=wf_1)

    # assert
    assert not WorkflowPermissionService.has_view(user=user, workflow=wf_1)
    assert WorkflowPermissionService.has_view(user=user, workflow=wf_2)


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
    WorkflowPermissionService.set_viewers(workflow=workflow)

    # assert
    assert WorkflowPermissionService.has_view(user=user, workflow=workflow)
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
    WorkflowPermissionService.set_viewers(workflow=workflow)
    task_1 = workflow.tasks.get(number=1)
    task_1.taskperformer_set.filter(user=user).update(
        directly_status=DirectlyStatus.DELETED,
    )

    # act
    WorkflowPermissionService.set_viewers(workflow=workflow)

    # assert
    assert WorkflowPermissionService.has_view(user=user, workflow=workflow)
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
    WorkflowPermissionService.set_viewers(workflow=workflow)
    for task in workflow.tasks.all():
        task.taskperformer_set.filter(user=user).update(
            directly_status=DirectlyStatus.DELETED,
        )

    # act
    WorkflowPermissionService.set_viewers(workflow=workflow)

    # assert
    assert not WorkflowPermissionService.has_view(
        user=user, workflow=workflow,
    )
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
    WorkflowPermissionService.set_viewers(workflow=workflow)

    # assert
    assert WorkflowPermissionService.has_view(
        user=owner, workflow=workflow,
    )
    assert WorkflowPermissionService.has_view(
        user=performer, workflow=workflow,
    )
    assert WorkflowPermissionService.has_view(
        user=mentioned, workflow=workflow,
    )
    assert WorkflowPermissionService.has_view(
        user=grp_member, workflow=workflow,
    )


def test_set_viewers__triple_call__no_extra_rows():
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    for _ in range(3):
        WorkflowPermissionService.set_viewers(workflow=workflow)

    # assert
    from guardian.models import UserObjectPermission  # noqa: PLC0415
    from django.contrib.contenttypes.models import ContentType  # noqa: PLC0415
    from src.processes.models.workflows.workflow import (  # noqa: PLC0415
        Workflow as WfModel,
    )

    ctype = ContentType.objects.get_for_model(WfModel)
    count = UserObjectPermission.objects.filter(
        content_type=ctype,
        object_pk=str(workflow.pk),
        permission__codename='view_workflow',
    ).count()
    viewer_ids = WorkflowPermissionService.get_viewer_ids(
        workflow=workflow,
    )
    assert count == len(viewer_ids)
