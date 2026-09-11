import pytest

from src.accounts.services.user_transfer import UserTransferService
from src.accounts.tokens import TransferToken
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_account,
    create_test_user,
)

pytestmark = pytest.mark.django_db


def test_accept_transfer__valid_token__emit_in_the_new_account(
    mocker,
    fake_stream,
):

    """ The record goes to the account the person arrived in and
        names the account left behind; that account has its own
        user.deactivate from the deactivation of the previous user. """

    # arrange
    prev_account = create_test_account(name='prev')
    prev_user = create_test_user(
        account=prev_account,
        email='transferred@test.test',
    )
    new_account = create_test_account(name='new')
    new_account_owner = create_test_user(account=new_account)
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
    service = UserTransferService()

    # act
    service.accept_transfer(user_id=new_user.id, token_str=str(token))

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_TRANSFER
    assert event.category == EventCategory.AUDIT
    assert event.account_id == new_account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=new_user.id,
        email='transferred@test.test',
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=new_user.id,
    )
    assert event.payload == {
        'prev_account_id': prev_account.id,
        'prev_user_id': prev_user.id,
    }
    get_valid_token_mock.assert_called_once_with(str(token))
    get_valid_user_mock.assert_called_once_with(new_user.id)
    get_valid_prev_user_mock.assert_called_once_with()
    deactivate_prev_user_mock.assert_called_once_with()
    activate_user_mock.assert_called_once_with()
    after_transfer_actions_mock.assert_called_once_with()


def test_accept_transfer__activation_failed__no_event(
    mocker,
    fake_stream,
):

    # arrange
    prev_account = create_test_account(name='prev')
    prev_user = create_test_user(
        account=prev_account,
        email='transferred@test.test',
    )
    new_account = create_test_account(name='new')
    new_user = create_invited_user(
        user=create_test_user(account=new_account),
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
    service = UserTransferService()

    # act
    with pytest.raises(ValueError):
        service.accept_transfer(user_id=new_user.id, token_str='token')

    # assert
    assert fake_stream.events == []
    get_valid_token_mock.assert_called_once_with('token')
    get_valid_user_mock.assert_called_once_with(new_user.id)
    get_valid_prev_user_mock.assert_called_once_with()
    deactivate_prev_user_mock.assert_called_once_with()
    activate_user_mock.assert_called_once_with()
