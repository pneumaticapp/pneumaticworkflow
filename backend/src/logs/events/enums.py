from typing import Optional

from typing_extensions import Literal, get_args

from src.authentication.enums import AuthTokenType


class EventCategory:

    AUDIT = 'audit'
    ACTIVITY = 'activity'
    DEBUG = 'debug'

    LITERALS = Literal[
        AUDIT,
        ACTIVITY,
        DEBUG,
    ]
    VALUES = set(get_args(LITERALS))


class TemplateSource:

    """ How a template came to be, when not through the editor. """

    BY_STEPS = 'by_steps'
    LIBRARY = 'library'


class LogoutReason:

    """ Why a session ended, when not by the user asking for it. """

    IDENTITY_PROVIDER = 'identity_provider'


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
    COMMENT = 'comment'
    CHECKLIST = 'checklist'
    TEMPLATE_PRESET = 'template_preset'
    SYSTEM_TEMPLATE = 'system_template'
    FIELDSET = 'fieldset'
    DATASET = 'dataset'
    DATASET_ITEM = 'dataset_item'
    WEBHOOK = 'webhook'
    FILE = 'file'
    # A row of the admin site that is none of the above: its model is
    # named in the payload of the event.
    OTHER = 'other'

    LITERALS = Literal[
        ACCOUNT,
        USER,
        INVITE,
        GROUP,
        API_KEY,
        TEMPLATE,
        WORKFLOW,
        TASK,
        COMMENT,
        CHECKLIST,
        TEMPLATE_PRESET,
        SYSTEM_TEMPLATE,
        FIELDSET,
        DATASET,
        DATASET_ITEM,
        WEBHOOK,
        FILE,
        OTHER,
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

    # Workflows and tasks changed in place: no WorkflowEvent behind them
    WORKFLOW_UPDATE = 'workflow.update'
    TASK_COMMENT_UPDATE = 'task.comment_update'
    TASK_COMMENT_DELETE = 'task.comment_delete'
    TASK_CHECKLIST_MARK = 'task.checklist_mark'
    TASK_CHECKLIST_UNMARK = 'task.checklist_unmark'

    # Authentication
    USER_LOGIN = 'user.login'
    USER_LOGOUT = 'user.logout'
    USER_LOGIN_FAILED = 'user.login_failed'
    USER_LOGIN_AS = 'user.login_as'
    TENANT_LOGIN_AS = 'tenant.login_as'
    USER_SIGNUP = 'user.signup'
    USER_PASSWORD_RESET_REQUEST = 'user.password_reset_request'
    USER_PASSWORD_RESET = 'user.password_reset'
    USER_PASSWORD_CHANGE = 'user.password_change'

    # Accounts, users, groups and API keys
    ACCOUNT_UPDATE = 'account.update'
    ACCOUNT_VERIFY = 'account.verify'
    ACCOUNT_VERIFICATION_RESEND = 'account.verification_resend'
    TENANT_CREATE = 'tenant.create'
    TENANT_DELETE = 'tenant.delete'
    USER_CREATE = 'user.create'
    USER_UPDATE = 'user.update'
    USER_PASSWORD_SET = 'user.password_set'
    USER_DEACTIVATE = 'user.deactivate'
    USER_ADMIN_TOGGLE = 'user.admin_toggle'
    USER_TRANSFER = 'user.transfer'
    USER_REASSIGN = 'user.reassign'
    USER_VACATION_ACTIVATE = 'user.vacation_activate'
    USER_VACATION_DEACTIVATE = 'user.vacation_deactivate'
    USER_UNSUBSCRIBE = 'user.unsubscribe'
    INVITE_CREATE = 'invite.create'
    INVITE_RESEND = 'invite.resend'
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
    TEMPLATE_DRAFT_DISCARD = 'template.draft_discard'
    TEMPLATE_AI_GENERATE = 'template.ai_generate'
    TEMPLATE_LIBRARY_FILL = 'template.library_fill'
    TEMPLATE_LIBRARY_IMPORT = 'template.library_import'
    TEMPLATE_PRESET_CREATE = 'template_preset.create'
    TEMPLATE_PRESET_UPDATE = 'template_preset.update'
    TEMPLATE_PRESET_DELETE = 'template_preset.delete'
    TEMPLATE_PRESET_SET_DEFAULT = 'template_preset.set_default'
    FIELDSET_CREATE = 'fieldset.create'
    FIELDSET_UPDATE = 'fieldset.update'
    FIELDSET_CLONE = 'fieldset.clone'
    FIELDSET_DELETE = 'fieldset.delete'
    WORKFLOW_TERMINATE = 'workflow.terminate'

    # Datasets
    DATASET_CREATE = 'dataset.create'
    DATASET_UPDATE = 'dataset.update'
    DATASET_DELETE = 'dataset.delete'
    DATASET_ITEMS_ADD = 'dataset.items_add'
    DATASET_ITEMS_REPLACE = 'dataset.items_replace'
    DATASET_ITEM_CREATE = 'dataset.item_create'
    DATASET_ITEM_UPDATE = 'dataset.item_update'
    DATASET_ITEM_DELETE = 'dataset.item_delete'

    # Billing
    BILLING_PURCHASE = 'billing.purchase'
    BILLING_SUBSCRIPTION_CANCEL = 'billing.subscription_cancel'
    BILLING_PAYMENT_CONFIRM = 'billing.payment_confirm'

    # Django admin site: a superuser editing the rows directly
    ADMIN_CREATE = 'admin.create'
    ADMIN_UPDATE = 'admin.update'
    ADMIN_DELETE = 'admin.delete'

    # Webhooks
    WEBHOOK_SUBSCRIBE = 'webhook.subscribe'
    WEBHOOK_UNSUBSCRIBE = 'webhook.unsubscribe'

    # Files: written by the file service into the same stream, the
    # backend only declares them. The record it writes is built in
    # storage/src/shared_kernel/events/schema.py, and the shape both
    # sides agree on is checked by tests/test_file_service_contract.py
    FILE_UPLOAD = 'file.upload'
    FILE_DOWNLOAD = 'file.download'
    FILE_ACCESS_DENIED = 'file.access_denied'


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
        An unknown value is the system: the lookup default answers
        it. A caller that knows a person is behind the call passes
        AuthTokenType.USER in place of a missing auth type itself
        (Actor.from_user, context_from_request). """

    return AUTH_TYPE_ACTOR_TYPES.get(auth_type, ActorType.SYSTEM)
