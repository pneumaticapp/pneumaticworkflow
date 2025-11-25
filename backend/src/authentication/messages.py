from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

MSG_AU_0001 = _('Access token not found for the user.')
MSG_AU_0002 = lambda email: format_lazy(
    _(
        'Your account has not been verified. '
        'A new verification link was sent to {email}.',
    ),
    email=email,
)
MSG_AU_0003 = _('Invalid login or password.')
# Translators: Microsoft account doesn't contain email
MSG_AU_0004 = _('Email is not listed in profile.')
MSG_AU_0005 = _('Error while retrieving Microsoft profile data.')
MSG_AU_0006 = _(
    'Phone number must be entered in the format: '
    '"+99999999999". Up to 15 digits allowed.',
)
# Translators: Guest authentication
MSG_AU_0007 = _('Authorization header contain spaces.')
MSG_AU_0008 = _('Token is invalid.')
MSG_AU_0009 = _('Token is expired.')
# Translators: Guest authentication
MSG_AU_0010 = _('Given token not valid for guest token type.')
# Translators: Guest authentication
MSG_AU_0011 = _('Token contained no recognizable user identification.')
# Translators: Change password from profile
MSG_AU_0012 = _('The current password is incorrect.')
MSG_AU_0013 = _('The new password and its confirmation don\'t match.')
# Translators: Google authorization
MSG_AU_0014 = _('Error while retrieving Google profile data.')
# Translators: Auth0 organization members request failed
MSG_AU_0015 = _(
    'The system is configured to use a different SSO provider. '
    'Please contact your administrator.',
)
MSG_AU_0016 = _(
    'This account uses SSO authentication. '
    'Please sign in through your organization\'s SSO portal.',
)
MSG_AU_0017 = _(
    'SSO authentication is currently unavailable. '
    'Please contact support.',
)
MSG_AU_0018 = lambda domain: format_lazy(
    _('No active SSO configuration found for the domain: "{domain}".'),
    domain=domain,
)
MSG_AU_0019 = _(
    'SSO settings are not properly configured. '
    'Please contact your administrator.',
)
MSG_AU_0020 = _(
    'This account does not use SSO authentication. '
    'Please contact support.',
)
