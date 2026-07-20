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

# Authenticated + plan + seat limit
ACCESS_AUTH_OVERLIMIT = access_description(
    'UserIsAuthenticated',
    *GATES_OVERLIMIT,
)

# Admin/owner (+ gates) — datasets write, fieldsets, create…
ACCESS_ADMIN = access_description(
    'UserIsAuthenticated',
    *GATES_OVERLIMIT,
    'UserIsAdminOrAccountOwner',
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
