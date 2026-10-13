"""Use core's actual canonicalizer to verify storage's filename contract."""

from io import BytesIO
from types import ModuleType
from typing import Any
from unittest.mock import ANY

import pytest
from pytest_mock import MockerFixture

from src.infra.mappers import FileRecordMapper
from src.infra.url_importer import ImportedFile
from src.shared_kernel.database.models import FileRecordORM
from src.shared_kernel.exceptions.mcp_exceptions import MCPUploadConflictError
from src.shared_kernel.security.filename import secure_filename


@pytest.mark.parametrize(
    ('original', 'canonical'),
    [
        ('my report.pdf', 'my_report.pdf'),
        ('my___ report.pdf', 'my_report.pdf'),
        ('отчёт за 2024.pdf', 'отчёт_за_2024.pdf'),
        ('.report.pdf', 'report.pdf'),
        ('report.pdf ', 'report.pdf_'),
        ('...', 'unnamed_file'),
    ],
)
def test_actual__core_filename_rules_match_storage__ok(
    core_metadata: ModuleType, original: str, canonical: str
):
    # arrange

    # act
    result = core_metadata.canonical_filename(value=original)

    # assert
    assert result == canonical
    assert secure_filename(filename=original) == canonical
    assert secure_filename(filename=canonical) == canonical


@pytest.mark.parametrize('operation', ['upload', 'import'])
@pytest.mark.parametrize('use_returned_name', [True, False])
async def test_spaced__session_name_callback_and_metadata_match_core__ok(
    mcp_context: dict[str, Any],
    mocker: MockerFixture,
    core_metadata: ModuleType,
    operation: str,
    use_returned_name: bool,
):
    # arrange

    context = mcp_context
    original_name = 'my report.pdf'

    # Core's actual helper supplies the filename returned to the UI/job.
    session_name = core_metadata.canonical_filename(value=original_name)

    submitted_name = session_name if use_returned_name else original_name
    content = b'%PDF-contract-file'
    mime = 'application/pdf'
    original_core = context['core'].side_effect

    async def strict_core(path: str, body: dict[str, Any]) -> dict[str, Any]:
        if path == '/internal/mcp/complete-upload' and (
            body['name'],
            body['size'],
            body['content_type'],
        ) != (session_name, len(content), mime):
            raise MCPUploadConflictError
        return await original_core(path=path, body=body)

    context['core'].side_effect = strict_core
    fetch = mocker.patch(
        'src.application.use_cases.mcp_import.URLImporter.download',
        return_value=ImportedFile(
            stream=BytesIO(content), size=len(content), content_type=mime
        ),
    )

    def submit():
        if operation == 'upload':
            return context['client'].post(
                url='/upload',
                headers={
                    'Authorization': 'Bearer mcp-u_upload',
                    'X-MCP-Upload-Session': 'session-1',
                },
                files={'file': (submitted_name, content, mime)},
            )
        secret = context['settings'].MCP_FILE_SERVICE_SECRET.get_secret_value()
        return context['client'].post(
            url='/internal/mcp/import',
            headers={'Authorization': f'Bearer {secret}'},
            json={
                'credential': 'mcp-u_import',
                'upload_session_id': 'session-1',
                'url': 'https://source.example/report.pdf',
                'filename': submitted_name,
            },
        )

    # act
    response = submit()
    record = await context['session'].get(
        entity=FileRecordORM, ident=response.json()['file_id']
    )
    context[
        'download'
    ].get_metadata.return_value = FileRecordMapper.orm_to_entity(orm=record)
    metadata = context['client'].get(
        url=f'/mcp/files/{record.file_id}',
        headers={'Authorization': 'Bearer mcp-d_read'},
    )
    await context['session'].commit()
    retry = submit()

    # assert
    assert session_name == 'my_report.pdf'
    assert response.status_code == 200, response.text
    assert retry.status_code == 200
    assert (record.filename, record.account_id, record.user_id) == (
        session_name,
        10,
        1,
    )
    assert metadata.status_code == 200
    assert metadata.json()['name'] == session_name
    assert metadata.json()['size'] == len(content)
    assert metadata.json()['content_type'] == mime
    assert context['callbacks'][0]['name'] == session_name
    assert context['callbacks'][1]['name'] == session_name
    context['storage'].upload_file.assert_awaited_once_with(
        bucket_name='bucket',
        file_path='path',
        file_stream=ANY,
        content_type=mime,
    )
    context['events'].file_upload.assert_awaited_once_with(
        user=ANY,
        file_id=record.file_id,
        file=ANY,
    )
    if operation == 'import':
        fetch.assert_awaited_once_with(
            raw_url='https://source.example/report.pdf',
        )
    else:
        fetch.assert_not_awaited()
