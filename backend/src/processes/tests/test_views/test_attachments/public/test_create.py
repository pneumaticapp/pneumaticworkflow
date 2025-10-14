import pytest

from src.accounts.enums import BillingPlanType
from src.authentication.tokens import (
    EmbedToken,
    PublicToken,
)
from src.processes.messages.workflow import (
    MSG_PW_0001,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_template,
    create_test_user,
)

pytestmark = pytest.mark.django_db


def test_create__public_token__ok(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        user=user,
        is_active=True,
        is_public=True,
    )
    auth_header_value = f'Token {template.public_id}'
    token = PublicToken(template.public_id)
    get_token_mock = mocker.patch(
        'src.authentication.services.public_auth.'
        'PublicAuthService.get_token',
        return_value=token,
    )
    get_template_mock = mocker.patch(
        'src.authentication.services.public_auth.'
        'PublicAuthService.get_template',
        return_value=template,
    )
    mocker.patch(
        'src.processes.views.public.file_attachment'
        '.StoragePermission.has_permission',
        return_value=True,
    )
    attachment = mocker.Mock(id=1)
    upload_url = 'some upload url'
    thumb_upload_url = 'some thumb upload url'
    filename = 'image.png'
    thumbnail = True
    content_type = 'image/png'
    size = 215678

    service_mock = mocker.patch(
        'src.processes.services.attachments.'
        'AttachmentService.create',
        return_value=(
            attachment,
            upload_url,
            thumb_upload_url,
        ),
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/workflows/public/attachments',
        data={
            'filename': filename,
            'thumbnail': thumbnail,
            'content_type': content_type,
            'size': size,
        },
        **{'X-Public-Authorization': auth_header_value},
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == attachment.id
    assert response.data['file_upload_url'] == upload_url
    assert response.data['thumbnail_upload_url'] == thumb_upload_url
    service_mock.assert_called_once_with(
        filename=filename,
        thumbnail=thumbnail,
        content_type=content_type,
        size=size,
    )
    get_token_mock.assert_called_once()
    get_template_mock.assert_called_once_with(token)


def test_create__not_authenticated__permission_denied(
    api_client,
    mocker,
):

    # arrange
    get_token_mock = mocker.patch(
        'src.authentication.services.public_auth.'
        'PublicAuthService.get_token',
        return_value=None,
    )
    get_template_mock = mocker.patch(
        'src.authentication.services.public_auth.'
        'PublicAuthService.get_template',
    )
    mocker.patch(
        'src.processes.views.public.file_attachment'
        '.StoragePermission.has_permission',
        return_value=True,
    )

    # act
    response = api_client.post(
        path='/workflows/public/attachments',
        data={
            'filename': 'mark_dacascas.png',
            'thumbnail': 'mark_dacascas_th.png',
            'content_type': 'image/png',
            'size': 215678,
        },
    )

    # assert
    assert response.status_code == 401
    get_token_mock.assert_called_once()
    get_template_mock.assert_not_called()


def test_create__embeded_token__ok(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        is_embedded=True,
    )
    auth_header_value = f'Token {template.embed_id}'
    token = EmbedToken(template.embed_id)
    get_token_mock = mocker.patch(
        'src.authentication.services.public_auth.'
        'PublicAuthService.get_token',
        return_value=token,
    )
    get_template_mock = mocker.patch(
        'src.authentication.services.public_auth.'
        'PublicAuthService.get_template',
        return_value=template,
    )
    mocker.patch(
        'src.processes.views.public.file_attachment'
        '.StoragePermission.has_permission',
        return_value=True,
    )
    attachment = mocker.Mock(id=1)
    upload_url = 'some upload url'
    thumb_upload_url = 'some thumb upload url'
    filename = 'image.png'
    thumbnail = True
    content_type = 'image/png'
    size = 215678

    service_mock = mocker.patch(
        'src.processes.services.attachments.'
        'AttachmentService.create',
        return_value=(
            attachment,
            upload_url,
            thumb_upload_url,
        ),
    )

    # act
    response = api_client.post(
        path='/workflows/public/attachments',
        data={
            'filename': filename,
            'thumbnail': thumbnail,
            'content_type': content_type,
            'size': size,
        },
        **{'X-Public-Authorization': auth_header_value},
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == attachment.id
    assert response.data['file_upload_url'] == upload_url
    assert response.data['thumbnail_upload_url'] == thumb_upload_url
    service_mock.assert_called_once_with(
        filename=filename,
        thumbnail=thumbnail,
        content_type=content_type,
        size=size,
    )
    get_token_mock.assert_called_once()
    get_template_mock.assert_called_once_with(token)


def test_create__disabled_billing__permission_error(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        user=user,
        is_active=True,
        is_public=True,
    )
    auth_header_value = f'Token {template.public_id}'
    token = PublicToken(template.public_id)
    get_token_mock = mocker.patch(
        'src.authentication.services.public_auth.'
        'PublicAuthService.get_token',
        return_value=token,
    )
    get_template_mock = mocker.patch(
        'src.authentication.services.public_auth.'
        'PublicAuthService.get_template',
        return_value=template,
    )
    mocker.patch(
        'src.processes.views.public.file_attachment'
        '.StoragePermission.has_permission',
        return_value=False,
    )
    attachment = mocker.Mock(id=1)
    upload_url = 'some upload url'
    thumb_upload_url = 'some thumb upload url'
    filename = 'image.png'
    thumbnail = True
    content_type = 'image/png'
    size = 215678

    service_mock = mocker.patch(
        'src.processes.services.attachments.'
        'AttachmentService.create',
        return_value=(
            attachment,
            upload_url,
            thumb_upload_url,
        ),
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/workflows/public/attachments',
        data={
            'filename': filename,
            'thumbnail': thumbnail,
            'content_type': content_type,
            'size': size,
        },
        **{'X-Public-Authorization': auth_header_value},
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_PW_0001
    service_mock.assert_not_called()
    get_token_mock.assert_called_once()
    get_template_mock.assert_called_once_with(token)
