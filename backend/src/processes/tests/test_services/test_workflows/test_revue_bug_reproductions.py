"""Regression reproductions for Guardian ACL revue findings.

These tests encode the EXPECTED correct behaviour. They fail on the
current code and must pass after the corresponding fixes.
"""

import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from src.accounts.models import UserVacation
from src.accounts.services.group import UserGroupService
from src.authentication.enums import AuthTokenType
from src.notifications.tasks import _send_event_created
from src.permissions.enums import PermissionSource
from src.permissions.models import UserObjectPermission
from src.processes.enums import (
    DirectlyStatus,
    PerformerType,
)
from src.processes.models.workflows.task import TaskPerformer
from src.processes.services.tasks.groups import GroupPerformerService
from src.processes.services.tasks.performers import TaskPerformersService
from src.processes.services.workflow_action import WorkflowActionService
from src.processes.services.workflow_permissions import (
    WorkflowPermissionService,
)
from src.processes.services.workflows.workflow import WorkflowService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_attachment,
    create_test_group,
    create_test_owner,
    create_test_user,
    create_test_workflow,
)
from src.storage.enums import AccessType, SourceType
from src.storage.services.attachments import AttachmentService

pytestmark = pytest.mark.django_db


def test_delete_group_actions__only_group_completed__auto_completes(
    mocker,
):
    """When the only completed performer is a GROUP, resolve a real
    User from group.users (not group.users.first().user).
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_user(
        account=account,
        email='member@test.test',
    )
    group_done = create_test_group(
        account,
        name='Group_done',
        users=[member],
    )
    group_remove = create_test_group(
        account,
        name='Group_remove',
        users=[create_test_user(
            account=account,
            email='other@test.test',
        )],
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    owner_tp = task.taskperformer_set.get(user=owner)
    owner_tp.directly_status = DirectlyStatus.DELETED
    owner_tp.save(update_fields=['directly_status'])
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group_done.id,
        is_completed=True,
    )
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group_remove.id,
        directly_status=DirectlyStatus.DELETED,
    )
    service = GroupPerformerService(
        user=owner,
        task=task,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.performer_group_deleted_event',
    )
    mocker.patch(
        'src.storage.utils.reassign_restricted_permissions_for_task',
    )
    mocker.patch(
        'src.storage.tasks.'
        'schedule_sync_workflow_attachment_permissions',
    )
    init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    complete_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.complete_task',
    )

    # act
    service._delete_group_actions(group=group_remove)

    # assert
    init_mock.assert_called_once_with(
        user=member,
        workflow=workflow,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    complete_mock.assert_called_once_with(task=task)


def test_delete_performer_actions__only_group_completed__auto_completes(
    mocker,
):
    """Same GROUP-only completion path in TaskPerformersService."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_user(
        account=account,
        email='member2@test.test',
    )
    removed = create_test_user(
        account=account,
        email='removed@test.test',
    )
    group_done = create_test_group(account, users=[member])
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    owner_tp = task.taskperformer_set.get(user=owner)
    owner_tp.directly_status = DirectlyStatus.DELETED
    owner_tp.save(update_fields=['directly_status'])
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group_done.id,
        is_completed=True,
    )
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.USER,
        user_id=removed.id,
        directly_status=DirectlyStatus.DELETED,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.performer_deleted_event',
    )
    mocker.patch(
        'src.storage.tasks.'
        'schedule_sync_workflow_attachment_permissions',
    )
    init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    complete_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.complete_task',
    )

    # act
    TaskPerformersService._delete_actions(
        request_user=owner,
        user=removed,
        task=task,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )

    # assert
    init_mock.assert_called_once_with(
        workflow=workflow,
        user=member,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    complete_mock.assert_called_once_with(task=task)


def test_send_event_created__foreign_account_uop__not_notified(
    mocker,
):
    """UOP for a user of another account must not receive WS events.

    Inserts a polluted UOP row directly (bypassing grant_view guard)
    to assert on_account filtering in _send_event_created.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    foreign_account = create_test_account()
    foreign_user = create_test_admin(
        account=foreign_account,
        email='foreign@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    ct = ContentType.objects.get_for_model(workflow)
    perm = Permission.objects.get(
        content_type=ct,
        codename='view_workflow',
    )
    UserObjectPermission.objects.create(
        user=foreign_user,
        permission=perm,
        content_type=ct,
        object_pk=str(workflow.pk),
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow.pk,
    )
    notify_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_event_created(
        logging=False,
        account_id=account.id,
        logo_lg=None,
        data={
            'id': 1,
            'workflow_id': workflow.id,
            'type': 'comment',
        },
    )

    # assert
    notified_ids = {
        kwargs['user_id']
        for _args, kwargs in notify_mock.call_args_list
    }
    assert foreign_user.id not in notified_ids


def test_grant_view__foreign_account_user__skipped():
    """grant_view must not create UOP for users of another account."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    foreign_account = create_test_account()
    foreign_user = create_test_admin(
        account=foreign_account,
        email='foreign2@test.test',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    svc = WorkflowPermissionService(workflow)

    # act
    svc.grant_view(
        user=foreign_user,
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow.pk,
    )

    # assert
    assert not svc.has_view(user=foreign_user)


def test_update_owners__schedules_attachment_sync(mocker):
    """Changing change/view owners must refresh attachment ACL."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    schedule_mock = mocker.patch(
        'src.processes.services.workflows.workflow.'
        'schedule_sync_workflow_attachment_permissions',
    )
    service = WorkflowService(
        instance=workflow,
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service.update_owners()

    # assert
    schedule_mock.assert_called_once_with(workflow.id)


def test_check_user_permission__same_file_id_other_account__denied():
    """RESTRICTED attachment with shared file_id in another account
    must not grant access via foreign UOP when checking for account A.
    """

    # arrange
    account_a = create_test_account()
    user_a = create_test_owner(account=account_a)
    workflow_a = create_test_workflow(user=user_a, tasks_count=1)
    account_b = create_test_account()
    owner_b = create_test_owner(
        account=account_b,
        email='owner_b@test.test',
    )
    workflow_b = create_test_workflow(user=owner_b, tasks_count=1)
    shared_file_id = 'shared_cross_account.pdf'
    create_test_attachment(
        account=account_a,
        file_id=shared_file_id,
        workflow=workflow_a,
        access_type=AccessType.RESTRICTED,
        source_type=SourceType.WORKFLOW,
    )
    att_b = create_test_attachment(
        account=account_b,
        file_id=shared_file_id,
        workflow=workflow_b,
        access_type=AccessType.RESTRICTED,
        source_type=SourceType.WORKFLOW,
    )
    ctype = ContentType.objects.get_for_model(att_b)
    perm = Permission.objects.get(
        content_type=ctype,
        codename='access_attachment',
    )
    UserObjectPermission.objects.create(
        user=user_a,
        permission=perm,
        content_type=ctype,
        object_pk=str(att_b.pk),
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow_b.pk,
    )
    service = AttachmentService(user=user_a)

    # act
    has_access = service.check_user_permission(
        user_id=user_a.id,
        account_id=account_a.id,
        file_id=shared_file_id,
    )

    # assert
    assert has_access is False


def test_delete_user_performer__vacation_sub_group__revokes_group_uop(
    mocker,
):
    """Deleting a vacationing user performer must revoke PERFORMER_GROUP
    for the substitute group even when run_actions=False (events skipped).
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    performer = create_test_user(
        account=account,
        email='vac_perf@test.test',
    )
    substitute = create_test_user(
        account=account,
        email='sub@test.test',
    )
    sub_group = create_test_group(
        account,
        name='VacSub',
        users=[substitute],
    )
    UserVacation.objects.create(
        user=performer,
        account=account,
        substitute_group=sub_group,
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    user_tp = TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.USER,
        user_id=performer.id,
        directly_status=DirectlyStatus.CREATED,
    )
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=sub_group.id,
    )
    perm_svc = WorkflowPermissionService(workflow)
    perm_svc.sync_view(
        user_ids=[performer.id],
        source_type=PermissionSource.PERFORMER,
        source_id=task.id,
    )
    perm_svc.sync_view(
        user_ids=[substitute.id],
        source_type=PermissionSource.PERFORMER_GROUP,
        source_id=sub_group.id,
    )
    assert perm_svc.has_view(user=substitute)
    # Mirror delete_performer(): mark user TP deleted before actions
    user_tp.directly_status = DirectlyStatus.DELETED
    user_tp.save(update_fields=['directly_status'])
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.performer_deleted_event',
    )
    mocker.patch(
        'src.storage.utils.reassign_restricted_permissions_for_task',
    )
    mocker.patch(
        'src.storage.tasks.'
        'schedule_sync_workflow_attachment_permissions',
    )
    mocker.patch(
        'src.notifications.tasks.send_task_deleted_notification.delay',
    )

    # act
    TaskPerformersService._delete_actions(
        request_user=owner,
        user=performer,
        task=task,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )

    # assert
    assert not UserObjectPermission.objects.filter(
        user=substitute,
        object_pk=str(workflow.pk),
        source_type=PermissionSource.PERFORMER_GROUP,
        source_id=sub_group.id,
    ).exists()
    assert not WorkflowPermissionService(workflow).has_view(
        user=substitute,
    )


def test_user_group_partial_update__performer_group__syncs_view(
    mocker,
):
    """Changing regular group membership must sync PERFORMER_GROUP UOP
    on workflows where the group is an active performer.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member_old = create_test_user(
        account=account,
        email='old_m@test.test',
    )
    member_new = create_test_user(
        account=account,
        email='new_m@test.test',
    )
    group = create_test_group(
        account,
        name='PerfGroup',
        users=[member_old],
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
    )
    WorkflowPermissionService(workflow).sync_view(
        user_ids=[member_old.id],
        source_type=PermissionSource.PERFORMER_GROUP,
        source_id=group.id,
    )
    assert WorkflowPermissionService(workflow).has_view(user=member_old)
    mocker.patch(
        'src.analysis.tasks.track_group_analytics.delay',
    )
    mocker.patch(
        'src.processes.tasks.update_workflow.update_workflow_owners.delay',
    )
    mocker.patch(
        'src.accounts.services.group.'
        'UserGroupService._send_added_users_notifications',
    )
    mocker.patch(
        'src.accounts.services.group.'
        'UserGroupService._send_removed_users_notifications',
    )
    mocker.patch(
        'src.notifications.tasks.'
        'send_group_updated_notification.delay',
    )
    service = UserGroupService(
        instance=group,
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service.partial_update(
        users=[member_new.id],
        force_save=True,
    )

    # assert
    perm_svc = WorkflowPermissionService(workflow)
    assert not perm_svc.has_view(user=member_old)
    assert perm_svc.has_view(user=member_new)
