from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

MSG_PM_0001 = lambda obj_type: format_lazy(
    _('"{obj_type}" is not a supported object type.'),
    obj_type=obj_type,
)
