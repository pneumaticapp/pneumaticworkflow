from datetime import timedelta
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.models import (
    Workflow,
)
from pneumatic_backend.processes.tasks.delay import (
    continue_delayed_workflows,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    OwnerType,
)
from pneumatic_backend.processes.utils.workflows import (
    resume_delayed_workflows
)
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService
)


UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_continue_delayed_workflows__ok(mocker):

    # arrange
    periodic_lock_mock = mocker.patch(
        'pneumatic_backend.celery.periodic_lock'
    )
    periodic_lock_mock.__enter__.return_value = True
    resume_delayed_workflows_mock = mocker.patch(
        'pneumatic_backend.processes.tasks.delay.resume_delayed_workflows'
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
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_workflow_started_webhook.delay',
    )
    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay'
    )
    user = create_test_user()
    api_client.token_authenticate(user)

    # act
    response_create = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id
                },
            ],
            'kickoff': {},
            'is_active': True,
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                },
                {
                    'number': 2,
                    'name': 'Second step',
                    'delay': '01:00:00',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    template_id = response_create.data['id']
    response_run = api_client.post(
        path=f'/templates/{template_id}/run',
        data={'name': 'Test template'}
    )
    workflow_id = response_run.data['id']
    workflow = Workflow.objects.get(id=workflow_id)

    response_complete = api_client.post(
        path=f'/workflows/{workflow_id}/task-complete',
        data={'task_id': workflow.current_task_instance.id}
    )
    workflow.refresh_from_db()
    current_task = workflow.tasks.get(number=2)
    delay = current_task.get_active_delay()
    delay.start_date = (timezone.now() - timedelta(days=2))
    delay.save()

    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    resume_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.'
        'workflow_action.WorkflowActionService.resume_workflow'
    )
    workflow.refresh_from_db()

    # act
    resume_delayed_workflows()

    # assert
    assert response_run.status_code == 200
    assert response_complete.status_code == 204
    workflow.refresh_from_db()
    service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    resume_workflow_mock.assert_called_once_with()


def test_resume_delayed_workflows__delay_not_expired__not_resume(
    mocker,
    api_client
):

    # arrange
    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_workflow_started_webhook.delay',
    )
    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay'
    )
    user = create_test_user()
    api_client.token_authenticate(user)

    # act
    response_create = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id
                },
            ],
            'kickoff': {},
            'is_active': True,
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                },
                {
                    'number': 2,
                    'name': 'Second step',
                    'delay': '01:00:00',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    template_id = response_create.data['id']
    response_run = api_client.post(
        path=f'/templates/{template_id}/run',
        data={'name': 'Test template'}
    )
    workflow_id = response_run.data['id']
    workflow = Workflow.objects.get(id=workflow_id)

    response_complete = api_client.post(
        path=f'/workflows/{workflow_id}/task-complete',
        data={'task_id': workflow.current_task_instance.id}
    )
    workflow.refresh_from_db()

    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    resume_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.'
        'workflow_action.WorkflowActionService.resume_workflow'
    )
    workflow.refresh_from_db()

    # act
    resume_delayed_workflows()

    # assert
    assert response_run.status_code == 200
    assert response_complete.status_code == 204
    workflow.refresh_from_db()
    service_init_mock.assert_not_called()
    resume_workflow_mock.assert_not_called()
