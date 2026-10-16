from contextlib import contextmanager

import pytest

from src.accounts.enums import NotificationType
from src.accounts.models import Notification
from src.ai.enums import AIAgentActionType
from src.ai.models import AIAgentAction
from src.ai.services.agent import MAX_RUN_FAILURES
from src.ai.tasks import dispatch_ai_agent_new_notifications
from src.ai.tests.fixtures import create_test_agent
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


@contextmanager
def _acquired_lock(*args, **kwargs):
    yield True


def _create_mention(mocker, runs: int = 0, failures: int = 0):
    mocker.patch('src.ai.tasks.periodic_lock', _acquired_lock)
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = create_test_agent(account=account)
    notification = Notification.objects.create(
        account=account,
        user=agent.user,
        author=owner,
        task=task,
        type=NotificationType.MENTION,
        text='Please call the customer.',
    )
    for action, count in (
        (AIAgentActionType.MENTION_IN_PROGRESS, runs),
        (AIAgentActionType.MENTION_FAILED, failures),
    ):
        for _ in range(count):
            AIAgentAction.objects.create(
                account=account,
                agent=agent,
                task=task,
                notification=notification,
                action=action,
            )
    return notification, agent


def test_dispatch_ai_agent_new_notifications__new_mention__dispatched(
    mocker,
):

    """ A new mention is dispatched """

    # arrange
    notification, agent = _create_mention(mocker)
    delay_mock = mocker.patch(
        'src.ai.tasks.execute_ai_agent_reply.delay',
    )

    # act
    dispatch_ai_agent_new_notifications()

    # assert
    delay_mock.assert_called_once_with(
        notification_id=notification.id,
        agent_id=agent.id,
    )


def test_dispatch_ai_agent_new_notifications__in_progress__skip(mocker):

    """ A mention in progress is not dispatched again """

    # arrange
    _create_mention(mocker, runs=1)
    delay_mock = mocker.patch(
        'src.ai.tasks.execute_ai_agent_reply.delay',
    )

    # act
    dispatch_ai_agent_new_notifications()

    # assert
    delay_mock.assert_not_called()


def test_dispatch_ai_agent_new_notifications__run_failed__dispatched(
    mocker,
):

    """ A mention whose run failed is dispatched again """

    # arrange
    notification, agent = _create_mention(mocker, runs=1, failures=1)
    delay_mock = mocker.patch(
        'src.ai.tasks.execute_ai_agent_reply.delay',
    )

    # act
    dispatch_ai_agent_new_notifications()

    # assert
    delay_mock.assert_called_once_with(
        notification_id=notification.id,
        agent_id=agent.id,
    )


def test_dispatch_ai_agent_new_notifications__max_run_failures__skip(
    mocker,
):

    """ A mention with all the allowed runs failed is not dispatched """

    # arrange
    _create_mention(
        mocker,
        runs=MAX_RUN_FAILURES,
        failures=MAX_RUN_FAILURES,
    )
    delay_mock = mocker.patch(
        'src.ai.tasks.execute_ai_agent_reply.delay',
    )

    # act
    dispatch_ai_agent_new_notifications()

    # assert
    delay_mock.assert_not_called()
