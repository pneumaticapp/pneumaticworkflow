from django.utils.text import format_lazy
from django.utils.translation import ugettext_lazy as _

MSG_FS_0001 = _(
    'Cannot delete a fieldset template that is used in templates.',
)
MSG_FS_0002 = lambda value: format_lazy(
    _('The sum of the fields in this field set must equal "{value}".'),
    value=value,
)
MSG_FS_0003 = _(
    'Rule "Sum equal" requires all fieldset fields to be of type "number".',
)
MSG_FS_0004 = _('Rule "Sum equal" value must be a number.')
