"""OpenAPI documentation entities (docs only)."""


class PermissionDoc:
    """Permission class name → human-readable Access block text."""

    # Auth / identity
    IsAuthenticated = 'Authenticated user or token'
    UserIsAuthenticated = 'Authenticated user (not guest)'
    UserIsAdminOrAccountOwner = 'Admin or account owner'
    AccountOwnerPermission = 'Account owner'
    StaffPermission = 'Staff user'
    IsAuthenticatedOrPublicTemplate = (
        'Authenticated user/token, or valid public '
        'template token'
    )
    PublicTemplatePermission = (
        'Valid public or embedded template token'
    )

    # Account gates
    ExpiredSubscriptionPermission = (
        'Account subscription is not expired '
        '(free plans always allowed)'
    )
    BillingPlanPermission = 'Account has a billing plan'
    UsersOverlimitedPermission = (
        'Account is within the user seat limit'
    )

    # Templates
    TemplateAdminOwnerPermission = (
        'Account owner or template owner'
    )
    TemplateAccessPermission = (
        'Account owner; template owner, viewer, '
        'or starter'
    )
    TemplateFieldsPermission = (
        'Account owner; template owner or viewer; '
        'or workflow member on this template'
    )
    TemplatePresetPermission = (
        'Preset author, account owner, or admin '
        'template owner (for account presets)'
    )

    # Features
    AIPermission = 'AI feature enabled for the project'

    # Tasks / workflows (for future blocks)
    TaskWorkflowMemberOrViewerPermission = (
        'Account owner; workflow member; '
        'template owner or viewer; guest for this task'
    )
    TaskCompletePermission = (
        'Account owner or task performer '
        '(user or group); guest only for own task'
    )
    TaskWorkflowMemberPermission = (
        'Account owner or workflow member; '
        'guest for this task where allowed'
    )
    TaskCommentPermission = (
        'Account owner, workflow member, or guest '
        'with access to comment on this task'
    )
    WorkflowMemberOrViewerPermission = (
        'Account owner; workflow member; '
        'template owner or viewer'
    )
