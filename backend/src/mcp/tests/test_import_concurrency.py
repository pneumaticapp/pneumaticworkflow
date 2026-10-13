from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import timedelta
from queue import Queue
from threading import Event
from types import SimpleNamespace

import pytest
from django.db import close_old_connections
from django.utils import timezone
from pytest_mock import MockerFixture

from src.mcp.models import ImportJob, UploadSession
from src.storage.tasks import import_upload
from src.processes.models.workflows.fields import TaskField

pytestmark = pytest.mark.django_db(transaction=True)


def test_import__concurrent_account_workers__two_active_third_deferred(
    grant: SimpleNamespace,
    task_field: TaskField,
    mocker: MockerFixture,
):
    # arrange
    sessions = [
        UploadSession.objects.create(
            connection=grant.connection,
            task=task_field.task,
            field=task_field,
            filename=f'import{index}.txt',
            content_type='text/plain',
            size=3,
            source_url='https://remote.test/file',
            status='importing',
            expires_at=timezone.now() + timedelta(hours=1),
        )
        for index in range(3)
    ]
    for session in sessions:
        ImportJob.objects.create(
            session=session,
            next_attempt_at=timezone.now(),
        )
    started, release = Queue(), Event()
    token_urlsafe_mock = mocker.patch(
        target='src.authentication.tokens.secrets.token_urlsafe',
        side_effect=['capability-1', 'capability-2'],
    )
    expected_storage_calls = []

    def storage_side_effect(*, path: str, payload: dict):
        session = UploadSession.objects.get(pk=payload['upload_session_id'])
        expected_storage_calls.append(
            mocker.call(
                path='/internal/mcp/import',
                payload={
                    'credential': payload['credential'],
                    'upload_session_id': str(session.pk),
                    'url': session.source_url,
                    'filename': session.filename,
                },
            ),
        )
        started.put(item=payload['upload_session_id'])
        assert release.wait(timeout=30)

    def run_import(session: UploadSession):
        close_old_connections()
        try:
            import_upload(session_id=str(session.pk))
        finally:
            close_old_connections()

    storage_mock = mocker.patch(
        target=(
            'src.storage.services.file_service.FileServiceClient.post_internal'
        ),
        side_effect=storage_side_effect,
    )

    # act
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(run_import, session) for session in sessions
        ]
        try:
            started.get(timeout=30)
            started.get(timeout=30)
            completed, pending = wait(
                futures,
                timeout=10,
                return_when=FIRST_COMPLETED,
            )
            states = list(
                ImportJob.objects.order_by('attempts').values(
                    'state',
                    'attempts',
                    'lease_until',
                    'next_attempt_at',
                ),
            )
        finally:
            release.set()
        for future in futures:
            future.result(timeout=30)

    # assert
    assert len(completed) == 1
    assert len(pending) == 2
    assert states[0]['state'] == 'queued'
    assert states[0]['attempts'] == 0
    assert states[0]['lease_until'] is None
    assert states[0]['next_attempt_at'] > (
        timezone.now() - timedelta(seconds=10)
    )
    assert states[1]['state'] == 'running'
    assert states[1]['attempts'] == 1
    assert states[2]['state'] == 'running'
    assert states[2]['attempts'] == 1
    assert storage_mock.call_count == 2
    storage_mock.assert_has_calls(expected_storage_calls, any_order=True)
    assert token_urlsafe_mock.call_count == 2
    token_urlsafe_mock.assert_has_calls([mocker.call(32), mocker.call(32)])
