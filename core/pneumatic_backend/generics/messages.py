from django.utils.translation import gettext_lazy as _
from django.utils.text import format_lazy

# Translators: Invalid choice for any list query parameter
MSG_GE_0001 = lambda choice: format_lazy(
    _('\'{choice}\' is an invalid value for the filter'),
    choice=choice,
)
# Translators: AccountPrimaryKeyRelatedField incorrect init
MSG_GE_0002 = _('Account or queryset not provided')
MSG_GE_0003 = _('Value should be a list of integers.')
MSG_GE_0004 = _(
    'The "raise_validation_error" method should be used only '
    'after calling the "is_valid" method'
)
MSG_GE_0005 = _(
    'You need to set a "Meta.fields" value before using '
    'AdditionalValidationMixin'
)
MSG_GE_0006 = _('Payment method required.')
MSG_GE_0007 = _('Numeric type expected.')

MSG_GE_0008 = _('Jan')
MSG_GE_0009 = _('Feb')
MSG_GE_0010 = _('Mar')
MSG_GE_0011 = _('Apr')
MSG_GE_0012 = _('May')
MSG_GE_0013 = _('Jun')
MSG_GE_0014 = _('Jul')
MSG_GE_0015 = _('Aug')
MSG_GE_0016 = _('Sep')
MSG_GE_0017 = _('Oct')
MSG_GE_0018 = _('Nov')
MSG_GE_0019 = _('Dec')
