from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Optional,
)

from src.logs.events.enums import (
    ActorType,
    EventName,
    EventObjectType,
)
from src.logs.events.exceptions import UnknownEventTypeError
from src.logs.events.schema import Actor, EventObject
from src.processes.enums import WorkflowEventType

if TYPE_CHECKING:
    from src.processes.models.workflows.event import WorkflowEvent


WORKFLOW_EVENT_TYPE_NAMES: Dict[int, str] = {
    WorkflowEventType.RUN: EventName.WORKFLOW_RUN,
    WorkflowEventType.COMPLETE: EventName.WORKFLOW_COMPLETE,
    WorkflowEventType.TASK_START: EventName.TASK_START,
    WorkflowEventType.TASK_COMPLETE: EventName.TASK_COMPLETE,
    WorkflowEventType.TASK_REVERT: EventName.TASK_REVERT,
    WorkflowEventType.COMMENT: EventName.TASK_COMMENT,
    WorkflowEventType.ENDED: EventName.WORKFLOW_ENDED,
    WorkflowEventType.DELAY: EventName.WORKFLOW_DELAY,
    WorkflowEventType.REVERT: EventName.WORKFLOW_REVERT,
    WorkflowEventType.TASK_SKIP: EventName.TASK_SKIP,
    WorkflowEventType.ENDED_BY_CONDITION:
        EventName.WORKFLOW_ENDED_BY_CONDITION,
    WorkflowEventType.URGENT: EventName.WORKFLOW_URGENT,
    WorkflowEventType.NOT_URGENT: EventName.WORKFLOW_NOT_URGENT,
    WorkflowEventType.TASK_SKIP_NO_PERFORMERS:
        EventName.TASK_SKIP_NO_PERFORMERS,
    WorkflowEventType.TASK_PERFORMER_CREATED:
        EventName.TASK_PERFORMER_CREATED,
    WorkflowEventType.TASK_PERFORMER_DELETED:
        EventName.TASK_PERFORMER_DELETED,
    WorkflowEventType.FORCE_RESUME: EventName.WORKFLOW_FORCE_RESUME,
    WorkflowEventType.FORCE_DELAY: EventName.WORKFLOW_FORCE_DELAY,
    WorkflowEventType.DUE_DATE_CHANGED: EventName.TASK_DUE_DATE_CHANGED,
    WorkflowEventType.SUB_WORKFLOW_RUN:
        EventName.WORKFLOW_SUB_WORKFLOW_RUN,
    WorkflowEventType.TASK_PERFORMER_GROUP_CREATED:
        EventName.TASK_PERFORMER_GROUP_CREATED,
    WorkflowEventType.TASK_PERFORMER_GROUP_DELETED:
        EventName.TASK_PERFORMER_GROUP_DELETED,
    WorkflowEventType.TASK_DELAY: EventName.TASK_DELAY,
    WorkflowEventType.TASK_DELEGATION: EventName.TASK_DELEGATION,
}


def workflow_event_to_kwargs(event: 'WorkflowEvent') -> Dict[str, Any]:

    """ Turn a stored WorkflowEvent into emit() keyword arguments.

        Only the fields an auditor needs: no comment text, no task or
        delay snapshots. They are big, they hold customer content and
        the workflow event itself keeps them anyway. """

    name = WORKFLOW_EVENT_TYPE_NAMES.get(event.type)
    if name is None:
        raise UnknownEventTypeError(
            f'Unknown workflow event type: {event.type}',
        )
    return {
        'event_type': name,
        'account_id': event.account_id,
        'actor': _actor(event),
        'event_object': _object(event),
        'workflow_id': event.workflow_id,
        'task_id': event.task_id,
        'ts': event.created,
        'payload': _payload(event),
    }


def _actor(event: 'WorkflowEvent') -> Actor:

    """ Events of a delay, a skip or a template condition have no
        user: they are made by the workflow engine itself. """

    if event.user_id is None:
        return Actor(type=ActorType.SYSTEM)
    user = _cached_relation(event, 'user')
    return Actor(
        type=ActorType.USER,
        id=event.user_id,
        email=getattr(user, 'email', None),
    )


def _object(event: 'WorkflowEvent') -> EventObject:
    if event.task_id is not None:
        return EventObject(type=EventObjectType.TASK, id=event.task_id)
    return EventObject(
        type=EventObjectType.WORKFLOW, id=event.workflow_id,
    )


def _payload(event: 'WorkflowEvent') -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        'workflow_event_id': event.id,
        'with_attachments': event.with_attachments,
    }
    workflow = _cached_relation(event, 'workflow')
    if workflow is not None:
        payload['workflow_name'] = workflow.name
        if workflow.template_id is not None:
            payload['template_id'] = workflow.template_id
    task = _cached_relation(event, 'task')
    if task is not None:
        payload['task_number'] = task.number
        payload['task_name'] = task.name
    if event.target_user_id is not None:
        payload['target_user_id'] = event.target_user_id
    if event.target_group_id is not None:
        payload['target_group_id'] = event.target_group_id
    return payload


def _cached_relation(event: 'WorkflowEvent', name: str) -> Optional[Any]:

    """ Read a foreign key only when it is already in the field cache.

        WorkflowEventService passes model instances to create(), so
        the related objects are there and the hook costs no query.
        A hand made event holding ids only loses the name and the
        e-mail instead of hitting the database on a user request. """

    field = event._meta.get_field(name)
    if field.is_cached(event):
        return field.get_cached_value(event)
    return None
