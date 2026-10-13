from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event
from types import SimpleNamespace

import pytest
from django.db import close_old_connections, transaction
from django.utils import timezone
from pytest_mock import MockerFixture

from src.mcp.models import ImportJob, UploadSession
from src.storage.constants import UPLOAD_STATE_RETENTION
from src.storage.enums import (
    AccessType,
    ImportJobState,
    SourceType,
    UploadStatus,
)
from src.storage.models import Attachment
from src.storage.services.pruning import UploadPruneService

pytestmark = pytest.mark.django_db


def test_import__malformed_url__returns_400_without_job(
    delegated_client,
    upload_session: SimpleNamespace,
):
    # arrange
    session = upload_session.session
    path = f'/integrations/mcp/uploads/{session.pk}/import'
    client = delegated_client(
        tool='import_attachment_from_url', method='POST', path=path,
    )

    # act
    response = client.post(path=path, data={'url': 'https://[invalid/file'})
    session.refresh_from_db()

    # assert
    assert response.status_code == 400
    assert response.json()['details']['name'] == 'url'
    assert session.status == UploadStatus.PENDING
    assert session.source_url == ''
    assert not ImportJob.objects.exists()


@pytest.mark.parametrize('status', [
    UploadStatus.ATTACHED, UploadStatus.CLEANED, UploadStatus.FAILED,
    UploadStatus.READY, UploadStatus.IMPORTING,
])
@pytest.mark.parametrize('old', [True, False])
def test_prune__retention__preserves_files_and_cleanup_fences(
    upload_session: SimpleNamespace,
    status: str,
    old: bool,
):
    # arrange
    session = upload_session.session
    attachment = Attachment.objects.create(
        account=session.connection.account,
        file_id='retained-file',
        source_type=SourceType.WORKFLOW,
        access_type=AccessType.ACCOUNT,
    )
    session.status = status
    session.expires_at = (
        timezone.now() - UPLOAD_STATE_RETENTION - timedelta(seconds=1)
        if old else timezone.now() - timedelta(days=1)
    )
    session.source_url = 'https://remote.test/file?private=token'
    session.save(update_fields=['status', 'expires_at', 'source_url'])
    job = ImportJob.objects.create(
        session=session,
        state=(
            ImportJobState.RUNNING if status == UploadStatus.IMPORTING
            else ImportJobState.DONE
        ),
        next_attempt_at=timezone.now(),
    )

    # act
    UploadPruneService.prune_expired_state()

    # assert
    should_delete = old and status == UploadStatus.ATTACHED
    assert UploadSession.objects.filter(pk=session.pk).exists() is (
        not should_delete
    )
    if not should_delete:
        session.refresh_from_db()
        assert session.status == status
        assert bool(session.source_url) is (
            status == UploadStatus.IMPORTING
        )
    assert ImportJob.objects.filter(pk=job.pk).exists() is (
        not old or status == UploadStatus.IMPORTING
    )
    assert Attachment.objects.filter(pk=attachment.pk).exists()


def test_prune__attached_with_active_job__preserves_session(
    upload_session: SimpleNamespace,
):
    # arrange
    session = upload_session.session
    session.status = UploadStatus.ATTACHED
    session.expires_at = (
        timezone.now() - UPLOAD_STATE_RETENTION - timedelta(seconds=1)
    )
    session.save(update_fields=['status', 'expires_at'])
    job = ImportJob.objects.create(
        session=session,
        state=ImportJobState.QUEUED,
        next_attempt_at=timezone.now(),
    )

    # act
    UploadPruneService.prune_expired_state()

    # assert
    assert UploadSession.objects.filter(pk=session.pk).exists()
    assert ImportJob.objects.filter(pk=job.pk).exists()


def test_prune__bounded_pass__keeps_remaining_rows(
    upload_session: SimpleNamespace,
    mocker: MockerFixture,
):
    # arrange
    first = upload_session.session
    cutoff = timezone.now() - UPLOAD_STATE_RETENTION - timedelta(seconds=1)
    first.status = UploadStatus.ATTACHED
    first.expires_at = cutoff
    first.save(update_fields=['status', 'expires_at'])
    UploadSession.objects.create(
        connection=first.connection,
        task=first.task,
        field=first.field,
        filename='second.txt',
        content_type='text/plain',
        size=3,
        status=UploadStatus.ATTACHED,
        expires_at=cutoff,
    )
    mocker.patch('src.storage.services.pruning.UPLOAD_PRUNE_BATCH_SIZE', 1)

    # act
    UploadPruneService.prune_expired_state()

    # assert
    assert UploadSession.objects.count() == 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('locked', ['job', 'session'])
def test_prune__locked_transfer_state__skips_without_waiting(
    upload_session: SimpleNamespace,
    locked: str,
):
    # arrange
    session = upload_session.session
    session.status = UploadStatus.ATTACHED
    session.expires_at = (
        timezone.now() - UPLOAD_STATE_RETENTION - timedelta(seconds=1)
    )
    session.save(update_fields=['status', 'expires_at'])
    job = ImportJob.objects.create(
        session=session,
        state=ImportJobState.DONE,
        next_attempt_at=timezone.now(),
    )
    acquired, release = Event(), Event()

    def hold_lock():
        close_old_connections()
        try:
            with transaction.atomic():
                query = (
                    ImportJob.objects.filter(pk=job.pk)
                    if locked == 'job'
                    else UploadSession.objects.filter(pk=session.pk)
                )
                query.select_for_update().get()
                acquired.set()
                assert release.wait(timeout=20)
        finally:
            close_old_connections()

    def prune():
        close_old_connections()
        try:
            UploadPruneService.prune_expired_state()
        finally:
            close_old_connections()

    # act
    with ThreadPoolExecutor(max_workers=2) as pool:
        holder = pool.submit(hold_lock)
        try:
            assert acquired.wait(timeout=20)
            pool.submit(prune).result(timeout=5)
            session_exists = UploadSession.objects.filter(
                pk=session.pk,
            ).exists()
            job_exists = ImportJob.objects.filter(pk=job.pk).exists()
        finally:
            release.set()
        holder.result(timeout=20)
    UploadPruneService.prune_expired_state()

    # assert
    assert session_exists
    assert job_exists is (locked == 'job')
    assert not UploadSession.objects.filter(pk=session.pk).exists()
    assert not ImportJob.objects.filter(pk=job.pk).exists()
