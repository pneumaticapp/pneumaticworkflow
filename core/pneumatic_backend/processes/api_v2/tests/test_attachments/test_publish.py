import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
)
from pneumatic_backend.processes.models import FileAttachment
from pneumatic_backend.processes.api_v2.services.exceptions import (
    AttachmentServiceException
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.messages.workflow import (
    MSG_PW_0001
)
from pneumatic_backend.utils.validation import ErrorCode


pytestmark = pytest.mark.django_db


def test_publish__ok(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    attachment = FileAttachment.objects.create(
        name='filename.png',
        url='https://some.url',
        size=249128,
        account_id=user.account_id
    )

    service_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService.publish'
    )
    ip = 'some ip'
    get_user_ip_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.file_attachment.'
        'BaseFileAttachmentViewSet.get_user_ip',
        return_value=ip
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.file_attachment'
        '.StoragePermission.has_permission',
        return_value=True
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/attachments/{attachment.id}/publish'
    )

    assert response.status_code == 200
    assert response.data['id'] == attachment.id
    assert response.data['name'] == attachment.name
    assert response.data['url'] == attachment.url
    assert response.data['thumbnail_url'] == attachment.thumbnail_url
    assert response.data['size'] == attachment.size
    get_user_ip_mock.assert_called_once()
    service_mock.assert_called_once_with(
        attachment=attachment,
        request_user=user,
        auth_type=AuthTokenType.USER,
        anonymous_id=ip
    )


def test_publish__anonymous_id__ok(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    attachment = FileAttachment.objects.create(
        name='filename.png',
        url='https://some.url',
        size=249128,
        account_id=user.account_id
    )
    service_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService.publish'
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.file_attachment'
        '.StoragePermission.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)
    anonymous_id = 'some id'

    # act
    response = api_client.post(
        path=f'/workflows/attachments/{attachment.id}/publish',
        data={'anonymous_id': anonymous_id}
    )

    assert response.status_code == 200
    service_mock.assert_called_once_with(
        attachment=attachment,
        request_user=user,
        auth_type=AuthTokenType.USER,
        anonymous_id=anonymous_id
    )


def test_publish__service_exception__validation_error(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    attachment = FileAttachment.objects.create(
        name='filename.png',
        url='https://some.url',
        size=249128,
        account_id=user.account_id
    )
    message = 'some message'
    service_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService.publish',
        side_effect=AttachmentServiceException(message)
    )
    ip = 'some ip'
    get_user_ip_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.file_attachment.'
        'BaseFileAttachmentViewSet.get_user_ip',
        return_value=ip
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.file_attachment'
        '.StoragePermission.has_permission',
        return_value=True
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/attachments/{attachment.id}/publish'
    )

    assert response.status_code == 400
    assert response.data['message'] == message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    get_user_ip_mock.assert_called_once()
    service_mock.assert_called_once_with(
        attachment=attachment,
        request_user=user,
        auth_type=AuthTokenType.USER,
        anonymous_id=ip
    )


def test_publish__no_authenticated__permission_denied(mocker, api_client):

    # arrange
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.file_attachment'
        '.StoragePermission.has_permission',
        return_value=True
    )

    # act
    response = api_client.post(
        f'/workflows/attachments/1/publish'
    )

    # assert
    assert response.status_code == 401


def test_publish__disabled_billing__permission_error(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    attachment = FileAttachment.objects.create(
        name='filename.png',
        url='https://some.url',
        size=249128,
        account_id=user.account_id
    )

    service_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService.publish'
    )
    ip = 'some ip'
    get_user_ip_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.file_attachment.'
        'BaseFileAttachmentViewSet.get_user_ip',
        return_value=ip
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.file_attachment'
        '.StoragePermission.has_permission',
        return_value=False
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/attachments/{attachment.id}/publish'
    )

    assert response.status_code == 403
    assert response.data['detail'] == MSG_PW_0001
    get_user_ip_mock.assert_not_called()
    service_mock.assert_not_called()
