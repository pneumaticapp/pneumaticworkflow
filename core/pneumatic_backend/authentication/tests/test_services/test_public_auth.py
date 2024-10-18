import pytest
from pneumatic_backend.accounts.tests.fixtures import (
    create_test_user,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_template,
    create_test_account,
)
from pneumatic_backend.authentication.services.public_auth import (
    PublicAuthService
)
from pneumatic_backend.processes.enums import TemplateType
from pneumatic_backend.authentication.tokens import (
    PublicToken,
    EmbedToken,
)
from pneumatic_backend.accounts.enums import BillingPlanType

pytestmark = pytest.mark.django_db


class TestPublicUsersVewSet:

    def test_get_header__from_headers__ok(self, mocker):

        # arrange
        header_value = 'Token AW!2d@'
        request_mock = mocker.Mock(
            headers={'X-Public-Authorization': header_value}
        )

        # act
        result = PublicAuthService._get_header(request_mock)

        # assert
        assert result == header_value

    def test_get_header__from_meta__ok(self, mocker):

        # arrange
        header_value = 'Token AW!2d@'
        request_mock = mocker.Mock(
            META={'X-Public-Authorization': header_value},
            headers={}
        )

        # act
        result = PublicAuthService._get_header(request_mock)

        # assert
        assert result == header_value

    def test_get_token__type_public__ok(self, mocker):

        # arrange
        public_id = 'a' * PublicToken.token_length
        header_value = f'Token {public_id}'
        request_mock = mocker.Mock()
        get_header_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService._get_header',
            return_value=header_value
        )

        # act
        token = PublicAuthService.get_token(request_mock)

        # assert
        assert str(token) == public_id
        assert token.is_public
        get_header_mock.assert_called_once_with(request_mock)

    def test_get_token__type_public_incorrect_len__return_none(self, mocker):

        # arrange
        public_id = 'a' * (PublicToken.token_length + 1)
        header_value = f'Token {public_id}'
        request_mock = mocker.Mock()
        get_header_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService._get_header',
            return_value=header_value
        )

        # act
        token = PublicAuthService.get_token(request_mock)

        # assert
        assert token is None
        get_header_mock.assert_called_once_with(request_mock)

    def test_get_token__type_embed__ok(self, mocker):

        # arrange
        embed_id = 'a' * EmbedToken.token_length
        header_value = f'Token {embed_id}'
        request_mock = mocker.Mock()
        get_header_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService._get_header',
            return_value=header_value
        )

        # act
        token = PublicAuthService.get_token(request_mock)

        # assert
        assert str(token) == embed_id
        assert token.is_embedded
        get_header_mock.assert_called_once_with(request_mock)

    def test_get_token__type_embed_incorrect_len__return_none(self, mocker):

        # arrange
        embed_id = 'a' * (EmbedToken.token_length + 1)
        header_value = f'Token {embed_id}'
        request_mock = mocker.Mock()
        get_header_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService._get_header',
            return_value=header_value
        )

        # act
        token = PublicAuthService.get_token(request_mock)

        # assert
        assert token is None
        get_header_mock.assert_called_once_with(request_mock)

    def test_get_token__skipped_header__return_none(self, mocker):

        # arrange
        request_mock = mocker.Mock()
        get_header_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService._get_header',
            return_value=None
        )

        # act
        result = PublicAuthService.get_token(request_mock)

        # assert
        assert result is None
        get_header_mock.assert_called_once_with(request_mock)

    def test_get_token__invalid_header_format__return_none(self, mocker):

        # arrange
        public_id = 'a' * PublicToken.token_length
        request_mock = mocker.Mock()
        get_header_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService._get_header',
            return_value=public_id
        )

        # act
        result = PublicAuthService.get_token(request_mock)

        # assert
        assert result is None
        get_header_mock.assert_called_once_with(request_mock)

    def test_get_token__invalid_header_prefix__return_none(self, mocker):

        # arrange
        public_id = 'a' * PublicToken.token_length
        header_value = f'Bearer {public_id}'
        request_mock = mocker.Mock()
        get_header_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService._get_header',
            return_value=header_value
        )

        # act
        result = PublicAuthService.get_token(request_mock)

        # assert
        assert result is None
        get_header_mock.assert_called_once_with(request_mock)

    def test_get_header__not_found__return_none(self, mocker):

        # arrange
        request_mock = mocker.Mock(headers={}, META={})

        # act
        result = PublicAuthService._get_header(request_mock)

        # assert
        assert result is None

    def test_get_template__public_template__ok(self):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True
        )
        token = PublicToken(template.public_id)

        # act
        result = PublicAuthService.get_template(token)

        # assert
        assert result.id == template.id

    def test_get_template__embed_template__ok(self):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            is_embedded=True
        )
        token = EmbedToken(template.embed_id)

        # act
        result = PublicAuthService.get_template(token)

        # assert
        assert result.embed_id == template.embed_id

    def test_get_template__draft__not_found(self):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=False,
            is_public=True
        )
        token = PublicToken(template.public_id)

        # act
        result = PublicAuthService.get_template(token)

        # assert
        assert result is None

    def test_get_template__not_public__not_found(self, mocker):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=False
        )
        token = PublicToken(template.public_id)

        # act
        result = PublicAuthService.get_template(token)

        # assert
        assert result is None

    def test_get_template__non_existent_public_id__not_found(
        self,
    ):
        # arrange
        user = create_test_user()
        create_test_template(
            user=user,
            is_active=True,
            is_public=True
        )
        token = PublicToken()

        # act
        result = PublicAuthService.get_template(token)

        # assert
        assert result is None

    def test_get_template__onboarding__not_found(self):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1,
            type_=TemplateType.ONBOARDING_ACCOUNT_OWNER
        )
        token = PublicToken(template.public_id)

        # act
        result = PublicAuthService.get_template(token)

        # assert
        assert result is None
