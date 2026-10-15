import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

from src.logs.events.entities import Entries, Event, format_ts
from src.logs.events.exceptions import SinkPermanentError, SinkTemporaryError
from src.logs.events.schema import to_json, without_url_secrets
from src.utils.logging import SentryLogLevel, capture_sentry_message_throttled

logger = logging.getLogger('pneumatic.events')
LOGS_PATH = '/v1/logs'
JSON_HEADERS = {'Content-Type': 'application/json'}
DEFAULT_TIMEOUT = (3.05, 10.0)
RETRY_AFTER_HEADER = 'Retry-After'
MAX_RETRY_AFTER = 10
PERMANENT_STATUSES = (400, 413, 415, 422)
BODY_LIMIT = 500
PARTIAL_SUCCESS_KEY = 'partialSuccess'
REJECTED_RECORDS_KEY = 'rejectedLogRecords'
SCOPE_NAME = 'pneumatic.events'
SCOPE_VERSION = '1'
PAYLOAD_PREFIX = 'payload.'
EXTRA_ATTRIBUTE = 'payload.extra'
MAX_ATTRIBUTES = 60
GroupKey = Tuple[str, Any, str]
SEVERITY_NUMBER, SEVERITY_TEXT = (9, 'INFO')
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
DAY_SECONDS = 86400
SECOND_NS = 1000000000
MICROSECOND_NS = 1000


class OTLPSink:
    """OTLP/HTTP JSON logs exporter: one POST per batch.

    A record is a (stream id, event) pair: the consumer acks by
    stream id, the sink sends the event. The consumer sees only
    SinkTemporaryError (keep the batch pending and try again) or
    SinkPermanentError (dead letter); every transport detail stays
    in this class. The endpoint is validated once at startup, by
    LogsConfig.ready."""

    def __init__(
        self,
        endpoint: str,
        timeout: Tuple[float, float] = DEFAULT_TIMEOUT,
        session: Optional[requests.Session] = None,
    ):
        self.url = endpoint.rstrip('/') + LOGS_PATH
        self.display_url = without_url_secrets(self.url)
        self.timeout = timeout
        self.session = session or requests.Session()

    def send(self, records: Entries):
        if not records:
            return
        try:
            payload = build_otlp_payload(
                records=records,
                service_name=settings.LOGS_SERVICE_NAME,
                service_version=settings.LOGS_SERVICE_VERSION,
                environment=settings.CONFIGURATION_CURRENT,
                observed_ns=time.time_ns(),
            )
            response = self.session.post(
                url=self.url,
                data=json.dumps(payload, cls=DjangoJSONEncoder).encode(),
                headers=JSON_HEADERS,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            self._handle_error(exc=exc, records=records)
        try:
            body = response.json()
        except ValueError:
            return
        if not isinstance(body, dict):
            return
        partial = body.get(PARTIAL_SUCCESS_KEY) or {}
        try:
            rejected = int(partial.get(REJECTED_RECORDS_KEY) or 0)
        except (AttributeError, TypeError, ValueError):
            return
        if rejected:
            count = len(records)
            logger.warning(
                'OTLP endpoint dropped records of a batch: %s of %s',
                rejected,
                count,
            )
            capture_sentry_message_throttled(
                message='OTLP endpoint dropped records of a batch',
                data={
                    'url': self.display_url,
                    'rejected': rejected,
                    'records': count,
                },
                level=SentryLogLevel.WARNING,
            )

    def _handle_error(self, exc: Exception, records: Entries):
        """Classify failures without putting endpoint credentials in errors.
        Always raises: a returned error would have the consumer ack
        records nobody received."""
        count = len(records)
        transport_message = f'{self.display_url}: {type(exc).__name__}'
        if isinstance(exc, (requests.ConnectionError, requests.Timeout)):
            raise SinkTemporaryError(transport_message) from exc
        if not isinstance(exc, requests.RequestException):
            message = f'OTLP batch cannot be built ({count} records): {exc!r}'
            logger.error(message)
            capture_sentry_message_throttled(
                message='OTLP batch cannot be built',
                data={'records': count, 'error': repr(exc)},
            )
            raise SinkPermanentError(message) from exc
        response = exc.response
        if response is None:
            raise SinkTemporaryError(transport_message) from exc
        status = response.status_code
        if status in PERMANENT_STATUSES:
            message = (
                f'{self.display_url} answered {status} for {count} records'
            )
            try:
                body = response.content[:BODY_LIMIT].decode(
                    'utf-8',
                    errors='replace',
                )
            except (AttributeError, TypeError, ValueError):
                body = ''
            logger.warning('%s: %s', message, body)
            capture_sentry_message_throttled(
                message='OTLP endpoint rejected the batch',
                data={
                    'url': self.display_url,
                    'status': status,
                    'records': count,
                },
            )
            raise SinkPermanentError(message) from exc
        retry_after = None
        try:
            delay = float(response.headers.get(RETRY_AFTER_HEADER))
        except (AttributeError, TypeError, ValueError):
            delay = None
        if delay is not None and 0 < delay <= MAX_RETRY_AFTER:
            retry_after = delay
        raise SinkTemporaryError(
            f'{self.display_url} answered {status}',
            retry_after=retry_after,
        ) from exc


_sinks: Dict[str, OTLPSink] = {}


def get_sink() -> OTLPSink:
    """Shared sink of the process: the keep alive connection of its
    session is reused between ticks. A settings change gives a new
    sink, exactly as get_stream() does for the stream."""
    endpoint = settings.LOGS_OTLP_ENDPOINT
    sink = _sinks.get(endpoint)
    if sink is None:
        sink = OTLPSink(endpoint=endpoint)
        _sinks[endpoint] = sink
    return sink


def build_otlp_payload(
    records: Entries,
    *,
    service_name: str,
    service_version: Optional[str],
    environment: str,
    observed_ns: int,
) -> Dict[str, Any]:
    """Group by service, tenant and category, which are resource labels."""
    groups: Dict[GroupKey, Entries] = {}
    for record_id, event in records:
        key = (event.service, event.account_id, event.category)
        groups.setdefault(key, []).append((record_id, event))
    resource_logs = []
    for (service, account_id, category), group in groups.items():
        attributes = [_get_attribute(key='service.name', value=service)]
        if service_version is not None and service == service_name:
            attributes.append(
                _get_attribute(key='service.version', value=service_version),
            )
        attributes.extend(
            [
                _get_attribute(
                    key='deployment.environment',
                    value=environment,
                ),
                _get_attribute(key='account_id', value=account_id),
                _get_attribute(key='event_category', value=category),
            ],
        )
        log_records = []
        for record_id, event in group:
            # Integer arithmetic: a float timestamp loses microseconds.
            ts = event.ts
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            delta = ts.astimezone(timezone.utc) - EPOCH
            seconds = delta.days * DAY_SECONDS + delta.seconds
            unix_nano = (
                seconds * SECOND_NS + delta.microseconds * MICROSECOND_NS
            )
            body = event.type
            if event.object is not None:
                body += f' {event.object.type}'
                if event.object.id is not None:
                    body += f':{event.object.id}'
                if event.object.name:
                    body += f' {event.object.name}'
            log_records.append(
                {
                    'timeUnixNano': str(unix_nano),
                    'observedTimeUnixNano': str(observed_ns),
                    'severityNumber': SEVERITY_NUMBER,
                    'severityText': SEVERITY_TEXT,
                    'body': {'stringValue': body},
                    'attributes': _get_record_attributes(
                        record_id=record_id,
                        event=event,
                    ),
                },
            )
        resource_logs.append(
            {
                'resource': {'attributes': attributes},
                'scopeLogs': [
                    {
                        'scope': {
                            'name': SCOPE_NAME,
                            'version': SCOPE_VERSION,
                        },
                        'logRecords': log_records,
                    },
                ],
            },
        )
    return {'resourceLogs': resource_logs}


def _get_record_attributes(
    record_id: str,
    event: Event,
) -> List[Dict[str, Any]]:
    """Flatten the record and preserve metadata beyond the attribute cap."""
    values: Dict[str, Any] = {'event.id': record_id, 'event.type': event.type}
    if event.actor is not None:
        values['actor.id'] = event.actor.id
        values['actor.email'] = event.actor.email
        values['actor.user_type'] = event.actor.user_type
    values['auth_type'] = event.auth_type
    if event.object is not None:
        values['object.type'] = event.object.type
        values['object.id'] = event.object.id
        values['object.name'] = event.object.name
    values.update(
        {
            'account_name': event.account_name,
            'workflow_id': event.workflow_id,
            'task_id': event.task_id,
            'ip': event.ip,
            'user_agent': event.user_agent,
            'request_id': event.request_id,
        },
    )
    values = {key: value for key, value in values.items() if value is not None}
    payload = {}
    if isinstance(event.payload, dict):
        payload = {
            PAYLOAD_PREFIX + str(key): value
            for key, value in event.payload.items()
            if value is not None
        }
    elif event.payload:
        payload = {PAYLOAD_PREFIX + 'value': event.payload}
    extra = {}
    if len(values) + len(payload) > MAX_ATTRIBUTES:
        allowed = max(MAX_ATTRIBUTES - len(values) - 1, 0)
        if EXTRA_ATTRIBUTE in payload:
            extra['extra'] = payload.pop(EXTRA_ATTRIBUTE)
        keys = list(payload)
        extra.update(
            {
                key[len(PAYLOAD_PREFIX):]: payload[key]
                for key in keys[allowed:]
            },
        )
        payload = {key: payload[key] for key in keys[:allowed]}
    values.update(payload)
    if extra:
        values[EXTRA_ATTRIBUTE] = extra
    return [
        _get_attribute(key=key, value=value) for key, value in values.items()
    ]


def _get_attribute(key: str, value: Any) -> Dict[str, Any]:
    """Keep booleans typed and serialize other values as OTLP strings."""
    if isinstance(value, bool):
        return {'key': key, 'value': {'boolValue': value}}
    if isinstance(value, datetime):
        value = format_ts(value)
    elif isinstance(value, (dict, list, tuple)):
        value = to_json(value)
    elif not isinstance(value, str):
        value = str(value)
    return {'key': key, 'value': {'stringValue': value}}
