from datetime import date

import pytest

from src.accounts.enums import AbsenceStatus
from src.accounts.models import UserVacation
from src.accounts.services.vacation import VacationDelegationService
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
    create_test_admin,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
    create_test_vacation,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_activate__new_vacation__emit_vacation_activate(
    mocker,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    substitute_1 = create_test_admin(
        account=account,
        email='s1@test.test',
    )
    substitute_2 = create_test_admin(
        account=account,
        email='s2@test.test',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    send_delegation_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_vacation_delegation_notification.delay',
    )
    service = VacationDelegationService(
        user=user,
        request_user=owner,
    )

    # act
    service.activate(
        substitute_user_ids=[substitute_2.id, substitute_1.id],
        absence_status=AbsenceStatus.SICK_LEAVE,
        vacation_start_date=date(2026, 9, 1),
        vacation_end_date=date(2026, 9, 20),
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_VACATION_ACTIVATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {
        'target_email': user.email,
        'substitute_user_ids': [substitute_1.id, substitute_2.id],
        'absence_status': AbsenceStatus.SICK_LEAVE,
        'start_date': '2026-09-01',
        'end_date': '2026-09-20',
        'delegated_tasks_count': 0,
        'is_update': False,
    }
    assert event.pii == ('actor.email', 'payload.target_email')
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )
    send_delegation_mock.assert_not_called()


def test_activate__active_task_without_delegation__emit_delegated_count(
    mocker,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    substitute = create_test_not_admin(account=account)
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    schedule_sync_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'schedule_sync_workflow_attachment_permissions',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    send_delegation_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_vacation_delegation_notification.delay',
    )
    service = VacationDelegationService(
        user=owner,
        request_user=admin,
    )

    # act
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_VACATION_ACTIVATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=admin.id,
        email=admin.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=owner.id,
    )
    assert event.payload == {
        'target_email': owner.email,
        'substitute_user_ids': [substitute.id],
        'absence_status': AbsenceStatus.VACATION,
        'start_date': None,
        'end_date': None,
        'delegated_tasks_count': 1,
        'is_update': False,
    }
    task_delegation_event_mock.assert_called_once_with(
        task=workflow.tasks.get(number=1),
        user=owner,
        substitute_group=mocker.ANY,
    )
    schedule_sync_mock.assert_called_once_with(workflow.id)
    send_delegation_mock.assert_called_once_with(
        user_id=substitute.id,
        user_email=substitute.email,
        user_first_name=substitute.first_name,
        account_id=account.id,
        tasks_count=1,
        vacation_owner_name=owner.get_full_name(),
    )
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_activate__existing_vacation__emit_is_update_true(
    mocker,
    fake_stream,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    substitute_1 = create_test_admin(
        account=account,
        email='s1@test.test',
    )
    substitute_2 = create_test_admin(
        account=account,
        email='s2@test.test',
    )
    create_test_vacation(
        user=user,
        substitutes=[substitute_1],
        start_date=date(2099, 1, 1),
        absence_status=AbsenceStatus.ACTIVE,
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    send_delegation_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_vacation_delegation_notification.delay',
    )
    service = VacationDelegationService(
        user=user,
        request_user=user,
    )

    # act
    service.activate(
        substitute_user_ids=[substitute_2.id],
        vacation_end_date=date(2099, 2, 1),
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_VACATION_ACTIVATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=user.id,
        email=user.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {
        'target_email': user.email,
        'substitute_user_ids': [substitute_2.id],
        'absence_status': AbsenceStatus.VACATION,
        'start_date': None,
        'end_date': '2099-02-01',
        'delegated_tasks_count': 0,
        'is_update': True,
    }
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )
    send_delegation_mock.assert_not_called()


def test_activate__no_request_user__emit_system_actor(
    mocker,
    fake_stream,
):

    """ A scheduled task turns the vacation on for nobody. """

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    substitute = create_test_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    send_delegation_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_vacation_delegation_notification.delay',
    )
    service = VacationDelegationService(user=user)

    # act
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_VACATION_ACTIVATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(type=ActorType.SYSTEM)
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {
        'target_email': user.email,
        'substitute_user_ids': [substitute.id],
        'absence_status': AbsenceStatus.VACATION,
        'start_date': None,
        'end_date': None,
        'delegated_tasks_count': 0,
        'is_update': False,
    }
    assert event.pii == ('payload.target_email',)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )
    send_delegation_mock.assert_not_called()


def test_activate__api_key_auth__emit_api_key_actor(
    mocker,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    substitute = create_test_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    send_delegation_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_vacation_delegation_notification.delay',
    )
    service = VacationDelegationService(
        user=user,
        request_user=owner,
        auth_type=AuthTokenType.API,
    )

    # act
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_VACATION_ACTIVATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.API_KEY,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {
        'target_email': user.email,
        'substitute_user_ids': [substitute.id],
        'absence_status': AbsenceStatus.VACATION,
        'start_date': None,
        'end_date': None,
        'delegated_tasks_count': 0,
        'is_update': False,
    }
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )
    send_delegation_mock.assert_not_called()


def test_activate__delegation_failed__no_event(
    mocker,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    substitute = create_test_admin(account=account)
    delegate_tasks_mock = mocker.patch.object(
        VacationDelegationService,
        attribute='delegate_tasks',
        side_effect=ValueError('broken'),
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    send_delegation_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_vacation_delegation_notification.delay',
    )
    service = VacationDelegationService(
        user=user,
        request_user=owner,
    )

    # act
    with pytest.raises(ValueError) as ex:
        service.activate(substitute_user_ids=[substitute.id])

    # assert
    assert str(ex.value) == 'broken'
    assert fake_stream.events == []
    delegate_tasks_mock.assert_called_once_with(group=mocker.ANY)
    send_user_updated_mock.assert_not_called()
    send_delegation_mock.assert_not_called()


def test_deactivate__existing_vacation__emit_vacation_deactivate(
    mocker,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    substitute = create_test_admin(account=account)
    create_test_vacation(
        user=user,
        substitutes=[substitute],
        absence_status=AbsenceStatus.VACATION,
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    service = VacationDelegationService(
        user=user,
        request_user=owner,
    )

    # act
    service.deactivate()

    # assert
    assert not UserVacation.objects.filter(user=user).exists()
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_VACATION_DEACTIVATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {'target_email': user.email}
    assert event.pii == ('actor.email', 'payload.target_email')
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_deactivate__no_request_user__emit_system_actor(
    mocker,
    fake_stream,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    substitute = create_test_admin(account=account)
    create_test_vacation(
        user=user,
        substitutes=[substitute],
        absence_status=AbsenceStatus.VACATION,
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    service = VacationDelegationService(user=user)

    # act
    service.deactivate()

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_VACATION_DEACTIVATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(type=ActorType.SYSTEM)
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {'target_email': user.email}
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_deactivate__no_vacation__no_event(
    mocker,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    service = VacationDelegationService(
        user=user,
        request_user=owner,
    )

    # act
    result = service.deactivate()

    # assert
    assert result == user
    assert fake_stream.events == []
    send_user_updated_mock.assert_not_called()


def test_clear_substitute_groups__last_substitute__emit_system_deactivate(
    mocker,
    fake_stream,
):

    """ The vacation ends because its last substitute left: nobody
        turned it off, so the actor is the system. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(account=account)
    create_test_vacation(
        user=owner,
        substitutes=[substitute],
        absence_status=AbsenceStatus.VACATION,
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )

    # act
    VacationDelegationService.clear_substitute_groups(user=substitute)

    # assert
    assert not UserVacation.objects.filter(user=owner).exists()
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_VACATION_DEACTIVATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(type=ActorType.SYSTEM)
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=owner.id,
    )
    assert event.payload == {'target_email': owner.email}
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )
