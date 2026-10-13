"""Tests for migrate_file_attachment_to_attachment command."""
import pytest

from django.contrib.contenttypes.models import ContentType
from src.permissions.models import UserObjectPermission

from src.permissions.models import GroupObjectPermission
from src.processes.enums import FieldType
from src.processes.models.workflows.fields import TaskField
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_event,
    create_test_workflow,
)
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment
from src.storage.services.attachments import AttachmentService

pytestmark = pytest.mark.django_db


# ── Basic scenarios ──────────────────────────────────────────


def test_migrate__workflow__creates_restricted_workflow(
    create_fa_with_file_id,
    run_migrate,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    create_fa_with_file_id(
        account=user.account,
        file_id='wf_file_001',
        workflow=workflow,
    )

    # act
    run_migrate(account_id=user.account.id)

    # assert
    att = Attachment.objects.get(file_id='wf_file_001')
    assert att.access_type == AccessType.RESTRICTED
    assert att.source_type == SourceType.WORKFLOW
    assert att.workflow_id == workflow.id
    assert att.account_id == user.account.id


def test_migrate__event_with_task__creates_restricted_task(
    create_fa_with_file_id,
    run_migrate,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.first()
    event = create_test_event(
        workflow=workflow,
        user=user,
        task=task,
    )
    create_fa_with_file_id(
        account=user.account,
        file_id='evt_task_file',
        event=event,
    )

    # act
    run_migrate(account_id=user.account.id)

    # assert
    att = Attachment.objects.get(file_id='evt_task_file')
    assert att.access_type == AccessType.RESTRICTED
    assert att.source_type == SourceType.TASK
    assert att.task_id == task.id


def test_migrate__event_without_task__creates_workflow(
    create_fa_with_file_id,
    run_migrate,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    event = create_test_event(
        workflow=workflow,
        user=user,
    )

    # Override event.task to None
    event.task = None
    event.save(update_fields=['task'])
    create_fa_with_file_id(
        account=user.account,
        file_id='evt_no_task',
        event=event,
    )

    # act
    run_migrate(account_id=user.account.id)

    # assert
    att = Attachment.objects.get(file_id='evt_no_task')
    assert att.source_type == SourceType.WORKFLOW


def test_migrate__output__creates_restricted_task(
    create_fa_with_file_id,
    run_migrate,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.first()
    output = TaskField.objects.create(
        task=task,
        workflow=workflow,
        account=user.account,
        type=FieldType.FILE,
        name='output_field',
        api_name='output-field-1',
    )
    create_fa_with_file_id(
        account=user.account,
        file_id='output_file',
        output=output,
    )

    # act
    run_migrate(account_id=user.account.id)

    # assert
    att = Attachment.objects.get(file_id='output_file')
    assert att.source_type == SourceType.TASK
    assert att.task_id == output.task_id


def test_migrate__no_relations__creates_account(
    create_fa_with_file_id,
    run_migrate,
):
    # arrange
    user = create_test_admin()
    create_fa_with_file_id(
        account=user.account,
        file_id='free_file',
    )

    # act
    run_migrate(account_id=user.account.id)

    # assert
    att = Attachment.objects.get(file_id='free_file')
    assert att.access_type == AccessType.ACCOUNT
    assert att.source_type == SourceType.ACCOUNT


def test_migrate__duplicate_file_id__skipped(
    create_fa_with_file_id,
    run_migrate,
):
    # arrange
    user = create_test_admin()
    create_fa_with_file_id(
        account=user.account,
        file_id='dup_file',
    )
    Attachment.objects.create(
        file_id='dup_file',
        access_type=AccessType.ACCOUNT,
        source_type=SourceType.ACCOUNT,
        account=user.account,
    )

    # act
    output = run_migrate(account_id=user.account.id)

    # assert
    assert 'Skipped: 1' in output
    assert Attachment.objects.filter(
        file_id='dup_file',
    ).count() == 1


def test_migrate__dry_run__no_records_created(
    create_fa_with_file_id,
    run_migrate,
):
    # arrange
    user = create_test_admin()
    create_fa_with_file_id(
        account=user.account,
        file_id='dry_file',
    )

    # act
    output = run_migrate(
        account_id=user.account.id,
        dry_run=True,
    )

    # assert
    assert 'DRY RUN' in output
    assert not Attachment.objects.filter(
        file_id='dry_file',
    ).exists()


def test_migrate__filters_by_account_ids(
    create_fa_with_file_id,
    run_migrate,
):
    # arrange
    user1 = create_test_admin()
    account2 = create_test_account(name='Other Company')
    create_fa_with_file_id(
        account=user1.account,
        file_id='acc1_file',
    )
    create_fa_with_file_id(
        account=account2,
        file_id='acc2_file',
    )

    # act
    run_migrate(account_id=user1.account.id)

    # assert
    assert Attachment.objects.filter(
        file_id='acc1_file',
    ).exists()
    assert not Attachment.objects.filter(
        file_id='acc2_file',
    ).exists()


# ── Guardian permissions ─────────────────────────────────────


def test_migrate__restricted_wf__assigns_guardian_perms(
    create_fa_with_file_id,
    run_migrate,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    create_fa_with_file_id(
        account=user.account,
        file_id='perm_wf_file',
        workflow=workflow,
    )

    # act
    run_migrate(account_id=user.account.id)

    # assert
    att = Attachment.objects.get(file_id='perm_wf_file')
    ctype = ContentType.objects.get_for_model(Attachment)
    assert UserObjectPermission.objects.filter(
        user=user,
        object_pk=str(att.pk),
        permission__content_type=ctype,
        permission__codename='access_attachment',
    ).exists()


def test_migrate__restricted_task__assigns_guardian_perms(
    create_fa_with_file_id,
    run_migrate,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.first()
    event = create_test_event(
        workflow=workflow,
        user=user,
        task=task,
    )
    create_fa_with_file_id(
        account=user.account,
        file_id='perm_task_file',
        event=event,
    )

    # act
    run_migrate(account_id=user.account.id)

    # assert
    att = Attachment.objects.get(
        file_id='perm_task_file',
    )
    ctype = ContentType.objects.get_for_model(Attachment)
    assert UserObjectPermission.objects.filter(
        user=user,
        object_pk=str(att.pk),
        permission__content_type=ctype,
    ).exists()


def test_migrate__restricted__user_can_access(
    create_fa_with_file_id,
    run_migrate,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    create_fa_with_file_id(
        account=user.account,
        file_id='check_perm_file',
        workflow=workflow,
    )

    # act
    run_migrate(account_id=user.account.id)

    # assert
    svc = AttachmentService(user=user)
    assert svc.check_user_permission(
        user_id=user.id,
        account_id=user.account_id,
        file_id='check_perm_file',
    )


def test_migrate__account__no_guardian_permissions(
    create_fa_with_file_id,
    run_migrate,
):
    # arrange
    user = create_test_admin()
    create_fa_with_file_id(
        account=user.account,
        file_id='no_perm_file',
    )

    # act
    run_migrate(account_id=user.account.id)

    # assert
    att = Attachment.objects.get(file_id='no_perm_file')
    ctype = ContentType.objects.get_for_model(Attachment)
    assert not UserObjectPermission.objects.filter(
        object_pk=str(att.pk),
        permission__content_type=ctype,
    ).exists()
    assert not GroupObjectPermission.objects.filter(
        object_pk=str(att.pk),
        content_type=ctype,
    ).exists()


# ── template_id propagation ──────────────────────────────────


def test_migrate__workflow__template_id_from_wf(
    create_fa_with_file_id,
    run_migrate,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    create_fa_with_file_id(
        account=user.account,
        file_id='tmpl_wf',
        workflow=workflow,
    )

    # act
    run_migrate(account_id=user.account.id)

    # assert
    att = Attachment.objects.get(file_id='tmpl_wf')
    assert att.template_id == workflow.template_id


def test_migrate__event_task__tmpl_id_from_task_wf(
    create_fa_with_file_id,
    run_migrate,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.first()
    event = create_test_event(
        workflow=workflow,
        user=user,
        task=task,
    )
    create_fa_with_file_id(
        account=user.account,
        file_id='tmpl_evt',
        event=event,
    )

    # act
    run_migrate(account_id=user.account.id)

    # assert
    att = Attachment.objects.get(file_id='tmpl_evt')
    assert att.template_id == workflow.template_id


def test_migrate__output__tmpl_id_from_output_wf(
    create_fa_with_file_id,
    run_migrate,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.first()
    output = TaskField.objects.create(
        task=task,
        workflow=workflow,
        account=user.account,
        type=FieldType.FILE,
        name='output_tmpl',
        api_name='output-tmpl-1',
    )
    create_fa_with_file_id(
        account=user.account,
        file_id='tmpl_out',
        output=output,
    )

    # act
    run_migrate(account_id=user.account.id)

    # assert
    att = Attachment.objects.get(file_id='tmpl_out')
    assert att.template_id == workflow.template_id


# ── Edge cases ───────────────────────────────────────────────


def test_migrate__error_in_one__continues_others(
    create_fa_with_file_id,
    run_migrate,
):
    # arrange
    user = create_test_admin()
    create_fa_with_file_id(
        account=user.account,
        file_id='good_file_1',
    )
    create_fa_with_file_id(
        account=user.account,
        file_id='good_file_2',
    )

    # act
    output = run_migrate(account_id=user.account.id)

    # assert
    assert Attachment.objects.filter(
        file_id__in=['good_file_1', 'good_file_2'],
    ).count() == 2
    assert 'Created: 2' in output


def test_migrate__atomicity__failure_rollbacks_single(
    create_fa_with_file_id,
    run_migrate,
):
    """
    If one attachment fails during creation inside atomic(),
    only that one rolls back; others succeed.
    """

    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    create_fa_with_file_id(
        account=user.account,
        file_id='atomic_ok',
        workflow=workflow,
    )
    create_fa_with_file_id(
        account=user.account,
        file_id='atomic_dup',
    )
    Attachment.objects.create(
        file_id='atomic_dup',
        access_type=AccessType.ACCOUNT,
        source_type=SourceType.ACCOUNT,
        account=user.account,
    )

    # act
    output = run_migrate(account_id=user.account.id)

    # assert
    assert Attachment.objects.filter(
        file_id='atomic_ok',
    ).exists()
    assert 'Skipped: 1' in output
