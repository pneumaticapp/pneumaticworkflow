import json
import os
from datetime import timedelta, timezone

import pytest

from src.logs.events import registry as registry_module
from src.logs.events.enums import EventCategory
from src.logs.events.registry import (
    ACTOR_PII,
)
from src.logs.events.schema import Actor, EventObject
from src.logs.events.sinks.otlp_payload import (
    MAX_ATTRIBUTES,
    _fit_limit,
    _payload_values,
)
from src.logs.events.tests.fakes import (
    ENVIRONMENT,
    EVENT_TS,
    EVENT_TS_NANO,
    OBSERVED_NS,
    SERVICE_NAME,
    SERVICE_VERSION,
    build_sample_payload,
    make_event,
    otlp_attributes,
    otlp_first_record,
    otlp_resource_attributes,
    scrub_times,
)
from src.utils.logging import SentryLogLevel


def test_build__two_accounts__two_resource_logs():

    """ Loki takes index labels from resource attributes only, so a
        batch is split by (account_id, category) before it is sent. """

    # arrange
    records = [
        ('1-0', make_event(account_id=42)),
        ('2-0', make_event(account_id=77)),
        ('3-0', make_event(account_id=42)),
    ]

    # act
    payload = build_sample_payload(records)

    # assert
    resource_logs = payload['resourceLogs']
    assert len(resource_logs) == 2
    first, second = resource_logs
    assert otlp_resource_attributes(first)['account_id'] == {
        'stringValue': '42',
    }
    assert otlp_resource_attributes(second)['account_id'] == {
        'stringValue': '77',
    }
    assert len(first['scopeLogs'][0]['logRecords']) == 2
    assert len(second['scopeLogs'][0]['logRecords']) == 1


def test_build__one_account_two_categories__two_resource_logs():

    # arrange
    records = [
        ('1-0', make_event(category=EventCategory.AUDIT)),
        ('2-0', make_event(category=EventCategory.ACTIVITY)),
    ]

    # act
    payload = build_sample_payload(records)

    # assert
    resource_logs = payload['resourceLogs']
    assert len(resource_logs) == 2
    assert otlp_resource_attributes(resource_logs[0])['event_category'] == {
        'stringValue': EventCategory.AUDIT,
    }
    assert otlp_resource_attributes(resource_logs[1])['event_category'] == {
        'stringValue': EventCategory.ACTIVITY,
    }


def test_build__two_services__two_resource_logs():

    """ The stream is shared with the file service: its records
        must not leave under the service name of the backend. """

    # arrange
    records = [
        ('1-0', make_event(service='pneumatic-backend')),
        ('2-0', make_event(service='pneumatic-file-service')),
        ('3-0', make_event(service='pneumatic-backend')),
    ]

    # act
    payload = build_sample_payload(records)

    # assert
    resource_logs = payload['resourceLogs']
    assert len(resource_logs) == 2
    first, second = resource_logs
    assert otlp_resource_attributes(first)['service.name'] == {
        'stringValue': 'pneumatic-backend',
    }
    assert otlp_resource_attributes(second)['service.name'] == {
        'stringValue': 'pneumatic-file-service',
    }
    assert len(first['scopeLogs'][0]['logRecords']) == 2
    assert len(second['scopeLogs'][0]['logRecords']) == 1


def test_build__record_without_service__service_name_of_the_sink():

    """ A record written before the field existed is a backend
        record and joins the group of the backend. """

    # arrange
    records = [
        ('1-0', make_event(service=None)),
        ('2-0', make_event(service=SERVICE_NAME)),
    ]

    # act
    payload = build_sample_payload(records)

    # assert
    resource_logs = payload['resourceLogs']
    assert len(resource_logs) == 1
    assert otlp_resource_attributes(resource_logs[0])['service.name'] == {
        'stringValue': SERVICE_NAME,
    }
    assert len(resource_logs[0]['scopeLogs'][0]['logRecords']) == 2


def test_build__no_records__empty_resource_logs():

    # act
    payload = build_sample_payload([])

    # assert
    assert payload == {'resourceLogs': []}


def test_build__any_record__expected_resource_attributes():

    # act
    payload = build_sample_payload([('1-0', make_event())])

    # assert
    assert otlp_resource_attributes(payload['resourceLogs'][0]) == {
        'service.name': {'stringValue': SERVICE_NAME},
        'service.version': {'stringValue': SERVICE_VERSION},
        'deployment.environment': {'stringValue': ENVIRONMENT},
        'account_id': {'stringValue': '42'},
        'event_category': {'stringValue': EventCategory.AUDIT},
    }


def test_build__any_record__expected_scope():

    # act
    payload = build_sample_payload([('1-0', make_event())])

    # assert
    scope_log = payload['resourceLogs'][0]['scopeLogs'][0]
    assert scope_log['scope'] == {
        'name': 'pneumatic.events',
        'version': '1',
    }


def test_build__known_ts__expected_time_unix_nano():

    # act
    payload = build_sample_payload([('1-0', make_event(ts=EVENT_TS))])

    # assert
    record = otlp_first_record(payload)
    assert record['timeUnixNano'] == EVENT_TS_NANO
    assert record['observedTimeUnixNano'] == str(OBSERVED_NS)


def test_build__non_utc_ts__converted_to_utc():

    # arrange
    event = make_event(ts=EVENT_TS.astimezone(timezone(timedelta(hours=3))))

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    assert otlp_first_record(payload)['timeUnixNano'] == EVENT_TS_NANO


def test_build__naive_ts__treated_as_utc():

    # arrange
    event = make_event(ts=EVENT_TS.replace(tzinfo=None))

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    assert otlp_first_record(payload)['timeUnixNano'] == EVENT_TS_NANO


@pytest.mark.parametrize(
    ('category', 'number', 'text'),
    [
        (EventCategory.AUDIT, 9, 'INFO'),
        (EventCategory.ACTIVITY, 9, 'INFO'),
        (EventCategory.HTTP, 5, 'DEBUG'),
        (EventCategory.DEBUG, 5, 'DEBUG'),
    ],
)
def test_build__category__expected_severity(category, number, text):

    # arrange
    event = make_event(category=category)

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    record = otlp_first_record(payload)
    assert record['severityNumber'] == number
    assert record['severityText'] == text


def test_build__unknown_category__info_severity():

    """ A record written by hand into the stream may carry any
        category: it is sent as INFO rather than failing the batch. """

    # arrange
    event = make_event(category='loud')

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    record = otlp_first_record(payload)
    assert record['severityNumber'] == 9
    assert record['severityText'] == 'INFO'


def test_build__event_with_object__body_holds_type_and_object():

    # act
    payload = build_sample_payload([('1-0', make_event())])

    # assert
    assert otlp_first_record(payload)['body'] == {
        'stringValue': 'workflow.run workflow:9001',
    }


def test_build__object_without_id__body_holds_object_type():

    # arrange
    event = make_event(object=EventObject(type='workflow'))

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    assert otlp_first_record(payload)['body'] == {
        'stringValue': 'workflow.run workflow',
    }


def test_build__event_without_object__body_is_the_type_only():

    # arrange
    event = make_event(object=None)

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    assert otlp_first_record(payload)['body'] == {
        'stringValue': 'workflow.run',
    }


def test_build__event_body__free_of_pii():

    """ The pii.* attributes are dropped by the collector rule, the
        body is not: it must not carry personal data at all. """

    # arrange
    event = make_event(payload={'workflow_name': 'Onboarding: Ann'})

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    assert otlp_first_record(payload)['body'] == {
        'stringValue': 'workflow.run workflow:9001',
    }


def test_build__stream_id__used_as_the_event_id():

    """ The id of the record wins over the one the event carries: it
        is the key of idempotency for a repeated delivery. """

    # arrange
    event = make_event(id='stale-value')

    # act
    payload = build_sample_payload([('1788830100123-0', event)])

    # assert
    attributes = otlp_attributes(otlp_first_record(payload))
    assert attributes['event.id'] == {'stringValue': '1788830100123-0'}


def test_build__filled_event__expected_attribute_keys():

    """ The account and the category are resource attributes (index
        labels) and are not repeated on the record. """

    # arrange
    event = make_event(
        task_id=7002,
        payload={'workflow_event_id': 555, 'template_id': 12},
    )

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    assert list(otlp_attributes(otlp_first_record(payload))) == [
        'event.id',
        'event.type',
        'actor.type',
        'actor.id',
        'object.type',
        'object.id',
        'workflow_id',
        'task_id',
        'request_id',
        'payload.workflow_event_id',
        'payload.template_id',
        'pii.actor.email',
        'pii.ip',
        'pii.user_agent',
    ]


def test_build__pii_paths__moved_to_the_pii_namespace():

    # arrange
    event = make_event(
        payload={'workflow_name': 'Onboarding: Ann', 'template_id': 12},
        pii=(*ACTOR_PII, 'payload.workflow_name'),
    )

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    attributes = otlp_attributes(otlp_first_record(payload))
    assert attributes['pii.actor.email'] == {
        'stringValue': 'ann@example.com',
    }
    assert attributes['pii.ip'] == {'stringValue': '203.0.113.7'}
    assert attributes['pii.user_agent'] == {'stringValue': 'Mozilla/5.0'}
    assert attributes['pii.payload.workflow_name'] == {
        'stringValue': 'Onboarding: Ann',
    }
    assert 'actor.email' not in attributes
    assert 'ip' not in attributes
    assert 'user_agent' not in attributes
    assert 'payload.workflow_name' not in attributes
    assert attributes['payload.template_id'] == {'stringValue': '12'}


def test_build__empty_pii_list_in_the_record__registry_wins():

    """ Whoever can write into the stream could otherwise hand in an
        event with a filled e-mail and an empty pii list, and it would
        leave as a plain attribute past the collector rule. """

    # arrange
    event = make_event(pii=())

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    attributes = otlp_attributes(otlp_first_record(payload))
    assert attributes['pii.actor.email'] == {
        'stringValue': 'ann@example.com',
    }
    assert attributes['pii.ip'] == {'stringValue': '203.0.113.7'}
    assert attributes['pii.user_agent'] == {'stringValue': 'Mozilla/5.0'}
    assert 'actor.email' not in attributes
    assert 'ip' not in attributes
    assert 'user_agent' not in attributes


def test_build__undeclared_event_type__actor_pii_still_moved(
    mocker,
    settings,
):

    """ The registry answers ACTOR_PII for a type nobody declared,
        which is the safe side of a typo. """

    # arrange
    settings.LOGS_STRICT = False
    capture_sentry_message_mock = mocker.patch(
        'src.logs.events.registry.capture_sentry_message',
    )
    mocker.patch.object(registry_module, '_reported_unknown_types', set())
    event = make_event(type='nope.nope', pii=())

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    attributes = otlp_attributes(otlp_first_record(payload))
    assert attributes['pii.actor.email'] == {
        'stringValue': 'ann@example.com',
    }
    assert 'actor.email' not in attributes
    capture_sentry_message_mock.assert_called_once_with(
        message='Unknown event type',
        data={'event_type': 'nope.nope'},
        level=SentryLogLevel.WARNING,
    )


def test_build__empty_values__attributes_dropped():

    """ An absent attribute is cheaper than an empty one both in Loki
        and in Elasticsearch. """

    # arrange
    event = make_event(
        actor=Actor(type='system'),
        object=None,
        workflow_id=None,
        request_id=None,
        payload={'template_id': None},
        pii=(),
        ip=None,
        user_agent=None,
    )

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    assert otlp_attributes(otlp_first_record(payload)) == {
        'event.id': {'stringValue': '1-0'},
        'event.type': {'stringValue': 'workflow.run'},
        'actor.type': {'stringValue': 'system'},
    }


def test_build__empty_payload__no_payload_attributes():

    # arrange
    event = make_event(payload={})

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    attributes = otlp_attributes(otlp_first_record(payload))
    assert 'payload.template_id' not in attributes
    assert attributes['event.type'] == {'stringValue': 'workflow.run'}


def test_build__payload_that_is_a_list__kept_under_one_key():

    """ A record written by hand into the stream may carry anything
        as its payload: it is sent whole rather than failing the
        batch. """

    # arrange
    event = make_event(payload=[1, 'two'])

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    attributes = otlp_attributes(otlp_first_record(payload))
    assert attributes['payload.value'] == {'stringValue': '[1, "two"]'}


def test_payload_values__string_payload__kept_under_one_key():

    # act
    values = _payload_values('plain text')

    # assert
    assert values == {'payload.value': 'plain text'}


def test_payload_values__empty_list__no_values():

    # act
    values = _payload_values([])

    # assert
    assert values == {}


def test_build__ids__sent_as_strings():

    """ An id sent as a number in one place and as a string in another
        gives Loki labels of different types. """

    # arrange
    event = make_event(task_id=7002)

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    attributes = otlp_attributes(otlp_first_record(payload))
    assert attributes['actor.id'] == {'stringValue': '17'}
    assert attributes['object.id'] == {'stringValue': '9001'}
    assert attributes['workflow_id'] == {'stringValue': '9001'}
    assert attributes['task_id'] == {'stringValue': '7002'}
    assert otlp_resource_attributes(payload['resourceLogs'][0])[
        'account_id'
    ] == {'stringValue': '42'}


def test_build__bool_in_the_payload__bool_value():

    # arrange
    event = make_event(payload={'with_attachments': True})

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    attributes = otlp_attributes(otlp_first_record(payload))
    assert attributes['payload.with_attachments'] == {'boolValue': True}


def test_build__nested_payload__json_string():

    # arrange
    event = make_event(
        payload={'fields': {'name': 'Ann'}, 'group_ids': [1, 2]},
    )

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    attributes = otlp_attributes(otlp_first_record(payload))
    assert attributes['payload.fields'] == {
        'stringValue': '{"name": "Ann"}',
    }
    assert attributes['payload.group_ids'] == {'stringValue': '[1, 2]'}


def test_build__time_string_in_the_payload__kept_as_is():

    """ 9.30: the payload holds milliseconds, ts holds microseconds.
        The builder formats its own ts and never parses a payload. """

    # arrange
    event = make_event(payload={'created': '2026-09-08T10:15:30.123Z'})

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    record = otlp_first_record(payload)
    assert otlp_attributes(record)['payload.created'] == {
        'stringValue': '2026-09-08T10:15:30.123Z',
    }
    assert record['timeUnixNano'] == EVENT_TS_NANO


def test_build__datetime_in_the_payload__rfc3339_string():

    # arrange
    event = make_event(payload={'created': EVENT_TS})

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    attributes = otlp_attributes(otlp_first_record(payload))
    assert attributes['payload.created'] == {
        'stringValue': '2026-09-08T10:15:30.123456Z',
    }


def test_build__too_many_payload_keys__collapsed_into_extra():

    """ Loki keeps 128 structured metadata entries per line, so the
        tail of the payload travels as one JSON string. The sample
        event has 8 plain and 3 pii attributes, which leaves 48 keys
        and payload.extra for 80 payload keys. """

    # arrange
    event = make_event(
        payload={f'key_{index:02d}': index for index in range(80)},
    )

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    attributes = otlp_attributes(otlp_first_record(payload))
    extra = json.loads(attributes['payload.extra']['stringValue'])
    assert len(attributes) == MAX_ATTRIBUTES
    assert attributes['payload.key_00'] == {'stringValue': '0'}
    assert attributes['payload.key_47'] == {'stringValue': '47'}
    assert 'payload.key_48' not in attributes
    assert 'payload.key_79' not in attributes
    assert len(extra) == 32
    assert extra['key_48'] == 48
    assert extra['key_79'] == 79
    assert attributes['pii.actor.email'] == {
        'stringValue': 'ann@example.com',
    }


def test_build__too_many_payload_keys__pii_kept_outside_extra():

    # arrange
    values = {f'key_{index:02d}': index for index in range(80)}
    values['workflow_name'] = 'Onboarding: Ann'
    event = make_event(
        payload=values,
        pii=(*ACTOR_PII, 'payload.workflow_name'),
    )

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    attributes = otlp_attributes(otlp_first_record(payload))
    extra = json.loads(attributes['payload.extra']['stringValue'])
    assert attributes['pii.payload.workflow_name'] == {
        'stringValue': 'Onboarding: Ann',
    }
    assert 'workflow_name' not in extra


def test_fit_limit__within_the_limit__payload_untouched():

    # arrange
    payload = {'payload.a': 1, 'payload.b': 2}

    # act
    kept, extra = _fit_limit(reserved=MAX_ATTRIBUTES - 2, payload=payload)

    # assert
    assert kept == {'payload.a': 1, 'payload.b': 2}
    assert extra is None


def test_fit_limit__reserved_over_the_limit__whole_payload_in_extra():

    """ Nothing is left for the payload keys: they all go into
        payload.extra, and the count never goes negative. """

    # arrange
    payload = {'payload.a': 1, 'payload.b': 2}

    # act
    kept, extra = _fit_limit(reserved=MAX_ATTRIBUTES, payload=payload)

    # assert
    assert kept == {}
    assert extra == {'a': 1, 'b': 2}


def test_fit_limit__one_slot_left__extra_takes_it():

    """ The last slot goes to payload.extra rather than to one of
        the two keys: the count stays at MAX_ATTRIBUTES. """

    # arrange
    payload = {'payload.a': 1, 'payload.b': 2}

    # act
    kept, extra = _fit_limit(reserved=MAX_ATTRIBUTES - 1, payload=payload)

    # assert
    assert kept == {}
    assert extra == {'a': 1, 'b': 2}


def test_build__nested_and_numeric_values__otlp_scalars():

    """ OTLP JSON wants 64 bit numbers as strings, so nothing but a
        boolean leaves the builder as a native JSON type. """

    # arrange
    records = [
        ('1-0', make_event()),
        ('2-0', make_event(account_id=77, payload={'nested': {'a': [1, 2]}})),
    ]

    # act
    payload = build_sample_payload(records)

    # assert
    second = payload['resourceLogs'][1]['scopeLogs'][0]['logRecords'][0]
    assert second['timeUnixNano'] == EVENT_TS_NANO
    assert otlp_attributes(second) == {
        'event.id': {'stringValue': '2-0'},
        'event.type': {'stringValue': 'workflow.run'},
        'actor.type': {'stringValue': 'user'},
        'actor.id': {'stringValue': '17'},
        'object.type': {'stringValue': 'workflow'},
        'object.id': {'stringValue': '9001'},
        'workflow_id': {'stringValue': '9001'},
        'request_id': {'stringValue': '3f9c2c1e6d0b4a0f9e2b7c1d5a6e8f90'},
        'payload.nested': {'stringValue': '{"a": [1, 2]}'},
        'pii.actor.email': {'stringValue': 'ann@example.com'},
        'pii.ip': {'stringValue': '203.0.113.7'},
        'pii.user_agent': {'stringValue': 'Mozilla/5.0'},
    }
    assert json.loads(json.dumps(payload)) == payload


def test_build__sample_events__matches_the_collector_fixture():

    """ The fixture is the body a live collector accepted (P3-T1). """

    # arrange
    fixture_path = os.path.join(
        os.path.dirname(__file__), 'fixtures', 'otlp_sample.json',
    )
    with open(fixture_path, encoding='utf-8') as fixture:
        sample = json.load(fixture)
    first = make_event(
        type='workflow.run',
        category=EventCategory.AUDIT,
        ts=EVENT_TS.replace(hour=1, minute=15, second=0),
        account_id=42,
        actor=Actor(type='user', id=17, email='ann@example.com'),
        object=EventObject(type='workflow', id=9001),
        payload={
            'workflow_event_id': 555,
            'workflow_name': 'Onboarding: Ann',
            'template_id': 12,
        },
        pii=(*ACTOR_PII, 'payload.workflow_name'),
        workflow_id=9001,
        ip='203.0.113.7',
        user_agent='Mozilla/5.0 (X11; Linux x86_64)',
        request_id='3f9c2c1e6d0b4a0f9e2b7c1d5a6e8f90',
    )
    second = make_event(
        type='task.complete',
        category=EventCategory.ACTIVITY,
        ts=EVENT_TS.replace(hour=1, minute=15, second=10, microsecond=654321),
        account_id=77,
        actor=Actor(type='user', id=31, email='bob@example.com'),
        object=EventObject(type='task', id=7002),
        payload={
            'workflow_event_id': 901,
            'task_number': 2,
            'task_name': 'Sign the contract with Bob',
        },
        pii=(*ACTOR_PII, 'payload.task_name'),
        workflow_id=9105,
        task_id=7002,
        ip='198.51.100.14',
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        request_id='b41d7e0a9c3f4d2eb8a15c60f7d92311',
    )

    # act
    payload = build_sample_payload([
        ('1788830100123-0', first),
        ('1788830110654-0', second),
    ])

    # assert
    assert scrub_times(payload) == scrub_times(sample)
