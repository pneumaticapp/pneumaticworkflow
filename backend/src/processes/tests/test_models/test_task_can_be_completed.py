import pytest

from src.accounts.enums import UserStatus
from src.processes.enums import (
    DirectlyStatus,
    PerformerType,
    TaskStatus,
)
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_admin,
    create_test_not_admin,
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


class TestCanBeCompleted:

    def test__task_already_completed__false(self):

        """ Task is already completed — returns False immediately """

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.get(number=1)
        task.status = TaskStatus.COMPLETED
        task.save(update_fields=['status'])

        # act
        result = task.can_be_completed()

        # assert
        assert result is False

    def test__all_performers_completed__true(self):
        """
        require_completion_by_all=False, one completed performer — True
        """

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.update(is_completed=True)

        # act
        result = task.can_be_completed()

        # assert
        assert result is True

    def test__directly_deleted_user_performer__true(self):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.update(
            is_completed=True,
            directly_status=DirectlyStatus.DELETED,
        )

        # act
        result = task.can_be_completed()

        # assert
        assert result is True

    def test__no_performers__true(self):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.all().delete()

        # act
        result = task.can_be_completed()

        # assert
        assert result is True

    def test__rcba_and_all_performers_completed__true(self):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.tasks.update(require_completion_by_all=True)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.update(is_completed=True)

        # act
        result = task.can_be_completed()

        # assert
        assert result is True

    def test__rcba_and_one_user_performer_incompleted__false(self):
        """
        require_completion_by_all=True, some incompleted performers — False
        """

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        admin = create_test_admin(account=account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.tasks.update(require_completion_by_all=True)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.update(is_completed=True)
        TaskPerformer.objects.create(
            task=task,
            user=admin,
            type=PerformerType.USER,
            is_completed=False,
        )

        # act
        result = task.can_be_completed()

        # assert
        assert result is False

    def test__rcba_and_group_performers_completed__true(self):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_admin(account=account)
        user_2 = create_test_not_admin(account=account)
        group = create_test_group(
            account=account,
            users=[user_1, user_2],
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.tasks.update(require_completion_by_all=True)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.all().delete()

        # add GROUP performer with all members completed
        TaskPerformer.objects.create(
            task=task,
            group=group,
            type=PerformerType.GROUP,
            completed_users=[user_1.id, user_2.id],
        )

        # act
        result = task.can_be_completed()

        # assert
        assert result is True

    def test__rcba_and_group_user_incompleted__false(self):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_admin(account=account)
        user_2 = create_test_not_admin(account=account)
        group = create_test_group(
            account=account,
            users=[user_1, user_2],
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.tasks.update(require_completion_by_all=True)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.all().delete()
        TaskPerformer.objects.create(
            task=task,
            group=group,
            type=PerformerType.GROUP,
            completed_users=[user_1.id],
        )

        # act
        result = task.can_be_completed()

        # assert
        assert result is False

    def test__rcba_and_no_performers__true(self):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.tasks.update(require_completion_by_all=True)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.all().delete()

        # act
        result = task.can_be_completed()

        # assert
        assert result is True

    def test__rcba_and_two_groups_completed__true(self):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_admin(account=account)
        user_2 = create_test_not_admin(account=account)
        group_1 = create_test_group(
            account=account,
            name='Group_1',
            users=[user_1],
        )
        group_2 = create_test_group(
            account=account,
            name='Group_2',
            users=[user_2],
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.tasks.update(require_completion_by_all=True)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.all().delete()
        TaskPerformer.objects.create(
            task=task,
            group=group_1,
            type=PerformerType.GROUP,
            completed_users=[user_1.id],
        )
        TaskPerformer.objects.create(
            task=task,
            group=group_2,
            type=PerformerType.GROUP,
            completed_users=[user_2.id],
        )

        # act
        result = task.can_be_completed()

        # assert
        assert result is True

    def test__rcba_and_two_groups_partial_completed__false(self):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_admin(account=account)
        user_2 = create_test_not_admin(account=account)
        group_1 = create_test_group(
            account=account,
            name='Group_1',
            users=[user_1],
        )
        group_2 = create_test_group(
            account=account,
            name='Group_2',
            users=[user_2],
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.tasks.update(require_completion_by_all=True)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.all().delete()

        TaskPerformer.objects.create(
            task=task,
            group=group_1,
            type=PerformerType.GROUP,
            completed_users=[user_1.id],
        )
        TaskPerformer.objects.create(
            task=task,
            group=group_2,
            type=PerformerType.GROUP,
        )

        # act
        result = task.can_be_completed()

        # assert
        assert result is False

    def test__rcba_and_group_directly_deleted__true(self):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_admin(account=account)
        user_2 = create_test_not_admin(account=account)
        group_1 = create_test_group(
            account=account,
            name='Group_1',
            users=[user_1],
        )
        group_2 = create_test_group(
            account=account,
            name='Group_2',
            users=[user_2],
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.tasks.update(require_completion_by_all=True)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.all().delete()
        TaskPerformer.objects.create(
            task=task,
            group=group_1,
            type=PerformerType.GROUP,
            completed_users=[user_1.id],
        )
        TaskPerformer.objects.create(
            task=task,
            group=group_2,
            type=PerformerType.GROUP,
            directly_status=DirectlyStatus.DELETED,
        )

        # act
        result = task.can_be_completed()

        # assert
        assert result is True

    def test__rcba_and_inactive_performer__true(self):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_admin(account=account)
        user_2 = create_test_not_admin(
            account=account,
            status=UserStatus.INACTIVE,
        )
        group = create_test_group(
            account=account,
            users=[user_1, user_2],
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.tasks.update(require_completion_by_all=True)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.all().delete()
        # only active user_1 completed; inactive user_2 is ignored by SQL
        TaskPerformer.objects.create(
            task=task,
            group=group,
            type=PerformerType.GROUP,
            completed_users=[user_1.id],
        )

        # act
        result = task.can_be_completed()

        # assert
        assert result is True

    def test__rcba_and_mixed_user_performer_and_group_performer__true(self):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_not_admin(account=account)
        group = create_test_group(
            account=account,
            users=[user_1],
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.tasks.update(require_completion_by_all=True)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.all().delete()
        TaskPerformer.objects.create(
            task=task,
            group=group,
            type=PerformerType.GROUP,
            completed_users=[user_1.id],
        )
        TaskPerformer.objects.create(
            task=task,
            user=owner,
            type=PerformerType.USER,
            is_completed=True,
        )
        # act
        result = task.can_be_completed()

        # assert
        assert result is True

    def test__rcba_and_soft_deleted_group__true(self):

        """ When a group performer's UserGroup is soft-deleted,
            its members must not appear in the incomplete set —
            the task should be completable. """

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_admin(account=account)
        user_2 = create_test_not_admin(account=account)
        active_group = create_test_group(
            account=account,
            name='ActiveGroup',
            users=[user_1],
        )
        deleted_group = create_test_group(
            account=account,
            name='DeletedGroup',
            users=[user_2],
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.tasks.update(require_completion_by_all=True)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.all().delete()

        TaskPerformer.objects.create(
            task=task,
            group=active_group,
            type=PerformerType.GROUP,
            completed_users=[user_1.id],
        )
        TaskPerformer.objects.create(
            task=task,
            group=deleted_group,
            type=PerformerType.GROUP,
        )

        # soft-delete the second group
        deleted_group.is_deleted = True
        deleted_group.save(update_fields=['is_deleted'])

        # act
        result = task.can_be_completed()

        # assert — deleted group's member is ignored
        assert result is True


class TestCanBeCompletedByUser:

    def test__user_performer__true(self):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.update(is_completed=False)

        # act
        result = task.can_be_completed(by_user=owner)

        # assert
        assert result is True

    def test__user_in_group_performer__true(self):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_not_admin(account=account)
        group = create_test_group(
            account=account,
            users=[user_1],
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.all().delete()

        TaskPerformer.objects.create(
            task=task,
            group=group,
            type=PerformerType.GROUP,
            is_completed=False,
        )

        # act
        result = task.can_be_completed(by_user=user_1)

        # assert
        assert result is True

    def test__other_user_performer_complete__true(self):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_not_admin(account=account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.get(number=1)

        # mark owner's performer as completed
        task.taskperformer_set.update(is_completed=True)

        # add second performer (not completed)
        TaskPerformer.objects.create(
            task=task,
            user=user_1,
            type=PerformerType.USER,
            is_completed=False,
        )

        # act
        result = task.can_be_completed(by_user=user_1)

        # assert
        assert result is True

    def test__user_not_performer__false(self):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_not_admin(account=account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.get(number=1)

        # act
        result = task.can_be_completed(by_user=user_1)

        # assert
        assert result is False

    def test__task_already_completed__false(self):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.tasks.update(status=TaskStatus.COMPLETED)
        task = workflow.tasks.get(number=1)

        # act
        result = task.can_be_completed(by_user=owner)

        # assert
        assert result is False

    def test__rcba_and_user_is_last__true(self):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_admin(account=account)
        user_2 = create_test_not_admin(account=account)
        group = create_test_group(
            account=account,
            users=[user_1, user_2],
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.tasks.update(require_completion_by_all=True)
        task = workflow.tasks.get(number=1)
        # mark owner USER performer as completed
        task.taskperformer_set.update(is_completed=True)
        TaskPerformer.objects.create(
            task=task,
            group=group,
            type=PerformerType.GROUP,
            completed_users=[user_1.id],
        )

        # act
        result = task.can_be_completed(by_user=user_2)

        # assert
        assert result is True

    def test__rcba_and_other_user_performer_incompleted__false(self):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_admin(account=account)
        user_2 = create_test_not_admin(account=account)
        group = create_test_group(
            account=account,
            users=[user_1, user_2],
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.tasks.update(require_completion_by_all=True)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task=task,
            group=group,
            type=PerformerType.GROUP,
            completed_users=[user_1.id],
        )

        # act
        result = task.can_be_completed(by_user=user_2)

        # assert
        assert result is False

    def test__rcba_and_user_already_completed__false(self):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_admin(account=account)
        user_2 = create_test_not_admin(account=account)
        group = create_test_group(
            account=account,
            users=[user_1, user_2],
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.tasks.update(require_completion_by_all=True)
        task = workflow.tasks.get(number=1)
        # mark owner USER performer as completed
        task.taskperformer_set.update(is_completed=True)
        TaskPerformer.objects.create(
            task=task,
            group=group,
            type=PerformerType.GROUP,
            completed_users=[user_1.id, user_2.id],
        )

        # act
        result = task.can_be_completed(by_user=user_1)

        # assert
        assert result is False

    def test__rcba_and_user_not_perf__false(self):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_admin(account=account)
        user_2 = create_test_not_admin(account=account)
        group = create_test_group(
            account=account,
            users=[user_1],
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.tasks.update(require_completion_by_all=True)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.all().delete()
        TaskPerformer.objects.create(
            task=task,
            group=group,
            type=PerformerType.GROUP,
            completed_users=[user_1.id],
        )

        # act
        result = task.can_be_completed(by_user=user_2)

        # assert
        assert result is False

    def test__rcba_and_soft_deleted_group__true(self):

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_admin(account=account)
        user_2 = create_test_not_admin(account=account)
        active_group = create_test_group(
            account=account,
            name='ActiveGroup',
            users=[user_1],
        )
        deleted_group = create_test_group(
            account=account,
            name='DeletedGroup',
            users=[user_2],
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.tasks.update(require_completion_by_all=True)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.all().delete()

        TaskPerformer.objects.create(
            task=task,
            group=active_group,
            type=PerformerType.GROUP,
        )
        TaskPerformer.objects.create(
            task=task,
            group=deleted_group,
            type=PerformerType.GROUP,
        )

        # soft-delete the second group
        deleted_group.is_deleted = True
        deleted_group.save(update_fields=['is_deleted'])

        # act — user_1 is the last remaining incomplete performer
        result = task.can_be_completed(by_user=user_1)

        # assert
        assert result is True
