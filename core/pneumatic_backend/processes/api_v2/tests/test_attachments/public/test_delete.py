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
from pneumatic_backend.processes.messages.workflow import (
    MSG_PW_0001
)

pytestmark = pytest.mark.django_db


def test_delete__public_token__ok(
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
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.public.file_attachment'
        '.StoragePermission.has_permission',
        return_value=True
    )
    attachment = FileAttachment.objects.create(
        name='filename.png',
        size=24214,
        url='https://link.to.file/filename.png',
        account_id=user.account_id
    )

    # act
    response = api_client.delete(
        path=f'/workflows/public/attachments/{attachment.id}',
        **{'X-Public-Authorization': auth_header_value},
    )

    # assert
    get_token_mock.assert_called_once()
    get_template_mock.assert_called_once_with(token)
    assert response.status_code == 204
    assert not FileAttachment.objects.filter(
        id=attachment.id
    ).exists()


def test_delete__disabled_billing__permission_error(
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
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.public.file_attachment'
        '.StoragePermission.has_permission',
        return_value=False
    )
    attachment = FileAttachment.objects.create(
        name='filename.png',
        size=24214,
        url='https://link.to.file/filename.png',
        account_id=user.account_id
    )

    # act
    response = api_client.delete(
        path=f'/workflows/public/attachments/{attachment.id}',
        **{'X-Public-Authorization': auth_header_value},
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_PW_0001
    get_token_mock.assert_called_once()
    get_template_mock.assert_called_once_with(token)
    assert FileAttachment.objects.filter(id=attachment.id).exists()


def test_delete__no_authenticated__permission_denied(
    mocker,
    api_client
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

    # act
    response = api_client.delete(
        f'/workflows/public/attachments/1'
    )

    # assert
    assert response.status_code == 401
    get_token_mock.assert_called_once()
    get_template_mock.assert_not_called()


def test_delete__embedded_token__ok(api_client, mocker):

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
    attachment = FileAttachment.objects.create(
        name='filename.png',
        size=24214,
        url='https://link.to.file/filename.png',
        account_id=account.id
    )

    # act
    response = api_client.delete(
        path=f'/workflows/public/attachments/{attachment.id}',
        **{'X-Public-Authorization': auth_header_value},
    )

    # assert
    get_token_mock.assert_called_once()
    get_template_mock.assert_called_once_with(token)
    assert response.status_code == 204
    assert not FileAttachment.objects.filter(
        id=attachment.id
    ).exists()
