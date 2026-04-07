import pytest

from src.accounts.enums import (
    AbsenceStatus,
    UserGroupType,
)
from src.accounts.models import (
    UserGroup,
    UserVacation,
)
from src.processes.enums import (
    DirectlyStatus,
    PerformerType,
    TaskStatus,
    WorkflowStatus,
)
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tasks.tasks import delegate_vacation_tasks
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)


pytestmark = pytest.mark.django_db


def test_delegate_vacation_tasks__delegates__ok(mocker):

    """
    Creates performers and calls event for active tasks missing substitutes.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(account=account, email='sub1@pneumatic.app')

    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    group.users.add(substitute)
    UserVacation.objects.create(
        user=owner,
        substitute_group=group,
    )
    owner.absence_status = AbsenceStatus.VACATION
    owner.save(update_fields=['absence_status'])

    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(user=owner, template=template)
    task = workflow.tasks.first()

    event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    delegate_vacation_tasks()

    # assert
    assert TaskPerformer.objects.filter(
        task=task,
        group=group,
        type=PerformerType.GROUP,
    ).exists()

    event_mock.assert_called_once_with(
        task=task,
        user=owner,
        substitute_group=group,
    )
    assert workflow.members.filter(id=substitute.id).exists()


def test_delegate_vacation_tasks__skips_already_delegated__ok(mocker):

    """
    Does not duplicate performer if the group is already assigned to the task.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(account=account, email='sub1@pneumatic.app')

    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    group.users.add(substitute)
    UserVacation.objects.create(user=owner, substitute_group=group)
    owner.absence_status = AbsenceStatus.VACATION
    owner.save(update_fields=['absence_status'])

    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(user=owner, template=template)
    task = workflow.tasks.first()

    TaskPerformer.objects.create(
        task=task,
        group=group,
        type=PerformerType.GROUP,
        directly_status=DirectlyStatus.CREATED,
    )

    event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    delegate_vacation_tasks()

    # assert
    event_mock.assert_not_called()
    assert TaskPerformer.objects.filter(
        task=task,
        group=group,
    ).count() == 1


def test_delegate_vacation_tasks__skips_soft_deleted_delegations__ok(mocker):

    """
    Soft-deleted group performers are considered already delegated and skipped.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    group = UserGroup.objects.create(
        name='Sub',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    UserVacation.objects.create(user=owner, substitute_group=group)
    owner.absence_status = AbsenceStatus.VACATION
    owner.save(update_fields=['absence_status'])

    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(user=owner, template=template)
    task = workflow.tasks.first()

    TaskPerformer.objects.create(
        task=task,
        group=group,
        type=PerformerType.GROUP,
        directly_status=DirectlyStatus.DELETED,
    )

    event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    delegate_vacation_tasks()

    # assert
    event_mock.assert_not_called()


def test_delegate_vacation_tasks__no_active_tasks__ok(mocker):

    """
    Does not delegate if tasks are not ACTIVE/DELAYED.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    group = UserGroup.objects.create(
        name='Sub',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    UserVacation.objects.create(user=owner, substitute_group=group)
    owner.absence_status = AbsenceStatus.VACATION
    owner.save(update_fields=['absence_status'])

    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(user=owner, template=template)
    task = workflow.tasks.first()
    task.status = TaskStatus.COMPLETED
    task.save(update_fields=['status'])

    event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    delegate_vacation_tasks()

    # assert
    event_mock.assert_not_called()


def test_delegate__skips_completed_performers__ok(mocker):

    """
    Skips user performers with is_completed=True so that
    tasks where the user already finished are not delegated.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub1@pneumatic.app',
    )

    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    group.users.add(substitute)
    UserVacation.objects.create(
        user=owner,
        substitute_group=group,
    )
    owner.absence_status = AbsenceStatus.VACATION
    owner.save(update_fields=['absence_status'])

    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.first()

    # mark user performer as completed
    TaskPerformer.objects.filter(
        task=task,
        user_id=owner.id,
        type=PerformerType.USER,
    ).update(is_completed=True)

    event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    delegate_vacation_tasks()

    # assert
    assert not TaskPerformer.objects.filter(
        task=task,
        group=group,
        type=PerformerType.GROUP,
    ).exists()
    event_mock.assert_not_called()


def test_delegate__user_error__continues_next(mocker):

    """
    When delegation fails for one user, subsequent users
    are still processed.
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
        substitute_group=group1,
    )
    UserVacation.objects.create(
        user=owner2,
        substitute_group=group2,
    )
    owner1.absence_status = AbsenceStatus.VACATION
    owner1.save(update_fields=['absence_status'])
    owner2.absence_status = AbsenceStatus.VACATION
    owner2.save(update_fields=['absence_status'])

    template1 = create_test_template(
        user=owner1,
        tasks_count=1,
        is_active=True,
    )
    workflow1 = create_test_workflow(
        user=owner1,
        template=template1,
    )
    task1 = workflow1.tasks.first()

    template2 = create_test_template(
        user=owner2,
        tasks_count=1,
        is_active=True,
    )
    workflow2 = create_test_workflow(
        user=owner2,
        template=template2,
    )
    task2 = workflow2.tasks.first()

    # make first user's delegation fail
    event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
        side_effect=[Exception('boom'), None],
    )

    # act
    delegate_vacation_tasks()

    # assert
    assert not TaskPerformer.objects.filter(
        task=task1,
        group=group1,
        type=PerformerType.GROUP,
    ).exists()

    assert TaskPerformer.objects.filter(
        task=task2,
        group=group2,
        type=PerformerType.GROUP,
    ).exists()
    assert event_mock.call_count == 2


def test_delegate__error__rolls_back_user(mocker):

    """
    When an error occurs mid-processing for a user, the
    atomic block rolls back all per-user changes (performers,
    members).
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub1@pneumatic.app',
    )

    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    group.users.add(substitute)
    UserVacation.objects.create(
        user=owner,
        substitute_group=group,
    )
    owner.absence_status = AbsenceStatus.VACATION
    owner.save(update_fields=['absence_status'])

    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.first()

    mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
        side_effect=Exception('event error'),
    )

    # act
    delegate_vacation_tasks()

    # assert
    assert not TaskPerformer.objects.filter(
        task=task,
        group=group,
        type=PerformerType.GROUP,
    ).exists()
    assert not workflow.members.filter(
        id=substitute.id,
    ).exists()


def test_delegate__skips_non_running_workflow__ok(mocker):

    """
    Tasks from completed (non-RUNNING) workflows are not
    delegated even if the task status is ACTIVE.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub1@pneumatic.app',
    )

    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    group.users.add(substitute)
    UserVacation.objects.create(
        user=owner,
        substitute_group=group,
    )
    owner.absence_status = AbsenceStatus.VACATION
    owner.save(update_fields=['absence_status'])

    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
        status=WorkflowStatus.DONE,
    )
    task = workflow.tasks.first()
    task.status = TaskStatus.ACTIVE
    task.save(update_fields=['status'])

    event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )

    # act
    delegate_vacation_tasks()

    # assert
    assert not TaskPerformer.objects.filter(
        task=task,
        group=group,
        type=PerformerType.GROUP,
    ).exists()
    event_mock.assert_not_called()


def test_delegate__all_delegated__skips_members(mocker):

    """
    When all tasks are already delegated, wf_ids is empty
    and _add_members_bulk is not called (early return).
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub1@pneumatic.app',
    )

    group = UserGroup.objects.create(
        name='Substitutes',
        type=UserGroupType.PERSONAL,
        account=account,
    )
    group.users.add(substitute)
    UserVacation.objects.create(
        user=owner,
        substitute_group=group,
    )
    owner.absence_status = AbsenceStatus.VACATION
    owner.save(update_fields=['absence_status'])

    template = create_test_template(
        user=owner,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.first()

    # pre-create group performer (already delegated)
    TaskPerformer.objects.create(
        task=task,
        group=group,
        type=PerformerType.GROUP,
        directly_status=DirectlyStatus.CREATED,
    )

    event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.task_delegation_event',
    )
    add_members_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'VacationDelegationService._add_members_bulk',
    )

    # act
    delegate_vacation_tasks()

    # assert
    event_mock.assert_not_called()
    add_members_mock.assert_not_called()
