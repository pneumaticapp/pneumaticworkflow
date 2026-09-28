import pytest
from django.utils import timezone

from src.authentication.enums import AuthTokenType
from src.processes.enums import PerformerType, TaskStatus
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tasks.tasks import complete_tasks
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_owner,
    create_test_user,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_complete_tasks__ok():

    # arrange
    user = create_test_user()
    second_user = create_test_user(
        email='second_user@pneumatic.app',
        account=user.account,
    )
    workflow = create_test_workflow(
        user=user,
    )
    second_workflow = create_test_workflow(
        user=user,
    )
    second_workflow_first_task = second_workflow.tasks.get(number=1)
    second_workflow_first_task.performers.add(second_user)
    second_workflow_first_task.require_completion_by_all = True
    second_workflow_first_task.save()
    first_task = workflow.tasks.get(number=1)
    first_task.require_completion_by_all = True
    first_task.save()
    first_task.taskperformer_set.filter(user=user).update(
        is_completed=True,
    )
    second_workflow_first_task.taskperformer_set.filter(
        user=user,
    ).update(is_completed=True)

    # act
    complete_tasks(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        user_id=user.id,
    )

    # assert
    first_task.refresh_from_db()
    second_workflow_first_task.refresh_from_db()
    assert first_task.is_completed
    assert second_workflow_first_task.is_completed is False


def test_complete_tasks__user_incomplete_group_user_completed__ok():

    """
    RCBA: USER incomplete + GROUP_USER completed for A; B deleted
    → complete_tasks(A) completes the task via can_be_completed()
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user_1 = create_test_admin(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.require_completion_by_all = True
    task.save(update_fields=['require_completion_by_all'])
    current_date = timezone.now()
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=user_1.id,
        type=PerformerType.USER,
        is_completed=True,
        date_completed=current_date,
    )
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=owner.id,
        type=PerformerType.GROUP_USER,
        is_completed=True,
        date_completed=current_date,
    )
    TaskPerformer.objects.filter(
        task_id=task.id,
        user_id=user_1.id,
        type=PerformerType.USER,
    ).delete()

    # act
    complete_tasks(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        user_id=owner.id,
    )

    # assert
    task.refresh_from_db()
    assert task.status == TaskStatus.COMPLETED


def test_complete_tasks__other_incomplete__skip():

    """
    RCBA: A credited via GROUP_USER, B still incomplete
    → complete_tasks(A) does not complete the task
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user_1 = create_test_admin(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.require_completion_by_all = True
    task.save(update_fields=['require_completion_by_all'])
    TaskPerformer.objects.filter(task_id=task.id).delete()
    group_1 = create_test_group(account=account, users=[owner, user_1])
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group_1.id,
    )
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=owner.id,
        type=PerformerType.GROUP_USER,
        is_completed=True,
        date_completed=timezone.now(),
    )

    # act
    complete_tasks(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        user_id=owner.id,
    )

    # assert
    task.refresh_from_db()
    assert task.status == TaskStatus.ACTIVE


def test_complete_tasks__group_user_only__skip():

    """
    Only GROUP_USER for user_1, no USER/GROUP assignment
    → complete_tasks(user_1) does not select/complete the task
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user_1 = create_test_admin(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.require_completion_by_all = True
    task.save(update_fields=['require_completion_by_all'])
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=user_1.id,
        type=PerformerType.GROUP_USER,
        is_completed=True,
        date_completed=timezone.now(),
    )

    # act
    complete_tasks(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        user_id=user_1.id,
    )

    # assert
    task.refresh_from_db()
    assert task.status == TaskStatus.ACTIVE
