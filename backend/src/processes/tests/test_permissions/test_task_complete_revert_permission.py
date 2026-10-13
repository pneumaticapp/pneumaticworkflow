from unittest.mock import Mock

import pytest
from django.utils import timezone

from src.processes.enums import PerformerType
from src.processes.models.workflows.task import TaskPerformer
from src.processes.permissions import (
    TaskCompletePermission,
    TaskRevertPermission,
)
from src.processes.serializers.workflows.task import TaskSerializer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_not_admin,
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


class TestTaskCompletePermission:

    def test_has_permission__group_user_only__false(self):

        """
        Ghost GROUP_USER without USER/GROUP assignment
        → TaskCompletePermission is False for non-owner
        """

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_not_admin(account=account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.filter(task_id=task.id).delete()
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=user_1.id,
            type=PerformerType.GROUP_USER,
            is_completed=True,
            date_completed=timezone.now(),
        )
        request = Mock()
        request.user = user_1
        request.task_id = None
        view = Mock()
        view.kwargs = {'pk': str(task.id)}
        permission = TaskCompletePermission()

        # act
        result = permission.has_permission(request=request, view=view)

        # assert
        assert result is False

    def test_has_permission__user_performer__ok(self):

        """
        USER assignment → TaskCompletePermission is True
        """

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_not_admin(account=account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.filter(task_id=task.id).delete()
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=user_1.id,
            type=PerformerType.USER,
        )
        request = Mock()
        request.user = user_1
        request.task_id = None
        view = Mock()
        view.kwargs = {'pk': str(task.id)}
        permission = TaskCompletePermission()

        # act
        result = permission.has_permission(request=request, view=view)

        # assert
        assert result is True

    def test_has_permission__group_performer__ok(self):

        """
        GROUP membership → TaskCompletePermission is True
        """

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_not_admin(account=account)
        group_1 = create_test_group(account=account, users=[user_1])
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.filter(task_id=task.id).delete()
        TaskPerformer.objects.create(
            task_id=task.id,
            type=PerformerType.GROUP,
            group_id=group_1.id,
        )
        request = Mock()
        request.user = user_1
        request.task_id = None
        view = Mock()
        view.kwargs = {'pk': str(task.id)}
        permission = TaskCompletePermission()

        # act
        result = permission.has_permission(request=request, view=view)

        # assert
        assert result is True


class TestTaskRevertPermission:

    def test_has_permission__group_user_only__false(self):

        """
        Ghost GROUP_USER without USER/GROUP assignment
        → TaskRevertPermission is False for non-owner
        """

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_not_admin(account=account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.filter(task_id=task.id).delete()
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=user_1.id,
            type=PerformerType.GROUP_USER,
            is_completed=True,
            date_completed=timezone.now(),
        )
        request = Mock()
        request.user = user_1
        view = Mock()
        view.kwargs = {'pk': str(task.id)}
        permission = TaskRevertPermission()

        # act
        result = permission.has_permission(request=request, view=view)

        # assert
        assert result is False


class TestTaskSerializerIsReadOnlyViewer:

    def test_get_is_read_only_viewer__group_user_only__true(self):

        """
        Only GROUP_USER, not assignment performer / admin owner
        → is_read_only_viewer is True
        """

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_not_admin(account=account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.filter(task_id=task.id).delete()
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=user_1.id,
            type=PerformerType.GROUP_USER,
            is_completed=True,
            date_completed=timezone.now(),
        )
        serializer = TaskSerializer(context={'user': user_1})

        # act
        result = serializer.get_is_read_only_viewer(instance=task)

        # assert
        assert result is True

    def test_get_is_read_only_viewer__user_performer__false(self):

        """
        USER assignment → is_read_only_viewer is False
        """

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_not_admin(account=account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.filter(task_id=task.id).delete()
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=user_1.id,
            type=PerformerType.USER,
        )
        serializer = TaskSerializer(context={'user': user_1})

        # act
        result = serializer.get_is_read_only_viewer(instance=task)

        # assert
        assert result is False

    def test_get_is_read_only_viewer__group_performer__false(self):

        """
        GROUP membership → is_read_only_viewer is False
        """

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user_1 = create_test_admin(account=account)
        group_1 = create_test_group(account=account, users=[user_1])
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.filter(task_id=task.id).delete()
        TaskPerformer.objects.create(
            task_id=task.id,
            type=PerformerType.GROUP,
            group_id=group_1.id,
        )
        serializer = TaskSerializer(context={'user': user_1})

        # act
        result = serializer.get_is_read_only_viewer(instance=task)

        # assert
        assert result is False
