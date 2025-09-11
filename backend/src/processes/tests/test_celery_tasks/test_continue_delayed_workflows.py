from datetime import timedelta
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from src.authentication.enums import AuthTokenType
from src.processes.models import (
    Delay,
)
from src.processes.tasks.delay import (
    continue_delayed_workflows,
)
from src.processes.tests.fixtures import (
    create_test_owner,
    create_test_workflow,
)
from src.processes.enums import (
    TaskStatus,
)
from src.processes.utils.workflows import (
    resume_delayed_workflows
)
from src.processes.services.workflow_action import (
    WorkflowActionService
)


UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_continue_delayed_workflows__ok(mocker):

    # arrange
    periodic_lock_mock = mocker.patch(
        'src.celery.periodic_lock'
    )
    periodic_lock_mock.__enter__.return_value = True
    resume_delayed_workflows_mock = mocker.patch(
        'src.processes.tasks.delay.resume_delayed_workflows'
    )

    # act
    continue_delayed_workflows()

    # assert
    resume_delayed_workflows_mock.assert_called_once()


def test_resume_delayed_workflows__delay_expired__resume(
    mocker,
    api_client
):

    # arrange
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_workflow_started_webhook.delay',
    )
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay'
    )
    user = create_test_owner()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(
        user=user,
        tasks_count=2
    )
    task_1 = workflow.tasks.get(number=1)
    task_1.status = TaskStatus.DELAYED
    task_1.date_created = timezone.now() - timedelta(hours=2)
    task_1.save()
    Delay.objects.create(
        task=task_1,
        start_date=task_1.date_created,
        duration=timedelta(hours=1),
        workflow=workflow
    )

    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    resume_task_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.resume_task'
    )

    # act
    resume_delayed_workflows()

    # assert
    service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    resume_task_mock.assert_called_once_with(task_1)


def test_resume_delayed_workflows__delay_not_expired__not_resume(
    mocker,
    api_client
):

    # arrange
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_workflow_started_webhook.delay',
    )
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay'
    )
    user = create_test_owner()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(
        user=user,
        tasks_count=2
    )
    task_1 = workflow.tasks.get(number=1)
    task_1.status = TaskStatus.DELAYED
    task_1.date_created = timezone.now() - timedelta(hours=1)
    task_1.save()
    Delay.objects.create(
        task=task_1,
        start_date=task_1.date_created,
        duration=timedelta(hours=2),
        workflow=workflow
    )

    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    resume_task_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.resume_task'
    )

    # act
    resume_delayed_workflows()

    # assert
    service_init_mock.assert_not_called()
    resume_task_mock.assert_not_called()


def test_resume_delayed_workflows__delay_already_ended__not_resume(
    mocker,
    api_client
):

    # arrange
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_workflow_started_webhook.delay',
    )
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay'
    )
    user = create_test_owner()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(
        user=user,
        tasks_count=2
    )
    task_1 = workflow.tasks.get(number=1)
    task_1.status = TaskStatus.DELAYED
    task_1.date_created = timezone.now() - timedelta(hours=2)
    task_1.save()
    Delay.objects.create(
        task=task_1,
        start_date=task_1.date_created,
        duration=timedelta(hours=1),
        end_date=timezone.now(),
        workflow=workflow
    )

    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    resume_task_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.resume_task'
    )

    # act
    resume_delayed_workflows()

    # assert
    service_init_mock.assert_not_called()
    resume_task_mock.assert_not_called()
