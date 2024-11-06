import pytest
from django.conf import settings
from rest_framework.exceptions import ValidationError

from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.messages import workflow as messages
from pneumatic_backend.processes.models import (
    TaskPerformer
)
from pneumatic_backend.processes.serializers.workflow import (
    WorkflowRevertSerializer,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_invited_user,
)


pytestmark = pytest.mark.django_db


class TestWorkflowRevert:

    def test_revert__first_task__validation_error(self):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user)
        serializer = WorkflowRevertSerializer(
            instance=workflow,
            data={},
            context={
                'user': user,
                'is_superuser': False,
                'auth_type': AuthTokenType.USER
            }
        )

        # act
        with pytest.raises(ValidationError) as ex:
            serializer.is_valid(raise_exception=True)

        # assert
        assert ex.value.detail['code'] == ErrorCode.VALIDATION_ERROR
        assert ex.value.detail['message'] == messages.MSG_PW_0012

    def test_revert__ok(self):
        user = create_test_user()
        workflow = create_test_workflow(user)
        task = workflow.tasks.get(number=workflow.current_task)
        task.is_completed = True
        task.save(update_fields=['is_completed'])
        task.taskperformer_set.update(is_completed=True)
        workflow.current_task += 1
        workflow.save(update_fields=['current_task'])
        current_task = workflow.current_task

        serializer = WorkflowRevertSerializer(
            instance=workflow,
            data={},
            context={
                'user': user,
                'is_superuser': False,
                'auth_type': AuthTokenType.USER
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        workflow.refresh_from_db()
        task = workflow.tasks.get(number=current_task)
        completed_performer = task.taskperformer_set.completed()

        assert workflow.current_task == current_task - 1
        assert task.is_completed is False
        assert completed_performer.exists() is False

    def test_revert_multiple_performers__ok(self):
        user = create_test_user()
        invited = create_invited_user(user)
        workflow = create_test_workflow(user)

        task = workflow.current_task_instance
        task.is_completed = True
        task.require_completion_by_all = True
        task.save(update_fields=['is_completed', 'require_completion_by_all'])
        raw_performer = task.add_raw_performer(invited)
        task.update_performers(raw_performer)
        TaskPerformer.objects.by_task(task.id).update(is_completed=True)

        workflow.current_task += 1
        workflow.save(update_fields=['current_task'])
        current_task = workflow.current_task

        serializer = WorkflowRevertSerializer(
            instance=workflow,
            data={},
            context={
                'user': user,
                'is_superuser': False,
                'auth_type': AuthTokenType.USER
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        workflow.refresh_from_db()
        task = workflow.tasks.get(number=current_task)
        performers_completed = TaskPerformer.objects.by_task(
            task
        ).completed()

        assert workflow.current_task == current_task - 1
        assert task.is_completed is False
        assert performers_completed.exists() is False

    def test_revert_revert_task_notification__sended(self, mocker):
        user = create_test_user()
        workflow = create_test_workflow(user)
        task = workflow.tasks.get(number=workflow.current_task)
        task.is_completed = True
        task.save(update_fields=['is_completed'])
        workflow.current_task += 1
        workflow.save(update_fields=['current_task'])

        send_new_task_notification_mock = mocker.patch(
            'pneumatic_backend.processes.services.workflow_action.'
            'send_new_task_notification.delay'
        )
        mocker.patch(
            'django.conf.settings.CONFIGURATION_CURRENT',
            settings.CONFIGURATION_STAGING
        )

        serializer = WorkflowRevertSerializer(
            instance=workflow,
            data={},
            context={
                'user': user,
                'is_superuser': False,
                'auth_type': AuthTokenType.USER
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        workflow.refresh_from_db()

        send_new_task_notification_mock.assert_called_once()
