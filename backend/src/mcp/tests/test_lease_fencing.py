from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.utils import timezone
from pytest_mock import MockerFixture

from src.storage.services.exceptions import (
    StorageUnavailable,
)
from src.mcp.models import ImportJob, UploadSession
from src.storage.tasks import import_upload
from src.processes.models.workflows.fields import TaskField

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('failure', [True, False])
def test_import__stale_completion__preserves_newer_claim(
    grant: SimpleNamespace,
    task_field: TaskField,
    mocker: MockerFixture,
    failure: bool,
):
    # arrange
    session = UploadSession.objects.create(
        connection=grant.connection,
        task=task_field.task,
        field=task_field,
        filename='import.txt',
        content_type='text/plain',
        size=3,
        source_url='https://remote.test/file',
        status='importing',
        expires_at=timezone.now() + timedelta(hours=1),
    )
    job = ImportJob.objects.create(
        session=session,
        next_attempt_at=timezone.now(),
    )
    newer_lease = timezone.now() + timedelta(seconds=120)
    token_urlsafe_mock = mocker.patch(
        target='src.authentication.tokens.secrets.token_urlsafe',
        return_value='test-import-capability',
    )

    def storage_side_effect(*, path: str, payload: dict):
        ImportJob.objects.filter(pk=job.pk).update(
            state='running',
            attempts=2,
            lease_until=newer_lease,
        )
        if failure:
            raise StorageUnavailable('test old worker failure')

    storage_mock = mocker.patch(
        target=(
            'src.storage.services.file_service.FileServiceClient.post_internal'
        ),
        side_effect=storage_side_effect,
    )

    # act
    import_upload(session_id=str(session.pk))
    job.refresh_from_db()

    # assert
    assert job.state == 'running'
    assert job.attempts == 2
    assert job.lease_until == newer_lease
    storage_mock.assert_called_once_with(
        path='/internal/mcp/import',
        payload={
            'credential': 'mcp-u_test-import-capability',
            'upload_session_id': str(session.pk),
            'url': 'https://remote.test/file',
            'filename': 'import.txt',
        },
    )
    token_urlsafe_mock.assert_called_once_with(32)
