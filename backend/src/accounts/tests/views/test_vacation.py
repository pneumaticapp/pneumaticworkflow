import pytest
from datetime import date

from src.accounts.enums import AbsenceStatus, UserGroupType
from src.accounts.models import UserGroup, UserVacation
from src.accounts.services.vacation import VacationDelegationService
from src.accounts.tasks import process_vacation_schedules
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
    assert owner.absence_status == AbsenceStatus.VACATION
    assert owner.vacation_schedule.substitute_group is not None


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
    assert owner.absence_status == AbsenceStatus.ACTIVE


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
    # past start_date so process_vacation_schedules auto-starts
    group = UserGroup.objects.create(
        name='Substitutes Test',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    group.users.set([substitute.id])
    UserVacation.objects.create(
        user=owner,
        substitute_group=group,
        start_date=date(2020, 1, 1),
    )
    owner.absence_status = AbsenceStatus.ACTIVE
    owner.save(update_fields=['absence_status'])

    # act
    process_vacation_schedules()

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
    process_vacation_schedules()

    # assert
    owner.refresh_from_db()
    assert owner.is_absent is False
    assert owner.absence_status == AbsenceStatus.ACTIVE


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
    process_vacation_schedules()

    # assert
    owner.refresh_from_db()
    assert owner.is_absent is True
