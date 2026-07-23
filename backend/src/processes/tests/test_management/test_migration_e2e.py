"""
E2E integration tests for the full file migration pipeline.

Tests the complete data flow:
  FileAttachment(GCS URL)
    -> fill_file_attachment_file_id (extract file_id)
    -> migrate_file_attachment_to_attachment (create Attachment)
    -> replace_storage_links_with_file_service (rewrite URLs)

sync_files_to_file_service uses psycopg2 directly
and is tested with mocked database connection.
"""
import psycopg2 as real_psycopg2
import pytest
from io import StringIO
from unittest.mock import patch, MagicMock

from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.db import connection
from src.permissions.models import UserObjectPermission

from src.processes.enums import FieldType
from src.processes.models.workflows.attachment import (
    FileAttachment,
)
from src.processes.models.workflows.fields import TaskField
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_event,
    create_test_workflow,
)
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment
from src.storage.queries import AttachmentListQuery
from src.storage.services.attachments import AttachmentService
from .conftest import GCS_API, FS_DOMAIN, gcs_url

pytestmark = pytest.mark.django_db


# ═══════════════════════════════════════════════════════════
# A. Full pipeline by source_type
# ═══════════════════════════════════════════════════════════


def test_e2e__workflow_file__full_pipeline(
    create_fa,
    run_pipeline,
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
    url = gcs_url('prefix_report.pdf')
    create_fa(
        account=user.account,
        file_key='prefix_report.pdf',
        workflow=workflow,
    )
    event.text = f'See file: {url}'
    event.save(update_fields=['text'])

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    fa = FileAttachment.objects.get(
        file_id='prefix_report.pdf',
    )
    assert fa.file_id == 'prefix_report.pdf'

    att = Attachment.objects.get(
        file_id='prefix_report.pdf',
    )
    assert att.access_type == AccessType.RESTRICTED
    assert att.source_type == SourceType.WORKFLOW
    assert att.workflow_id == workflow.id

    svc = AttachmentService(user=user)
    assert svc.check_user_permission(
        user_id=user.id,
        account_id=user.account_id,
        file_id='prefix_report.pdf',
    )

    event.refresh_from_db()
    assert GCS_API not in event.text
    assert FS_DOMAIN in event.text


def test_e2e__task_event_file__full_pipeline(
    create_fa,
    run_pipeline,
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
    create_fa(
        account=user.account,
        file_key='task_file.docx',
        event=event,
    )

    # act
    run_pipeline(
        account_id=user.account.id,
        steps='fill,migrate',
    )

    # assert
    att = Attachment.objects.get(
        file_id='task_file.docx',
    )
    assert att.access_type == AccessType.RESTRICTED
    assert att.source_type == SourceType.TASK
    assert att.task_id == task.id

    svc = AttachmentService(user=user)
    assert svc.check_user_permission(
        user_id=user.id,
        account_id=user.account_id,
        file_id='task_file.docx',
    )


def test_e2e__account_file__full_pipeline(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    create_fa(
        account=user.account,
        file_key='logo_file.png',
    )

    # act
    run_pipeline(
        account_id=user.account.id,
        steps='fill,migrate',
    )

    # assert
    att = Attachment.objects.get(file_id='logo_file.png')
    assert att.access_type == AccessType.ACCOUNT
    assert att.source_type == SourceType.ACCOUNT

    ctype = ContentType.objects.get_for_model(Attachment)
    assert not UserObjectPermission.objects.filter(
        object_pk=str(att.pk),
        permission__content_type=ctype,
    ).exists()


# ═══════════════════════════════════════════════════════════
# B. Data integrity
# ═══════════════════════════════════════════════════════════


def test_e2e__file_id_preserved_across_steps(
    create_fa,
    run_fill,
    run_migrate,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    create_fa(
        account=user.account,
        file_key='chain_test.pdf',
        workflow=workflow,
    )

    # act
    run_fill(account_id=user.account.id)
    run_migrate(account_id=user.account.id)

    # assert
    fa = FileAttachment.objects.get(
        url=gcs_url('chain_test.pdf'),
    )
    att = Attachment.objects.get(file_id='chain_test.pdf')
    assert fa.file_id == att.file_id == 'chain_test.pdf'


def test_e2e__template_id_chain__wf_to_attachment(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    create_fa(
        account=user.account,
        file_key='tmpl_chain.pdf',
        workflow=workflow,
    )

    # act
    run_pipeline(
        account_id=user.account.id,
        steps='fill,migrate',
    )

    # assert
    att = Attachment.objects.get(
        file_id='tmpl_chain.pdf',
    )
    assert att.template_id == workflow.template_id
    assert att.template_id is not None


def test_e2e__multiple_accounts__isolated(
    create_fa,
    run_pipeline,
):
    # arrange
    user1 = create_test_admin()
    account2 = create_test_account(name='Company B')
    create_fa(
        account=user1.account,
        file_key='acc1.pdf',
    )
    create_fa(
        account=account2,
        file_key='acc2.pdf',
    )

    # act
    run_pipeline(
        account_id=user1.account.id,
        steps='fill,migrate',
    )

    # assert
    assert Attachment.objects.filter(
        file_id='acc1.pdf',
    ).exists()
    assert not Attachment.objects.filter(
        file_id='acc2.pdf',
    ).exists()
    fa2 = FileAttachment.objects.get(
        url=gcs_url('acc2.pdf'),
    )
    assert fa2.file_id is None


# ═══════════════════════════════════════════════════════════
# C. Permissions e2e
# ═══════════════════════════════════════════════════════════


def test_e2e__restricted__accessible_via_check(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    create_fa(
        account=user.account,
        file_key='perm_ok.pdf',
        workflow=workflow,
    )

    # act
    run_pipeline(
        account_id=user.account.id,
        steps='fill,migrate',
    )

    # assert
    svc = AttachmentService(user=user)
    assert svc.check_user_permission(
        user_id=user.id,
        account_id=user.account_id,
        file_id='perm_ok.pdf',
    )


def test_e2e__restricted__denied_for_outsider(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    create_fa(
        account=user.account,
        file_key='perm_deny.pdf',
        workflow=workflow,
    )
    account2 = create_test_account(name='Outsider Co')
    outsider = create_test_admin(
        account=account2,
        email='outsider@test.com',
    )

    # act
    run_pipeline(
        account_id=user.account.id,
        steps='fill,migrate',
    )

    # assert
    svc = AttachmentService(user=outsider)
    assert not svc.check_user_permission(
        user_id=outsider.id,
        account_id=outsider.account_id,
        file_id='perm_deny.pdf',
    )


def test_e2e__migrated_visible_in_attachment_list(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    create_fa(
        account=user.account,
        file_key='list_test.pdf',
        workflow=workflow,
    )

    # act
    run_pipeline(
        account_id=user.account.id,
        steps='fill,migrate',
    )

    # assert
    query = AttachmentListQuery(
        user=user,
        limit=100,
    )
    sql, params = query.get_sql()
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        columns = [
            col[0] for col in cursor.description
        ]
        rows = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    file_ids = [r['file_id'] for r in rows]
    assert 'list_test.pdf' in file_ids


# ═══════════════════════════════════════════════════════════
# D. Multiple files and mixed types
# ═══════════════════════════════════════════════════════════


def test_e2e__wf_multiple_files__all_migrated(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    for i in range(3):
        create_fa(
            account=user.account,
            file_key=f'multi_{i}.pdf',
            workflow=workflow,
        )

    # act
    run_pipeline(
        account_id=user.account.id,
        steps='fill,migrate',
    )

    # assert
    for i in range(3):
        att = Attachment.objects.get(
            file_id=f'multi_{i}.pdf',
        )
        assert att.access_type == AccessType.RESTRICTED
        assert att.source_type == SourceType.WORKFLOW


def test_e2e__mixed_access__correct_permissions(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    create_fa(
        account=user.account,
        file_key='mixed_restricted.pdf',
        workflow=workflow,
    )
    create_fa(
        account=user.account,
        file_key='mixed_account.pdf',
    )

    # act
    run_pipeline(
        account_id=user.account.id,
        steps='fill,migrate',
    )

    # assert
    restricted = Attachment.objects.get(
        file_id='mixed_restricted.pdf',
    )
    account = Attachment.objects.get(
        file_id='mixed_account.pdf',
    )
    assert restricted.access_type == AccessType.RESTRICTED
    assert account.access_type == AccessType.ACCOUNT

    ctype = ContentType.objects.get_for_model(Attachment)
    assert UserObjectPermission.objects.filter(
        object_pk=str(restricted.pk),
        permission__content_type=ctype,
    ).exists()
    assert not UserObjectPermission.objects.filter(
        object_pk=str(account.pk),
        permission__content_type=ctype,
    ).exists()


def test_e2e__output_attachment__full_pipeline(
    create_fa,
    run_pipeline,
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
        name='doc',
        api_name='output-doc-1',
    )
    create_fa(
        account=user.account,
        file_key='output_e2e.pdf',
        output=output,
    )

    # act
    run_pipeline(
        account_id=user.account.id,
        steps='fill,migrate',
    )

    # assert
    att = Attachment.objects.get(
        file_id='output_e2e.pdf',
    )
    assert att.source_type == SourceType.TASK
    assert att.task_id == task.id


def test_e2e__multi_task_wf__each_task_migrated(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=3,
    )
    tasks = list(workflow.tasks.order_by('number'))
    for i, task in enumerate(tasks):
        event = create_test_event(
            workflow=workflow,
            user=user,
            task=task,
        )
        create_fa(
            account=user.account,
            file_key=f'task{i}_file.pdf',
            event=event,
        )

    # act
    run_pipeline(
        account_id=user.account.id,
        steps='fill,migrate',
    )

    # assert
    for i, task in enumerate(tasks):
        att = Attachment.objects.get(
            file_id=f'task{i}_file.pdf',
        )
        assert att.task_id == task.id
        assert att.source_type == SourceType.TASK


# ═══════════════════════════════════════════════════════════
# E. URL replacement across models
# ═══════════════════════════════════════════════════════════


def test_e2e__url_replaced_in_event_and_task(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.first()
    url = gcs_url('shared_file.pdf')
    create_fa(
        account=user.account,
        file_key='shared_file.pdf',
        workflow=workflow,
    )
    event = create_test_event(
        workflow=workflow,
        user=user,
        task=task,
    )
    event.text = f'Attached: {url}'
    event.save(update_fields=['text'])
    task.description = f'See {url} for details'
    task.save(update_fields=['description'])

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    event.refresh_from_db()
    task.refresh_from_db()
    assert GCS_API not in event.text
    assert FS_DOMAIN in event.text
    assert GCS_API not in task.description
    assert FS_DOMAIN in task.description


def test_e2e__url_replaced_in_json_fields(
    create_fa,
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    url = gcs_url('json_file.pdf')
    create_fa(
        account=user.account,
        file_key='json_file.pdf',
        workflow=workflow,
    )
    event = create_test_event(
        workflow=workflow,
        user=user,
    )
    event.task_json = {
        'attachments': [
            {'url': url, 'name': 'file.pdf'},
        ],
    }
    event.save(update_fields=['task_json'])

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    event.refresh_from_db()
    assert GCS_API not in str(event.task_json)
    assert FS_DOMAIN in str(event.task_json)


def test_e2e__thumbnail_url__both_mapped(
    run_pipeline,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    url = gcs_url('thumb_file.pdf')
    thumb_url = gcs_url('thumb_file_thumb.jpg')
    fa = FileAttachment.objects.create(
        name='thumb_file.pdf',
        url=url,
        thumbnail_url=thumb_url,
        account=user.account,
        workflow=workflow,
        size=2048,
    )

    # act
    run_pipeline(account_id=user.account.id)

    # assert
    fa.refresh_from_db()
    assert GCS_API not in (fa.url or '')
    assert GCS_API not in (fa.thumbnail_url or '')


# ═══════════════════════════════════════════════════════════
# F. Edge cases
# ═══════════════════════════════════════════════════════════


def test_e2e__idempotent__second_run_safe(
    create_fa,
    run_pipeline,
    run_migrate,
):
    # arrange
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    create_fa(
        account=user.account,
        file_key='idem_file.pdf',
        workflow=workflow,
    )

    # act
    run_pipeline(
        account_id=user.account.id,
        steps='fill,migrate',
    )
    output = run_migrate(account_id=user.account.id)

    # assert
    assert 'Created: 0' in output
    assert 'Skipped: 1' in output
    assert Attachment.objects.filter(
        file_id='idem_file.pdf',
    ).count() == 1


def test_e2e__url_encoded_filename__preserved(
    create_fa,
    run_fill,
):
    # arrange
    user = create_test_admin()
    encoded = 'File%20(1).pdf'
    create_fa(
        account=user.account,
        file_key=encoded,
        url=gcs_url(encoded),
        name='File (1).pdf',
    )

    # act
    run_fill(account_id=user.account.id)

    # assert
    fa = FileAttachment.objects.get(
        name='File (1).pdf',
    )
    assert fa.file_id == 'File (1).pdf'


def test_e2e__dry_run__full_pipeline__no_side_effects(
    create_fa,
):
    # arrange
    user = create_test_admin()
    create_fa(
        account=user.account,
        file_key='dry_e2e.pdf',
    )

    # act
    out = StringIO()
    call_command(
        'fill_file_attachment_file_id',
        account_ids=str(user.account.id),
        dry_run=True,
        stdout=out,
    )
    call_command(
        'migrate_file_attachment_to_attachment',
        account_ids=str(user.account.id),
        dry_run=True,
        stdout=out,
    )

    # assert
    fa = FileAttachment.objects.get(
        url=gcs_url('dry_e2e.pdf'),
    )
    assert fa.file_id is None
    assert not Attachment.objects.filter(
        file_id='dry_e2e.pdf',
    ).exists()


# ═══════════════════════════════════════════════════════════
# G. Sync to file DB — step 5
# ═══════════════════════════════════════════════════════════


SYNC_PG_PATH = (
    'src.processes.management.commands'
    '.sync_files_to_file_service.psycopg2'
)
SYNC_SETT_PATH = (
    'src.processes.management.commands'
    '.sync_files_to_file_service.settings'
)


@patch(SYNC_SETT_PATH)
@patch(SYNC_PG_PATH)
def test_e2e__sync_receives_correct_metadata(
    mock_psycopg2,
    mock_sett,
    create_fa,
    run_pipeline,
):
    # arrange
    mock_sett.FILE_POSTGRES_DB = 'file_db'
    mock_sett.FILE_POSTGRES_USER = 'file_user'
    mock_sett.FILE_POSTGRES_PASSWORD = 'file_pass'
    mock_sett.FILE_POSTGRES_HOST = 'localhost'
    mock_sett.FILE_POSTGRES_PORT = '5432'
    user = create_test_admin()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    create_fa(
        account=user.account,
        file_key='sync_meta.pdf',
        workflow=workflow,
    )
    run_pipeline(
        account_id=user.account.id,
        steps='fill,migrate',
    )

    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_psycopg2.connect.return_value = mock_conn
    mock_psycopg2.Error = real_psycopg2.Error
    mock_psycopg2.OperationalError = (
        real_psycopg2.OperationalError
    )
    mock_cursor.fetchone.side_effect = [
        (True,),
        None,
    ]

    # act
    out = StringIO()
    call_command(
        'sync_files_to_file_service',
        account_ids=str(user.account.id),
        stdout=out,
    )

    # assert
    insert_calls = [
        c for c in mock_cursor.execute.call_args_list
        if 'INSERT INTO files' in str(c)
    ]
    assert len(insert_calls) == 1
    args = insert_calls[0][0][1]
    assert args[0] == 'sync_meta.pdf'


@patch(SYNC_SETT_PATH)
@patch(SYNC_PG_PATH)
def test_e2e__sync_only_files_with_attachment(
    mock_psycopg2,
    mock_sett,
):
    # arrange
    mock_sett.FILE_POSTGRES_DB = 'file_db'
    mock_sett.FILE_POSTGRES_USER = 'file_user'
    mock_sett.FILE_POSTGRES_PASSWORD = 'file_pass'
    mock_sett.FILE_POSTGRES_HOST = 'localhost'
    mock_sett.FILE_POSTGRES_PORT = '5432'
    user = create_test_admin()
    FileAttachment.objects.create(
        name='no_att.pdf',
        url=gcs_url('no_att.pdf'),
        file_id='no_att.pdf',
        account=user.account,
        size=100,
    )

    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_psycopg2.connect.return_value = mock_conn
    mock_psycopg2.Error = real_psycopg2.Error
    mock_psycopg2.OperationalError = (
        real_psycopg2.OperationalError
    )

    # act
    out = StringIO()
    call_command(
        'sync_files_to_file_service',
        account_ids=str(user.account.id),
        stdout=out,
    )

    # assert
    assert 'Found 0 records' in out.getvalue()


@patch(SYNC_SETT_PATH)
@patch(SYNC_PG_PATH)
def test_e2e__sync_after_migrate__complete_chain(
    mock_psycopg2,
    mock_sett,
    create_fa,
    run_pipeline,
):
    # arrange
    mock_sett.FILE_POSTGRES_DB = 'file_db'
    mock_sett.FILE_POSTGRES_USER = 'file_user'
    mock_sett.FILE_POSTGRES_PASSWORD = 'file_pass'
    mock_sett.FILE_POSTGRES_HOST = 'localhost'
    mock_sett.FILE_POSTGRES_PORT = '5432'
    user = create_test_admin()
    create_fa(
        account=user.account,
        file_key='chain_sync.pdf',
    )
    run_pipeline(
        account_id=user.account.id,
        steps='fill,migrate',
    )

    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_psycopg2.connect.return_value = mock_conn
    mock_psycopg2.Error = real_psycopg2.Error
    mock_psycopg2.OperationalError = (
        real_psycopg2.OperationalError
    )
    mock_cursor.fetchone.side_effect = [
        (True,),
        None,
    ]

    # act
    out = StringIO()
    call_command(
        'sync_files_to_file_service',
        account_ids=str(user.account.id),
        stdout=out,
    )

    # assert
    assert 'Synced: 1' in out.getvalue()
