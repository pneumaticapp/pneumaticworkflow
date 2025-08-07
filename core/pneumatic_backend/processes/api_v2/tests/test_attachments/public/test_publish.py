import pytest
from pneumatic_backend.processes.models import FileAttachment
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template,
    create_test_account,
)
from pneumatic_backend.authentication.tokens import (
    PublicToken,
    EmbedToken,
)
from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.authentication.enums import AuthTokenType
from django.contrib.auth.models import AnonymousUser
from pneumatic_backend.processes.messages.workflow import (
    MSG_PW_0001
)


pytestmark = pytest.mark.django_db


def test_publish__public_token__ok(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        user=user,
        is_active=True,
        is_public=True,
    )
    attachment = FileAttachment.objects.create(
        name='filename.png',
        url='https://some.url',
        size=249128,
        account_id=user.account_id
    )
    auth_header_value = f'Token {template.public_id}'
    token = PublicToken(template.public_id)
    get_token_mock = mocker.patch(
        'pneumatic_backend.authentication.services.public_auth.'
        'PublicAuthService.get_token',
        return_value=token
    )
    get_template_mock = mocker.patch(
        'pneumatic_backend.authentication.services.public_auth.'
        'PublicAuthService.get_template',
        return_value=template
    )

    service_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService.publish'
    )
    ip = 'some ip'
    get_user_ip_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.public.file_attachment.'
        'BaseFileAttachmentViewSet.get_user_ip',
        return_value=ip
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.public.file_attachment'
        '.StoragePermission.has_permission',
        return_value=True
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/workflows/public/attachments/{attachment.id}/publish',
        **{'X-Public-Authorization': auth_header_value},
    )

    # assert

    assert response.status_code == 200
    assert response.data['id'] == attachment.id
    assert response.data['name'] == attachment.name
    assert response.data['url'] == attachment.url
    assert response.data['thumbnail_url'] == attachment.thumbnail_url
    assert response.data['size'] == attachment.size
    get_user_ip_mock.assert_called_once()
    get_token_mock.assert_called_once()
    get_template_mock.assert_called_once_with(token)
    service_mock.assert_called_once_with(
        attachment=attachment,
        request_user=AnonymousUser(),
        auth_type=AuthTokenType.PUBLIC,
        anonymous_id=ip
    )


def test_publish__not_authenticated__permission_denied(
    api_client,
    mocker
):

    # arrange
    get_token_mock = mocker.patch(
        'pneumatic_backend.authentication.services.public_auth.'
        'PublicAuthService.get_token',
        return_value=None
    )
    get_template_mock = mocker.patch(
        'pneumatic_backend.authentication.services.public_auth.'
        'PublicAuthService.get_template'
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.public.file_attachment'
        '.StoragePermission.has_permission',
        return_value=True
    )
    user = create_test_user()
    attachment = FileAttachment.objects.create(
        name='filename.png',
        url='https://file.png',
        thumbnail_url='https://storage.thumb.png',
        size=249128,
        account_id=user.account_id
    )

    # act
    response = api_client.post(
        path=f'/workflows/public/attachments/{attachment.id}/publish',
    )

    # assert
    get_token_mock.assert_called_once()
    get_template_mock.assert_not_called()
    assert response.status_code == 401


def test_publish__embeded_token__ok(
    api_client,
    mocker
):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        is_embedded=True,
    )
    attachment = FileAttachment.objects.create(
        name='filename.png',
        url='https://some.url',
        size=249128,
        account_id=user.account_id
    )
    auth_header_value = f'Token {template.embed_id}'
    token = EmbedToken(template.embed_id)
    get_token_mock = mocker.patch(
        'pneumatic_backend.authentication.services.public_auth.'
        'PublicAuthService.get_token',
        return_value=token
    )
    get_template_mock = mocker.patch(
        'pneumatic_backend.authentication.services.public_auth.'
        'PublicAuthService.get_template',
        return_value=template
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.public.file_attachment'
        '.StoragePermission.has_permission',
        return_value=True
    )
    service_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService.publish'
    )
    ip = 'some ip'
    get_user_ip_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.public.file_attachment.'
        'BaseFileAttachmentViewSet.get_user_ip',
        return_value=ip
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/workflows/public/attachments/{attachment.id}/publish',
        **{'X-Public-Authorization': auth_header_value},
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == attachment.id
    assert response.data['name'] == attachment.name
    assert response.data['url'] == attachment.url
    assert response.data['thumbnail_url'] == attachment.thumbnail_url
    assert response.data['size'] == attachment.size
    get_token_mock.assert_called_once()
    get_template_mock.assert_called_once_with(token)
    get_user_ip_mock.assert_called_once()
    service_mock.assert_called_once_with(
        attachment=attachment,
        request_user=AnonymousUser(),
        auth_type=AuthTokenType.EMBEDDED,
        anonymous_id=ip
    )


def test_publish__disabled_billing__permission_error(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        user=user,
        is_active=True,
        is_public=True,
    )
    attachment = FileAttachment.objects.create(
        name='filename.png',
        url='https://some.url',
        size=249128,
        account_id=user.account_id
    )
    auth_header_value = f'Token {template.public_id}'
    token = PublicToken(template.public_id)
    get_token_mock = mocker.patch(
        'pneumatic_backend.authentication.services.public_auth.'
        'PublicAuthService.get_token',
        return_value=token
    )
    get_template_mock = mocker.patch(
        'pneumatic_backend.authentication.services.public_auth.'
        'PublicAuthService.get_template',
        return_value=template
    )

    service_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService.publish'
    )
    ip = 'some ip'
    get_user_ip_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.public.file_attachment.'
        'BaseFileAttachmentViewSet.get_user_ip',
        return_value=ip
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.public.file_attachment'
        '.StoragePermission.has_permission',
        return_value=False
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/workflows/public/attachments/{attachment.id}/publish',
        **{'X-Public-Authorization': auth_header_value},
    )

    # assert

    assert response.status_code == 403
    assert response.data['detail'] == MSG_PW_0001
    get_user_ip_mock.assert_not_called()
    get_token_mock.assert_called_once()
    get_template_mock.assert_called_once_with(token)
    service_mock.assert_not_called()
