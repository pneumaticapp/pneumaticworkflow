import pytest
from django.conf import settings
from pneumatic_backend.accounts.tests.fixtures import (
    create_test_user,
    create_test_account
)
from pneumatic_backend.accounts.services.exceptions import (
    InvalidTransferTokenException,
    AlreadyAcceptedInviteException,
)


pytestmark = pytest.mark.django_db


class TestDeprecatedTransfer:
    # TODO remove in https://my.pneumatic.app/workflows/15691/

    def test_transfer__ok(
        self,
        api_client,
        mocker,
    ):
        # arrange
        account_to_transfer = create_test_account()
        user_to_transfer = create_test_user()
        token = '1@ad!'
        accept_transfer_mock = mocker.patch(
            'pneumatic_backend.accounts.services.user_transfer.'
            'UserTransferService.accept_transfer'
        )
        mocker.patch(
            'pneumatic_backend.accounts.services.user_transfer.'
            'UserTransferService.get_account',
            return_value=account_to_transfer
        )

        # act
        response = api_client.get(
            f'/accounts/users/{user_to_transfer.id}/transfer?token={token}'
        )

        # assert
        assert response.status_code == 200
        assert b'You was successfully transferred to account' in (
            response.content
        )
        accept_transfer_mock.assert_called_once_with(
            token_str=token,
            user_id=user_to_transfer.id
        )

    def test_transfer__skip_token__redirect(
        self,
        api_client,
        mocker,
    ):
        # arrange
        user_to_transfer = create_test_user()
        accept_transfer_mock = mocker.patch(
            'pneumatic_backend.accounts.services.user_transfer.'
            'UserTransferService.accept_transfer'
        )

        # act
        response = api_client.get(
            f'/accounts/users/{user_to_transfer.id}/transfer?token='
        )

        # assert
        assert response.status_code == 302
        assert response.url == settings.EXPIRED_INVITE_PAGE
        accept_transfer_mock.assert_not_called()

    def test_transfer__invalid_user_id__redirect(
        self,
        api_client,
        mocker,
    ):
        # arrange
        token = '!2wds@'
        accept_transfer_mock = mocker.patch(
            'pneumatic_backend.accounts.services.user_transfer.'
            'UserTransferService.accept_transfer'
        )

        # act
        response = api_client.get(
            f'/accounts/users/lol/transfer?token={token}'
        )

        # assert
        assert response.status_code == 302
        assert response.url == settings.EXPIRED_INVITE_PAGE
        accept_transfer_mock.assert_not_called()

    def test_transfer__already_accepted__redirect(
        self,
        api_client,
        mocker,
    ):
        # arrange
        user_to_transfer = create_test_user()
        token = '1@ad!'
        accept_transfer_mock = mocker.patch(
            'pneumatic_backend.accounts.services.user_transfer.'
            'UserTransferService.accept_transfer',
            side_effect=AlreadyAcceptedInviteException
        )

        # act
        response = api_client.get(
            f'/accounts/users/{user_to_transfer.id}/transfer?token={token}'
        )

        # assert
        assert response.status_code == 302
        assert response.url == settings.FRONTEND_URL
        accept_transfer_mock.assert_called_once_with(
            token_str=token,
            user_id=user_to_transfer.id
        )

    def test_transfer__invalid_token__redirect(
        self,
        api_client,
        mocker,
    ):
        # arrange
        user_to_transfer = create_test_user()
        token = '1@ad!'
        accept_transfer_mock = mocker.patch(
            'pneumatic_backend.accounts.services.user_transfer.'
            'UserTransferService.accept_transfer',
            side_effect=InvalidTransferTokenException
        )

        # act
        response = api_client.get(
            f'/accounts/users/{user_to_transfer.id}/transfer?token={token}'
        )

        # assert
        assert response.status_code == 302
        assert response.url == settings.EXPIRED_INVITE_PAGE
        accept_transfer_mock.assert_called_once_with(
            token_str=token,
            user_id=user_to_transfer.id
        )


# TODO uncomment in https://my.pneumatic.app/workflows/15691/
# class TestTransfer:
#
#     def test_transfer__ok(
#         self,
#         api_client,
#         mocker,
#     ):
#         # arrange
#         user_to_transfer = create_test_user()
#         accept_transfer_mock = mocker.patch(
#             'pneumatic_backend.accounts.services.user_transfer.'
#             'UserTransferService.accept_transfer'
#         )
#         new_user_mock = mocker.Mock()
#         mocker.patch(
#             'pneumatic_backend.accounts.services.user_transfer.'
#             'UserTransferService.get_user',
#             return_value=new_user_mock
#         )
#         token = '123123asd'
#         get_token_mock = mocker.patch(
#             'pneumatic_backend.authentication.services.'
#             'AuthService.get_auth_token',
#             return_value=token
#         )
#         user_agent = 'Some/Mozilla'
#         user_ip = '128.18.0.99'
#
#         # act
#         response = api_client.get(
#             f'/accounts/users/{user_to_transfer.id}/transfer?token={token}',
#             HTTP_USER_AGENT=user_agent,
#             HTTP_X_REAL_IP=user_ip
#         )
#
#         # assert
#         assert response.status_code == 200
#         accept_transfer_mock.assert_called_once_with(
#             token_str=token,
#             user_id=user_to_transfer.id
#         )
#         get_token_mock.assert_called_once_with(
#             user=new_user_mock,
#             user_agent=user_agent,
#             user_ip=user_ip
#         )
#
#     def test_transfer__skip_token__validation_error(
#         self,
#         api_client,
#         mocker,
#     ):
#         # arrange
#         user_to_transfer = create_test_user()
#         accept_transfer_mock = mocker.patch(
#             'pneumatic_backend.accounts.services.user_transfer.'
#             'UserTransferService.accept_transfer'
#         )
#
#         # act
#         response = api_client.get(
#             f'/accounts/users/{user_to_transfer.id}/transfer?token='
#         )
#
#         # assert
#         assert response.status_code == 400
#         assert response.data['code'] == ErrorCode.VALIDATION_ERROR
#         assert response.data['message'] == 'This field may not be blank.'
#         accept_transfer_mock.assert_not_called()
#
#     def test_transfer__invalid_user_id__validation_error(
#         self,
#         api_client,
#         mocker,
#     ):
#         # arrange
#         token = '!2wds@'
#         accept_transfer_mock = mocker.patch(
#             'pneumatic_backend.accounts.services.user_transfer.'
#             'UserTransferService.accept_transfer',
#             side_effect=InvalidTransferTokenException()
#         )
#
#         # act
#         response = api_client.get(
#             f'/accounts/users/lol/transfer?token={token}'
#         )
#
#         # assert
#         assert response.status_code == 400
#         assert response.data['code'] == ErrorCode.VALIDATION_ERROR
#         assert response.data['message'] == 'A valid integer is required.'
#         accept_transfer_mock.assert_not_called()
#
#     def test_transfer__service_exception__validation_error(
#         self,
#         api_client,
#         mocker,
#     ):
#         # arrange
#         user_to_transfer = create_test_user()
#         token = '1@ad!'
#         accept_transfer_mock = mocker.patch(
#             'pneumatic_backend.accounts.services.user_transfer.'
#             'UserTransferService.accept_transfer',
#             side_effect=InvalidTransferTokenException()
#         )
#
#         # act
#         response = api_client.get(
#             f'/accounts/users/{user_to_transfer.id}/transfer?token={token}'
#         )
#
#         # assert
#         assert response.status_code == 400
#         assert response.data['code'] == ErrorCode.VALIDATION_ERROR
#         assert response.data['message'] == MSG_A_0008
#         accept_transfer_mock.assert_called_once_with(
#             token_str=token,
#             user_id=user_to_transfer.id
#         )
#
#     def test_transfer__already_accepted__already_accepted_error(
#         self,
#         api_client,
#         mocker,
#     ):
#         # arrange
#         user_to_transfer = create_test_user()
#         token = '1@ad!'
#         accept_transfer_mock = mocker.patch(
#             'pneumatic_backend.accounts.services.user_transfer.'
#             'UserTransferService.accept_transfer',
#             side_effect=AlreadyAcceptedInviteException
#         )
#
#         # act
#         response = api_client.get(
#             f'/accounts/users/{user_to_transfer.id}/transfer?token={token}'
#         )
#
#         # assert
#         assert response.status_code == 400
#         assert response.data['code'] == ErrorCode.VALIDATION_ERROR
#         assert response.data['message'] == MSG_A_0007
#         accept_transfer_mock.assert_called_once_with(
#             token_str=token,
#             user_id=user_to_transfer.id
#         )
