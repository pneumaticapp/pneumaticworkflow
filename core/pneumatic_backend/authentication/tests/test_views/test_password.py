import pytest
from pneumatic_backend.accounts.tokens import (
    ResetPasswordToken,
)
from pneumatic_backend.authentication.enums import ResetPasswordStatus
from pneumatic_backend.accounts.enums import UserStatus
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_guest,
    create_invited_user,
)
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.authentication import messages


pytestmark = pytest.mark.django_db


class TestResetPasswordViewSet:

    def test_create__ok(self, mocker, api_client):

        # arrange
        user = create_test_user()
        send_reset_password_notification_mock = mocker.patch(
            'pneumatic_backend.authentication.views.password.'
            'send_reset_password_notification.delay'
        )

        # act
        response = api_client.post(
            '/auth/reset-password',
            {
                'email': user.email
            }
        )

        # assert
        assert response.status_code == 204
        send_reset_password_notification_mock.assert_called_once_with(
            user_id=user.id,
            user_email=user.email,
            logo_lg=user.account.logo_lg,
        )

    def test_create__not_user__ok(self, mocker, api_client):

        # arrange
        email = 'test@pneumatic.app'
        send_reset_password_notification_mock = mocker.patch(
            'pneumatic_backend.authentication.views.password.'
            'send_reset_password_notification.delay'
        )

        # act
        response = api_client.post(
            '/auth/reset-password',
            {
                'email': email
            }
        )

        # assert
        assert response.status_code == 204
        send_reset_password_notification_mock.assert_not_called()

    def test_create__active_and_invited_user__call_active(
        self,
        mocker,
        api_client
    ):
        # arrange
        email = 'owner@test.test'
        user = create_test_user(email=email)
        another_owner = create_test_user(email='another@test.test')
        create_invited_user(user=another_owner, email=email)
        send_reset_password_notification_mock = mocker.patch(
            'pneumatic_backend.authentication.views.password.'
            'send_reset_password_notification.delay'
        )

        # act
        response = api_client.post(
            path='/auth/reset-password',
            data={
                'email': email
            }
        )

        # assert
        assert response.status_code == 204
        send_reset_password_notification_mock.assert_called_once_with(
            user_id=user.id,
            user_email=email,
            logo_lg=user.account.logo_lg,
        )

    def test_list_valid(self, api_client):
        # arrange
        user = create_test_user()
        jwt_key = str(ResetPasswordToken.for_user(user))

        # act
        response = api_client.get(f'/auth/reset-password?token={jwt_key}')

        assert response.status_code == 200
        assert response.data['status'] == ResetPasswordStatus.VALID

    def test_list_invalid(self, api_client):
        # act
        response = api_client.get('/auth/reset-password?token=SDKSDJnksnelg')

        # assert
        assert response.status_code == 200
        assert response.data['status'] == ResetPasswordStatus.INVALID

    @pytest.mark.parametrize('status', UserStatus.NOT_ACTIVE)
    def test_list__not_active_user__invalid(self, api_client, status):
        # arrange
        user = create_test_user()
        jwt_key = str(ResetPasswordToken.for_user(user))
        user.status = status
        user.save(update_fields=['status'])

        # act
        response = api_client.get(f'/auth/reset-password?token={jwt_key}')

        assert response.status_code == 200
        assert response.data['status'] == ResetPasswordStatus.INVALID

    def test_list__deleted_user__invalid(self, api_client):
        # arrange
        user = create_test_user()
        jwt_key = str(ResetPasswordToken.for_user(user))
        user.delete()

        # act
        response = api_client.get(f'/auth/reset-password?token={jwt_key}')

        assert response.status_code == 200
        assert response.data['status'] == ResetPasswordStatus.INVALID

    def test_list__guest__invalid(self, api_client):

        # arrange
        owner = create_test_user(
            is_account_owner=True,
            email='owner@test.test',
        )
        guest = create_test_guest(account=owner.account)
        jwt_key = str(ResetPasswordToken.for_user(guest))

        # act
        response = api_client.get(f'/auth/reset-password?token={jwt_key}')

        assert response.status_code == 200
        assert response.data['status'] == ResetPasswordStatus.INVALID

    def test_confirm__ok(
        self,
        mocker,
        api_client,
        expire_tokens_mock
    ):

        # arrange
        user = create_test_user()
        another_owner = create_test_user(email='owner@test.test')
        create_invited_user(user=another_owner, email=user.email)
        user_change_password_mock = mocker.patch(
            'pneumatic_backend.accounts.services.user.UserService'
            '.change_password'
        )
        jwt_key = str(ResetPasswordToken.for_user(user))
        data = {
            'new_password': 'test',
            'confirm_new_password': 'test',
            'token': jwt_key
        }

        # act
        response = api_client.post('/auth/reset-password/confirm', data)

        # assert
        expire_tokens_mock.assert_called_once_with(user)
        user_change_password_mock.assert_called_once_with(
            password=data['new_password']
        )
        assert response.status_code == 200
        assert response.data['token']

    def test_confirm__active_and_invited_user__return_active(
        self,
        mocker,
        api_client,
        expire_tokens_mock
    ):

        # arrange
        user = create_test_user()
        user_change_password_mock = mocker.patch(
            'pneumatic_backend.accounts.services.user.UserService'
            '.change_password'
        )
        jwt_key = str(ResetPasswordToken.for_user(user))
        data = {
            'new_password': 'test',
            'confirm_new_password': 'test',
            'token': jwt_key
        }

        # act
        response = api_client.post('/auth/reset-password/confirm', data)

        # assert
        expire_tokens_mock.assert_called_once_with(user)
        user_change_password_mock.assert_called_once_with(
            password=data['new_password']
        )
        assert response.status_code == 200
        assert response.data['token']

    def test_confirm__password_mismatch__validation_error(
        self,
        mocker,
        api_client,
        expire_tokens_mock
    ):

        # arrange
        user = create_test_user()
        user_change_password_mock = mocker.patch(
            'pneumatic_backend.accounts.services.user.UserService'
            '.change_password'
        )
        jwt_key = str(ResetPasswordToken.for_user(user))
        data = {
            'new_password': 'test',
            'confirm_new_password': '12345',
            'token': jwt_key
        }

        # act
        response = api_client.post('/auth/reset-password/confirm', data)

        # assert
        expire_tokens_mock.assert_not_called()
        user_change_password_mock.assert_not_called()
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == messages.MSG_AU_0013

    @pytest.mark.parametrize(
        'new_password, confirm_new_password', [
            ('', ''),
            (' ', ' '),
        ]
    )
    def test_confirm__password_blank__validation_error(
        self,
        mocker,
        api_client,
        expire_tokens_mock,
        new_password,
        confirm_new_password,
    ):

        # arrange
        user = create_test_user()
        user_change_password_mock = mocker.patch(
            'pneumatic_backend.accounts.services.user.UserService'
            '.change_password'
        )
        jwt_key = str(ResetPasswordToken.for_user(user))
        data = {
            'new_password': new_password,
            'confirm_new_password': confirm_new_password,
            'token': jwt_key
        }

        # act
        response = api_client.post('/auth/reset-password/confirm', data)

        # assert
        message = 'This field may not be blank.'
        expire_tokens_mock.assert_not_called()
        user_change_password_mock.assert_not_called()
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['name'] == 'new_password'

    def test_confirm__password_none__validation_error(
        self,
        mocker,
        api_client,
        expire_tokens_mock,
    ):

        # arrange
        user = create_test_user()
        user_change_password_mock = mocker.patch(
            'pneumatic_backend.accounts.services.user.UserService'
            '.change_password'
        )
        jwt_key = str(ResetPasswordToken.for_user(user))
        data = {
            'new_password': None,
            'confirm_new_password': None,
            'token': jwt_key
        }

        # act
        response = api_client.post('/auth/reset-password/confirm', data)

        # assert
        message = 'This field may not be null.'
        expire_tokens_mock.assert_not_called()
        user_change_password_mock.assert_not_called()
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['name'] == 'new_password'


class TestChangePassword:

    def test_change__ok(
        self,
        mocker,
        api_client,
        expire_tokens_mock
    ):
        # arrange
        user = create_test_user()
        user.set_password('12345')
        user.save()
        user_change_password_mock = mocker.patch(
            'pneumatic_backend.accounts.services.user.UserService'
            '.change_password'
        )
        data = {
            'old_password': '12345',
            'new_password': '54321',
            'confirm_new_password': '54321'
        }
        api_client.token_authenticate(user)

        # act
        response = api_client.post('/auth/change-password', data=data)

        # assert
        assert response.status_code == 200
        assert response.data['token']
        expire_tokens_mock.assert_called_once_with(user)
        user_change_password_mock.assert_called_once_with(
            password=data['new_password']
        )

    def test_change__invited_and_active_user__return_active(
        self,
        mocker,
        api_client,
        expire_tokens_mock
    ):
        # arrange
        user = create_test_user()
        user.set_password('12345')
        user.save()
        another_account_owner = create_test_user(email='ao@t.t')
        create_invited_user(
            user=another_account_owner,
            email=user.email
        )
        user_change_password_mock = mocker.patch(
            'pneumatic_backend.accounts.services.user.UserService'
            '.change_password'
        )
        data = {
            'old_password': '12345',
            'new_password': '54321',
            'confirm_new_password': '54321'
        }
        api_client.token_authenticate(user)

        # act
        response = api_client.post('/auth/change-password', data=data)

        # assert
        assert response.status_code == 200
        assert response.data['token']
        expire_tokens_mock.assert_called_once_with(user)
        user_change_password_mock.assert_called_once_with(
            password=data['new_password']
        )

    def test_change_wrong_old_password(
        self,
        mocker,
        api_client,
        expire_tokens_mock
    ):
        # arrange
        user = create_test_user()
        user.set_password('12345')
        user.save()
        user_change_password_mock = mocker.patch(
            'pneumatic_backend.accounts.services.user.UserService'
            '.change_password'
        )
        data = {
            'old_password': '123',
            'new_password': '54321',
            'confirm_new_password': '54321'
        }
        api_client.token_authenticate(user)

        # act
        response = api_client.post('/auth/change-password', data=data)

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == messages.MSG_AU_0012
        expire_tokens_mock.assert_not_called()
        user_change_password_mock.assert_not_called()

    def test_change_wrong_confirm_password(
        self,
        mocker,
        api_client,
        expire_tokens_mock
    ):
        # arrange
        user = create_test_user()
        user.set_password('12345')
        user.save()
        user_change_password_mock = mocker.patch(
            'pneumatic_backend.accounts.services.user.UserService'
            '.change_password'
        )
        data = {
            'old_password': '12345',
            'new_password': '54321',
            'confirm_new_password': '12345'
        }
        api_client.token_authenticate(user)

        # act
        response = api_client.post('/auth/change-password', data=data)

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == messages.MSG_AU_0013
        expire_tokens_mock.assert_not_called()
        user_change_password_mock.assert_not_called()

    @pytest.mark.parametrize(
        'new_password, confirm_new_password', [('', ''), (' ', ' '), ]
    )
    def test_change__password_blank__validation_error(
        self,
        mocker,
        api_client,
        expire_tokens_mock,
        new_password,
        confirm_new_password,
    ):

        # arrange
        user = create_test_user()
        user.set_password('12345')
        user.save()
        user_change_password_mock = mocker.patch(
            'pneumatic_backend.accounts.services.user.UserService'
            '.change_password'
        )
        data = {
            'old_password': '12345',
            'new_password': new_password,
            'confirm_new_password': confirm_new_password
        }
        api_client.token_authenticate(user)

        # act
        response = api_client.post('/auth/change-password', data=data)

        # assert
        message = 'This field may not be blank.'
        expire_tokens_mock.assert_not_called()
        user_change_password_mock.assert_not_called()
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['name'] == 'new_password'

    def test_change__password_none__validation_error(
        self,
        mocker,
        api_client,
        expire_tokens_mock,
    ):
        # arrange
        user = create_test_user()
        user.set_password('12345')
        user.save()
        user_change_password_mock = mocker.patch(
            'pneumatic_backend.accounts.services.user.UserService'
            '.change_password'
        )
        data = {
            'old_password': '12345',
            'new_password': None,
            'confirm_new_password': None
        }
        api_client.token_authenticate(user)

        # act
        response = api_client.post('/auth/change-password', data=data)

        # assert
        message = 'This field may not be null.'
        expire_tokens_mock.assert_not_called()
        user_change_password_mock.assert_not_called()
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['name'] == 'new_password'
