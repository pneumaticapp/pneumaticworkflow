""" The record the file service writes into the shared stream.

    fixtures/file_service_*_record.json are the contract between the
    two writers: the file service tests build their records and compare
    them with these files, the tests below read them back the way the
    consumer does. fixtures/file_service_contract.json adds the two
    names both sides keep as constants of their own, the stream and the
    actor types. A change on either side breaks the other side's test
    instead of the dead letter of a running deployment. """

from django.conf import settings
from typing_extensions import get_args

from src.logs.events.enums import ActorType, EventCategory, EventName
from src.logs.events.registry import resolve_event_type
from src.logs.events.schema import Event
from src.logs.events.sinks.otlp_payload import build_otlp_payload
from src.logs.events.tests.fixtures import (
    load_file_service_contract,
    load_file_service_record,
)


def test_from_dict__file_service_record__parsed():

    # arrange
    data = load_file_service_record()

    # act
    event = Event.from_dict(data=data)

    # assert
    assert event.type == EventName.FILE_DOWNLOAD
    assert event.service == 'pneumatic-file-service'
    assert event.account_id == 42
    assert event.actor.type == 'user'
    assert event.actor.id == 17
    assert event.actor.email is None
    assert event.object.type == 'file'
    assert event.object.id == '0f8fad5b-d9cb-469f-a165-70867728950e'
    assert event.payload['filename'] == 'Contract Ann Smith.pdf'
    assert event.pii == ('ip', 'user_agent', 'payload.filename')


def test_to_dict__file_service_record__round_trip():

    # arrange
    data = load_file_service_record()

    # act
    restored = Event.from_dict(data=data).to_dict()

    # assert
    assert restored == data


def test_to_dict__upload_record__round_trip():

    """ Every record the file service writes has to survive the trip
        through the consumer unchanged, not just the download one. """

    # arrange
    data = load_file_service_record(name='file_service_upload_record.json')

    # act
    restored = Event.from_dict(data=data).to_dict()

    # assert
    assert restored == data


def test_to_dict__denied_record__round_trip():

    # arrange
    data = load_file_service_record(name='file_service_denied_record.json')

    # act
    restored = Event.from_dict(data=data).to_dict()

    # assert
    assert restored == data


def test_resolve__file_service_record__category_of_the_registry():

    """ The sink groups by the category of the record, the registry
        is asked for the personal fields only: the two must agree. """

    # arrange
    event = Event.from_dict(data=load_file_service_record())

    # act
    declared = resolve_event_type(name=event.type)

    # assert
    assert declared.category == EventCategory.AUDIT
    assert declared.category == event.category
    assert declared.pii == (
        'actor.email',
        'ip',
        'user_agent',
        'payload.filename',
    )


def test_build__file_service_record__own_service_name():

    # arrange
    records = [('1-0', Event.from_dict(data=load_file_service_record()))]

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


def test_build__file_service_record__filename_in_the_pii_namespace():

    # arrange
    records = [('1-0', Event.from_dict(data=load_file_service_record()))]

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
    assert record['body'] == {
        'stringValue': (
            'file.download file:0f8fad5b-d9cb-469f-a165-70867728950e'
        ),
    }
    assert record['attributes'] == [
        {'key': 'event.id', 'value': {'stringValue': '1-0'}},
        {'key': 'event.type', 'value': {'stringValue': 'file.download'}},
        {'key': 'actor.type', 'value': {'stringValue': 'user'}},
        {'key': 'actor.id', 'value': {'stringValue': '17'}},
        {'key': 'object.type', 'value': {'stringValue': 'file'}},
        {
            'key': 'object.id',
            'value': {
                'stringValue': '0f8fad5b-d9cb-469f-a165-70867728950e',
            },
        },
        {
            'key': 'request_id',
            'value': {'stringValue': '3f9c2c1e6d0b4a0f9e2b7c1d5a6e8f90'},
        },
        {'key': 'payload.size', 'value': {'stringValue': '12345'}},
        {
            'key': 'payload.content_type',
            'value': {'stringValue': 'application/pdf'},
        },
        {'key': 'payload.is_owner', 'value': {'boolValue': True}},
        {'key': 'pii.ip', 'value': {'stringValue': '203.0.113.7'}},
        {
            'key': 'pii.user_agent',
            'value': {'stringValue': 'Mozilla/5.0 (X11; Linux x86_64)'},
        },
        {
            'key': 'pii.payload.filename',
            'value': {'stringValue': 'Contract Ann Smith.pdf'},
        },
    ]


def test_from_dict__upload_record__parsed():

    # arrange
    data = load_file_service_record(name='file_service_upload_record.json')

    # act
    event = Event.from_dict(data=data)

    # assert
    assert event.type == EventName.FILE_UPLOAD
    assert event.service == 'pneumatic-file-service'
    assert event.object.type == 'file'
    assert event.object.id == '0f8fad5b-d9cb-469f-a165-70867728950e'
    assert event.payload == {
        'filename': 'Contract Ann Smith.pdf',
        'size': 12345,
        'content_type': 'application/pdf',
    }


def test_resolve__upload_record__category_of_the_registry():

    # arrange
    event = Event.from_dict(
        data=load_file_service_record(
            name='file_service_upload_record.json',
        ),
    )

    # act
    declared = resolve_event_type(name=event.type)

    # assert
    assert declared.category == EventCategory.AUDIT
    assert declared.pii == (
        'actor.email',
        'ip',
        'user_agent',
        'payload.filename',
    )


def test_from_dict__denied_record__parsed():

    """ A refusal names the account of the file when it is not the
        account of the person reaching for it. """

    # arrange
    data = load_file_service_record(name='file_service_denied_record.json')

    # act
    event = Event.from_dict(data=data)

    # assert
    assert event.type == EventName.FILE_ACCESS_DENIED
    assert event.account_id == 42
    assert event.payload['file_account_id'] == 99


def test_resolve__denied_record__category_of_the_registry():

    # arrange
    event = Event.from_dict(
        data=load_file_service_record(
            name='file_service_denied_record.json',
        ),
    )

    # act
    declared = resolve_event_type(name=event.type)

    # assert
    assert declared.category == EventCategory.AUDIT
    assert declared.pii == (
        'actor.email',
        'ip',
        'user_agent',
        'payload.filename',
    )


def test_stream_key__file_service_contract__backend_reads_that_stream():

    """ Both writers name the stream as a constant of their own. A
        rename on one side would send its records into a stream the
        consumer never reads, with every other test still green. """

    # arrange
    contract = load_file_service_contract()

    # act
    stream_key = settings.LOGS_STREAM_KEY

    # assert
    assert stream_key == contract['stream_key']


def test_actor_types__file_service_contract__known_to_the_backend():

    """ Every actor type the file service may write is one the backend
        declares. The backend has one more of its own, system. """

    # arrange
    contract = load_file_service_contract()

    # act
    unknown = set(contract['actor_types']) - set(get_args(ActorType.LITERALS))

    # assert
    assert unknown == set()
