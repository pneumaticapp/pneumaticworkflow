import pytest

from src.accounts.enums import BillingPlanType, SourceType, UserStatus
from src.accounts.models import UserInvite
from src.accounts.services.exceptions import (
    AlreadyAcceptedInviteException,
    UsersLimitInvitesException,
)
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
    create_test_not_admin,
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
    assert event.object == EventObject(type=EventObjectType.INVITE)
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
    assert event.object == EventObject(type=EventObjectType.INVITE)
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
    assert event.object == EventObject(type=EventObjectType.INVITE)
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
    assert event.object == EventObject(type=EventObjectType.INVITE)
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


def test_invite_user__users_limit__no_event(
    mocker,
    fake_stream,
):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    owner = create_test_owner(account=account)
    account.max_users = 1
    account.max_invites = 1
    account.active_users = 1
    account.save()
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
    with pytest.raises(UsersLimitInvitesException):
        service.invite_user(
            email='invited@test.test',
            invited_from=SourceType.EMAIL,
        )

    # assert
    assert fake_stream.events == []
    user_create_actions_mock.assert_not_called()
    user_invite_actions_mock.assert_not_called()


def test_resend_invite__already_accepted__no_event(
    mocker,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    user_invite_actions_mock = mocker.patch.object(
        UserInviteService,
        attribute='_user_invite_actions',
    )
    service = UserInviteService(request_user=owner)

    # act
    with pytest.raises(AlreadyAcceptedInviteException):
        service.resend_invite(user_id=user.id)

    # assert
    assert fake_stream.events == []
    user_invite_actions_mock.assert_not_called()


def test_accept__sso_callback__emit_invite_accept(
    mocker,
    fake_stream,
):

    """ An invite accepted through an SSO callback never touches the
        endpoint: the event has to come from the service, which is the
        one thing both ways in have in common. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invited = create_invited_user(user=owner)
    invite = invited.invite
    create_onboarding_workflows_mock = mocker.patch(
        'src.processes.services.system_workflows.SystemWorkflowService'
        '.create_onboarding_workflows',
    )
    create_activated_workflows_mock = mocker.patch(
        'src.processes.services.system_workflows.SystemWorkflowService'
        '.create_activated_workflows',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user_invite.send_user_updated_notification'
        '.delay',
    )
    users_joined_mock = mocker.patch(
        'src.accounts.services.user_invite.AnalyticService.users_joined',
    )
    identify_mock = mocker.patch.object(
        UserInviteService,
        attribute='identify',
    )
    group_mock = mocker.patch.object(
        UserInviteService,
        attribute='group',
    )
    service = UserInviteService(
        request_user=invited,
        current_url='',
        send_email=False,
    )

    # act
    service.accept(
        invite=invite,
        first_name='Some',
        last_name='Body',
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.INVITE_ACCEPT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=invited.id,
        email=invited.email,
    )
    assert event.object == EventObject(type=EventObjectType.INVITE)
    assert event.payload == {'invited_by_id': owner.id}
    create_onboarding_workflows_mock.assert_called_once_with()
    create_activated_workflows_mock.assert_called_once_with()
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )
    users_joined_mock.assert_called_once_with(invited)
    identify_mock.assert_called_once_with(invited)
    group_mock.assert_called_once_with(invited)


def test_decline__invited_user__emit_actor_is_the_invited_user(
    mocker,
    identify_mock,
    group_mock,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invited = create_invited_user(user=owner)
    identify_users_mock = mocker.patch(
        'src.accounts.services.account.identify_users.delay',
    )
    send_user_deactivated_mock = mocker.patch(
        'src.notifications.tasks.send_user_deactivated_notification.delay',
    )
    send_user_deleted_mock = mocker.patch(
        'src.notifications.tasks.send_user_deleted_notification.delay',
    )
    emit_mock = mocker.patch('src.logs.events.mixins.emit')
    service = UserInviteService(request_user=invited)

    # act
    service.decline(invited.invite)

    # assert
    emit_mock.assert_called_once_with(
        EventName.USER_DEACTIVATE,
        account_id=account.id,
        actor=Actor(
            type=ActorType.USER,
            id=invited.id,
            email=invited.email,
        ),
        event_object=EventObject(type=EventObjectType.USER, id=invited.id),
        payload={
            'target_email': invited.email,
            'status_before': UserStatus.INVITED,
        },
    )
    identify_mock.assert_called_once_with(invited)
    identify_users_mock.assert_called_once_with(user_ids=(owner.id,))
    group_mock.assert_called_once_with(user=invited, account=account)

    # An invited person never signed in: no deactivation email.
    send_user_deactivated_mock.assert_not_called()
    send_user_deleted_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )
