import pytest
from pneumatic_backend.accounts.models import User, UserInvite
from pneumatic_backend.accounts.tokens import (
    AuthToken,
)
from pneumatic_backend.accounts.enums import (
    UserInviteStatus,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_invited_user,
)
from pneumatic_backend.accounts.enums import SourceType
from pneumatic_backend.accounts.services.user import UserService
from pneumatic_backend.authentication.enums import AuthTokenType


pytestmark = pytest.mark.django_db


class TestSignInWithGoogleView:

    def test_create__ok(
        self,
        mocker,
        api_client,
        identify_mock,
    ):
        # arrange
        user = create_test_user()
        UserInvite.objects.create(
            email=user.email,
            account=user.account,
            invited_user=user,
        )
        mocker.patch(
            'pneumatic_backend.authentication.views.google.'
            'GoogleAuthPermission.has_permission',
            return_value=True
        )
        analytics_mock = mocker.patch(
            'pneumatic_backend.authentication.views.signin.'
            'AnalyticService.users_logged_in'
        )

        # act
        response = api_client.post(
            '/auth/signin-google',
            data={'email': user.email}
        )

        # assert
        user = User.objects.get(pk=user.pk)
        assert response.status_code == 200
        assert response.data['token']
        assert user.invite.status == UserInviteStatus.ACCEPTED
        analytics_mock.assert_called_once_with(
            user=user,
            auth_type=AuthTokenType.USER,
            source=SourceType.GOOGLE,
            is_superuser=False
        )
        identify_mock.assert_called_once_with(user)

    def test_create__disable_google_auth__auth_error(
        self,
        mocker,
        api_client,
        identify_mock,
    ):
        # arrange
        user = create_test_user()
        UserInvite.objects.create(
            email=user.email,
            account=user.account,
            invited_user=user,
        )
        mocker.patch(
            'pneumatic_backend.authentication.views.google.'
            'GoogleAuthPermission.has_permission',
            return_value=False
        )
        analytics_mock = mocker.patch(
            'pneumatic_backend.authentication.views.signin.'
            'AnalyticService.users_logged_in'
        )

        # act
        response = api_client.post(
            '/auth/signin-google',
            data={'email': user.email}
        )

        # assert
        assert response.status_code == 401
        analytics_mock.assert_not_called()
        identify_mock.assert_not_called()

    def test_create__invited_and_active_user__ok(
        self,
        api_client,
        mocker,
        identify_mock,
    ):
        # arrange
        user = create_test_user()
        another_account_owner = create_test_user(email='ao@t.t')
        create_invited_user(
            user=another_account_owner,
            email=user.email
        )
        mocker.patch(
            'pneumatic_backend.authentication.views.google.'
            'GoogleAuthPermission.has_permission',
            return_value=True
        )
        analytics_mock = mocker.patch(
            'pneumatic_backend.authentication.views.signin.'
            'AnalyticService.users_logged_in'
        )

        # act
        response = api_client.post(
            '/auth/signin-google',
            data={'email': user.email}
        )

        # assert
        assert response.status_code == 200
        assert response.data['token']
        analytics_mock.assert_called_once_with(
            user=user,
            auth_type=AuthTokenType.USER,
            source=SourceType.GOOGLE,
            is_superuser=False
        )


class TestGoogleAuthViewSet:

    def test_create__ok(self, api_client, mocker):
        # arrange
        data = {
            'email': 'test@pneumatic.app'
        }
        mocker.patch(
            'pneumatic_backend.authentication.views.google.'
            'GoogleAuthPermission.has_permission',
            return_value=True
        )

        # act
        response = api_client.post('/auth/google', data)
        token_data = AuthToken(response.data['token'])

        assert response.status_code == 200
        assert token_data['email'] == data['email']

    def test_create__disable_google_auth__auth_error(
        self,
        api_client,
        mocker
    ):
        # arrange
        data = {
            'email': 'test@pneumatic.app'
        }
        mocker.patch(
            'pneumatic_backend.authentication.views.google.'
            'GoogleAuthPermission.has_permission',
            return_value=False
        )

        # act
        response = api_client.post('/auth/google', data)

        # assert
        assert response.status_code == 401

    def test_list__user_does_not_exist__not_response_token(
        self,
        mocker,
        api_client,
        identify_mock,
        group_mock,
    ):
        # arrange
        email = 'test@pneumatic.app'
        jwt_token = str(AuthToken.for_auth_data(email=email))
        mocker.patch(
            'pneumatic_backend.authentication.views.google.'
            'GoogleAuthPermission.has_permission',
            return_value=True
        )

        # act
        response = api_client.get(f'/auth/google?token={jwt_token}')

        # assert
        assert response.status_code == 200
        assert response.data['email'] == email
        identify_mock.assert_not_called()
        group_mock.assert_not_called()

    def test_list__user__ok(
        self,
        api_client,
        identify_mock,
        mocker,
    ):
        # arrange
        user = create_test_user()
        jwt_token = str(AuthToken.for_auth_data(email=user.email))
        group_mock = mocker.patch(
            'pneumatic_backend.analytics.mixins.BaseIdentifyMixin.group'
        )
        mocker.patch(
            'pneumatic_backend.authentication.views.google.'
            'GoogleAuthPermission.has_permission',
            return_value=True
        )

        # act
        response = api_client.get(f'/auth/google?token={jwt_token}')

        # assert
        assert response.status_code == 200
        assert response.data['token']
        identify_mock.assert_called_once()
        group_mock.assert_called_once_with(user)

    def test_list__inactive_user__not_token(self, api_client, mocker):

        # arrange
        user = create_test_user()
        UserService.deactivate(user)
        jwt_token = str(AuthToken.for_auth_data(email=user.email))
        mocker.patch(
            'pneumatic_backend.authentication.views.google.'
            'GoogleAuthPermission.has_permission',
            return_value=True
        )

        # act
        response = api_client.get(f'/auth/google?token={jwt_token}')

        # assert
        assert response.status_code == 200
        assert 'token' not in response.data

    def test_list__invited_user_and_active__return_active(
        self,
        api_client,
        identify_mock,
        group_mock,
        mocker,
    ):

        # arrange
        user = create_test_user()
        another_account_user = create_test_user(
            email='another@test.test'
        )
        create_invited_user(
            user=another_account_user,
            email=user.email
        )
        jwt_token = str(AuthToken.for_auth_data(email=user.email))
        mocker.patch(
            'pneumatic_backend.authentication.views.google.'
            'GoogleAuthPermission.has_permission',
            return_value=True
        )

        # act
        response = api_client.get(f'/auth/google?token={jwt_token}')

        # assert
        assert response.status_code == 200
        assert 'token' in response.data
        identify_mock.assert_called_once()
        group_mock.assert_called_once_with(user)
