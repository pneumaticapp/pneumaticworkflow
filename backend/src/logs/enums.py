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
    """Value of LOGS_BACKEND: where the collector sends the events.
    The backend itself always delivers OTLP to the collector at
    LOGS_OTLP_ENDPOINT. An unset value disables the pipeline; an
    invalid value refuses to start the web and celery processes."""

    OTLP = 'otlp'
    ELASTICSEARCH = 'elasticsearch'

    LITERALS = Literal[
        OTLP,
        ELASTICSEARCH,
    ]
    VALUES = set(get_args(LITERALS))
