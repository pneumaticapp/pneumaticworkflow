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
from src.logs.events.tests.fakes import (
    FILE_SERVICE_FILE_ID,
    FILE_SERVICE_NAME,
    build_sample_payload,
    load_file_service_contract,
    load_file_service_record,
    otlp_attributes,
    otlp_first_record,
    otlp_resource_attributes,
)


def test_from_dict__file_service_record__parsed():

    # arrange
    data = load_file_service_record()

    # act
    event = Event.from_dict(data)

    # assert
    assert event.type == EventName.FILE_DOWNLOAD
    assert event.service == FILE_SERVICE_NAME
    assert event.account_id == 42
    assert event.actor.type == 'user'
    assert event.actor.id == 17
    assert event.actor.email is None
    assert event.object.type == 'file'
    assert event.object.id == FILE_SERVICE_FILE_ID
    assert event.payload['filename'] == 'Contract Ann Smith.pdf'
    assert event.pii == ('ip', 'user_agent', 'payload.filename')


def test_to_dict__file_service_record__round_trip():

    # arrange
    data = load_file_service_record()

    # act
    restored = Event.from_dict(data).to_dict()

    # assert
    assert restored == data


def test_resolve__file_service_record__category_of_the_registry():

    """ The sink groups by the category of the record, the registry
        is asked for the personal fields only: the two must agree. """

    # arrange
    event = Event.from_dict(load_file_service_record())

    # act
    declared = resolve_event_type(event.type)

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
    event = Event.from_dict(load_file_service_record())

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    resource = otlp_resource_attributes(payload['resourceLogs'][0])
    assert resource['service.name'] == {'stringValue': FILE_SERVICE_NAME}
    assert resource['account_id'] == {'stringValue': '42'}
    assert resource['event_category'] == {
        'stringValue': EventCategory.AUDIT,
    }


def test_build__file_service_record__filename_in_the_pii_namespace():

    # arrange
    event = Event.from_dict(load_file_service_record())

    # act
    payload = build_sample_payload([('1-0', event)])

    # assert
    attributes = otlp_attributes(otlp_first_record(payload))
    assert attributes['pii.payload.filename'] == {
        'stringValue': 'Contract Ann Smith.pdf',
    }
    assert 'payload.filename' not in attributes
    assert attributes['pii.ip'] == {'stringValue': '203.0.113.7'}
    assert 'ip' not in attributes
    assert 'actor.email' not in attributes
    assert 'pii.actor.email' not in attributes
    assert attributes['object.id'] == {'stringValue': FILE_SERVICE_FILE_ID}
    assert attributes['payload.size'] == {'stringValue': '12345'}
    assert attributes['payload.is_owner'] == {'boolValue': True}
    assert otlp_first_record(payload)['body'] == {
        'stringValue': f'file.download file:{FILE_SERVICE_FILE_ID}',
    }


def test_from_dict__upload_record__parsed():

    # arrange
    data = load_file_service_record('file_service_upload_record.json')

    # act
    event = Event.from_dict(data)

    # assert
    assert event.type == EventName.FILE_UPLOAD
    assert event.service == FILE_SERVICE_NAME
    assert event.object.type == 'file'
    assert event.object.id == FILE_SERVICE_FILE_ID
    assert event.payload == {
        'filename': 'Contract Ann Smith.pdf',
        'size': 12345,
        'content_type': 'application/pdf',
    }


def test_resolve__upload_record__category_of_the_registry():

    # arrange
    event = Event.from_dict(
        load_file_service_record('file_service_upload_record.json'),
    )

    # act
    declared = resolve_event_type(event.type)

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
    data = load_file_service_record('file_service_denied_record.json')

    # act
    event = Event.from_dict(data)

    # assert
    assert event.type == EventName.FILE_ACCESS_DENIED
    assert event.account_id == 42
    assert event.payload['file_account_id'] == 99


def test_resolve__denied_record__category_of_the_registry():

    # arrange
    event = Event.from_dict(
        load_file_service_record('file_service_denied_record.json'),
    )

    # act
    declared = resolve_event_type(event.type)

    # assert
    assert declared.category == EventCategory.AUDIT
    assert declared.pii == (
        'actor.email',
        'ip',
        'user_agent',
        'payload.filename',
    )


def test_to_dict__every_file_record__round_trip():

    """ Every record the file service writes has to survive the trip
        through the consumer unchanged, not just the download one. """

    # arrange
    names = (
        'file_service_record.json',
        'file_service_upload_record.json',
        'file_service_denied_record.json',
    )

    # act
    restored = [
        Event.from_dict(load_file_service_record(name)).to_dict()
        for name in names
    ]

    # assert
    assert restored[0] == load_file_service_record(names[0])
    assert restored[1] == load_file_service_record(names[1])
    assert restored[2] == load_file_service_record(names[2])


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
