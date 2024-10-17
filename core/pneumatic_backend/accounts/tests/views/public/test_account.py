import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_template,
)
from pneumatic_backend.accounts.enums import (
    Timezone,
    Language,
    UserDateFormat,
    UserFirstDayWeek,
)
from pneumatic_backend.authentication.tokens import (
    PublicToken,
    EmbedToken,
)


pytestmark = pytest.mark.django_db


class TestPublicAccountViewSet:

    def test_list__ok(self, api_client, mocker):

        # arrange
        account_name = 'West coast company'
        language = Language.es
        tz = Timezone.UTC_8
        date_fdw = UserFirstDayWeek.FRIDAY
        date_fmt = UserDateFormat.PY_EUROPE_24
        logo_lg = 'https://some.logo/image1.png'
        logo_sm = 'https://some.logo/image2.png'

        account = create_test_account(
            name=account_name,
            logo_lg=logo_lg,
            logo_sm=logo_sm,
        )
        account_owner = create_test_user(
            account=account,
            is_account_owner=True,
            language=language,
            tz=tz,
            date_fdw=date_fdw,
            date_fmt=date_fmt
        )
        template = create_test_template(user=account_owner, is_public=True)
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

        # act
        response = api_client.get(
            '/accounts/public/account',
            **{'X-Public-Authorization': auth_header_value},
        )

        # assert
        assert response.status_code == 200
        assert response.data['id'] == account.id
        assert response.data['name'] == account_name
        assert response.data['logo_lg'] == logo_lg
        assert response.data['logo_sm'] == logo_sm
        assert response.data['language'] == language
        assert response.data['timezone'] == tz
        assert response.data['date_fmt'] == date_fmt
        assert response.data['date_fdw'] == date_fdw
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_list__permission_denied(self, api_client, mocker):

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            is_account_owner=True,
        )
        create_test_template(user=account_owner)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=None
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=None
        )

        # act
        response = api_client.get(
            '/accounts/public/account',
            **{'X-Public-Authorization': 'invalid'},
        )

        # assert
        assert response.status_code == 401
        get_token_mock.assert_called_once()
        get_template_mock.assert_not_called()


class TestEmbedAccountVewSet:

    def test_list__ok(self, api_client, mocker):

        # arrange

        # arrange
        account_name = 'West coast company'
        language = Language.es
        tz = Timezone.UTC_8
        date_fdw = UserFirstDayWeek.FRIDAY
        date_fmt = UserDateFormat.PY_EUROPE_24
        logo_lg = 'https://some.logo/image1.png'
        logo_sm = 'https://some.logo/image2.png'

        account = create_test_account(
            name=account_name,
            logo_lg=logo_lg,
            logo_sm=logo_sm,
        )
        account_owner = create_test_user(
            account=account,
            is_account_owner=True,
            language=language,
            tz=tz,
            date_fdw=date_fdw,
            date_fmt=date_fmt
        )
        template = create_test_template(user=account_owner, is_embedded=True)
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

        # act
        response = api_client.get(
            '/accounts/public/account',
            **{'X-Public-Authorization': auth_header_value},
        )

        # assert
        assert response.status_code == 200
        assert response.data['id'] == account.id
        assert response.data['name'] == account_name
        assert response.data['logo_lg'] == logo_lg
        assert response.data['logo_sm'] == logo_sm
        assert response.data['language'] == language
        assert response.data['timezone'] == tz
        assert response.data['date_fmt'] == date_fmt
        assert response.data['date_fdw'] == date_fdw

        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_list__permission_denied(self, api_client, mocker):

        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            is_account_owner=True,
        )
        create_test_template(user=account_owner, is_embedded=True)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=None
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=None
        )

        # act
        response = api_client.get(
            '/accounts/public/account',
            **{'X-Public-Authorization': 'invalid'},
        )

        # assert
        assert response.status_code == 401
        get_token_mock.assert_called_once()
        get_template_mock.assert_not_called()
