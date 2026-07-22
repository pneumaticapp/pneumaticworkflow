import pytest
from django.conf import settings

from src.ai.enums import AITaskRunStatus
from src.ai.models import (
    AIAgent,
    AITaskRun,
)
from src.ai.clients.chat_completions import AIRequestError
from src.ai.services.performers import (
    AIPerformerService,
    AITransientError,
)
from src.processes.services.workflow_action import (
    WorkflowActionService,
)
from src.ai.tasks import run_ai_performer
from src.processes.enums import (
    FieldType,
    PerformerType,
    TaskStatus,
)
from src.processes.models.workflows.fields import (
    FieldSelection,
    TaskField,
)
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def ai_performers_enabled(mocker):
    mocker.patch.dict(
        settings.PROJECT_CONF,
        {'AI_PERFORMERS': True},
    )
    mocker.patch.object(
        settings,
        'OPENROUTER_API_KEY',
        'test-platform-key',
    )


def _setup(tasks_count=1, required_string=True):
    user = create_test_user(is_account_owner=True)
    account = user.account
    account.ai_performers_enabled = True
    account.save(update_fields=['ai_performers_enabled'])
    workflow = create_test_workflow(user=user, tasks_count=tasks_count)
    task = workflow.tasks.get(number=1)
    if required_string:
        TaskField.objects.create(
            task=task,
            api_name='field-1',
            name='Summary',
            type=FieldType.STRING,
            is_required=True,
            workflow=workflow,
            account=account,
        )
    agent = AIAgent.objects.create(
        account=account,
        name='Analyst',
        model_slug='test/model',
    )
    TaskPerformer.objects.create(
        task=task,
        ai_agent=agent,
        type=PerformerType.AI,
    )
    return user, workflow, task, agent


def _mock_model(mocker, result):
    return mocker.patch(
        'src.ai.services.performers.ChatCompletionsClient.call_model',
        return_value=result,
    )


def test_run__happy_path__completes_task(mocker):
    _user, _workflow, task, agent = _setup()
    call_model_mock = _mock_model(mocker, {'field-1': 'All good'})

    run_ai_performer(task_id=task.id, agent_id=agent.id)

    task.refresh_from_db()
    assert task.status == TaskStatus.COMPLETED
    field = TaskField.objects.get(task=task, api_name='field-1')
    assert field.value == 'All good'
    run = AITaskRun.objects.get(task=task, agent=agent)
    assert run.status == AITaskRunStatus.COMPLETED
    assert run.model_used == 'test/model'
    assert run.attempts == 1
    call_model_mock.assert_called_once()


def test_run__choice_field__display_value_written(mocker):
    user, workflow, task, agent = _setup(required_string=False)
    field = TaskField.objects.create(
        task=task,
        api_name='field-2',
        name='Verdict',
        type=FieldType.RADIO,
        is_required=True,
        workflow=workflow,
        account=user.account,
    )
    FieldSelection.objects.create(field=field, value='Approved')
    FieldSelection.objects.create(field=field, value='Rejected')
    _mock_model(mocker, {'field-2': 'Approved'})

    run_ai_performer(task_id=task.id, agent_id=agent.id)

    task.refresh_from_db()
    assert task.status == TaskStatus.COMPLETED
    field.refresh_from_db()
    assert field.value == 'Approved'


def test_run__required_user_field__left_for_human(mocker):
    user, workflow, task, agent = _setup()
    TaskField.objects.create(
        task=task,
        api_name='field-user',
        name='Owner',
        type=FieldType.USER,
        is_required=True,
        workflow=workflow,
        account=user.account,
    )
    call_model_mock = _mock_model(mocker, {})

    run_ai_performer(task_id=task.id, agent_id=agent.id)

    task.refresh_from_db()
    assert task.status == TaskStatus.ACTIVE
    run = AITaskRun.objects.get(task=task, agent=agent)
    assert run.status == AITaskRunStatus.LEFT_FOR_HUMAN
    assert 'Owner' in run.reason
    call_model_mock.assert_not_called()


def test_run__incomplete_model_output__left_for_human(mocker):
    _user, _workflow, task, agent = _setup()
    _mock_model(mocker, {'field-1': None})

    run_ai_performer(task_id=task.id, agent_id=agent.id)

    task.refresh_from_db()
    assert task.status == TaskStatus.ACTIVE
    run = AITaskRun.objects.get(task=task, agent=agent)
    assert run.status == AITaskRunStatus.LEFT_FOR_HUMAN
    assert 'Summary' in run.reason


def test_run__already_claimed__drops_silently(mocker):
    _user, _workflow, task, agent = _setup()
    AITaskRun.objects.create(
        task=task,
        agent=agent,
        status=AITaskRunStatus.RUNNING,
    )
    call_model_mock = _mock_model(mocker, {'field-1': 'x'})

    run_ai_performer(task_id=task.id, agent_id=agent.id)

    task.refresh_from_db()
    assert task.status == TaskStatus.ACTIVE
    call_model_mock.assert_not_called()


def test_run__feature_disabled_on_account__drops_silently(mocker):
    user, _workflow, task, agent = _setup()
    account = user.account
    account.ai_performers_enabled = False
    account.save(update_fields=['ai_performers_enabled'])
    call_model_mock = _mock_model(mocker, {'field-1': 'x'})

    run_ai_performer(task_id=task.id, agent_id=agent.id)

    task.refresh_from_db()
    assert task.status == TaskStatus.ACTIVE
    assert not AITaskRun.objects.filter(task=task).exists()
    call_model_mock.assert_not_called()


def test_run__require_completion_by_all__completes_for_agent_only(
    mocker,
):
    _user, _workflow, task, agent = _setup()
    task.require_completion_by_all = True
    task.save(update_fields=['require_completion_by_all'])
    _mock_model(mocker, {'field-1': 'done'})

    run_ai_performer(task_id=task.id, agent_id=agent.id)

    task.refresh_from_db()
    assert task.status == TaskStatus.ACTIVE
    ai_performer = TaskPerformer.objects.get(task=task, ai_agent=agent)
    assert ai_performer.is_completed is True
    run = AITaskRun.objects.get(task=task, agent=agent)
    assert run.status == AITaskRunStatus.COMPLETED


def test_run__no_fillable_fields__completes_without_model_call(mocker):
    _user, _workflow, task, agent = _setup(required_string=False)
    call_model_mock = _mock_model(mocker, {})

    run_ai_performer(task_id=task.id, agent_id=agent.id)

    task.refresh_from_db()
    assert task.status == TaskStatus.COMPLETED
    call_model_mock.assert_not_called()


def test_service_run__transient_provider_error__requeued(mocker):
    _user, _workflow, task, agent = _setup()
    mocker.patch(
        'src.ai.services.performers.ChatCompletionsClient.call_model',
        side_effect=AIRequestError('down', status=503),
    )
    service = AIPerformerService.load(
        task_id=task.id,
        agent_id=agent.id,
    )
    run = service.claim()

    with pytest.raises(AITransientError):
        service.run(run)

    run.refresh_from_db()
    assert run.status == AITaskRunStatus.QUEUED
    assert run.attempts == 1
    task.refresh_from_db()
    assert task.status == TaskStatus.ACTIVE


def test_service_run__hard_provider_error__failed(mocker):
    _user, _workflow, task, agent = _setup()
    mocker.patch(
        'src.ai.services.performers.ChatCompletionsClient.call_model',
        side_effect=AIRequestError('bad key', status=401),
    )

    run_ai_performer(task_id=task.id, agent_id=agent.id)

    task.refresh_from_db()
    assert task.status == TaskStatus.ACTIVE
    run = AITaskRun.objects.get(task=task, agent=agent)
    assert run.status == AITaskRunStatus.FAILED
    assert 'bad key' in run.reason


def _mock_notifications(mocker):
    mocker.patch(
        'src.processes.services.workflow_action'
        '.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action'
        '.send_new_task_websocket.delay',
    )


def test_continue_task__ai_performer__dispatches_run(mocker):
    user, workflow, task, agent = _setup()
    _mock_notifications(mocker)
    delay_mock = mocker.patch(
        'src.ai.tasks.run_ai_performer.delay',
    )
    service = WorkflowActionService(user=user, workflow=workflow)

    service.continue_task(task=task)

    delay_mock.assert_called_once_with(
        task_id=task.id,
        agent_id=agent.id,
    )


def test_continue_task__feature_disabled__no_dispatch(mocker):
    user, workflow, task, _agent = _setup()
    account = user.account
    account.ai_performers_enabled = False
    account.save(update_fields=['ai_performers_enabled'])
    _mock_notifications(mocker)
    delay_mock = mocker.patch(
        'src.ai.tasks.run_ai_performer.delay',
    )
    service = WorkflowActionService(user=user, workflow=workflow)

    service.continue_task(task=task)

    delay_mock.assert_not_called()


def test_continue_task__returned_task__resets_run(mocker):
    user, workflow, task, agent = _setup()
    AITaskRun.objects.create(
        task=task,
        agent=agent,
        status=AITaskRunStatus.LEFT_FOR_HUMAN,
        reason='old reason',
    )
    _mock_notifications(mocker)
    delay_mock = mocker.patch(
        'src.ai.tasks.run_ai_performer.delay',
    )
    service = WorkflowActionService(user=user, workflow=workflow)

    service.continue_task(task=task, is_returned=True)

    assert not AITaskRun.objects.filter(task=task).exists()
    delay_mock.assert_called_once()
