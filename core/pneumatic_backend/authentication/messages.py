from django.utils.translation import gettext_lazy as _
from django.utils.text import format_lazy


MSG_AU_0001 = _('Access token not found for the user.')
MSG_AU_0002 = lambda email: format_lazy(
    _(
        'Your account has not been verified. '
        'A new verification link was sent to {email}.'
    ),
    email=email
)
MSG_AU_0003 = _('Invalid login or password.')
# Translators: Microsoft account doesn't contain email
MSG_AU_0004 = _('Email is not listed in profile.')
MSG_AU_0005 = _('Error while retrieving Microsoft profile data.')
MSG_AU_0006 = _(
    'Phone number must be entered in the format: '
    '"+99999999999". Up to 15 digits allowed.'
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
