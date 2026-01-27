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
    create_test_user,
)

pytestmark = pytest.mark.django_db


class TestPublicUsersVewSet:

    def test_list__ok(self, api_client, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account, last_name='z')
        invited_user = create_invited_user(user, last_name='y')
        create_test_user(
            account=account,
            email='inactive@test.test',
            status=UserStatus.INACTIVE,
        )
        create_test_guest(account=account)
        template = create_test_template(user=user, is_public=True)
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
            '/accounts/public/users',
            **{'X-Public-Authorization': auth_header_value},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['id'] == user.id
        assert response.data[0]['email'] == user.email
        assert response.data[0]['status'] == UserStatus.ACTIVE
        assert response.data[0]['first_name'] == user.first_name
        assert response.data[0]['last_name'] == user.last_name

        assert response.data[1]['id'] == invited_user.id
        assert response.data[1]['email'] == invited_user.email
        assert response.data[1]['status'] == UserStatus.INVITED
        assert response.data[1]['first_name'] == invited_user.first_name
        assert response.data[1]['last_name'] == invited_user.last_name
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_list__permission_denied(self, api_client, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        create_test_template(user=user)
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

    def test_list__ok(self, api_client, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        invited_user = create_invited_user(user)
        create_test_user(
            account=account,
            email='inactive@test.test',
            status=UserStatus.INACTIVE,
        )
        create_test_guest(account=account)
        template = create_test_template(user=user, is_embedded=True)
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
            '/accounts/public/users',
            **{'X-Public-Authorization': auth_header_value},
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['id'] == user.id
        assert response.data[0]['email'] == user.email
        assert response.data[0]['status'] == UserStatus.ACTIVE
        assert response.data[0]['first_name'] == user.first_name
        assert response.data[0]['last_name'] == user.last_name
        assert response.data[1]['id'] == invited_user.id
        assert response.data[1]['email'] == invited_user.email
        assert response.data[1]['status'] == UserStatus.INVITED
        assert response.data[1]['first_name'] == invited_user.first_name
        assert response.data[1]['last_name'] == invited_user.last_name

        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)
