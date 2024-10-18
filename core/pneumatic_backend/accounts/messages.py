from django.utils.translation import gettext_lazy as _
from django.utils.text import format_lazy

MSG_A_0001 = _(
    'Saving files is not available, file storage does\'t '
    'configured. Contact support.'
)
# Translators: Create invite form validation
MSG_A_0002 = _('The "type" or "invited_from" field must be specified.')
MSG_A_0003 = _('Logo change is not allowed for this account.')
# Translators: Reassign logic when user deleted
MSG_A_0004 = _(
    'You can\'t assign workflows to the same user. Please choose another one.'
)
MSG_A_0005 = _('There is already a registered user with these email.')
MSG_A_0006 = _(
    'You have reached limit on invitations. '
    'Contact Support to invite more users.'
)
MSG_A_0007 = _('Invite is already accepted.')
MSG_A_0008 = _('Token is invalid.')
MSG_A_0009 = _('Token is expired.')
MSG_A_0010 = _('The user with the specified credentials not found.')
# Translators: Validate delete user
MSG_A_0011 = _(
    'You can\'t delete a user without assigning their tasks '
    'to a different user.'
)
MSG_A_0012 = _('Reassign user does not exist.')
MSG_A_0013 = _('Token is invalid or expired.')
# Translators: Unsubscribe from any mailing or digest
MSG_A_0014 = _('You have successfully unsubscribed.')
MSG_A_0015 = _('Email')
MSG_A_0016 = _('First name')
MSG_A_0017 = _('Password')
MSG_A_0018 = _('Password confirmation')
# Translators: Signup form help text
MSG_A_0019 = _('Enter the same password as before, for verification.')
MSG_A_0020 = _('User info')
MSG_A_0021 = _('Status')
MSG_A_0022 = _('Permissions')
MSG_A_0023 = _('Important dates')
MSG_A_0024 = _('This field is required.')
# Translators: Create tenant from admin
MSG_A_0025 = _('"Master account" does not exists.')
# Translators: Create tenant from admin
MSG_A_0026 = _('"Master account" is not subscribed.')
MSG_A_0027 = _(
    'Moving tenants between master accounts is not currently supported.'
)
MSG_A_0028 = _('"Master Account" must be blank for a non-tenant account.')
MSG_A_0029 = _('The "Master account" required for the lease level "tenant".')
# Translators: Validation change lease level
MSG_A_0030 = lambda prev_lease_level, new_lease_level: format_lazy(
    _('Converting from "{prev}" to "{new}" is not currently supported.'),
    prev=prev_lease_level,
    new=new_lease_level,
)
# Translators: Primary account data in the admin
MSG_A_0031 = _('Primary')
# Translators: Subscription account data in the admin
MSG_A_0032 = _('Subscription')
# Translators: Account tenants list in the admin
MSG_A_0033 = _('Tenants')
# Translators: Aborting to delete account from admin if tenants exists
MSG_A_0034 = _('Deletion not allowed while the account contains tenants.')
MSG_A_0035 = _(
    'Your subscription has already expired. '
    'Renew subscription or downgrade to Freemium plan.'
)
# Translators: Account owner permission
MSG_A_0036 = _('Only the account owner is allowed to perform this action.')
# Translators: Free plan paywall
MSG_A_0037 = _(
    'The user count is over your plan limit. '
    'Please upgrade your plan or delete some users.'
)
# Translators: Free plan paywall for toggle admin role
MSG_A_0038 = _(
    'Granular access control is included in the Premium Plan. '
    'Upgrade your plan to access this functionality.'
)
MSG_A_0039 = _(
    'The list of group members contains a non-existent group identifier'
)
MSG_A_0040 = _('The list of groups contains a non-existent group identifier')
