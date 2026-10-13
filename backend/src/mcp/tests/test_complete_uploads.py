from src.storage.services.upload_sessions import UploadSessionService
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

import pytest
from pytest_django.fixtures import SettingsWrapper

from src.generics.tests.clients import PneumaticApiClient
from src.mcp.models import UploadSession
from src.processes.enums import FieldType
from src.processes.models.workflows.fields import TaskField
from src.processes.services.tasks.field import TaskFieldService
from src.storage.models import Attachment
from src.storage.utils import get_file_service_file_url

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('files_write', [True, False])
@pytest.mark.django_db(transaction=True)
def test_complete__fieldset_upload_reference__file_scope(
    grant: SimpleNamespace,
    delegated_client: Callable,
    task_fieldset: SimpleNamespace,
    fieldset_upload_session: SimpleNamespace,
    files_write: bool,
):

    # arrange
    upload = fieldset_upload_session
    UploadSessionService.complete_upload(
        data={
            'credential': upload.credential,
            'upload_session_id': str(upload.session.pk),
            'file_id': 'fieldset-complete-1',
            'name': 'fieldset.txt',
            'size': 3,
            'content_type': 'text/plain',
        },
    )
    path = f'/v2/tasks/{task_fieldset.task.pk}/complete'
    scopes = ['pneumatic:write']
    if files_write:
        scopes.append('files:write')
    client = delegated_client(
        tool='complete_task',
        method='POST',
        path=path,
        scopes=scopes,
    )
    data = {
        'output': {
            task_fieldset.field.api_name: [
                {'upload_id': str(upload.session.pk)},
            ],
        },
    }

    # act
    response = client.post(
        path=path,
        data=data,
    )
    upload.session.refresh_from_db()

    # assert
    if files_write:
        assert response.status_code == 200, response.content
        assert upload.session.status == 'attached'
        attachment = task_fieldset.field.storage_attachments.get()
        assert attachment.file_id == 'fieldset-complete-1'
        assert attachment.workflow_id == task_fieldset.task.workflow_id
        assert attachment.task_id is None
        assert task_fieldset.field.task_id is None
        assert attachment.account_id == grant.account.pk
    else:
        assert response.status_code == 403, response.content
        assert response.json()['required_scopes'] == [
            'pneumatic:write',
            'files:write',
        ]
        assert upload.session.status == 'ready'
        assert not task_fieldset.field.storage_attachments.exists()


@pytest.mark.parametrize('field_type', [FieldType.FILE, FieldType.TEXT])
@pytest.mark.parametrize('files_write', [True, False])
def test_complete__fieldset_file_clear__requires_file_scope(
    grant: SimpleNamespace,
    delegated_client: Callable,
    task_fieldset: SimpleNamespace,
    files_write: bool,
    field_type: str,
):

    # arrange
    field = task_fieldset.field
    field.type = field_type
    field.save(update_fields=['type'])
    link = (
        '[old.txt](' + get_file_service_file_url(file_id='fieldset-old') + ')'
    )
    TaskFieldService(user=grant.user, instance=field).partial_update(
        value=[link] if field_type == FieldType.FILE else link,
    )
    path = f'/v2/tasks/{task_fieldset.task.pk}/complete'
    scopes = ['pneumatic:write']
    if files_write:
        scopes.append('files:write')
    client = delegated_client(
        tool='complete_task',
        method='POST',
        path=path,
        scopes=scopes,
    )
    data = {'output': {field.api_name: ''}}

    # act
    response = client.post(
        path=path,
        data=data,
    )
    field.refresh_from_db()

    # assert
    if files_write:
        assert response.status_code == 200, response.content
        assert field.value == ''
        assert not Attachment.objects.filter(
            workflow=task_fieldset.task.workflow,
            file_id='fieldset-old',
        ).exists()
    else:
        assert response.status_code == 403, response.content
        assert field.markdown_value == link
        assert (
            Attachment.objects.filter(
                workflow=task_fieldset.task.workflow,
                file_id='fieldset-old',
            ).count()
            == 1
        )


def test_complete__repeated_file_clear_lower_scopes__denied(
    delegated_client: Callable,
    task_field: TaskField,
):
    # arrange
    path = f'/v2/tasks/{task_field.task_id}/complete'
    payload = {'output': {task_field.api_name: []}}
    client = delegated_client(
        tool='complete_task',
        method='POST',
        path=path,
    )
    first = client.post(
        path=path,
        data=payload,
    )
    client = delegated_client(
        tool='complete_task',
        method='POST',
        path=path,
        scopes=['pneumatic:write'],
    )

    # act
    replay = client.post(
        path=path,
        data=payload,
    )

    # assert
    assert first.status_code == 200, first.content
    assert replay.status_code == 403, replay.content
    assert replay.json()['required_scopes'] == [
        'pneumatic:write',
        'files:write',
    ]


@pytest.mark.parametrize('files_write', [True, False])
@pytest.mark.parametrize('value', [None, [], ''])
def test_complete__clear_existing_file__requires_file_scope(
    grant: SimpleNamespace,
    delegated_client: Callable,
    task_field: TaskField,
    files_write: bool,
    value: Any,
):
    # arrange
    link = (
        '[existing.txt]('
        + get_file_service_file_url(
            file_id='existing-file-1',
        )
        + ')'
    )
    TaskFieldService(user=grant.user, instance=task_field).partial_update(
        value=[link],
    )
    path = f'/v2/tasks/{task_field.task_id}/complete'
    scopes = ['pneumatic:write']
    if files_write:
        scopes.append('files:write')
    client = delegated_client(
        tool='complete_task',
        method='POST',
        path=path,
        scopes=scopes,
    )

    # act
    response = client.post(
        path=path,
        data={'output': {task_field.api_name: value}},
    )
    task_field.refresh_from_db()

    # assert
    if files_write:
        assert response.status_code == 200, response.content
        assert task_field.markdown_value == ''
        assert not task_field.storage_attachments.exists()
    else:
        assert response.status_code == 403, response.content
        assert response.json()['required_scopes'] == [
            'pneumatic:write',
            'files:write',
        ]
        assert task_field.markdown_value == link
        assert task_field.storage_attachments.count() == 1


@pytest.mark.parametrize('files_write', [True, False])
def test_complete__verified_upload_reference__conditional_file_scope(
    api_client: PneumaticApiClient,
    delegated_client: Callable,
    grant: SimpleNamespace,
    task_field: TaskField,
    mcp_settings: SettingsWrapper,
    files_write: bool,
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
            'task_id': task_field.task_id,
            'field_api_name': task_field.api_name,
            'filename': 'result.txt',
            'size': 3,
            'content_type': 'text/plain',
        },
    )
    upload = created.json()
    api_client.credentials(
        HTTP_X_MCP_FILE_SERVICE_SECRET=mcp_settings.MCP_FILE_SERVICE_SECRET,
    )
    completed = api_client.post(
        path='/internal/mcp/complete-upload',
        data={
            'credential': upload['credential'],
            'upload_session_id': upload['id'],
            'file_id': 'complete-file-1',
            'name': 'result.txt',
            'size': 3,
            'content_type': 'text/plain',
        },
    )
    path = f'/v2/tasks/{task_field.task_id}/complete'
    scopes = ['pneumatic:write']
    if files_write:
        scopes.append('files:write')
    client = delegated_client(
        tool='complete_task',
        method='POST',
        path=path,
        scopes=scopes,
    )
    payload = {
        'output': {task_field.api_name: [{'upload_id': upload['id']}]},
    }

    # act
    response = client.post(
        path=path,
        data=payload,
    )
    session = UploadSession.objects.get(pk=upload['id'])

    # assert
    assert created.status_code == 201, created.content
    assert completed.status_code == 200, completed.content
    if files_write:
        assert response.status_code == 200, response.content
        assert session.status == 'attached'
        attachment = task_field.storage_attachments.get()
        assert attachment.file_id == 'complete-file-1'
    else:
        assert response.status_code == 403, response.content
        assert session.status == 'ready'


@pytest.mark.parametrize(
    'value',
    [
        ['https://files.test/arbitrary-file'],
        [{'upload_id': 'invalid-uuid'}],
    ],
)
def test_complete__unverified_file_input__400(
    delegated_client: Callable,
    task_field: TaskField,
    value: Any,
):
    # arrange
    path = f'/v2/tasks/{task_field.task_id}/complete'
    client = delegated_client(tool='complete_task', method='POST', path=path)

    # act
    response = client.post(
        path=path,
        data={'output': {task_field.api_name: value}},
    )

    # assert
    assert response.status_code == 400, response.content
