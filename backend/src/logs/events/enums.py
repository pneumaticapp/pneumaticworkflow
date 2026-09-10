from typing import Optional

from typing_extensions import Literal

from src.authentication.enums import AuthTokenType


class EventCategory:

    AUDIT = 'audit'
    ACTIVITY = 'activity'
    HTTP = 'http'
    DEBUG = 'debug'

    VALUES = {AUDIT, ACTIVITY, HTTP, DEBUG}

    LITERALS = Literal[
        AUDIT,
        ACTIVITY,
        HTTP,
        DEBUG,
    ]


class ActorType:

    USER = 'user'
    API_KEY = 'api_key'
    SYSTEM = 'system'
    GUEST = 'guest'

    LITERALS = Literal[
        USER,
        API_KEY,
        SYSTEM,
        GUEST,
    ]


class EventObjectType:

    """ What an event is about: the object.type of the record. """

    ACCOUNT = 'account'
    USER = 'user'
    INVITE = 'invite'
    GROUP = 'group'
    API_KEY = 'api_key'
    TEMPLATE = 'template'
    WORKFLOW = 'workflow'
    TASK = 'task'
    WEBHOOK = 'webhook'
    FILE = 'file'

    LITERALS = Literal[
        ACCOUNT,
        USER,
        INVITE,
        GROUP,
        API_KEY,
        TEMPLATE,
        WORKFLOW,
        TASK,
        WEBHOOK,
        FILE,
    ]


class EventName:

    """ Names of the event types, one constant per registry entry.
        The registry (registry.py) declares category and personal
        data for each of them; a name that is not declared there
        fails the tests through LOGS_STRICT. """

    # Workflow events, one per WorkflowEventType
    WORKFLOW_RUN = 'workflow.run'
    WORKFLOW_COMPLETE = 'workflow.complete'
    TASK_START = 'task.start'
    TASK_COMPLETE = 'task.complete'
    TASK_REVERT = 'task.revert'
    TASK_COMMENT = 'task.comment'
    WORKFLOW_ENDED = 'workflow.ended'
    WORKFLOW_DELAY = 'workflow.delay'
    WORKFLOW_REVERT = 'workflow.revert'
    TASK_SKIP = 'task.skip'
    WORKFLOW_ENDED_BY_CONDITION = 'workflow.ended_by_condition'
    WORKFLOW_URGENT = 'workflow.urgent'
    WORKFLOW_NOT_URGENT = 'workflow.not_urgent'
    TASK_SKIP_NO_PERFORMERS = 'task.skip_no_performers'
    TASK_PERFORMER_CREATED = 'task.performer_created'
    TASK_PERFORMER_DELETED = 'task.performer_deleted'
    WORKFLOW_FORCE_RESUME = 'workflow.force_resume'
    WORKFLOW_FORCE_DELAY = 'workflow.force_delay'
    TASK_DUE_DATE_CHANGED = 'task.due_date_changed'
    WORKFLOW_SUB_WORKFLOW_RUN = 'workflow.sub_workflow_run'
    TASK_PERFORMER_GROUP_CREATED = 'task.performer_group_created'
    TASK_PERFORMER_GROUP_DELETED = 'task.performer_group_deleted'
    TASK_DELAY = 'task.delay'
    TASK_DELEGATION = 'task.delegation'

    # Authentication
    USER_LOGIN = 'user.login'
    USER_LOGOUT = 'user.logout'
    USER_LOGIN_FAILED = 'user.login_failed'
    USER_LOGIN_AS = 'user.login_as'
    TENANT_LOGIN_AS = 'tenant.login_as'
    USER_SIGNUP = 'user.signup'

    # Users, groups and API keys
    USER_DEACTIVATE = 'user.deactivate'
    USER_ADMIN_TOGGLE = 'user.admin_toggle'
    INVITE_ACCEPT = 'invite.accept'
    GROUP_CREATE = 'group.create'
    GROUP_UPDATE = 'group.update'
    GROUP_DELETE = 'group.delete'
    API_KEY_CREATE = 'api_key.create'
    API_KEY_REVOKE = 'api_key.revoke'

    # Templates and workflows
    TEMPLATE_PUBLISH = 'template.publish'
    TEMPLATE_DRAFT_SAVE = 'template.draft_save'
    TEMPLATE_CLONE = 'template.clone'
    TEMPLATE_DELETE = 'template.delete'
    TEMPLATE_EXPORT = 'template.export'
    WORKFLOW_TERMINATE = 'workflow.terminate'

    # Webhooks
    WEBHOOK_SUBSCRIBE = 'webhook.subscribe'
    WEBHOOK_UNSUBSCRIBE = 'webhook.unsubscribe'

    # Files: written by the file service into the same stream, the
    # backend only declares them (docs/logging-file-service-design.md)
    FILE_UPLOAD = 'file.upload'
    FILE_DOWNLOAD = 'file.download'
    FILE_ACCESS_DENIED = 'file.access_denied'

    # Service types
    HTTP_REQUEST = 'http.request'


AUTH_TYPE_ACTOR_TYPES = {
    AuthTokenType.API: ActorType.API_KEY,
    AuthTokenType.GUEST: ActorType.GUEST,
    AuthTokenType.PUBLIC: ActorType.GUEST,
    AuthTokenType.EMBEDDED: ActorType.GUEST,
    AuthTokenType.USER: ActorType.USER,
    AuthTokenType.WEBHOOK: ActorType.SYSTEM,
}


def actor_type_from_auth(auth_type: Optional[str]) -> str:

    """ Convert AuthTokenType value to the event actor type.
        Unknown and empty values mean a non-request context. """

    if not auth_type:
        return ActorType.SYSTEM
    return AUTH_TYPE_ACTOR_TYPES.get(auth_type, ActorType.SYSTEM)
