# pylint:disable=redefined-outer-name
import pytest
from pneumatic_backend.accounts.enums import (
    UserInviteStatus,
    SourceType,
    UserStatus,
    Timezone,
    Language,
)
from pneumatic_backend.accounts.tests.fixtures import (
    create_test_owner,
    create_test_account,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_invited_user,
    create_test_group,
)
from pneumatic_backend.accounts.tokens import (
    InviteToken,
)
from pneumatic_backend.accounts.services import (
    UserInviteService,
)
from pneumatic_backend.accounts.services.exceptions import (
    AlreadyAcceptedInviteException,
    UserNotFoundException,
    UsersLimitInvitesException,
    UserIsPerformerException,
    AlreadyRegisteredException,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.accounts.messages import (
    MSG_A_0002,
    MSG_A_0005,
    MSG_A_0006,
    MSG_A_0007,
    MSG_A_0011,
    MSG_A_0013,
    MSG_A_0040,
)
from pneumatic_backend.utils.validation import ErrorCode


pytestmark = pytest.mark.django_db


class TestCreate:

    def test_create__all_fields__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        group = create_test_group(user=user)
        current_url = 'https://my.pneumatic.app/dashboard'
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        invite_users_mock = mocker.patch(
            'pneumatic_backend.accounts.services.UserInviteService.'
            'invite_users'
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            '/accounts/invites',
            data={
                'users': [
                    {
                        'email': 'test1@pneumatic.app',
                        'invited_from': SourceType.EMAIL,
                        'groups': [group.id, ]
                    },
                ]
            },
            HTTP_X_CURRENT_URL=current_url,
        )

        # assert
        assert response.status_code == 200
        assert response.data['already_accepted'] == ()
        service_mock.assert_called_once_with(
            is_superuser=False,
            request_user=user,
            current_url=current_url
        )
        invite_users_mock.assert_called_once_with(data=[
            {
                'email': 'test1@pneumatic.app',
                'invited_from': SourceType.EMAIL,
                'groups': [group.id, ]
            },
        ])

    def test_create_group_not_in_account_ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        group = create_test_group(user=user)
        another_user = create_test_owner(email='test2@pneumatic.app')
        another_group = create_test_group(user=another_user)
        current_url = 'https://my.pneumatic.app/dashboard'
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        invite_users_mock = mocker.patch(
            'pneumatic_backend.accounts.services.UserInviteService.'
            'invite_users'
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            '/accounts/invites',
            data={
                'users': [
                    {
                        'email': 'test1@pneumatic.app',
                        'invited_from': SourceType.EMAIL,
                        'groups': [group.id, another_group.id]
                    },
                ]
            },
            HTTP_X_CURRENT_URL=current_url,
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == MSG_A_0040
        assert response.data['details']['reason'] == MSG_A_0040
        assert response.data['details']['name'] == 'groups'
        service_mock.assert_not_called()
        invite_users_mock.assert_not_called()

    def test_create__multiple_invites__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        current_url = 'https://my.pneumatic.app/dashboard'
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        invite_users_mock = mocker.patch(
            'pneumatic_backend.accounts.services.UserInviteService.'
            'invite_users'
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            '/accounts/invites',
            data={
                'users': [
                    {
                        'email': 'test1@pneumatic.app',
                        'invited_from': SourceType.EMAIL
                    },
                    {
                        'email': 'test2@pneumatic.app',
                        'invited_from': SourceType.MICROSOFT
                    },
                    {
                        'email': 'test3@pneumatic.app',
                        'invited_from': SourceType.GOOGLE
                    }
                ]
            },
            HTTP_X_CURRENT_URL=current_url,
        )

        # assert
        assert response.status_code == 200
        assert response.data['already_accepted'] == ()
        service_mock.assert_called_once_with(
            is_superuser=False,
            request_user=user,
            current_url=current_url
        )
        invite_users_mock.assert_called_once_with(data=[
            {
                'email': 'test1@pneumatic.app',
                'invited_from': SourceType.EMAIL
            },
            {
                'email': 'test2@pneumatic.app',
                'invited_from': SourceType.MICROSOFT
            },
            {
                'email': 'test3@pneumatic.app',
                'invited_from': SourceType.GOOGLE
            }
        ])

    def test_create__already_accepted__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        current_url = 'https://my.pneumatic.app/dashboard'
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        invite_users_mock = mocker.patch(
            'pneumatic_backend.accounts.services.UserInviteService.'
            'invite_users',
            side_effect=AlreadyAcceptedInviteException(
                invites_data=[
                    {
                        'email': 'test1@pneumatic.app',
                        'invited_from': SourceType.EMAIL
                    }
                ]
            )
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            '/accounts/invites',
            data={
                'users': [
                    {
                        'email': 'test1@pneumatic.app',
                        'invited_from': SourceType.EMAIL
                    }
                ]
            },
            HTTP_X_CURRENT_URL=current_url,
        )

        # assert
        assert response.status_code == 200
        assert response.data['already_accepted'] == [
            {
                'email': 'test1@pneumatic.app',
                'invited_from': SourceType.EMAIL
            }
        ]
        service_mock.assert_called_once_with(
            is_superuser=False,
            request_user=user,
            current_url=current_url
        )
        invite_users_mock.assert_called_once_with(data=[
            {
                'email': 'test1@pneumatic.app',
                'invited_from': SourceType.EMAIL
            }
        ])

    def test_create__limit_invites__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        current_url = 'https://my.pneumatic.app/dashboard'
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        invite_users_mock = mocker.patch(
            'pneumatic_backend.accounts.services.UserInviteService.'
            'invite_users',
            side_effect=UsersLimitInvitesException()
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            '/accounts/invites',
            data={
                'users': [
                    {
                        'email': 'test1@pneumatic.app',
                        'invited_from': SourceType.EMAIL
                    }
                ]
            },
            HTTP_X_CURRENT_URL=current_url,
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == MSG_A_0006
        service_mock.assert_called_once_with(
            is_superuser=False,
            request_user=user,
            current_url=current_url
        )
        invite_users_mock.assert_called_once_with(data=[
            {
                'email': 'test1@pneumatic.app',
                'invited_from': SourceType.EMAIL
            }
        ])

    def test_create__invalid_email__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        current_url = 'https://my.pneumatic.app/dashboard'
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        invite_users_mock = mocker.patch(
            'pneumatic_backend.accounts.services.UserInviteService.'
            'invite_users'
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            '/accounts/invites',
            data={
                'users': [
                    {
                        'email': 'error',
                        'invited_from': SourceType.EMAIL
                    }
                ]
            },
            HTTP_X_CURRENT_URL=current_url,
        )

        # assert
        assert response.status_code == 400
        message = 'Enter a valid email address.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['name'] == 'email'
        assert response.data['details']['reason'] == message
        service_mock.assert_not_called()
        invite_users_mock.assert_not_called()

    def test_create__skip_invited_from__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        current_url = 'https://my.pneumatic.app/dashboard'
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        invite_users_mock = mocker.patch(
            'pneumatic_backend.accounts.services.UserInviteService.'
            'invite_users'
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            '/accounts/invites',
            data={
                'users': [
                    {
                        'email': 'test@test.test',
                    }
                ]
            },
            HTTP_X_CURRENT_URL=current_url,
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == MSG_A_0002
        service_mock.assert_not_called()
        invite_users_mock.assert_not_called()

    def test_create__invited_email__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        current_url = 'https://my.pneumatic.app/dashboard'
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        invite_users_mock = mocker.patch(
            'pneumatic_backend.accounts.services.UserInviteService.'
            'invite_users'
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            '/accounts/invites',
            data={
                'users': [
                    {
                        'email': 'error',
                        'invited_from': SourceType.EMAIL,
                    }
                ]
            },
            HTTP_X_CURRENT_URL=current_url,
        )

        # assert
        assert response.status_code == 400
        message = 'Enter a valid email address.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        service_mock.assert_not_called()
        invite_users_mock.assert_not_called()

    @pytest.mark.parametrize('group', ([''], [' '], ['none']))
    def test_accept__group__invalid_value__validation_error(
        self,
        group,
        mocker,
        api_client,
    ):

        # arrange
        user = create_test_owner()
        current_url = 'https://my.pneumatic.app/dashboard'
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        invite_users_mock = mocker.patch(
            'pneumatic_backend.accounts.services.UserInviteService.'
            'invite_users'
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            '/accounts/invites',
            data={
                'users': [
                    {
                        'email': 'test1@pneumatic.app',
                        'invited_from': SourceType.EMAIL,
                        'groups': group
                    }
                ]
            },
            HTTP_X_CURRENT_URL=current_url,
        )

        # assert
        assert response.status_code == 400
        message = 'A valid integer is required.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['name'] == 'groups'
        assert response.data['details']['reason'] == message
        service_mock.assert_not_called()
        invite_users_mock.assert_not_called()

    @pytest.mark.parametrize('group', ('', ' ', 'undefined'))
    def test_accept__group__invalid_list__validation_error(
        self,
        group,
        mocker,
        api_client,
    ):

        # arrange
        user = create_test_owner()
        current_url = 'https://my.pneumatic.app/dashboard'
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        invite_users_mock = mocker.patch(
            'pneumatic_backend.accounts.services.UserInviteService.'
            'invite_users'
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            '/accounts/invites',
            data={
                'users': [
                    {
                        'email': 'test1@pneumatic.app',
                        'invited_from': SourceType.EMAIL,
                        'groups': group
                    }
                ]
            },
            HTTP_X_CURRENT_URL=current_url,
        )

        # assert
        assert response.status_code == 400
        message = 'Expected a list of items but got type "str".'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['name'] == 'groups'
        assert response.data['details']['reason'] == message
        service_mock.assert_not_called()
        invite_users_mock.assert_not_called()

    def test_accept__group_is_None__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        current_url = 'https://my.pneumatic.app/dashboard'
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        invite_users_mock = mocker.patch(
            'pneumatic_backend.accounts.services.UserInviteService.'
            'invite_users'
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            '/accounts/invites',
            data={
                'users': [
                    {
                        'email': 'test1@pneumatic.app',
                        'invited_from': SourceType.EMAIL,
                        'groups': None,
                    }
                ]
            },
            HTTP_X_CURRENT_URL=current_url,
        )

        # assert
        assert response.status_code == 400
        message = 'This field may not be null.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['name'] == 'groups'
        assert response.data['details']['reason'] == message
        service_mock.assert_not_called()
        invite_users_mock.assert_not_called()


class TestDecline:

    def test_decline__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        account = create_test_account()
        request_user = create_test_user(account=account)
        invited_user = create_invited_user(request_user)
        deactivate_mock = mocker.patch(
            'pneumatic_backend.accounts.services.user.UserService'
            '.deactivate'
        )
        api_client.token_authenticate(request_user)

        # act
        response = api_client.post(
            '/accounts/invites/decline',
            data={'invite_id': invited_user.invite.id}
        )

        # assert
        assert response.status_code == 204
        deactivate_mock.assert_called_once_with(invited_user)

    def test_decline__user_is_performer__validation_error(
        self,
        mocker,
        api_client,
    ):

        # arrange
        account = create_test_account()
        request_user = create_test_user(account=account)
        invited_user = create_invited_user(request_user)
        deactivate_mock = mocker.patch(
            'pneumatic_backend.accounts.services.user.UserService'
            '.deactivate',
            side_effect=UserIsPerformerException()
        )
        api_client.token_authenticate(request_user)

        # act
        response = api_client.post(
            '/accounts/invites/decline',
            data={'invite_id': invited_user.invite.id}
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == MSG_A_0011
        deactivate_mock.assert_called_once_with(invited_user)

    def test_decline__another_account_invite__not_found(
        self,
        mocker,
        api_client,
    ):

        # arrange
        account = create_test_account()
        request_user = create_test_user(account=account)

        another_account = create_test_account()
        another_user = create_test_user(
            email='another@test.test',
            account=another_account
        )
        another_invited_user = create_invited_user(another_user)
        api_client.token_authenticate(request_user)
        deactivate_mock = mocker.patch(
            'pneumatic_backend.accounts.services.user.UserService'
            '.deactivate'
        )

        # act
        response = api_client.post(
            '/accounts/invites/decline',
            data={'invite_id': another_invited_user.invite.id}
        )

        # assert
        assert response.status_code == 404
        deactivate_mock.assert_not_called()

    def test_decline__accepted_invite__not_found(
        self,
        mocker,
        api_client,
    ):

        # arrange
        account = create_test_account()
        request_user = create_test_user(account=account)
        invited_user = create_invited_user(request_user)
        invite = invited_user.invite
        invite.status = UserInviteStatus.ACCEPTED
        invite.save()

        api_client.token_authenticate(request_user)
        deactivate_mock = mocker.patch(
            'pneumatic_backend.accounts.services.user.UserService'
            '.deactivate'
        )

        # act
        response = api_client.post(
            '/accounts/invites/decline',
            data={'invite_id': invited_user.invite.id}
        )

        # assert
        assert response.status_code == 404
        deactivate_mock.assert_not_called()

    def test_decline__not_admin__permission_denied(
        self,
        mocker,
        api_client,
    ):

        # arrange
        request_user = create_test_user(is_admin=False, is_account_owner=False)
        invited_user = create_invited_user(request_user)

        api_client.token_authenticate(request_user)
        deactivate_mock = mocker.patch(
            'pneumatic_backend.accounts.services.user.UserService'
            '.deactivate'
        )

        # act
        response = api_client.post(
            '/accounts/invites/decline',
            data={'invite_id': invited_user.invite.id}
        )

        # assert
        assert response.status_code == 403
        deactivate_mock.assert_not_called()


class TestToken:

    def test_token__ok(
        self,
        api_client,
        identify_mock,
        group_mock
    ):

        # arrange
        account_owner = create_test_user()
        user = create_invited_user(account_owner)
        invite = user.incoming_invites.filter(
            account=account_owner.account
        ).first()
        invite_token = str(InviteToken.for_user(user))

        # act
        response = api_client.get(
            f'/accounts/invites/token?token={invite_token}'
        )

        # assert
        assert response.status_code == 200
        assert response.data['id'] == invite.id
        identify_mock.assert_called_once_with(user)
        group_mock.assert_called_once_with(user)

    def test_token__invalid_token__raise_validation_error(
        self,
        api_client,
        identify_mock,
        group_mock,
    ):
        # act
        response = api_client.get(f'/accounts/invites/token?token={12345}')

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == MSG_A_0013
        identify_mock.assert_not_called()
        group_mock.assert_not_called()

    def test_token__deleted_invite__validation_error(
        self,
        api_client,
        identify_mock,
        group_mock
    ):

        # arrange
        account_owner = create_test_user()
        user = create_invited_user(account_owner)

        invite_token = str(InviteToken.for_user(user))
        user.incoming_invites.delete()

        # act
        response = api_client.get(
            f'/accounts/invites/token?token={invite_token}'
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == MSG_A_0013
        identify_mock.assert_not_called()
        group_mock.assert_not_called()

    def test_token__inactive_user__validation_error(
        self,
        api_client,
        identify_mock,
        group_mock
    ):

        # arrange
        account_owner = create_test_user()
        user = create_invited_user(account_owner)

        invite_token = str(InviteToken.for_user(user))
        user.status = UserStatus.INACTIVE
        user.save(update_fields=['status'])

        # act
        response = api_client.get(
            f'/accounts/invites/token?token={invite_token}'
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == MSG_A_0013
        identify_mock.assert_not_called()
        group_mock.assert_not_called()

    def test_token__token_is_null__validation_error(
        self,
        api_client,
        identify_mock,
        group_mock,
    ):
        # act
        response = api_client.get(
            path='/accounts/invites/token?token=null',
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == MSG_A_0013
        identify_mock.assert_not_called()
        group_mock.assert_not_called()

    def test_token__token_blank__validation_error(
        self,
        api_client,
        identify_mock,
        group_mock,
    ):
        # act
        response = api_client.get(
            path='/accounts/invites/token',
            data={
                'token': ''
            }
        )

        # assert
        assert response.status_code == 400
        message = 'This field may not be blank.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        identify_mock.assert_not_called()
        group_mock.assert_not_called()

    def test_token__skip_token__validation_error(
        self,
        api_client,
        identify_mock,
        group_mock,
    ):
        # act
        response = api_client.get(
            path='/accounts/invites/token',
        )

        # assert
        assert response.status_code == 400
        message = 'This field is required.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        identify_mock.assert_not_called()
        group_mock.assert_not_called()

    def test_token__user_already_active__already_accepted_error(
        self,
        api_client,
        identify_mock,
        group_mock,
    ):
        # arrange
        account_owner = create_test_user()
        user = create_invited_user(account_owner)
        user.status = UserStatus.ACTIVE
        user.save(update_fields=['status'])
        invite_token = str(InviteToken.for_user(user))

        # act
        response = api_client.get(
            f'/accounts/invites/token?token={invite_token}',
        )

        # assert
        assert response.status_code == 400
        assert response.data['message'] == MSG_A_0007
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        identify_mock.assert_not_called()
        group_mock.assert_not_called()

    def test_token__user_already_registered__validation_error(
        self,
        api_client,
        identify_mock,
        group_mock,
    ):
        # arrange
        account_owner = create_test_user()
        email = 'existent@gmail.com'
        create_test_user(
            email=email,
            account=account_owner.account
        )
        user = create_invited_user(
            email=email,
            user=account_owner,
        )
        invite_token = str(InviteToken.for_user(user))

        # act
        response = api_client.get(
            f'/accounts/invites/token?token={invite_token}',
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == MSG_A_0005
        identify_mock.assert_not_called()
        group_mock.assert_not_called()


class TestAccept:

    def test_accept__all_fields__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        account_owner = create_test_user(account=account)
        user = create_invited_user(
            user=account_owner,
        )

        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        accept_mock = mocker.patch(
            'pneumatic_backend.accounts.services.UserInviteService.'
            'accept',
            return_value=user
        )
        token = '!@fghgh!@#'
        authenticate_mock = mocker.patch(
            'pneumatic_backend.authentication.services.AuthService'
            '.get_auth_token',
            return_value=token
        )
        current_url = 'https://my.pneumatic.app/team'
        user_agent = 'Some/Mozilla'
        user_ip = '128.18.0.99'
        data = {
            'first_name': 'Some',
            'last_name': 'Body',
            'password': '123123',
            'language': Language.de,
            'timezone': Timezone.UTC_8
        }

        # act
        response = api_client.post(
            f'/accounts/invites/{user.invite.id}/accept',
            data=data,
            HTTP_X_CURRENT_URL=current_url,
            HTTP_USER_AGENT=user_agent,
            HTTP_X_REAL_IP=user_ip
        )
        user.invite.refresh_from_db()
        user.refresh_from_db()

        # assert
        assert response.status_code == 200
        assert response.data['token'] == token
        service_mock.assert_called_once_with(
            current_url=current_url,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )
        accept_mock.assert_called_once_with(
            invite=user.invite,
            first_name=data['first_name'],
            last_name=data['last_name'],
            password=data['password'],
            language=data['language'],
            timezone=data['timezone'],
        )
        authenticate_mock.assert_called_once_with(
            user=user,
            user_agent=user_agent,
            user_ip=user_ip
        )

    def test_accept__required_fields__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        account_owner = create_test_user(account=account)
        user = create_invited_user(account_owner)

        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        accept_mock = mocker.patch(
            'pneumatic_backend.accounts.services.UserInviteService.'
            'accept',
            return_value=user
        )
        token = '!@fghgh!@#'
        authenticate_mock = mocker.patch(
            'pneumatic_backend.authentication.services.AuthService'
            '.get_auth_token',
            return_value=token
        )
        current_url = 'https://my.pneumatic.app/team'
        user_agent = 'Some/Mozilla'
        user_ip = '128.18.0.99'
        data = {
            'first_name': 'Some',
            'last_name': 'Body',
            'password': '123123'
        }

        # act
        response = api_client.post(
            f'/accounts/invites/{user.invite.id}/accept',
            data=data,
            HTTP_X_CURRENT_URL=current_url,
            HTTP_USER_AGENT=user_agent,
            HTTP_X_REAL_IP=user_ip
        )
        user.invite.refresh_from_db()
        user.refresh_from_db()

        # assert
        assert response.status_code == 200
        assert response.data['token'] == token
        service_mock.assert_called_once_with(
            current_url=current_url,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )
        accept_mock.assert_called_once_with(
            invite=user.invite,
            first_name=data['first_name'],
            last_name=data['last_name'],
            password=data['password'],
        )
        authenticate_mock.assert_called_once_with(
            user=user,
            user_agent=user_agent,
            user_ip=user_ip
        )

    @pytest.mark.parametrize('field', ('first_name', 'last_name', 'password'))
    def test_accept__skip_required_field__validation_error(
        self,
        field,
        mocker,
        api_client,
    ):
        # arrange
        account_owner = create_test_user()
        user = create_invited_user(account_owner)

        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        authenticate_mock = mocker.patch(
            'pneumatic_backend.authentication.services.AuthService'
            '.get_auth_token'
        )
        data = {
            'first_name': 'Mike',
            'last_name': 'Body',
            'password': '123123'
        }
        del data[field]

        # act
        response = api_client.post(
            f'/accounts/invites/{user.invite.id}/accept',
            data=data,
        )
        user.invite.refresh_from_db()
        user.refresh_from_db()

        # assert
        assert response.status_code == 400
        message = 'This field is required.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['name'] == field
        assert response.data['details']['reason'] == message

        service_mock.assert_not_called()
        authenticate_mock.assert_not_called()

    @pytest.mark.parametrize('field', ('first_name', 'last_name', 'password'))
    def test_accept__blank_required_field__validation_error(
        self,
        field,
        mocker,
        api_client,
    ):
        # arrange
        account_owner = create_test_user()
        user = create_invited_user(account_owner)
        data = {
            'first_name': 'Mike',
            'last_name': 'Body',
            'password': '123123'
        }
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        authenticate_mock = mocker.patch(
            'pneumatic_backend.authentication.services.AuthService'
            '.get_auth_token'
        )
        data[field] = ''

        # act
        response = api_client.post(
            f'/accounts/invites/{user.invite.id}/accept',
            data=data,
        )
        user.invite.refresh_from_db()
        user.refresh_from_db()

        # assert
        assert response.status_code == 400
        message = 'This field may not be blank.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['name'] == field
        assert response.data['details']['reason'] == message

        service_mock.assert_not_called()
        authenticate_mock.assert_not_called()

    @pytest.mark.parametrize('field', ('first_name', 'last_name', 'password'))
    def test_accept__null_required_field__validation_error(
        self,
        field,
        mocker,
        api_client,
    ):
        # arrange
        account_owner = create_test_user()
        user = create_invited_user(account_owner)
        data = {
            'first_name': 'Mike',
            'last_name': 'Body',
            'password': '123123'
        }
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        authenticate_mock = mocker.patch(
            'pneumatic_backend.authentication.services.AuthService'
            '.get_auth_token'
        )
        data[field] = None

        # act
        response = api_client.post(
            f'/accounts/invites/{user.invite.id}/accept',
            data=data,
        )
        user.invite.refresh_from_db()
        user.refresh_from_db()

        # assert
        assert response.status_code == 400
        message = 'This field may not be null.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['name'] == field
        assert response.data['details']['reason'] == message

        service_mock.assert_not_called()
        authenticate_mock.assert_not_called()

    def test_accept__short_password__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account_owner = create_test_user()
        user = create_invited_user(account_owner)
        data = {
            'first_name': 'Mike',
            'last_name': 'Body',
            'password': 'a'*5
        }
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        authenticate_mock = mocker.patch(
            'pneumatic_backend.authentication.services.AuthService'
            '.get_auth_token'
        )

        # act
        response = api_client.post(
            f'/accounts/invites/{user.invite.id}/accept',
            data=data,
        )
        user.invite.refresh_from_db()
        user.refresh_from_db()

        # assert
        assert response.status_code == 400
        message = 'Ensure this field has at least 6 characters.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['name'] == 'password'
        assert response.data['details']['reason'] == message

        service_mock.assert_not_called()
        authenticate_mock.assert_not_called()

    def test_accept__long_password__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account_owner = create_test_user()
        user = create_invited_user(account_owner)
        data = {
            'first_name': 'Mike',
            'last_name': 'Body',
            'password': 'a'*129
        }
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        authenticate_mock = mocker.patch(
            'pneumatic_backend.authentication.services.AuthService'
            '.get_auth_token'
        )

        # act
        response = api_client.post(
            f'/accounts/invites/{user.invite.id}/accept',
            data=data,
        )
        user.invite.refresh_from_db()
        user.refresh_from_db()

        # assert
        assert response.status_code == 400
        message = 'Ensure this field has no more than 128 characters.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['name'] == 'password'
        assert response.data['details']['reason'] == message

        service_mock.assert_not_called()
        authenticate_mock.assert_not_called()

    def test_accept__long_first_name__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account_owner = create_test_user()
        user = create_invited_user(account_owner)
        data = {
            'first_name': 'A'*31,
            'last_name': 'Body',
            'password': 'abcd123123'
        }
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        authenticate_mock = mocker.patch(
            'pneumatic_backend.authentication.services.AuthService'
            '.get_auth_token'
        )

        # act
        response = api_client.post(
            f'/accounts/invites/{user.invite.id}/accept',
            data=data,
        )
        user.invite.refresh_from_db()
        user.refresh_from_db()

        # assert
        assert response.status_code == 400
        message = 'Ensure this field has no more than 30 characters.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['name'] == 'first_name'
        assert response.data['details']['reason'] == message

        service_mock.assert_not_called()
        authenticate_mock.assert_not_called()

    def test_accept__long_last_name__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account_owner = create_test_user()
        user = create_invited_user(account_owner)
        data = {
            'first_name': 'A',
            'last_name': 'B'*151,
            'password': 'abcd123123'
        }
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        authenticate_mock = mocker.patch(
            'pneumatic_backend.authentication.services.AuthService'
            '.get_auth_token'
        )

        # act
        response = api_client.post(
            f'/accounts/invites/{user.invite.id}/accept',
            data=data,
        )
        user.invite.refresh_from_db()
        user.refresh_from_db()

        # assert
        assert response.status_code == 400
        message = 'Ensure this field has no more than 150 characters.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['name'] == 'last_name'
        assert response.data['details']['reason'] == message

        service_mock.assert_not_called()
        authenticate_mock.assert_not_called()

    def test_accept__timezone_is_null__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account_owner = create_test_user()
        user = create_invited_user(account_owner)
        data = {
            'first_name': 'Mike',
            'last_name': 'Body',
            'password': '123123',
            'timezone': None,
        }
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        authenticate_mock = mocker.patch(
            'pneumatic_backend.authentication.services.AuthService'
            '.get_auth_token'
        )

        # act
        response = api_client.post(
            f'/accounts/invites/{user.invite.id}/accept',
            data=data,
        )
        user.invite.refresh_from_db()
        user.refresh_from_db()

        # assert
        assert response.status_code == 400
        message = 'This field may not be null.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['name'] == 'timezone'
        assert response.data['details']['reason'] == message

        service_mock.assert_not_called()
        authenticate_mock.assert_not_called()

    def test_accept__language_is_null__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account_owner = create_test_user()
        user = create_invited_user(account_owner)
        data = {
            'first_name': 'Mike',
            'last_name': 'Body',
            'password': '123123',
            'language': None,
        }
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        authenticate_mock = mocker.patch(
            'pneumatic_backend.authentication.services.AuthService'
            '.get_auth_token'
        )

        # act
        response = api_client.post(
            f'/accounts/invites/{user.invite.id}/accept',
            data=data,
        )
        user.invite.refresh_from_db()
        user.refresh_from_db()

        # assert
        assert response.status_code == 400
        message = 'This field may not be null.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['name'] == 'language'
        assert response.data['details']['reason'] == message

        service_mock.assert_not_called()
        authenticate_mock.assert_not_called()

    def test_accept__timezone_blank__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account_owner = create_test_user()
        user = create_invited_user(account_owner)
        data = {
            'first_name': 'Mike',
            'last_name': 'Body',
            'password': '123123',
            'timezone': '',
        }
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        authenticate_mock = mocker.patch(
            'pneumatic_backend.authentication.services.AuthService'
            '.get_auth_token'
        )

        # act
        response = api_client.post(
            f'/accounts/invites/{user.invite.id}/accept',
            data=data,
        )
        user.invite.refresh_from_db()
        user.refresh_from_db()

        # assert
        assert response.status_code == 400
        message = '"" is not a valid choice.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['name'] == 'timezone'
        assert response.data['details']['reason'] == message

        service_mock.assert_not_called()
        authenticate_mock.assert_not_called()

    def test_accept__language_blank__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account_owner = create_test_user()
        user = create_invited_user(account_owner)
        data = {
            'first_name': 'Mike',
            'last_name': 'Body',
            'password': '123123',
            'language': '',
        }
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        authenticate_mock = mocker.patch(
            'pneumatic_backend.authentication.services.AuthService'
            '.get_auth_token'
        )

        # act
        response = api_client.post(
            f'/accounts/invites/{user.invite.id}/accept',
            data=data,
        )
        user.invite.refresh_from_db()
        user.refresh_from_db()

        # assert
        assert response.status_code == 400
        message = '"" is not a valid choice.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['name'] == 'language'
        assert response.data['details']['reason'] == message

        service_mock.assert_not_called()
        authenticate_mock.assert_not_called()

    def test_accept__already_registered__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account_owner = create_test_user()
        user = create_invited_user(account_owner)
        data = {
            'first_name': 'User',
            'last_name': 'Buster',
            'password': 'abcd123123'
        }
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        accept_mock = mocker.patch(
            'pneumatic_backend.accounts.services.UserInviteService.'
            'accept',
            side_effect=AlreadyRegisteredException()
        )
        authenticate_mock = mocker.patch(
            'pneumatic_backend.authentication.services.AuthService'
            '.get_auth_token'
        )
        current_url = 'https://my.pneumatic.app/team'

        # act
        response = api_client.post(
            f'/accounts/invites/{user.invite.id}/accept',
            data=data,
            HTTP_X_CURRENT_URL=current_url,
        )
        user.invite.refresh_from_db()
        user.refresh_from_db()

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == MSG_A_0005
        service_mock.assert_called_once_with(
            current_url=current_url,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )
        accept_mock.assert_called_once_with(
            invite=user.invite,
            first_name=data['first_name'],
            last_name=data['last_name'],
            password=data['password'],
        )
        authenticate_mock.assert_not_called()


class TestRetrieve:

    def test_retrieve(self, api_client):
        # arrange
        account_owner = create_test_user()
        user = create_invited_user(account_owner)
        invite = user.invite

        # act
        response = api_client.get(f'/accounts/invites/{str(invite.id)}')

        # assert
        assert response.status_code == 200
        assert response.data['id'] == str(invite.id)


class TestList:

    def test_list__ok(self, api_client):
        account_owner = create_test_user()
        user = create_invited_user(account_owner)
        api_client.token_authenticate(account_owner)
        response = api_client.get('/accounts/invites?status=pending')
        assert response.status_code == 200
        assert response.data[0]['id'] == str(user.invite.id)


class TestResend:

    def test_resend__ok(self, mocker, api_client):

        # arrange
        user = create_test_user()
        invited_user_id = '1'
        current_url = 'https://my.pneumatic.app/team'
        api_client.token_authenticate(user)
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        resend_mock = mocker.patch(
            'pneumatic_backend.accounts.services.UserInviteService.'
            'resend_invite'
        )

        # act
        response = api_client.post(
            f'/accounts/invites/{invited_user_id}/resend',
            HTTP_X_CURRENT_URL=current_url,
        )

        # assert
        assert response.status_code == 204
        service_mock.assert_called_once_with(
            is_superuser=False,
            request_user=user,
            current_url=current_url
        )
        resend_mock.assert_called_once_with(user_id=invited_user_id)

    def test_resend__already_accepted__validation_error(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        invited_user_id = '1'
        current_url = 'https://my.pneumatic.app/team'
        api_client.token_authenticate(user)
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        resend_mock = mocker.patch(
            'pneumatic_backend.accounts.services.UserInviteService.'
            'resend_invite',
            side_effect=AlreadyAcceptedInviteException()
        )

        # act
        response = api_client.post(
            f'/accounts/invites/{invited_user_id}/resend',
            HTTP_X_CURRENT_URL=current_url,
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == MSG_A_0007
        service_mock.assert_called_once_with(
            is_superuser=False,
            request_user=user,
            current_url=current_url
        )
        resend_mock.assert_called_once_with(user_id=invited_user_id)

    def test_resend__user_not_found__not_found(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        invited_user_id = '1'
        current_url = 'https://my.pneumatic.app/team'
        api_client.token_authenticate(user)
        service_mock = mocker.patch.object(
            UserInviteService,
            '__init__',
            return_value=None
        )
        resend_mock = mocker.patch(
            'pneumatic_backend.accounts.services.UserInviteService.'
            'resend_invite',
            side_effect=UserNotFoundException()
        )

        # act
        response = api_client.post(
            f'/accounts/invites/{invited_user_id}/resend',
            HTTP_X_CURRENT_URL=current_url,
        )

        # assert
        assert response.status_code == 404
        service_mock.assert_called_once_with(
            is_superuser=False,
            request_user=user,
            current_url=current_url
        )
        resend_mock.assert_called_once_with(user_id=invited_user_id)
