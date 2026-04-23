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
    'Rule "Sum equal" requires all fields to be of type "number".',
)
MSG_FS_0004 = _('Rule "Sum equal" value must be a number.')
MSG_FS_0005 = lambda rule, field: format_lazy(
    _('field "{field}" not found in rule "{rule}".'),
    field=field,
    rule=rule,
)
MSG_FS_0006 = _(
    'The task with the specified "api_name" was not found in the template',
)
