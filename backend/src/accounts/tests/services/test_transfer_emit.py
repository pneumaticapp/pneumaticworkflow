import pytest

from src.accounts.services.reassign import ReassignService
from src.accounts.services.user import UserService
from src.accounts.services.user_transfer import UserTransferService
from src.accounts.tokens import TransferToken
from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_account,
    create_test_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_accept_transfer__valid_token__audit_user_transferred(mocker):

    # arrange
    prev_account = create_test_account(name='prev')
    prev_user = create_test_owner(
        account=prev_account,
        email='transferred@test.test',
    )
    new_account = create_test_account(name='new')
    new_account_owner = create_test_owner(account=new_account)
    new_user = create_invited_user(
        user=new_account_owner,
        email='transferred@test.test',
    )
    token = TransferToken()
    token['prev_user_id'] = prev_user.id
    token['new_user_id'] = new_user.id
    get_valid_token_mock = mocker.patch.object(
        UserTransferService,
        attribute='_get_valid_token',
        return_value=token,
    )
    get_valid_user_mock = mocker.patch.object(
        UserTransferService,
        attribute='_get_valid_user',
        return_value=new_user,
    )
    get_valid_prev_user_mock = mocker.patch.object(
        UserTransferService,
        attribute='_get_valid_prev_user',
        return_value=prev_user,
    )
    deactivate_prev_user_mock = mocker.patch.object(
        UserTransferService,
        attribute='_deactivate_prev_user',
    )
    activate_user_mock = mocker.patch.object(
        UserTransferService,
        attribute='_activate_user',
    )
    after_transfer_actions_mock = mocker.patch.object(
        UserTransferService,
        attribute='_after_transfer_actions',
    )
    user_transferred_mock = mocker.patch(
        'src.accounts.services.user_transfer.AuditEventService.'
        'user_transferred',
    )
    service = UserTransferService()

    # act
    service.accept_transfer(
        user_id=new_user.id,
        token_str=str(token),
    )

    # assert
    user_transferred_mock.assert_called_once_with(
        user=new_user,
        auth_type=AuthTokenType.USER,
        prev_user=prev_user,
    )
    get_valid_token_mock.assert_called_once_with(str(token))
    get_valid_user_mock.assert_called_once_with(new_user.id)
    get_valid_prev_user_mock.assert_called_once_with()
    deactivate_prev_user_mock.assert_called_once_with()
    activate_user_mock.assert_called_once_with()
    after_transfer_actions_mock.assert_called_once_with()


def test_accept_transfer__activation_failed__audit_not_called(mocker):

    # arrange
    prev_account = create_test_account(name='prev')
    prev_user = create_test_owner(
        account=prev_account,
        email='transferred@test.test',
    )
    new_account = create_test_account(name='new')
    new_user = create_invited_user(
        user=create_test_owner(account=new_account),
        email='transferred@test.test',
    )
    token = TransferToken()
    get_valid_token_mock = mocker.patch.object(
        UserTransferService,
        attribute='_get_valid_token',
        return_value=token,
    )
    get_valid_user_mock = mocker.patch.object(
        UserTransferService,
        attribute='_get_valid_user',
        return_value=new_user,
    )
    get_valid_prev_user_mock = mocker.patch.object(
        UserTransferService,
        attribute='_get_valid_prev_user',
        return_value=prev_user,
    )
    deactivate_prev_user_mock = mocker.patch.object(
        UserTransferService,
        attribute='_deactivate_prev_user',
    )
    activate_user_mock = mocker.patch.object(
        UserTransferService,
        attribute='_activate_user',
        side_effect=ValueError('broken'),
    )
    user_transferred_mock = mocker.patch(
        'src.accounts.services.user_transfer.AuditEventService.'
        'user_transferred',
    )
    service = UserTransferService()

    # act
    with pytest.raises(ValueError) as ex:
        service.accept_transfer(
            user_id=new_user.id,
            token_str='token',
        )

    # assert
    assert str(ex.value) == 'broken'
    user_transferred_mock.assert_not_called()
    get_valid_token_mock.assert_called_once_with('token')
    get_valid_user_mock.assert_called_once_with(new_user.id)
    get_valid_prev_user_mock.assert_called_once_with()
    deactivate_prev_user_mock.assert_called_once_with()
    activate_user_mock.assert_called_once_with()


def test_deactivate_prev_user__user_left__reassign_actor_prev_user(mocker):

    """ The reassignment happens in the account the person leaves, and
        there they are the previous user: a vacation it switches off is
        journalled as their doing. """

    # arrange
    prev_account = create_test_account(name='prev')
    prev_owner = create_test_owner(account=prev_account)
    prev_user = create_test_admin(
        account=prev_account,
        email='transferred@test.test',
    )
    reassign_service_init_mock = mocker.patch.object(
        ReassignService,
        attribute='__init__',
        return_value=None,
    )
    reassign_everywhere_mock = mocker.patch.object(
        ReassignService,
        attribute='reassign_everywhere',
    )
    remove_user_from_draft_mock = mocker.patch(
        'src.accounts.services.user_transfer.remove_user_from_draft',
    )
    deactivate_mock = mocker.patch.object(
        UserService,
        attribute='deactivate',
    )
    service = UserTransferService()
    service.prev_user = prev_user

    # act
    service._deactivate_prev_user()

    # assert
    reassign_service_init_mock.assert_called_once_with(
        old_user=prev_user,
        new_user=prev_owner,
        request_user=prev_user,
    )
    reassign_everywhere_mock.assert_called_once_with()
    remove_user_from_draft_mock.assert_called_once_with(
        account_id=prev_account.id,
        user_id=prev_user.id,
    )
    deactivate_mock.assert_called_once_with(skip_validation=True)
