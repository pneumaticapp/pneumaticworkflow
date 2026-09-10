import re
from dataclasses import dataclass
from typing import Dict, Set, Tuple

from django.conf import settings

from src.logs.events.enums import EventCategory, EventName
from src.logs.events.exceptions import (
    EventsError,
    UnknownEventTypeError,
)
from src.utils.logging import (
    SentryLogLevel,
    capture_sentry_message,
)

EVENT_NAME_PATTERN = re.compile(r'^[a-z_]+\.[a-z_]+$')
ACTOR_PII = ('actor.email', 'ip', 'user_agent')
ANONYMOUS_PII = ('ip', 'user_agent')
WORKFLOW_PII = (
    *ACTOR_PII,
    'payload.workflow_name',
    'payload.task_name',
)
NAMED_PII = (*ACTOR_PII, 'payload.name')
TARGET_PII = (*ACTOR_PII, 'payload.target_email')
FILE_PII = (*ACTOR_PII, 'payload.filename')
PII_ROOTS = ('ip', 'user_agent')
PII_NAMESPACES = ('actor', 'object', 'payload')

_reported_unknown_types: Set[str] = set()


@dataclass(frozen=True)
class EventType:

    name: str
    category: str
    pii: Tuple[str, ...] = ()
    description: str = ''


EVENT_TYPES: Tuple[EventType, ...] = (

    # One type per WorkflowEventType constant, mapped by
    # adapters/workflow.py; a new constant there needs a line here.
    EventType(
        name=EventName.WORKFLOW_RUN,
        category=EventCategory.AUDIT,
        pii=WORKFLOW_PII,
        description='Workflow started',
    ),
    EventType(
        name=EventName.WORKFLOW_COMPLETE,
        category=EventCategory.AUDIT,
        pii=WORKFLOW_PII,
        description='Workflow completed',
    ),
    EventType(
        name=EventName.TASK_START,
        category=EventCategory.ACTIVITY,
        pii=WORKFLOW_PII,
        description='Task started',
    ),
    EventType(
        name=EventName.TASK_COMPLETE,
        category=EventCategory.AUDIT,
        pii=WORKFLOW_PII,
        description='Task completed',
    ),
    EventType(
        name=EventName.TASK_REVERT,
        category=EventCategory.AUDIT,
        pii=WORKFLOW_PII,
        description='Task returned to the previous performer',
    ),
    EventType(
        name=EventName.TASK_COMMENT,
        category=EventCategory.ACTIVITY,
        pii=WORKFLOW_PII,
        description='Comment added to a task',
    ),
    EventType(
        name=EventName.WORKFLOW_ENDED,
        category=EventCategory.AUDIT,
        pii=WORKFLOW_PII,
        description='Workflow ended by a user',
    ),
    EventType(
        name=EventName.WORKFLOW_DELAY,
        category=EventCategory.ACTIVITY,
        pii=WORKFLOW_PII,
        description='Workflow delayed',
    ),
    EventType(
        name=EventName.WORKFLOW_REVERT,
        category=EventCategory.AUDIT,
        pii=WORKFLOW_PII,
        description='Workflow returned to a previous task',
    ),
    EventType(
        name=EventName.TASK_SKIP,
        category=EventCategory.ACTIVITY,
        pii=WORKFLOW_PII,
        description='Task skipped',
    ),
    EventType(
        name=EventName.WORKFLOW_ENDED_BY_CONDITION,
        category=EventCategory.ACTIVITY,
        pii=WORKFLOW_PII,
        description='Workflow ended by a condition',
    ),
    EventType(
        name=EventName.WORKFLOW_URGENT,
        category=EventCategory.ACTIVITY,
        pii=WORKFLOW_PII,
        description='Workflow marked as urgent',
    ),
    EventType(
        name=EventName.WORKFLOW_NOT_URGENT,
        category=EventCategory.ACTIVITY,
        pii=WORKFLOW_PII,
        description='Workflow urgent mark removed',
    ),
    EventType(
        name=EventName.TASK_SKIP_NO_PERFORMERS,
        category=EventCategory.ACTIVITY,
        pii=WORKFLOW_PII,
        description='Task skipped because it has no performers',
    ),
    EventType(
        name=EventName.TASK_PERFORMER_CREATED,
        category=EventCategory.AUDIT,
        pii=WORKFLOW_PII,
        description='Task performer added',
    ),
    EventType(
        name=EventName.TASK_PERFORMER_DELETED,
        category=EventCategory.AUDIT,
        pii=WORKFLOW_PII,
        description='Task performer removed',
    ),
    EventType(
        name=EventName.WORKFLOW_FORCE_RESUME,
        category=EventCategory.ACTIVITY,
        pii=WORKFLOW_PII,
        description='Workflow resumed manually',
    ),
    EventType(
        name=EventName.WORKFLOW_FORCE_DELAY,
        category=EventCategory.ACTIVITY,
        pii=WORKFLOW_PII,
        description='Workflow delayed manually',
    ),
    EventType(
        name=EventName.TASK_DUE_DATE_CHANGED,
        category=EventCategory.ACTIVITY,
        pii=WORKFLOW_PII,
        description='Task due date changed',
    ),
    EventType(
        name=EventName.WORKFLOW_SUB_WORKFLOW_RUN,
        category=EventCategory.ACTIVITY,
        pii=WORKFLOW_PII,
        description='Sub-workflow started',
    ),
    EventType(
        name=EventName.TASK_PERFORMER_GROUP_CREATED,
        category=EventCategory.AUDIT,
        pii=WORKFLOW_PII,
        description='Task performer group added',
    ),
    EventType(
        name=EventName.TASK_PERFORMER_GROUP_DELETED,
        category=EventCategory.AUDIT,
        pii=WORKFLOW_PII,
        description='Task performer group removed',
    ),
    EventType(
        name=EventName.TASK_DELAY,
        category=EventCategory.ACTIVITY,
        pii=WORKFLOW_PII,
        description='Task delayed',
    ),
    EventType(
        name=EventName.TASK_DELEGATION,
        category=EventCategory.AUDIT,
        pii=WORKFLOW_PII,
        description='Task delegated to another performer',
    ),

    # Authentication
    EventType(
        name=EventName.USER_LOGIN,
        category=EventCategory.AUDIT,
        pii=ACTOR_PII,
        description='User signed in',
    ),
    EventType(
        name=EventName.USER_LOGOUT,
        category=EventCategory.AUDIT,
        pii=ACTOR_PII,
        description='User signed out',
    ),
    EventType(
        name=EventName.USER_LOGIN_FAILED,
        category=EventCategory.AUDIT,
        pii=ANONYMOUS_PII,
        description='Sign in attempt failed',
    ),
    EventType(
        name=EventName.USER_LOGIN_AS,
        category=EventCategory.AUDIT,
        # The reason is free text typed by a staff member: it names
        # people and tickets as often as not.
        pii=(*TARGET_PII, 'payload.reason'),
        description='Superuser signed in as a user',
    ),
    EventType(
        name=EventName.TENANT_LOGIN_AS,
        category=EventCategory.AUDIT,
        pii=ACTOR_PII,
        description='Master account signed in as a tenant',
    ),
    EventType(
        name=EventName.USER_SIGNUP,
        category=EventCategory.AUDIT,
        pii=ACTOR_PII,
        description='User signed up',
    ),

    # Users, groups and API keys
    EventType(
        name=EventName.USER_DEACTIVATE,
        category=EventCategory.AUDIT,
        pii=TARGET_PII,
        description='User deactivated',
    ),
    EventType(
        name=EventName.USER_ADMIN_TOGGLE,
        category=EventCategory.AUDIT,
        pii=TARGET_PII,
        description='User admin permission changed',
    ),
    EventType(
        name=EventName.INVITE_ACCEPT,
        category=EventCategory.AUDIT,
        pii=ACTOR_PII,
        description='Invite accepted',
    ),
    EventType(
        name=EventName.GROUP_CREATE,
        category=EventCategory.AUDIT,
        pii=NAMED_PII,
        description='Group created',
    ),
    EventType(
        name=EventName.GROUP_UPDATE,
        category=EventCategory.AUDIT,
        pii=ACTOR_PII,
        description='Group updated',
    ),
    EventType(
        name=EventName.GROUP_DELETE,
        category=EventCategory.AUDIT,
        pii=NAMED_PII,
        description='Group deleted',
    ),
    EventType(
        name=EventName.API_KEY_CREATE,
        category=EventCategory.AUDIT,
        pii=NAMED_PII,
        description='API key created',
    ),
    EventType(
        name=EventName.API_KEY_REVOKE,
        category=EventCategory.AUDIT,
        pii=NAMED_PII,
        description='API key revoked',
    ),

    # Templates and workflows
    EventType(
        name=EventName.TEMPLATE_PUBLISH,
        category=EventCategory.AUDIT,
        pii=NAMED_PII,
        description='Template published',
    ),
    EventType(
        name=EventName.TEMPLATE_DRAFT_SAVE,
        category=EventCategory.ACTIVITY,
        pii=NAMED_PII,
        description='Template draft saved',
    ),
    EventType(
        name=EventName.TEMPLATE_CLONE,
        category=EventCategory.ACTIVITY,
        pii=NAMED_PII,
        description='Template cloned into a new draft',
    ),
    EventType(
        name=EventName.TEMPLATE_DELETE,
        category=EventCategory.AUDIT,
        pii=NAMED_PII,
        description='Template deleted',
    ),
    EventType(
        name=EventName.TEMPLATE_EXPORT,
        category=EventCategory.AUDIT,
        pii=ACTOR_PII,
        description='Templates exported',
    ),
    EventType(
        name=EventName.WORKFLOW_TERMINATE,
        category=EventCategory.AUDIT,
        pii=(*ACTOR_PII, 'payload.workflow_name'),
        description='Workflow deleted',
    ),

    # Webhooks
    EventType(
        name=EventName.WEBHOOK_SUBSCRIBE,
        category=EventCategory.AUDIT,
        pii=(*ACTOR_PII, 'payload.url'),
        description='Webhook subscription created',
    ),
    EventType(
        name=EventName.WEBHOOK_UNSUBSCRIBE,
        category=EventCategory.AUDIT,
        pii=(*ACTOR_PII, 'payload.url'),
        description='Webhook subscription removed',
    ),

    # Files
    EventType(
        name=EventName.FILE_UPLOAD,
        category=EventCategory.AUDIT,
        pii=FILE_PII,
        description='File uploaded to the file service',
    ),
    EventType(
        name=EventName.FILE_DOWNLOAD,
        category=EventCategory.AUDIT,
        pii=FILE_PII,
        description='File handed out by the file service',
    ),
    EventType(
        name=EventName.FILE_ACCESS_DENIED,
        category=EventCategory.AUDIT,
        pii=FILE_PII,
        description='File download refused by the permission check',
    ),

    # Service types
    EventType(
        name=EventName.HTTP_REQUEST,
        category=EventCategory.HTTP,
        pii=(*ACTOR_PII, 'payload.path'),
        description='API request',
    ),
)

REGISTRY: Dict[str, EventType] = {
    event_type.name: event_type for event_type in EVENT_TYPES
}


class EventRegistry:

    @staticmethod
    def get(name: str) -> EventType:

        """ Return the declared event type or raise. """

        event_type = REGISTRY.get(name)
        if event_type is None:
            raise UnknownEventTypeError(f'Unknown event type: {name}')
        return event_type

    @staticmethod
    def resolve(name: str) -> EventType:

        """ Return the declared event type.
            A typo has to break tests, but it must not break a user
            request in a running deployment: there the event is
            downgraded to the debug category and reported to Sentry
            once per name per process.

            The switch is the explicit LOGS_STRICT flag, not the name
            of the environment: ENVIRONMENT is optional and falls back
            to Development, so any deployment that forgot to set it
            would get the strict mode on live traffic. """

        event_type = REGISTRY.get(name)
        if event_type is not None:
            return event_type
        if settings.LOGS_STRICT:
            raise UnknownEventTypeError(f'Unknown event type: {name}')
        if name not in _reported_unknown_types:
            _reported_unknown_types.add(name)
            capture_sentry_message(
                message='Unknown event type',
                data={'event_type': name},
                level=SentryLogLevel.WARNING,
            )
        # ACTOR_PII, not an empty tuple: the sink moves declared paths
        # into the pii.* namespace, and the collector drops that
        # namespace for external backends. An undeclared type with an
        # empty list would send the e-mail and the ip as plain
        # attributes, straight past the redaction rule.
        return EventType(name, EventCategory.DEBUG, ACTOR_PII)


def validate_registry() -> None:

    """ Raise EventsError if the registry declaration is broken. """

    names: Set[str] = set()
    for event_type in EVENT_TYPES:
        name = event_type.name
        if name in names:
            raise EventsError(f'Duplicated event type: {name}')
        if not EVENT_NAME_PATTERN.match(name):
            raise EventsError(f'Invalid event type name: {name}')
        if event_type.category not in EventCategory.VALUES:
            raise EventsError(
                f'Invalid category "{event_type.category}" '
                f'of the event type: {name}',
            )
        _validate_pii(event_type)
        names.add(name)


def _validate_pii(event_type: EventType) -> None:

    """ An unresolvable path is dropped by the emitter without a word,
        and the field then leaves as a plain attribute past the
        collector rule. A typo here is a silent data leak, so it has
        to break the build instead. """

    for path in event_type.pii:
        head, _, tail = path.partition('.')
        if head in PII_ROOTS and not tail:
            continue
        if head in PII_NAMESPACES and tail:
            continue
        raise EventsError(
            f'Invalid pii path "{path}" of the event type: '
            f'{event_type.name}',
        )
