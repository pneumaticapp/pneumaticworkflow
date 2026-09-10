import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

from src.logs.events.enums import EventCategory
from src.logs.events.exceptions import (
    SinkPermanentError,
    SinkTemporaryError,
)
from src.logs.events.registry import ACTOR_PII, EventRegistry
from src.logs.events.reporting import report_error
from src.logs.events.schema import Event, format_ts, to_json
from src.logs.events.sinks.base import BaseSink
from src.utils.logging import SentryLogLevel

logger = logging.getLogger('pneumatic.events')

SCOPE_NAME = 'pneumatic.events'
SCOPE_VERSION = '1'

PAYLOAD_PREFIX = 'payload.'
PII_PREFIX = 'pii.'
EXTRA_ATTRIBUTE = 'payload.extra'
# Loki keeps up to 128 structured metadata entries per line; half of
# that leaves room for the labels the collector adds on its way.
MAX_ATTRIBUTES = 60
# One resourceLogs per (service, account_id, category).
GroupKey = Tuple[str, Any, str]

SEVERITY_INFO = (9, 'INFO')
SEVERITY_DEBUG = (5, 'DEBUG')
CATEGORY_SEVERITY = {
    EventCategory.AUDIT: SEVERITY_INFO,
    EventCategory.ACTIVITY: SEVERITY_INFO,
    EventCategory.HTTP: SEVERITY_DEBUG,
    EventCategory.DEBUG: SEVERITY_DEBUG,
}

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
SECOND_NS = 1000000000
MICROSECOND_NS = 1000

LOGS_PATH = '/v1/logs'
JSON_HEADERS = {'Content-Type': 'application/json'}
# Connect and read timeouts: a slow collector must not hold the tick.
DEFAULT_TIMEOUT = (3.05, 10.0)
RETRY_AFTER_HEADER = 'Retry-After'
# A longer pause than the whole retry sequence is not worth waiting.
MAX_RETRY_AFTER = 10
# The batch itself is wrong: a malformed body, a body too large, a
# wrong content type, an unprocessable record. Everything else, 401,
# 403, 404 and 405 included, is a misconfiguration of the endpoint or
# of the proxy in front of it and gets fixed without our help, so the
# records wait in the stream instead of going to the dead letter.
PERMANENT_STATUSES = (400, 413, 415, 422)
BODY_LIMIT = 500
PARTIAL_SUCCESS_KEY = 'partialSuccess'
REJECTED_RECORDS_KEY = 'rejectedLogRecords'


class OTLPSink(BaseSink):

    """ OTLP/HTTP JSON logs exporter: one POST per batch.

        The consumer sees only SinkTemporaryError (keep the batch
        pending and try again) or SinkPermanentError (dead letter);
        every transport detail stays in this class. """

    name = 'otlp'

    def __init__(
        self,
        endpoint: str,
        timeout: Tuple[float, float] = DEFAULT_TIMEOUT,
        session: Optional[requests.Session] = None,
    ):
        self.url = endpoint.rstrip('/') + LOGS_PATH
        self.timeout = timeout
        # One session per sink, and one sink per endpoint per process
        # (get_sink): a session rebuilt every tick would open a new
        # connection for every batch it sends.
        self.session = session or requests.Session()

    def _send(self, records: List[Tuple[str, Event]]) -> None:
        payload = build_otlp_payload(
            records,
            service_name=settings.LOGS_SERVICE_NAME,
            service_version=settings.LOGS_SERVICE_VERSION,
            environment=settings.CONFIGURATION_CURRENT,
            observed_ns=time.time_ns(),
        )
        response = self.session.post(
            self.url,
            data=json.dumps(payload, cls=DjangoJSONEncoder).encode(),
            headers=JSON_HEADERS,
            timeout=self.timeout,
        )
        response.raise_for_status()
        self._report_rejected(response, len(records))

    def _handle_error(
        self,
        exc: Exception,
        records: List[Tuple[str, Event]],
    ) -> None:

        """ Only an answer that condemns this very batch is permanent
            (PERMANENT_STATUSES); network trouble and every other
            status are worth another try. An error that is not about
            the transport at all comes from building the batch: the
            records themselves are the problem, and sending them again
            would block the stream on the same batch forever, so they
            go to the dead letter for inspection. """

        if isinstance(exc, (requests.ConnectionError, requests.Timeout)):
            raise SinkTemporaryError(f'{self.url}: {exc!r}') from exc
        if not isinstance(exc, requests.RequestException):
            raise self._build_error(exc, len(records)) from exc
        status = getattr(getattr(exc, 'response', None), 'status_code', None)
        if status is None:
            # Unknown transport failure: the batch stays pending.
            raise SinkTemporaryError(f'{self.url}: {exc!r}') from exc
        if status in PERMANENT_STATUSES:
            raise self._permanent_error(
                exc.response, status, len(records),
            ) from exc
        raise self._temporary_error(exc.response, status) from exc

    def _temporary_error(self, response, status: int) -> SinkTemporaryError:
        error = SinkTemporaryError(f'{self.url} answered {status}')
        # The consumer reads this through getattr: the exception class
        # is shared with the other sinks and carries no fields.
        error.retry_after = self._retry_after(response)
        return error

    def _permanent_error(
        self,
        response,
        status: int,
        count: int,
    ) -> SinkPermanentError:
        body = self._body_prefix(response)
        message = f'{self.url} answered {status} for {count} records'
        logger.error('%s: %s', message, body)
        report_error(
            message='OTLP endpoint rejected the batch',
            data={
                'url': self.url,
                'status': status,
                'records': count,
                'body': body,
            },
        )
        return SinkPermanentError(f'{message}: {body}')

    def _build_error(self, exc: Exception, count: int) -> SinkPermanentError:
        message = f'OTLP batch cannot be built ({count} records): {exc!r}'
        logger.error(message)
        report_error(
            message='OTLP batch cannot be built',
            data={'records': count, 'error': repr(exc)},
        )
        return SinkPermanentError(message)

    def _report_rejected(self, response, count: int) -> None:

        """ A 2xx with partialSuccess means the collector took the
            batch but dropped some records. Sending them again would
            change nothing, so the batch counts as delivered. The
            report is throttled: a collector that drops a record of
            every batch would otherwise cost a message per tick. """

        rejected = self._rejected_records(response)
        if not rejected:
            return
        logger.warning(
            'OTLP endpoint dropped records of a batch: %s of %s',
            rejected, count,
        )
        report_error(
            message='OTLP endpoint dropped records of a batch',
            data={
                'url': self.url,
                'rejected': rejected,
                'records': count,
            },
            level=SentryLogLevel.WARNING,
        )

    @staticmethod
    def _retry_after(response) -> Optional[float]:

        """ Honour the header only when it asks for a short pause:
            a longer one belongs to the next tick, not to this one.
            The HTTP date form is ignored on purpose. """

        try:
            delay = float(response.headers.get(RETRY_AFTER_HEADER))
        except (AttributeError, TypeError, ValueError):
            return None
        if 0 < delay <= MAX_RETRY_AFTER:
            return delay
        return None

    @staticmethod
    def _body_prefix(response) -> str:

        """ First bytes of the answer: enough to tell a schema error
            from a wrong path, short enough for Sentry. """

        try:
            return response.content[:BODY_LIMIT].decode(
                'utf-8', errors='replace',
            )
        except (AttributeError, TypeError, ValueError):
            return ''

    @staticmethod
    def _rejected_records(response) -> int:
        try:
            body = response.json()
        except ValueError:
            return 0
        if not isinstance(body, dict):
            return 0
        partial = body.get(PARTIAL_SUCCESS_KEY) or {}
        try:
            return int(partial.get(REJECTED_RECORDS_KEY) or 0)
        except (AttributeError, TypeError, ValueError):
            return 0


_sinks: Dict[str, OTLPSink] = {}


def get_sink() -> OTLPSink:

    """ Shared sink of the process: the keep alive connection of its
        session is reused between ticks. A settings change gives a new
        sink, exactly as get_stream() does for the stream. """

    endpoint = settings.LOGS_OTLP_ENDPOINT
    sink = _sinks.get(endpoint)
    if sink is None:
        sink = OTLPSink(endpoint)
        _sinks[endpoint] = sink
    return sink


def build_otlp_payload(
    records: List[Tuple[str, Event]],
    *,
    service_name: str,
    service_version: str,
    environment: str,
    observed_ns: int,
) -> Dict[str, Any]:

    """ Build an OTLP/HTTP JSON logs request out of stream records.

        No network and no clock: the moment of reading comes in as
        observed_ns. The only thing read from the outside is the
        registry, and only for the personal data paths (_pii_paths).

        Records are grouped by (service, account_id, category) into
        separate resourceLogs: Loki takes index labels from resource
        attributes only, record attributes become structured
        metadata and cannot be labels. The stream is shared with the
        file service, so the service comes from the record; a record
        without one is a backend record written before the field
        existed and takes service_name. """

    observed = str(observed_ns)
    groups = _group_records(records, default_service=service_name)
    resource_logs = [
        {
            'resource': {
                'attributes': _resource_attributes(
                    service_name=service,
                    service_version=service_version,
                    environment=environment,
                    account_id=account_id,
                    category=category,
                ),
            },
            'scopeLogs': [{
                'scope': {'name': SCOPE_NAME, 'version': SCOPE_VERSION},
                'logRecords': [
                    _log_record(record_id, event, observed)
                    for record_id, event in group
                ],
            }],
        }
        for (service, account_id, category), group in groups.items()
    ]
    return {'resourceLogs': resource_logs}


def _group_records(
    records: List[Tuple[str, Event]],
    default_service: str,
) -> Dict[GroupKey, List[Tuple[str, Event]]]:
    groups: Dict[GroupKey, List[Tuple[str, Event]]] = {}
    for record_id, event in records:
        key = (
            event.service or default_service,
            event.account_id,
            event.category,
        )
        groups.setdefault(key, []).append((record_id, event))
    return groups


def _resource_attributes(
    *,
    service_name: str,
    service_version: str,
    environment: str,
    account_id: Any,
    category: str,
) -> List[Dict[str, Any]]:
    return [
        _attr('service.name', service_name),
        _attr('service.version', service_version),
        _attr('deployment.environment', environment),
        _attr('account_id', account_id),
        _attr('event_category', category),
    ]


def _log_record(
    record_id: str,
    event: Event,
    observed: str,
) -> Dict[str, Any]:
    severity_number, severity_text = CATEGORY_SEVERITY.get(
        event.category, SEVERITY_INFO,
    )
    return {
        'timeUnixNano': _to_unix_nano(event.ts),
        'observedTimeUnixNano': observed,
        'severityNumber': severity_number,
        'severityText': severity_text,
        'body': {'stringValue': _body(event)},
        'attributes': _record_attributes(record_id, event),
    }


def _body(event: Event) -> str:

    """ Short line without PII. Nothing strips the record on the
        way out, so the body is the one field every reader of the
        journal sees whether or not it wants personal data. """

    if event.object is None:
        return event.type
    if event.object.id is None:
        return f'{event.type} {event.object.type}'
    return f'{event.type} {event.object.type}:{event.object.id}'


def _record_attributes(
    record_id: str,
    event: Event,
) -> List[Dict[str, Any]]:
    plain = _plain_values(record_id, event)
    payload = _payload_values(event.payload)
    pii = _extract_pii(_pii_paths(event), plain, payload)
    payload, extra = _fit_limit(len(plain) + len(pii), payload)

    attributes = [_attr(key, value) for key, value in plain.items()]
    attributes += [_attr(key, value) for key, value in payload.items()]
    if extra:
        attributes.append(_attr(EXTRA_ATTRIBUTE, extra))
    attributes += [_attr(key, value) for key, value in pii.items()]
    return attributes


def _pii_paths(event: Event) -> Tuple[str, ...]:

    """ The personal fields of the type as the registry of this
        process declares them, not as the record of the stream claims.

        Whoever can write into the stream could otherwise hand in
        an event with a filled e-mail and an empty pii list, and it
        would arrive at the receiver as a plain attribute, outside
        the namespace that says "this is personal data". For a type
        nobody declared the registry answers ACTOR_PII, which is the
        safe side.

        ACTOR_PII is unioned in for every type, exactly as the emitter
        does in _present_pii. Without it the two ends disagree: a type
        declaring ANONYMOUS_PII (user.login_failed) would move the ip
        and the user agent but leave an actor e-mail as a plain
        attribute whenever one is present. """

    declared = EventRegistry.resolve(event.type).pii
    return declared + tuple(
        path for path in ACTOR_PII if path not in declared
    )


def _plain_values(record_id: str, event: Event) -> Dict[str, Any]:

    """ Flat attributes of the event itself. Empty values are
        dropped: an absent attribute is cheaper than an empty one
        both in Loki and in Elasticsearch. The account and the
        category are resource attributes already (index labels),
        repeating them here only gives Loki a duplicate to rename. """

    values: Dict[str, Any] = {
        'event.id': record_id,
        'event.type': event.type,
    }
    if event.actor is not None:
        values['actor.type'] = event.actor.type
        values['actor.id'] = event.actor.id
        values['actor.email'] = event.actor.email
    if event.object is not None:
        values['object.type'] = event.object.type
        values['object.id'] = event.object.id
    values['workflow_id'] = event.workflow_id
    values['task_id'] = event.task_id
    values['ip'] = event.ip
    values['user_agent'] = event.user_agent
    values['request_id'] = event.request_id
    return {
        key: value for key, value in values.items() if value is not None
    }


def _payload_values(payload: Any) -> Dict[str, Any]:

    """ One level of unwrapping: payload.<key>. Nested containers
        stay as they are, _attr turns them into a JSON string. A
        payload that is not a mapping (a record written by hand into
        the stream) is kept whole under one key rather than failing
        the batch. """

    if not payload:
        return {}
    if not isinstance(payload, dict):
        return {PAYLOAD_PREFIX + 'value': payload}
    return {
        PAYLOAD_PREFIX + str(key): value
        for key, value in payload.items()
        if value is not None
    }


def _extract_pii(
    paths: Tuple[str, ...],
    plain: Dict[str, Any],
    payload: Dict[str, Any],
) -> Dict[str, Any]:

    """ Move the declared personal fields into the pii.* namespace
        and remove them from their original place, so that one prefix
        names every personal attribute of a record. Nothing deletes
        them on the way out (decision 2 in docs/logging-design.md);
        a receiver that does not want them drops the prefix. """

    pii: Dict[str, Any] = {}
    for path in paths:
        source = plain if path in plain else payload
        if path in source:
            pii[PII_PREFIX + path] = source.pop(path)
    return pii


def _fit_limit(
    reserved: int,
    payload: Dict[str, Any],
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:

    """ Keep at most MAX_ATTRIBUTES attributes per record: the tail of
        the payload collapses into a single payload.extra JSON string.
        Only non PII keys get here, the pii.* ones are already out. """

    if reserved + len(payload) <= MAX_ATTRIBUTES:
        return payload, None
    allowed = max(MAX_ATTRIBUTES - reserved - 1, 0)
    keys = list(payload)
    kept = {key: payload[key] for key in keys[:allowed]}
    extra = {
        key[len(PAYLOAD_PREFIX):]: payload[key] for key in keys[allowed:]
    }
    return kept, extra


def _attr(key: str, value: Any) -> Dict[str, Any]:

    """ OTLP attribute. Everything but booleans goes as stringValue:
        an id sent as a number in one place and as a string in another
        gives Loki labels of different types. """

    if isinstance(value, bool):
        return {'key': key, 'value': {'boolValue': value}}
    return {'key': key, 'value': {'stringValue': _to_string(value)}}


def _to_string(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return format_ts(value)
    if isinstance(value, (dict, list, tuple)):
        return to_json(value)
    return str(value)


def _to_unix_nano(value: datetime) -> str:

    """ Nanoseconds since epoch as a string, as OTLP JSON wants 64 bit
        numbers. Built out of the timedelta, not out of timestamp():
        a float would lose the microseconds of a 2026 date. """

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    delta = value.astimezone(timezone.utc) - EPOCH
    seconds = delta.days * 86400 + delta.seconds
    return str(seconds * SECOND_NS + delta.microseconds * MICROSECOND_NS)
