import pytest

from src.accounts.services.exceptions import (
    AlreadyRegisteredException,
)
from src.logs.events.enums import (
    ActorType,
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


def test_accept__invited_user__emit_invite_accept(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invited = create_invited_user(user=owner)
    accept_mock = mocker.patch(
        'src.accounts.services.user_invite.UserInviteService.accept',
        return_value=invited,
    )
    auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.AuthService'
        '.get_auth_token',
        return_value='token-value',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    response = api_client.post(
        path=f'/accounts/invites/{invited.invite.id}/accept',
        data={
            'first_name': 'Some',
            'last_name': 'Body',
            'password': 'secret-123',
        },
    )

    # assert
    assert response.status_code == 200
    emit_mock.assert_called_once_with(
        EventName.INVITE_ACCEPT,
        account_id=invited.account_id,
        actor=Actor(
            type=ActorType.USER,
            id=invited.id,
            email=invited.email,
        ),
        event_object=EventObject(
            type=EventObjectType.INVITE,
            id=str(invited.invite.id),
        ),
        payload={'invited_by_id': owner.id},
        request=mocker.ANY,
    )
    accept_mock.assert_called_once_with(
        invite=invited.invite,
        first_name='Some',
        last_name='Body',
        password='secret-123',
    )
    auth_token_mock.assert_called_once_with(
        user=invited,
        user_agent='Mozilla/5.0',
        user_ip=None,
    )


def test_accept__already_registered__no_event(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invited = create_invited_user(user=owner)
    accept_mock = mocker.patch(
        'src.accounts.services.user_invite.UserInviteService.accept',
        side_effect=AlreadyRegisteredException(),
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    response = api_client.post(
        path=f'/accounts/invites/{invited.invite.id}/accept',
        data={
            'first_name': 'Some',
            'last_name': 'Body',
            'password': 'secret-123',
        },
    )

    # assert
    assert response.status_code == 400
    emit_mock.assert_not_called()
    accept_mock.assert_called_once_with(
        invite=invited.invite,
        first_name='Some',
        last_name='Body',
        password='secret-123',
    )


def test_accept__anonymous_request__event_keeps_request_context(
    mocker,
    api_client,
    events_enabled,
    run_on_commit,
    fake_stream,
):

    """ The endpoint is open, so the actor cannot come from the
        request: the event has to name the invited person and still
        carry the address and the browser of the attempt. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invited = create_invited_user(user=owner)
    accept_mock = mocker.patch(
        'src.accounts.services.user_invite.UserInviteService.accept',
        return_value=invited,
    )
    auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.AuthService'
        '.get_auth_token',
        return_value='token-value',
    )

    # act
    response = api_client.post(
        path=f'/accounts/invites/{invited.invite.id}/accept',
        data={
            'first_name': 'Some',
            'last_name': 'Body',
            'password': 'secret-123',
        },
        HTTP_X_REAL_IP='10.10.0.9',
        HTTP_USER_AGENT='Safari/18',
        HTTP_X_REQUEST_ID='audit-invite-1',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.INVITE_ACCEPT
    assert event.account_id == invited.account_id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=invited.id,
        email=invited.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.INVITE,
        id=str(invited.invite.id),
    )
    assert event.payload == {'invited_by_id': owner.id}
    assert event.ip == '10.10.0.9'
    assert event.user_agent == 'Safari/18'
    assert event.request_id == 'audit-invite-1'
    accept_mock.assert_called_once_with(
        invite=invited.invite,
        first_name='Some',
        last_name='Body',
        password='secret-123',
    )
    auth_token_mock.assert_called_once_with(
        user=invited,
        user_agent='Safari/18',
        user_ip='10.10.0.9',
    )
