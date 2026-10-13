from src.storage import messages as fs_messages
from datetime import timedelta
from types import SimpleNamespace

import pytest
import requests
from django.utils import timezone
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from src.storage.enums import (
    ImportJobState,
)
from src.storage.services.exceptions import (
    StorageUnavailable,
)
from src.mcp.models import ImportJob, UploadCapability
from src.storage.services.file_service import FileServiceClient
from src.storage.tasks import (
    cleanup_uploads,
    dispatch_pending_imports,
    import_upload,
)


def test_storage_tasks__registered_names__existing_queue_contract():
    # arrange
    tasks = {
        import_upload: 'src.mcp.tasks.import_upload',
        dispatch_pending_imports: 'src.mcp.tasks.dispatch_pending_imports',
        cleanup_uploads: 'src.mcp.tasks.cleanup_uploads',
    }

    # act
    names = {task.name for task in tasks}

    # assert
    assert names == set(tasks.values())


pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'case',
    ['due', 'future', 'expired_lease', 'live_lease', 'done', 'failed'],
)
def test_dispatch_pending_imports__job_schedule__only_due(
    upload_session: SimpleNamespace,
    mocker: MockerFixture,
    case: str,
):
    # arrange
    now = timezone.now()
    state = ImportJobState.QUEUED
    next_attempt_at = now - timedelta(seconds=1)
    lease_until = None
    if case == 'future':
        next_attempt_at = now + timedelta(minutes=1)
    elif case in {'expired_lease', 'live_lease'}:
        state = ImportJobState.RUNNING
        next_attempt_at = now + timedelta(minutes=1)
        lease_until = now - timedelta(seconds=1)
        if case == 'live_lease':
            lease_until = now + timedelta(minutes=1)
    elif case == 'done':
        state = ImportJobState.DONE
    elif case == 'failed':
        state = ImportJobState.FAILED
    job = ImportJob.objects.create(
        session=upload_session.session,
        state=state,
        next_attempt_at=next_attempt_at,
        lease_until=lease_until,
    )
    import_upload_mock = mocker.patch(
        target='src.storage.tasks.import_upload.delay',
    )

    # act
    dispatch_pending_imports()
    job.refresh_from_db()

    # assert
    assert job.state == state
    assert job.attempts == 0
    assert job.next_attempt_at == next_attempt_at
    assert job.lease_until == lease_until
    if case in {'due', 'expired_lease'}:
        import_upload_mock.assert_called_once_with(str(job.session_id))
    else:
        import_upload_mock.assert_not_called()


def test_dispatch_pending_imports__disabled__no_delivery(
    upload_session: SimpleNamespace,
    mcp_settings: SettingsWrapper,
    mocker: MockerFixture,
):
    # arrange
    job = ImportJob.objects.create(
        session=upload_session.session,
        next_attempt_at=timezone.now() - timedelta(seconds=1),
    )
    mcp_settings.MCP_ENABLED = False
    import_upload_mock = mocker.patch(
        target='src.storage.tasks.import_upload.delay',
    )

    # act
    dispatch_pending_imports()
    job.refresh_from_db()

    # assert
    assert job.state == ImportJobState.QUEUED
    assert job.attempts == 0
    import_upload_mock.assert_not_called()


def test_dispatch_pending_imports__empty_queue__no_delivery(
    mocker: MockerFixture,
):
    # arrange
    import_upload_mock = mocker.patch(
        target='src.storage.tasks.import_upload.delay',
    )

    # act
    dispatch_pending_imports()

    # assert
    assert ImportJob.objects.count() == 0
    import_upload_mock.assert_not_called()


@pytest.mark.parametrize('enabled', [False, True])
def test_cleanup_uploads__feature_gate__bounded_request(
    mcp_settings: SettingsWrapper,
    mocker: MockerFixture,
    enabled: bool,
):

    # arrange
    mcp_settings.MCP_ENABLED = enabled
    storage_post_mock = mocker.patch(
        target=(
            'src.storage.services.file_service.FileServiceClient.post_internal'
        ),
    )

    # act
    cleanup_uploads()

    # assert
    if enabled:
        storage_post_mock.assert_called_once_with(
            path='/internal/mcp/cleanup',
            payload={'limit': 100},
        )
    else:
        storage_post_mock.assert_not_called()


@pytest.mark.parametrize('case', ['future', 'due', 'lease', 'expired_lease'])
def test_import_upload__retry_schedule_and_lease__respects_claim(
    upload_session: SimpleNamespace,
    mocker: MockerFixture,
    case: str,
):

    # arrange
    session = upload_session.session
    session.status = 'importing'
    session.source_url = 'https://remote.test/file'
    session.save(update_fields=['status', 'source_url'])
    now = timezone.now()
    is_running = case in {'lease', 'expired_lease'}
    next_attempt_at = now + timedelta(minutes=5)
    if case == 'due':
        next_attempt_at = now - timedelta(seconds=1)
    lease_until = None
    if is_running:
        lease_until = now + timedelta(minutes=2)
    if case == 'expired_lease':
        lease_until = now - timedelta(seconds=1)
    job = ImportJob.objects.create(
        session=session,
        state='running' if is_running else 'queued',
        attempts=2 if is_running else 0,
        next_attempt_at=next_attempt_at,
        lease_until=lease_until,
    )
    storage_post_mock = mocker.patch(
        target=(
            'src.storage.services.file_service.FileServiceClient.post_internal'
        ),
    )
    token_urlsafe_mock = mocker.patch(
        target='src.authentication.tokens.secrets.token_urlsafe',
        return_value='scheduled-import',
    )
    capability_count = UploadCapability.objects.count()

    # act
    import_upload(session_id=str(session.pk))
    job.refresh_from_db()

    # assert
    if case in {'future', 'lease'}:
        assert job.state == ('running' if is_running else 'queued')
        assert job.attempts == (2 if is_running else 0)
        assert job.next_attempt_at == next_attempt_at
        assert job.lease_until == lease_until
        assert UploadCapability.objects.count() == capability_count
        storage_post_mock.assert_not_called()
        token_urlsafe_mock.assert_not_called()
    else:
        assert job.state == 'queued'
        assert job.attempts == (3 if is_running else 1)
        assert job.lease_until is None
        assert job.next_attempt_at > now
        assert UploadCapability.objects.count() == capability_count + 1
        storage_post_mock.assert_called_once_with(
            path='/internal/mcp/import',
            payload={
                'credential': 'mcp-u_scheduled-import',
                'upload_session_id': str(session.pk),
                'url': 'https://remote.test/file',
                'filename': 'test.txt',
            },
        )
        token_urlsafe_mock.assert_called_once_with(32)


@pytest.mark.parametrize('status', [200, 302])
def test_storage_post__private_service__no_proxy_or_redirect(
    mocker: MockerFixture,
    mcp_settings: SettingsWrapper,
    status: int,
):
    # arrange
    client = requests.Session()
    session_mock = mocker.patch(
        target='src.storage.services.file_service.requests.Session',
        return_value=client,
    )
    response = requests.Response()
    response.status_code = status
    post_mock = mocker.patch.object(
        target=client,
        attribute='post',
        return_value=response,
    )

    # act
    if status == 302:
        with pytest.raises(StorageUnavailable) as error:
            FileServiceClient.post_internal(
                path='/internal/mcp/cleanup',
                payload={'limit': 100},
            )
    else:
        FileServiceClient.post_internal(
            path='/internal/mcp/cleanup',
            payload={'limit': 100},
        )

    # assert
    if status == 302:
        assert str(error.value) == fs_messages.MSG_FS_0013
    assert client.trust_env is False
    session_mock.assert_called_once_with()
    post_mock.assert_called_once_with(
        url='http://file-service:8000/internal/mcp/cleanup',
        headers={
            'Authorization': f'Bearer {mcp_settings.MCP_FILE_SERVICE_SECRET}',
        },
        json={'limit': 100},
        timeout=75,
        allow_redirects=False,
    )
