from contextlib import contextmanager

import pytest

from src.accounts.enums import NotificationType
from src.accounts.models import Notification
from src.ai.enums import AIAgentActionType
from src.ai.models import AIAgentAction
from src.ai.services.agent import MAX_RUN_FAILURES
from src.ai.tasks import (
    dispatch_ai_agent_new_notifications,
    dispatch_ai_agent_new_tasks,
)
from src.ai.tests.fixtures import create_test_agent
from src.processes.enums import PerformerType
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


@contextmanager
def _acquired_lock(*args, **kwargs):
    yield True


def _create_agent_task(
    mocker,
    is_active: bool = True,
    via_user: bool = True,
    via_group: bool = False,
):
    mocker.patch('src.ai.tasks.periodic_lock', _acquired_lock)
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = create_test_agent(account=account, is_active=is_active)
    if via_user:
        TaskPerformer.objects.create(task_id=task.id, user_id=agent.user_id)
    if via_group:
        group = create_test_group(account=account, users=[agent.user])
        TaskPerformer.objects.create(
            task_id=task.id,
            group_id=group.id,
            type=PerformerType.GROUP,
        )
    return task, agent


def _create_mention(
    mocker,
    runs: int = 0,
    failures: int = 0,
    is_active: bool = True,
):
    mocker.patch('src.ai.tasks.periodic_lock', _acquired_lock)
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = create_test_agent(account=account, is_active=is_active)
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


def test_dispatch_ai_agent_new_notifications__agent_inactive__skip(mocker):

    """ A mention of an inactive agent is not dispatched """

    # arrange
    _create_mention(mocker, is_active=False)
    delay_mock = mocker.patch(
        'src.ai.tasks.execute_ai_agent_reply.delay',
    )

    # act
    dispatch_ai_agent_new_notifications()

    # assert
    delay_mock.assert_not_called()


def test_dispatch_ai_agent_new_tasks__active_agent__dispatched(mocker):

    """ A task of an active agent is dispatched """

    # arrange
    task, agent = _create_agent_task(mocker)
    delay_mock = mocker.patch(
        'src.ai.tasks.complete_ai_agent_task.delay',
    )

    # act
    dispatch_ai_agent_new_tasks()

    # assert
    delay_mock.assert_called_once_with(task_id=task.id, agent_id=agent.id)


def test_dispatch_ai_agent_new_tasks__agent_inactive__skip(mocker):

    """ A task of an inactive agent is not dispatched """

    # arrange
    _create_agent_task(mocker, is_active=False)
    delay_mock = mocker.patch(
        'src.ai.tasks.complete_ai_agent_task.delay',
    )

    # act
    dispatch_ai_agent_new_tasks()

    # assert
    delay_mock.assert_not_called()


def test_dispatch_ai_agent_new_tasks__group_member__dispatched(mocker):

    """ A task assigned to a group with an agent is dispatched """

    # arrange
    task, agent = _create_agent_task(mocker, via_user=False, via_group=True)
    delay_mock = mocker.patch(
        'src.ai.tasks.complete_ai_agent_task.delay',
    )

    # act
    dispatch_ai_agent_new_tasks()

    # assert
    delay_mock.assert_called_once_with(task_id=task.id, agent_id=agent.id)


def test_dispatch_ai_agent_new_tasks__group_member_inactive__skip(mocker):

    """ A task assigned to a group with an inactive agent
        is not dispatched """

    # arrange
    _create_agent_task(
        mocker,
        is_active=False,
        via_user=False,
        via_group=True,
    )
    delay_mock = mocker.patch(
        'src.ai.tasks.complete_ai_agent_task.delay',
    )

    # act
    dispatch_ai_agent_new_tasks()

    # assert
    delay_mock.assert_not_called()


def test_dispatch_ai_agent_new_tasks__group_member_in_progress__skip(mocker):

    """ A group task in progress is not dispatched again """

    # arrange
    task, agent = _create_agent_task(mocker, via_user=False, via_group=True)
    AIAgentAction.objects.create(
        account=agent.account,
        agent=agent,
        task=task,
        action=AIAgentActionType.TASK_IN_PROGRESS,
    )
    delay_mock = mocker.patch(
        'src.ai.tasks.complete_ai_agent_task.delay',
    )

    # act
    dispatch_ai_agent_new_tasks()

    # assert
    delay_mock.assert_not_called()


def test_dispatch_ai_agent_new_tasks__group_member_completed__skip(mocker):

    """ The agent completed its part of the group task
        that requires completion by all: not dispatched """

    # arrange
    task, agent = _create_agent_task(mocker, via_user=False, via_group=True)
    task.require_completion_by_all = True
    task.save(update_fields=['require_completion_by_all'])
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=agent.user_id,
        type=PerformerType.GROUP_USER,
        is_completed=True,
    )
    delay_mock = mocker.patch(
        'src.ai.tasks.complete_ai_agent_task.delay',
    )

    # act
    dispatch_ai_agent_new_tasks()

    # assert
    delay_mock.assert_not_called()


def test_dispatch_ai_agent_new_tasks__user_and_group__dispatched_once(
    mocker,
):

    """ An agent assigned directly and via a group is dispatched once """

    # arrange
    task, agent = _create_agent_task(mocker, via_group=True)
    delay_mock = mocker.patch(
        'src.ai.tasks.complete_ai_agent_task.delay',
    )

    # act
    dispatch_ai_agent_new_tasks()

    # assert
    delay_mock.assert_called_once_with(task_id=task.id, agent_id=agent.id)
