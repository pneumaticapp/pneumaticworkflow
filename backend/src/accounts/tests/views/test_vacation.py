import pytest
from datetime import date

from src.accounts.enums import AbsenceStatus, UserGroupType
from src.accounts.models import UserGroup, UserVacation
from src.accounts.services.vacation import VacationDelegationService
from src.accounts.tasks import process_vacations
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)


pytestmark = pytest.mark.django_db


def test_vacation_activate__ok(api_client, mocker):

    """POST /accounts/user/activate-vacation activates vacation."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    create_test_workflow(
        user=owner,
        template=template,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/user/activate-vacation',
        data={
            'substitute_user_ids': [substitute.id],
            'absence_status': AbsenceStatus.VACATION,
        },
    )

    # assert
    assert response.status_code == 200
    owner.refresh_from_db()
    assert owner.is_absent is True
    user = UserVacation.objects.get(user=owner)
    assert user.absence_status == AbsenceStatus.VACATION
    assert owner.vacation.substitute_group is not None


def test_vacation_deactivate__ok(api_client, mocker):

    """POST /accounts/user/deactivate-vacation deactivates."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    create_test_workflow(
        user=owner,
        template=template,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    service = VacationDelegationService(user=owner)
    service.activate(
        substitute_user_ids=[substitute.id],
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/user/deactivate-vacation',
    )

    # assert
    assert response.status_code == 200
    owner.refresh_from_db()
    assert owner.is_absent is False
    assert not UserVacation.objects.filter(user=owner).exists()


def test_vacation_deactivate__not_absent__error(api_client):

    """POST when not absent returns validation error."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/user/deactivate-vacation',
    )

    # assert
    assert response.status_code == 400
    assert 'message' in response.data


def test_vacation_deactivate__pre_scheduled__ok(
    api_client,
    mocker,
):

    """Pre-scheduled vacation (absence_status=ACTIVE)
    can be deactivated."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    group = UserGroup.objects.create(
        name='Substitutes Test',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    group.users.set([substitute.id])
    UserVacation.objects.create(
        user=owner,
        account=account,
        substitute_group=group,
        start_date=date(2099, 1, 1),
        absence_status=AbsenceStatus.ACTIVE,
    )
    owner.refresh_from_db()
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/user/deactivate-vacation',
    )

    # assert
    assert response.status_code == 200
    owner.refresh_from_db()
    assert owner.vacation is None
    assert not UserVacation.objects.filter(
        user=owner,
    ).exists()
    event_mock.assert_not_called()


def test_schedule__auto_start__past_date__ok(mocker):

    """
    ACTIVE user past start_date with group is
    auto-activated.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    create_test_workflow(
        user=owner,
        template=template,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # setup pre-activation state: create UserVacation with
    # past start_date so process_vacations auto-starts
    group = UserGroup.objects.create(
        name='Substitutes Test',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    group.users.set([substitute.id])
    UserVacation.objects.create(
        user=owner,
        account=account,
        substitute_group=group,
        start_date=date(2020, 1, 1),
    )
    vacation = UserVacation.objects.get(user=owner)
    vacation.absence_status = AbsenceStatus.ACTIVE
    vacation.save(update_fields=['absence_status'])

    # act
    process_vacations()

    # assert
    owner.refresh_from_db()
    assert owner.is_absent is True


def test_schedule__auto_stop__past_date__ok(mocker):

    """
    Absent user past end_date is auto-deactivated.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    create_test_workflow(
        user=owner,
        template=template,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    service = VacationDelegationService(user=owner)
    service.activate(
        substitute_user_ids=[substitute.id],
        vacation_end_date=date(2020, 1, 1),
    )
    owner.refresh_from_db()
    assert owner.is_absent is True

    # act
    process_vacations()

    # assert
    owner.refresh_from_db()
    assert owner.is_absent is False
    assert not UserVacation.objects.filter(user=owner).exists()


def test_schedule__future_end__stays_absent__ok(mocker):

    """
    User with future end_date stays absent.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    create_test_workflow(
        user=owner,
        template=template,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    service = VacationDelegationService(user=owner)
    service.activate(
        substitute_user_ids=[substitute.id],
        vacation_end_date=date(2099, 12, 31),
    )
    owner.refresh_from_db()
    assert owner.is_absent is True

    # act
    process_vacations()

    # assert
    owner.refresh_from_db()
    assert owner.is_absent is True


def test_schedule__auto_start_error__continues__ok(mocker):

    """
    When auto-start fails for one user, subsequent
    users are still processed.
    """

    # arrange
    account = create_test_account()
    owner1 = create_test_owner(account=account)
    owner2 = create_test_admin(
        account=account,
        email='owner2@pneumatic.app',
    )
    sub1 = create_test_admin(
        account=account,
        email='sub1@pneumatic.app',
    )
    sub2 = create_test_admin(
        account=account,
        email='sub2@pneumatic.app',
    )

    group1 = UserGroup.objects.create(
        name='Sub1',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    group1.users.add(sub1)
    group2 = UserGroup.objects.create(
        name='Sub2',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    group2.users.add(sub2)

    UserVacation.objects.create(
        user=owner1,
        account=account,
        substitute_group=group1,
        start_date=date(2020, 1, 1),
    )
    UserVacation.objects.create(
        user=owner2,
        account=account,
        substitute_group=group2,
        start_date=date(2020, 1, 1),
    )
    v1 = UserVacation.objects.get(user=owner1)
    v1.absence_status = AbsenceStatus.ACTIVE
    v1.save(update_fields=['absence_status'])
    v2 = UserVacation.objects.get(user=owner2)
    v2.absence_status = AbsenceStatus.ACTIVE
    v2.save(update_fields=['absence_status'])

    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    activate_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'VacationDelegationService.activate',
        side_effect=[Exception('boom'), None],
    )

    # act
    process_vacations()

    # assert
    assert activate_mock.call_count == 2


def test_schedule__auto_stop_error__continues__ok(mocker):

    """
    When auto-stop fails for one user, subsequent
    users are still processed.
    """

    # arrange
    account = create_test_account()
    owner1 = create_test_owner(account=account)
    owner2 = create_test_admin(
        account=account,
        email='owner2@pneumatic.app',
        first_name='Jane',
    )
    sub1 = create_test_admin(
        account=account,
        email='sub1@pneumatic.app',
    )
    sub2 = create_test_admin(
        account=account,
        email='sub2@pneumatic.app',
    )

    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    service1 = VacationDelegationService(user=owner1)
    service1.activate(
        substitute_user_ids=[sub1.id],
        vacation_end_date=date(2020, 1, 1),
    )
    service2 = VacationDelegationService(user=owner2)
    service2.activate(
        substitute_user_ids=[sub2.id],
        vacation_end_date=date(2020, 1, 1),
    )

    deactivate_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'VacationDelegationService.deactivate',
        side_effect=[Exception('boom'), None],
    )

    # act
    process_vacations()

    # assert
    assert deactivate_mock.call_count == 2
