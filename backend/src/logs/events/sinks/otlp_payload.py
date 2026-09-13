"""OTLP/HTTP JSON body of a batch: no network, no clock, no state.

The transport that sends it lives in sinks/otlp.py.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from src.logs.events.enums import EventCategory
from src.logs.events.registry import resolve_event_type
from src.logs.events.schema import Event, format_ts, to_json

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
    EventCategory.DEBUG: SEVERITY_DEBUG,
}

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
SECOND_NS = 1000000000
MICROSECOND_NS = 1000


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
        file service, so the service comes from the record, and the
        version is known for one service only: the one this process
        is (service_name), the others carry none. """

    observed = str(observed_ns)
    groups = _group_records(records)
    resource_logs = [
        {
            'resource': {
                'attributes': _resource_attributes(
                    service_name=service,
                    service_version=(
                        service_version if service == service_name
                        else None
                    ),
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
) -> Dict[GroupKey, List[Tuple[str, Event]]]:
    groups: Dict[GroupKey, List[Tuple[str, Event]]] = {}
    for record_id, event in records:
        key = (
            event.service,
            event.account_id,
            event.category,
        )
        groups.setdefault(key, []).append((record_id, event))
    return groups


def _resource_attributes(
    *,
    service_name: str,
    service_version: Optional[str],
    environment: str,
    account_id: Any,
    category: str,
) -> List[Dict[str, Any]]:
    attributes = [_attr('service.name', service_name)]
    if service_version is not None:
        attributes.append(_attr('service.version', service_version))
    attributes += [
        _attr('deployment.environment', environment),
        _attr('account_id', account_id),
        _attr('event_category', category),
    ]
    return attributes


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
        safe side. """

    return resolve_event_type(event.type).pii


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
        them on the way out; a receiver that does not want them drops
        the prefix.

        A path is matched against the attribute keys directly and not
        split the way schema.split_pii_path splits it: _plain_values
        and _payload_values name their keys after the paths on
        purpose ("actor.email", "payload.filename"), so the lookup is
        the whole resolution. Renaming a key there without renaming
        the path here leaves a personal field outside the namespace,
        which is what test_registry pins. """

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
