import pytest
from datetime import timedelta
from pneumatic_backend.accounts.models import UserInvite
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.accounts.enums import (
    UserStatus,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
)
from pneumatic_backend.accounts.enums import SourceType
from pneumatic_backend.authentication import messages


pytestmark = pytest.mark.django_db


class TestTokenObtainView:

    @pytest.mark.parametrize(
        'username', [
            'test@pneumatic.app',
            'tESt@pneumatic.app',
        ]
    )
    def test_correct_data(
        self,
        mocker,
        username,
        api_client,
        identify_mock,
    ):
        # arrange
        user = create_test_user()
        user.set_password('12345')
        UserInvite.objects.create(
            email=user.email,
            account=user.account,
            invited_user=user,
        )
        user.save(update_fields=['password'])
        data = {
            'username': username,
            'password': '12345'
        }
        analytics_mock = mocker.patch(
            'pneumatic_backend.authentication.views.signin.'
            'AnalyticService.users_logged_in'
        )

        # act
        response = api_client.post('/auth/token/obtain', data=data)

        # assert
        assert response.status_code == 200
        assert response.data['token']
        identify_mock.assert_called_once_with(user)
        analytics_mock.assert_called_once_with(
            user=user,
            auth_type=AuthTokenType.USER,
            source=SourceType.EMAIL,
            is_superuser=False
        )

    def test_incorrect_data(
        self,
        mocker,
        api_client,
        identify_mock,
    ):
        # arrange
        user = create_test_user()
        user.set_password('password')
        user.save(update_fields=['password'])
        data = {
            'username': user.email,
            'password': 'YouShallNotPass'
        }
        analytics_mock = mocker.patch(
            'pneumatic_backend.authentication.views.signin.'
            'AnalyticService.users_logged_in'
        )

        # act
        response = api_client.post('/auth/token/obtain', data=data)

        # assert
        assert response.status_code == 403
        assert response.data['detail'] == messages.MSG_AU_0003
        identify_mock.assert_not_called()
        analytics_mock.assert_not_called()

    def test_user_not_verified(
        self,
        mocker,
        api_client,
        identify_mock,
        verification_check_true_mock,
    ):
        # arrange
        user = create_test_user()
        user.is_account_owner = True
        user.set_password('12345')
        user.save()
        account = user.account
        account.is_verified = False
        account.date_joined = user.date_joined - timedelta(weeks=3)
        account.save()

        data = {
            'username': user.email,
            'password': '12345'
        }
        analytics_mock = mocker.patch(
            'pneumatic_backend.authentication.views.signin.'
            'AnalyticService.users_logged_in'
        )

        # act
        response = api_client.post('/auth/token/obtain', data=data)

        assert response.status_code == 403
        assert response.data['detail'] == messages.MSG_AU_0002(user.email)
        analytics_mock.assert_not_called()
        identify_mock.assert_not_called()


class TestSuperuserView:

    def test_get_token(self, api_client, mocker):

        superuser = create_test_user()
        superuser.is_superuser = True
        superuser.save()
        email = 'user@pneumatic.app'
        user = create_test_user(email=email, status=UserStatus.ACTIVE)
        create_test_user(email=email, status=UserStatus.INACTIVE)
        create_test_user(email=email, status=UserStatus.INVITED)
        token = 'NeverGonnaGiveYouUpNeverGonnaLet'
        api_client.token_authenticate(superuser)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.views.signin.AuthService.'
            'get_superuser_auth_token',
            return_value=token
        )

        response = api_client.post(
            '/auth/superuser/token',
            data={
                'email': user.email,
            }
        )

        assert response.status_code == 200
        assert response.data['token'] == token
        get_token_mock.assert_called_once_with(user)

    def test_get_token__not_superuser(self, api_client):
        user = create_test_user()
        another_user = create_test_user(email='user@pneumatic.app')
        api_client.token_authenticate(user)

        response = api_client.post(
            '/auth/superuser/token',
            data={
                'email': another_user.email,
            }
        )

        assert response.status_code == 403
