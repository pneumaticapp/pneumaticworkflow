import json
import os
from datetime import timedelta, timezone

import pytest

from src.logs.events.enums import EventCategory
from src.logs.events.registry import ACTOR_PII
from src.logs.events.schema import Actor, EventObject
from src.logs.events.sinks.otlp_payload import (
    MAX_ATTRIBUTES,
    _fit_limit,
    _payload_values,
    build_otlp_payload,
)
from src.logs.events.tests.fixtures import EVENT_TS, make_event
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
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    first, second = payload['resourceLogs']
    assert first['resource']['attributes'][3] == {
        'key': 'account_id',
        'value': {'stringValue': '42'},
    }
    assert second['resource']['attributes'][3] == {
        'key': 'account_id',
        'value': {'stringValue': '77'},
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
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    first, second = payload['resourceLogs']
    assert first['resource']['attributes'][4] == {
        'key': 'event_category',
        'value': {'stringValue': 'audit'},
    }
    assert second['resource']['attributes'][4] == {
        'key': 'event_category',
        'value': {'stringValue': 'activity'},
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
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    first, second = payload['resourceLogs']
    assert first['resource']['attributes'][0] == {
        'key': 'service.name',
        'value': {'stringValue': 'pneumatic-backend'},
    }
    assert second['resource']['attributes'][0] == {
        'key': 'service.name',
        'value': {'stringValue': 'pneumatic-file-service'},
    }
    assert len(first['scopeLogs'][0]['logRecords']) == 2
    assert len(second['scopeLogs'][0]['logRecords']) == 1


def test_build__no_records__empty_resource_logs():

    # arrange
    records = []

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    assert payload == {'resourceLogs': []}


def test_build__any_record__expected_resource_attributes():

    # arrange
    records = [('1-0', make_event())]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    assert payload['resourceLogs'][0]['resource']['attributes'] == [
        {'key': 'service.name', 'value': {'stringValue': 'pneumatic-backend'}},
        {'key': 'service.version', 'value': {'stringValue': '1.0.0'}},
        {
            'key': 'deployment.environment',
            'value': {'stringValue': 'Production'},
        },
        {'key': 'account_id', 'value': {'stringValue': '42'}},
        {'key': 'event_category', 'value': {'stringValue': 'audit'}},
    ]


def test_build__record_of_another_service__no_version():

    """ The version of the process is the version of its own
        service only: a file service record would otherwise show the
        backend release in Grafana. """

    # arrange
    records = [('1-0', make_event(service='pneumatic-file-service'))]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    assert payload['resourceLogs'][0]['resource']['attributes'] == [
        {
            'key': 'service.name',
            'value': {'stringValue': 'pneumatic-file-service'},
        },
        {
            'key': 'deployment.environment',
            'value': {'stringValue': 'Production'},
        },
        {'key': 'account_id', 'value': {'stringValue': '42'}},
        {'key': 'event_category', 'value': {'stringValue': 'audit'}},
    ]


def test_build__any_record__expected_scope():

    # arrange
    records = [('1-0', make_event())]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    scope_log = payload['resourceLogs'][0]['scopeLogs'][0]
    assert scope_log['scope'] == {
        'name': 'pneumatic.events',
        'version': '1',
    }


def test_build__known_ts__expected_time_unix_nano():

    # arrange
    records = [('1-0', make_event(ts=EVENT_TS))]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    assert record['timeUnixNano'] == '1788862530123456000'
    assert record['observedTimeUnixNano'] == '1788862535000000000'


def test_build__non_utc_ts__converted_to_utc():

    # arrange
    moscow = timezone(timedelta(hours=3))
    records = [('1-0', make_event(ts=EVENT_TS.astimezone(moscow)))]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    assert record['timeUnixNano'] == '1788862530123456000'


def test_build__naive_ts__treated_as_utc():

    # arrange
    records = [('1-0', make_event(ts=EVENT_TS.replace(tzinfo=None)))]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    assert record['timeUnixNano'] == '1788862530123456000'


@pytest.mark.parametrize(
    ('category', 'number', 'text'),
    [
        (EventCategory.AUDIT, 9, 'INFO'),
        (EventCategory.ACTIVITY, 9, 'INFO'),
        (EventCategory.DEBUG, 5, 'DEBUG'),
    ],
)
def test_build__category__expected_severity(category, number, text):

    # arrange
    records = [('1-0', make_event(category=category))]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    assert record['severityNumber'] == number
    assert record['severityText'] == text


def test_build__unknown_category__info_severity():

    """ A record written by hand into the stream may carry any
        category: it is sent as INFO rather than failing the batch. """

    # arrange
    records = [('1-0', make_event(category='loud'))]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    assert record['severityNumber'] == 9
    assert record['severityText'] == 'INFO'


def test_build__event_with_object__body_holds_type_and_object():

    # arrange
    records = [('1-0', make_event())]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    assert record['body'] == {'stringValue': 'workflow.run workflow:9001'}


def test_build__object_without_id__body_holds_object_type():

    # arrange
    records = [('1-0', make_event(object=EventObject(type='workflow')))]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    assert record['body'] == {'stringValue': 'workflow.run workflow'}


def test_build__event_without_object__body_is_the_type_only():

    # arrange
    records = [('1-0', make_event(object=None))]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    assert record['body'] == {'stringValue': 'workflow.run'}


def test_build__event_body__free_of_pii():

    """ The pii.* attributes are dropped by the collector rule, the
        body is not: it must not carry personal data at all. """

    # arrange
    event = make_event(payload={'workflow_name': 'Onboarding: Ann'})
    records = [('1-0', event)]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    assert record['body'] == {'stringValue': 'workflow.run workflow:9001'}


def test_build__stream_id__used_as_the_event_id():

    """ The id of the record wins over the one the event carries: it
        is the key of idempotency for a repeated delivery. """

    # arrange
    records = [('1788830100123-0', make_event(id='stale-value'))]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    assert record['attributes'][0] == {
        'key': 'event.id',
        'value': {'stringValue': '1788830100123-0'},
    }


def test_build__filled_event__expected_attributes():

    """ The account and the category are resource attributes (index
        labels) and are not repeated on the record. """

    # arrange
    event = make_event(
        task_id=7002,
        payload={'workflow_event_id': 555, 'template_id': 12},
    )
    records = [('1-0', event)]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    assert record['attributes'] == [
        {'key': 'event.id', 'value': {'stringValue': '1-0'}},
        {'key': 'event.type', 'value': {'stringValue': 'workflow.run'}},
        {'key': 'actor.type', 'value': {'stringValue': 'user'}},
        {'key': 'actor.id', 'value': {'stringValue': '17'}},
        {'key': 'object.type', 'value': {'stringValue': 'workflow'}},
        {'key': 'object.id', 'value': {'stringValue': '9001'}},
        {'key': 'workflow_id', 'value': {'stringValue': '9001'}},
        {'key': 'task_id', 'value': {'stringValue': '7002'}},
        {
            'key': 'request_id',
            'value': {'stringValue': '3f9c2c1e6d0b4a0f9e2b7c1d5a6e8f90'},
        },
        {'key': 'payload.workflow_event_id', 'value': {'stringValue': '555'}},
        {'key': 'payload.template_id', 'value': {'stringValue': '12'}},
        {
            'key': 'pii.actor.email',
            'value': {'stringValue': 'ann@example.com'},
        },
        {'key': 'pii.ip', 'value': {'stringValue': '203.0.113.7'}},
        {'key': 'pii.user_agent', 'value': {'stringValue': 'Mozilla/5.0'}},
    ]


def test_build__event_without_actor__no_actor_attributes():

    # arrange
    records = [('1-0', make_event(actor=None))]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    assert record['attributes'] == [
        {'key': 'event.id', 'value': {'stringValue': '1-0'}},
        {'key': 'event.type', 'value': {'stringValue': 'workflow.run'}},
        {'key': 'object.type', 'value': {'stringValue': 'workflow'}},
        {'key': 'object.id', 'value': {'stringValue': '9001'}},
        {'key': 'workflow_id', 'value': {'stringValue': '9001'}},
        {
            'key': 'request_id',
            'value': {'stringValue': '3f9c2c1e6d0b4a0f9e2b7c1d5a6e8f90'},
        },
        {'key': 'payload.template_id', 'value': {'stringValue': '12'}},
        {'key': 'pii.ip', 'value': {'stringValue': '203.0.113.7'}},
        {'key': 'pii.user_agent', 'value': {'stringValue': 'Mozilla/5.0'}},
    ]


def test_build__pii_paths__moved_to_the_pii_namespace():

    # arrange
    event = make_event(
        payload={'workflow_name': 'Onboarding: Ann', 'template_id': 12},
        pii=(*ACTOR_PII, 'payload.workflow_name'),
    )
    records = [('1-0', event)]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    assert record['attributes'] == [
        {'key': 'event.id', 'value': {'stringValue': '1-0'}},
        {'key': 'event.type', 'value': {'stringValue': 'workflow.run'}},
        {'key': 'actor.type', 'value': {'stringValue': 'user'}},
        {'key': 'actor.id', 'value': {'stringValue': '17'}},
        {'key': 'object.type', 'value': {'stringValue': 'workflow'}},
        {'key': 'object.id', 'value': {'stringValue': '9001'}},
        {'key': 'workflow_id', 'value': {'stringValue': '9001'}},
        {
            'key': 'request_id',
            'value': {'stringValue': '3f9c2c1e6d0b4a0f9e2b7c1d5a6e8f90'},
        },
        {'key': 'payload.template_id', 'value': {'stringValue': '12'}},
        {
            'key': 'pii.actor.email',
            'value': {'stringValue': 'ann@example.com'},
        },
        {'key': 'pii.ip', 'value': {'stringValue': '203.0.113.7'}},
        {'key': 'pii.user_agent', 'value': {'stringValue': 'Mozilla/5.0'}},
        {
            'key': 'pii.payload.workflow_name',
            'value': {'stringValue': 'Onboarding: Ann'},
        },
    ]


def test_build__empty_pii_list_in_the_record__registry_wins():

    """ Whoever can write into the stream could otherwise hand in an
        event with a filled e-mail and an empty pii list, and it would
        leave as a plain attribute past the collector rule. """

    # arrange
    records = [('1-0', make_event(pii=()))]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    assert record['attributes'] == [
        {'key': 'event.id', 'value': {'stringValue': '1-0'}},
        {'key': 'event.type', 'value': {'stringValue': 'workflow.run'}},
        {'key': 'actor.type', 'value': {'stringValue': 'user'}},
        {'key': 'actor.id', 'value': {'stringValue': '17'}},
        {'key': 'object.type', 'value': {'stringValue': 'workflow'}},
        {'key': 'object.id', 'value': {'stringValue': '9001'}},
        {'key': 'workflow_id', 'value': {'stringValue': '9001'}},
        {
            'key': 'request_id',
            'value': {'stringValue': '3f9c2c1e6d0b4a0f9e2b7c1d5a6e8f90'},
        },
        {'key': 'payload.template_id', 'value': {'stringValue': '12'}},
        {
            'key': 'pii.actor.email',
            'value': {'stringValue': 'ann@example.com'},
        },
        {'key': 'pii.ip', 'value': {'stringValue': '203.0.113.7'}},
        {'key': 'pii.user_agent', 'value': {'stringValue': 'Mozilla/5.0'}},
    ]


def test_build__undeclared_event_type__actor_pii_still_moved(
    mocker,
    settings,
):

    """ The registry answers ACTOR_PII for a type nobody declared,
        which is the safe side of a typo. """

    # arrange
    settings.LOGS_STRICT = False
    report_error_mock = mocker.patch(
        'src.logs.events.registry.report_error',
    )
    records = [('1-0', make_event(type='nope.nope', pii=()))]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    assert record['attributes'] == [
        {'key': 'event.id', 'value': {'stringValue': '1-0'}},
        {'key': 'event.type', 'value': {'stringValue': 'nope.nope'}},
        {'key': 'actor.type', 'value': {'stringValue': 'user'}},
        {'key': 'actor.id', 'value': {'stringValue': '17'}},
        {'key': 'object.type', 'value': {'stringValue': 'workflow'}},
        {'key': 'object.id', 'value': {'stringValue': '9001'}},
        {'key': 'workflow_id', 'value': {'stringValue': '9001'}},
        {
            'key': 'request_id',
            'value': {'stringValue': '3f9c2c1e6d0b4a0f9e2b7c1d5a6e8f90'},
        },
        {'key': 'payload.template_id', 'value': {'stringValue': '12'}},
        {
            'key': 'pii.actor.email',
            'value': {'stringValue': 'ann@example.com'},
        },
        {'key': 'pii.ip', 'value': {'stringValue': '203.0.113.7'}},
        {'key': 'pii.user_agent', 'value': {'stringValue': 'Mozilla/5.0'}},
    ]
    report_error_mock.assert_called_once_with(
        message='Unknown event type',
        data={'event_type': 'nope.nope'},
        level=SentryLogLevel.WARNING,
        key='unknown-event-type:nope.nope',
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
    records = [('1-0', event)]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    assert record['attributes'] == [
        {'key': 'event.id', 'value': {'stringValue': '1-0'}},
        {'key': 'event.type', 'value': {'stringValue': 'workflow.run'}},
        {'key': 'actor.type', 'value': {'stringValue': 'system'}},
    ]


def test_build__empty_payload__no_payload_attributes():

    # arrange
    records = [('1-0', make_event(payload={}))]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    assert record['attributes'] == [
        {'key': 'event.id', 'value': {'stringValue': '1-0'}},
        {'key': 'event.type', 'value': {'stringValue': 'workflow.run'}},
        {'key': 'actor.type', 'value': {'stringValue': 'user'}},
        {'key': 'actor.id', 'value': {'stringValue': '17'}},
        {'key': 'object.type', 'value': {'stringValue': 'workflow'}},
        {'key': 'object.id', 'value': {'stringValue': '9001'}},
        {'key': 'workflow_id', 'value': {'stringValue': '9001'}},
        {
            'key': 'request_id',
            'value': {'stringValue': '3f9c2c1e6d0b4a0f9e2b7c1d5a6e8f90'},
        },
        {
            'key': 'pii.actor.email',
            'value': {'stringValue': 'ann@example.com'},
        },
        {'key': 'pii.ip', 'value': {'stringValue': '203.0.113.7'}},
        {'key': 'pii.user_agent', 'value': {'stringValue': 'Mozilla/5.0'}},
    ]


def test_build__payload_that_is_a_list__kept_under_one_key():

    """ A record written by hand into the stream may carry anything
        as its payload: it is sent whole rather than failing the
        batch. """

    # arrange
    records = [('1-0', make_event(payload=[1, 'two']))]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    assert record['attributes'][8] == {
        'key': 'payload.value',
        'value': {'stringValue': '[1, "two"]'},
    }


def test_payload_values__string_payload__kept_under_one_key():

    # arrange
    payload = 'plain text'

    # act
    values = _payload_values(payload=payload)

    # assert
    assert values == {'payload.value': 'plain text'}


def test_payload_values__empty_list__no_values():

    # arrange
    payload = []

    # act
    values = _payload_values(payload=payload)

    # assert
    assert values == {}


def test_build__ids__sent_as_strings():

    """ An id sent as a number in one place and as a string in another
        gives Loki labels of different types. """

    # arrange
    records = [('1-0', make_event(task_id=7002))]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    resource_log = payload['resourceLogs'][0]
    record = resource_log['scopeLogs'][0]['logRecords'][0]
    assert record['attributes'][3] == {
        'key': 'actor.id',
        'value': {'stringValue': '17'},
    }
    assert record['attributes'][5] == {
        'key': 'object.id',
        'value': {'stringValue': '9001'},
    }
    assert record['attributes'][6] == {
        'key': 'workflow_id',
        'value': {'stringValue': '9001'},
    }
    assert record['attributes'][7] == {
        'key': 'task_id',
        'value': {'stringValue': '7002'},
    }
    assert resource_log['resource']['attributes'][3] == {
        'key': 'account_id',
        'value': {'stringValue': '42'},
    }


def test_build__bool_in_the_payload__bool_value():

    # arrange
    records = [('1-0', make_event(payload={'with_attachments': True}))]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    assert record['attributes'][8] == {
        'key': 'payload.with_attachments',
        'value': {'boolValue': True},
    }


def test_build__nested_payload__json_string():

    # arrange
    event = make_event(
        payload={'fields': {'name': 'Ann'}, 'group_ids': [1, 2]},
    )
    records = [('1-0', event)]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    assert record['attributes'][8] == {
        'key': 'payload.fields',
        'value': {'stringValue': '{"name": "Ann"}'},
    }
    assert record['attributes'][9] == {
        'key': 'payload.group_ids',
        'value': {'stringValue': '[1, 2]'},
    }


def test_build__time_string_in_the_payload__kept_as_is():

    """ 9.30: the payload holds milliseconds, ts holds microseconds.
        The builder formats its own ts and never parses a payload. """

    # arrange
    event = make_event(payload={'created': '2026-09-08T10:15:30.123Z'})
    records = [('1-0', event)]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    assert record['attributes'][8] == {
        'key': 'payload.created',
        'value': {'stringValue': '2026-09-08T10:15:30.123Z'},
    }
    assert record['timeUnixNano'] == '1788862530123456000'


def test_build__datetime_in_the_payload__rfc3339_string():

    # arrange
    records = [('1-0', make_event(payload={'created': EVENT_TS}))]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    assert record['attributes'][8] == {
        'key': 'payload.created',
        'value': {'stringValue': '2026-09-08T10:15:30.123456Z'},
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
    records = [('1-0', event)]
    extra = {f'key_{index:02d}': index for index in range(48, 80)}

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    attributes = record['attributes']
    assert len(attributes) == MAX_ATTRIBUTES
    assert attributes[8] == {
        'key': 'payload.key_00',
        'value': {'stringValue': '0'},
    }
    assert attributes[55] == {
        'key': 'payload.key_47',
        'value': {'stringValue': '47'},
    }
    assert attributes[56]['key'] == 'payload.extra'
    assert json.loads(attributes[56]['value']['stringValue']) == extra
    assert attributes[57] == {
        'key': 'pii.actor.email',
        'value': {'stringValue': 'ann@example.com'},
    }


def test_build__too_many_payload_keys__pii_kept_outside_extra():

    # arrange
    values = {f'key_{index:02d}': index for index in range(80)}
    values['workflow_name'] = 'Onboarding: Ann'
    event = make_event(
        payload=values,
        pii=(*ACTOR_PII, 'payload.workflow_name'),
    )
    records = [('1-0', event)]
    extra = {f'key_{index:02d}': index for index in range(47, 80)}

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    record = payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    attributes = record['attributes']
    assert len(attributes) == MAX_ATTRIBUTES
    assert attributes[55]['key'] == 'payload.extra'
    assert json.loads(attributes[55]['value']['stringValue']) == extra
    assert attributes[59] == {
        'key': 'pii.payload.workflow_name',
        'value': {'stringValue': 'Onboarding: Ann'},
    }


def test_fit_limit__within_the_limit__payload_untouched():

    # arrange
    payload = {'payload.a': 1, 'payload.b': 2}
    reserved = MAX_ATTRIBUTES - 2

    # act
    kept, extra = _fit_limit(reserved=reserved, payload=payload)

    # assert
    assert kept == {'payload.a': 1, 'payload.b': 2}
    assert extra is None


def test_fit_limit__reserved_over_the_limit__whole_payload_in_extra():

    """ Nothing is left for the payload keys: they all go into
        payload.extra, and the count never goes negative. """

    # arrange
    payload = {'payload.a': 1, 'payload.b': 2}
    reserved = MAX_ATTRIBUTES

    # act
    kept, extra = _fit_limit(reserved=reserved, payload=payload)

    # assert
    assert kept == {}
    assert extra == {'a': 1, 'b': 2}


def test_fit_limit__one_slot_left__extra_takes_it():

    """ The last slot goes to payload.extra rather than to one of
        the two keys: the count stays at MAX_ATTRIBUTES. """

    # arrange
    payload = {'payload.a': 1, 'payload.b': 2}
    reserved = MAX_ATTRIBUTES - 1

    # act
    kept, extra = _fit_limit(reserved=reserved, payload=payload)

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
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    second = payload['resourceLogs'][1]['scopeLogs'][0]['logRecords'][0]
    assert second['timeUnixNano'] == '1788862530123456000'
    assert second['attributes'] == [
        {'key': 'event.id', 'value': {'stringValue': '2-0'}},
        {'key': 'event.type', 'value': {'stringValue': 'workflow.run'}},
        {'key': 'actor.type', 'value': {'stringValue': 'user'}},
        {'key': 'actor.id', 'value': {'stringValue': '17'}},
        {'key': 'object.type', 'value': {'stringValue': 'workflow'}},
        {'key': 'object.id', 'value': {'stringValue': '9001'}},
        {'key': 'workflow_id', 'value': {'stringValue': '9001'}},
        {
            'key': 'request_id',
            'value': {'stringValue': '3f9c2c1e6d0b4a0f9e2b7c1d5a6e8f90'},
        },
        {'key': 'payload.nested', 'value': {'stringValue': '{"a": [1, 2]}'}},
        {
            'key': 'pii.actor.email',
            'value': {'stringValue': 'ann@example.com'},
        },
        {'key': 'pii.ip', 'value': {'stringValue': '203.0.113.7'}},
        {'key': 'pii.user_agent', 'value': {'stringValue': 'Mozilla/5.0'}},
    ]
    assert json.loads(json.dumps(payload)) == payload


def test_build__sample_events__matches_the_collector_fixture():

    """ The fixture is the body a live collector accepted (P3-T1),
        read at its own moment: the moment of reading is the one
        field the builder takes from the caller. """

    # arrange
    fixture_path = os.path.join(
        os.path.dirname(__file__), 'fixtures', 'otlp_sample.json',
    )
    with open(fixture_path, encoding='utf-8') as fixture:
        sample = json.load(fixture)
    first_sample = sample['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]
    first_sample['observedTimeUnixNano'] = '1788862535000000000'
    second_sample = sample['resourceLogs'][1]['scopeLogs'][0]['logRecords'][0]
    second_sample['observedTimeUnixNano'] = '1788862535000000000'
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
    records = [('1788830100123-0', first), ('1788830110654-0', second)]

    # act
    payload = build_otlp_payload(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Production',
        observed_ns=1788862535000000000,
    )

    # assert
    assert payload == sample
