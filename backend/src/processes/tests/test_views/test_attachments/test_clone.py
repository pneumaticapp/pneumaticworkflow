import pytest

from src.processes.models.workflows.attachment import FileAttachment
from src.processes.tests.fixtures import (
    create_test_user,
)

pytestmark = pytest.mark.django_db


def test_clone__ok(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    attachment = FileAttachment.objects.create(
        account=user.account,
        name='filename',
        url='https://link.to/filename',
        size=100,
    )
    clone_attachment = mocker.Mock(id=1)
    service_mock = mocker.patch(
        'src.processes.services.attachments.'
        'AttachmentService.create_clone',
        return_value=clone_attachment,
    )
    mocker.patch(
        'src.processes.views.file_attachment'
        '.StoragePermission.has_permission',
        return_value=True,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/attachments/{attachment.id}/clone',
    )

    assert response.status_code == 200
    assert response.data['id'] == clone_attachment.id
    service_mock.assert_called_once_with(attachment)


def test_clone__not_exists__not_found(mocker, api_client):

    # arrange
    user = create_test_user()
    mocker.patch(
        'src.processes.views.file_attachment'
        '.StoragePermission.has_permission',
        return_value=True,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/workflows/attachments/9999/clone',
    )

    # assert
    assert response.status_code == 404


def test_create__no_authenticated__permission_denied(
    mocker,
    api_client,
):
    mocker.patch(
        'src.processes.views.file_attachment'
        '.StoragePermission.has_permission',
        return_value=True,
    )

    # act
    response = api_client.post('/workflows/attachments/1/clone')

    # assert
    assert response.status_code == 401


def test_clone__disable_storage__permission_denied(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    attachment = FileAttachment.objects.create(
        account=user.account,
        name='filename',
        url='https://link.to/filename',
        size=100,
    )
    service_mock = mocker.patch(
        'src.processes.services.attachments.'
        'AttachmentService.create_clone',
    )
    mocker.patch(
        'src.processes.views.file_attachment'
        '.StoragePermission.has_permission',
        return_value=False,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/attachments/{attachment.id}/clone',
    )

    assert response.status_code == 403
    service_mock.assert_not_called()
