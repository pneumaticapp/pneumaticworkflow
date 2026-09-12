import pytest

from src.accounts.services.exceptions import (
    AlreadyRegisteredException,
)
from src.accounts.services.user_invite import UserInviteService
from src.accounts.messages import MSG_A_0005
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
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_accept__invited_user__emit_invite_accept(
    mocker,
    api_client,
):

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
    emit_mock = mocker.patch('src.logs.events.mixins.emit')

    # act
    response = api_client.post(
        path=f'/accounts/invites/{invite.id}/accept',
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
        account_id=account.id,
        actor=Actor(
            type=ActorType.USER,
            id=invited.id,
            email=invited.email,
        ),
        event_object=EventObject(
            type=EventObjectType.INVITE,
            id=str(invite.id),
        ),
        payload={'invited_by_id': owner.id},
    )
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
    assert event.object == EventObject(
        type=EventObjectType.INVITE,
        id=str(invite.id),
    )
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
    emit_mock = mocker.patch('src.logs.events.mixins.emit')

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
    assert response.data['message'] == MSG_A_0005
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
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
    fake_stream,
):

    """ The endpoint is open, so the actor cannot come from the
        request: the event has to name the invited person and still
        carry the address and the browser of the attempt. """

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

    # act
    response = api_client.post(
        path=f'/accounts/invites/{invite.id}/accept',
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
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=invited.id,
        email=invited.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.INVITE,
        id=str(invite.id),
    )
    assert event.payload == {'invited_by_id': owner.id}
    assert event.ip == '10.10.0.9'
    assert event.user_agent == 'Safari/18'
    assert event.request_id == 'audit-invite-1'
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
