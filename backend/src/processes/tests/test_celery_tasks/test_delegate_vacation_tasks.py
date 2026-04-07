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
