"""Prebuilt Access blocks for OpenAPI endpoint descriptions."""

from src.openapi.helpers import access_description

# Common stacks matching get_permissions() patterns
GATES = (
    'ExpiredSubscriptionPermission',
    'BillingPlanPermission',
)
GATES_OVERLIMIT = (*GATES, 'UsersOverlimitedPermission')

# Authenticated + plan gates (list titles, steps, …)
ACCESS_AUTH = access_description(
    'UserIsAuthenticated',
    *GATES,
)

# Guest-allowed + billing plan (no expired check)
ACCESS_AUTH_LITE = access_description(
    'IsAuthenticated',
    'BillingPlanPermission',
)

# Authenticated user + billing plan (no expired check)
ACCESS_AUTH_BASIC = access_description(
    'UserIsAuthenticated',
    'BillingPlanPermission',
)

# Authenticated + plan + seat limit
ACCESS_AUTH_OVERLIMIT = access_description(
    'UserIsAuthenticated',
    *GATES_OVERLIMIT,
)

# Admin/owner + gates (no seat limit)
ACCESS_ADMIN_BASE = access_description(
    'UserIsAuthenticated',
    *GATES,
    'UserIsAdminOrAccountOwner',
)

# Admin/owner + billing plan (no expired, no seat limit)
ACCESS_ADMIN_BASIC = access_description(
    'UserIsAuthenticated',
    'BillingPlanPermission',
    'UserIsAdminOrAccountOwner',
)

# Admin/owner (+ gates + seat limit) — datasets write, fieldsets…
ACCESS_ADMIN = access_description(
    'UserIsAuthenticated',
    *GATES_OVERLIMIT,
    'UserIsAdminOrAccountOwner',
)

# Dashboard reports
ACCESS_DASHBOARD = access_description(
    'UserIsAuthenticated',
    *GATES,
    'UserCanAccessDashboardPermission',
)

# Highlights feed
ACCESS_HIGHLIGHTS = access_description(
    'UserIsAuthenticated',
    *GATES,
    'UserCanAccessHighlightsPermission',
)

# Push device registration
ACCESS_PUSH = access_description(
    'UserIsAuthenticated',
    'PushPermission',
)

# Template owner/admin object mutations
ACCESS_TEMPLATE_OWNER = access_description(
    'UserIsAuthenticated',
    *GATES_OVERLIMIT,
    'UserIsAdminOrAccountOwner',
    'TemplateAdminOwnerPermission',
)

# Run / list presets — template access roles
ACCESS_TEMPLATE_ACCESS = access_description(
    'UserIsAuthenticated',
    *GATES_OVERLIMIT,
    'TemplateAccessPermission',
)

# Template fields
ACCESS_TEMPLATE_FIELDS = access_description(
    'UserIsAuthenticated',
    *GATES,
    'TemplateFieldsPermission',
)

# AI generate
ACCESS_TEMPLATE_AI = access_description(
    'AIPermission',
    'UserIsAuthenticated',
    *GATES_OVERLIMIT,
    'UserIsAdminOrAccountOwner',
)

# Export templates
ACCESS_ACCOUNT_OWNER = access_description(
    'AccountOwnerPermission',
    *GATES,
)

# Template presets CRUD
ACCESS_PRESET = access_description(
    'UserIsAuthenticated',
    *GATES_OVERLIMIT,
    'UserIsAdminOrAccountOwner',
    'TemplatePresetPermission',
)

# System library templates (same stack as ACCESS_ADMIN)
ACCESS_SYSTEM_TEMPLATE = ACCESS_ADMIN

# Library import (staff)
ACCESS_STAFF_IMPORT = access_description(
    'UserIsAuthenticated',
    *GATES,
    'StaffPermission',
)

# Attachments list
ACCESS_ATTACHMENT = access_description(
    'IsAuthenticated',
)

# Public / embed template
ACCESS_PUBLIC_TEMPLATE = access_description(
    'PublicTemplatePermission',
)

# Checklist (guest-allowed + gates)
ACCESS_CHECKLIST = access_description(
    'IsAuthenticated',
    *GATES,
    'GuestTaskPermission',
)

# Comment edit/delete
ACCESS_COMMENT_EDIT = access_description(
    'IsAuthenticated',
    'BillingPlanPermission',
    'ExpiredSubscriptionPermission',
    'UsersOverlimitedPermission',
    'CommentEditPermission',
)
ACCESS_COMMENT_REACTION = access_description(
    'IsAuthenticated',
    'BillingPlanPermission',
    'ExpiredSubscriptionPermission',
    'UsersOverlimitedPermission',
    'CommentReactionPermission',
)

# Notifications
ACCESS_NOTIFICATIONS_LIST = access_description(
    'UserIsAuthenticated',
)
ACCESS_NOTIFICATIONS_DESTROY = access_description(
    'UserIsAuthenticated',
    'BillingPlanPermission',
    'ExpiredSubscriptionPermission',
)

# Tasks
ACCESS_TASK_RETRIEVE = access_description(
    'IsAuthenticated',
    *GATES,
    'TaskWorkflowMemberOrViewerPermission',
    'GuestTaskPermission',
)
ACCESS_TASK_PERFORMER = access_description(
    'UserIsAuthenticated',
    *GATES,
    'UserIsAdminOrAccountOwner',
    'TaskWorkflowOwnerPermission',
    'UsersOverlimitedPermission',
)
ACCESS_TASK_COMPLETE = access_description(
    'IsAuthenticated',
    *GATES,
    'UsersOverlimitedPermission',
    'TaskCompletePermission',
)
ACCESS_TASK_REVERT = access_description(
    'UserIsAuthenticated',
    *GATES,
    'UsersOverlimitedPermission',
    'TaskRevertPermission',
)
ACCESS_TASK_COMMENT = access_description(
    'IsAuthenticated',
    *GATES,
    'GuestTaskPermission',
    'TaskCommentPermission',
)

# Tenants
ACCESS_TENANT_WRITE = access_description(
    'UserIsAuthenticated',
    'BillingPlanPermission',
    'ExpiredSubscriptionPermission',
    'MasterAccountPermission',
    'UserIsAdminOrAccountOwner',
)
ACCESS_TENANT_ACCESS = access_description(
    'UserIsAuthenticated',
    'BillingPlanPermission',
    'ExpiredSubscriptionPermission',
    'MasterAccountAccessPermission',
    'UserIsAdminOrAccountOwner',
)
ACCESS_TENANT_READ = access_description(
    'UserIsAuthenticated',
    'ExpiredSubscriptionPermission',
    'MasterAccountPermission',
    'UserIsAdminOrAccountOwner',
)

# Workflows
ACCESS_WORKFLOW_OWNER = access_description(
    'UserIsAuthenticated',
    *GATES,
    'UserIsAdminOrAccountOwner',
    'WorkflowOwnerPermission',
    'UsersOverlimitedPermission',
)
ACCESS_WORKFLOW_MEMBER = access_description(
    'UserIsAuthenticated',
    *GATES,
    'WorkflowMemberOrViewerPermission',
)
ACCESS_WORKFLOW_COMPLETE = access_description(
    'IsAuthenticated',
    *GATES,
    'UsersOverlimitedPermission',
    'GuestWorkflowPermission',
)
ACCESS_WORKFLOW_COMMENT = access_description(
    'IsAuthenticated',
    *GATES,
    'UsersOverlimitedPermission',
    'GuestWorkflowPermission',
    'WorkflowCommentPermission',
)
ACCESS_WORKFLOW_EVENTS = access_description(
    'IsAuthenticated',
    *GATES,
    'GuestWorkflowEventsPermission',
    'WorkflowMemberOrViewerPermission',
)
