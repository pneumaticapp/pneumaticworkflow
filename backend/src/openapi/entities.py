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
    PushPermission = 'Push notifications feature enabled'

    # Reports
    UserCanAccessDashboardPermission = (
        'Admin/account owner, or any template '
        'owner/viewer/starter on the account'
    )
    UserCanAccessHighlightsPermission = (
        'Admin/account owner, or any template '
        'owner/viewer/starter on the account'
    )

    # Workflows
    WorkflowMemberOrViewerPermission = (
        'Account owner; workflow member; '
        'template owner or viewer'
    )
    WorkflowOwnerPermission = (
        'Admin/account owner who started the workflow'
    )
    GuestWorkflowPermission = (
        'Guest user with access to this workflow'
    )
    GuestWorkflowEventsPermission = (
        'Guest user with access to workflow events'
    )
    WorkflowCommentPermission = (
        'Workflow member or guest with comment access'
    )

    # Tasks
    TaskWorkflowMemberOrViewerPermission = (
        'Workflow member, template owner/viewer, or guest '
        'assigned to this task'
    )
    TaskWorkflowMemberPermission = (
        'Account owner or workflow member; '
        'guest for this task where allowed'
    )
    TaskWorkflowOwnerPermission = (
        'Admin/account owner who owns the workflow'
    )
    TaskCompletePermission = (
        'Task performer (user/group) or guest '
        'assigned to this task'
    )
    TaskRevertPermission = (
        'Task performer who can revert a completed task'
    )
    TaskCommentPermission = (
        'Task member or guest with comment access'
    )
    GuestTaskPermission = (
        'Guest user assigned to this task'
    )

    # Comments
    CommentEditPermission = (
        'Comment author (can edit/delete own comments)'
    )
    CommentReactionPermission = (
        'Workflow member with access to react to comments'
    )

    # Tenants
    MasterAccountPermission = (
        'Master account with tenants feature enabled'
    )
    MasterAccountAccessPermission = (
        'Master account with access to manage tenants'
    )
