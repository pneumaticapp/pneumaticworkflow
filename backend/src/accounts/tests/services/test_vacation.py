import pytest

from src.accounts.enums import AbsenceStatus, UserGroupType
from src.accounts.models import UserGroup, UserVacation
from src.accounts.services.vacation import VacationDelegationService
from src.processes.enums import (
    DirectlyStatus,
    PerformerType,
    TaskStatus,
)
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)


pytestmark = pytest.mark.django_db


def test_init__default__ok():

    """
    Init with user sets self.user.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)

    # act
    service = VacationDelegationService(user=owner)

    # assert
    assert service.user == owner


def test_activate__creates_group__ok(mocker):

    """
    Creates personal group with substitutes.
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

    # act
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()
    group = owner.vacation_schedule.substitute_group
    assert group is not None
    assert group.type == UserGroupType.PERSONAL
    assert group.account_id == account.id
    assert list(
        group.users.values_list('id', flat=True),
    ) == [substitute.id]
    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=group,
    )


def test_activate__does_not_freeze_performers__ok(mocker):

    """
    Activate does NOT freeze user performers (DELEGATED removed).
    User performer stays NO_STATUS; group performer created alongside.
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
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    performer = TaskPerformer.objects.get(
        task__workflow=workflow,
        task__status=TaskStatus.ACTIVE,
        user_id=owner.id,
        type=PerformerType.USER,
    )
    assert performer.directly_status == DirectlyStatus.NO_STATUS
    group_perf = TaskPerformer.objects.filter(
        task__workflow=workflow,
        task__status=TaskStatus.ACTIVE,
        type=PerformerType.GROUP,
    ).first()
    assert group_perf is not None

    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=mocker.ANY,
    )


def test_activate__adds_group_perf__ok(mocker):

    """
    Adds GROUP performer for substitute group via bulk_create.
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
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()
    group_perf_exists = TaskPerformer.objects.filter(
        task__workflow=workflow,
        task__status=TaskStatus.ACTIVE,
        type=PerformerType.GROUP,
        group=owner.vacation_schedule.substitute_group,
    ).exists()
    assert group_perf_exists is True
    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=owner.vacation_schedule.substitute_group,
    )


def test_activate__skip_deleted__ok(mocker):

    """
    Skips DELETED performers.
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
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.get(status=TaskStatus.ACTIVE)
    TaskPerformer.objects.filter(
        task=task,
        user_id=owner.id,
        type=PerformerType.USER,
    ).update(directly_status=DirectlyStatus.DELETED)
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    performer = TaskPerformer.objects.get(
        task=task,
        user_id=owner.id,
        type=PerformerType.USER,
    )
    assert performer.directly_status == DirectlyStatus.DELETED
    task_delegation_event_mock.assert_not_called()


def test_activate__group_tasks__ok(mocker):

    """
    Handles group tasks (user in regular group).
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_admin(
        account=account,
        email='member@pneumatic.app',
    )
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    regular_group = create_test_group(
        account=account,
        name='Dev Team',
        users=[owner, member],
    )
    template = create_test_template(
        user=member,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=member,
        template=template,
    )
    task = workflow.tasks.get(status=TaskStatus.ACTIVE)

    # add group performer to task
    TaskPerformer.objects.create(
        task=task,
        type=PerformerType.GROUP,
        group=regular_group,
    )

    # remove any USER performer for owner (test group path)
    TaskPerformer.objects.filter(
        task=task,
        user_id=owner.id,
        type=PerformerType.USER,
    ).delete()
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()
    sub_group = owner.vacation_schedule.substitute_group
    sub_perf_exists = TaskPerformer.objects.filter(
        task=task,
        type=PerformerType.GROUP,
        group=sub_group,
    ).exists()
    assert sub_perf_exists is True
    task_delegation_event_mock.assert_called_once_with(
        task=task,
        user=owner,
        substitute_group=sub_group,
    )


def test_activate__no_user_groups__ok(mocker):

    """
    No group tasks when user has no regular groups.
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
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()
    assert owner.absence_status == AbsenceStatus.VACATION
    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=mocker.ANY,
    )


def test_activate__adds_members__ok(mocker):

    """
    Adds substitutes to workflow.members.
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
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    assert workflow.members.filter(id=substitute.id).exists()
    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=mocker.ANY,
    )


def test_activate__preserves_notif_settings__ok(mocker):

    """
    Activate does NOT mute notification settings.
    Notifications are skipped at send time based on
    absence_status instead of mutating user fields.
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

    original_new_tasks = owner.is_new_tasks_subscriber
    original_complete_tasks = owner.is_complete_tasks_subscriber

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()
    assert owner.is_new_tasks_subscriber == original_new_tasks
    assert owner.is_complete_tasks_subscriber == original_complete_tasks


def test_activate__sets_status__ok(mocker):

    """
    Sets absence_status to VACATION.
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
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()
    assert owner.absence_status == AbsenceStatus.VACATION
    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=mocker.ANY,
    )


def test_activate__sets_sick_leave__ok(mocker):

    """
    Sets absence_status to SICK_LEAVE when specified.
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

    # act
    service = VacationDelegationService(user=owner)
    service.activate(
        substitute_user_ids=[substitute.id],
        absence_status=AbsenceStatus.SICK_LEAVE,
    )

    # assert
    owner.refresh_from_db()
    assert owner.absence_status == AbsenceStatus.SICK_LEAVE


def test_activate__sets_sub_group__ok(mocker):

    """
    Sets vacation_substitute_group FK.
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
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()
    assert owner.vacation_schedule.substitute_group is not None
    assert owner.vacation_schedule.substitute_group.type == (
        UserGroupType.PERSONAL
    )
    task_delegation_event_mock.assert_called_once_with(
        task=mocker.ANY,
        user=owner,
        substitute_group=owner.vacation_schedule.substitute_group,
    )


def test_activate__update_existing__ok(mocker):

    """
    Updates substitutes when vacation is already active.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    sub1 = create_test_admin(
        account=account,
        email='sub1@pneumatic.app',
    )
    sub2 = create_test_admin(
        account=account,
        email='sub2@pneumatic.app',
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

    # activate first time
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[sub1.id])
    owner.refresh_from_db()
    group_id = owner.vacation_schedule.substitute_group_id

    # act — update substitutes
    service.activate(substitute_user_ids=[sub2.id])

    # assert
    owner.refresh_from_db()

    # same group is reused
    assert owner.vacation_schedule.substitute_group_id == group_id

    # sub2 is now the only member
    members = list(
        owner.vacation_schedule.substitute_group.users
        .values_list('id', flat=True),
    )
    assert members == [sub2.id]


def test_activate__update_existing__status__ok(mocker):

    """
    Updates absence_status on re-activation.
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
        absence_status=AbsenceStatus.VACATION,
    )

    # act
    service.activate(
        substitute_user_ids=[substitute.id],
        absence_status=AbsenceStatus.SICK_LEAVE,
    )

    # assert
    owner.refresh_from_db()
    assert owner.absence_status == AbsenceStatus.SICK_LEAVE


def test_activate__active_user_with_group__ok(mocker):

    """
    Reuses existing group if user is ACTIVE but has a scheduled vacation
    (substitute_group_id exists).
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub1@pneumatic.app',
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    service = VacationDelegationService(user=owner)

    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    UserVacation.objects.create(
        user=owner,
        substitute_group=group,
    )
    owner.absence_status = AbsenceStatus.ACTIVE
    owner.save(update_fields=['absence_status'])

    # act
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()

    assert owner.vacation_schedule.substitute_group_id == group.id


def test_activate__update_existing__creates_perfs__ok(mocker):

    """
    Auto-start: _update_existing creates group performers
    when none exist yet (first activation with pre-configured
    group) and emits delegation events for direct tasks.
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
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.get(status=TaskStatus.ACTIVE)
    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # Pre-configure vacation with substitute group (UI setup)
    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    UserVacation.objects.create(
        user=owner,
        substitute_group=group,
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()
    assert owner.absence_status == AbsenceStatus.VACATION
    group_perf_exists = TaskPerformer.objects.filter(
        task=task,
        type=PerformerType.GROUP,
        group=group,
    ).exists()
    assert group_perf_exists is True
    assert workflow.members.filter(id=substitute.id).exists()
    task_delegation_event_mock.assert_called_once_with(
        task=task,
        user=owner,
        substitute_group=group,
    )


def test_activate__update_existing__creates_grp_perfs__ok(
    mocker,
):

    """
    Auto-start _update_existing creates group performers
    for tasks where the user participates via regular group
    (no direct USER performer).
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_admin(
        account=account,
        email='member@pneumatic.app',
    )
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    regular_group = create_test_group(
        account=account,
        name='Dev Team',
        users=[owner, member],
    )
    template = create_test_template(
        user=member,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=member,
        template=template,
    )
    task = workflow.tasks.get(status=TaskStatus.ACTIVE)

    # add group performer to task
    TaskPerformer.objects.create(
        task=task,
        type=PerformerType.GROUP,
        group=regular_group,
    )

    # remove any USER performer for owner (test group path)
    TaskPerformer.objects.filter(
        task=task,
        user_id=owner.id,
        type=PerformerType.USER,
    ).delete()

    task_delegation_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # Pre-configure vacation with substitute group
    sub_group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    UserVacation.objects.create(
        user=owner,
        substitute_group=sub_group,
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    sub_perf_exists = TaskPerformer.objects.filter(
        task=task,
        type=PerformerType.GROUP,
        group=sub_group,
    ).exists()
    assert sub_perf_exists is True
    task_delegation_event_mock.assert_called_once_with(
        task=task,
        user=owner,
        substitute_group=sub_group,
    )


def test_activate__update_existing__filters_completed_tasks__ok(mocker):

    """
    Completed tasks and soft-deleted performers are ignored when updating.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(account=account, email='sub1@pneumatic.app')

    template = create_test_template(
        user=owner,
        tasks_count=2,
        is_active=True,
    )
    workflow = create_test_workflow(user=owner, template=template)

    task1 = workflow.tasks.order_by('number').first()
    task2 = workflow.tasks.order_by('number').last()

    task1.status = TaskStatus.COMPLETED
    task1.save(update_fields=['status'])

    task2.status = TaskStatus.ACTIVE
    task2.save(update_fields=['status'])

    TaskPerformer.objects.filter(task=task1).update(is_completed=True)

    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    notify_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_vacation_delegation_notification.delay',
    )

    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    UserVacation.objects.create(
        user=owner,
        substitute_group=group,
    )

    TaskPerformer.objects.create(
        task=task1,
        group=group,
        type=PerformerType.GROUP,
        is_completed=True,
        directly_status=DirectlyStatus.CREATED,
    )
    TaskPerformer.objects.create(
        task=task2,
        group=group,
        type=PerformerType.GROUP,
        is_completed=False,
        directly_status=DirectlyStatus.DELETED,
    )

    owner.absence_status = AbsenceStatus.VACATION
    owner.save(update_fields=['absence_status'])

    service = VacationDelegationService(user=owner)

    # act
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    notify_mock.assert_called_once_with(
        user_id=substitute.id,
        user_email=substitute.email,
        user_first_name=substitute.first_name,
        account_id=owner.account_id,
        tasks_count=1,
        vacation_owner_name=owner.get_full_name(),
    )


def test_activate__no_active_tasks__ok(mocker):

    """
    No crash when no active/delayed tasks exist.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()
    assert owner.absence_status == AbsenceStatus.VACATION
    assert owner.vacation_schedule.substitute_group is not None


def test_deactivate__unfreezes__ok(mocker):

    """
    Unfreezes DELEGATED performers to NO_STATUS.
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
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # act
    service.deactivate()

    # assert
    performer = TaskPerformer.objects.get(
        task__workflow=workflow,
        task__status=TaskStatus.ACTIVE,
        user_id=owner.id,
        type=PerformerType.USER,
    )
    assert performer.directly_status == DirectlyStatus.NO_STATUS


def test_deactivate__deletes_group__ok(mocker):

    """
    Deletes substitute group (cascade).
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
    service.activate(substitute_user_ids=[substitute.id])
    owner.refresh_from_db()
    group_id = owner.vacation_schedule.substitute_group_id

    # act
    service.deactivate()

    # assert
    assert not UserGroup.objects.filter(id=group_id).exists()


def test_deactivate__no_group__ok():

    """
    No error when vacation_substitute_group is None.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)

    # act
    service = VacationDelegationService(user=owner)
    service.deactivate()

    # assert
    owner.refresh_from_db()
    assert owner.absence_status == AbsenceStatus.ACTIVE


def test_deactivate__preserves_notif_settings__ok(mocker):

    """
    Preserves existing notification settings through activate/deactivate cycle.
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

    original_new_tasks = owner.is_new_tasks_subscriber
    original_complete_tasks = owner.is_complete_tasks_subscriber

    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # act
    service.deactivate()

    # assert
    owner.refresh_from_db()
    assert owner.is_new_tasks_subscriber == original_new_tasks
    assert owner.is_complete_tasks_subscriber == original_complete_tasks


def test_deactivate__notifs_default__ok():

    """
    Defaults notifications to True when saved is None.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    owner.save()

    # act
    service = VacationDelegationService(user=owner)
    service.deactivate()

    # assert
    owner.refresh_from_db()
    assert owner.is_new_tasks_subscriber is True
    assert owner.is_complete_tasks_subscriber is True


def test_deactivate__resets_status__ok(mocker):

    """
    Resets absence_status to ACTIVE.
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
    service.activate(substitute_user_ids=[substitute.id])

    # act
    service.deactivate()

    # assert
    owner.refresh_from_db()
    assert owner.absence_status == AbsenceStatus.ACTIVE


def test_deactivate__clears_fields__ok(mocker):

    """
    Clears vacation dates and saved fields.
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
    service.activate(substitute_user_ids=[substitute.id])

    # act
    service.deactivate()

    # assert
    owner.refresh_from_db()
    assert not UserVacation.objects.filter(user=owner).exists()


def test_deactivate__cleans_group_performers__ok(mocker):

    """
    Deactivate removes substitute group performers and
    restores the user to ACTIVE status.
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
        tasks_count=2,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # act
    service.deactivate()

    # assert
    group_perfs = TaskPerformer.objects.filter(
        task__workflow=workflow,
        type=PerformerType.GROUP,
    )
    assert group_perfs.count() == 0

    owner.refresh_from_db()
    assert owner.absence_status == AbsenceStatus.ACTIVE


def test_activate__update_replaces_subs__ok(mocker):

    """
    Re-activating with different substitutes replaces old members
    while keeping the same group.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    sub1 = create_test_admin(
        account=account,
        email='sub1@pneumatic.app',
    )
    sub2 = create_test_admin(
        account=account,
        email='sub2@pneumatic.app',
    )
    sub3 = create_test_admin(
        account=account,
        email='sub3@pneumatic.app',
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

    # activate with sub1, sub2
    service = VacationDelegationService(user=owner)
    service.activate(
        substitute_user_ids=[sub1.id, sub2.id],
    )
    owner.refresh_from_db()
    group_id = owner.vacation_schedule.substitute_group_id

    # act
    service.activate(
        substitute_user_ids=[sub2.id, sub3.id],
    )

    # assert — same group, new members
    owner.refresh_from_db()
    assert owner.vacation_schedule.substitute_group_id == group_id
    member_ids = set(
        owner.vacation_schedule.substitute_group.users
        .values_list('id', flat=True),
    )
    assert member_ids == {sub2.id, sub3.id}


def test_clear_sub_groups__removes_user__ok():

    """
    Removes user from personal groups.
    """

    # arrange
    account = create_test_account()
    _owner = create_test_owner(account=account)
    sub = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    sub2 = create_test_admin(
        account=account,
        email='sub2@pneumatic.app',
    )
    group = UserGroup.objects.create(
        name='Substitutes Test',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    group.users.set([sub.id, sub2.id])

    # act
    VacationDelegationService.clear_substitute_groups(
        user=sub,
    )

    # assert
    assert not group.users.filter(id=sub.id).exists()
    assert group.users.filter(id=sub2.id).exists()


def test_clear_sub_groups__empty__deactivates(mocker):

    """
    Auto-deactivates vacation when group becomes empty.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    sub = create_test_admin(
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
    service.activate(substitute_user_ids=[sub.id])
    owner.refresh_from_db()
    assert owner.is_absent is True

    # act
    VacationDelegationService.clear_substitute_groups(
        user=sub,
    )

    # assert
    owner.refresh_from_db()
    assert owner.absence_status == AbsenceStatus.ACTIVE
    assert not UserVacation.objects.filter(user=owner).exists()


def test_clear_sub_groups__no_groups__ok():

    """
    No error when user not in any personal groups.
    """

    # arrange
    account = create_test_account()
    user = create_test_admin(
        account=account,
        email='user@pneumatic.app',
    )

    # act
    VacationDelegationService.clear_substitute_groups(
        user=user,
    )

    # assert — no exception raised, user has no personal groups
    personal_groups = UserGroup.objects.filter(
        type=UserGroupType.PERSONAL,
        users=user,
    )
    assert personal_groups.count() == 0


def test_activate__sends_notification__ok(mocker):

    """
    Sends delegation notification to substitutes.
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
    send_notif_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_vacation_delegation_notification.delay',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    send_notif_mock.assert_called_once_with(
        user_id=substitute.id,
        user_email=substitute.email,
        user_first_name=substitute.first_name,
        account_id=account.id,
        tasks_count=1,
        vacation_owner_name=owner.get_full_name(),
    )


def test_activate__no_tasks__skip_notif__ok(mocker):

    """
    No notification when no tasks are delegated.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    send_notif_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_vacation_delegation_notification.delay',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    send_notif_mock.assert_not_called()


def test_activate_new__skips_completed_grp_perfs__ok(mocker):

    """
    _activate_new skips group performers with is_completed=True
    when building the set of tasks to delegate from regular groups.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_admin(
        account=account,
        email='member@pneumatic.app',
    )
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    regular_group = create_test_group(
        account=account,
        name='Dev Team',
        users=[owner, member],
    )
    template = create_test_template(
        user=member,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=member,
        template=template,
    )
    task = workflow.tasks.get(status=TaskStatus.ACTIVE)

    # add completed group performer to task
    TaskPerformer.objects.create(
        task=task,
        type=PerformerType.GROUP,
        group=regular_group,
        is_completed=True,
    )

    # remove USER performer for owner (test group path)
    TaskPerformer.objects.filter(
        task=task,
        user_id=owner.id,
        type=PerformerType.USER,
    ).delete()

    event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    owner.refresh_from_db()
    sub_group = owner.vacation_schedule.substitute_group
    sub_perf_exists = TaskPerformer.objects.filter(
        task=task,
        type=PerformerType.GROUP,
        group=sub_group,
    ).exists()
    assert sub_perf_exists is False
    event_mock.assert_not_called()


def test_update_existing__skips_completed_grp_perfs__ok(
    mocker,
):

    """
    _update_existing skips group performers with
    is_completed=True when scanning regular groups.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_admin(
        account=account,
        email='member@pneumatic.app',
    )
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    regular_group = create_test_group(
        account=account,
        name='Dev Team',
        users=[owner, member],
    )
    template = create_test_template(
        user=member,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=member,
        template=template,
    )
    task = workflow.tasks.get(status=TaskStatus.ACTIVE)

    # add completed group performer to task
    TaskPerformer.objects.create(
        task=task,
        type=PerformerType.GROUP,
        group=regular_group,
        is_completed=True,
    )

    # remove USER performer for owner
    TaskPerformer.objects.filter(
        task=task,
        user_id=owner.id,
        type=PerformerType.USER,
    ).delete()

    event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # Pre-configure vacation with substitute group
    sub_group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    UserVacation.objects.create(
        user=owner,
        substitute_group=sub_group,
    )

    # act
    service = VacationDelegationService(user=owner)
    service.activate(substitute_user_ids=[substitute.id])

    # assert
    sub_perf_exists = TaskPerformer.objects.filter(
        task=task,
        type=PerformerType.GROUP,
        group=sub_group,
    ).exists()
    assert sub_perf_exists is False
    event_mock.assert_not_called()
