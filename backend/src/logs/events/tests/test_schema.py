import json
from datetime import datetime, timedelta, timezone

import pytest
from django.core.serializers.json import DjangoJSONEncoder

from src.accounts.enums import UserType
from src.authentication.enums import AuthTokenType
from src.logs.events.entities import Actor, Event, EventObject
from src.logs.events.schema import to_json, without_url_secrets
from src.logs.events.tests.fixtures import EVENT_TS, make_event


def test_to_dict__filled_event__expected_json():

    # arrange
    event = make_event(id='1725790000000-0')

    # act
    data = event.to_dict()

    # assert
    assert data == {
        'id': '1725790000000-0',
        'type': 'workflow.run',
        'category': 'workflows',
        'service': 'pneumatic-backend',
        'ts': '2026-09-08T10:15:30.123456Z',
        'account_id': 42,
        'actor': {'id': 17, 'email': 'ann@example.com', 'user_type': 'user'},
        'auth_type': 'User',
        'object': {'type': 'workflow', 'id': 9001},
        'workflow_id': 9001,
        'task_id': None,
        'ip': '203.0.113.7',
        'user_agent': 'Mozilla/5.0',
        'request_id': '3f9c2c1e6d0b4a0f9e2b7c1d5a6e8f90',
        'payload': {'template_id': 12},
    }


def test_to_dict__datetime_in_payload__survives_the_stream_encoder():
    """xadd serializes the dict with DjangoJSONEncoder, so a moment
    of the payload has to come back as a readable string."""

    # arrange
    event = make_event(payload={'created': EVENT_TS})

    # act
    data = json.loads(json.dumps(event.to_dict(), cls=DjangoJSONEncoder))

    # assert
    assert data['payload'] == {'created': '2026-09-08T10:15:30.123Z'}


def test_to_dict__id_not_known_yet__key_absent():
    """5.1: Redis assigns the id on XADD, the record of the stream
    carries none. A null would reach Loki as the string "None"."""

    # arrange
    event = make_event(id=None)

    # act
    data = event.to_dict()

    # assert
    assert 'id' not in data


def test_from_dict__to_dict_result__round_trip():

    # arrange
    event = make_event(id='1725790000000-0')
    data = json.loads(json.dumps(event.to_dict()))

    # act
    restored = Event.from_dict(data=data)

    # assert
    assert restored == event


def test_from_dict__human_names__preserved_after_stream_serialization():

    # arrange
    event = make_event(
        account_name='Operations',
        object=EventObject(
            type='workflow',
            id=9001,
            name='Purchase request',
        ),
    )
    stored = json.loads(json.dumps(event.to_dict(), cls=DjangoJSONEncoder))

    # act
    restored = Event.from_dict(data=stored)

    # assert
    assert stored['account_name'] == 'Operations'
    assert stored['object']['name'] == 'Purchase request'
    assert restored == event


def test_from_dict__event_without_actor_and_object__both_none():

    # arrange
    event = make_event(actor=None, object=None, payload={}, id=None)
    data = event.to_dict()

    # act
    restored = Event.from_dict(data=data)

    # assert
    assert restored.actor is None
    assert restored.object is None
    assert restored == event


def test_from_dict__record_without_optional_keys__defaults():

    # arrange
    data = {
        'type': 'system.smoke',
        'category': 'accounts',
        'service': 'pneumatic-backend',
        'ts': '2026-09-08T10:15:30.123456Z',
        'account_id': 7,
    }

    # act
    restored = Event.from_dict(data=data)

    # assert
    assert restored.payload == {}
    assert restored.actor is None
    assert restored.auth_type is None
    assert restored.service == 'pneumatic-backend'
    assert restored.id is None
    assert restored.ts.tzinfo == timezone.utc


def test_to_dict__non_utc_ts__converted_to_utc():

    # arrange
    moscow = timezone(timedelta(hours=3))
    event = make_event(ts=EVENT_TS.astimezone(moscow))

    # act
    data = event.to_dict()

    # assert
    assert data['ts'] == '2026-09-08T10:15:30.123456Z'


def test_to_dict__naive_ts__treated_as_utc():

    # arrange
    event = make_event(ts=EVENT_TS.replace(tzinfo=None))

    # act
    data = event.to_dict()

    # assert
    assert data['ts'] == '2026-09-08T10:15:30.123456Z'


def test_from_dict__utc_string__same_moment():

    # arrange
    data = make_event(ts=EVENT_TS).to_dict()

    # act
    restored = Event.from_dict(data=data)

    # assert
    assert restored.ts == datetime(
        2026,
        9,
        8,
        10,
        15,
        30,
        123456,
        tzinfo=timezone.utc,
    )


def test_to_dict__no_service__key_written_as_null():
    """The key is always there: a record of the stream is read by
    eye as often as by the consumer, and an absent key reads as a
    record of another shape."""

    # arrange
    event = make_event(service=None)

    # act
    data = event.to_dict()

    # assert
    assert data['service'] is None


def test_from_dict__record_of_another_service__service_kept():

    # arrange
    data = make_event(service='pneumatic-file-service').to_dict()

    # act
    restored = Event.from_dict(data=data)

    # assert
    assert restored.service == 'pneumatic-file-service'


def test_actor_from_dict__empty_dict__none():

    # arrange
    data = {}

    # act
    actor = Actor.from_dict(data=data)

    # assert
    assert actor is None


def test_event_object_from_dict__empty_dict__none():

    # arrange
    data = {}

    # act
    event_object = EventObject.from_dict(data=data)

    # assert
    assert event_object is None


def test_event_object_from_dict__filled_dict__object():

    # arrange
    data = {'type': 'group', 'id': 5}

    # act
    event_object = EventObject.from_dict(data=data)

    # assert
    assert event_object == EventObject(
        type='group',
        id=5,
    )


def test_to_dict__system_event__no_actor_and_no_auth_type():
    """The system has no actor and no credential: both keys are
    written as null, so that a record is read by eye as one of
    the same shape."""

    # arrange
    event = make_event(actor=None, auth_type=None)

    # act
    data = event.to_dict()

    # assert
    assert data['actor'] is None
    assert data['auth_type'] is None


def test_from_dict__auth_type__read_back():

    # arrange
    data = make_event(auth_type=AuthTokenType.API).to_dict()

    # act
    restored = Event.from_dict(data=data)

    # assert
    assert restored.auth_type == 'API'


def test_from_dict__guest_actor__user_type_read_back():

    # arrange
    data = make_event(
        actor=Actor(
            id=3,
            email='guest@test.test',
            user_type=UserType.GUEST,
        ),
        auth_type=AuthTokenType.GUEST,
    ).to_dict()

    # act
    restored = Event.from_dict(data=data)

    # assert
    assert restored.actor == Actor(
        id=3,
        email='guest@test.test',
        user_type='guest',
    )
    assert restored.auth_type == 'Guest'


def test_to_json__value_no_encoder_knows__its_text():
    """A value that cannot be encoded becomes its text instead of
    breaking the batch."""

    # arrange
    value = object()

    # act
    result = to_json(value=value)

    # assert
    assert result == json.dumps(str(value))


@pytest.mark.parametrize(
    ('url', 'expected'),
    [
        (
            'http://otel-collector:4318/v1/logs',
            'http://otel-collector:4318/v1/logs',
        ),
        (
            'https://user:secret@collector.test/v1/logs',
            'https://collector.test/v1/logs',
        ),
        (
            'https://user:secret@collector.test:4318/v1/logs',
            'https://collector.test:4318/v1/logs',
        ),
        (
            'https://token@collector.test/v1/logs',
            'https://collector.test/v1/logs',
        ),
    ],
)
def test_without_url_secrets__url__credential_dropped(url, expected):

    # arrange
    endpoint_url = url

    # act
    result = without_url_secrets(value=endpoint_url)

    # assert
    assert result == expected


def test_without_url_secrets__ipv6_host_with_credential__brackets_kept():

    # arrange
    url = 'http://user:secret@[::1]:4318/v1/logs'

    # act
    result = without_url_secrets(value=url)

    # assert
    assert result == 'http://[::1]:4318/v1/logs'
