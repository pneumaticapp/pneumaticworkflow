import src.storage.messages as fs_messages
import pytest
from pytest_django.fixtures import SettingsWrapper
from rest_framework.exceptions import ValidationError

from src.mcp import messages
from src.mcp.serializers.uploads import UploadSerializer


@pytest.mark.parametrize('size', [1, 5])
def test_upload_serializer__size_boundary_default_target__valid(
    mcp_settings: SettingsWrapper,
    size: int,
):

    # arrange
    mcp_settings.MCP_MAX_IMPORT_BYTES = 5
    serializer = UploadSerializer(
        data={
            'task_id': 1,
            'field_api_name': 'file',
            'filename': 'test.txt',
            'size': size,
            'content_type': 'text/plain',
        },
    )

    # act
    valid = serializer.is_valid(raise_exception=True)

    # assert
    assert valid is True
    assert serializer.validated_data['size'] == size
    assert serializer.validated_data['target_type'] == 'task'


def test_upload_serializer__oversize__message_constant(
    mcp_settings: SettingsWrapper,
):

    # arrange
    mcp_settings.MCP_MAX_IMPORT_BYTES = 5
    serializer = UploadSerializer(
        data={
            'task_id': 1,
            'field_api_name': 'file',
            'filename': 'test.txt',
            'size': 6,
            'content_type': 'text/plain',
        },
    )

    # act
    with pytest.raises(ValidationError) as error:
        serializer.is_valid(raise_exception=True)

    # assert
    assert error.value.detail == {
        'message': fs_messages.MSG_FS_0014,
        'code': 'validation_error',
        'details': {'name': 'size', 'reason': fs_messages.MSG_FS_0014},
    }


@pytest.mark.parametrize('task_ids', [{}, {'task_id': 1, 'template_id': 1}])
def test_upload_serializer__ambiguous_target__message_constant(task_ids: dict):

    # arrange
    serializer = UploadSerializer(
        data={
            **task_ids,
            'field_api_name': 'file',
            'filename': 'test.txt',
            'size': 3,
            'content_type': 'text/plain',
        },
    )

    # act
    with pytest.raises(ValidationError) as error:
        serializer.is_valid(raise_exception=True)

    # assert
    assert error.value.detail == {
        'message': messages.MSG_MCP_0002,
        'code': 'validation_error',
    }


@pytest.mark.parametrize(
    'mime,expected',
    [
        ('text/html', 'application/octet-stream'),
        ('image/svg+xml', 'application/octet-stream'),
        ('application/unknown', 'application/octet-stream'),
        ('TEXT/PLAIN', 'text/plain'),
    ],
)
def test_upload_metadata__same_as_storage__canonical(mime: str, expected: str):
    # arrange
    serializer = UploadSerializer(
        data={
            'target_type': 'task',
            'task_id': 123,
            'field_api_name': 'file',
            'filename': 'мой report.txt',
            'size': 3,
            'content_type': mime,
        },
    )

    # act
    valid = serializer.is_valid()

    # assert
    assert valid is True, serializer.errors
    assert serializer.validated_data['filename'] == 'мой_report.txt'
    assert serializer.validated_data['content_type'] == expected


@pytest.mark.parametrize(
    'filename,expected',
    [
        ('my report.pdf', 'my_report.pdf'),
        ('.hidden.txt', 'hidden.txt'),
        ('мой отчёт.txt', 'мой_отчёт.txt'),
        ('report!@#$.txt', 'report_.txt'),
        ('report.pdf ', 'report.pdf_'),
    ],
)
def test_upload_filename__storage_algorithm__same_canonical(
    filename: str,
    expected: str,
):

    # arrange
    serializer = UploadSerializer(
        data={
            'target_type': 'task',
            'task_id': 123,
            'field_api_name': 'file',
            'filename': filename,
            'size': 3,
            'content_type': 'text/plain',
        },
    )

    # act
    valid = serializer.is_valid()

    # assert
    assert valid is True, serializer.errors
    assert serializer.validated_data['filename'] == expected
