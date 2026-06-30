import pytest
from guardian.shortcuts import assign_perm

from src.authentication.tokens import PublicToken
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_attachment,
    create_test_template,
)
from src.storage.enums import AccessType, SourceType
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


class TestCheckPermissionView:

    def test_check_permission__has_permission__ok(self, api_client):
        # arrange
        user = create_test_admin()
        api_client.token_authenticate(user)

        attachment = create_test_attachment(
            user.account,
            file_id='test_file_123',
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.ACCOUNT,
        )
        assign_perm('storage.access_attachment', user, attachment)

        # act
        response = api_client.post(
            '/attachments/check-permission',
            data={
                'file_id': 'test_file_123',
            },
        )

        # assert
        assert response.status_code == 204
        assert response.data is None

    def test_check_permission__no_permission__forbidden(self, api_client):
        # arrange
        user = create_test_admin()
        api_client.token_authenticate(user)

        create_test_attachment(
            user.account,
            file_id='test_file_123',
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.ACCOUNT,
        )

        # act
        response = api_client.post(
            '/attachments/check-permission',
            data={
                'file_id': 'test_file_123',
            },
        )

        # assert
        assert response.status_code == 403

    def test_check_permission__invalid_data__bad_request(
        self,
        api_client,
    ):
        # arrange
        user = create_test_admin()
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            '/attachments/check-permission',
            data={
                'file_id': '',
            },
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR

    def test_check_permission__missing_file_id__bad_request(
        self,
        api_client,
    ):
        # arrange
        user = create_test_admin()
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            '/attachments/check-permission',
            data={},
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR

    def test_check_permission__not_authenticated__unauthorized(
        self,
        api_client,
    ):

        # act
        response = api_client.post(
            '/attachments/check-permission',
            data={
                'file_id': 'test_file_123',
            },
        )

        # assert
        assert response.status_code == 401

    def test_check_permission__file_id_with_spaces__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_admin()
        api_client.token_authenticate(user)

        attachment = create_test_attachment(
            user.account,
            file_id='test_file_123',
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.ACCOUNT,
        )
        assign_perm(
            'storage.access_attachment',
            user,
            attachment,
        )

        # act
        response = api_client.post(
            '/attachments/check-permission',
            data={
                'file_id': '  test_file_123  ',
            },
        )

        # assert
        assert response.status_code == 204
        assert response.data is None

    def test_check_permission__file_not_found__forbidden(
        self,
        api_client,
    ):
        # arrange
        user = create_test_admin()
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            '/attachments/check-permission',
            data={
                'file_id': 'nonexistent_file',
            },
        )

        # assert
        assert response.status_code == 403

    def test_check_permission__public_access__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_admin()
        api_client.token_authenticate(user)

        create_test_attachment(
            account=user.account,
            file_id='public_file',
            access_type=AccessType.PUBLIC,
            source_type=SourceType.ACCOUNT,
        )

        # act
        response = api_client.post(
            '/attachments/check-permission',
            data={
                'file_id': 'public_file',
            },
        )

        # assert
        assert response.status_code == 204
        assert response.data is None

    def test_check_permission__account_access__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_admin()
        api_client.token_authenticate(user)

        create_test_attachment(
            account=user.account,
            file_id='account_file',
            access_type=AccessType.ACCOUNT,
            source_type=SourceType.ACCOUNT,
        )

        # act
        response = api_client.post(
            '/attachments/check-permission',
            data={
                'file_id': 'account_file',
            },
        )

        # assert
        assert response.status_code == 204
        assert response.data is None

    def test_check_permission__account_access_other__forbidden(
        self,
        api_client,
    ):
        # arrange
        user = create_test_admin()
        api_client.token_authenticate(user)

        other_account = create_test_account(name='Other')
        create_test_attachment(
            account=other_account,
            file_id='other_account_file',
            access_type=AccessType.ACCOUNT,
            source_type=SourceType.ACCOUNT,
        )

        # act
        response = api_client.post(
            '/attachments/check-permission',
            data={
                'file_id': 'other_account_file',
            },
        )

        # assert
        assert response.status_code == 403

    def test_check_permission__public_template__ok(
        self,
        api_client,
        mocker,
    ):
        # arrange
        user = create_test_admin()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
        )
        attachment = create_test_attachment(
            account=user.account,
            file_id='test_file_public',
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TEMPLATE,
            template=template,
        )
        auth_header_value = (
            f'Token {template.public_id}'
        )
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

        # act
        response = api_client.post(
            '/attachments/check-permission',
            data={'file_id': attachment.file_id},
            **{
                'HTTP_X_PUBLIC_AUTHORIZATION':
                    auth_header_value,
            },
        )

        # assert
        assert response.status_code == 204
        assert response.data is None
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_check_permission__public_tmpl_no_access__forbidden(
        self,
        api_client,
        mocker,
    ):
        # arrange
        user = create_test_admin()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
        )
        other_template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
        )
        attachment = create_test_attachment(
            account=user.account,
            file_id='test_file_public_other',
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TEMPLATE,
            template=other_template,
        )
        auth_header_value = (
            f'Token {template.public_id}'
        )
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

        # act
        response = api_client.post(
            '/attachments/check-permission',
            data={'file_id': attachment.file_id},
            **{
                'HTTP_X_PUBLIC_AUTHORIZATION':
                    auth_header_value,
            },
        )

        # assert
        assert response.status_code == 403
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)
