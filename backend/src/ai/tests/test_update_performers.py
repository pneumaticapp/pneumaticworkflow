import pytest

from src.ai.models import AIAgent
from src.processes.enums import PerformerType
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_template,
    create_test_user,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def _create_agent(user, name='Analyst'):
    return AIAgent.objects.create(
        account=user.account,
        name=name,
        model_slug='test/model',
    )


def test_update_performers__ai_raw_performer__creates_performer():
    user = create_test_user()
    agent = _create_agent(user)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    raw_performer = task.add_raw_performer(
        ai_agent_id=agent.id,
        performer_type=PerformerType.AI,
    )

    task.update_performers()

    performer = TaskPerformer.objects.get(task=task, ai_agent=agent)
    assert performer.type == PerformerType.AI
    raw_performer.refresh_from_db()
    assert raw_performer.task_performer_id == performer.id


def test_update_performers__called_twice__no_duplicates():
    user = create_test_user()
    agent = _create_agent(user)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.add_raw_performer(
        ai_agent_id=agent.id,
        performer_type=PerformerType.AI,
    )

    task.update_performers()
    task.update_performers()

    assert TaskPerformer.objects.filter(
        task=task,
        ai_agent=agent,
    ).count() == 1


def test_update_performers__raw_performer_removed__performer_deleted():
    user = create_test_user()
    agent = _create_agent(user)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.add_raw_performer(
        ai_agent_id=agent.id,
        performer_type=PerformerType.AI,
    )
    task.update_performers()

    task.delete_raw_performer(
        ai_agent=agent,
        performer_type=PerformerType.AI,
    )

    assert not TaskPerformer.objects.filter(
        task=task,
        ai_agent=agent,
    ).exists()


def test_update_raw_performers_from_template_dict__replaces_with_ai():

    """ The template-versioning path passes raw performers as dicts:
        the human raw performer is dropped and the AI one takes over """

    user = create_test_user()
    agent = _create_agent(user)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.update_performers()
    assert TaskPerformer.objects.filter(
        task=task,
        user=user,
    ).exists()

    task.update_raw_performers_from_task_template({
        'raw_performers': [
            {
                'type': PerformerType.AI,
                'ai_agent_id': agent.id,
                'api_name': 'raw-performer-ai-1',
                'source_task_api_name': None,
                'field': None,
            },
        ],
    })
    task.update_performers()

    assert TaskPerformer.objects.filter(
        task=task,
        ai_agent=agent,
        type=PerformerType.AI,
    ).exists()
    assert not TaskPerformer.objects.filter(
        task=task,
        user=user,
    ).exists()


def test_workflow_from_template__ai_raw_performer__resolved():

    """ End to end: an AI performer defined on the task template
        reaches the workflow task as a TaskPerformer """

    user = create_test_user()
    agent = _create_agent(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    task_template = template.tasks.get(number=1)
    task_template.add_raw_performer(
        ai_agent_id=agent.id,
        performer_type=PerformerType.AI,
    )

    workflow = create_test_workflow(user=user, template=template)

    task = workflow.tasks.get(number=1)
    performer = TaskPerformer.objects.get(task=task, ai_agent=agent)
    assert performer.type == PerformerType.AI
    raw_performer = task.raw_performers.get(ai_agent=agent)
    assert raw_performer.task_performer_id == performer.id
