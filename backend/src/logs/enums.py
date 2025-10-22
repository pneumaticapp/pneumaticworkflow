from typing_extensions import Literal


class AccountEventType:

    API = 'api'
    AUTH = 'auth'
    DATABUS = 'databus'
    WEBHOOK = 'webhook'
    SYSTEM = 'system'

    CHOICES = (
        (API, API),
        (AUTH, AUTH),
        (DATABUS, DATABUS),
        (WEBHOOK, WEBHOOK),
        (SYSTEM, SYSTEM),
    )


class AccountEventStatus:

    PENDING = 'pending'
    SUCCESS = 'success'
    FAILED = 'failed'

    CHOICES = (
        (PENDING, PENDING),
        (SUCCESS, SUCCESS),
        (FAILED, FAILED),
    )

    LITERALS = Literal[PENDING, SUCCESS, FAILED]


class RequestDirection:

    RECEIVED = 'received'
    SENT = 'sent'

    CHOICES = (
        (RECEIVED, RECEIVED),
        (SENT, SENT),
    )
