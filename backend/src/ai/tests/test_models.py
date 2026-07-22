import pytest
from django.db import (
    IntegrityError,
    transaction,
)

from src.ai.enums import AITaskRunStatus
from src.ai.models import (
    AIAgent,
    AITaskRun,
)
from src.processes.enums import PerformerType
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def _create_agent(account, name='Blog Writer'):
    return AIAgent.objects.create(
        account=account,
        name=name,
        model_slug='anthropic/claude-3',
    )


def test_agent__same_name_on_account__rejected():
    user = create_test_user()
    _create_agent(user.account)

    with pytest.raises(IntegrityError):
        _create_agent(user.account)


def test_agent__same_name_after_soft_delete__allowed():
    user = create_test_user()
    agent = _create_agent(user.account)
    agent.delete()

    new_agent = _create_agent(user.account)

    assert new_agent.id != agent.id
    assert AIAgent.objects.count() == 1


def test_task_run__get_or_create__claims_once():
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = _create_agent(user.account)

    run, created_first = AITaskRun.objects.get_or_create(
        task=task,
        agent=agent,
    )
    same_run, created_second = AITaskRun.objects.get_or_create(
        task=task,
        agent=agent,
    )

    assert created_first is True
    assert created_second is False
    assert same_run.id == run.id
    assert run.status == AITaskRunStatus.QUEUED


def test_task_performer__duplicate_ai_agent__rejected():
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = _create_agent(user.account)
    TaskPerformer.objects.create(
        task=task,
        ai_agent=agent,
        type=PerformerType.AI,
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        TaskPerformer.objects.create(
            task=task,
            ai_agent=agent,
            type=PerformerType.AI,
        )


def test_task_performer__ai_agent_after_soft_delete__allowed():
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = _create_agent(user.account)
    performer = TaskPerformer.objects.create(
        task=task,
        ai_agent=agent,
        type=PerformerType.AI,
    )
    performer.delete()

    new_performer = TaskPerformer.objects.create(
        task=task,
        ai_agent=agent,
        type=PerformerType.AI,
    )

    assert new_performer.id != performer.id
