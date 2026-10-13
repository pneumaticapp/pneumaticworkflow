from src.storage import messages as fs_messages
from types import SimpleNamespace
from urllib.parse import quote

import pytest
from pytest_django.fixtures import SettingsWrapper
from rest_framework.exceptions import PermissionDenied, ValidationError

from src.authentication.services.delegation import DelegationService
from src.generics.tests.clients import PneumaticApiClient
from src.mcp.models import Delegation
from src.mcp.serializers.files import FileValidationSerializer
from src.authentication.tokens import get_digest
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment

pytestmark = pytest.mark.django_db


def test_delegate__long_unicode_encoded_path__http_and_db_accept(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
    mcp_settings: SettingsWrapper,
):
    # arrange
    file_id = '😀' * 508 + '.pdf'
    path = f'/mcp/files/{quote(file_id, safe="")}'
    api_client.credentials(
        HTTP_X_MCP_SERVICE_SECRET=mcp_settings.MCP_SERVICE_SECRET,
    )

    # act
    response = api_client.post(
        path='/internal/mcp/delegate',
        data={
            'token': grant.token,
            'resource': mcp_settings.MCP_PUBLIC_URL,
            'tool': 'get_file_metadata',
            'method': 'GET',
            'path': path,
        },
    )

    # assert
    assert len(path) > 2048
    assert response.status_code == 200, response.content
    record = Delegation.objects.get(
        digest=get_digest(value=response.json()['credential']),
    )
    assert record.path == path


@pytest.mark.parametrize(
    'file_id',
    [
        'NiihssB_Drawing (v2).odg',
        'legacy_мой отчёт (версия2).pdf',  # noqa: RUF001 - legacy Unicode identity
        '😀' * 508 + '.pdf',
    ],
)
def test_validate_files__legacy_encoded_identity__metadata_and_ticket(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
    mcp_settings: SettingsWrapper,
    file_id: str,
):
    # arrange
    Attachment.objects.create(
        account=grant.account,
        file_id=file_id,
        access_type=AccessType.ACCOUNT,
        source_type=SourceType.ACCOUNT,
    )
    segment = quote(file_id, safe='')
    metadata = DelegationService.create(
        token=grant.token,
        resource=mcp_settings.MCP_PUBLIC_URL,
        tool='get_file_metadata',
        method='GET',
        path=f'/mcp/files/{segment}',
    )
    ticket = DelegationService.create(
        token=grant.token,
        resource=mcp_settings.MCP_PUBLIC_URL,
        tool='create_download_ticket',
        method='POST',
        path=f'/mcp/files/{segment}/download-ticket',
    )
    api_client.credentials(
        HTTP_X_MCP_FILE_SERVICE_SECRET=mcp_settings.MCP_FILE_SERVICE_SECRET,
    )

    # act
    read = api_client.post(
        path='/internal/mcp/validate-files',
        data={
            'credential': metadata.credential,
            'operation': 'metadata',
            'file_id': file_id,
        },
    )
    issued = api_client.post(
        path='/internal/mcp/validate-files',
        data={
            'credential': ticket.credential,
            'operation': 'download',
            'file_id': file_id,
        },
    )
    checked = api_client.post(
        path='/internal/mcp/validate-files',
        data={
            'operation': 'download',
            'file_id': file_id,
            'connection_id': str(grant.connection.pk),
            'authorization_id': issued.json()['authorization_id'],
        },
    )
    wrong = api_client.post(
        path='/internal/mcp/validate-files',
        data={
            'credential': metadata.credential,
            'operation': 'metadata',
            'file_id': file_id[:-1] + 'x',
        },
    )

    # assert
    assert read.status_code == 200, read.content
    assert read.json()['active'] is True
    assert issued.status_code == 200, issued.content
    assert issued.json()['active'] is True
    assert checked.json()['active'] is True
    assert wrong.json() == {'active': False}


@pytest.mark.parametrize(
    'segment',
    [
        'raw space.txt',
        '%2F',
        '%5C',
        '%252F',
        '%3F',
        '%23',
        '%00',
        '..',
        'bad%ff',
        'legacy%20name%2etxt',
    ],
)
def test_delegate__noncanonical_or_unsafe_file_path__denied(
    grant: SimpleNamespace,
    mcp_settings: SettingsWrapper,
    segment: str,
):
    # arrange
    path = f'/mcp/files/{segment}'

    # act
    with pytest.raises(PermissionDenied) as error:
        DelegationService.create(
            token=grant.token,
            resource=mcp_settings.MCP_PUBLIC_URL,
            tool='get_file_metadata',
            method='GET',
            path=path,
        )

    # assert
    assert str(error.value) == PermissionDenied.default_detail


@pytest.mark.parametrize('file_id', ['a/b', 'a\\b', 'a?b', 'a#b', '%2f', '..'])
def test_file_validation__unsafe_raw_identity__400(file_id: str):
    # arrange
    serializer = FileValidationSerializer(
        data={
            'operation': 'metadata',
            'file_id': file_id,
        },
    )

    # act
    with pytest.raises(ValidationError) as error:
        serializer.is_valid(raise_exception=True)

    # assert
    assert error.value.detail == {
        'message': fs_messages.MSG_FS_0012,
        'code': 'validation_error',
        'details': {'name': 'file_id', 'reason': fs_messages.MSG_FS_0012},
    }
