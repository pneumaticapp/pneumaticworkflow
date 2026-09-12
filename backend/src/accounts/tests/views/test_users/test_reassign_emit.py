import pytest

from src.accounts.messages import MSG_A_0004
from src.accounts.services.exceptions import ReassignUserSameUser
from src.accounts.services.reassign import ReassignService
from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_not_admin,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_reassign__user_to_user__emit_user_reassign(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    old_user = create_test_not_admin(
        account=account,
        email='old@test.test',
    )
    new_user = create_test_not_admin(
        account=account,
        email='new@test.test',
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
    api_client.token_authenticate(
        owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.11',
    )

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={'old_user': old_user.id, 'new_user': new_user.id},
        format='json',
    )

    # assert
    assert response.status_code == 204
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_REASSIGN
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=old_user.id,
    )
    assert event.payload == {
        'old_user_id': old_user.id,
        'old_group_id': None,
        'new_user_id': new_user.id,
        'new_group_id': None,
    }
    assert event.ip == '10.10.0.11'
    assert event.user_agent == 'Chrome/141'
    reassign_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        request_user=owner,
        old_user=old_user,
        new_user=new_user,
    )
    reassign_everywhere_mock.assert_called_once_with()


def test_reassign__group_to_group__emit_group_object(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    old_group = create_test_group(
        account=account,
        name='old',
    )
    new_group = create_test_group(
        account=account,
        name='new',
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
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={'old_group': old_group.id, 'new_group': new_group.id},
        format='json',
    )

    # assert
    assert response.status_code == 204
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_REASSIGN
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.GROUP,
        id=old_group.id,
    )
    assert event.payload == {
        'old_user_id': None,
        'old_group_id': old_group.id,
        'new_user_id': None,
        'new_group_id': new_group.id,
    }
    reassign_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        request_user=owner,
        old_group=old_group,
        new_group=new_group,
    )
    reassign_everywhere_mock.assert_called_once_with()


def test_reassign__user_to_group__emit_user_object(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    old_user = create_test_not_admin(account=account)
    new_group = create_test_group(account=account)
    reassign_service_init_mock = mocker.patch.object(
        ReassignService,
        attribute='__init__',
        return_value=None,
    )
    reassign_everywhere_mock = mocker.patch.object(
        ReassignService,
        attribute='reassign_everywhere',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={'old_user': old_user.id, 'new_group': new_group.id},
        format='json',
    )

    # assert
    assert response.status_code == 204
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_REASSIGN
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=old_user.id,
    )
    assert event.payload == {
        'old_user_id': old_user.id,
        'old_group_id': None,
        'new_user_id': None,
        'new_group_id': new_group.id,
    }
    reassign_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        request_user=owner,
        old_user=old_user,
        new_group=new_group,
    )
    reassign_everywhere_mock.assert_called_once_with()


def test_reassign__service_exception__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    old_user = create_test_not_admin(
        account=account,
        email='old@test.test',
    )
    new_user = create_test_not_admin(
        account=account,
        email='new@test.test',
    )
    reassign_service_init_mock = mocker.patch.object(
        ReassignService,
        attribute='__init__',
        return_value=None,
    )
    reassign_everywhere_mock = mocker.patch.object(
        ReassignService,
        attribute='reassign_everywhere',
        side_effect=ReassignUserSameUser(),
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={'old_user': old_user.id, 'new_user': new_user.id},
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_A_0004
    assert response.data['details'] == {}
    assert fake_stream.events == []
    reassign_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        request_user=owner,
        old_user=old_user,
        new_user=new_user,
    )
    reassign_everywhere_mock.assert_called_once_with()


def test_reassign__invalid_old_user__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    new_user = create_test_not_admin(account=account)
    reassign_service_init_mock = mocker.patch.object(
        ReassignService,
        attribute='__init__',
        return_value=None,
    )
    reassign_everywhere_mock = mocker.patch.object(
        ReassignService,
        attribute='reassign_everywhere',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={'old_user': 'invalid-id', 'new_user': new_user.id},
        format='json',
    )

    # assert
    message = 'Incorrect type. Expected pk value, received str.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'old_user'
    assert response.data['details']['reason'] == message
    assert fake_stream.events == []
    reassign_service_init_mock.assert_not_called()
    reassign_everywhere_mock.assert_not_called()
