import pytest
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from pneumatic_backend.processes.messages import workflow as messages
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.models import TaskPerformer
from pneumatic_backend.processes.serializers.workflow import (
    WorkflowReturnToTaskSerializer,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.enums import WorkflowStatus
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
)


pytestmark = pytest.mark.django_db


class TestWorkflowRevertToStepSerializer:

    def test_revert_to__current_task__raise_exception(self):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user)
        task = workflow.tasks.get(number=workflow.current_task)
        task.is_completed = True
        task.save(update_fields=['is_completed'])
        task.taskperformer_set.update(is_completed=True)
        workflow.current_task += 1
        workflow.save(update_fields=['current_task'])
        data = {
            'task': workflow.current_task_instance.id
        }
        serializer = WorkflowReturnToTaskSerializer(
            instance=workflow,
            data=data,
            context={
                'user': user,
                'account': user.account,
                'is_superuser': False,
                'auth_type': AuthTokenType.USER
            }
        )

        # act
        with pytest.raises(ValidationError) as ex:
            serializer.is_valid(raise_exception=True)

        assert ex.value.detail['code'] == ErrorCode.VALIDATION_ERROR
        assert ex.value.detail['message'] == messages.MSG_PW_0013

    def test_revert_concrete_task(self):
        user = create_test_user()
        workflow = create_test_workflow(user)
        workflow.tasks.filter(number__lte=2).update(
            date_started=timezone.now(),
            date_completed=timezone.now(),
            is_completed=True,
        )
        TaskPerformer.objects.by_workflow(workflow.id).filter(
            task__number__lte=2
        ).update(is_completed=True)
        workflow.current_task = 3
        workflow.save()
        workflow.tasks.filter(
            number=workflow.current_task
        ).update(date_started=timezone.now())
        data = {
            'task': workflow.tasks.get(number=1).id
        }

        serializer = WorkflowReturnToTaskSerializer(
            instance=workflow,
            data=data,
            context={
                'user': user,
                'account': user.account,
                'is_superuser': False,
                'auth_type': AuthTokenType.USER
            }
        )
        serializer.is_valid(raise_exception=True)
        workflow = serializer.save()
        performers_completed = TaskPerformer.objects.by_workflow(
            workflow.id
        ).completed().exists()

        assert workflow.current_task == 1
        assert workflow.tasks.filter(
            Q(date_started__isnull=False) |
            Q(date_completed__isnull=False) |
            Q(is_completed=True),
            number__gt=1
        ).count() == 0
        assert performers_completed is False

    def test_revert_completed_process(self):
        user = create_test_user()
        workflow = create_test_workflow(user)
        workflow.tasks.update(
            date_started=timezone.now(),
            date_completed=timezone.now(),
            is_completed=True,
        )
        TaskPerformer.objects.by_workflow(workflow.id).update(
            is_completed=True
        )
        workflow.current_task = workflow.tasks_count
        workflow.status = WorkflowStatus.DONE
        workflow.save()
        data = {
            'task': workflow.tasks.get(number=1).id
        }

        serializer = WorkflowReturnToTaskSerializer(
            instance=workflow,
            data=data,
            context={
                'user': user,
                'account': user.account,
                'is_superuser': False,
                'auth_type': AuthTokenType.USER
            }
        )
        serializer.is_valid(raise_exception=True)
        workflow = serializer.save()
        performers_completed = TaskPerformer.objects.by_workflow(
            workflow.id
        ).completed().exists()

        assert workflow.current_task == 1
        assert workflow.tasks.filter(
            Q(date_started__isnull=False) |
            Q(date_completed__isnull=False) |
            Q(is_completed=True),
            number__gt=1
        ).count() == 0
        assert performers_completed is False

    def test_revert_completed_process__to_current_task(self):
        user = create_test_user()
        workflow = create_test_workflow(user)
        workflow.tasks.update(
            date_started=timezone.now(),
            date_completed=timezone.now(),
            is_completed=True,
        )
        TaskPerformer.objects.by_workflow(workflow.id).update(
            is_completed=True
        )
        workflow.current_task = workflow.tasks_count
        workflow.status = WorkflowStatus.DONE
        workflow.save()
        task_revert_to = workflow.current_task_instance
        data = {
            'task': task_revert_to.id
        }

        serializer = WorkflowReturnToTaskSerializer(
            instance=workflow,
            data=data,
            context={
                'user': user,
                'account': user.account,
                'is_superuser': False,
                'auth_type': AuthTokenType.USER
            }
        )
        serializer.is_valid(raise_exception=True)
        workflow = serializer.save()

        assert workflow.current_task == task_revert_to.number
        assert workflow.tasks.filter(
            Q(date_started__isnull=False) |
            Q(date_completed__isnull=False) |
            Q(is_completed=True),
            number__lt=task_revert_to.number
        ).count() == task_revert_to.number - 1
