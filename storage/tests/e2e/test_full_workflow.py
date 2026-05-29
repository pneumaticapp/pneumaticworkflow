"""Tests for complete upload-download workflow."""

from unittest.mock import MagicMock

import pytest

from tests.fixtures.e2e import AsyncIteratorMock


def test_workflow__basic_upload_download__ok(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    sample_file_content,
    auth_headers,
    mock_upload_response,
    mock_download_response,
    mock_upload_use_case_execute,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
):

    # arrange
    filename = 'workflow_test.txt'
    content_type = 'text/plain'
    mock_upload_use_case_execute.return_value = (
        mock_upload_response
    )
    file_record, stream = mock_download_response
    mock_download_use_case_get_metadata.return_value = (
        file_record
    )
    mock_download_use_case_get_stream.return_value = (
        stream
    )

    # act — upload
    upload_response = e2e_client.post(
        '/upload',
        files={
            'file': (
                filename,
                sample_file_content,
                content_type,
            ),
        },
        headers=auth_headers,
    )

    # assert — upload
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    assert 'file_id' in upload_data
    assert 'public_url' in upload_data
    assert upload_data['file_id'] == (
        '12345678-1234-5678-1234-567812345679'
    )

    file_id = upload_data['file_id']

    # act — download
    download_response = e2e_client.get(
        f'/{file_id}', headers=auth_headers,
    )

    # assert — download
    assert download_response.status_code == 200
    assert 'text/plain' in download_response.headers[
        'content-type'
    ]
    assert 'content-disposition' in (
        download_response.headers
    )


@pytest.mark.parametrize(
    ('filename', 'content', 'content_type'),
    [
        ('text.txt', b'Text file', 'text/plain'),
        ('image.jpg', b'fake-jpeg', 'image/jpeg'),
        ('doc.pdf', b'fake-pdf', 'application/pdf'),
        ('data.json', b'{"k": "v"}', 'application/json'),
        ('script.py', b'print("hi")', 'text/x-python'),
    ],
)
def test_workflow__diff_file_types__ok(
    filename,
    content,
    content_type,
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_upload_use_case_execute,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
):

    # arrange
    mock_response = MagicMock()
    mock_response.file_id = (
        '12345678-1234-5678-1234-567812345678'
    )
    mock_response.public_url = (
        'http://localhost:8000/'
        '12345678-1234-5678-1234-567812345678'
    )
    mock_upload_use_case_execute.return_value = (
        mock_response
    )

    mock_record = MagicMock()
    mock_record.file_id = (
        '12345678-1234-5678-1234-567812345678'
    )
    mock_record.filename = filename
    mock_record.content_type = content_type
    mock_record.size = len(content)
    mock_record.user_id = 1
    mock_record.account_id = 1
    mock_download_use_case_get_metadata.return_value = (
        mock_record
    )
    mock_download_use_case_get_stream.return_value = (
        AsyncIteratorMock(content)
    )

    # act — upload
    upload_response = e2e_client.post(
        '/upload',
        files={
            'file': (filename, content, content_type),
        },
        headers=auth_headers,
    )

    # assert — upload
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    assert 'file_id' in upload_data
    assert 'public_url' in upload_data

    file_id = upload_data['file_id']

    # act — download
    download_response = e2e_client.get(
        f'/{file_id}', headers=auth_headers,
    )

    # assert — download
    assert download_response.status_code == 200
    assert content_type in download_response.headers[
        'content-type'
    ]
    assert 'content-disposition' in (
        download_response.headers
    )
