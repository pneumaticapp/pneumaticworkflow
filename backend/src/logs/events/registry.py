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

# Personal data sets of the declaration table below. A path names a
# field of the record: "ip", "actor.email", "payload.<key>".
ACTOR_PII = ('actor.email', 'ip', 'user_agent')
ANONYMOUS_PII = ('ip', 'user_agent')
WORKFLOW_PII = (
    *ACTOR_PII,
    'payload.workflow_name',
    'payload.task_name',
)
WORKFLOW_NAME_PII = (*ACTOR_PII, 'payload.workflow_name')
NAMED_PII = (*ACTOR_PII, 'payload.name')
TARGET_PII = (*ACTOR_PII, 'payload.target_email')
FILE_PII = (*ACTOR_PII, 'payload.filename')
URL_PII = (*ACTOR_PII, 'payload.url')
PATH_PII = (*ACTOR_PII, 'payload.path')
# The reason of a login as is free text typed by a staff member: it
# names people and tickets as often as not.
LOGIN_AS_PII = (*TARGET_PII, 'payload.reason')

PII_ROOTS = ('ip', 'user_agent')
PII_NAMESPACES = ('actor', 'object', 'payload')

_reported_unknown_types: Set[str] = set()


@dataclass(frozen=True)
class EventType:

    name: str
    category: str
    pii: Tuple[str, ...] = ()
    description: str = ''

    @property
    def effective_pii(self) -> Tuple[str, ...]:

        """ The declared personal fields together with ACTOR_PII,
            which counts for every type: the actor e-mail, the ip and
            the user agent are personal data of whoever made the
            request whatever the type is, and a type that forgot to
            declare them would leak them as plain attributes.

            Both ends of the pipeline read this one list, the emitter
            to fill Event.pii and the sink to move the same paths
            into the pii.* namespace. Two lists would disagree, and a
            personal field would end up outside that namespace. """

        return self.pii + tuple(
            path for path in ACTOR_PII if path not in self.pii
        )


# Short names of the categories, for the width of the table below.
AUDIT = EventCategory.AUDIT
ACTIVITY = EventCategory.ACTIVITY
HTTP = EventCategory.HTTP

# The declaration table: one row per event type, as
# (name, category, personal data, description).
#
# The first block holds one row per WorkflowEventType constant,
# mapped by adapters/workflow.py; a new constant there needs a row
# here. A name that is not declared in this table fails the tests
# through LOGS_STRICT (resolve_event_type).
DECLARATIONS = (
    (EventName.WORKFLOW_RUN, AUDIT, WORKFLOW_PII, 'Workflow started'),
    (EventName.WORKFLOW_COMPLETE, AUDIT, WORKFLOW_PII, 'Workflow completed'),
    (EventName.TASK_START, ACTIVITY, WORKFLOW_PII, 'Task started'),
    (EventName.TASK_COMPLETE, AUDIT, WORKFLOW_PII, 'Task completed'),
    (EventName.TASK_REVERT, AUDIT, WORKFLOW_PII,
     'Task returned to the previous performer'),
    (EventName.TASK_COMMENT, ACTIVITY, WORKFLOW_PII,
     'Comment added to a task'),
    (EventName.WORKFLOW_ENDED, AUDIT, WORKFLOW_PII,
     'Workflow ended by a user'),
    (EventName.WORKFLOW_DELAY, ACTIVITY, WORKFLOW_PII, 'Workflow delayed'),
    (EventName.WORKFLOW_REVERT, AUDIT, WORKFLOW_PII,
     'Workflow returned to a previous task'),
    (EventName.TASK_SKIP, ACTIVITY, WORKFLOW_PII, 'Task skipped'),
    (EventName.WORKFLOW_ENDED_BY_CONDITION, ACTIVITY, WORKFLOW_PII,
     'Workflow ended by a condition'),
    (EventName.WORKFLOW_URGENT, ACTIVITY, WORKFLOW_PII,
     'Workflow marked as urgent'),
    (EventName.WORKFLOW_NOT_URGENT, ACTIVITY, WORKFLOW_PII,
     'Workflow urgent mark removed'),
    (EventName.TASK_SKIP_NO_PERFORMERS, ACTIVITY, WORKFLOW_PII,
     'Task skipped because it has no performers'),
    (EventName.TASK_PERFORMER_CREATED, AUDIT, WORKFLOW_PII,
     'Task performer added'),
    (EventName.TASK_PERFORMER_DELETED, AUDIT, WORKFLOW_PII,
     'Task performer removed'),
    (EventName.WORKFLOW_FORCE_RESUME, ACTIVITY, WORKFLOW_PII,
     'Workflow resumed manually'),
    (EventName.WORKFLOW_FORCE_DELAY, ACTIVITY, WORKFLOW_PII,
     'Workflow delayed manually'),
    (EventName.TASK_DUE_DATE_CHANGED, ACTIVITY, WORKFLOW_PII,
     'Task due date changed'),
    (EventName.WORKFLOW_SUB_WORKFLOW_RUN, ACTIVITY, WORKFLOW_PII,
     'Sub-workflow started'),
    (EventName.TASK_PERFORMER_GROUP_CREATED, AUDIT, WORKFLOW_PII,
     'Task performer group added'),
    (EventName.TASK_PERFORMER_GROUP_DELETED, AUDIT, WORKFLOW_PII,
     'Task performer group removed'),
    (EventName.TASK_DELAY, ACTIVITY, WORKFLOW_PII, 'Task delayed'),
    (EventName.TASK_DELEGATION, AUDIT, WORKFLOW_PII,
     'Task delegated to another performer'),

    # Authentication
    (EventName.USER_LOGIN, AUDIT, ACTOR_PII, 'User signed in'),
    (EventName.USER_LOGOUT, AUDIT, ACTOR_PII, 'User signed out'),
    (EventName.USER_LOGIN_FAILED, AUDIT, ANONYMOUS_PII,
     'Sign in attempt failed'),
    (EventName.USER_LOGIN_AS, AUDIT, LOGIN_AS_PII,
     'Superuser signed in as a user'),
    (EventName.TENANT_LOGIN_AS, AUDIT, ACTOR_PII,
     'Master account signed in as a tenant'),
    (EventName.USER_SIGNUP, AUDIT, ACTOR_PII, 'User signed up'),

    # Users, groups and API keys
    (EventName.USER_DEACTIVATE, AUDIT, TARGET_PII, 'User deactivated'),
    (EventName.USER_ADMIN_TOGGLE, AUDIT, TARGET_PII,
     'User admin permission changed'),
    (EventName.INVITE_ACCEPT, AUDIT, ACTOR_PII, 'Invite accepted'),
    (EventName.GROUP_CREATE, AUDIT, NAMED_PII, 'Group created'),
    (EventName.GROUP_UPDATE, AUDIT, ACTOR_PII, 'Group updated'),
    (EventName.GROUP_DELETE, AUDIT, NAMED_PII, 'Group deleted'),
    (EventName.API_KEY_CREATE, AUDIT, NAMED_PII, 'API key created'),
    (EventName.API_KEY_REVOKE, AUDIT, NAMED_PII, 'API key revoked'),

    # Templates and workflows
    (EventName.TEMPLATE_PUBLISH, AUDIT, NAMED_PII, 'Template published'),
    (EventName.TEMPLATE_DRAFT_SAVE, ACTIVITY, NAMED_PII,
     'Template draft saved'),
    (EventName.TEMPLATE_CLONE, ACTIVITY, NAMED_PII,
     'Template cloned into a new draft'),
    (EventName.TEMPLATE_DELETE, AUDIT, NAMED_PII, 'Template deleted'),
    (EventName.TEMPLATE_EXPORT, AUDIT, ACTOR_PII, 'Templates exported'),
    (EventName.WORKFLOW_TERMINATE, AUDIT, WORKFLOW_NAME_PII,
     'Workflow deleted'),

    # Webhooks
    (EventName.WEBHOOK_SUBSCRIBE, AUDIT, URL_PII,
     'Webhook subscription created'),
    (EventName.WEBHOOK_UNSUBSCRIBE, AUDIT, URL_PII,
     'Webhook subscription removed'),

    # Files
    (EventName.FILE_UPLOAD, AUDIT, FILE_PII,
     'File uploaded to the file service'),
    (EventName.FILE_DOWNLOAD, AUDIT, FILE_PII,
     'File handed out by the file service'),
    (EventName.FILE_ACCESS_DENIED, AUDIT, FILE_PII,
     'File download refused by the permission check'),

    # Service types
    (EventName.HTTP_REQUEST, HTTP, PATH_PII, 'API request'),
)

EVENT_TYPES: Tuple[EventType, ...] = tuple(
    EventType(*declaration) for declaration in DECLARATIONS
)

REGISTRY: Dict[str, EventType] = {
    event_type.name: event_type for event_type in EVENT_TYPES
}


def get_event_type(name: str) -> EventType:

    """ Return the declared event type or raise. """

    event_type = REGISTRY.get(name)
    if event_type is None:
        raise UnknownEventTypeError(f'Unknown event type: {name}')
    return event_type


def resolve_event_type(name: str) -> EventType:

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
