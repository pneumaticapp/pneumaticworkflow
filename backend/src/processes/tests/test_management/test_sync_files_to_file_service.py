"""Tests for sync_files_to_file_service management command."""
import pytest
from io import StringIO
from unittest.mock import patch

import psycopg2 as real_psycopg2

from django.core.management import call_command

from src.processes.models.workflows.attachment import (
    FileAttachment,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
)
from .conftest import GCS_API, BUCKET

pytestmark = pytest.mark.django_db

PSYCOPG2_PATH = (
    'src.processes.management.commands'
    '.sync_files_to_file_service.psycopg2'
)
SETTINGS_PATH = (
    'src.processes.management.commands'
    '.sync_files_to_file_service.settings'
)


def _set_pg_exceptions(mock_pg):
    mock_pg.Error = real_psycopg2.Error
    mock_pg.OperationalError = (
        real_psycopg2.OperationalError
    )


def _run_sync(
    *,
    account_id,
    mock_psycopg2_mod,
    mock_conn,
    **kwargs,
):
    """Run sync command with patched settings."""
    _set_pg_exceptions(mock_psycopg2_mod)
    mock_psycopg2_mod.connect.return_value = mock_conn
    with patch(SETTINGS_PATH) as mock_sett:
        mock_sett.FILE_POSTGRES_DB = 'file_db'
        mock_sett.FILE_POSTGRES_USER = 'file_user'
        mock_sett.FILE_POSTGRES_PASSWORD = 'file_pass'
        mock_sett.FILE_POSTGRES_HOST = 'localhost'
        mock_sett.FILE_POSTGRES_PORT = '5432'
        out = StringIO()
        call_command(
            'sync_files_to_file_service',
            account_ids=str(account_id),
            stdout=out,
            **kwargs,
        )
        return out.getvalue()


def _find_insert_calls(mock_cursor):
    """Extract INSERT INTO files calls from cursor."""
    return [
        c for c in mock_cursor.execute.call_args_list
        if 'INSERT INTO files' in str(c)
    ]


# ── Basic sync ───────────────────────────────────────────────


@patch(PSYCOPG2_PATH)
def test_sync__inserts_correct_data(
    mock_pg,
    create_synced_fa,
    mock_file_db,
):
    # arrange
    user = create_test_admin()
    create_synced_fa(
        account=user.account,
        file_id='sync_basic.pdf',
        name='report.pdf',
    )
    mock_conn, mock_cursor = mock_file_db()
    mock_cursor.fetchone.side_effect = [
        (True,),
        None,
    ]

    # act
    output = _run_sync(
        account_id=user.account.id,
        mock_psycopg2_mod=mock_pg,
        mock_conn=mock_conn,
    )

    # assert
    insert_calls = _find_insert_calls(mock_cursor)
    assert len(insert_calls) == 1
    args = insert_calls[0][0][1]
    assert args[0] == 'sync_basic.pdf'
    assert args[2] == 'application/pdf'
    assert args[3] == 'report.pdf'
    assert 'Synced: 1' in output


@patch(PSYCOPG2_PATH)
def test_sync__skips_existing_in_file_db(
    mock_pg,
    create_synced_fa,
    mock_file_db,
):
    # arrange
    user = create_test_admin()
    create_synced_fa(
        account=user.account,
        file_id='sync_dup.pdf',
    )
    mock_conn, mock_cursor = mock_file_db()
    mock_cursor.fetchone.side_effect = [
        (True,),
        ('sync_dup.pdf',),
    ]

    # act
    output = _run_sync(
        account_id=user.account.id,
        mock_psycopg2_mod=mock_pg,
        mock_conn=mock_conn,
    )

    # assert
    assert 'Skipped: 1' in output


# ── Content type detection ───────────────────────────────────


@patch(PSYCOPG2_PATH)
def test_sync__pdf__application_pdf(
    mock_pg,
    create_synced_fa,
    mock_file_db,
):
    # arrange
    user = create_test_admin()
    create_synced_fa(
        account=user.account,
        file_id='ct.pdf',
        name='doc.pdf',
    )
    mock_conn, mock_cursor = mock_file_db()
    mock_cursor.fetchone.side_effect = [(True,), None]

    # act
    _run_sync(
        account_id=user.account.id,
        mock_psycopg2_mod=mock_pg,
        mock_conn=mock_conn,
    )

    # assert
    insert_calls = _find_insert_calls(mock_cursor)
    assert insert_calls[0][0][1][2] == 'application/pdf'


@patch(PSYCOPG2_PATH)
def test_sync__png__image_png(
    mock_pg,
    create_synced_fa,
    mock_file_db,
):
    # arrange
    user = create_test_admin()
    create_synced_fa(
        account=user.account,
        file_id='ct.png',
        name='logo.png',
    )
    mock_conn, mock_cursor = mock_file_db()
    mock_cursor.fetchone.side_effect = [(True,), None]

    # act
    _run_sync(
        account_id=user.account.id,
        mock_psycopg2_mod=mock_pg,
        mock_conn=mock_conn,
    )

    # assert
    insert_calls = _find_insert_calls(mock_cursor)
    assert insert_calls[0][0][1][2] == 'image/png'


@patch(PSYCOPG2_PATH)
def test_sync__unknown_ext__octet_stream(
    mock_pg,
    create_synced_fa,
    mock_file_db,
):
    # arrange
    user = create_test_admin()
    create_synced_fa(
        account=user.account,
        file_id='ct.xyz',
        name='data.xyz',
    )
    mock_conn, mock_cursor = mock_file_db()
    mock_cursor.fetchone.side_effect = [(True,), None]

    # act
    _run_sync(
        account_id=user.account.id,
        mock_psycopg2_mod=mock_pg,
        mock_conn=mock_conn,
    )

    # assert
    insert_calls = _find_insert_calls(mock_cursor)
    assert insert_calls[0][0][1][2] == (
        'application/octet-stream'
    )


@patch(PSYCOPG2_PATH)
def test_sync__unnamed_fallback__octet_stream(
    mock_pg,
    create_synced_fa,
    mock_file_db,
):
    # arrange
    user = create_test_admin()
    create_synced_fa(
        account=user.account,
        file_id='noname',
        name='',
    )
    mock_conn, mock_cursor = mock_file_db()
    mock_cursor.fetchone.side_effect = [(True,), None]

    # act
    _run_sync(
        account_id=user.account.id,
        mock_psycopg2_mod=mock_pg,
        mock_conn=mock_conn,
    )

    # assert
    insert_calls = _find_insert_calls(mock_cursor)
    assert insert_calls[0][0][1][2] == (
        'application/octet-stream'
    )
    assert insert_calls[0][0][1][3] == 'unnamed'


# ── Edge cases ───────────────────────────────────────────────


@patch(PSYCOPG2_PATH)
def test_sync__no_attachment__skips(
    mock_pg,
    mock_file_db,
):
    """FileAttachment without Attachment is not synced."""

    # arrange
    user = create_test_admin()
    FileAttachment.objects.create(
        name='no_att.pdf',
        url=f'{GCS_API}/{BUCKET}/no_att.pdf',
        file_id='no_att.pdf',
        account=user.account,
        size=100,
    )
    mock_conn, _ = mock_file_db()

    # act
    output = _run_sync(
        account_id=user.account.id,
        mock_psycopg2_mod=mock_pg,
        mock_conn=mock_conn,
    )

    # assert
    assert 'Found 0 records' in output


@patch(PSYCOPG2_PATH)
def test_sync__size_zero__syncs_zero(
    mock_pg,
    create_synced_fa,
    mock_file_db,
):
    # arrange
    user = create_test_admin()
    create_synced_fa(
        account=user.account,
        file_id='zero.pdf',
        size=0,
    )
    mock_conn, mock_cursor = mock_file_db()
    mock_cursor.fetchone.side_effect = [(True,), None]

    # act
    _run_sync(
        account_id=user.account.id,
        mock_psycopg2_mod=mock_pg,
        mock_conn=mock_conn,
    )

    # assert
    insert_calls = _find_insert_calls(mock_cursor)
    assert insert_calls[0][0][1][1] == 0


@patch(SETTINGS_PATH)
@patch(PSYCOPG2_PATH)
def test_sync__table_missing__aborts(
    mock_pg,
    mock_sett,
    create_synced_fa,
    mock_file_db,
):
    # arrange
    _set_pg_exceptions(mock_pg)
    mock_sett.FILE_POSTGRES_DB = 'file_db'
    mock_sett.FILE_POSTGRES_USER = 'file_user'
    mock_sett.FILE_POSTGRES_PASSWORD = 'file_pass'
    mock_sett.FILE_POSTGRES_HOST = 'localhost'
    mock_sett.FILE_POSTGRES_PORT = '5432'
    user = create_test_admin()
    create_synced_fa(
        account=user.account,
        file_id='miss.pdf',
    )
    mock_conn, _ = mock_file_db(table_exists=False)
    mock_pg.connect.return_value = mock_conn

    # act
    out = StringIO()
    call_command(
        'sync_files_to_file_service',
        account_ids=str(user.account.id),
        stdout=out,
    )

    # assert
    assert "'files' table does not exist" in (
        out.getvalue()
    )


# ── Options ──────────────────────────────────────────────────


@patch(PSYCOPG2_PATH)
def test_sync__dry_run__no_connection(
    mock_pg,
    create_synced_fa,
):
    # arrange
    user = create_test_admin()
    create_synced_fa(
        account=user.account,
        file_id='dry.pdf',
    )

    # act
    out = StringIO()
    call_command(
        'sync_files_to_file_service',
        account_ids=str(user.account.id),
        dry_run=True,
        stdout=out,
    )

    # assert
    assert 'DRY RUN' in out.getvalue()
    assert 'Synced: 1' in out.getvalue()
    mock_pg.connect.assert_not_called()


@patch(PSYCOPG2_PATH)
def test_sync__filters_by_account(
    mock_pg,
    create_synced_fa,
    mock_file_db,
):
    # arrange
    user = create_test_admin()
    account2 = create_test_account(name='Other')
    create_synced_fa(
        account=user.account,
        file_id='acc1.pdf',
    )
    create_synced_fa(
        account=account2,
        file_id='acc2.pdf',
    )
    mock_conn, mock_cursor = mock_file_db()
    mock_cursor.fetchone.side_effect = [(True,), None]

    # act
    output = _run_sync(
        account_id=user.account.id,
        mock_psycopg2_mod=mock_pg,
        mock_conn=mock_conn,
    )

    # assert
    assert 'Found 1 records' in output


@patch(PSYCOPG2_PATH)
def test_sync__batch_commit__every_batch_size(
    mock_pg,
    create_synced_fa,
    mock_file_db,
):
    # arrange
    user = create_test_admin()
    for i in range(5):
        create_synced_fa(
            account=user.account,
            file_id=f'batch_{i}.pdf',
        )
    mock_conn, mock_cursor = mock_file_db()
    side_effects = [(True,)] + [None] * 5
    mock_cursor.fetchone.side_effect = side_effects

    # act
    _run_sync(
        account_id=user.account.id,
        mock_psycopg2_mod=mock_pg,
        mock_conn=mock_conn,
        batch_size=3,
    )

    # assert
    assert mock_conn.commit.call_count >= 2


@patch(PSYCOPG2_PATH)
def test_sync__psycopg2_error__counted_as_error(
    mock_pg,
    create_synced_fa,
    mock_file_db,
):
    # arrange
    user = create_test_admin()
    create_synced_fa(
        account=user.account,
        file_id='err.pdf',
    )
    mock_conn, mock_cursor = mock_file_db()
    mock_cursor.fetchone.side_effect = [(True,), None]
    original_execute = mock_cursor.execute

    def failing_execute(sql, params=None):
        if (
            isinstance(sql, str)
            and 'INSERT INTO files' in sql
        ):
            raise real_psycopg2.Error('test error')
        return original_execute(sql, params)

    mock_cursor.execute = failing_execute

    # act
    output = _run_sync(
        account_id=user.account.id,
        mock_psycopg2_mod=mock_pg,
        mock_conn=mock_conn,
    )

    # assert
    assert 'Errors: 1' in output
