import pytest
from pneumatic_backend.processes.messages import workflow as messages
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
)
from pneumatic_backend.processes.api_v2.services.exceptions import (
    AttachmentServiceException
)
from pneumatic_backend.processes.messages.workflow import (
    MSG_PW_0001
)
from pneumatic_backend.utils.validation import ErrorCode


pytestmark = pytest.mark.django_db


def test_create__ok(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    attachment = mocker.Mock(id=1)
    upload_url = 'some upload url'
    thumb_upload_url = 'some thumb upload url'
    filename = 'image.png'
    thumbnail = True
    content_type = 'image/png'
    size = 215678
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.file_attachment'
        '.StoragePermission.has_permission',
        return_value=True
    )
    service_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService.create',
        return_value=(
            attachment,
            upload_url,
            thumb_upload_url
        )
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/workflows/attachments',
        data={
            'filename': filename,
            'thumbnail': thumbnail,
            'content_type': content_type,
            'size': size
        }
    )

    assert response.status_code == 200
    assert response.data['id'] == attachment.id
    assert response.data['file_upload_url'] == upload_url
    assert response.data['thumbnail_upload_url'] == thumb_upload_url
    service_mock.assert_called_once_with(
        account_id=user.account_id,
        filename=filename,
        thumbnail=thumbnail,
        content_type=content_type,
        size=size
    )


def test_create__limit_exceeded__validation_error(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    filename = 'image.png'
    thumbnail = True
    content_type = 'image/png'
    size = 1024*1024
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.file_attachment'
        '.StoragePermission.has_permission',
        return_value=True
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.serializers.'
        'file_attachment.ATTACHMENT_MAX_SIZE_BYTES',
        size
    )
    service_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService.create'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/workflows/attachments',
        data={
            'filename': filename,
            'thumbnail': thumbnail,
            'content_type': content_type,
            'size': size + 1
        }
    )

    assert response.status_code == 400
    message = messages.MSG_PW_0050(size)
    assert response.data['message'] == message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'size'
    service_mock.assert_not_called()


def test_create__service_exception__validation_error(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    filename = 'image.png'
    thumbnail = True
    content_type = 'image/png'
    size = 100
    message = 'some message'
    service_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService.create',
        side_effect=AttachmentServiceException(message)
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.file_attachment'
        '.StoragePermission.has_permission',
        return_value=True
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/workflows/attachments',
        data={
            'filename': filename,
            'thumbnail': thumbnail,
            'content_type': content_type,
            'size': size
        }
    )

    assert response.status_code == 400
    assert response.data['message'] == message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    service_mock.assert_called_once_with(
        account_id=user.account_id,
        filename=filename,
        thumbnail=thumbnail,
        content_type=content_type,
        size=size
    )


def test_create__no_authenticated__permission_denied(mocker, api_client):

    # arrange
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.file_attachment'
        '.StoragePermission.has_permission',
        return_value=True
    )

    # act
    response = api_client.post(
        path='/workflows/attachments',
        data={
            'filename': 'mark_dacascas.png',
            'thumbnail': 'mark_dacascas_th.png',
            'content_type': 'image/png',
            'size': 215678
        }
    )

    # assert
    assert response.status_code == 401


def test_create__disabled_billing__permission_error(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    attachment = mocker.Mock(id=1)
    upload_url = 'some upload url'
    thumb_upload_url = 'some thumb upload url'
    filename = 'image.png'
    thumbnail = True
    content_type = 'image/png'
    size = 215678
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.file_attachment'
        '.StoragePermission.has_permission',
        return_value=False
    )
    service_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService.create',
        return_value=(
            attachment,
            upload_url,
            thumb_upload_url
        )
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/workflows/attachments',
        data={
            'filename': filename,
            'thumbnail': thumbnail,
            'content_type': content_type,
            'size': size
        }
    )

    assert response.status_code == 403
    assert response.data['detail'] == MSG_PW_0001
    service_mock.assert_not_called()
