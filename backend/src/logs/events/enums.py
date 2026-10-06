from typing_extensions import Literal, get_args


class EventCategory:
    """What an event is about, the way the analytics module groups
    its events: one value per kind of thing a user acts on. The
    category is an index label of the log backend, so a dashboard
    filters by it before it reads a single record."""

    WORKFLOWS = 'workflows'
    TASKS = 'tasks'
    USERS = 'users'
    ACCOUNTS = 'accounts'
    GROUPS = 'groups'
    API_KEYS = 'api_keys'
    TEMPLATES = 'templates'
    DATASETS = 'datasets'
    BILLING = 'billing'
    WEBHOOKS = 'webhooks'
    FILES = 'files'
    ADMIN = 'admin'

    LITERALS = Literal[
        WORKFLOWS,
        TASKS,
        USERS,
        ACCOUNTS,
        GROUPS,
        API_KEYS,
        TEMPLATES,
        DATASETS,
        BILLING,
        WEBHOOKS,
        FILES,
        ADMIN,
    ]
    VALUES = set(get_args(LITERALS))


class TemplateSource:
    """How a template came to be, when not through the editor."""

    BY_STEPS = 'by_steps'
    LIBRARY = 'library'


class LogoutReason:
    """Why a session ended, when not by the user asking for it."""

    IDENTITY_PROVIDER = 'identity_provider'


class LoginFailedReason:
    """Why a sign in was refused, the reason of a user.login_failed
    event. One value per refusing branch, so that an alert can
    tell a brute force burst from a deactivated account."""

    BAD_CREDENTIALS = 'bad_credentials'
    VERIFICATION_EXPIRED = 'verification_expired'
    SIGNUP_DISABLED = 'signup_disabled'
    SSO_REQUIRED = 'sso_required'

    LITERALS = Literal[
        BAD_CREDENTIALS,
        VERIFICATION_EXPIRED,
        SIGNUP_DISABLED,
        SSO_REQUIRED,
    ]


class WorkflowEvents:
    # Written next to the WorkflowEvent of the same action
    RUN = 'workflow.run'
    COMPLETE = 'workflow.complete'
    ENDED = 'workflow.ended'
    REVERT = 'workflow.revert'
    ENDED_BY_CONDITION = 'workflow.ended_by_condition'
    URGENT = 'workflow.urgent'
    NOT_URGENT = 'workflow.not_urgent'
    FORCE_RESUME = 'workflow.force_resume'
    FORCE_DELAY = 'workflow.force_delay'
    SUB_WORKFLOW_RUN = 'workflow.sub_workflow_run'
    # Changed in place: no WorkflowEvent behind them
    UPDATE = 'workflow.update'
    TERMINATE = 'workflow.terminate'


class TaskEvents:
    # Written next to the WorkflowEvent of the same action
    START = 'task.start'
    COMPLETE = 'task.complete'
    REVERT = 'task.revert'
    COMMENT = 'task.comment'
    SKIP = 'task.skip'
    SKIP_NO_PERFORMERS = 'task.skip_no_performers'
    PERFORMER_CREATED = 'task.performer_created'
    PERFORMER_DELETED = 'task.performer_deleted'
    DUE_DATE_CHANGED = 'task.due_date_changed'
    PERFORMER_GROUP_CREATED = 'task.performer_group_created'
    PERFORMER_GROUP_DELETED = 'task.performer_group_deleted'
    DELAY = 'task.delay'
    DELEGATION = 'task.delegation'
    # Changed in place: no WorkflowEvent behind them
    COMMENT_UPDATE = 'task.comment_update'
    COMMENT_DELETE = 'task.comment_delete'
    REACTION_CREATE = 'task.reaction_create'
    REACTION_DELETE = 'task.reaction_delete'
    CHECKLIST_MARK = 'task.checklist_mark'
    CHECKLIST_UNMARK = 'task.checklist_unmark'


class UserEvents:
    # Authentication
    LOGIN = 'user.login'
    LOGOUT = 'user.logout'
    LOGIN_FAILED = 'user.login_failed'
    LOGIN_AS = 'user.login_as'
    SIGNUP = 'user.signup'
    PASSWORD_RESET_REQUEST = 'user.password_reset_request'
    PASSWORD_RESET = 'user.password_reset'
    PASSWORD_CHANGE = 'user.password_change'
    # The user as a row of the account
    CREATE = 'user.create'
    UPDATE = 'user.update'
    PASSWORD_SET = 'user.password_set'
    DEACTIVATE = 'user.deactivate'
    ADMIN_TOGGLE = 'user.admin_toggle'
    TRANSFER = 'user.transfer'
    REASSIGN = 'user.reassign'
    VACATION_ACTIVATE = 'user.vacation_activate'
    VACATION_DEACTIVATE = 'user.vacation_deactivate'
    UNSUBSCRIBE = 'user.unsubscribe'
    # Invites: how a user gets into the account
    INVITE_CREATE = 'invite.create'
    INVITE_RESEND = 'invite.resend'
    INVITE_ACCEPT = 'invite.accept'


class AccountEvents:
    UPDATE = 'account.update'
    VERIFY = 'account.verify'
    VERIFICATION_RESEND = 'account.verification_resend'
    # A tenant is an account of the master account
    TENANT_CREATE = 'tenant.create'
    TENANT_DELETE = 'tenant.delete'
    TENANT_LOGIN_AS = 'tenant.login_as'


class GroupEvents:
    CREATE = 'group.create'
    UPDATE = 'group.update'
    DELETE = 'group.delete'


class ApiKeyEvents:
    CREATE = 'api_key.create'
    REVOKE = 'api_key.revoke'


class TemplateEvents:
    CREATE = 'template.create'
    UPDATE = 'template.update'
    CLONE = 'template.clone'
    DELETE = 'template.delete'
    EXPORT = 'template.export'
    DRAFT_DISCARD = 'template.draft_discard'
    AI_GENERATE = 'template.ai_generate'
    LIBRARY_FILL = 'template.library_fill'
    LIBRARY_IMPORT = 'template.library_import'
    PRESET_CREATE = 'template_preset.create'
    PRESET_UPDATE = 'template_preset.update'
    PRESET_DELETE = 'template_preset.delete'
    PRESET_SET_DEFAULT = 'template_preset.set_default'
    # Shared fieldsets are parts of templates
    FIELDSET_CREATE = 'fieldset.create'
    FIELDSET_UPDATE = 'fieldset.update'
    FIELDSET_CLONE = 'fieldset.clone'
    FIELDSET_DELETE = 'fieldset.delete'


class DatasetEvents:
    CREATE = 'dataset.create'
    UPDATE = 'dataset.update'
    DELETE = 'dataset.delete'
    ITEM_CREATE = 'dataset.item_create'
    ITEM_UPDATE = 'dataset.item_update'
    ITEM_DELETE = 'dataset.item_delete'


class BillingEvents:
    PURCHASE = 'billing.purchase'
    SUBSCRIPTION_CANCEL = 'billing.subscription_cancel'
    PAYMENT_CONFIRM = 'billing.payment_confirm'


class WebhookEvents:
    SUBSCRIBE = 'webhook.subscribe'
    UNSUBSCRIBE = 'webhook.unsubscribe'


class FileEvents:
    """Written by the file service into the same stream, the backend
    only declares them. The record it writes is built in
    storage/src/shared_kernel/events/schema.py, and the shape both
    sides agree on is checked by tests/test_file_service_contract.py"""

    UPLOAD = 'file.upload'
    DOWNLOAD = 'file.download'
    ACCESS_DENIED = 'file.access_denied'


class AdminEvents:
    """Django admin site: a superuser editing the rows directly."""

    CREATE = 'admin.create'
    UPDATE = 'admin.update'
    DELETE = 'admin.delete'
