import pytest

from src.accounts.enums import SourceType
from src.accounts.models import UserInvite
from src.accounts.services.user_invite import UserInviteService
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
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_invite_user__new_person__emit_invite_create(
    mocker,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user_create_actions_mock = mocker.patch.object(
        UserInviteService,
        attribute='_user_create_actions',
    )
    user_invite_actions_mock = mocker.patch.object(
        UserInviteService,
        attribute='_user_invite_actions',
    )
    service = UserInviteService(request_user=owner)

    # act
    service.invite_user(
        email='invited@test.test',
        invited_from=SourceType.EMAIL,
    )

    # assert
    invite = UserInvite.objects.get(email='invited@test.test')
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.INVITE_CREATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.INVITE,
        id=str(invite.id),
    )
    assert event.payload == {
        'target_email': 'invited@test.test',
        'invited_user_id': invite.invited_user_id,
        'is_transfer': False,
    }
    user_create_actions_mock.assert_called_once_with(invite.invited_user)
    user_invite_actions_mock.assert_called_once_with(invite.invited_user)


def test_invite_user__person_of_another_account__emit_transfer_invite(
    mocker,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    other_account = create_test_account(name='Other')
    other_user = create_test_owner(
        account=other_account,
        email='moving@test.test',
    )
    user_create_actions_mock = mocker.patch.object(
        UserInviteService,
        attribute='_user_create_actions',
    )
    user_transfer_actions_mock = mocker.patch.object(
        UserInviteService,
        attribute='_user_transfer_actions',
    )
    send_transfer_email_mock = mocker.patch.object(
        UserInviteService,
        attribute='_send_transfer_email',
    )
    service = UserInviteService(request_user=owner)

    # act
    service.invite_user(
        email='moving@test.test',
        invited_from=SourceType.EMAIL,
    )

    # assert
    invite = UserInvite.objects.get(account=account, email='moving@test.test')
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.INVITE_CREATE
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.INVITE,
        id=str(invite.id),
    )
    assert event.payload == {
        'target_email': 'moving@test.test',
        'invited_user_id': invite.invited_user_id,
        'is_transfer': True,
    }
    user_create_actions_mock.assert_called_once_with(invite.invited_user)
    user_transfer_actions_mock.assert_called_once_with(
        current_account_user=invite.invited_user,
        another_account_user=other_user,
    )
    send_transfer_email_mock.assert_called_once_with(
        current_account_user=invite.invited_user,
        another_account_user=other_user,
    )


def test_invite_user__already_invited__no_event(
    mocker,
    fake_stream,
):

    """ Inviting a person who has a pending invite creates nothing,
        so the journal gets nothing either. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    create_invited_user(user=owner, email='invited@test.test')
    user_create_actions_mock = mocker.patch.object(
        UserInviteService,
        attribute='_user_create_actions',
    )
    service = UserInviteService(request_user=owner)

    # act
    service.invite_user(
        email='invited@test.test',
        invited_from=SourceType.EMAIL,
    )

    # assert
    assert fake_stream.events == []
    user_create_actions_mock.assert_not_called()


def test_resend_invite__invited_person__emit_invite_resend(
    mocker,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invited = create_invited_user(user=owner, email='invited@test.test')
    user_invite_actions_mock = mocker.patch.object(
        UserInviteService,
        attribute='_user_invite_actions',
    )
    service = UserInviteService(request_user=owner)

    # act
    service.resend_invite(user_id=invited.id)

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.INVITE_RESEND
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.INVITE,
        id=str(invited.invite.id),
    )
    assert event.payload == {
        'target_email': 'invited@test.test',
        'invited_user_id': invited.id,
        'is_transfer': False,
    }
    user_invite_actions_mock.assert_called_once_with(invited)


def test_resend_invite__person_of_another_account__transfer_resent(
    mocker,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invited = create_invited_user(user=owner, email='moving@test.test')
    other_account = create_test_account(name='Other')
    other_user = create_test_owner(
        account=other_account,
        email='moving@test.test',
    )
    send_transfer_email_mock = mocker.patch.object(
        UserInviteService,
        attribute='_send_transfer_email',
    )
    user_transfer_actions_mock = mocker.patch.object(
        UserInviteService,
        attribute='_user_transfer_actions',
    )
    service = UserInviteService(request_user=owner)

    # act
    service.resend_invite(user_id=invited.id)

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.INVITE_RESEND
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.INVITE,
        id=str(invited.invite.id),
    )
    assert event.payload == {
        'target_email': 'moving@test.test',
        'invited_user_id': invited.id,
        'is_transfer': True,
    }
    send_transfer_email_mock.assert_called_once_with(
        current_account_user=invited,
        another_account_user=other_user,
    )
    user_transfer_actions_mock.assert_called_once_with(
        current_account_user=invited,
        another_account_user=other_user,
    )
