import pytest
from pneumatic_backend.processes.models import FileAttachment
from pneumatic_backend.processes.tests.fixtures import create_test_user
from pneumatic_backend.processes.messages.workflow import (
    MSG_PW_0001
)

pytestmark = pytest.mark.django_db


def test_delete__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    attachment = FileAttachment.objects.create(
        name='filename.png',
        size=24214,
        url='https://link.to.file.png',
        account_id=user.account_id
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.file_attachment'
        '.StoragePermission.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.delete(
        f'/workflows/attachments/{attachment.id}'
    )

    # assert
    assert response.status_code == 204
    assert not FileAttachment.objects.filter(
        id=attachment.id
    ).exists()


def test_delete__no_authenticated__permission_denied(api_client, mocker):

    # arrange
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.file_attachment'
        '.StoragePermission.has_permission',
        return_value=True
    )

    # act
    response = api_client.delete(f'/workflows/attachments/1')

    # assert
    assert response.status_code == 401


def test_delete__disabled_billing__permission_error(api_client, mocker):

    # arrange
    user = create_test_user()
    attachment = FileAttachment.objects.create(
        name='filename.png',
        size=24214,
        url='https://link.to.file.png',
        account_id=user.account_id
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.file_attachment'
        '.StoragePermission.has_permission',
        return_value=False
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.delete(
        f'/workflows/attachments/{attachment.id}'
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_PW_0001
    assert FileAttachment.objects.filter(id=attachment.id).exists()
