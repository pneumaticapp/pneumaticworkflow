import pytest

from src.accounts.tokens import (
    VerificationToken,
)
from src.authentication import messages
from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_user,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


class TestTokenVerificationView:

    def test_user_checking(self, mocker, api_client):
        # arrange
        user = create_test_user()
        account = user.account
        account.is_verified = False
        account.save()
        token = str(VerificationToken.for_user(user))
        analysis_mock = mocker.patch(
            'src.accounts.services.user.'
            'AnalyticService.account_verified',
        )

        # act
        response = api_client.get(f'/auth/verification?token={token}')
        account.refresh_from_db()

        # assert
        assert response.status_code == 204
        assert account.is_verified is True
        analysis_mock.assert_called_once_with(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )

    @pytest.mark.parametrize('token', ('?token=', '?token'))
    def test_user_checking__invalid_token__validation_error(
        self,
        mocker,
        api_client,
        token,
    ):
        # arrange
        user = create_test_user()
        account = user.account
        account.is_verified = False
        account.save()
        analysis_mock = mocker.patch(
            'src.accounts.services.user.'
            'AnalyticService.account_verified',
        )

        # act
        response = api_client.get(f'/auth/verification{token}')

        # assert
        account.refresh_from_db()
        message = 'This field may not be blank.'
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert account.is_verified is False
        analysis_mock.assert_not_called()

    @pytest.mark.parametrize('token', ('', '?'))
    def test_user_checking__token_missing__validation_error(
        self,
        mocker,
        api_client,
        token,
    ):
        # arrange
        user = create_test_user()
        account = user.account
        account.is_verified = False
        account.save()
        analysis_mock = mocker.patch(
            'src.accounts.services.user.'
            'AnalyticService.account_verified',
        )

        # act
        response = api_client.get(f'/auth/verification{token}')

        # assert
        account.refresh_from_db()
        message = 'This field is required.'
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert account.is_verified is False
        analysis_mock.assert_not_called()

    def test_double_user_checking__analysis_sent_once(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_user()
        account = user.account
        account.is_verified = False
        account.save()
        token = str(VerificationToken.for_user(user))
        analysis_mock = mocker.patch(
            'src.accounts.services.user.'
            'AnalyticService.account_verified',
        )

        # act
        response = api_client.get(f'/auth/verification?token={token}')
        response_2 = api_client.get(f'/auth/verification?token={token}')
        account.refresh_from_db()

        # assert
        assert response.status_code == 204
        assert response_2.status_code == 204
        assert account.is_verified is True
        analysis_mock.assert_called_once_with(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )

    def test_user_checking_wrong_token(self, mocker, api_client):

        # arrange
        user = create_test_user()
        account = user.account
        account.is_verified = False
        account.save()
        token = '12345'
        analysis_mock = mocker.patch(
            'src.accounts.services.user.'
            'AnalyticService.account_verified',
        )

        # act
        response = api_client.get(f'/auth/verification?token={token}')
        account.refresh_from_db()

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == messages.MSG_AU_0008
        analysis_mock.assert_not_called()


class TestVerificationTokenResendView:
    def test_resend_mail__enabled_verification__ok(
        self,
        mocker,
        api_client,
        verification_check_true_mock,
    ):
        user = create_test_user(is_account_owner=True, is_admin=True)
        user.save()
        account = user.account
        account.is_verified = False
        account.save()

        send_verification_notification_mock = mocker.patch(
            'src.authentication.views.verification.'
            'send_verification_notification.delay',
        )
        api_client.token_authenticate(user)

        response = api_client.post('/auth/resend-verification')

        assert response.status_code == 200
        assert response.data['email'] == user.email
        send_verification_notification_mock.assert_called_once()

    def test_resend_mail__disable_verification__not_sent(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_user(is_account_owner=True, is_admin=True)
        account = user.account
        account.is_verified = False
        account.save()

        send_verification_notification_mock = mocker.patch(
            'src.authentication.views.verification.'
            'send_verification_notification.delay',
        )

        api_client.token_authenticate(user)

        # act
        response = api_client.post('/auth/resend-verification')

        # assert
        assert response.status_code == 200
        assert response.data['email'] == user.email
        send_verification_notification_mock.assert_not_called()

    def test_resend_already_verified(self, mocker, api_client):

        user = create_test_user(is_account_owner=True, is_admin=True)
        send_verification_notification_mock = mocker.patch(
            'src.authentication.views.verification.'
            'send_verification_notification.delay',
        )
        api_client.token_authenticate(user)

        response = api_client.post('/auth/resend-verification')

        assert response.status_code == 200
        send_verification_notification_mock.assert_not_called()
