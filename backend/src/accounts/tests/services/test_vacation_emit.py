from datetime import date

import pytest

from src.accounts.enums import AbsenceStatus
from src.accounts.models import UserVacation
from src.accounts.services.vacation import VacationDelegationService
from src.authentication.enums import AuthTokenType
from src.processes.enums import PerformerType
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
    create_test_vacation,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_activate__new_vacation__audit_vacation_activated(mocker):

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
    captured_substitutes = []
    vacation_activated_mock = mocker.patch(
        'src.accounts.services.vacation.AuditEventService.vacation_activated',
        side_effect=lambda **kwargs: captured_substitutes.append(
            kwargs['substitute_users'],
        ),
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    send_vacation_delegation_notification_mock = mocker.patch(
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
    vacation_activated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=user,
        substitute_users=captured_substitutes[0],
        absence_status=AbsenceStatus.SICK_LEAVE,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 20),
        delegated_tasks_count=0,
        is_update=False,
    )
    assert list(captured_substitutes[0].order_by('id')) == [
        substitute_1,
        substitute_2,
    ]
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )
    send_vacation_delegation_notification_mock.assert_not_called()


def test_activate__active_task_without_delegation__audit_delegated_count(
    mocker,
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
    task_delegation_mock = mocker.patch(
        'src.accounts.services.vacation.AuditEventService.task_delegation',
    )
    captured_substitutes = []
    vacation_activated_mock = mocker.patch(
        'src.accounts.services.vacation.AuditEventService.vacation_activated',
        side_effect=lambda **kwargs: captured_substitutes.append(
            kwargs['substitute_users'],
        ),
    )
    schedule_sync_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'schedule_sync_workflow_attachment_permissions',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    send_vacation_delegation_notification_mock = mocker.patch(
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
    substitute_group = UserVacation.objects.get(user=owner).substitute_group
    vacation_activated_mock.assert_called_once_with(
        user=admin,
        auth_type=AuthTokenType.USER,
        target=owner,
        substitute_users=captured_substitutes[0],
        absence_status=AbsenceStatus.VACATION,
        start_date=None,
        end_date=None,
        delegated_tasks_count=1,
        is_update=False,
    )
    assert list(captured_substitutes[0].order_by('id')) == [substitute]
    task_delegation_event_mock.assert_called_once_with(
        task=workflow.tasks.get(number=1),
        user=owner,
        substitute_group=substitute_group,
    )
    task_delegation_mock.assert_called_once_with(
        task=workflow.tasks.get(number=1),
        target=owner,
        substitute_group=substitute_group,
    )
    schedule_sync_mock.assert_called_once_with(workflow.id)
    send_vacation_delegation_notification_mock.assert_called_once_with(
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


def test_activate__regular_group_task__audit_task_delegation(mocker):
    """The person on vacation performs the task through a regular
    group, not directly: the task is delegated all the same."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    substitute = create_test_not_admin(account=account)
    regular_group = create_test_group(
        account=account,
        name='Dev Team',
        users=[owner, admin],
    )
    template = create_test_template(
        user=admin,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=admin,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task=task,
        type=PerformerType.GROUP,
        group=regular_group,
    )
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    task_delegation_mock = mocker.patch(
        'src.accounts.services.vacation.AuditEventService.task_delegation',
    )
    captured_substitutes = []
    vacation_activated_mock = mocker.patch(
        'src.accounts.services.vacation.AuditEventService.vacation_activated',
        side_effect=lambda **kwargs: captured_substitutes.append(
            kwargs['substitute_users'],
        ),
    )
    schedule_sync_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'schedule_sync_workflow_attachment_permissions',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    send_vacation_delegation_notification_mock = mocker.patch(
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
    substitute_group = UserVacation.objects.get(user=owner).substitute_group
    task_delegation_mock.assert_called_once_with(
        task=task,
        target=owner,
        substitute_group=substitute_group,
    )
    task_delegation_event_mock.assert_called_once_with(
        task=task,
        user=owner,
        substitute_group=substitute_group,
    )
    vacation_activated_mock.assert_called_once_with(
        user=admin,
        auth_type=AuthTokenType.USER,
        target=owner,
        substitute_users=captured_substitutes[0],
        absence_status=AbsenceStatus.VACATION,
        start_date=None,
        end_date=None,
        delegated_tasks_count=1,
        is_update=False,
    )
    assert list(captured_substitutes[0].order_by('id')) == [substitute]
    schedule_sync_mock.assert_called_once_with(workflow.id)
    send_vacation_delegation_notification_mock.assert_called_once_with(
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


def test_activate__existing_vacation__audit_is_update_true(mocker):

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
    captured_substitutes = []
    vacation_activated_mock = mocker.patch(
        'src.accounts.services.vacation.AuditEventService.vacation_activated',
        side_effect=lambda **kwargs: captured_substitutes.append(
            kwargs['substitute_users'],
        ),
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    send_vacation_delegation_notification_mock = mocker.patch(
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
    vacation_activated_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        target=user,
        substitute_users=captured_substitutes[0],
        absence_status=AbsenceStatus.VACATION,
        start_date=None,
        end_date=date(2099, 2, 1),
        delegated_tasks_count=0,
        is_update=True,
    )
    assert list(captured_substitutes[0].order_by('id')) == [substitute_2]
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )
    send_vacation_delegation_notification_mock.assert_not_called()


def test_activate__no_request_user__audit_no_actor(mocker):
    """A scheduled task turns the vacation on for nobody."""

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    substitute = create_test_admin(account=account)
    captured_substitutes = []
    vacation_activated_mock = mocker.patch(
        'src.accounts.services.vacation.AuditEventService.vacation_activated',
        side_effect=lambda **kwargs: captured_substitutes.append(
            kwargs['substitute_users'],
        ),
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    send_vacation_delegation_notification_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_vacation_delegation_notification.delay',
    )
    service = VacationDelegationService(user=user)

    # act
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    vacation_activated_mock.assert_called_once_with(
        user=None,
        auth_type=AuthTokenType.USER,
        target=user,
        substitute_users=captured_substitutes[0],
        absence_status=AbsenceStatus.VACATION,
        start_date=None,
        end_date=None,
        delegated_tasks_count=0,
        is_update=False,
    )
    assert list(captured_substitutes[0].order_by('id')) == [substitute]
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )
    send_vacation_delegation_notification_mock.assert_not_called()


def test_activate__api_key_auth__audit_api_key_actor(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    substitute = create_test_admin(account=account)
    captured_substitutes = []
    vacation_activated_mock = mocker.patch(
        'src.accounts.services.vacation.AuditEventService.vacation_activated',
        side_effect=lambda **kwargs: captured_substitutes.append(
            kwargs['substitute_users'],
        ),
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    send_vacation_delegation_notification_mock = mocker.patch(
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
    vacation_activated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.API,
        target=user,
        substitute_users=captured_substitutes[0],
        absence_status=AbsenceStatus.VACATION,
        start_date=None,
        end_date=None,
        delegated_tasks_count=0,
        is_update=False,
    )
    assert list(captured_substitutes[0].order_by('id')) == [substitute]
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )
    send_vacation_delegation_notification_mock.assert_not_called()


def test_activate__delegation_failed__audit_not_called(mocker):

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
    vacation_activated_mock = mocker.patch(
        'src.accounts.services.vacation.AuditEventService.vacation_activated',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    send_vacation_delegation_notification_mock = mocker.patch(
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
    delegate_tasks_mock.assert_called_once_with(group=mocker.ANY)
    vacation_activated_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()
    send_vacation_delegation_notification_mock.assert_not_called()


def test_deactivate__existing_vacation__audit_vacation_deactivated(mocker):

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
    vacation_deactivated_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'AuditEventService.vacation_deactivated',
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
    vacation_deactivated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=user,
    )
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_deactivate__no_request_user__audit_no_actor(mocker):

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
    vacation_deactivated_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'AuditEventService.vacation_deactivated',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    service = VacationDelegationService(user=user)

    # act
    service.deactivate()

    # assert
    vacation_deactivated_mock.assert_called_once_with(
        user=None,
        auth_type=AuthTokenType.USER,
        target=user,
    )
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_deactivate__no_vacation__audit_not_called(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    vacation_deactivated_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'AuditEventService.vacation_deactivated',
    )
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
    vacation_deactivated_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()


def test_clear_substitute_groups__last_substitute__audit_no_actor(
    mocker,
):
    """The vacation ends because its last substitute left: nobody
    turned it off, so the actor is the system."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(account=account)
    create_test_vacation(
        user=owner,
        substitutes=[substitute],
        absence_status=AbsenceStatus.VACATION,
    )
    vacation_deactivated_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'AuditEventService.vacation_deactivated',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )

    # act
    VacationDelegationService.clear_substitute_groups(user=substitute)

    # assert
    assert not UserVacation.objects.filter(user=owner).exists()
    vacation_deactivated_mock.assert_called_once_with(
        user=None,
        auth_type=AuthTokenType.USER,
        target=owner,
    )
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_clear_substitute_groups__request_user__audit_actor(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    substitute = create_test_not_admin(account=account)
    create_test_vacation(
        user=owner,
        substitutes=[substitute],
        absence_status=AbsenceStatus.VACATION,
    )
    vacation_deactivated_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'AuditEventService.vacation_deactivated',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )

    # act
    VacationDelegationService.clear_substitute_groups(
        user=substitute,
        request_user=admin,
        auth_type=AuthTokenType.API,
    )

    # assert
    assert not UserVacation.objects.filter(user=owner).exists()
    vacation_deactivated_mock.assert_called_once_with(
        user=admin,
        auth_type=AuthTokenType.API,
        target=owner,
    )
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )
