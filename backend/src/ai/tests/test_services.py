import pytest
from django.conf import settings
from django.test import override_settings
from django.utils import timezone

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
from src.accounts.enums import NotificationType
from src.accounts.models import Notification
from src.notifications.tasks import (
    _send_ai_completed_task_notification,
    _send_ai_left_task_notification,
)
from src.processes.services.exceptions import AIPerformersStillWorking
from src.processes.enums import (
    FieldType,
    PerformerType,
    TaskStatus,
    WorkflowEventType,
)
from src.processes.models.workflows.event import WorkflowEvent
from src.storage.services.exceptions import (
    FileDownloadException,
    FileServiceConnectionFailedException,
    FileUploadException,
)
from src.storage.services.file_service import FileServiceClient
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


def _setup(tasks_count=1, required_string=True, human_performer=False):
    user = create_test_user(is_account_owner=True)
    account = user.account
    account.ai_performers_enabled = True
    account.save(update_fields=['ai_performers_enabled'])
    workflow = create_test_workflow(user=user, tasks_count=tasks_count)
    task = workflow.tasks.get(number=1)
    if not human_performer:
        # the default shape: the agent is the sole performer
        TaskPerformer.objects.filter(task=task).delete()
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
    _user, _workflow, task, agent = _setup(human_performer=True)
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
    # The agent's share is recorded on the timeline even though the
    # task is still waiting for the human co-performers
    event = WorkflowEvent.objects.get(
        task=task,
        type=WorkflowEventType.AI_AGENT_COMPLETED,
    )
    assert event.text == agent.name


def test_run__human_co_performer__completes_for_agent_only(mocker):

    """ AI drafts, human approves: on a shared task the agent fills
        its output and waits — it never closes the task over an
        active human performer, even without "completion by all" """

    user, _workflow, task, agent = _setup(human_performer=True)
    _mock_model(mocker, {'field-1': 'Draft ready'})

    run_ai_performer(task_id=task.id, agent_id=agent.id)

    task.refresh_from_db()
    assert task.status == TaskStatus.ACTIVE
    ai_performer = TaskPerformer.objects.get(task=task, ai_agent=agent)
    assert ai_performer.is_completed is True
    human_performer = TaskPerformer.objects.get(task=task, user=user)
    assert human_performer.is_completed is False
    field = TaskField.objects.get(task=task, api_name='field-1')
    assert field.value == 'Draft ready'
    run = AITaskRun.objects.get(task=task, agent=agent)
    assert run.status == AITaskRunStatus.COMPLETED
    assert WorkflowEvent.objects.filter(
        task=task,
        type=WorkflowEventType.AI_AGENT_COMPLETED,
    ).exists()


def test_run__human_completes_after_agent__task_completed(mocker):
    user, workflow, task, agent = _setup(human_performer=True)
    _mock_model(mocker, {'field-1': 'Draft ready'})
    run_ai_performer(task_id=task.id, agent_id=agent.id)

    service = WorkflowActionService(user=user, workflow=workflow)
    service.complete_task_for_user(task=task)

    task.refresh_from_db()
    assert task.status == TaskStatus.COMPLETED


def test_run__agent_last_pending_by_all__completes_task(mocker):

    """ With "completion by all", the agent closing the task as the
        last pending performer is still allowed — every human already
        completed their share """

    user, _workflow, task, agent = _setup(human_performer=True)
    task.require_completion_by_all = True
    task.save(update_fields=['require_completion_by_all'])
    TaskPerformer.objects.filter(task=task, user=user).update(
        is_completed=True,
        date_completed=timezone.now(),
    )
    _mock_model(mocker, {'field-1': 'done'})

    run_ai_performer(task_id=task.id, agent_id=agent.id)

    task.refresh_from_db()
    assert task.status == TaskStatus.COMPLETED


def test_run__human_co_performer__draft_notification_sent(mocker):
    user, _workflow, task, agent = _setup(human_performer=True)
    _mock_model(mocker, {'field-1': 'Draft ready'})
    notification_mock = mocker.patch(
        'src.ai.services.performers.'
        'send_ai_completed_task_notification.delay',
    )

    run_ai_performer(task_id=task.id, agent_id=agent.id)

    notification_mock.assert_called_once()
    kwargs = notification_mock.call_args[1]
    assert kwargs['task_id'] == task.id
    assert kwargs['agent_name'] == agent.name
    assert kwargs['recipients'] == [(user.id, user.email)]


def test_run__sole_performer__no_draft_notification(mocker):
    _user, _workflow, task, agent = _setup()
    _mock_model(mocker, {'field-1': 'All good'})
    notification_mock = mocker.patch(
        'src.ai.services.performers.'
        'send_ai_completed_task_notification.delay',
    )

    run_ai_performer(task_id=task.id, agent_id=agent.id)

    task.refresh_from_db()
    assert task.status == TaskStatus.COMPLETED
    notification_mock.assert_not_called()


def test_send_ai_completed_task_notification__creates_row(mocker):
    user, _workflow, task, _agent = _setup()
    send_mock = mocker.patch('src.notifications.tasks._send_notification')

    _send_ai_completed_task_notification(
        logging=False,
        account_id=user.account_id,
        recipients=[(user.id, user.email)],
        task_id=task.id,
        agent_name='Analyst',
    )

    notification = Notification.objects.get(
        user_id=user.id,
        type=NotificationType.AI_COMPLETED_TASK,
    )
    assert notification.task_id == task.id
    assert notification.text == 'Analyst is done'
    send_mock.assert_called_once()


def test_complete_for_user__agent_still_working__blocked():
    user, workflow, task, agent = _setup(human_performer=True)
    AITaskRun.objects.create(
        task=task,
        agent=agent,
        status=AITaskRunStatus.RUNNING,
    )
    service = WorkflowActionService(user=user, workflow=workflow)

    with pytest.raises(AIPerformersStillWorking):
        service.complete_task_for_user(task=task)

    task.refresh_from_db()
    assert task.status == TaskStatus.ACTIVE


def test_complete_for_user__agent_not_dispatched_yet__blocked():
    user, workflow, task, _agent = _setup(human_performer=True)
    service = WorkflowActionService(user=user, workflow=workflow)

    with pytest.raises(AIPerformersStillWorking):
        service.complete_task_for_user(task=task)


def test_complete_for_user__agent_left_for_human__ok():
    user, workflow, task, agent = _setup(human_performer=True)
    AITaskRun.objects.create(
        task=task,
        agent=agent,
        status=AITaskRunStatus.LEFT_FOR_HUMAN,
        reason='cannot fill',
    )
    service = WorkflowActionService(user=user, workflow=workflow)

    service.complete_task_for_user(
        task=task,
        fields_values={'field-1': 'human filled it'},
    )

    task.refresh_from_db()
    assert task.status == TaskStatus.COMPLETED


def test_complete_for_user__agent_run_failed__ok():
    user, workflow, task, agent = _setup(human_performer=True)
    AITaskRun.objects.create(
        task=task,
        agent=agent,
        status=AITaskRunStatus.FAILED,
        reason='missing api_key',
    )
    service = WorkflowActionService(user=user, workflow=workflow)

    service.complete_task_for_user(
        task=task,
        fields_values={'field-1': 'human filled it'},
    )

    task.refresh_from_db()
    assert task.status == TaskStatus.COMPLETED


def test_complete_for_user__feature_disabled__inert_agent_not_blocking():
    user, workflow, task, _agent = _setup(human_performer=True)
    account = user.account
    account.ai_performers_enabled = False
    account.save(update_fields=['ai_performers_enabled'])
    service = WorkflowActionService(user=user, workflow=workflow)

    service.complete_task_for_user(
        task=task,
        fields_values={'field-1': 'human filled it'},
    )

    task.refresh_from_db()
    assert task.status == TaskStatus.COMPLETED


def test_complete_for_user__agent_removed__not_blocking():
    user, workflow, task, agent = _setup(human_performer=True)
    TaskPerformer.objects.filter(task=task, ai_agent=agent).delete()
    service = WorkflowActionService(user=user, workflow=workflow)

    service.complete_task_for_user(
        task=task,
        fields_values={'field-1': 'human filled it'},
    )

    task.refresh_from_db()
    assert task.status == TaskStatus.COMPLETED


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


def test_run__usage__recorded_on_run(mocker):

    """ Token counts and the served model name from the provider
        response land on the AITaskRun row """

    _user, _workflow, task, agent = _setup()
    response = mocker.Mock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {
        'model': 'served/model-x',
        'usage': {'prompt_tokens': 100, 'completion_tokens': 20},
        'choices': [
            {
                'finish_reason': 'stop',
                'message': {'content': '{"field-1": "All good"}'},
            },
        ],
    }
    mocker.patch(
        'src.ai.clients.chat_completions.requests.post',
        return_value=response,
    )

    run_ai_performer(task_id=task.id, agent_id=agent.id)

    run = AITaskRun.objects.get(task=task, agent=agent)
    assert run.status == AITaskRunStatus.COMPLETED
    assert run.model_used == 'served/model-x'
    assert run.prompt_tokens == 100
    assert run.completion_tokens == 20


def test_run__happy_path__creates_ai_completed_event(mocker):

    """ The workflow log records the completion under the agent,
        not under the acting account owner """

    _user, _workflow, task, agent = _setup()
    _mock_model(mocker, {'field-1': 'All good'})

    run_ai_performer(task_id=task.id, agent_id=agent.id)

    event = WorkflowEvent.objects.get(
        task=task,
        type=WorkflowEventType.AI_AGENT_COMPLETED,
    )
    assert event.text == agent.name
    assert event.user is None
    assert not WorkflowEvent.objects.filter(
        task=task,
        type=WorkflowEventType.TASK_COMPLETE,
    ).exists()


def test_run__left_for_human__event_and_notification(mocker):
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
    notification_mock = mocker.patch(
        'src.ai.services.performers.send_ai_left_task_notification.delay',
    )

    run_ai_performer(task_id=task.id, agent_id=agent.id)

    event = WorkflowEvent.objects.get(
        task=task,
        type=WorkflowEventType.AI_AGENT_LEFT,
    )
    assert agent.name in event.text
    assert 'Owner' in event.text
    assert event.user is None
    notification_mock.assert_called_once()
    kwargs = notification_mock.call_args[1]
    assert kwargs['task_id'] == task.id
    assert kwargs['agent_name'] == agent.name
    # AI-only task: falls back to the workflow starter
    assert kwargs['recipients'] == [(user.id, user.email)]


def test_send_ai_left_task_notification__creates_notification_row(mocker):
    user, _workflow, task, _agent = _setup()
    send_mock = mocker.patch('src.notifications.tasks._send_notification')

    _send_ai_left_task_notification(
        logging=False,
        account_id=user.account_id,
        recipients=[(user.id, user.email)],
        task_id=task.id,
        agent_name='Analyst',
        reason='Required fields an AI agent cannot fill: "Owner"',
    )

    notification = Notification.objects.get(
        user_id=user.id,
        type=NotificationType.AI_LEFT_TASK,
    )
    assert notification.task_id == task.id
    assert notification.text == (
        'Analyst: Required fields an AI agent cannot fill: "Owner"'
    )
    send_mock.assert_called_once()


_FILES_URL = 'https://files.test'


def _attachment_setup(mocker, download_result):
    user, workflow, task, agent = _setup()
    task.description = (
        'Review [report.txt](https://files.test/abc12345xyz)'
    )
    task.save(update_fields=['description'])
    download_mock = mocker.patch.object(
        FileServiceClient,
        'download_file',
        return_value=download_result,
    )
    return user, workflow, task, agent, download_mock


def test_run__text_attachment__included_in_prompt(mocker):
    _user, _workflow, task, agent, download_mock = _attachment_setup(
        mocker,
        download_result=(b'quarterly numbers', 'text/plain'),
    )
    call_model_mock = _mock_model(mocker, {'field-1': 'ok'})

    with override_settings(
        FILE_SERVICE_URL=_FILES_URL,
        FILE_SERVICE_HOST_PATH='files.test',
    ):
        run_ai_performer(task_id=task.id, agent_id=agent.id)

    task.refresh_from_db()
    assert task.status == TaskStatus.COMPLETED
    download_mock.assert_called_once_with('abc12345xyz')
    user_content = call_model_mock.call_args[1]['user_content']
    assert isinstance(user_content, str)
    assert '--- Attached document: report.txt ---' in user_content
    assert 'quarterly numbers' in user_content


def test_run__image_attachment__vision_blocks(mocker):
    _user, _workflow, task, agent, _download_mock = _attachment_setup(
        mocker,
        download_result=(b'\x89PNG bytes', 'image/png'),
    )
    call_model_mock = _mock_model(mocker, {'field-1': 'ok'})

    with override_settings(
        FILE_SERVICE_URL=_FILES_URL,
        FILE_SERVICE_HOST_PATH='files.test',
    ):
        run_ai_performer(task_id=task.id, agent_id=agent.id)

    user_content = call_model_mock.call_args[1]['user_content']
    assert isinstance(user_content, list)
    assert user_content[0]['type'] == 'text'
    assert 'The image "report.txt"' in user_content[0]['text']
    assert user_content[1]['type'] == 'image_url'
    assert user_content[1]['image_url']['url'].startswith(
        'data:image/png;base64,',
    )


def test_run__attachment_download_404__left_for_human(mocker):
    user, _workflow, task, agent, download_mock = _attachment_setup(
        mocker,
        download_result=None,
    )
    download_mock.side_effect = FileDownloadException(status_code=404)
    call_model_mock = _mock_model(mocker, {'field-1': 'ok'})
    mocker.patch(
        'src.ai.services.performers.send_ai_left_task_notification.delay',
    )

    with override_settings(
        FILE_SERVICE_URL=_FILES_URL,
        FILE_SERVICE_HOST_PATH='files.test',
    ):
        run_ai_performer(task_id=task.id, agent_id=agent.id)

    task.refresh_from_db()
    assert task.status == TaskStatus.ACTIVE
    run = AITaskRun.objects.get(task=task, agent=agent)
    assert run.status == AITaskRunStatus.LEFT_FOR_HUMAN
    assert 'could not be downloaded' in run.reason
    assert 'report.txt' in run.reason
    call_model_mock.assert_not_called()


def test_service_run__file_service_down__requeued(mocker):
    _user, _workflow, task, agent, download_mock = _attachment_setup(
        mocker,
        download_result=None,
    )
    download_mock.side_effect = FileServiceConnectionFailedException()
    _mock_model(mocker, {'field-1': 'ok'})

    with override_settings(
        FILE_SERVICE_URL=_FILES_URL,
        FILE_SERVICE_HOST_PATH='files.test',
    ):
        service = AIPerformerService.load(
            task_id=task.id,
            agent_id=agent.id,
        )
        run = service.claim()

        with pytest.raises(AITransientError):
            service.run(run)

    run.refresh_from_db()
    assert run.status == AITaskRunStatus.QUEUED


def test_run__no_file_service_configured__no_download(mocker):
    _user, _workflow, task, agent, download_mock = _attachment_setup(
        mocker,
        download_result=(b'x', 'text/plain'),
    )
    _mock_model(mocker, {'field-1': 'ok'})

    with override_settings(
        FILE_SERVICE_URL=None,
        FILE_SERVICE_HOST_PATH=None,
    ):
        run_ai_performer(task_id=task.id, agent_id=agent.id)

    task.refresh_from_db()
    assert task.status == TaskStatus.COMPLETED
    download_mock.assert_not_called()


def _file_field_setup(mocker, is_required=True):
    user, workflow, task, agent = _setup(required_string=False)
    TaskField.objects.create(
        task=task,
        api_name='field-report',
        name='Report',
        type=FieldType.FILE,
        is_required=is_required,
        workflow=workflow,
        account=user.account,
    )
    upload_mock = mocker.patch.object(
        FileServiceClient,
        'upload_file_with_attachment',
        return_value='https://files.test/gen12345xyz',
    )
    return user, workflow, task, agent, upload_mock


def test_run__file_field__document_uploaded_and_linked(mocker):
    _user, _workflow, task, agent, upload_mock = _file_field_setup(mocker)
    _mock_model(
        mocker,
        {
            'field-report': {
                'filename': 'screening.md',
                'content': '# Screening summary',
            },
        },
    )

    with override_settings(
        FILE_SERVICE_URL=_FILES_URL,
        FILE_SERVICE_HOST_PATH='files.test',
    ):
        run_ai_performer(task_id=task.id, agent_id=agent.id)

    task.refresh_from_db()
    assert task.status == TaskStatus.COMPLETED
    upload_mock.assert_called_once_with(
        file_content=b'# Screening summary',
        filename='screening.md',
        content_type='text/markdown',
        account=agent.account,
    )
    field = TaskField.objects.get(task=task, api_name='field-report')
    assert field.markdown_value == (
        '[screening.md](https://files.test/gen12345xyz)'
    )
    run = AITaskRun.objects.get(task=task, agent=agent)
    assert run.status == AITaskRunStatus.COMPLETED


def test_run__file_field__upload_connection_error__requeued(mocker):
    _user, _workflow, task, agent, upload_mock = _file_field_setup(mocker)
    upload_mock.side_effect = FileServiceConnectionFailedException()
    _mock_model(
        mocker,
        {'field-report': {'filename': 'a.md', 'content': 'text'}},
    )

    with override_settings(
        FILE_SERVICE_URL=_FILES_URL,
        FILE_SERVICE_HOST_PATH='files.test',
    ):
        service = AIPerformerService.load(
            task_id=task.id,
            agent_id=agent.id,
        )
        run = service.claim()

        with pytest.raises(AITransientError):
            service.run(run)

    run.refresh_from_db()
    assert run.status == AITaskRunStatus.QUEUED
    task.refresh_from_db()
    assert task.status == TaskStatus.ACTIVE


def test_run__file_field__upload_rejected__left_for_human(mocker):
    _user, _workflow, task, agent, upload_mock = _file_field_setup(mocker)
    upload_mock.side_effect = FileUploadException()
    _mock_model(
        mocker,
        {'field-report': {'filename': 'a.md', 'content': 'text'}},
    )
    mocker.patch(
        'src.ai.services.performers.send_ai_left_task_notification.delay',
    )

    with override_settings(
        FILE_SERVICE_URL=_FILES_URL,
        FILE_SERVICE_HOST_PATH='files.test',
    ):
        run_ai_performer(task_id=task.id, agent_id=agent.id)

    task.refresh_from_db()
    assert task.status == TaskStatus.ACTIVE
    run = AITaskRun.objects.get(task=task, agent=agent)
    assert run.status == AITaskRunStatus.LEFT_FOR_HUMAN
    assert 'could not be uploaded' in run.reason


def test_run__file_field__bad_shape__left_for_human(mocker):
    _user, _workflow, task, agent, upload_mock = _file_field_setup(mocker)
    _mock_model(mocker, {'field-report': 'just text, not a document'})
    mocker.patch(
        'src.ai.services.performers.send_ai_left_task_notification.delay',
    )

    with override_settings(
        FILE_SERVICE_URL=_FILES_URL,
        FILE_SERVICE_HOST_PATH='files.test',
    ):
        run_ai_performer(task_id=task.id, agent_id=agent.id)

    task.refresh_from_db()
    assert task.status == TaskStatus.ACTIVE
    run = AITaskRun.objects.get(task=task, agent=agent)
    assert run.status == AITaskRunStatus.LEFT_FOR_HUMAN
    assert '{filename, content}' in run.reason
    upload_mock.assert_not_called()


def test_run__required_file_field__no_file_service__left_for_human(mocker):
    _user, _workflow, task, agent, upload_mock = _file_field_setup(mocker)
    call_model_mock = _mock_model(mocker, {'field-report': None})
    mocker.patch(
        'src.ai.services.performers.send_ai_left_task_notification.delay',
    )

    with override_settings(
        FILE_SERVICE_URL=None,
        FILE_SERVICE_HOST_PATH=None,
    ):
        run_ai_performer(task_id=task.id, agent_id=agent.id)

    task.refresh_from_db()
    assert task.status == TaskStatus.ACTIVE
    run = AITaskRun.objects.get(task=task, agent=agent)
    assert run.status == AITaskRunStatus.LEFT_FOR_HUMAN
    assert 'Required fields an AI agent cannot fill' in run.reason
    assert '"Report"' in run.reason
    call_model_mock.assert_not_called()
    upload_mock.assert_not_called()


def test_run__byo_connection__enables_and_supplies_credentials(mocker):

    """ An account with no operator flag but a saved provider
        connection runs agents with the connection's credentials """

    from src.ai.clients.chat_completions import ChatCompletionsClient
    from src.ai.models import AIProviderConnection

    user, _workflow, task, agent = _setup()
    account = user.account
    account.ai_performers_enabled = False
    account.save(update_fields=['ai_performers_enabled'])
    AIProviderConnection.objects.create(
        account=account,
        name='OpenRouter',
        base_url='https://byo.example.com/v1',
        api_key='byo-key',
    )
    captured = {}
    real_init = ChatCompletionsClient.__init__

    def capturing_init(self, **kwargs):
        captured.update(kwargs)
        real_init(self, **kwargs)

    mocker.patch.object(ChatCompletionsClient, '__init__', capturing_init)
    _mock_model(mocker, {'field-1': 'All good'})

    run_ai_performer(task_id=task.id, agent_id=agent.id)

    task.refresh_from_db()
    assert task.status == TaskStatus.COMPLETED
    assert captured == {
        'base_url': 'https://byo.example.com/v1',
        'api_key': 'byo-key',
    }
