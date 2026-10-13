from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event, get_ident
from types import SimpleNamespace

import pytest
from django.db import close_old_connections, transaction
from django.utils import timezone
from pytest_mock import MockerFixture

from src.authentication.services.upload_capabilities import (
    UploadCapabilityService,
)
from src.storage.constants import (
    IMPORT_MAX_ATTEMPTS,
)
from src.storage.enums import (
    ImportJobState,
    UploadStatus,
)
from src.mcp.models import ImportJob, UploadCapability, UploadSession
from src.processes.models.workflows.fields import TaskField
from src.storage.services.imports import ImportService
from src.storage.services.upload_sessions import UploadSessionService

pytestmark = pytest.mark.django_db(transaction=True)


def test_create__credential_failure__rolls_back_session(
    delegated_client,
    task_field: TaskField,
    mocker: MockerFixture,
):
    # arrange
    original_issue = UploadCapabilityService.issue

    def hide_target_and_issue(session: UploadSession) -> str:
        TaskField.objects.filter(pk=session.field_id).update(is_hidden=True)
        return original_issue(session=session)

    mocker.patch.object(
        UploadCapabilityService,
        'issue',
        side_effect=hide_target_and_issue,
    )
    path = '/integrations/mcp/uploads'
    client = delegated_client(
        tool='create_upload_link', method='POST', path=path,
    )
    before = UploadSession.objects.count()

    # act
    response = client.post(path=path, data={
        'task_id': task_field.task_id,
        'field_api_name': task_field.api_name,
        'filename': 'test.txt',
        'content_type': 'text/plain',
        'size': 3,
    })

    # assert
    assert response.status_code == 404
    assert UploadSession.objects.count() == before
    assert not UploadCapability.objects.exists()


def test_import__late_completion_before_claim__preserves_ready(
    upload_session: SimpleNamespace,
    mocker: MockerFixture,
):
    # arrange
    session = upload_session.session
    session.status = UploadStatus.IMPORTING
    session.source_url = 'https://example.com/file'
    session.save(update_fields=['status', 'source_url'])
    job = ImportJob.objects.create(
        session=session,
        attempts=IMPORT_MAX_ATTEMPTS,
        next_attempt_at=timezone.now() - timedelta(seconds=1),
    )
    claim_started, callback_done = Event(), Event()
    worker = {}
    original_lock = UploadSessionService.lock_session

    def pause_claim(session_id: str) -> UploadSession:
        if get_ident() == worker.get('id'):
            claim_started.set()
            assert callback_done.wait(timeout=20)
        return original_lock(session_id=session_id)

    mocker.patch.object(
        UploadSessionService, 'lock_session', side_effect=pause_claim,
    )

    def claim():
        close_old_connections()
        worker['id'] = get_ident()
        try:
            return ImportService._claim(session_id=str(session.pk))
        finally:
            close_old_connections()

    # act
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(claim)
        try:
            assert claim_started.wait(timeout=20)
            completed = UploadSessionService.complete_upload(data={
                'credential': upload_session.credential,
                'upload_session_id': str(session.pk),
                'file_id': 'late-success-1',
                'name': 'test.txt',
                'size': 3,
                'content_type': 'text/plain',
            })
        finally:
            callback_done.set()
        result = future.result(timeout=20)
    session.refresh_from_db()
    job.refresh_from_db()

    # assert
    assert result is None
    assert completed.status == UploadStatus.READY
    assert session.status == UploadStatus.READY
    assert session.file_id == 'late-success-1'
    assert job.state == ImportJobState.DONE


@pytest.mark.parametrize('status', [UploadStatus.READY, UploadStatus.ATTACHED])
def test_import__stale_failure__preserves_completed_session(
    upload_session: SimpleNamespace,
    status: str,
):
    # arrange
    session = upload_session.session
    job = ImportJob.objects.create(
        session=session,
        next_attempt_at=timezone.now(),
    )
    UploadSession.objects.filter(pk=session.pk).update(
        status=status,
        file_id='completed-file',
    )

    # act
    with transaction.atomic():
        ImportService._fail(job=job, session=session)
    session.refresh_from_db()
    job.refresh_from_db()

    # assert
    assert session.status == status
    assert session.file_id == 'completed-file'
    assert job.state == ImportJobState.DONE
