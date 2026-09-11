from typing_extensions import Literal, get_args


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


class LogsBackend:

    """ Value of LOGS_BACKEND: where the collector sends the events.
        NONE switches the whole pipeline off, emit() writes nothing. """

    LOCAL = 'local'
    OTLP = 'otlp'
    ELASTICSEARCH = 'elasticsearch'
    NONE = 'none'

    LITERALS = Literal[
        LOCAL,
        OTLP,
        ELASTICSEARCH,
        NONE,
    ]
    VALUES = set(get_args(LITERALS))


DEFAULT_CONSUMER_BATCH_SIZE = 1000
DEFAULT_CONSUMER_IDLE_MS = 60000
DEFAULT_CONSUMER_INTERVAL_SECONDS = 5
