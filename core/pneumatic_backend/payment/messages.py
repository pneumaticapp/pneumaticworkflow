from django.utils.translation import gettext_lazy as _
from django.utils.text import format_lazy


MSG_BL_0001 = _('Token is expired.')
MSG_BL_0002 = _('Products list cannot be empty.')
MSG_BL_0003 = lambda code: format_lazy(
    _('Price with code(s) {code} not found.'),
    code=(
        f'"{code}"' if type(code) == str
        else ', '.join(f'"{c}"' for c in code)
    )
)
MSG_BL_0004 = _('Please, contact our support for a downgrade options.')
MSG_BL_0005 = _('Subscription not exist.')
MSG_BL_0006 = _('Multiple subscriptions not allowed.')
MSG_BL_0007 = _('The request data does not change the subscription state.')
MSG_BL_0008 = _(
    'Current payment method is unavailable. '
    'Specify a new payment method to complete the action.'
)
MSG_BL_0009 = _(
    'Payment failed. Check your payment method and balance or contact support.'
)
MSG_BL_0010 = _(
    'You can only use your subscription\'s currency to make purchases.',
)
MSG_BL_0011 = lambda quantity, product: format_lazy(
    _(
        'You cannot purchase more than {quantity} '
        'unit(s) of the "{product}" subscription.'
    ),
    quantity=quantity,
    product=product
)
MSG_BL_0012 = lambda quantity, product: format_lazy(
    _(
        'You cannot purchase less than {quantity} '
        'unit(s) of the "{product}" subscription.'
    ),
    quantity=quantity,
    product=product
)
MSG_BL_0013 = lambda quantity, product: format_lazy(
    _('You cannot purchase more than {quantity} unit(s) of the "{product}".'),
    quantity=quantity,
    product=product
)
MSG_BL_0014 = lambda quantity, product: format_lazy(
    _('You cannot purchase less than {quantity} unit(s) of the "{product}".'),
    quantity=quantity,
    product=product
)
MSG_BL_0015 = _('Unsupported subscription plan.')
MSG_BL_0016 = _('Purchase at the archive price is disallowed.')
MSG_BL_0017 = _('No account found for this subscription.')
MSG_BL_0018 = _('Billing is disabled, contact support to change the plan.')
MSG_BL_0019 = _('Webhook account not found.')
MSG_BL_0020 = _('Webhook account owner not found.')
MSG_BL_0021 = _('Payments API is disabled in this project.')
MSG_BL_0022 = _(
    'Downgrade is not available while there is an active subscription.'
)
MSG_BL_0023 = _('Account not found.')
MSG_BL_0024 = _('Master account not found for tenant.')
