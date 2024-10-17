from typing_extensions import Literal


class PriceType:

    ONE_TIME = 'one_time'
    RECURRING = 'recurring'

    CHOICES = (
        (ONE_TIME, ONE_TIME),
        (RECURRING, RECURRING),
    )


class BillingPeriod:

    DAILY = 'day'
    WEEKLY = 'week'
    MONTHLY = 'month'
    YEARLY = 'year'

    CHOICES = (
        (DAILY, DAILY),
        (WEEKLY, WEEKLY),
        (MONTHLY, MONTHLY),
        (YEARLY, YEARLY),
    )

    LITERALS = Literal[
        DAILY,
        WEEKLY,
        MONTHLY,
        YEARLY,
    ]


class PriceStatus:

    ACTIVE = 'active'
    ARCHIVED = 'archived'
    INACTIVE = 'inactive'

    CHOICES = (
        (ACTIVE, ACTIVE),
        (ARCHIVED, ARCHIVED),
        (INACTIVE, INACTIVE),
    )

    LITERALS = Literal[
        ACTIVE,
        ARCHIVED,
        INACTIVE,
    ]
