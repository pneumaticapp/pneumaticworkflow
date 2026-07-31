import pytest
from django.conf import settings

from src.ai.models import AIAgent
from src.processes.enums import DirectlyStatus, FieldType, PerformerType
from src.processes.messages.template import MSG_PT_0076
from src.processes.messages.workflow import (
    MSG_PW_0016,
    MSG_PW_0018,
    MSG_PW_0094,
    MSG_PW_0095,
)
from src.processes.models.workflows.fields import TaskField
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_not_admin,
    create_test_user,
    create_test_workflow,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def ai_performers_deployed(mocker):
    mocker.patch.dict(
        settings.PROJECT_CONF,
        {'AI_PERFORMERS': True},
    )


def _setup(tasks_count=1):
    user = create_test_user(is_account_owner=True)
    account = user.account
    account.ai_performers_enabled = True
    account.save(update_fields=['ai_performers_enabled'])
    workflow = create_test_workflow(user=user, tasks_count=tasks_count)
    task = workflow.tasks.get(number=1)
    TaskField.objects.create(
        account=account,
        workflow=workflow,
        task=task,
        name='Result',
        type=FieldType.STRING,
        order=1,
        api_name='field-result',
    )
    agent = AIAgent.objects.create(
        account=account,
        name='Analyst',
        model_slug='test/model',
    )
    return user, task, agent


def _ai_performer(task, agent):
    return TaskPerformer.objects.filter(
        task=task,
        type=PerformerType.AI,
        ai_agent=agent,
    ).first()


def test_create__active_task__performer_added_and_dispatched(
    api_client,
    mocker,
):

    # arrange
    user, task, agent = _setup()
    delay_mock = mocker.patch('src.ai.tasks.run_ai_performer.delay')
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/create-ai-performer',
        data={'ai_agent_id': agent.id},
    )

    # assert
    assert response.status_code == 204
    performer = _ai_performer(task, agent)
    assert performer.directly_status == DirectlyStatus.CREATED
    delay_mock.assert_called_once_with(task_id=task.id, agent_id=agent.id)


def test_create__feature_off__validation_error(api_client, mocker):

    # arrange
    user, task, agent = _setup()
    account = user.account
    account.ai_performers_enabled = False
    account.save(update_fields=['ai_performers_enabled'])
    delay_mock = mocker.patch('src.ai.tasks.run_ai_performer.delay')
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/create-ai-performer',
        data={'ai_agent_id': agent.id},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_PT_0076
    assert _ai_performer(task, agent) is None
    delay_mock.assert_not_called()


def test_create__no_output_fields__validation_error(api_client, mocker):

    # arrange
    user, task, agent = _setup()
    task.output.all().delete()
    delay_mock = mocker.patch('src.ai.tasks.run_ai_performer.delay')
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/create-ai-performer',
        data={'ai_agent_id': agent.id},
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == MSG_PW_0095
    assert _ai_performer(task, agent) is None
    delay_mock.assert_not_called()


def test_create__unknown_agent__validation_error(api_client, mocker):

    # arrange
    user, task, _agent = _setup()
    mocker.patch('src.ai.tasks.run_ai_performer.delay')
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/create-ai-performer',
        data={'ai_agent_id': 999999},
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == MSG_PW_0094


def test_create__inactive_agent__validation_error(api_client, mocker):

    # arrange
    user, task, agent = _setup()
    agent.is_active = False
    agent.save(update_fields=['is_active'])
    mocker.patch('src.ai.tasks.run_ai_performer.delay')
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/create-ai-performer',
        data={'ai_agent_id': agent.id},
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == MSG_PW_0094


def test_create__inactive_task__validation_error(api_client, mocker):

    # arrange
    user, workflow_task, agent = _setup(tasks_count=2)
    inactive_task = workflow_task.workflow.tasks.get(number=2)
    mocker.patch('src.ai.tasks.run_ai_performer.delay')
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/v2/tasks/{inactive_task.id}/create-ai-performer',
        data={'ai_agent_id': agent.id},
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == MSG_PW_0018


def test_create__not_admin__permission_denied(api_client, mocker):

    # arrange
    user, task, agent = _setup()
    not_admin = create_test_not_admin(account=user.account)
    mocker.patch('src.ai.tasks.run_ai_performer.delay')
    api_client.token_authenticate(not_admin)

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/create-ai-performer',
        data={'ai_agent_id': agent.id},
    )

    # assert
    assert response.status_code == 403


def test_create__again__no_duplicate_no_redispatch(api_client, mocker):

    # arrange
    user, task, agent = _setup()
    delay_mock = mocker.patch('src.ai.tasks.run_ai_performer.delay')
    api_client.token_authenticate(user)
    api_client.post(
        f'/v2/tasks/{task.id}/create-ai-performer',
        data={'ai_agent_id': agent.id},
    )

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/create-ai-performer',
        data={'ai_agent_id': agent.id},
    )

    # assert
    assert response.status_code == 204
    assert TaskPerformer.objects.filter(
        task=task,
        type=PerformerType.AI,
        ai_agent=agent,
    ).count() == 1
    delay_mock.assert_called_once()


def test_delete__assigned__marked_deleted(api_client, mocker):

    # arrange
    user, task, agent = _setup()
    mocker.patch('src.ai.tasks.run_ai_performer.delay')
    api_client.token_authenticate(user)
    api_client.post(
        f'/v2/tasks/{task.id}/create-ai-performer',
        data={'ai_agent_id': agent.id},
    )

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/delete-ai-performer',
        data={'ai_agent_id': agent.id},
    )

    # assert
    assert response.status_code == 204
    performer = _ai_performer(task, agent)
    assert performer.directly_status == DirectlyStatus.DELETED


def test_delete__re_add__revived_and_redispatched(api_client, mocker):

    # arrange
    user, task, agent = _setup()
    delay_mock = mocker.patch('src.ai.tasks.run_ai_performer.delay')
    api_client.token_authenticate(user)
    api_client.post(
        f'/v2/tasks/{task.id}/create-ai-performer',
        data={'ai_agent_id': agent.id},
    )
    api_client.post(
        f'/v2/tasks/{task.id}/delete-ai-performer',
        data={'ai_agent_id': agent.id},
    )

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/create-ai-performer',
        data={'ai_agent_id': agent.id},
    )

    # assert
    assert response.status_code == 204
    performer = _ai_performer(task, agent)
    assert performer.directly_status == DirectlyStatus.CREATED
    assert delay_mock.call_count == 2


def test_delete__last_performer__validation_error(api_client, mocker):

    # arrange
    user, task, agent = _setup()
    mocker.patch('src.ai.tasks.run_ai_performer.delay')
    api_client.token_authenticate(user)
    api_client.post(
        f'/v2/tasks/{task.id}/create-ai-performer',
        data={'ai_agent_id': agent.id},
    )
    TaskPerformer.objects.by_task(task.id).filter(
        type=PerformerType.USER,
    ).delete()

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/delete-ai-performer',
        data={'ai_agent_id': agent.id},
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == MSG_PW_0016
    performer = _ai_performer(task, agent)
    assert performer.directly_status == DirectlyStatus.CREATED


def test_delete__not_assigned__ok_noop(api_client, mocker):

    # arrange
    user, task, agent = _setup()
    mocker.patch('src.ai.tasks.run_ai_performer.delay')
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/delete-ai-performer',
        data={'ai_agent_id': agent.id},
    )

    # assert
    assert response.status_code == 204
    assert _ai_performer(task, agent) is None


def test_delete__remaining_completed__task_completes(api_client, mocker):

    # arrange
    user, task, agent = _setup()
    mocker.patch('src.ai.tasks.run_ai_performer.delay')
    api_client.token_authenticate(user)
    api_client.post(
        f'/v2/tasks/{task.id}/create-ai-performer',
        data={'ai_agent_id': agent.id},
    )
    task.require_completion_by_all = True
    task.save(update_fields=['require_completion_by_all'])
    TaskPerformer.objects.by_task(task.id).filter(
        type=PerformerType.USER,
    ).update(is_completed=True)
    action_service_mock = mocker.patch(
        'src.processes.services.tasks.ai_performer.WorkflowActionService',
    )

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/delete-ai-performer',
        data={'ai_agent_id': agent.id},
    )

    # assert
    assert response.status_code == 204
    action_service_mock.assert_called_once()
    assert action_service_mock.call_args[1]['user'].id == user.id
    action_service_mock.return_value.complete_task.assert_called_once_with(
        task=task,
    )
