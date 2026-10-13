from src.processes.services.upload_fields import UploadFieldService
from collections.abc import Callable
from types import SimpleNamespace

import pytest
from django.http import Http404
from pytest_django.fixtures import SettingsWrapper

from src.generics.tests.clients import PneumaticApiClient
from src.mcp.models import UploadSession
from src.processes.enums import FieldType
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.templates.template import TemplateIntegrations
from src.processes.tests.fixtures import create_test_template

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'case',
    ['hidden', 'field_deleted', 'fieldset_deleted', 'kickoff_deleted'],
)
def test_get_kickoff_field__unavailable_fieldset_parent__not_found(
    grant: SimpleNamespace,
    kickoff_fieldset: SimpleNamespace,
    case: str,
):

    # arrange
    field = kickoff_fieldset.field
    if case == 'hidden':
        field.is_hidden = True
        field.save(update_fields=['is_hidden'])
    else:
        target = {
            'field_deleted': field,
            'fieldset_deleted': kickoff_fieldset.fieldset,
            'kickoff_deleted': kickoff_fieldset.template.kickoff_instance,
        }[case]
        target.is_deleted = True
        target.save(update_fields=['is_deleted'])

    # act
    with pytest.raises(Http404) as error:
        UploadFieldService.get_kickoff_field(
            user=grant.user,
            template_id=kickoff_fieldset.template.pk,
            field_api_name=field.api_name,
        )

    # assert
    assert str(error.value) == 'No FieldTemplate matches the given query.'
    assert not UploadSession.objects.exists()


@pytest.mark.parametrize('files_write', [True, False])
@pytest.mark.parametrize('layout', ['direct', 'fieldset'])
@pytest.mark.parametrize('invalid_payload', [True, False])
@pytest.mark.django_db(transaction=True)
def test_run__verified_kickoff_session__consumed_transactionally(
    api_client: PneumaticApiClient,
    delegated_client: Callable,
    grant: SimpleNamespace,
    mcp_settings: SettingsWrapper,
    kickoff_fieldset: SimpleNamespace,
    layout: str,
    files_write: bool,
    invalid_payload: bool,
):
    # arrange
    template = (
        kickoff_fieldset.template
        if layout == 'fieldset'
        else create_test_template(user=grant.user, is_active=True)
    )
    TemplateIntegrations.objects.create(
        template=template,
        account=grant.account,
    )
    if layout == 'fieldset':
        field = kickoff_fieldset.field
    else:
        field = FieldTemplate.objects.create(
            template=template,
            kickoff=template.kickoff_instance,
            account=grant.account,
            api_name='field_file',
            type=FieldType.FILE,
            name='Input file',
        )
    client = delegated_client(
        tool='create_upload_link',
        method='POST',
        path='/integrations/mcp/uploads',
    )
    created = client.post(
        path='/integrations/mcp/uploads',
        data={
            'target_type': 'kickoff',
            'template_id': template.pk,
            'field_api_name': field.api_name,
            'filename': 'input.txt',
            'content_type': 'text/plain',
            'size': 3,
        },
    )
    upload = created.json()
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {mcp_settings.MCP_FILE_SERVICE_SECRET}',
    )
    completed = api_client.post(
        path='/internal/mcp/complete-upload',
        data={
            'credential': upload['credential'],
            'upload_session_id': upload['id'],
            'file_id': 'kickoff-file-1',
            'name': 'input.txt',
            'size': 3,
            'content_type': 'text/plain',
        },
    )
    path = f'/templates/{template.pk}/run'
    client = delegated_client(
        tool='run_workflow',
        method='POST',
        path=path,
        scopes=None if files_write else ['pneumatic:write'],
    )

    # act
    response = client.post(
        path=path,
        data={
            **({'due_date_tsp': 'invalid'} if invalid_payload else {}),
            'kickoff': {
                field.api_name: [{'upload_id': upload['id']}],
            },
        },
    )
    session = UploadSession.objects.get(pk=upload['id'])

    # assert
    assert created.status_code == 201, created.content
    assert completed.status_code == 200, completed.content
    assert (field.kickoff_id is None) == (layout == 'fieldset')
    if files_write and not invalid_payload:
        assert response.status_code == 200, response.content
        assert session.status == 'attached'
        workflow = template.workflows.get(pk=response.json()['id'])
        assert (
            workflow.fields.get(api_name=field.api_name)
            .storage_attachments.get()
            .file_id
            == 'kickoff-file-1'
        )
    elif not files_write:
        assert response.status_code == 403, response.content
        assert response.json()['required_scopes'] == [
            'pneumatic:write',
            'files:write',
        ]
        assert session.status == 'ready'
        assert not template.workflows.exists()
    else:
        assert response.status_code == 400, response.content
        assert session.status == 'ready'
        assert not template.workflows.exists()
