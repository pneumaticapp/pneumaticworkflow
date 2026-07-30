import pytest
from django.conf import settings

from src.ai.dispatch import dispatch_ai_performers
from src.ai.models import AIAgent
from src.processes.enums import PerformerType
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


def _setup():
    user = create_test_user(is_account_owner=True)
    account = user.account
    account.ai_performers_enabled = True
    account.save(update_fields=['ai_performers_enabled'])
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
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
    return task, agent


def test_dispatch__publishes_via_on_commit(mocker, immediate_on_commit):

    """ Task completion runs inside transaction.atomic(); publishing
        immediately lets the worker read pre-commit state and drop the
        run as irrelevant, so the publish must be commit-deferred """

    # arrange
    task, agent = _setup()
    delay_mock = mocker.patch('src.ai.tasks.run_ai_performer.delay')

    # act
    dispatch_ai_performers(task)

    # assert
    assert immediate_on_commit.call_count == 1
    delay_mock.assert_called_once_with(task_id=task.id, agent_id=agent.id)


def test_dispatch__feature_off__no_on_commit(mocker, immediate_on_commit):

    # arrange
    task, _agent = _setup()
    task.account.ai_performers_enabled = False
    task.account.save(update_fields=['ai_performers_enabled'])
    delay_mock = mocker.patch('src.ai.tasks.run_ai_performer.delay')

    # act
    dispatch_ai_performers(task)

    # assert
    immediate_on_commit.assert_not_called()
    delay_mock.assert_not_called()
