from django.utils.translation import gettext_lazy as _
from django.utils.text import format_lazy


# Translators: Call analytics need specify any user id
MSG_AS_0001 = _('You must specify "user_id" or "anonymous_id"')
MSG_AS_0002 = lambda metric: format_lazy(
    _('Missing handler for metric "{metric}"'),
    metric=metric
)
MSG_AS_0003 = _('The user with the specified credentials was not found.')
MSG_AS_0004 = lambda error: format_lazy(
    _('Data format error. Key error: {error}'),
    error=error
)
