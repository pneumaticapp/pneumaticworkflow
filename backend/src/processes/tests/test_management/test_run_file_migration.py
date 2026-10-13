"""Tests for run_file_migration orchestrator command."""
import pytest
from io import StringIO
from unittest.mock import patch

import psycopg2 as real_psycopg2

from django.core.management import call_command
from django.core.management.base import CommandError

pytestmark = pytest.mark.django_db

PSYCOPG2_PATH = (
    'src.processes.management.commands'
    '.run_file_migration.psycopg2'
)
SETTINGS_PATH = (
    'src.processes.management.commands'
    '.run_file_migration.settings'
)
CALL_CMD_PATH = (
    'src.processes.management.commands'
    '.run_file_migration.call_command'
)

VALID_FILE_SETTINGS = {
    'FILE_POSTGRES_DB': 'file_db',
    'FILE_POSTGRES_USER': 'file_user',
    'FILE_POSTGRES_PASSWORD': 'file_pass',
    'FILE_POSTGRES_HOST': 'localhost',
    'FILE_POSTGRES_PORT': '5432',
}


def _mock_settings(mock_obj, overrides=None):
    """Apply valid FILE_POSTGRES_* to a mock settings."""
    values = {
        **VALID_FILE_SETTINGS,
        **(overrides or {}),
    }
    for key, value in values.items():
        setattr(mock_obj, key, value)
    mock_obj.DEBUG = False


def _set_pg_exceptions(mock_pg):
    mock_pg.Error = real_psycopg2.Error
    mock_pg.OperationalError = (
        real_psycopg2.OperationalError
    )


# ── Pre-flight checks ───────────────────────────────────────


@patch(PSYCOPG2_PATH)
def test_orchestrator__missing_file_config__raises(
    mock_pg,
):
    """Missing FILE_POSTGRES_* raises CommandError."""

    # arrange
    _set_pg_exceptions(mock_pg)

    # act & assert
    with patch(SETTINGS_PATH) as mock_settings:
        mock_settings.FILE_POSTGRES_DB = ''
        mock_settings.FILE_POSTGRES_USER = ''
        mock_settings.FILE_POSTGRES_PASSWORD = ''
        mock_settings.FILE_POSTGRES_HOST = ''
        mock_settings.FILE_POSTGRES_PORT = ''

        with pytest.raises(
            CommandError,
            match='FILE_POSTGRES_',
        ):
            call_command(
                'run_file_migration',
                account_ids='1',
                stdout=StringIO(),
            )


@patch(SETTINGS_PATH)
@patch(PSYCOPG2_PATH)
def test_orchestrator__files_table_missing__raises(
    mock_pg,
    mock_sett,
    mock_file_db,
):
    # arrange
    _mock_settings(mock_sett)
    _set_pg_exceptions(mock_pg)
    mock_conn, _ = mock_file_db(table_exists=False)
    mock_pg.connect.return_value = mock_conn

    # act & assert
    with pytest.raises(
        CommandError,
        match="'files' table",
    ):
        call_command(
            'run_file_migration',
            account_ids='1',
            stdout=StringIO(),
        )


@patch(SETTINGS_PATH)
@patch(PSYCOPG2_PATH)
def test_orchestrator__connection_failure__raises(
    mock_pg,
    mock_sett,
):
    # arrange
    _mock_settings(mock_sett)
    _set_pg_exceptions(mock_pg)
    mock_pg.connect.side_effect = (
        real_psycopg2.OperationalError(
            'connection refused',
        )
    )

    # act & assert
    with pytest.raises(
        CommandError,
        match='Failed to connect',
    ):
        call_command(
            'run_file_migration',
            account_ids='1',
            stdout=StringIO(),
        )


# ── Execution ────────────────────────────────────────────────


@patch(CALL_CMD_PATH)
@patch(SETTINGS_PATH)
@patch(PSYCOPG2_PATH)
def test_orchestrator__runs_all_cmds_in_order(
    mock_pg,
    mock_sett,
    mock_call,
    mock_file_db,
):
    # arrange
    _mock_settings(mock_sett)
    _set_pg_exceptions(mock_pg)
    mock_conn, _ = mock_file_db()
    mock_pg.connect.return_value = mock_conn

    # act
    call_command(
        'run_file_migration',
        account_ids='42',
        stdout=StringIO(),
    )

    # assert
    assert mock_call.call_count == 4


@patch(CALL_CMD_PATH)
@patch(SETTINGS_PATH)
@patch(PSYCOPG2_PATH)
def test_orchestrator__passes_account_ids(
    mock_pg,
    mock_sett,
    mock_call,
    mock_file_db,
):
    # arrange
    _mock_settings(mock_sett)
    _set_pg_exceptions(mock_pg)
    mock_conn, _ = mock_file_db()
    mock_pg.connect.return_value = mock_conn

    # act
    call_command(
        'run_file_migration',
        account_ids='42,43',
        stdout=StringIO(),
    )

    # assert
    for c in mock_call.call_args_list:
        assert c[1].get('account_ids') == '42,43'


@patch(CALL_CMD_PATH)
@patch(SETTINGS_PATH)
@patch(PSYCOPG2_PATH)
def test_orchestrator__migrate_correct_apps(
    mock_pg,
    mock_sett,
    mock_call,
    mock_file_db,
):
    # arrange
    _mock_settings(mock_sett)
    _set_pg_exceptions(mock_pg)
    mock_conn, _ = mock_file_db()
    mock_pg.connect.return_value = mock_conn

    # act
    call_command(
        'run_file_migration',
        account_ids='1',
        stdout=StringIO(),
    )

    # assert
    assert mock_call.call_count == 4
    expected_cmds = [
        'fill_file_attachment_file_id',
        'migrate_file_attachment_to_attachment',
        'sync_files_to_file_service',
        'replace_storage_links_with_file_service',
    ]
    actual_cmds = [c[0][0] for c in mock_call.call_args_list]
    assert actual_cmds == expected_cmds


@patch(CALL_CMD_PATH)
@patch(SETTINGS_PATH)
@patch(PSYCOPG2_PATH)
def test_orchestrator__success_message(
    mock_pg,
    mock_sett,
    mock_call,
    mock_file_db,
):
    # arrange
    _mock_settings(mock_sett)
    _set_pg_exceptions(mock_pg)
    mock_conn, _ = mock_file_db()
    mock_pg.connect.return_value = mock_conn
    out = StringIO()

    # act
    call_command(
        'run_file_migration',
        account_ids='1',
        stdout=out,
    )

    # assert
    assert '✅' in out.getvalue()
    assert 'completed successfully' in out.getvalue()
    assert mock_call.call_count == 4


# ── Fallback ─────────────────────────────────────────────────


@patch(SETTINGS_PATH)
@patch(PSYCOPG2_PATH)
def test_orchestrator__primary_fails__tries_fallback(
    mock_pg,
    mock_sett,
    mock_file_db,
):
    # arrange
    _mock_settings(mock_sett)
    _set_pg_exceptions(mock_pg)
    mock_conn_fallback, _ = mock_file_db()
    mock_pg.connect.side_effect = [
        real_psycopg2.OperationalError('primary failed'),
        mock_conn_fallback,
    ]

    # act
    with patch(CALL_CMD_PATH):
        call_command(
            'run_file_migration',
            account_ids='1',
            stdout=StringIO(),
        )

    # assert
    assert mock_pg.connect.call_count == 2


@patch(SETTINGS_PATH)
@patch(PSYCOPG2_PATH)
def test_orchestrator__both_conns_fail__raises(
    mock_pg,
    mock_sett,
):
    # arrange
    _mock_settings(mock_sett)
    _set_pg_exceptions(mock_pg)
    mock_pg.connect.side_effect = [
        real_psycopg2.OperationalError('primary'),
        real_psycopg2.OperationalError('fallback'),
    ]

    # act & assert
    with pytest.raises(
        CommandError,
        match='fallback',
    ):
        call_command(
            'run_file_migration',
            account_ids='1',
            stdout=StringIO(),
        )
