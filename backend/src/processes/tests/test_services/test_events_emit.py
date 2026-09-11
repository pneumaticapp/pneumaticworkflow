import pytest

from src.logs.events.exceptions import EventsError
from src.logs.events.enums import (
    ActorType,
    EventName,
    EventObjectType,
)
from src.logs.events.exceptions import UnknownEventTypeError
from src.logs.events.schema import Actor, EventObject
from src.processes.enums import WorkflowEventType
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.services.events import (
    WorkflowEventService,
)
from src.processes.tests.fixtures import (
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_workflow_run_event__ok__emit_workflow_run(mocker):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    emit_mock = mocker.patch('src.logs.events.adapters.workflow.emit')

    # act
    event = WorkflowEventService.workflow_run_event(
        workflow=workflow,
        user=user,
    )

    # assert
    emit_mock.assert_called_once_with(
        event_type=EventName.WORKFLOW_RUN,
        account_id=user.account_id,
        actor=Actor(type=ActorType.USER, id=user.id, email=user.email),
        event_object=EventObject(
            type=EventObjectType.WORKFLOW,
            id=workflow.id,
        ),
        workflow_id=workflow.id,
        task_id=None,
        ts=event.created,
        payload={
            'workflow_event_id': event.id,
            'with_attachments': False,
            'workflow_name': workflow.name,
            'template_id': workflow.template_id,
        },
    )


def test_task_complete_event__ok__emit_task_complete(mocker):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    emit_mock = mocker.patch('src.logs.events.adapters.workflow.emit')

    # act
    event = WorkflowEventService.task_complete_event(
        user=user,
        task=task,
        after_create_actions=False,
    )

    # assert
    emit_mock.assert_called_once_with(
        event_type=EventName.TASK_COMPLETE,
        account_id=user.account_id,
        actor=Actor(type=ActorType.USER, id=user.id, email=user.email),
        event_object=EventObject(type=EventObjectType.TASK, id=task.id),
        workflow_id=workflow.id,
        task_id=task.id,
        ts=event.created,
        payload={
            'workflow_event_id': event.id,
            'with_attachments': False,
            'workflow_name': workflow.name,
            'template_id': workflow.template_id,
            'task_number': task.number,
            'task_name': task.name,
        },
    )


def test_task_started_event__no_user__emit_system_actor(mocker):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    emit_mock = mocker.patch('src.logs.events.adapters.workflow.emit')

    # act
    event = WorkflowEventService.task_started_event(
        task=task,
        after_create_actions=False,
    )

    # assert
    emit_mock.assert_called_once_with(
        event_type=EventName.TASK_START,
        account_id=user.account_id,
        actor=Actor(type=ActorType.SYSTEM),
        event_object=EventObject(type=EventObjectType.TASK, id=task.id),
        workflow_id=workflow.id,
        task_id=task.id,
        ts=event.created,
        payload={
            'workflow_event_id': event.id,
            'with_attachments': False,
            'workflow_name': workflow.name,
            'template_id': workflow.template_id,
            'task_number': task.number,
            'task_name': task.name,
        },
    )


def test_workflow_urgent_event__not_urgent__emit_workflow_not_urgent(mocker):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    emit_mock = mocker.patch('src.logs.events.adapters.workflow.emit')

    # act
    event = WorkflowEventService.workflow_urgent_event(
        user=user,
        event_type=WorkflowEventType.NOT_URGENT,
        workflow=workflow,
        after_create_actions=False,
    )

    # assert
    emit_mock.assert_called_once_with(
        event_type=EventName.WORKFLOW_NOT_URGENT,
        account_id=user.account_id,
        actor=Actor(type=ActorType.USER, id=user.id, email=user.email),
        event_object=EventObject(
            type=EventObjectType.WORKFLOW,
            id=workflow.id,
        ),
        workflow_id=workflow.id,
        task_id=None,
        ts=event.created,
        payload={
            'workflow_event_id': event.id,
            'with_attachments': False,
            'workflow_name': workflow.name,
            'template_id': workflow.template_id,
        },
    )


def test_workflow_run_event__emit_error_in_production__event_created(
    mocker,
    settings,
):

    # arrange
    settings.LOGS_STRICT = False
    error = EventsError('the pipeline is broken')
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    emit_mock = mocker.patch(
        'src.logs.events.adapters.workflow.emit',
        side_effect=error,
    )
    report_error_mock = mocker.patch(
        'src.logs.events.adapters.workflow.report_error',
    )

    # act
    event = WorkflowEventService.workflow_run_event(
        workflow=workflow,
        user=user,
    )

    # assert
    assert WorkflowEvent.objects.filter(id=event.id).exists()
    emit_mock.assert_called_once_with(
        event_type=EventName.WORKFLOW_RUN,
        account_id=user.account_id,
        actor=Actor(type=ActorType.USER, id=user.id, email=user.email),
        event_object=EventObject(
            type=EventObjectType.WORKFLOW,
            id=workflow.id,
        ),
        workflow_id=workflow.id,
        task_id=None,
        ts=event.created,
        payload={
            'workflow_event_id': event.id,
            'with_attachments': False,
            'workflow_name': workflow.name,
            'template_id': workflow.template_id,
        },
    )
    report_error_mock.assert_called_once_with(
        message='Failed to emit a workflow event',
        data={
            'workflow_event_id': event.id,
            'workflow_event_type': event.type,
            'error': repr(error),
        },
    )


def test_workflow_run_event__bug_in_the_pipeline__raises(
    mocker,
    settings,
):

    """ Only the errors of the pipeline are swallowed. A TypeError of
        the adapter is a bug and has to reach the caller, otherwise a
        broken build looks like a healthy one with no events. """

    # arrange
    settings.LOGS_STRICT = False
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    emit_mock = mocker.patch(
        'src.logs.events.adapters.workflow.emit',
        side_effect=TypeError('emit() got an unexpected argument'),
    )
    report_error_mock = mocker.patch(
        'src.logs.events.adapters.workflow.report_error',
    )

    # act
    with pytest.raises(TypeError) as ex:
        WorkflowEventService.workflow_run_event(
            workflow=workflow,
            user=user,
        )

    # assert
    assert str(ex.value) == 'emit() got an unexpected argument'
    event = WorkflowEvent.objects.get(
        workflow=workflow,
        type=WorkflowEventType.RUN,
    )
    emit_mock.assert_called_once_with(
        event_type=EventName.WORKFLOW_RUN,
        account_id=user.account_id,
        actor=Actor(type=ActorType.USER, id=user.id, email=user.email),
        event_object=EventObject(
            type=EventObjectType.WORKFLOW,
            id=workflow.id,
        ),
        workflow_id=workflow.id,
        task_id=None,
        ts=event.created,
        payload={
            'workflow_event_id': event.id,
            'with_attachments': False,
            'workflow_name': workflow.name,
            'template_id': workflow.template_id,
        },
    )
    report_error_mock.assert_not_called()


def test_workflow_run_event__emit_error_in_testing__raises(
    mocker,
    settings,
):

    # arrange
    settings.LOGS_STRICT = True
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    emit_mock = mocker.patch(
        'src.logs.events.adapters.workflow.emit',
        side_effect=ValueError('the pipeline is broken'),
    )
    report_error_mock = mocker.patch(
        'src.logs.events.adapters.workflow.report_error',
    )

    # act
    with pytest.raises(ValueError) as ex:
        WorkflowEventService.workflow_run_event(
            workflow=workflow,
            user=user,
        )

    # assert
    assert str(ex.value) == 'the pipeline is broken'
    event = WorkflowEvent.objects.get(workflow_id=workflow.id)
    assert event.type == WorkflowEventType.RUN
    emit_mock.assert_called_once_with(
        event_type=EventName.WORKFLOW_RUN,
        account_id=user.account_id,
        actor=Actor(type=ActorType.USER, id=user.id, email=user.email),
        event_object=EventObject(
            type=EventObjectType.WORKFLOW,
            id=workflow.id,
        ),
        workflow_id=workflow.id,
        task_id=None,
        ts=event.created,
        payload={
            'workflow_event_id': event.id,
            'with_attachments': False,
            'workflow_name': workflow.name,
            'template_id': workflow.template_id,
        },
    )
    report_error_mock.assert_not_called()


def test_workflow_run_event__type_missing_in_the_adapter__raises(
    mocker,
    settings,
):

    """ A WorkflowEventType constant nobody mapped breaks the tests
        instead of producing events no reader can name. The workflow
        event itself is already saved: the user action is done and a
        broken pipeline must not undo it. """

    # arrange
    settings.LOGS_STRICT = True
    mocker.patch.dict(
        'src.logs.events.adapters.workflow.WORKFLOW_EVENT_TYPE_NAMES',
        clear=True,
    )
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)

    # act
    with pytest.raises(UnknownEventTypeError) as ex:
        WorkflowEventService.workflow_run_event(
            workflow=workflow,
            user=user,
        )

    # assert
    assert str(ex.value) == (
        f'Unknown workflow event type: {WorkflowEventType.RUN}'
    )
    assert WorkflowEvent.objects.filter(
        workflow_id=workflow.id,
        type=WorkflowEventType.RUN,
    ).exists()
