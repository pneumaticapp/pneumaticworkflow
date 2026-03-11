import pytest

from src.accounts.enums import UserStatus
from src.authentication.tokens import (
    EmbedToken,
    PublicToken,
)
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_account,
    create_test_guest,
    create_test_template,
    create_test_owner, create_test_admin,
)

pytestmark = pytest.mark.django_db


class TestPublicUsersVewSet:

    def test_list__only_active_users__ok(self, api_client, mocker):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        create_test_admin(
            account=account,
            status=UserStatus.INACTIVE,
        )
        create_test_guest(account=account)
        template = create_test_template(user=owner, is_public=True)
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

        # act
        response = api_client.get(
            '/accounts/public/users?ordering=status',
            **{'X-Public-Authorization': auth_header_value},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == owner.id
        assert response.data[0]['email'] == owner.email
        assert response.data[0]['status'] == UserStatus.ACTIVE
        assert response.data[0]['first_name'] == owner.first_name
        assert response.data[0]['last_name'] == owner.last_name

        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_list__ordering_status__ok(self, api_client, mocker):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        invited_user = create_invited_user(owner)
        template = create_test_template(user=owner, is_public=True)
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

        # act
        response = api_client.get(
            '/accounts/public/users?ordering=status',
            **{'X-Public-Authorization': auth_header_value},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['id'] == owner.id
        assert response.data[1]['id'] == invited_user.id
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_list__ordering_last_name__ok(self, api_client, mocker):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account, last_name='z')
        user = create_test_admin(account=account, last_name='a')
        template = create_test_template(user=owner, is_public=True)
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

        # act
        response = api_client.get(
            '/accounts/public/users?ordering=last_name',
            **{'X-Public-Authorization': auth_header_value},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['id'] == user.id
        assert response.data[1]['id'] == owner.id

        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_list__ordering_first_name__ok(self, api_client, mocker):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account, last_name='z')
        user = create_test_admin(account=account, last_name='a')
        template = create_test_template(user=owner, is_public=True)
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

        # act
        response = api_client.get(
            '/accounts/public/users?ordering=last_name',
            **{'X-Public-Authorization': auth_header_value},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['id'] == user.id
        assert response.data[1]['id'] == owner.id
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_list__permission_denied(self, api_client, mocker):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        create_test_template(user=owner)
        get_token_mock = mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=None,
        )
        get_template_mock = mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=None,
        )

        # act
        response = api_client.get(
            '/accounts/public/users',
            **{'X-Public-Authorization': 'invalid'},
        )

        # assert
        assert response.status_code == 401
        get_token_mock.assert_called_once()
        get_template_mock.assert_not_called()


class TestEmbedUsersVewSet:

    def test_list__only_active_users__ok(self, api_client, mocker):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        create_test_admin(
            account=account,
            status=UserStatus.INACTIVE,
        )
        create_test_guest(account=account)
        template = create_test_template(user=owner, is_embedded=True)
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

        # act
        response = api_client.get(
            '/accounts/public/users?ordering=status',
            **{'X-Public-Authorization': auth_header_value},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == owner.id
        assert response.data[0]['email'] == owner.email
        assert response.data[0]['status'] == UserStatus.ACTIVE
        assert response.data[0]['first_name'] == owner.first_name
        assert response.data[0]['last_name'] == owner.last_name

        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_list__ordering_status__ok(self, api_client, mocker):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        invited_user = create_invited_user(owner)
        create_test_admin(
            account=account,
            status=UserStatus.INACTIVE,
        )
        create_test_guest(account=account)
        template = create_test_template(user=owner, is_embedded=True)
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

        # act
        response = api_client.get(
            '/accounts/public/users?ordering=status',
            **{'X-Public-Authorization': auth_header_value},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['id'] == owner.id
        assert response.data[1]['id'] == invited_user.id
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)
