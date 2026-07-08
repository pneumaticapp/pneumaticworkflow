import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from src.permissions.enums import PermissionSource
from src.permissions.models import UserObjectPermission

from src.permissions.models import GroupObjectPermission
from src.processes.tests.fixtures import (
    create_test_admin,
    create_test_attachment,
    create_test_event,
    create_test_group,
    create_test_not_admin,
    create_test_workflow,
)
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment
from src.storage.services.attachments import AttachmentService

pytestmark = pytest.mark.django_db


def test_bulk_create_scope__same_file_same_task__skip():
    """Same file_id in the same task scope creates only one
    attachment (deduplication)."""

    # arrange
    owner = create_test_admin()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    service = AttachmentService(user=owner)

    service.bulk_create_for_scope(
        file_ids=['file_A'],
        account=owner.account,
        source_type=SourceType.TASK,
        task=task,
    )

    # act
    result = service.bulk_create_for_scope(
        file_ids=['file_A'],
        account=owner.account,
        source_type=SourceType.TASK,
        task=task,
    )

    # assert
    assert result == []
    assert Attachment.objects.filter(
        file_id='file_A',
        task=task,
    ).count() == 1


def test_bulk_create_scope__same_file_diff_tasks__both():
    """Same file_id in different task scopes creates independent
    attachments."""

    # arrange
    owner = create_test_admin()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    task_1 = workflow.tasks.all()[0]
    task_2 = workflow.tasks.all()[1]
    service = AttachmentService(user=owner)
    result_1 = service.bulk_create_for_scope(
        file_ids=['file_B'],
        account=owner.account,
        source_type=SourceType.TASK,
        task=task_1,
    )

    # act
    result_2 = service.bulk_create_for_scope(
        file_ids=['file_B'],
        account=owner.account,
        source_type=SourceType.TASK,
        task=task_2,
    )

    # assert
    assert len(result_1) == 1
    assert len(result_2) == 1
    assert result_1[0].task == task_1
    assert result_2[0].task == task_2
    assert Attachment.objects.filter(file_id='file_B').count() == 2


def test_bulk_create_scope__same_file_tpl_and_task__both():
    """Same file_id in template scope and task scope creates
    independent attachments (cross-scope)."""

    # arrange
    owner = create_test_admin()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    template = workflow.template
    service = AttachmentService(user=owner)
    result_tpl = service.bulk_create_for_scope(
        file_ids=['file_C'],
        account=owner.account,
        source_type=SourceType.TEMPLATE,
        template=template,
    )

    # act
    result_task = service.bulk_create_for_scope(
        file_ids=['file_C'],
        account=owner.account,
        source_type=SourceType.TASK,
        task=task,
    )

    # assert
    assert len(result_tpl) == 1
    assert len(result_task) == 1
    assert result_tpl[0].template == template
    assert result_task[0].task == task
    assert Attachment.objects.filter(file_id='file_C').count() == 2


def test_bulk_create_event__same_file_same_event__skip():
    """Same file_id in the same event scope creates only one
    attachment."""

    # arrange
    owner = create_test_admin()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    event = create_test_event(
        workflow=workflow,
        user=owner,
    )
    service = AttachmentService(user=owner)

    service.bulk_create_for_event(
        file_ids=['file_D'],
        account=owner.account,
        source_type=SourceType.TASK,
        event=event,
    )

    # act
    result = service.bulk_create_for_event(
        file_ids=['file_D'],
        account=owner.account,
        source_type=SourceType.TASK,
        event=event,
    )

    # assert
    assert result == []
    assert Attachment.objects.filter(
        file_id='file_D',
        event=event,
    ).count() == 1


def test_bulk_create_event__same_file_diff_events__both():
    """Same file_id in different event scopes creates independent
    attachments."""

    # arrange
    owner = create_test_admin()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    event_1 = create_test_event(
        workflow=workflow,
        user=owner,
    )
    event_2 = create_test_event(
        workflow=workflow,
        user=owner,
    )
    service = AttachmentService(user=owner)

    result_1 = service.bulk_create_for_event(
        file_ids=['file_E'],
        account=owner.account,
        source_type=SourceType.TASK,
        event=event_1,
    )

    # act
    result_2 = service.bulk_create_for_event(
        file_ids=['file_E'],
        account=owner.account,
        source_type=SourceType.TASK,
        event=event_2,
    )

    # assert
    assert len(result_1) == 1
    assert len(result_2) == 1
    assert result_1[0].event == event_1
    assert result_2[0].event == event_2
    assert Attachment.objects.filter(file_id='file_E').count() == 2


def test_check_perm__multi_att_perm_on_one__ok():
    """When multiple attachments exist for the same file_id across
    scopes, access is granted if user has permission on ANY one."""

    # arrange
    owner = create_test_admin()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    task_1 = workflow.tasks.all()[0]
    task_2 = workflow.tasks.all()[1]

    # attachment in task_1 — user has NO perm
    create_test_attachment(
        account=owner.account,
        file_id='file_F',
        task=task_1,
        access_type=AccessType.RESTRICTED,
    )

    # attachment in task_2 — user HAS perm
    att_2 = create_test_attachment(
        account=owner.account,
        file_id='file_F',
        task=task_2,
        access_type=AccessType.RESTRICTED,
    )
    att_ctype = ContentType.objects.get_for_model(att_2)
    att_perm = Permission.objects.get(
        content_type=att_ctype,
        codename='access_attachment',
    )
    UserObjectPermission.objects.create(
        user=owner,
        permission=att_perm,
        content_type=att_ctype,
        object_pk=str(att_2.pk),
        source_type=PermissionSource.PERFORMER,
        source_id='0',
    )

    service = AttachmentService(user=owner)

    # act
    result = service.check_user_permission(
        user_id=owner.id,
        account_id=owner.account_id,
        file_id='file_F',
    )

    # assert
    assert result is True


def test_check_perm__multi_att_no_perm__denied():
    """When multiple RESTRICTED attachments exist for the same
    file_id and user has permission on NONE, access is denied."""

    # arrange
    owner = create_test_admin()
    workflow = create_test_workflow(user=owner, tasks_count=2)
    task_1 = workflow.tasks.all()[0]
    task_2 = workflow.tasks.all()[1]

    create_test_attachment(
        account=owner.account,
        file_id='file_G',
        task=task_1,
        access_type=AccessType.RESTRICTED,
    )
    create_test_attachment(
        account=owner.account,
        file_id='file_G',
        task=task_2,
        access_type=AccessType.RESTRICTED,
    )

    # create a different user without any perms
    viewer = create_test_admin(
        email='viewer@pneumatic.app',
        account=owner.account,
    )
    service = AttachmentService(user=viewer)

    # act
    result = service.check_user_permission(
        user_id=viewer.id,
        account_id=viewer.account_id,
        file_id='file_G',
    )

    # assert
    assert result is False


def test_bulk_create_scope__soft_deleted__creates_new():
    """When existing attachment is soft-deleted in the scope,
    bulk_create should create a new one (soft-deleted records
    are excluded from the active queryset)."""

    # arrange
    owner = create_test_admin()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()

    # create and soft-delete
    att = create_test_attachment(
        account=owner.account,
        file_id='file_H',
        task=task,
        access_type=AccessType.RESTRICTED,
    )
    att.is_deleted = True
    att.save(update_fields=['is_deleted'])

    service = AttachmentService(user=owner)

    # act
    result = service.bulk_create_for_scope(
        file_ids=['file_H'],
        account=owner.account,
        source_type=SourceType.TASK,
        task=task,
    )

    # assert
    assert len(result) == 1
    assert result[0].file_id == 'file_H'
    assert result[0].task == task
    assert result[0].is_deleted is False


def test_bulk_create_scope__two_wf_same_tpl__independent():
    """Two workflows from the same template create independent
    task-level attachments for the same file_id. Deleting one
    does not affect the other."""

    # arrange
    owner = create_test_admin()
    workflow_1 = create_test_workflow(user=owner, tasks_count=1)
    workflow_2 = create_test_workflow(
        user=owner,
        template=workflow_1.template,
        tasks_count=1,
    )
    task_1 = workflow_1.tasks.first()
    task_2 = workflow_2.tasks.first()
    service = AttachmentService(user=owner)

    service.bulk_create_for_scope(
        file_ids=['file_I'],
        account=owner.account,
        source_type=SourceType.TASK,
        task=task_1,
    )
    service.bulk_create_for_scope(
        file_ids=['file_I'],
        account=owner.account,
        source_type=SourceType.TASK,
        task=task_2,
    )

    # act
    att_1 = Attachment.objects.get(
        file_id='file_I',
        task=task_1,
    )
    att_1.is_deleted = True
    att_1.save(update_fields=['is_deleted'])

    # assert
    att_2 = Attachment.objects.get(
        file_id='file_I',
        task=task_2,
    )
    assert att_2.is_deleted is False


def test_check_perm__multi_att_one_public__ok():
    """If one attachment for file_id is PUBLIC and another is
    RESTRICTED without permission, access is still granted
    via the PUBLIC record."""

    # arrange
    owner = create_test_admin()

    # PUBLIC attachment (no scope)
    create_test_attachment(
        account=owner.account,
        file_id='file_J',
        access_type=AccessType.PUBLIC,
        source_type=SourceType.ACCOUNT,
    )

    # RESTRICTED attachment (no perm assigned)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    create_test_attachment(
        account=owner.account,
        file_id='file_J',
        task=task,
        access_type=AccessType.RESTRICTED,
    )

    viewer = create_test_admin(
        email='viewer@pneumatic.app',
        account=owner.account,
    )
    service = AttachmentService(user=viewer)

    # act
    result = service.check_user_permission(
        user_id=viewer.id,
        account_id=viewer.account_id,
        file_id='file_J',
    )

    # assert
    assert result is True


def test_bulk_create_scope__same_file_same_wf__skip():
    """Same file_id in the same workflow scope creates only one
    attachment (deduplication)."""

    # arrange
    owner = create_test_admin()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    service = AttachmentService(user=owner)

    service.bulk_create_for_scope(
        file_ids=['file_K'],
        account=owner.account,
        source_type=SourceType.WORKFLOW,
        workflow=workflow,
    )

    # act
    result = service.bulk_create_for_scope(
        file_ids=['file_K'],
        account=owner.account,
        source_type=SourceType.WORKFLOW,
        workflow=workflow,
    )

    # assert
    assert result == []
    assert Attachment.objects.filter(
        file_id='file_K',
        workflow=workflow,
    ).count() == 1


def test_bulk_create_scope__partial_existing__only_new():
    """When some file_ids already exist in scope, only new
    ones are created."""

    # arrange
    owner = create_test_admin()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    service = AttachmentService(user=owner)

    service.bulk_create_for_scope(
        file_ids=['existing_1', 'existing_2'],
        account=owner.account,
        source_type=SourceType.TASK,
        task=task,
    )

    # act
    result = service.bulk_create_for_scope(
        file_ids=['existing_1', 'new_1', 'existing_2', 'new_2'],
        account=owner.account,
        source_type=SourceType.TASK,
        task=task,
    )

    # assert
    assert len(result) == 2
    created_ids = {att.file_id for att in result}
    assert created_ids == {'new_1', 'new_2'}
    assert Attachment.objects.filter(task=task).count() == 4


def test_bulk_create_event__vs_task_scope__both():
    """Same file_id in event scope and task scope creates
    independent attachments."""

    # arrange
    owner = create_test_admin()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    event = create_test_event(
        workflow=workflow,
        user=owner,
    )
    service = AttachmentService(user=owner)
    result_task = service.bulk_create_for_scope(
        file_ids=['file_L'],
        account=owner.account,
        source_type=SourceType.TASK,
        task=task,
    )

    # act
    result_event = service.bulk_create_for_event(
        file_ids=['file_L'],
        account=owner.account,
        source_type=SourceType.TASK,
        event=event,
    )

    # assert
    assert len(result_task) == 1
    assert len(result_event) == 1
    assert result_task[0].event is None
    assert result_event[0].event == event
    assert Attachment.objects.filter(
        file_id='file_L',
    ).count() == 2


def test_check_perm__soft_deleted_att__not_granting():
    """Soft-deleted attachments are excluded by
    BaseSoftDeleteManager and do not grant access."""

    # arrange
    owner = create_test_admin()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()

    att = create_test_attachment(
        account=owner.account,
        file_id='file_M',
        task=task,
        access_type=AccessType.RESTRICTED,
    )
    att_ctype = ContentType.objects.get_for_model(att)
    att_perm = Permission.objects.get(
        content_type=att_ctype,
        codename='access_attachment',
    )
    UserObjectPermission.objects.create(
        user=owner,
        permission=att_perm,
        content_type=att_ctype,
        object_pk=str(att.pk),
        source_type=PermissionSource.PERFORMER,
        source_id='0',
    )

    # soft-delete
    att.is_deleted = True
    att.save(update_fields=['is_deleted'])

    service = AttachmentService(user=owner)

    # act
    result = service.check_user_permission(
        user_id=owner.id,
        account_id=owner.account_id,
        file_id='file_M',
    )

    # assert
    assert result is False


def test_check_perm__group_perm_multi_att__ok():
    """When multiple attachments exist and user has access via
    group permission on one of them, access is granted."""

    # arrange
    owner = create_test_admin(email='owner@pneumatic.app')
    member = create_test_not_admin(
        email='member@pneumatic.app',
        account=owner.account,
    )
    group = create_test_group(
        account=owner.account,
        users=[member],
    )
    workflow = create_test_workflow(user=owner, tasks_count=2)
    task_1 = workflow.tasks.all()[0]
    task_2 = workflow.tasks.all()[1]

    # attachment without any perm
    create_test_attachment(
        account=owner.account,
        file_id='file_N',
        task=task_1,
        access_type=AccessType.RESTRICTED,
    )

    # attachment with group perm
    att_2 = create_test_attachment(
        account=owner.account,
        file_id='file_N',
        task=task_2,
        access_type=AccessType.RESTRICTED,
    )

    ctype = ContentType.objects.get_for_model(Attachment)
    perm = Permission.objects.get(
        content_type=ctype,
        codename='access_attachment',
    )
    GroupObjectPermission.objects.create(
        group=group,
        permission=perm,
        content_type=ctype,
        object_pk=str(att_2.pk),
    )

    service = AttachmentService(user=member)

    # act
    result = service.check_user_permission(
        user_id=member.id,
        account_id=member.account_id,
        file_id='file_N',
    )

    # assert
    assert result is True


def test_tpl_cascade_delete__task_att_survives():
    """When template is deleted (CASCADE), template-level
    attachment is removed but task-level attachment with the
    same file_id survives."""

    # arrange
    owner = create_test_admin()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    template = workflow.template

    create_test_attachment(
        account=owner.account,
        file_id='file_O',
        template=template,
        source_type=SourceType.TEMPLATE,
    )
    task_att = create_test_attachment(
        account=owner.account,
        file_id='file_O',
        task=task,
        source_type=SourceType.TASK,
    )
    task_att_id = task_att.id

    # act
    template.delete()

    # assert
    assert not Attachment.objects.filter(
        file_id='file_O',
        source_type=SourceType.TEMPLATE,
    ).exists()
    assert Attachment.objects.filter(id=task_att_id).exists()


def test_bulk_create_scope__empty_file_ids__ok():
    """Empty file_ids list returns empty result without
    errors."""

    # arrange
    owner = create_test_admin()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()
    service = AttachmentService(user=owner)

    # act
    result = service.bulk_create_for_scope(
        file_ids=[],
        account=owner.account,
        source_type=SourceType.TASK,
        task=task,
    )

    # assert
    assert result == []
    assert Attachment.objects.filter(task=task).count() == 0


def test_check_perm__account_type_multi_att__ok():
    """When ACCOUNT-type and RESTRICTED-type attachments coexist
    for the same file_id, same-account user gets access via
    the ACCOUNT record."""

    # arrange
    owner = create_test_admin()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.first()

    create_test_attachment(
        account=owner.account,
        file_id='file_P',
        access_type=AccessType.ACCOUNT,
        source_type=SourceType.ACCOUNT,
    )
    create_test_attachment(
        account=owner.account,
        file_id='file_P',
        task=task,
        access_type=AccessType.RESTRICTED,
    )

    viewer = create_test_not_admin(
        email='viewer@pneumatic.app',
        account=owner.account,
    )
    service = AttachmentService(user=viewer)

    # act
    result = service.check_user_permission(
        user_id=viewer.id,
        account_id=viewer.account_id,
        file_id='file_P',
    )

    # assert
    assert result is True
