import pytest
from io import StringIO
from unittest.mock import MagicMock

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command

from src.processes.models.workflows.attachment import FileAttachment
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment

GCS_API = 'https://storage.googleapis.com'
GCS_CLOUD = 'https://storage.cloud.google.com'
BUCKET = 'test-bucket'
FS_DOMAIN = 'https://files.pneumatic.app'


def gcs_url(file_key, bucket=BUCKET, base=GCS_API):
    return f'{base}/{bucket}/{file_key}'


@pytest.fixture(autouse=True)
def create_attachment_permissions(db):
    """
    Ensure attachment permissions exist in test database.
    Django creates permissions during migrations, but in tests
    they might not be created automatically.
    """
    content_type = ContentType.objects.get_for_model(Attachment)
    Permission.objects.get_or_create(
        codename='access_attachment',
        name='Can access attachment',
        content_type=content_type,
    )


@pytest.fixture
def create_fa():
    """Factory: create FileAttachment with GCS URL."""

    def _create(*, account, file_key, **kwargs):
        return FileAttachment.objects.create(
            name=kwargs.pop('name', file_key.split('/')[-1]),
            url=kwargs.pop('url', gcs_url(file_key)),
            account=account,
            size=kwargs.pop('size', 1024),
            **kwargs,
        )

    return _create


@pytest.fixture
def create_fa_with_file_id():
    """Factory: create FileAttachment with file_id already set."""

    def _create(*, account, file_id, **kwargs):
        return FileAttachment.objects.create(
            name=kwargs.pop('name', 'test.pdf'),
            url=kwargs.pop(
                'url',
                f'{GCS_API}/{BUCKET}/{file_id}',
            ),
            file_id=file_id,
            account=account,
            size=kwargs.pop('size', 1024),
            **kwargs,
        )

    return _create


@pytest.fixture
def create_synced_fa():
    """Factory: create FileAttachment + Attachment (ready for sync)."""

    def _create(*, account, file_id, name='test.pdf', size=1024):
        FileAttachment.objects.create(
            name=name,
            url=f'{GCS_API}/{BUCKET}/{file_id}',
            file_id=file_id,
            account=account,
            size=size,
        )
        Attachment.objects.create(
            file_id=file_id,
            access_type=AccessType.ACCOUNT,
            source_type=SourceType.ACCOUNT,
            account=account,
        )

    return _create


@pytest.fixture
def run_fill():
    """Runner: execute fill_file_attachment_file_id command."""

    def _run(*, account_id, **kwargs):
        out = StringIO()
        call_command(
            'fill_file_attachment_file_id',
            account_ids=str(account_id),
            stdout=out,
            **kwargs,
        )
        return out.getvalue()

    return _run


@pytest.fixture
def run_migrate():
    """Runner: execute migrate_file_attachment_to_attachment."""

    def _run(*, account_id, **kwargs):
        out = StringIO()
        call_command(
            'migrate_file_attachment_to_attachment',
            account_ids=str(account_id),
            stdout=out,
            **kwargs,
        )
        return out.getvalue()

    return _run


@pytest.fixture
def run_replace():
    """Runner: execute replace_storage_links_with_file_service."""

    def _run(*, account_id, fs_domain=FS_DOMAIN, **kwargs):
        out = StringIO()
        call_command(
            'replace_storage_links_with_file_service',
            account_ids=str(account_id),
            file_service_domain=fs_domain,
            stdout=out,
            **kwargs,
        )
        return out.getvalue()

    return _run


@pytest.fixture
def run_pipeline(run_fill, run_migrate, run_replace):
    """Runner: execute selected pipeline steps in order."""

    def _run(*, account_id, steps='fill,migrate,replace'):
        results = {}
        for raw_step in steps.split(','):
            step = raw_step.strip()
            if step == 'fill':
                results['fill'] = run_fill(
                    account_id=account_id,
                )
            elif step == 'migrate':
                results['migrate'] = run_migrate(
                    account_id=account_id,
                )
            elif step == 'replace':
                results['replace'] = run_replace(
                    account_id=account_id,
                )
        return results

    return _run


@pytest.fixture
def mock_file_db():
    """Factory: create mock psycopg2 connection + cursor."""

    def _create(*, table_exists=True):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (table_exists,)
        return mock_conn, mock_cursor

    return _create
