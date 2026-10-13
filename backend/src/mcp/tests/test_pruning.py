from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.utils import timezone

from src.mcp.models import (
    AuthorizationRequest,
    CodeBinding,
    Delegation,
    FileAuthorization,
    ImportJob,
    LoginCode,
    UploadCapability,
    UploadSession,
)
from src.mcp.tasks import prune_expired_state
from src.processes.models.workflows.fields import TaskField

pytestmark = pytest.mark.django_db


def test_prune__expired_ephemeral_records__keep_live_and_pending(
    grant: SimpleNamespace,
    task_field: TaskField,
):
    # arrange
    expired = timezone.now() - timedelta(seconds=1)
    live = timezone.now() + timedelta(hours=24)
    request = AuthorizationRequest.objects.create(
        parameters={},
        user=grant.user,
        account=grant.account,
        expires_at=expired,
    )
    LoginCode.objects.create(
        digest='expired-login',
        authorization_request=request,
        user=grant.user,
        account=grant.account,
        expires_at=expired,
    )
    CodeBinding.objects.create(
        digest='expired-code',
        connection=grant.connection,
        expires_at=expired,
    )
    session = UploadSession.objects.create(
        connection=grant.connection,
        task=task_field.task,
        field=task_field,
        filename='test.txt',
        size=3,
        content_type='text/plain',
        expires_at=live,
        status='importing',
        source_url='https://remote.test/file?signature=private',
    )
    ImportJob.objects.create(session=session, next_attempt_at=expired)
    UploadCapability.objects.create(
        session=session,
        digest='expired-capability',
        expires_at=expired,
    )
    FileAuthorization.objects.create(
        connection=grant.connection,
        source_token=grant.access,
        file_id='file-1',
        expires_at=expired,
    )
    # act
    prune_expired_state()
    session.refresh_from_db()

    # assert
    assert not AuthorizationRequest.objects.exists()
    assert not LoginCode.objects.exists()
    assert not CodeBinding.objects.exists()
    assert not UploadCapability.objects.exists()
    assert not FileAuthorization.objects.exists()
    assert ImportJob.objects.get().state == 'queued'
    assert session.source_url == 'https://remote.test/file?signature=private'


def test_prune__bounded_expired_batch__preserves_remaining_and_live(
    grant: SimpleNamespace,
):
    # arrange
    records = [
        Delegation(
            digest=f'old-{number}',
            connection=grant.connection,
            source_token=grant.access,
            audience='pneumatic-backend',
            operation='list_templates',
            method='GET',
            path='/templates',
            scopes=['pneumatic:read'],
            expires_at=timezone.now() - timedelta(seconds=1),
        )
        for number in range(501)
    ]
    Delegation.objects.bulk_create(records)
    live = Delegation.objects.create(
        digest='live',
        connection=grant.connection,
        source_token=grant.access,
        audience='pneumatic-backend',
        operation='list_templates',
        method='GET',
        path='/templates',
        scopes=['pneumatic:read'],
        expires_at=timezone.now() + timedelta(seconds=60),
    )

    # act
    prune_expired_state()

    # assert
    assert Delegation.objects.count() == 2
    assert Delegation.objects.filter(pk=live.pk).exists()
