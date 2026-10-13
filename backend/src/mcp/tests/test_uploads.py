import src.storage.messages as fs_messages
from src.processes.services.upload_fields import UploadFieldService
from src.storage.services.upload_sessions import UploadSessionService
from collections.abc import Callable
from datetime import timedelta
from types import SimpleNamespace
from uuid import NAMESPACE_URL, uuid5

import pytest
from django.http import Http404
from django.utils import timezone
from pytest_django.fixtures import SettingsWrapper
from rest_framework.exceptions import ValidationError

from src.accounts.enums import BillingPlanType
from src.authentication.services.delegation import DelegationService
from src.generics.tests.clients import PneumaticApiClient
from src.authentication.constants import (
    UPLOAD_CAPABILITY_TTL,
)
from src.mcp.models import (
    FileAuthorization,
    ImportJob,
    UploadCapability,
    UploadSession,
)
from src.mcp.serializers.uploads import ImportSerializer
from src.authentication.tokens import get_digest, get_expires_in
from src.processes.models.workflows.fields import TaskField
from src.processes.tests.fixtures import create_test_account
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment
from src.storage.utils import extract_file_ids_from_text

pytestmark = pytest.mark.django_db


def test_create_session__template_task_fieldset__real_parent_link(
    grant: SimpleNamespace,
    task_fieldset: SimpleNamespace,
    mcp_settings: SettingsWrapper,
):

    # arrange
    issued = DelegationService.create(
        token=grant.token,
        resource=mcp_settings.MCP_PUBLIC_URL,
        tool='create_upload_link',
        method='POST',
        path='/integrations/mcp/uploads',
    )
    request = SimpleNamespace(
        user=grant.user,
        auth=DelegationService.get_delegation(
            credential=issued.credential,
        ),
    )
    data = {
        'target_type': 'task',
        'task_id': task_fieldset.task.pk,
        'field_api_name': task_fieldset.field.api_name,
        'filename': 'fieldset.txt',
        'content_type': 'text/plain',
        'size': 3,
    }

    # act
    result = UploadSessionService.create(
        user=request.user,
        delegation=request.auth,
        data=data,
    )
    session = result.session

    # assert
    assert task_fieldset.field.task_id is None
    assert session.task_id == task_fieldset.task.pk
    assert session.field_id == task_fieldset.field.pk
    assert session.status == 'pending'
    assert UploadCapability.objects.filter(session=session).count() == 1


@pytest.mark.parametrize(
    'case',
    [
        'hidden',
        'field_deleted',
        'fieldset_deleted',
        'task_deleted',
        'workflow_deleted',
        'missing_parent',
        'foreign_parent',
    ],
)
def test_get_task_field__unavailable_fieldset_parent__not_found(
    grant: SimpleNamespace,
    task_fieldset: SimpleNamespace,
    case: str,
):

    # arrange
    task = task_fieldset.task
    field = task_fieldset.field
    fieldset = task_fieldset.fieldset
    if case == 'hidden':
        field.is_hidden = True
        field.save(update_fields=['is_hidden'])
    elif case == 'missing_parent':
        fieldset.task = None
        fieldset.save(update_fields=['task'])
    elif case == 'foreign_parent':
        fieldset.account = create_test_account()
        fieldset.save(update_fields=['account'])
    else:
        target = {
            'field_deleted': field,
            'fieldset_deleted': fieldset,
            'task_deleted': task,
            'workflow_deleted': task.workflow,
        }[case]
        target.is_deleted = True
        target.save(update_fields=['is_deleted'])
    # act
    with pytest.raises(Http404) as error:
        UploadFieldService.get_task_field(
            user=grant.user,
            task_id=task.pk,
            field_api_name=field.api_name,
        )

    # assert
    assert str(error.value) in {
        'No Task matches the given query.',
        'No TaskField matches the given query.',
    }
    assert not UploadSession.objects.exists()
    assert not UploadCapability.objects.exists()


def test_attach_upload__task_fieldset__single_real_attachment(
    grant: SimpleNamespace,
    task_fieldset: SimpleNamespace,
    fieldset_upload_session: SimpleNamespace,
):

    # arrange
    upload = fieldset_upload_session
    UploadSessionService.complete_upload(
        data={
            'credential': upload.credential,
            'upload_session_id': str(upload.session.pk),
            'file_id': 'fieldset-file-1',
            'name': 'fieldset.txt',
            'size': 3,
            'content_type': 'text/plain',
        },
    )

    # act
    result = UploadSessionService.attach(
        user=upload.request.user,
        delegation=upload.request.auth,
        session_id=upload.session.pk,
        task_id=task_fieldset.task.pk,
    )
    attachment = Attachment.objects.get(file_id='fieldset-file-1')
    task_fieldset.field.refresh_from_db()
    upload.session.refresh_from_db()

    # assert
    assert result.status == 'attached'
    assert upload.session.status == 'attached'
    assert task_fieldset.field.task_id is None
    assert attachment.task_id is None
    assert attachment.workflow_id == task_fieldset.task.workflow_id
    assert attachment.output_id == task_fieldset.field.pk
    assert attachment.source_type == SourceType.WORKFLOW
    assert attachment.account_id == grant.account.pk
    assert task_fieldset.field.storage_attachments.count() == 1
    assert extract_file_ids_from_text(task_fieldset.field.markdown_value) == [
        'fieldset-file-1',
    ]


@pytest.mark.parametrize('case', ['visible', 'hidden', 'parent_deleted'])
def test_attach_upload__fieldset_repeat__current_visibility(
    delegated_client: Callable,
    task_fieldset: SimpleNamespace,
    fieldset_upload_session: SimpleNamespace,
    case: str,
):

    # arrange
    upload = fieldset_upload_session
    UploadSessionService.complete_upload(
        data={
            'credential': upload.credential,
            'upload_session_id': str(upload.session.pk),
            'file_id': 'fieldset-replay-1',
            'name': 'fieldset.txt',
            'size': 3,
            'content_type': 'text/plain',
        },
    )
    path = f'/integrations/mcp/uploads/{upload.session.pk}/attach'
    client = delegated_client(
        tool='attach_uploaded_file',
        method='POST',
        path=path,
    )
    data = {'task_id': task_fieldset.task.pk}
    first = client.post(
        path=path,
        data=data,
    )
    if case == 'hidden':
        task_fieldset.field.is_hidden = True
        task_fieldset.field.save(update_fields=['is_hidden'])
    elif case == 'parent_deleted':
        task_fieldset.fieldset.is_deleted = True
        task_fieldset.fieldset.save(update_fields=['is_deleted'])

    # act
    replay = client.post(
        path=path,
        data=data,
    )

    # assert
    assert first.status_code == 200, first.content
    if case == 'visible':
        assert replay.status_code == 409, replay.content
    else:
        assert replay.status_code == 404, replay.content
    assert Attachment.objects.filter(file_id='fieldset-replay-1').count() == 1


@pytest.mark.parametrize('url', [
    'https://remote.test:bad/file',
    'https://[invalid/file',
    'https://[invalid]/file',
])
def test_import_serializer__invalid_url__validation_error(
    upload_session: SimpleNamespace,
    url: str,
):

    # arrange
    message = fs_messages.MSG_FS_0021
    serializer = ImportSerializer(
        data={'url': url},
    )

    # act
    with pytest.raises(ValidationError) as error:
        serializer.is_valid(raise_exception=True)

    # assert
    assert error.value.detail == {
        'message': message,
        'code': 'validation_error',
        'details': {'name': 'url', 'reason': message},
    }
    upload_session.session.refresh_from_db()
    assert upload_session.session.status == 'pending'
    assert upload_session.session.source_url == ''
    assert not ImportJob.objects.exists()


def test_create_upload_token__session_near_expiry__bounded_lifetime(
    upload_session: SimpleNamespace,
):

    # arrange
    session = upload_session.session
    session.expires_at = timezone.now() + timedelta(seconds=20)
    session.save(update_fields=['expires_at'])

    # act
    result = UploadSessionService.create_upload_token(
        user=upload_session.request.user,
        delegation=upload_session.request.auth,
        session_id=session.pk,
    )

    # assert
    capability = UploadCapability.objects.get(
        digest=get_digest(value=result.credential),
    )
    assert capability.expires_at == session.expires_at
    assert result.session.pk == session.pk
    assert (
        0
        < get_expires_in(
            expires_at=capability.expires_at,
            ttl=UPLOAD_CAPABILITY_TTL,
        )
        <= 20
    )


@pytest.mark.parametrize(
    'callback,status',
    [
        ('validate-files', 200),
        ('complete-upload', 403),
    ],
)
def test_upload__hidden_target__callback_denied(
    api_client: PneumaticApiClient,
    upload_session: SimpleNamespace,
    task_field: TaskField,
    mcp_settings: SettingsWrapper,
    callback: str,
    status: int,
):

    # arrange
    task_field.is_hidden = True
    task_field.save(update_fields=['is_hidden'])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {mcp_settings.MCP_FILE_SERVICE_SECRET}',
    )
    data = {
        'credential': upload_session.credential,
        'operation': 'upload',
        'upload_session_id': str(upload_session.session.pk),
        'file_id': 'uploaded-file-1',
        'name': 'test.txt',
        'size': 3,
        'content_type': 'text/plain',
    }

    # act
    response = api_client.post(path=f'/internal/mcp/{callback}', data=data)

    # assert
    assert response.status_code == status
    if status == 200:
        assert response.json() == {'active': False}
    else:
        assert response.json() == {
            'detail': 'You do not have permission to perform this action.',
        }
    upload_session.session.refresh_from_db()
    assert upload_session.session.file_id == ''
    assert upload_session.session.status == 'pending'


@pytest.mark.parametrize(
    'case,active',
    [
        ('valid', True),
        ('expired', False),
        ('missing', False),
    ],
)
def test_validate_files__ticket_authorization__expected_activity(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
    mcp_settings: SettingsWrapper,
    case: str,
    active: bool,
):

    # arrange
    file_id = 'download-file-1'
    Attachment.objects.create(
        account=grant.account,
        file_id=file_id,
        access_type=AccessType.ACCOUNT,
        source_type=SourceType.ACCOUNT,
    )
    authorization = FileAuthorization.objects.create(
        connection=grant.connection,
        source_token=grant.access,
        file_id=file_id,
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    data = {
        'operation': 'download',
        'file_id': file_id,
        'connection_id': str(grant.connection.pk),
    }
    if case != 'missing':
        data['authorization_id'] = str(authorization.pk)
    if case == 'expired':
        grant.access.expires = timezone.now() - timedelta(seconds=1)
        grant.access.save(update_fields=['expires'])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {mcp_settings.MCP_FILE_SERVICE_SECRET}',
    )

    # act
    response = api_client.post(path='/internal/mcp/validate-files', data=data)

    # assert
    assert response.status_code == 200
    assert response.json()['active'] is active
    if active:
        assert response.json()['authorization_id'] == str(authorization.pk)
        assert response.json()['account_id'] == grant.account.pk
    else:
        assert response.json() == {'active': False}


def test_attach_upload__three_files__preserves_all_links(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
    delegated_client: Callable,
    task_field: TaskField,
    mcp_settings: SettingsWrapper,
):
    # arrange
    results = []

    # act
    for number in range(3):
        client = delegated_client(
            tool='create_upload_link',
            method='POST',
            path='/integrations/mcp/uploads',
        )
        created = client.post(
            path='/integrations/mcp/uploads',
            data={
                'target_type': 'task',
                'task_id': task_field.task_id,
                'field_api_name': task_field.api_name,
                'filename': f'file{number}.txt',
                'content_type': 'text/plain',
                'size': 3,
            },
            HTTP_IDEMPOTENCY_KEY=f'upload-{number}',
        )
        assert created.status_code == 201, created.content
        upload = created.json()
        file_secret = mcp_settings.MCP_FILE_SERVICE_SECRET
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {file_secret}')
        completed = api_client.post(
            path='/internal/mcp/complete-upload',
            data={
                'credential': upload['credential'],
                'upload_session_id': upload['id'],
                'file_id': f'uploaded-file-{number}',
                'name': f'file{number}.txt',
                'size': 3,
                'content_type': 'text/plain',
            },
        )
        assert completed.status_code == 200, completed.content
        path = f'/integrations/mcp/uploads/{upload["id"]}/attach'
        client = delegated_client(
            tool='attach_uploaded_file',
            method='POST',
            path=path,
        )
        results.append(
            client.post(
                path=path,
                data={
                    'task_id': task_field.task_id,
                },
                HTTP_IDEMPOTENCY_KEY=f'attach-{number}',
            ),
        )
    task_field.refresh_from_db()

    # assert
    assert results[0].status_code == 200, results[0].content
    assert results[1].status_code == 200, results[1].content
    assert results[2].status_code == 200, results[2].content
    assert extract_file_ids_from_text(task_field.markdown_value) == [
        'uploaded-file-0',
        'uploaded-file-1',
        'uploaded-file-2',
    ]
    assert task_field.storage_attachments.count() == 3


@pytest.mark.parametrize('action,status', [('validate', 200), ('revoke', 204)])
def test_subscription_expired__file_access_or_revocation__expected_status(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
    mcp_settings: SettingsWrapper,
    action: str,
    status: int,
):
    # arrange
    file_id = 'download-file-1'
    Attachment.objects.create(
        account=grant.account,
        file_id=file_id,
        access_type=AccessType.ACCOUNT,
        source_type=SourceType.ACCOUNT,
    )
    delegated = DelegationService.create(
        token=grant.token,
        resource=mcp_settings.MCP_PUBLIC_URL,
        tool='get_file_metadata',
        method='GET',
        path=f'/mcp/files/{file_id}',
    )
    grant.account.billing_plan = BillingPlanType.PREMIUM
    grant.account.plan_expiration = timezone.now() - timedelta(days=1)
    grant.account.save(update_fields=['billing_plan', 'plan_expiration'])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {mcp_settings.MCP_FILE_SERVICE_SECRET}',
    )

    if action == 'revoke':
        api_client.token_authenticate(user=grant.user)

    # act
    if action == 'validate':
        response = api_client.post(
            path='/internal/mcp/validate-files',
            data={
                'credential': delegated.credential,
                'operation': 'metadata',
                'file_id': file_id,
            },
        )
    else:
        response = api_client.delete(
            path=f'/integrations/mcp/connections/{grant.connection.pk}',
        )

    # assert
    assert response.status_code == status
    if action == 'validate':
        assert response.json() == {'active': False}
    else:
        grant.connection.refresh_from_db()
        assert grant.connection.revoked_at is not None


def test_cleanup__deleted_attachment_reference__conservative_deny(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
    task_field: TaskField,
    mcp_settings: SettingsWrapper,
):
    # arrange
    session = UploadSession.objects.create(
        connection=grant.connection,
        task=task_field.task,
        field=task_field,
        filename='test.txt',
        size=3,
        content_type='text/plain',
        status='ready',
        file_id='cleanup-file-1',
        expires_at=timezone.now() - timedelta(hours=1),
    )
    UploadSession.objects.filter(pk=session.pk).update(
        created_at=timezone.now() - timedelta(hours=25),
    )
    attachment = Attachment.objects.create(
        account=grant.account,
        file_id=session.file_id,
        source_type=SourceType.ACCOUNT,
        is_deleted=True,
    )
    data = {
        'upload_session_id': str(session.pk),
        'file_id': session.file_id,
        'user_id': grant.user.pk,
        'account_id': grant.account.pk,
    }
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {mcp_settings.MCP_FILE_SERVICE_SECRET}',
    )

    # act
    referenced = api_client.post(
        path='/internal/mcp/cleanup-upload',
        data=data,
    )
    Attachment._base_manager.filter(pk=attachment.pk).delete()
    eligible = api_client.post(path='/internal/mcp/cleanup-upload', data=data)
    retry = api_client.post(path='/internal/mcp/cleanup-upload', data=data)
    session.refresh_from_db()

    # assert
    assert referenced.json() == {'eligible': False}
    assert eligible.json() == {'eligible': True}
    assert retry.json() == {'eligible': True}
    assert session.status == 'cleaned'


def test_cleanup__lost_completion_callback__deterministic_file_only(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
    task_field: TaskField,
    mcp_settings: SettingsWrapper,
):
    # arrange
    session = UploadSession.objects.create(
        connection=grant.connection,
        task=task_field.task,
        field=task_field,
        filename='test.txt',
        size=3,
        content_type='text/plain',
        expires_at=timezone.now() - timedelta(hours=1),
    )
    UploadSession.objects.filter(pk=session.pk).update(
        created_at=timezone.now() - timedelta(hours=25),
    )
    file_id = str(uuid5(NAMESPACE_URL, f'pneumatic:mcp:{session.pk}'))
    data = {
        'upload_session_id': str(session.pk),
        'file_id': 'wrong-file-id',
        'user_id': grant.user.pk,
        'account_id': grant.account.pk,
    }
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {mcp_settings.MCP_FILE_SERVICE_SECRET}',
    )

    # act
    wrong = api_client.post(path='/internal/mcp/cleanup-upload', data=data)
    data['file_id'] = file_id
    accepted = api_client.post(path='/internal/mcp/cleanup-upload', data=data)
    session.refresh_from_db()

    # assert
    assert wrong.json() == {'eligible': False}
    assert accepted.json() == {'eligible': True}
    assert session.status == 'cleaned'
    assert session.file_id == file_id


@pytest.mark.parametrize('operation', ['upload', 'import'])
def test_upload__spaced_filename_callback__canonical_ready(
    api_client: PneumaticApiClient,
    delegated_client: Callable,
    task_field: TaskField,
    mcp_settings: SettingsWrapper,
    operation: str,
):
    # arrange
    client = delegated_client(
        tool='create_upload_link',
        method='POST',
        path='/integrations/mcp/uploads',
    )
    created = client.post(
        path='/integrations/mcp/uploads',
        data={
            'target_type': 'task',
            'task_id': task_field.task_id,
            'field_api_name': task_field.api_name,
            'filename': 'my report.pdf',
            'content_type': 'application/pdf',
            'size': 3,
        },
    )
    upload = created.json()
    if operation == 'import':
        path = f'/integrations/mcp/uploads/{upload["id"]}/import'
        client = delegated_client(
            tool='import_attachment_from_url',
            method='POST',
            path=path,
        )
        queued = client.post(
            path=path,
            data={
                'url': 'https://remote.test/report.pdf',
            },
        )
        assert queued.status_code == 202, queued.content
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {mcp_settings.MCP_FILE_SERVICE_SECRET}',
    )
    actual_size = 5 if operation == 'import' else 3

    # act
    response = api_client.post(
        path='/internal/mcp/complete-upload',
        data={
            'credential': upload['credential'],
            'upload_session_id': upload['id'],
            'file_id': 'canonical-file-1',
            'name': 'my_report.pdf',
            'size': actual_size,
            'content_type': 'application/pdf',
        },
    )
    session = UploadSession.objects.get(pk=upload['id'])

    # assert
    assert created.status_code == 201, created.content
    assert upload['filename'] == 'my_report.pdf'
    assert response.status_code == 200, response.content
    assert session.status == 'ready'
    assert session.size == actual_size
    assert session.filename == 'my_report.pdf'
