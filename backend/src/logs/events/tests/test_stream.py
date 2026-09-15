import json
import logging

import pytest
import redis
from django.core.serializers.json import DjangoJSONEncoder

from src.logs.events.stream import (
    AUTOCLAIM_START,
    DEAD_MAXLEN,
    MALFORMED_REASON,
    NEW_ENTRIES,
    PENDING_ENTRIES,
    ParsedEntries,
    _to_event,
)
from src.logs.events.tests.fixtures import make_event, make_unit_stream


def test_dead_key__any_stream__suffixed_key():

    # arrange
    stream = make_unit_stream()

    # act
    result = stream.dead_key

    # assert
    assert result == 'pneumatic:events-unit:dead'


def test_client__first_call__built_from_the_url(mocker):

    # arrange
    client_mock = mocker.Mock()
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()

    # act
    client = stream.client

    # assert
    assert client is client_mock
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_client__called_twice__one_connection(mocker):

    # arrange
    client_mock = mocker.Mock()
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()

    # act
    first = stream.client
    second = stream.client

    # assert
    assert first is client_mock
    assert second is client_mock
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_xadd__event__written_with_the_trim(mocker):

    # arrange
    client_mock = mocker.Mock()
    client_mock.xadd.return_value = '1-0'
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()
    event = make_event()

    # act
    result = stream.xadd(event=event)

    # assert
    assert result == '1-0'
    client_mock.xadd.assert_called_once_with(
        name='pneumatic:events-unit',
        fields={
            'type': 'workflow.run',
            'data': json.dumps(event.to_dict(), cls=DjangoJSONEncoder),
        },
        maxlen=10,
        approximate=True,
    )
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_ensure_group__new_stream__group_created(mocker):

    # arrange
    client_mock = mocker.Mock()
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()

    # act
    stream.ensure_group()

    # assert
    client_mock.xgroup_create.assert_called_once_with(
        name='pneumatic:events-unit',
        groupname='otlp',
        id='0',
        mkstream=True,
    )
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_ensure_group__group_exists__error_swallowed(mocker):

    # arrange
    client_mock = mocker.Mock()
    client_mock.xgroup_create.side_effect = redis.ResponseError(
        'BUSYGROUP Consumer Group name already exists',
    )
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()

    # act
    stream.ensure_group()

    # assert
    client_mock.xgroup_create.assert_called_once_with(
        name='pneumatic:events-unit',
        groupname='otlp',
        id='0',
        mkstream=True,
    )
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_ensure_group__other_response_error__raised(mocker):

    """ Only the "already exists" answer is expected; anything else
        is a broken stream and must not be hidden. """

    # arrange
    client_mock = mocker.Mock()
    client_mock.xgroup_create.side_effect = redis.ResponseError(
        'WRONGTYPE Operation against a key',
    )
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()

    # act
    with pytest.raises(redis.ResponseError) as ex:
        stream.ensure_group()

    # assert
    assert str(ex.value) == 'WRONGTYPE Operation against a key'
    client_mock.xgroup_create.assert_called_once_with(
        name='pneumatic:events-unit',
        groupname='otlp',
        id='0',
        mkstream=True,
    )
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_read_new__entries__events_with_their_ids(mocker):

    # arrange
    event = make_event()
    client_mock = mocker.Mock()
    client_mock.xreadgroup.return_value = [(
        'pneumatic:events-unit',
        [(
            '1-0',
            {
                'type': 'workflow.run',
                'data': json.dumps(event.to_dict(), cls=DjangoJSONEncoder),
            },
        )],
    )]
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()

    # act
    result = stream.read_new(consumer='consumer-1', count=5)

    # assert
    assert len(result.events) == 1
    assert result.events[0][0] == '1-0'
    assert result.events[0][1].id == '1-0'
    assert result.events[0][1].type == 'workflow.run'
    assert result.malformed == []
    assert result.vanished == []
    client_mock.xreadgroup.assert_called_once_with(
        groupname='otlp',
        consumername='consumer-1',
        streams={'pneumatic:events-unit': NEW_ENTRIES},
        count=5,
    )
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_read_pending__entries__read_from_the_start(mocker):

    # arrange
    client_mock = mocker.Mock()
    client_mock.xreadgroup.return_value = []
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()

    # act
    result = stream.read_pending(consumer='consumer-1', count=5)

    # assert
    assert result == ParsedEntries()
    client_mock.xreadgroup.assert_called_once_with(
        groupname='otlp',
        consumername='consumer-1',
        streams={'pneumatic:events-unit': PENDING_ENTRIES},
        count=5,
    )
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_read_new__no_answer__no_events(mocker):

    # arrange
    client_mock = mocker.Mock()
    client_mock.xreadgroup.return_value = None
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()

    # act
    result = stream.read_new(consumer='consumer-1', count=5)

    # assert
    assert result == ParsedEntries()
    client_mock.xreadgroup.assert_called_once_with(
        groupname='otlp',
        consumername='consumer-1',
        streams={'pneumatic:events-unit': NEW_ENTRIES},
        count=5,
    )
    client_mock.xack.assert_not_called()
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_read_new__entry_without_fields__acked_and_dropped(mocker, caplog):

    """ A record trimmed away while it was pending comes back with
        no fields: nothing can be delivered, the id is acked. The log
        says how many, not which: an answer holds up to count ids. """

    # arrange
    caplog.set_level(logging.WARNING, logger='pneumatic.events')
    client_mock = mocker.Mock()
    client_mock.xreadgroup.return_value = [
        ('pneumatic:events-unit', [('1-0', {})]),
    ]
    client_mock.xack.return_value = 1
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()

    # act
    result = stream.read_new(consumer='consumer-1', count=5)

    # assert
    assert result == ParsedEntries(vanished=['1-0'])
    assert caplog.messages == ['Trimmed pending events acked: 1']
    client_mock.xack.assert_called_once_with(
        'pneumatic:events-unit', 'otlp', '1-0',
    )
    client_mock.pipeline.assert_not_called()
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_read_new__unparsable_entry__parked_in_the_dead_letter(
    mocker,
    caplog,
):

    # arrange
    caplog.set_level(logging.WARNING, logger='pneumatic.events')
    client_mock = mocker.Mock()
    client_mock.xreadgroup.return_value = [
        ('pneumatic:events-unit', [('1-0', {'data': 'not json'})]),
    ]
    pipeline_mock = mocker.Mock()
    pipeline_mock.execute.return_value = [1]
    client_mock.pipeline.return_value = pipeline_mock
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()

    # act
    result = stream.read_new(consumer='consumer-1', count=5)

    # assert
    assert result == ParsedEntries(malformed=[('1-0', {'data': 'not json'})])
    assert caplog.messages == ['Malformed events dropped: 1']
    client_mock.pipeline.assert_called_once_with(transaction=True)
    pipeline_mock.xadd.assert_called_once_with(
        name='pneumatic:events-unit:dead',
        fields={
            'type': '',
            'reason': MALFORMED_REASON,
            'source_id': '1-0',
            'data': json.dumps({'data': 'not json'}),
        },
        maxlen=DEAD_MAXLEN,
        approximate=True,
    )
    pipeline_mock.xack.assert_called_once_with(
        'pneumatic:events-unit', 'otlp', '1-0',
    )
    pipeline_mock.execute.assert_called_once_with()
    client_mock.xack.assert_not_called()
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_autoclaim__redis_62_answer__entries_taken_over(mocker):

    # arrange
    event = make_event()
    client_mock = mocker.Mock()
    client_mock.xautoclaim.return_value = [
        '0-0',
        [(
            '1-0',
            {
                'type': 'workflow.run',
                'data': json.dumps(event.to_dict(), cls=DjangoJSONEncoder),
            },
        )],
    ]
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()

    # act
    result = stream.autoclaim(
        consumer='consumer-1',
        min_idle_ms=1000,
        count=5,
    )

    # assert
    assert len(result.events) == 1
    assert result.events[0][0] == '1-0'
    client_mock.xautoclaim.assert_called_once_with(
        name='pneumatic:events-unit',
        groupname='otlp',
        consumername='consumer-1',
        min_idle_time=1000,
        start_id=AUTOCLAIM_START,
        count=5,
    )
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_autoclaim__redis_70_answer__deleted_ids_ignored(mocker):

    """ Redis 7.0 answers [next_id, entries, deleted_ids] and removes
        the deleted ids from the pending list itself: there is nothing
        to ack or to park for them. """

    # arrange
    event = make_event()
    client_mock = mocker.Mock()
    client_mock.xautoclaim.return_value = [
        '0-0',
        [(
            '1-0',
            {
                'type': 'workflow.run',
                'data': json.dumps(event.to_dict(), cls=DjangoJSONEncoder),
            },
        )],
        ['2-0'],
    ]
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()

    # act
    result = stream.autoclaim(
        consumer='consumer-1',
        min_idle_ms=1000,
        count=5,
    )

    # assert
    assert len(result.events) == 1
    assert result.events[0][0] == '1-0'
    assert result.vanished == []
    assert result.malformed == []
    client_mock.xautoclaim.assert_called_once_with(
        name='pneumatic:events-unit',
        groupname='otlp',
        consumername='consumer-1',
        min_idle_time=1000,
        start_id=AUTOCLAIM_START,
        count=5,
    )
    client_mock.xack.assert_not_called()
    client_mock.pipeline.assert_not_called()
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_autoclaim__deleted_record_pair__dropped(mocker):

    """ Redis 6.2 answers a claimed record the stream no longer holds
        as a (None, None) pair. """

    # arrange
    client_mock = mocker.Mock()
    client_mock.xautoclaim.return_value = ['0-0', [(None, None)]]
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()

    # act
    result = stream.autoclaim(
        consumer='consumer-1',
        min_idle_ms=1000,
        count=5,
    )

    # assert
    assert result == ParsedEntries()
    client_mock.xautoclaim.assert_called_once_with(
        name='pneumatic:events-unit',
        groupname='otlp',
        consumername='consumer-1',
        min_idle_time=1000,
        start_id=AUTOCLAIM_START,
        count=5,
    )
    client_mock.xack.assert_not_called()
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_autoclaim__answer_without_entries__no_events(mocker):

    # arrange
    client_mock = mocker.Mock()
    client_mock.xautoclaim.return_value = ['0-0']
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()

    # act
    result = stream.autoclaim(
        consumer='consumer-1',
        min_idle_ms=1000,
        count=5,
    )

    # assert
    assert result == ParsedEntries()
    client_mock.xautoclaim.assert_called_once_with(
        name='pneumatic:events-unit',
        groupname='otlp',
        consumername='consumer-1',
        min_idle_time=1000,
        start_id=AUTOCLAIM_START,
        count=5,
    )
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_ack__ids__acked_in_one_call(mocker):

    # arrange
    client_mock = mocker.Mock()
    client_mock.xack.return_value = 2
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()
    ids = ['1-0', '2-0']

    # act
    result = stream.ack(ids=ids)

    # assert
    assert result == 2
    client_mock.xack.assert_called_once_with(
        'pneumatic:events-unit', 'otlp', '1-0', '2-0',
    )
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_ack__no_ids__redis_not_called(mocker):

    # arrange
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
    )
    stream = make_unit_stream()
    ids = []

    # act
    result = stream.ack(ids=ids)

    # assert
    assert result == 0
    from_url_mock.assert_not_called()


def test_dead_letter__event__parked_with_its_type(mocker):

    # arrange
    event = make_event()
    client_mock = mocker.Mock()
    pipeline_mock = mocker.Mock()
    pipeline_mock.execute.return_value = [1]
    client_mock.pipeline.return_value = pipeline_mock
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()

    # act
    result = stream.dead_letter(entries=[('1-0', event)], reason='rejected')

    # assert
    assert result == 1
    client_mock.pipeline.assert_called_once_with(transaction=True)
    pipeline_mock.xadd.assert_called_once_with(
        name='pneumatic:events-unit:dead',
        fields={
            'type': 'workflow.run',
            'reason': 'rejected',
            'source_id': '1-0',
            'data': json.dumps(event.to_dict()),
        },
        maxlen=DEAD_MAXLEN,
        approximate=True,
    )
    pipeline_mock.xack.assert_called_once_with(
        'pneumatic:events-unit', 'otlp', '1-0',
    )
    pipeline_mock.execute.assert_called_once_with()
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_dead_letter__raw_fields__parked_as_they_are(mocker):

    # arrange
    client_mock = mocker.Mock()
    pipeline_mock = mocker.Mock()
    pipeline_mock.execute.return_value = [1]
    client_mock.pipeline.return_value = pipeline_mock
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()
    raw = {'type': 'user.login', 'data': 'broken'}

    # act
    result = stream.dead_letter(entries=[('1-0', raw)], reason='malformed')

    # assert
    assert result == 1
    client_mock.pipeline.assert_called_once_with(transaction=True)
    pipeline_mock.xadd.assert_called_once_with(
        name='pneumatic:events-unit:dead',
        fields={
            'type': 'user.login',
            'reason': 'malformed',
            'source_id': '1-0',
            'data': json.dumps(raw),
        },
        maxlen=DEAD_MAXLEN,
        approximate=True,
    )
    pipeline_mock.xack.assert_called_once_with(
        'pneumatic:events-unit', 'otlp', '1-0',
    )
    pipeline_mock.execute.assert_called_once_with()
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_dead_letter__two_entries__one_pipeline(mocker):

    """ A rejected batch is as long as a delivered one: one round
        trip for all of it, the ack in the same transaction. """

    # arrange
    first = make_event()
    second = make_event(type='user.login')
    client_mock = mocker.Mock()
    pipeline_mock = mocker.Mock()
    pipeline_mock.execute.return_value = [2]
    client_mock.pipeline.return_value = pipeline_mock
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()

    # act
    result = stream.dead_letter(
        entries=[('1-0', first), ('2-0', second)],
        reason='rejected',
    )

    # assert
    assert result == 2
    client_mock.pipeline.assert_called_once_with(transaction=True)
    assert pipeline_mock.xadd.call_count == 2
    pipeline_mock.xadd.assert_has_calls([
        mocker.call(
            name='pneumatic:events-unit:dead',
            fields={
                'type': 'workflow.run',
                'reason': 'rejected',
                'source_id': '1-0',
                'data': json.dumps(first.to_dict()),
            },
            maxlen=DEAD_MAXLEN,
            approximate=True,
        ),
        mocker.call(
            name='pneumatic:events-unit:dead',
            fields={
                'type': 'user.login',
                'reason': 'rejected',
                'source_id': '2-0',
                'data': json.dumps(second.to_dict()),
            },
            maxlen=DEAD_MAXLEN,
            approximate=True,
        ),
    ])
    pipeline_mock.xack.assert_called_once_with(
        'pneumatic:events-unit', 'otlp', '1-0', '2-0',
    )
    pipeline_mock.execute.assert_called_once_with()
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_dead_letter__no_entries__redis_not_called(mocker):

    # arrange
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
    )
    stream = make_unit_stream()
    entries = []

    # act
    result = stream.dead_letter(entries=entries, reason='rejected')

    # assert
    assert result == 0
    from_url_mock.assert_not_called()


def test_read_new__entry_without_data_field__parked_as_malformed(mocker):

    """ A record somebody wrote by hand without the data field is
        not an event: KeyError, parked with its raw fields. """

    # arrange
    client_mock = mocker.Mock()
    client_mock.xreadgroup.return_value = [
        ('pneumatic:events-unit', [('1-0', {'type': 'user.login'})]),
    ]
    pipeline_mock = mocker.Mock()
    pipeline_mock.execute.return_value = [1]
    client_mock.pipeline.return_value = pipeline_mock
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()

    # act
    result = stream.read_new(consumer='consumer-1', count=5)

    # assert
    assert result == ParsedEntries(
        malformed=[('1-0', {'type': 'user.login'})],
    )
    client_mock.xreadgroup.assert_called_once_with(
        groupname='otlp',
        consumername='consumer-1',
        streams={'pneumatic:events-unit': NEW_ENTRIES},
        count=5,
    )
    client_mock.pipeline.assert_called_once_with(transaction=True)
    pipeline_mock.xadd.assert_called_once_with(
        name='pneumatic:events-unit:dead',
        fields={
            'type': 'user.login',
            'reason': MALFORMED_REASON,
            'source_id': '1-0',
            'data': json.dumps({'type': 'user.login'}),
        },
        maxlen=DEAD_MAXLEN,
        approximate=True,
    )
    pipeline_mock.xack.assert_called_once_with(
        'pneumatic:events-unit', 'otlp', '1-0',
    )
    pipeline_mock.execute.assert_called_once_with()
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_read_new__data_that_is_not_an_object__parked_as_malformed(
    mocker,
):

    """ Valid JSON that is not a mapping: Event.from_dict raises
        TypeError on a list, and the record is parked. """

    # arrange
    client_mock = mocker.Mock()
    client_mock.xreadgroup.return_value = [
        ('pneumatic:events-unit', [('1-0', {'data': '[]'})]),
    ]
    pipeline_mock = mocker.Mock()
    pipeline_mock.execute.return_value = [1]
    client_mock.pipeline.return_value = pipeline_mock
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()

    # act
    result = stream.read_new(consumer='consumer-1', count=5)

    # assert
    assert result == ParsedEntries(malformed=[('1-0', {'data': '[]'})])
    client_mock.xreadgroup.assert_called_once_with(
        groupname='otlp',
        consumername='consumer-1',
        streams={'pneumatic:events-unit': NEW_ENTRIES},
        count=5,
    )
    client_mock.pipeline.assert_called_once_with(transaction=True)
    pipeline_mock.xadd.assert_called_once_with(
        name='pneumatic:events-unit:dead',
        fields={
            'type': '',
            'reason': MALFORMED_REASON,
            'source_id': '1-0',
            'data': json.dumps({'data': '[]'}),
        },
        maxlen=DEAD_MAXLEN,
        approximate=True,
    )
    pipeline_mock.xack.assert_called_once_with(
        'pneumatic:events-unit', 'otlp', '1-0',
    )
    pipeline_mock.execute.assert_called_once_with()
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_read_new__vanished_and_malformed_in_one_answer__both_cleared(
    mocker,
):

    """ The trimmed record is acked, the broken one parked, the good
        one delivered: three kinds in one answer. """

    # arrange
    event = make_event()
    client_mock = mocker.Mock()
    client_mock.xreadgroup.return_value = [(
        'pneumatic:events-unit',
        [
            ('1-0', {}),
            ('2-0', {'data': 'not json'}),
            (
                '3-0',
                {
                    'type': 'workflow.run',
                    'data': json.dumps(
                        event.to_dict(),
                        cls=DjangoJSONEncoder,
                    ),
                },
            ),
        ],
    )]
    client_mock.xack.return_value = 1
    pipeline_mock = mocker.Mock()
    pipeline_mock.execute.return_value = [1]
    client_mock.pipeline.return_value = pipeline_mock
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()

    # act
    result = stream.read_new(consumer='consumer-1', count=5)

    # assert
    assert len(result.events) == 1
    assert result.events[0][0] == '3-0'
    assert result.vanished == ['1-0']
    assert result.malformed == [('2-0', {'data': 'not json'})]
    client_mock.xack.assert_called_once_with(
        'pneumatic:events-unit', 'otlp', '1-0',
    )
    client_mock.pipeline.assert_called_once_with(transaction=True)
    pipeline_mock.xadd.assert_called_once_with(
        name='pneumatic:events-unit:dead',
        fields={
            'type': '',
            'reason': MALFORMED_REASON,
            'source_id': '2-0',
            'data': json.dumps({'data': 'not json'}),
        },
        maxlen=DEAD_MAXLEN,
        approximate=True,
    )
    pipeline_mock.xack.assert_called_once_with(
        'pneumatic:events-unit', 'otlp', '2-0',
    )
    pipeline_mock.execute.assert_called_once_with()
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_read_new__type_not_string__only_that_entry_parked(mocker):

    """ A record with a number for the type passes Event.from_dict:
        it has to be parked alone instead of breaking the whole batch
        in the sink. """

    # arrange
    good = make_event()
    broken = make_event().to_dict()
    broken['type'] = 5
    client_mock = mocker.Mock()
    client_mock.xreadgroup.return_value = [(
        'pneumatic:events-unit',
        [
            ('1-0', {'data': json.dumps(broken)}),
            (
                '2-0',
                {
                    'type': 'workflow.run',
                    'data': json.dumps(
                        good.to_dict(),
                        cls=DjangoJSONEncoder,
                    ),
                },
            ),
        ],
    )]
    pipeline_mock = mocker.Mock()
    pipeline_mock.execute.return_value = [1]
    client_mock.pipeline.return_value = pipeline_mock
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=client_mock,
    )
    stream = make_unit_stream()

    # act
    result = stream.read_new(consumer='consumer-1', count=5)

    # assert
    assert len(result.events) == 1
    assert result.events[0][0] == '2-0'
    assert result.malformed == [('1-0', {'data': json.dumps(broken)})]
    client_mock.pipeline.assert_called_once_with(transaction=True)
    pipeline_mock.xadd.assert_called_once_with(
        name='pneumatic:events-unit:dead',
        fields={
            'type': '',
            'reason': MALFORMED_REASON,
            'source_id': '1-0',
            'data': json.dumps({'data': json.dumps(broken)}),
        },
        maxlen=DEAD_MAXLEN,
        approximate=True,
    )
    pipeline_mock.xack.assert_called_once_with(
        'pneumatic:events-unit', 'otlp', '1-0',
    )
    pipeline_mock.execute.assert_called_once_with()
    client_mock.xack.assert_not_called()
    from_url_mock.assert_called_once_with(
        'redis://localhost:6379/4',
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_to_event__valid_record__event_with_the_stream_id():

    # arrange
    event = make_event()
    fields = {'data': json.dumps(event.to_dict(), cls=DjangoJSONEncoder)}

    # act
    result = _to_event(entry_id='1-0', fields=fields)

    # assert
    assert result.id == '1-0'
    assert result.type == 'workflow.run'
    assert result.account_id == 42


def test_to_event__type_not_string__none():

    # arrange
    data = make_event().to_dict()
    data['type'] = 5
    fields = {'data': json.dumps(data)}

    # act
    result = _to_event(entry_id='1-0', fields=fields)

    # assert
    assert result is None


def test_to_event__category_not_string__none():

    # arrange
    data = make_event().to_dict()
    data['category'] = ['users']
    fields = {'data': json.dumps(data)}

    # act
    result = _to_event(entry_id='1-0', fields=fields)

    # assert
    assert result is None


def test_to_event__service_not_string__none():

    # arrange
    data = make_event().to_dict()
    data['service'] = None
    fields = {'data': json.dumps(data)}

    # act
    result = _to_event(entry_id='1-0', fields=fields)

    # assert
    assert result is None


def test_to_event__account_id_not_integer__none():

    # arrange
    data = make_event().to_dict()
    data['account_id'] = '42'
    fields = {'data': json.dumps(data)}

    # act
    result = _to_event(entry_id='1-0', fields=fields)

    # assert
    assert result is None


def test_to_event__payload_not_object__none():

    # arrange
    data = make_event().to_dict()
    data['payload'] = ['template_id']
    fields = {'data': json.dumps(data)}

    # act
    result = _to_event(entry_id='1-0', fields=fields)

    # assert
    assert result is None
