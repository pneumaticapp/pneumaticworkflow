

class AccountEventType:

    API = 'api'
    DATABUS = 'databus'
    WEBHOOK = 'webhook'

    CHOICES = (
        (API, API),
        (DATABUS, DATABUS),
        (WEBHOOK, WEBHOOK),
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


class RequestDirection:

    RECEIVED = 'received'
    SENT = 'sent'

    CHOICES = (
        (RECEIVED, RECEIVED),
        (SENT, SENT),
    )
