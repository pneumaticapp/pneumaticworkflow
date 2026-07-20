import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from src.accounts.validators import (
    user_is_last_performer,
)
from src.processes.enums import PerformerType, TaskStatus
from src.processes.models.workflows.task import Task, TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
    create_test_template,
    create_test_user,
    create_test_workflow, create_test_group,
)

pytestmark = pytest.mark.django_db
UserModel = get_user_model()


class TestTemplateTask:

    def test_user_is_last_performer__exist__ok(self):

        # arrange
        user = create_test_user()
        template = create_test_template(user, tasks_count=1, is_active=True)
        template_task = template.tasks.get(number=1)
        template_task.raw_performers.all().delete()
        template_task.add_raw_performer(user)

        # act
        result = user_is_last_performer(user)

        # assert
        assert result is True

    def test_user_is_last_performer__not_exist__not_found(self):

        # arrange
        user = create_test_user()
        template = create_test_template(user, tasks_count=1, is_active=True)
        template_task = template.tasks.get(number=1)
        template_task.raw_performers.all().delete()
        template_task.add_raw_performer(
            performer_type=PerformerType.WORKFLOW_STARTER,
        )

        # act
        result = user_is_last_performer(user)

        # assert
        assert result is False

    def test_user_is_last_performer__template_inactive__not_found(self):

        # arrange
        user = create_test_user()
        template = create_test_template(user, tasks_count=1, is_active=False)
        template_task = template.tasks.get(number=1)
        template_task.raw_performers.all().delete()
        template_task.add_raw_performer(user)

        # act
        result = user_is_last_performer(user)

        # assert
        assert result is False

    def test_user_is_last_performer__not_last__not_found(self):

        # arrange
        user = create_test_user()
        template = create_test_template(user, tasks_count=1, is_active=False)
        template_task = template.tasks.get(number=1)
        template_task.raw_performers.all().delete()
        user_2 = create_test_user(
            email='performer@test.test',
            account=user.account,
        )
        template_task.add_raw_performer(user)
        template_task.add_raw_performer(user_2)

        # act
        result = user_is_last_performer(user)

        # assert
        assert result is False


class TestWorkflowTask:

    def test_user_is_last_performer__exist__ok(self):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=1)
        user_performer = create_test_user(
            email='performer@test.test',
            account=user.account,
        )
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.all().delete()
        task.raw_performers.all().delete()
        task.add_raw_performer(user_performer)
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=user_performer.id,
        )

        # act
        result = user_is_last_performer(user_performer)

        # assert
        assert result is True

    def test_user_is_last_performer__not_last__not_found(self):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.all().delete()
        task.raw_performers.all().delete()

        user_2 = create_test_user(
            email='performer@test.test',
            account=user.account,
        )
        task.add_raw_performer(user)
        task.add_raw_performer(user_2)
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=user.id,
        )
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=user_2.id,
        )

        # act
        result = user_is_last_performer(user_2)

        # assert
        assert result is False

    def test_user_is_last__not_raw_performer__not_found(self):

        """ Invalid case """

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        workflow = create_test_workflow(owner, tasks_count=1)
        performer = create_test_admin(account=account)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.all().delete()
        task.raw_performers.all().delete()
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=performer.id,
        )

        # act
        result = user_is_last_performer(performer)

        # assert
        assert result is False

    @pytest.mark.parametrize('status', (
        TaskStatus.PENDING,
        TaskStatus.DELAYED,
        TaskStatus.ACTIVE,
    ))
    def test_user_is_last_performer__active_task__ok(self, status):

        # arrange
        account = create_test_account()
        owner = create_test_user(account=account)
        workflow = create_test_workflow(owner, tasks_count=1)
        user_performer = create_test_admin(account=account)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.all().delete()
        task.raw_performers.all().delete()
        task.status = status
        task.save()
        task.add_raw_performer(user_performer)
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=user_performer.id,
        )

        # act
        result = user_is_last_performer(user_performer)

        # assert
        assert result is True

    @pytest.mark.parametrize('status', (
        TaskStatus.COMPLETED,
        TaskStatus.SKIPPED,
    ))
    def test_user_is_last_performer__not_active_task__not_found(self, status):

        # arrange
        account = create_test_account()
        owner = create_test_user(account=account)
        workflow = create_test_workflow(owner, tasks_count=1)
        user_performer = create_test_admin(account=account)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.all().delete()
        task.raw_performers.all().delete()
        task.status = status
        task.save()
        task.add_raw_performer(user_performer)
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=user_performer.id,
        )

        # act
        result = user_is_last_performer(user_performer)

        # assert
        assert result is False

    def test_user_is_last_performer__group_user__false(self):

        """
        Only completed GROUP_USER (no USER assignment)
        → user_is_last_performer is False; on_performer is empty
        """

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_admin(account=account)
        group = create_test_group(account=account, users=[user_1])
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.get(number=1)
        task.taskperformer_set.all().delete()
        TaskPerformer.objects.create(
            task_id=task.id,
            group=group,
            type=PerformerType.GROUP,
        )

        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=user_1.id,
            type=PerformerType.GROUP_USER,
            is_completed=True,
            date_completed=timezone.now(),
        )

        # act
        result = user_is_last_performer(user_1)

        # assert
        assert result is False
        assert not (
            Task.objects
            .on_performer(user_1.id)
            .filter(id=task.id)
            .exists()
        )
