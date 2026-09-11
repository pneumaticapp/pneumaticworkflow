import json

import pytest
import redis

from src.logs.events.stream import (
    AUTOCLAIM_START,
    DEAD_MAXLEN,
    MALFORMED_REASON,
    NEW_ENTRIES,
    PENDING_ENTRIES,
)
from src.logs.events.tests.fakes import (
    UNIT_STREAM_DEAD_KEY,
    UNIT_STREAM_KEY,
    UNIT_STREAM_URL,
    dead_letter_pipeline,
    make_event,
    make_unit_stream,
    stream_fields,
)


def test_dead_key__any_stream__suffixed_key():

    # arrange
    stream = make_unit_stream()

    # act
    result = stream.dead_key

    # assert
    assert result == UNIT_STREAM_DEAD_KEY


def test_client__first_call__built_from_the_url(mocker):

    # arrange
    stream = make_unit_stream()
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=mocker.Mock(),
    )

    # act
    client = stream.client

    # assert
    assert client is from_url_mock.return_value
    from_url_mock.assert_called_once_with(
        UNIT_STREAM_URL,
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_client__called_twice__one_connection(mocker):

    # arrange
    stream = make_unit_stream()
    from_url_mock = mocker.patch(
        'src.logs.events.stream.redis.Redis.from_url',
        return_value=mocker.Mock(),
    )

    # act
    first = stream.client
    second = stream.client

    # assert
    assert first is second
    from_url_mock.assert_called_once_with(
        UNIT_STREAM_URL,
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )


def test_close__open_client__connection_released(mocker):

    # arrange
    stream = make_unit_stream()
    client_mock = mocker.Mock()
    stream._client = client_mock

    # act
    stream.close()

    # assert
    client_mock.close.assert_called_once_with()
    assert stream._client is None


def test_close__never_opened__nothing_happens():

    # arrange
    stream = make_unit_stream()

    # act
    stream.close()

    # assert
    assert stream._client is None


def test_xadd__event__written_with_the_trim(mocker):

    # arrange
    stream = make_unit_stream()
    client_mock = mocker.Mock()
    client_mock.xadd.return_value = '1-0'
    stream._client = client_mock
    event = make_event()

    # act
    result = stream.xadd(event)

    # assert
    assert result == '1-0'
    client_mock.xadd.assert_called_once_with(
        name=UNIT_STREAM_KEY,
        fields=stream_fields(event),
        maxlen=10,
        approximate=True,
    )


def test_ensure_group__new_stream__group_created(mocker):

    # arrange
    stream = make_unit_stream()
    client_mock = mocker.Mock()
    stream._client = client_mock

    # act
    stream.ensure_group()

    # assert
    client_mock.xgroup_create.assert_called_once_with(
        name=UNIT_STREAM_KEY,
        groupname='otlp',
        id='0',
        mkstream=True,
    )


def test_ensure_group__group_exists__error_swallowed(mocker):

    # arrange
    stream = make_unit_stream()
    client_mock = mocker.Mock()
    client_mock.xgroup_create.side_effect = redis.ResponseError(
        'BUSYGROUP Consumer Group name already exists',
    )
    stream._client = client_mock

    # act
    stream.ensure_group()

    # assert
    client_mock.xgroup_create.assert_called_once_with(
        name=UNIT_STREAM_KEY,
        groupname='otlp',
        id='0',
        mkstream=True,
    )


def test_ensure_group__other_response_error__raised(mocker):

    """ Only the "already exists" answer is expected; anything else
        is a broken stream and must not be hidden. """

    # arrange
    stream = make_unit_stream()
    client_mock = mocker.Mock()
    client_mock.xgroup_create.side_effect = redis.ResponseError(
        'WRONGTYPE Operation against a key',
    )
    stream._client = client_mock

    # act
    with pytest.raises(redis.ResponseError) as ex:
        stream.ensure_group()

    # assert
    assert str(ex.value) == 'WRONGTYPE Operation against a key'


def test_read_new__entries__events_with_their_ids(mocker):

    # arrange
    stream = make_unit_stream()
    event = make_event()
    client_mock = mocker.Mock()
    client_mock.xreadgroup.return_value = [
        (UNIT_STREAM_KEY, [('1-0', stream_fields(event))]),
    ]
    stream._client = client_mock

    # act
    result = stream.read_new(consumer='consumer-1', count=5)

    # assert
    assert len(result) == 1
    assert result[0][0] == '1-0'
    assert result[0][1].id == '1-0'
    assert result[0][1].type == event.type
    client_mock.xreadgroup.assert_called_once_with(
        groupname='otlp',
        consumername='consumer-1',
        streams={UNIT_STREAM_KEY: NEW_ENTRIES},
        count=5,
    )


def test_read_pending__entries__read_from_the_start(mocker):

    # arrange
    stream = make_unit_stream()
    client_mock = mocker.Mock()
    client_mock.xreadgroup.return_value = []
    stream._client = client_mock

    # act
    result = stream.read_pending(consumer='consumer-1', count=5)

    # assert
    assert result == []
    client_mock.xreadgroup.assert_called_once_with(
        groupname='otlp',
        consumername='consumer-1',
        streams={UNIT_STREAM_KEY: PENDING_ENTRIES},
        count=5,
    )


def test_read_new__no_answer__no_events(mocker):

    # arrange
    stream = make_unit_stream()
    client_mock = mocker.Mock()
    client_mock.xreadgroup.return_value = None
    stream._client = client_mock

    # act
    result = stream.read_new(consumer='consumer-1', count=5)

    # assert
    assert result == []


def test_read_new__entry_without_fields__acked_and_dropped(mocker):

    """ A record trimmed away while it was pending comes back with
        no fields: nothing can be delivered, the id is acked. """

    # arrange
    stream = make_unit_stream()
    client_mock = mocker.Mock()
    client_mock.xreadgroup.return_value = [(UNIT_STREAM_KEY, [('1-0', {})])]
    client_mock.xack.return_value = 1
    stream._client = client_mock

    # act
    result = stream.read_new(consumer='consumer-1', count=5)

    # assert
    assert result == []
    client_mock.xack.assert_called_once_with(UNIT_STREAM_KEY, 'otlp', '1-0')


def test_read_new__unparsable_entry__parked_in_the_dead_letter(mocker):

    # arrange
    stream = make_unit_stream()
    client_mock = mocker.Mock()
    client_mock.xreadgroup.return_value = [
        (UNIT_STREAM_KEY, [('1-0', {'data': 'not json'})]),
    ]
    pipe = dead_letter_pipeline(client_mock, acked=1)
    stream._client = client_mock

    # act
    result = stream.read_new(consumer='consumer-1', count=5)

    # assert
    assert result == []
    pipe.xadd.assert_called_once_with(
        name=UNIT_STREAM_DEAD_KEY,
        fields={
            'type': '',
            'reason': MALFORMED_REASON,
            'source_id': '1-0',
            'data': json.dumps({'data': 'not json'}),
        },
        maxlen=DEAD_MAXLEN,
        approximate=True,
    )
    pipe.xack.assert_called_once_with(UNIT_STREAM_KEY, 'otlp', '1-0')
    pipe.execute.assert_called_once_with()
    client_mock.xack.assert_not_called()


def test_autoclaim__redis_62_answer__entries_taken_over(mocker):

    # arrange
    stream = make_unit_stream()
    event = make_event()
    client_mock = mocker.Mock()
    client_mock.xautoclaim.return_value = [
        '0-0',
        [('1-0', stream_fields(event))],
    ]
    stream._client = client_mock

    # act
    result = stream.autoclaim(
        consumer='consumer-1',
        min_idle_ms=1000,
        count=5,
    )

    # assert
    assert len(result) == 1
    assert result[0][0] == '1-0'
    client_mock.xautoclaim.assert_called_once_with(
        name=UNIT_STREAM_KEY,
        groupname='otlp',
        consumername='consumer-1',
        min_idle_time=1000,
        start_id=AUTOCLAIM_START,
        count=5,
    )


def test_autoclaim__deleted_record_pair__dropped(mocker):

    """ Redis 6.2 answers a claimed record the stream no longer holds
        as a (None, None) pair. """

    # arrange
    stream = make_unit_stream()
    client_mock = mocker.Mock()
    client_mock.xautoclaim.return_value = ['0-0', [(None, None)]]
    stream._client = client_mock

    # act
    result = stream.autoclaim(
        consumer='consumer-1',
        min_idle_ms=1000,
        count=5,
    )

    # assert
    assert result == []
    client_mock.xack.assert_not_called()


def test_autoclaim__answer_without_entries__no_events(mocker):

    # arrange
    stream = make_unit_stream()
    client_mock = mocker.Mock()
    client_mock.xautoclaim.return_value = ['0-0']
    stream._client = client_mock

    # act
    result = stream.autoclaim(
        consumer='consumer-1',
        min_idle_ms=1000,
        count=5,
    )

    # assert
    assert result == []


def test_ack__ids__acked_in_one_call(mocker):

    # arrange
    stream = make_unit_stream()
    client_mock = mocker.Mock()
    client_mock.xack.return_value = 2
    stream._client = client_mock

    # act
    result = stream.ack(['1-0', '2-0'])

    # assert
    assert result == 2
    client_mock.xack.assert_called_once_with(
        UNIT_STREAM_KEY, 'otlp', '1-0', '2-0',
    )


def test_ack__no_ids__redis_not_called(mocker):

    # arrange
    stream = make_unit_stream()
    client_mock = mocker.Mock()
    stream._client = client_mock

    # act
    result = stream.ack([])

    # assert
    assert result == 0
    client_mock.xack.assert_not_called()


def test_dead_letter__event__parked_with_its_type(mocker):

    # arrange
    stream = make_unit_stream()
    event = make_event()
    client_mock = mocker.Mock()
    pipe = dead_letter_pipeline(client_mock, acked=1)
    stream._client = client_mock

    # act
    result = stream.dead_letter([('1-0', event)], reason='rejected')

    # assert
    assert result == 1
    client_mock.pipeline.assert_called_once_with(transaction=True)
    pipe.xadd.assert_called_once_with(
        name=UNIT_STREAM_DEAD_KEY,
        fields={
            'type': event.type,
            'reason': 'rejected',
            'source_id': '1-0',
            'data': json.dumps(event.to_dict()),
        },
        maxlen=DEAD_MAXLEN,
        approximate=True,
    )
    pipe.xack.assert_called_once_with(UNIT_STREAM_KEY, 'otlp', '1-0')
    pipe.execute.assert_called_once_with()


def test_dead_letter__raw_fields__parked_as_they_are(mocker):

    # arrange
    stream = make_unit_stream()
    client_mock = mocker.Mock()
    pipe = dead_letter_pipeline(client_mock, acked=1)
    stream._client = client_mock
    raw = {'type': 'user.login', 'data': 'broken'}

    # act
    result = stream.dead_letter([('1-0', raw)], reason='malformed')

    # assert
    assert result == 1
    pipe.xadd.assert_called_once_with(
        name=UNIT_STREAM_DEAD_KEY,
        fields={
            'type': 'user.login',
            'reason': 'malformed',
            'source_id': '1-0',
            'data': json.dumps(raw),
        },
        maxlen=DEAD_MAXLEN,
        approximate=True,
    )


def test_dead_letter__two_entries__one_pipeline(mocker):

    """ A rejected batch is as long as a delivered one: one round
        trip for all of it, the ack in the same transaction. """

    # arrange
    stream = make_unit_stream()
    first = make_event()
    second = make_event(type='user.login')
    client_mock = mocker.Mock()
    pipe = dead_letter_pipeline(client_mock, acked=2)
    stream._client = client_mock

    # act
    result = stream.dead_letter(
        [('1-0', first), ('2-0', second)], reason='rejected',
    )

    # assert
    assert result == 2
    client_mock.pipeline.assert_called_once_with(transaction=True)
    assert pipe.xadd.call_count == 2
    pipe.xack.assert_called_once_with(
        UNIT_STREAM_KEY, 'otlp', '1-0', '2-0',
    )
    pipe.execute.assert_called_once_with()


def test_dead_letter__no_entries__redis_not_called(mocker):

    # arrange
    stream = make_unit_stream()
    client_mock = mocker.Mock()
    stream._client = client_mock

    # act
    result = stream.dead_letter([], reason='rejected')

    # assert
    assert result == 0
    client_mock.pipeline.assert_not_called()


def test_read_new__entry_without_data_field__parked_as_malformed(mocker):

    """ A record somebody wrote by hand without the data field is
        not an event: KeyError, parked with its raw fields. """

    # arrange
    stream = make_unit_stream()
    client_mock = mocker.Mock()
    client_mock.xreadgroup.return_value = [
        (UNIT_STREAM_KEY, [('1-0', {'type': 'user.login'})]),
    ]
    pipe = dead_letter_pipeline(client_mock, acked=1)
    stream._client = client_mock

    # act
    result = stream.read_new(consumer='consumer-1', count=5)

    # assert
    assert result == []
    pipe.xadd.assert_called_once_with(
        name=UNIT_STREAM_DEAD_KEY,
        fields={
            'type': 'user.login',
            'reason': MALFORMED_REASON,
            'source_id': '1-0',
            'data': json.dumps({'type': 'user.login'}),
        },
        maxlen=DEAD_MAXLEN,
        approximate=True,
    )
    pipe.xack.assert_called_once_with(UNIT_STREAM_KEY, 'otlp', '1-0')


def test_read_new__data_that_is_not_an_object__parked_as_malformed(
    mocker,
):

    """ Valid JSON that is not a mapping: Event.from_dict raises
        TypeError on a list, and the record is parked. """

    # arrange
    stream = make_unit_stream()
    client_mock = mocker.Mock()
    client_mock.xreadgroup.return_value = [
        (UNIT_STREAM_KEY, [('1-0', {'data': '[]'})]),
    ]
    pipe = dead_letter_pipeline(client_mock, acked=1)
    stream._client = client_mock

    # act
    result = stream.read_new(consumer='consumer-1', count=5)

    # assert
    assert result == []
    pipe.xack.assert_called_once_with(UNIT_STREAM_KEY, 'otlp', '1-0')


def test_read_new__vanished_and_malformed_in_one_answer__both_cleared(
    mocker,
):

    """ The trimmed record is acked, the broken one parked, the good
        one delivered: three kinds in one answer. """

    # arrange
    stream = make_unit_stream()
    event = make_event()
    client_mock = mocker.Mock()
    client_mock.xreadgroup.return_value = [(
        UNIT_STREAM_KEY,
        [
            ('1-0', {}),
            ('2-0', {'data': 'not json'}),
            ('3-0', stream_fields(event)),
        ],
    )]
    client_mock.xack.return_value = 1
    pipe = dead_letter_pipeline(client_mock, acked=1)
    stream._client = client_mock

    # act
    result = stream.read_new(consumer='consumer-1', count=5)

    # assert
    assert [entry_id for entry_id, _ in result] == ['3-0']
    client_mock.xack.assert_called_once_with(UNIT_STREAM_KEY, 'otlp', '1-0')
    pipe.xack.assert_called_once_with(UNIT_STREAM_KEY, 'otlp', '2-0')
