"""
Integration tests for Guardian permission side-effects
triggered by other services.

TaskPerformersService, GroupPerformerService, Celery tasks,
CommentService, WorkflowCreation, VersionService.
"""

import pytest

from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    CommentStatus,
    DirectlyStatus,
    OwnerType,
    PerformerType,
    TaskStatus,
    WorkflowEventType,
)
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.models.workflows.task import TaskPerformer
from src.processes.services.events import CommentService
from src.processes.services.tasks.groups import (
    GroupPerformerService,
)
from src.processes.services.tasks.performers import (
    TaskPerformersService,
)
from src.processes.services.workflow_action import (
    WorkflowActionService,
)
from src.processes.services.workflow_permissions import (
    WorkflowPermissionService,
)
from src.processes.tasks.update_workflow import (
    update_workflow_owners,
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
    assert_no_guardian_view,
)
from src.storage.models import Attachment

pytestmark = pytest.mark.django_db


# ── TaskPerformersService ─────────────────────────────────


def test_delete_performer__revokes_view(mocker):

    # arrange

    # suppressed — not part of test scope
    mocker.patch(
        'src.processes.services.tasks.performers.'
        'send_task_deleted_notification.delay',
    )
    mocker.patch(
        'src.processes.services.tasks.performers.'
        'WorkflowEventService.performer_deleted_event',
    )
    mocker.patch(
        'src.processes.services.tasks.performers.'
        'AnalyticService.task_performer_deleted',
    )
    mocker.patch(
        'src.processes.services.tasks.performers.'
        'reassign_restricted_permissions_for_task',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    performer = create_test_admin(
        account=account, email='performer@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    template.tasks.first().add_raw_performer(user=performer)
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    task = workflow.tasks.first()
    WorkflowPermissionService.set_viewers(workflow=workflow)
    assert WorkflowPermissionService.has_view(
        user=performer, workflow=workflow,
    )

    # act
    TaskPerformersService.delete_performer(
        task=task,
        user_key=performer.id,
        request_user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # assert
    workflow.refresh_from_db()
    assert not WorkflowPermissionService.has_view(
        user=performer, workflow=workflow,
    )
    assert_no_guardian_view(workflow, performer)


def test_create_performer__grants_view(mocker):

    # arrange

    # suppressed — not part of test scope
    mocker.patch(
        'src.processes.services.tasks.performers.'
        'send_new_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.tasks.performers.'
        'send_new_task_websocket.delay',
    )
    mocker.patch(
        'src.processes.services.tasks.performers.'
        'WorkflowEventService.performer_created_event',
    )
    mocker.patch(
        'src.processes.services.tasks.performers.'
        'AnalyticService.task_performer_created',
    )
    mocker.patch(
        'src.processes.services.tasks.performers.'
        'reassign_restricted_permissions_for_task',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    new_perf = create_test_admin(
        account=account, email='new@test.test',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    task = workflow.tasks.first()
    assert not WorkflowPermissionService.has_view(
        user=new_perf, workflow=workflow,
    )

    # act
    TaskPerformersService.create_performer(
        task=task,
        current_url='/test',
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        user_key=new_perf.id,
        request_user=owner,
    )

    # assert
    assert WorkflowPermissionService.has_view(
        user=new_perf, workflow=workflow,
    )
    assert_guardian_view(workflow, new_perf)


# ── GroupPerformerService ─────────────────────────────────


def test_delete_group_performer__revokes_view(mocker):

    # arrange

    # suppressed — not part of test scope
    mocker.patch(
        'src.processes.services.tasks.groups.'
        'send_task_deleted_notification.delay',
    )
    mocker.patch(
        'src.processes.services.tasks.groups.'
        'WorkflowEventService.performer_group_deleted_event',
    )
    mocker.patch(
        'src.processes.services.tasks.groups.'
        'AnalyticService.task_group_performer_deleted',
    )
    mocker.patch(
        'src.processes.services.tasks.groups.'
        'reassign_restricted_permissions_for_task',
    )
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
        directly_status=DirectlyStatus.CREATED,
    )
    WorkflowPermissionService.set_viewers(workflow=workflow)
    assert WorkflowPermissionService.has_view(
        user=member, workflow=workflow,
    )

    # act
    service = GroupPerformerService(
        user=owner,
        task=task,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    service.delete_performer(group_id=group.id)

    # assert
    workflow.refresh_from_db()
    assert not WorkflowPermissionService.has_view(
        user=member, workflow=workflow,
    )
    assert_no_guardian_view(workflow, member)


def test_create_group_performer__grants_view(mocker):

    # arrange

    # suppressed — not part of test scope
    mocker.patch(
        'src.processes.services.tasks.groups.'
        'send_new_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.tasks.groups.'
        'send_new_task_websocket.delay',
    )
    mocker.patch(
        'src.processes.services.tasks.groups.'
        'WorkflowEventService.performer_group_created_event',
    )
    mocker.patch(
        'src.processes.services.tasks.groups.'
        'AnalyticService.task_group_performer_created',
    )
    mocker.patch(
        'src.processes.services.tasks.groups.'
        'reassign_restricted_permissions_for_task',
    )
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
    assert not WorkflowPermissionService.has_view(
        user=member, workflow=workflow,
    )

    # act
    service = GroupPerformerService(
        user=owner,
        task=task,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    service.create_performer(group_id=group.id)

    # assert
    assert WorkflowPermissionService.has_view(
        user=member, workflow=workflow,
    )
    assert_guardian_view(workflow, member)


# ── Celery: update_workflow_owners ────────────────────────


def test_celery_update_owners__grants_manage(mocker):

    # arrange

    # suppressed — not part of test scope
    mocker.patch(
        'src.storage.tasks'
        '.sync_workflow_attachment_permissions.delay',
    )
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
    assert not WorkflowPermissionService.has_manage(
        user=admin, workflow=workflow,
    )
    TemplateOwner.objects.create(
        template=template, type=OwnerType.USER, user=admin,
        account=account,
    )

    # act
    update_workflow_owners(template_ids=[template.id])

    # assert
    workflow.refresh_from_db()
    assert WorkflowPermissionService.has_manage(
        user=admin, workflow=workflow,
    )
    assert WorkflowPermissionService.has_view(
        user=admin, workflow=workflow,
    )


def test_celery_update_owners__revokes_removed(mocker):

    # arrange

    # suppressed — not part of test scope
    mocker.patch(
        'src.storage.tasks'
        '.sync_workflow_attachment_permissions.delay',
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
    WorkflowPermissionService.grant_manage(user=admin, workflow=workflow)
    assert WorkflowPermissionService.has_manage(
        user=admin, workflow=workflow,
    )

    # act
    update_workflow_owners(template_ids=[template.id])

    # assert
    workflow.refresh_from_db()
    assert not WorkflowPermissionService.has_manage(
        user=admin, workflow=workflow,
    )


# ── continue_workflow — grant_view_bulk ───────────────────


def test_continue_wf__performers_get_view(mocker):

    # arrange

    # suppressed — not part of test scope
    mocker.patch(
        'src.processes.services.workflow_action'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action'
        '.send_new_task_websocket.delay',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    performer = create_test_not_admin(
        account=account, email='p@t.t',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=2,
    )
    # Don't add performer to template — add to task 2
    # after workflow creation so pre-condition holds.
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    assert not WorkflowPermissionService.has_view(
        user=performer, workflow=workflow,
    )
    task_2 = workflow.tasks.get(number=2)

    # Add raw performer to the workflow task directly
    task_2.add_raw_performer(user=performer)
    task_2.update_performers(restore_performers=True)

    # act
    service = WorkflowActionService(
        user=owner, workflow=workflow,
    )
    service.continue_workflow(task=task_2)

    # assert
    assert WorkflowPermissionService.has_view(
        user=performer, workflow=workflow,
    )
    assert_guardian_view(workflow, performer)


# ── CommentService — mention grants ──────────────────────


def test_comment_create__mention_grants_view(mocker):

    # arrange

    # suppressed — not part of test scope
    mocker.patch(
        'src.processes.services.events'
        '.send_mention_notification.delay',
    )
    mocker.patch(
        'src.processes.services.events'
        '.send_comment_notification.delay',
    )
    mocker.patch(
        'src.processes.services.events'
        '.send_event_updated.delay',
    )
    mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    mentioned = create_test_not_admin(
        account=account, email='m@t.t',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    template.tasks.first().add_raw_performer(owner)
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    assert not WorkflowPermissionService.has_view(
        user=mentioned, workflow=workflow,
    )
    task = workflow.tasks.first()
    task.update_performers(restore_performers=True)
    task.status = 'active'
    task.save(update_fields=['status'])

    # act
    service = CommentService(
        instance=None, user=owner, is_superuser=False,
    )
    service.create(
        task=task,
        text=f'Hey [Mentioned| {mentioned.id}]',
    )

    # assert
    assert WorkflowPermissionService.has_view(
        user=mentioned, workflow=workflow,
    )
    assert_guardian_view(workflow, mentioned)


def test_comment_update__new_mention_grants_view(mocker):

    # arrange

    # suppressed — not part of test scope
    mocker.patch(
        'src.processes.services.events'
        '.send_mention_notification.delay',
    )
    mocker.patch(
        'src.processes.services.events'
        '.send_event_updated.delay',
    )
    mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    mentioned = create_test_not_admin(
        account=account, email='m2@t.t',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    template.tasks.first().add_raw_performer(owner)
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    task = workflow.tasks.first()
    task.update_performers(restore_performers=True)
    task.status = 'active'
    task.save(update_fields=['status'])
    comment = WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text='Hello',
        status=CommentStatus.CREATED,
    )
    assert not WorkflowPermissionService.has_view(
        user=mentioned, workflow=workflow,
    )

    # act
    service = CommentService(
        instance=comment, user=owner, is_superuser=False,
    )
    service.update(
        text=f'Hey [User| {mentioned.id}] check',
        force_save=True,
    )

    # assert
    assert WorkflowPermissionService.has_view(
        user=mentioned, workflow=workflow,
    )


# ── CommentService.delete — attachment Guardian ───────────


def test_comment_delete__clears_attach_guardian(mocker):

    # arrange
    clear_guardian_perms_mock = mocker.patch(
        'src.processes.services.events'
        '.clear_guardian_permissions_for_attachment_ids',
    )

    # suppressed — not part of test scope
    mocker.patch(
        'src.processes.services.events'
        '.send_event_updated.delay',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    template.tasks.first().add_raw_performer(owner)
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    task = workflow.tasks.first()
    task.update_performers(restore_performers=True)
    task.status = 'active'
    task.save(update_fields=['status'])
    comment = WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text='Some comment',
        status=CommentStatus.CREATED,
    )

    # act
    service = CommentService(
        instance=comment, user=owner, is_superuser=False,
    )
    service.delete()

    # assert
    clear_guardian_perms_mock.assert_called_once_with([])


def test_comment_delete_with_attach__passes_ids(mocker):

    # arrange
    clear_guardian_perms_mock = mocker.patch(
        'src.processes.services.events'
        '.clear_guardian_permissions_for_attachment_ids',
    )

    # suppressed — not part of test scope
    mocker.patch(
        'src.processes.services.events'
        '.send_event_updated.delay',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    template.tasks.first().add_raw_performer(owner)
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    task = workflow.tasks.first()
    task.update_performers(restore_performers=True)
    task.status = 'active'
    task.save(update_fields=['status'])
    comment = WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text='With attachment',
        status=CommentStatus.CREATED,
    )
    attachment = Attachment.objects.create(
        file_id='test-file-123',
        account=account,
        event=comment,
        task=task,
        workflow=workflow,
        source_type='task',
        access_type='restricted',
    )

    # act
    service = CommentService(
        instance=comment, user=owner, is_superuser=False,
    )
    service.delete()

    # assert
    clear_guardian_perms_mock.assert_called_once_with(
        [attachment.id],
    )


# ── WorkflowCreation — set_owners lifecycle ───────────────


def test_wf_create__tmpl_owner_gets_manage():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )

    # act
    workflow = create_test_workflow(
        user=owner, template=template,
    )

    # assert
    assert WorkflowPermissionService.has_manage(
        user=owner, workflow=workflow,
    )
    assert WorkflowPermissionService.has_view(
        user=owner, workflow=workflow,
    )


def test_wf_create__multiple_tmpl_owners():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    TemplateOwner.objects.create(
        template=template, type=OwnerType.USER, user=admin,
        account=account,
    )

    # act
    workflow = create_test_workflow(
        user=owner, template=template,
    )

    # assert
    assert WorkflowPermissionService.has_manage(
        user=owner, workflow=workflow,
    )
    assert WorkflowPermissionService.has_manage(
        user=admin, workflow=workflow,
    )
    ids = WorkflowPermissionService.get_owner_ids(workflow=workflow)
    assert set(ids) == {owner.id, admin.id}


# ── VersionService — set_owners on update ─────────────────


def test_version_update__sets_owners_from_tmpl(mocker):

    # arrange

    # suppressed — not part of test scope
    mocker.patch(
        'src.processes.services.workflows.workflow_version'
        '.send_task_deleted_notification.delay',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    TemplateOwner.objects.create(
        template=template, type=OwnerType.USER, user=admin,
        account=account,
    )
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    WorkflowPermissionService.set_owners(
        workflow=workflow, user_ids=[owner.id],
    )
    assert not WorkflowPermissionService.has_manage(
        user=admin, workflow=workflow,
    )
    tmpl_owner_ids = list(
        TemplateOwner.objects.filter(
            template=template,
            is_deleted=False,
            type=OwnerType.USER,
            user__isnull=False,
        ).values_list('user_id', flat=True),
    )

    # act
    WorkflowPermissionService.set_owners(
        workflow, tmpl_owner_ids,
    )

    # assert
    assert WorkflowPermissionService.has_manage(
        user=owner, workflow=workflow,
    )
    assert WorkflowPermissionService.has_manage(
        user=admin, workflow=workflow,
    )


def test_version_update__removed_owner__loses_manage():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    WorkflowPermissionService.set_owners(
        workflow=workflow, user_ids=[owner.id, admin.id],
    )
    assert WorkflowPermissionService.has_manage(
        user=admin, workflow=workflow,
    )
    tmpl_owner_ids = list(
        TemplateOwner.objects.filter(
            template=template,
            is_deleted=False,
            type=OwnerType.USER,
            user__isnull=False,
        ).values_list('user_id', flat=True),
    )

    # act
    WorkflowPermissionService.set_owners(
        workflow, tmpl_owner_ids,
    )

    # assert
    assert WorkflowPermissionService.has_manage(
        user=owner, workflow=workflow,
    )
    assert not WorkflowPermissionService.has_manage(
        user=admin, workflow=workflow,
    )


# ── Task.update_performers — grant_view_bulk ──────────────


def test_update_performers__grants_view():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(
        account=account, email='perf@t.t',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    template.tasks.first().add_raw_performer(user=user)

    # act
    workflow = create_test_workflow(
        user=owner, template=template,
    )

    # assert
    assert WorkflowPermissionService.has_view(
        user=user, workflow=workflow,
    )


# ── Serializer get_owners ─────────────────────────────────


def test_get_owner_ids__returns_guardian_ids():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)

    # act
    WorkflowPermissionService.set_owners(
        workflow=workflow, user_ids=[owner.id, admin.id],
    )

    # assert
    ids = WorkflowPermissionService.get_owner_ids(workflow=workflow)
    assert set(ids) == {owner.id, admin.id}


def test_get_owner_ids__empty_after_clear():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService.grant_manage(user=owner, workflow=workflow)
    assert WorkflowPermissionService.get_owner_ids(
        workflow=workflow,
    ) != []

    # act
    WorkflowPermissionService.set_owners(workflow=workflow, user_ids=[])

    # assert
    assert WorkflowPermissionService.get_owner_ids(
        workflow=workflow,
    ) == []


# ── CommentService — mention revocation ───────────────────


def test_comment_update__remove_mention__revokes_view(mocker):

    # arrange

    # suppressed — not part of test scope
    mocker.patch(
        'src.processes.services.events'
        '.send_mention_notification.delay',
    )
    mocker.patch(
        'src.processes.services.events'
        '.send_event_updated.delay',
    )
    mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    mocker.patch(
        'src.storage.tasks'
        '.sync_workflow_attachment_permissions.delay',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    mentioned = create_test_not_admin(
        account=account, email='mentioned@t.t',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    template.tasks.first().add_raw_performer(owner)
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    task = workflow.tasks.first()
    task.update_performers(restore_performers=True)
    task.status = TaskStatus.ACTIVE
    task.save(update_fields=['status'])
    comment = WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text=f'Hey [User| {mentioned.id}]',
        status=CommentStatus.CREATED,
    )
    WorkflowPermissionService.set_viewers(workflow=workflow)
    assert WorkflowPermissionService.has_view(
        user=mentioned, workflow=workflow,
    )

    # act
    service = CommentService(
        instance=comment, user=owner, is_superuser=False,
    )
    service.update(
        text='Hey everyone',
        force_save=True,
    )

    # assert
    assert not WorkflowPermissionService.has_view(
        user=mentioned, workflow=workflow,
    )
    assert_no_guardian_view(workflow, mentioned)


def test_comment_update__replace_mention__old_revoked(mocker):

    # arrange

    # suppressed — not part of test scope
    mocker.patch(
        'src.processes.services.events'
        '.send_mention_notification.delay',
    )
    mocker.patch(
        'src.processes.services.events'
        '.send_event_updated.delay',
    )
    mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    mocker.patch(
        'src.storage.tasks'
        '.sync_workflow_attachment_permissions.delay',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    user_old = create_test_not_admin(
        account=account, email='old@t.t',
    )
    user_new = create_test_not_admin(
        account=account, email='new@t.t',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    template.tasks.first().add_raw_performer(owner)
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    task = workflow.tasks.first()
    task.update_performers(restore_performers=True)
    task.status = TaskStatus.ACTIVE
    task.save(update_fields=['status'])
    comment = WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text=f'Hey [Old| {user_old.id}]',
        status=CommentStatus.CREATED,
    )
    WorkflowPermissionService.set_viewers(workflow=workflow)
    assert WorkflowPermissionService.has_view(
        user=user_old, workflow=workflow,
    )

    # act
    service = CommentService(
        instance=comment, user=owner, is_superuser=False,
    )
    service.update(
        text=f'Hey [New| {user_new.id}]',
        force_save=True,
    )

    # assert
    assert not WorkflowPermissionService.has_view(
        user=user_old, workflow=workflow,
    )
    assert_no_guardian_view(workflow, user_old)
    assert WorkflowPermissionService.has_view(
        user=user_new, workflow=workflow,
    )
    assert_guardian_view(workflow, user_new)


def test_comment_update__remove_mention__still_performer(mocker):

    # arrange

    # suppressed — not part of test scope
    mocker.patch(
        'src.processes.services.events'
        '.send_mention_notification.delay',
    )
    mocker.patch(
        'src.processes.services.events'
        '.send_event_updated.delay',
    )
    mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    mocker.patch(
        'src.storage.tasks'
        '.sync_workflow_attachment_permissions.delay',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    performer = create_test_not_admin(
        account=account, email='perf@t.t',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    template.tasks.first().add_raw_performer(owner)
    template.tasks.first().add_raw_performer(performer)
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    task = workflow.tasks.first()
    task.update_performers(restore_performers=True)
    task.status = TaskStatus.ACTIVE
    task.save(update_fields=['status'])
    comment = WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text=f'Hey [Perf| {performer.id}]',
        status=CommentStatus.CREATED,
    )
    WorkflowPermissionService.set_viewers(workflow=workflow)
    assert WorkflowPermissionService.has_view(
        user=performer, workflow=workflow,
    )

    # act
    service = CommentService(
        instance=comment, user=owner, is_superuser=False,
    )
    service.update(
        text='Hey team',
        force_save=True,
    )

    # assert — still has view because performer role remains
    assert WorkflowPermissionService.has_view(
        user=performer, workflow=workflow,
    )
    assert_guardian_view(workflow, performer)


def test_comment_delete__mentioned_user__revokes_view(mocker):

    # arrange

    # suppressed — not part of test scope
    mocker.patch(
        'src.processes.services.events'
        '.send_event_updated.delay',
    )
    mocker.patch(
        'src.storage.tasks'
        '.sync_workflow_attachment_permissions.delay',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    mentioned = create_test_not_admin(
        account=account, email='mentioned@t.t',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    template.tasks.first().add_raw_performer(owner)
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    task = workflow.tasks.first()
    task.update_performers(restore_performers=True)
    task.status = TaskStatus.ACTIVE
    task.save(update_fields=['status'])
    comment = WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text=f'[User| {mentioned.id}]',
        status=CommentStatus.CREATED,
    )
    WorkflowPermissionService.set_viewers(workflow=workflow)
    assert WorkflowPermissionService.has_view(
        user=mentioned, workflow=workflow,
    )

    # act
    service = CommentService(
        instance=comment, user=owner, is_superuser=False,
    )
    service.delete()

    # assert
    assert not WorkflowPermissionService.has_view(
        user=mentioned, workflow=workflow,
    )
    assert_no_guardian_view(workflow, mentioned)


def test_comment_delete__mentioned_in_two__keeps_view(mocker):

    # arrange

    # suppressed — not part of test scope
    mocker.patch(
        'src.processes.services.events'
        '.send_event_updated.delay',
    )
    mocker.patch(
        'src.storage.tasks'
        '.sync_workflow_attachment_permissions.delay',
    )
    account = create_test_account()
    owner = create_test_owner(account=account)
    mentioned = create_test_not_admin(
        account=account, email='mentioned@t.t',
    )
    template = create_test_template(
        user=owner, is_active=True, tasks_count=1,
    )
    template.tasks.first().add_raw_performer(owner)
    workflow = create_test_workflow(
        user=owner, template=template,
    )
    task = workflow.tasks.first()
    task.update_performers(restore_performers=True)
    task.status = TaskStatus.ACTIVE
    task.save(update_fields=['status'])
    comment_1 = WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text=f'[User| {mentioned.id}] first',
        status=CommentStatus.CREATED,
    )
    WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        workflow=workflow,
        user=owner,
        task=task,
        text=f'[User| {mentioned.id}] second',
        status=CommentStatus.CREATED,
    )
    WorkflowPermissionService.set_viewers(workflow=workflow)
    assert WorkflowPermissionService.has_view(
        user=mentioned, workflow=workflow,
    )

    # act — delete only the first comment
    service = CommentService(
        instance=comment_1, user=owner, is_superuser=False,
    )
    service.delete()

    # assert — still has view via second comment
    assert WorkflowPermissionService.has_view(
        user=mentioned, workflow=workflow,
    )
    assert_guardian_view(workflow, mentioned)
