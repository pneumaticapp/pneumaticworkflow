from django.utils.text import format_lazy
from django.utils.translation import ugettext_lazy as _

MSG_DS_0001 = _('A dataset with this name already exists.')
MSG_DS_0002 = lambda value: format_lazy(
    _('A dataset item with value "{value}" already exists.'),
    value=value,
)
