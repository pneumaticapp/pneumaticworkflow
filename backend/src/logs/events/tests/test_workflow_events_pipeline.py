import pytest

from src.logs.enums import LogsBackend
from src.logs.events.adapters.workflow import WORKFLOW_EVENT_TYPE_NAMES
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.tests.fakes import expected_workflow_events
from src.processes.enums import WorkflowEventType
from src.processes.services.events import WorkflowEventService
from src.processes.tests.fixtures import (
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_type_names__workflow_event_types__every_constant_mapped():

    """ A new constant of WorkflowEventType has to reach the stream:
        the adapter needs a line for it and the registry a type. """

    # arrange
    declared_types = {value for value, _ in WorkflowEventType.CHOICES}

    # act
    mapped_types = set(WORKFLOW_EVENT_TYPE_NAMES)

    # assert
    assert mapped_types == declared_types


def test_expected_events__table_of_the_plan__covers_every_mapped_type():

    """ The parametrized test below runs the chain once per row of
        the table: a type missing from it would go untested. """

    # arrange
    table = expected_workflow_events()

    # act
    listed_types = {type_event for type_event, _, _ in table}

    # assert
    assert listed_types == set(WORKFLOW_EVENT_TYPE_NAMES)
    assert len(table) == len(WORKFLOW_EVENT_TYPE_NAMES)


@pytest.mark.parametrize(
    ('type_event', 'name', 'category'),
    expected_workflow_events(),
)
def test_create_event__every_workflow_type__event_in_the_stream(
    type_event,
    name,
    category,
    fake_stream,
):

    """ The whole chain for every type of the feed: the hook of
        WorkflowEventService, the adapter, emit() and the write into
        the stream. _create_event is the single point every one of the
        23 service methods goes through. """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)

    # act
    WorkflowEventService._create_event(
        type=type_event,
        account=user.account,
        workflow=workflow,
        task=task,
        user=user,
    )

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == name
    assert event.category == category
    assert event.account_id == user.account_id
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id


def test_workflow_run_event__pipeline_enabled__filled_event(
    fake_stream,
):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)

    # act
    WorkflowEventService.workflow_run_event(workflow=workflow, user=user)

    # assert
    event = fake_stream.last_event()
    assert len(fake_stream.events) == 1
    assert event.type == EventName.WORKFLOW_RUN
    assert event.category == EventCategory.AUDIT
    assert event.account_id == user.account_id
    assert event.workflow_id == workflow.id
    assert event.actor.type == ActorType.USER
    assert event.actor.id == user.id
    assert event.actor.email == user.email
    assert event.object.type == EventObjectType.WORKFLOW
    assert event.object.id == workflow.id
    assert event.payload['workflow_name'] == workflow.name
    assert event.pii == ('actor.email', 'payload.workflow_name')


def test_workflow_run_event__pipeline_off__nothing_written(
    settings,
    fake_stream,
):

    """ LOGS_BACKEND='none' is the configuration of the test suite and
        of a deployment that does not collect events at all. """

    # arrange
    settings.LOGS_BACKEND = LogsBackend.NONE
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)

    # act
    WorkflowEventService.workflow_run_event(workflow=workflow, user=user)

    # assert
    assert fake_stream.events == []
