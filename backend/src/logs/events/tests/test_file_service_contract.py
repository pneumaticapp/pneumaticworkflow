""" The record the file service writes into the shared stream.

    fixtures/file_service_record.json is the contract between the two
    writers: the file service tests build their record and compare it
    with this file, the tests below read it back the way the consumer
    does. A change on either side breaks the other side's test instead
    of the dead letter of a running deployment. """

from src.logs.events.enums import EventCategory, EventName
from src.logs.events.registry import FILE_PII, EventRegistry
from src.logs.events.schema import Event
from src.logs.events.tests.fakes import (
    FILE_SERVICE_FILE_ID,
    FILE_SERVICE_NAME,
    build_sample_payload,
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
    declared = EventRegistry.resolve(event.type)

    # assert
    assert declared.category == EventCategory.AUDIT
    assert declared.category == event.category
    assert declared.pii == FILE_PII


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
