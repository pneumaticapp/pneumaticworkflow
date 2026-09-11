import pytest

from src.logs.events.adapters.workflow import (
    workflow_event_to_kwargs,
)
from src.logs.events.enums import (
    ActorType,
    EventName,
    EventObjectType,
)
from src.logs.events.exceptions import UnknownEventTypeError
from src.logs.events.schema import Actor, EventObject
from src.processes.enums import WorkflowEventType
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.services.events import WorkflowEventService
from src.processes.tests.fixtures import (
    create_test_event,
    create_test_group,
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_to_kwargs__event_with_a_task__task_object():

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    event = create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.TASK_COMPLETE,
        task=task,
    )

    # act
    kwargs = workflow_event_to_kwargs(event)

    # assert
    assert kwargs['event_type'] == EventName.TASK_COMPLETE
    assert kwargs['account_id'] == user.account_id
    assert kwargs['actor'] == Actor(
        type=ActorType.USER,
        id=user.id,
        email=user.email,
    )
    assert kwargs['event_object'] == EventObject(
        type=EventObjectType.TASK,
        id=task.id,
    )
    assert kwargs['workflow_id'] == workflow.id
    assert kwargs['task_id'] == task.id
    assert kwargs['ts'] == event.created
    assert kwargs['payload'] == {
        'workflow_event_id': event.id,
        'with_attachments': False,
        'workflow_name': workflow.name,
        'template_id': workflow.template_id,
        'task_number': task.number,
        'task_name': task.name,
    }


def test_to_kwargs__event_without_a_task__workflow_object():

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    event = WorkflowEventService.workflow_run_event(
        workflow=workflow,
        user=user,
    )

    # act
    kwargs = workflow_event_to_kwargs(event)

    # assert
    assert kwargs['event_type'] == EventName.WORKFLOW_RUN
    assert kwargs['event_object'] == EventObject(
        type=EventObjectType.WORKFLOW,
        id=workflow.id,
    )
    assert kwargs['task_id'] is None
    assert kwargs['payload'] == {
        'workflow_event_id': event.id,
        'with_attachments': False,
        'workflow_name': workflow.name,
        'template_id': workflow.template_id,
    }


def test_to_kwargs__event_without_a_user__system_actor():

    """ A delay, a skip or a template condition is made by the
        workflow engine itself. """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    event = WorkflowEventService.workflow_run_event(workflow=workflow)

    # act
    kwargs = workflow_event_to_kwargs(event)

    # assert
    assert kwargs['actor'] == Actor(type=ActorType.SYSTEM)
    assert kwargs['actor'].id is None
    assert kwargs['actor'].email is None


def test_to_kwargs__comment_event__payload_without_the_text():

    """ The comment holds customer content and the workflow event
        keeps it anyway: an auditor needs the fact, not the text. """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.comment_created_event(
        user=user,
        task=task,
        text='Secret customer data',
        after_create_actions=False,
    )

    # act
    kwargs = workflow_event_to_kwargs(event)

    # assert
    assert event.text == 'Secret customer data'
    assert kwargs['event_type'] == EventName.TASK_COMMENT
    assert kwargs['payload'] == {
        'workflow_event_id': event.id,
        'with_attachments': False,
        'workflow_name': workflow.name,
        'template_id': workflow.template_id,
        'task_number': task.number,
        'task_name': task.name,
    }


def test_to_kwargs__performer_event__target_user_in_the_payload():

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.performer_created_event(
        user=user,
        task=task,
        performer=user,
        after_create_actions=False,
    )

    # act
    kwargs = workflow_event_to_kwargs(event)

    # assert
    assert kwargs['event_type'] == EventName.TASK_PERFORMER_CREATED
    assert kwargs['payload'] == {
        'workflow_event_id': event.id,
        'with_attachments': False,
        'workflow_name': workflow.name,
        'template_id': workflow.template_id,
        'task_number': task.number,
        'task_name': task.name,
        'target_user_id': user.id,
    }


def test_to_kwargs__performer_group_event__target_group_in_the_payload():

    """ Without this an auditor cannot tell which group was given
        access to the task. """

    # arrange
    user = create_test_owner()
    group = create_test_group(account=user.account, users=[user])
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.performer_group_created_event(
        user=user,
        task=task,
        performer=group,
        after_create_actions=False,
    )

    # act
    kwargs = workflow_event_to_kwargs(event)

    # assert
    assert kwargs['event_type'] == EventName.TASK_PERFORMER_GROUP_CREATED
    assert kwargs['payload'] == {
        'workflow_event_id': event.id,
        'with_attachments': False,
        'workflow_name': workflow.name,
        'template_id': workflow.template_id,
        'task_number': task.number,
        'task_name': task.name,
        'target_group_id': group.id,
    }


def test_to_kwargs__performer_group_deleted__target_group_in_the_payload():

    # arrange
    user = create_test_owner()
    group = create_test_group(account=user.account, users=[user])
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.performer_group_deleted_event(
        user=user,
        task=task,
        performer=group,
        after_create_actions=False,
    )

    # act
    kwargs = workflow_event_to_kwargs(event)

    # assert
    assert kwargs['event_type'] == EventName.TASK_PERFORMER_GROUP_DELETED
    assert kwargs['payload']['target_group_id'] == group.id


def test_to_kwargs__event_with_ids_only__no_extra_query(
    django_assert_num_queries,
):

    """ The hook runs inside a user request: a related object that is
        not in the field cache costs its name, never a query. """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    event = create_test_event(workflow=workflow, user=user)
    stored = WorkflowEvent.objects.get(id=event.id)

    # act
    with django_assert_num_queries(0):
        kwargs = workflow_event_to_kwargs(stored)

    # assert
    assert kwargs['event_type'] == EventName.WORKFLOW_RUN
    assert kwargs['payload'] == {
        'workflow_event_id': event.id,
        'with_attachments': False,
    }
    assert kwargs['actor'] == Actor(type=ActorType.USER, id=user.id)


def test_to_kwargs__undeclared_type__raise():

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    event = create_test_event(
        workflow=workflow,
        user=user,
        type_event=999,
    )

    # act
    with pytest.raises(UnknownEventTypeError) as ex:
        workflow_event_to_kwargs(event)

    # assert
    assert str(ex.value) == 'Unknown workflow event type: 999'


def test_to_kwargs__workflow_without_a_template__no_template_id():

    """ A workflow whose template is gone still has a name; the
        payload then names no template rather than None. """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    workflow.template = None
    event = WorkflowEvent(
        type=WorkflowEventType.RUN,
        account=user.account,
        workflow=workflow,
        user=user,
        with_attachments=True,
    )

    # act
    kwargs = workflow_event_to_kwargs(event)

    # assert
    assert kwargs['payload'] == {
        'workflow_event_id': None,
        'with_attachments': True,
        'workflow_name': workflow.name,
    }
