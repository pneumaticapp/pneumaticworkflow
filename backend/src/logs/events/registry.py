import re
from dataclasses import dataclass
from typing import Dict, Set, Tuple

from django.conf import settings

from src.logs.events.enums import (
    EVENT_CLASSES,
    AccountEvents,
    AdminEvents,
    ApiKeyEvents,
    BillingEvents,
    DatasetEvents,
    EventCategory,
    FileEvents,
    GroupEvents,
    TaskEvents,
    TemplateEvents,
    UserEvents,
    WebhookEvents,
    WorkflowEvents,
    event_names_of,
)
from src.logs.events.exceptions import (
    EventsError,
    UnknownEventTypeError,
)
from src.logs.events.reporting import report_error
from src.utils.logging import SentryLogLevel

EVENT_NAME_PATTERN = re.compile(r'^[a-z_]+\.[a-z_]+\Z')


@dataclass(frozen=True)
class EventType:

    name: str
    category: EventCategory.LITERALS
    description: str = ''


# The declaration table: the events of each class with a description.
# The category comes from the class. A name that is not declared here
# fails the tests through LOGS_STRICT (resolve_event_type), and a
# constant of a class that has no row here fails the start of the
# process (validate_registry).
DECLARATIONS = (
    (WorkflowEvents, (
        (WorkflowEvents.RUN, 'Workflow started'),
        (WorkflowEvents.COMPLETE, 'Workflow completed'),
        (WorkflowEvents.ENDED, 'Workflow ended by a user'),
        (WorkflowEvents.DELAY, 'Workflow delayed'),
        (WorkflowEvents.REVERT, 'Workflow returned to a previous task'),
        (WorkflowEvents.ENDED_BY_CONDITION, 'Workflow ended by a condition'),
        (WorkflowEvents.URGENT, 'Workflow marked as urgent'),
        (WorkflowEvents.NOT_URGENT, 'Workflow urgent mark removed'),
        (WorkflowEvents.FORCE_RESUME, 'Workflow resumed manually'),
        (WorkflowEvents.FORCE_DELAY, 'Workflow delayed manually'),
        (WorkflowEvents.SUB_WORKFLOW_RUN, 'Sub-workflow started'),
        (WorkflowEvents.UPDATE,
         'Workflow name, kickoff fields or due date changed'),
        (WorkflowEvents.TERMINATE, 'Workflow deleted'),
    )),
    (TaskEvents, (
        (TaskEvents.START, 'Task started'),
        (TaskEvents.COMPLETE, 'Task completed'),
        (TaskEvents.REVERT, 'Task returned to the previous performer'),
        (TaskEvents.COMMENT, 'Comment added to a task'),
        (TaskEvents.SKIP, 'Task skipped'),
        (TaskEvents.SKIP_NO_PERFORMERS,
         'Task skipped because it has no performers'),
        (TaskEvents.PERFORMER_CREATED, 'Task performer added'),
        (TaskEvents.PERFORMER_DELETED, 'Task performer removed'),
        (TaskEvents.DUE_DATE_CHANGED, 'Task due date changed'),
        (TaskEvents.PERFORMER_GROUP_CREATED, 'Task performer group added'),
        (TaskEvents.PERFORMER_GROUP_DELETED, 'Task performer group removed'),
        (TaskEvents.DELAY, 'Task delayed'),
        (TaskEvents.DELEGATION, 'Task delegated to another performer'),
        (TaskEvents.COMMENT_UPDATE, 'Comment edited by its author'),
        (TaskEvents.COMMENT_DELETE, 'Comment deleted by its author'),
        (TaskEvents.CHECKLIST_MARK, 'Checklist item marked'),
        (TaskEvents.CHECKLIST_UNMARK, 'Checklist item unmarked'),
    )),
    (UserEvents, (
        (UserEvents.LOGIN, 'User signed in'),
        (UserEvents.LOGOUT, 'User signed out'),
        (UserEvents.LOGIN_FAILED, 'Sign in attempt failed'),
        (UserEvents.LOGIN_AS, 'Superuser signed in as a user'),
        (UserEvents.SIGNUP, 'User signed up'),
        (UserEvents.PASSWORD_RESET_REQUEST,
         'Password reset e-mail requested'),
        (UserEvents.PASSWORD_RESET, 'Password set through a reset link'),
        (UserEvents.PASSWORD_CHANGE, 'Password changed by its owner'),
        (UserEvents.CREATE, 'User created by an admin'),
        (UserEvents.UPDATE,
         'User profile, permissions, groups or manager changed'),
        (UserEvents.PASSWORD_SET, 'Password of a user set by somebody else'),
        (UserEvents.DEACTIVATE, 'User deactivated'),
        (UserEvents.ADMIN_TOGGLE, 'User admin permission changed'),
        (UserEvents.TRANSFER, 'User moved over from another account'),
        (UserEvents.REASSIGN,
         'Tasks and templates handed over to another user or group'),
        (UserEvents.VACATION_ACTIVATE,
         'Vacation turned on, tasks delegated to substitutes'),
        (UserEvents.VACATION_DEACTIVATE,
         'Vacation turned off, delegation withdrawn'),
        (UserEvents.UNSUBSCRIBE,
         'E-mail subscription turned off through a link'),
        (UserEvents.INVITE_CREATE, 'User invited'),
        (UserEvents.INVITE_RESEND, 'Invite sent again'),
        (UserEvents.INVITE_ACCEPT, 'Invite accepted'),
    )),
    (AccountEvents, (
        (AccountEvents.UPDATE, 'Account settings changed'),
        (AccountEvents.VERIFY, 'Account verified through the e-mail link'),
        (AccountEvents.VERIFICATION_RESEND,
         'Account verification e-mail sent again'),
        (AccountEvents.TENANT_CREATE, 'Tenant account created'),
        (AccountEvents.TENANT_DELETE, 'Tenant account deleted'),
        (AccountEvents.TENANT_LOGIN_AS,
         'Master account signed in as a tenant'),
    )),
    (GroupEvents, (
        (GroupEvents.CREATE, 'Group created'),
        (GroupEvents.UPDATE, 'Group updated'),
        (GroupEvents.DELETE, 'Group deleted'),
    )),
    (ApiKeyEvents, (
        (ApiKeyEvents.CREATE, 'API key created'),
        (ApiKeyEvents.REVOKE, 'API key revoked'),
    )),
    (TemplateEvents, (
        (TemplateEvents.PUBLISH, 'Template published'),
        (TemplateEvents.DRAFT_SAVE, 'Template draft saved'),
        (TemplateEvents.CLONE, 'Template cloned into a new draft'),
        (TemplateEvents.DELETE, 'Template deleted'),
        (TemplateEvents.EXPORT, 'Templates exported'),
        (TemplateEvents.DRAFT_DISCARD, 'Template draft changes discarded'),
        (TemplateEvents.AI_GENERATE, 'Template generated with AI'),
        (TemplateEvents.LIBRARY_FILL,
         'Template filled from a library template'),
        (TemplateEvents.LIBRARY_IMPORT,
         'Library templates imported by staff'),
        (TemplateEvents.PRESET_CREATE, 'Template preset created'),
        (TemplateEvents.PRESET_UPDATE, 'Template preset changed'),
        (TemplateEvents.PRESET_DELETE, 'Template preset deleted'),
        (TemplateEvents.PRESET_SET_DEFAULT,
         'Template preset made the default one'),
        (TemplateEvents.FIELDSET_CREATE, 'Shared fieldset created'),
        (TemplateEvents.FIELDSET_UPDATE, 'Shared fieldset changed'),
        (TemplateEvents.FIELDSET_CLONE, 'Shared fieldset cloned'),
        (TemplateEvents.FIELDSET_DELETE, 'Shared fieldset deleted'),
    )),
    (DatasetEvents, (
        (DatasetEvents.CREATE, 'Dataset created'),
        (DatasetEvents.UPDATE, 'Dataset changed'),
        (DatasetEvents.DELETE, 'Dataset deleted'),
        (DatasetEvents.ITEM_CREATE, 'Dataset row created'),
        (DatasetEvents.ITEM_UPDATE, 'Dataset row changed'),
        (DatasetEvents.ITEM_DELETE, 'Dataset row deleted'),
    )),
    (BillingEvents, (
        (BillingEvents.PURCHASE,
         'Subscription purchased or checkout started'),
        (BillingEvents.SUBSCRIPTION_CANCEL, 'Subscription cancelled'),
        (BillingEvents.PAYMENT_CONFIRM,
         'Payment confirmed through the checkout link'),
    )),
    (WebhookEvents, (
        (WebhookEvents.SUBSCRIBE, 'Webhook subscription created'),
        (WebhookEvents.UNSUBSCRIBE, 'Webhook subscription removed'),
    )),
    (FileEvents, (
        (FileEvents.UPLOAD, 'File uploaded to the file service'),
        (FileEvents.DOWNLOAD, 'File handed out by the file service'),
        (FileEvents.ACCESS_DENIED,
         'File download refused by the permission check'),
    )),
    (AdminEvents, (
        (AdminEvents.CREATE, 'Row created in the admin site'),
        (AdminEvents.UPDATE, 'Row changed in the admin site'),
        (AdminEvents.DELETE, 'Row deleted in the admin site'),
    )),
)

EVENT_TYPES: Tuple[EventType, ...] = tuple(
    EventType(name, events_class.CATEGORY, description)
    for events_class, rows in DECLARATIONS
    for name, description in rows
)

REGISTRY: Dict[str, EventType] = {
    event_type.name: event_type for event_type in EVENT_TYPES
}


def resolve_event_type(name: str) -> EventType:

    """ Return the declared event type.
        A typo has to break tests, but it must not break a user
        request in a running deployment: there the event is filed
        under the OTHER category and reported to Sentry once a
        minute per name for as long as it is emitted.

        The switch is the explicit LOGS_STRICT flag, not the name
        of the environment: ENVIRONMENT is optional and falls back
        to Development, so any deployment that forgot to set it
        would get the strict mode on live traffic. """

    event_type = REGISTRY.get(name)
    if event_type is not None:
        return event_type
    if settings.LOGS_STRICT:
        raise UnknownEventTypeError(f'Unknown event type: {name}')
    report_error(
        message='Unknown event type',
        data={'event_type': name},
        level=SentryLogLevel.WARNING,
        key=f'unknown-event-type:{name}',
    )
    return EventType(name, EventCategory.OTHER)


def validate_registry() -> None:

    """ Raise EventsError if the registry declaration is broken:
        a duplicated or malformed name, a category that is not one,
        or a constant of an events class that has no row here. """

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
        names.add(name)
    for events_class in EVENT_CLASSES:
        for name in event_names_of(events_class):
            if name not in names:
                raise EventsError(
                    f'Event type {name} of {events_class.__name__} '
                    f'is not declared in the registry',
                )
