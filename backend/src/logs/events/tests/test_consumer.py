import logging

from src.logs.events.consumer import (
    LOCK_EXPIRE,
    EventsConsumer,
    tick_budget,
)
from src.logs.events.exceptions import (
    SinkPermanentError,
    SinkTemporaryError,
)
from src.logs.events.tests.fakes import FakeEventStream, fill_stream


def test_tick_budget__otlp_timeouts__lock_minus_the_worst_batch():

    """ Three sends of 13.05 s with two pauses of the longest
        Retry-After between them: 120 - 59.15 s. """

    # act
    budget = tick_budget(send_seconds=13.05, max_retry_after=10)

    # assert
    assert round(budget, 2) == 60.85
    assert budget < LOCK_EXPIRE


def test_tick_budget__short_retry_after__backoff_pause_used():

    """ The receiver cannot shorten the pause below the fixed
        backoff: the worst pause is the longer of the two. """

    # act
    budget = tick_budget(send_seconds=1, max_retry_after=0)

    # assert
    assert budget == 115.0


def test_tick_budget__batch_longer_than_the_lock__zero():

    # act
    budget = tick_budget(send_seconds=100, max_retry_after=10)

    # assert
    assert budget == 0.0


def test_tick_budget__given_lock_expire__used():

    # act
    budget = tick_budget(send_seconds=1, max_retry_after=0, lock_expire=10)

    # assert
    assert budget == 5.0


def test_run_once__new_entries__delivered_and_acked(mocker):

    # arrange
    stream = FakeEventStream()
    fill_stream(stream, count=3)
    sink_mock = mocker.Mock()
    sleep_mock = mocker.Mock()
    consumer = EventsConsumer(
        stream=stream,
        sink=sink_mock,
        batch_size=1000,
        consumer='consumer-1',
        sleep=sleep_mock,
    )

    # act
    stats = consumer.run_once()

    # assert
    assert stats.delivered == 3
    assert stats.acked == 3
    assert stats.dead == 0
    assert stats.claimed == 0
    assert stats.failed is False
    assert stream.group_created is True
    assert stream.pending == {}
    sink_mock.send.assert_called_once_with(stream.events)
    sleep_mock.assert_not_called()


def test_run_once__empty_stream__nothing_sent(mocker):

    # arrange
    stream = FakeEventStream()
    sink_mock = mocker.Mock()
    sleep_mock = mocker.Mock()
    consumer = EventsConsumer(
        stream=stream,
        sink=sink_mock,
        consumer='consumer-1',
        sleep=sleep_mock,
    )

    # act
    stats = consumer.run_once()

    # assert
    assert stats.delivered == 0
    assert stats.acked == 0
    assert stats.failed is False
    assert stream.group_created is True
    sink_mock.send.assert_not_called()
    sleep_mock.assert_not_called()


def test_run_once__more_than_one_batch__batches_of_the_count(mocker):

    # arrange
    stream = FakeEventStream()
    fill_stream(stream, count=2500)
    sink_mock = mocker.Mock()
    sleep_mock = mocker.Mock()
    consumer = EventsConsumer(
        stream=stream,
        sink=sink_mock,
        batch_size=1000,
        consumer='consumer-1',
        sleep=sleep_mock,
    )

    # act
    stats = consumer.run_once()

    # assert
    assert sink_mock.send.call_count == 3
    sink_mock.send.assert_has_calls([
        mocker.call(stream.events[:1000]),
        mocker.call(stream.events[1000:2000]),
        mocker.call(stream.events[2000:]),
    ])
    assert stats.delivered == 2500
    assert stats.acked == 2500
    assert stats.failed is False
    assert stream.pending == {}
    sleep_mock.assert_not_called()


def test_run_once__max_batches__rest_of_the_stream_untouched(mocker):

    # arrange
    stream = FakeEventStream()
    fill_stream(stream, count=300)
    sink_mock = mocker.Mock()
    sleep_mock = mocker.Mock()
    consumer = EventsConsumer(
        stream=stream,
        sink=sink_mock,
        batch_size=100,
        max_batches=2,
        consumer='consumer-1',
        sleep=sleep_mock,
    )

    # act
    stats = consumer.run_once()

    # assert
    assert stats.delivered == 200
    assert stats.acked == 200
    assert sink_mock.send.call_count == 2
    sink_mock.send.assert_has_calls([
        mocker.call(stream.events[:100]),
        mocker.call(stream.events[100:200]),
    ])
    assert stream.pending == {}
    sleep_mock.assert_not_called()


def test_run_once__deadline_reached__nothing_delivered(mocker):

    """ The tick has to be over before the periodic lock expires, or
        beat starts a second tick next to this one. """

    # arrange
    stream = FakeEventStream()
    fill_stream(stream, count=3)
    sink_mock = mocker.Mock()
    sleep_mock = mocker.Mock()
    consumer = EventsConsumer(
        stream=stream,
        sink=sink_mock,
        consumer='consumer-1',
        sleep=sleep_mock,
        max_seconds=0,
    )

    # act
    stats = consumer.run_once()

    # assert
    assert stats.delivered == 0
    assert stream.pending == {}
    sink_mock.send.assert_not_called()
    sleep_mock.assert_not_called()


def test_run_once__temporary_error__attempts_and_entries_pending(mocker):

    # arrange
    stream = FakeEventStream()
    fill_stream(stream, count=3)
    sink_mock = mocker.Mock()
    sink_mock.send.side_effect = SinkTemporaryError('collector is down')
    sleep_mock = mocker.Mock()
    consumer = EventsConsumer(
        stream=stream,
        sink=sink_mock,
        batch_size=1000,
        consumer='consumer-1',
        sleep=sleep_mock,
    )

    # act
    stats = consumer.run_once()

    # assert
    assert sink_mock.send.call_count == 3
    sink_mock.send.assert_has_calls([
        mocker.call(stream.events),
        mocker.call(stream.events),
        mocker.call(stream.events),
    ])
    assert sleep_mock.call_count == 2
    sleep_mock.assert_has_calls([mocker.call(0.5), mocker.call(1.0)])
    assert stats.delivered == 0
    assert stats.acked == 0
    assert stats.failed is True
    assert len(stream.pending) == 3


def test_run_once__retry_after__pause_of_the_receiver_is_used(mocker):

    # arrange
    stream = FakeEventStream()
    fill_stream(stream, count=1)
    error = SinkTemporaryError('too many requests')
    error.retry_after = 3
    sink_mock = mocker.Mock()
    sink_mock.send.side_effect = error
    sleep_mock = mocker.Mock()
    consumer = EventsConsumer(
        stream=stream,
        sink=sink_mock,
        consumer='consumer-1',
        sleep=sleep_mock,
    )

    # act
    stats = consumer.run_once()

    # assert
    assert sleep_mock.call_count == 2
    sleep_mock.assert_has_calls([mocker.call(3), mocker.call(3)])
    assert sink_mock.send.call_count == 3
    sink_mock.send.assert_has_calls([
        mocker.call(stream.events),
        mocker.call(stream.events),
        mocker.call(stream.events),
    ])
    assert stats.failed is True
    assert len(stream.pending) == 1


def test_run_once__healthy_sink_after_failure__pending_delivered(mocker):

    # arrange
    stream = FakeEventStream()
    fill_stream(stream, count=3)
    sink_mock = mocker.Mock()
    sink_mock.send.side_effect = SinkTemporaryError('collector is down')
    sleep_mock = mocker.Mock()
    consumer = EventsConsumer(
        stream=stream,
        sink=sink_mock,
        batch_size=1000,
        consumer='consumer-1',
        sleep=sleep_mock,
    )
    failed_stats = consumer.run_once()
    sink_mock.send.side_effect = None

    # act
    stats = consumer.run_once()

    # assert
    assert failed_stats.failed is True
    assert stats.delivered == 3
    assert stats.acked == 3
    assert stats.claimed == 0
    assert stats.failed is False
    assert sink_mock.send.call_count == 4
    sink_mock.send.assert_has_calls([
        mocker.call(stream.events),
        mocker.call(stream.events),
        mocker.call(stream.events),
        mocker.call(stream.events),
    ])
    assert sleep_mock.call_count == 2
    sleep_mock.assert_has_calls([mocker.call(0.5), mocker.call(1.0)])
    assert stream.pending == {}


def test_run_once__permanent_error__batch_dead_lettered(mocker):

    # arrange
    stream = FakeEventStream()
    fill_stream(stream, count=2)
    sink_mock = mocker.Mock()
    sink_mock.send.side_effect = SinkPermanentError('400 bad request')
    sleep_mock = mocker.Mock()
    consumer = EventsConsumer(
        stream=stream,
        sink=sink_mock,
        batch_size=1000,
        consumer='consumer-1',
        sleep=sleep_mock,
    )

    # act
    stats = consumer.run_once()

    # assert
    assert stats.dead == 2
    assert stats.acked == 2
    assert stats.delivered == 0
    assert stats.failed is False
    assert len(stream.dead) == 2
    assert stream.dead[0][0] == '1-0'
    assert stream.dead[0][2] == 'rejected'
    assert stream.dead[1][0] == '2-0'
    assert stream.dead[1][2] == 'rejected'
    assert stream.pending == {}
    sink_mock.send.assert_called_once_with(stream.events)
    sleep_mock.assert_not_called()


def test_run_once__permanent_error__next_batches_left_in_the_stream(
    mocker,
):

    """ The reason is usually the receiver, not the batch: carrying
        the rest into the dead letter at full speed would lose it. """

    # arrange
    stream = FakeEventStream()
    fill_stream(stream, count=300)
    sink_mock = mocker.Mock()
    sink_mock.send.side_effect = SinkPermanentError('400 bad request')
    sleep_mock = mocker.Mock()
    consumer = EventsConsumer(
        stream=stream,
        sink=sink_mock,
        batch_size=100,
        consumer='consumer-1',
        sleep=sleep_mock,
    )

    # act
    stats = consumer.run_once()

    # assert
    assert stats.dead == 100
    assert len(stream.dead) == 100
    sink_mock.send.assert_called_once_with(stream.events[:100])
    sleep_mock.assert_not_called()


def test_run_once__idle_entries_of_a_dead_consumer__claimed(mocker):

    # arrange
    stream = FakeEventStream()
    fill_stream(stream, count=3)
    abandoned = stream.read_new(consumer='dead-consumer', count=1000)
    for entry in stream.pending.values():
        entry.delivered_at -= 120
    sink_mock = mocker.Mock()
    sleep_mock = mocker.Mock()
    consumer = EventsConsumer(
        stream=stream,
        sink=sink_mock,
        batch_size=1000,
        idle_ms=60000,
        consumer='consumer-1',
        sleep=sleep_mock,
    )

    # act
    stats = consumer.run_once()

    # assert
    assert len(abandoned) == 3
    assert stats.claimed == 3
    assert stats.delivered == 3
    assert stats.acked == 3
    assert stats.failed is False
    assert stream.pending == {}
    sink_mock.send.assert_called_once_with(stream.events)
    sleep_mock.assert_not_called()


def test_run_once__fresh_entries_of_another_consumer__not_claimed(mocker):

    """ The idle timeout is longer than the longest tick, so a living
        consumer never loses its entries to another one. """

    # arrange
    stream = FakeEventStream()
    fill_stream(stream, count=1)
    stream.read_new(consumer='consumer-2', count=1000)
    sink_mock = mocker.Mock()
    sleep_mock = mocker.Mock()
    consumer = EventsConsumer(
        stream=stream,
        sink=sink_mock,
        idle_ms=60000,
        consumer='consumer-1',
        sleep=sleep_mock,
    )

    # act
    stats = consumer.run_once()

    # assert
    assert stats.claimed == 0
    assert stats.delivered == 0
    assert stats.acked == 0
    assert len(stream.pending) == 1
    sink_mock.send.assert_not_called()
    sleep_mock.assert_not_called()


def test_run_once__delivered_batch__tick_line_in_the_log(mocker, caplog):

    # arrange
    caplog.set_level(logging.INFO, logger='pneumatic.events.consumer')
    stream = FakeEventStream()
    fill_stream(stream, count=3)
    sink_mock = mocker.Mock()
    sleep_mock = mocker.Mock()
    consumer = EventsConsumer(
        stream=stream,
        sink=sink_mock,
        consumer='consumer-1',
        sleep=sleep_mock,
    )

    # act
    stats = consumer.run_once()

    # assert
    assert caplog.messages == [
        f'delivered=3 acked=3 dead=0 claimed=0 in {stats.duration_ms} ms',
    ]
    sink_mock.send.assert_called_once_with(stream.events)
    sleep_mock.assert_not_called()


def test_init__no_consumer_name__host_name(mocker):

    # arrange
    consumer_name_mock = mocker.patch(
        'src.logs.events.consumer.consumer_name',
        return_value='worker-1',
    )

    # act
    consumer = EventsConsumer(
        stream=FakeEventStream(),
        sink=mocker.Mock(),
    )

    # assert
    assert consumer.consumer == 'worker-1'
    consumer_name_mock.assert_called_once_with()


def test_run_once__temporary_error_with_more_batches__tick_ends(mocker):

    """ A batch given up on ends the tick: the batches behind it wait
        for the next one instead of being sent to a receiver that has
        just refused three times. """

    # arrange
    stream = FakeEventStream()
    fill_stream(stream, count=3)
    sink_mock = mocker.Mock()
    sink_mock.send.side_effect = SinkTemporaryError('collector is down')
    sleep_mock = mocker.Mock()
    consumer = EventsConsumer(
        stream=stream,
        sink=sink_mock,
        batch_size=1,
        consumer='consumer-1',
        sleep=sleep_mock,
    )

    # act
    stats = consumer.run_once()

    # assert
    assert sink_mock.send.call_count == 3
    sink_mock.send.assert_has_calls([
        mocker.call(stream.events[:1]),
        mocker.call(stream.events[:1]),
        mocker.call(stream.events[:1]),
    ])
    assert stats.delivered == 0
    assert stats.failed is True
    assert len(stream.pending) == 1


def test_run_once__deadline_between_batches__rest_left_for_next_tick(
    mocker,
):

    """ The deadline is checked before every batch, not only before
        the first one: a slow receiver ends the tick after the batch
        in flight. """

    # arrange
    stream = FakeEventStream()
    fill_stream(stream, count=3)
    sink_mock = mocker.Mock()
    sleep_mock = mocker.Mock()
    # started, the check of the pending phase, of the claim phase, of
    # the first new batch, then late: the check of the second batch
    # and the end.
    mocker.patch(
        'src.logs.events.consumer.time.monotonic',
        side_effect=[0.0, 0.0, 0.0, 0.0, 100.0, 100.0],
    )
    consumer = EventsConsumer(
        stream=stream,
        sink=sink_mock,
        batch_size=1,
        consumer='consumer-1',
        sleep=sleep_mock,
        max_seconds=10,
    )

    # act
    stats = consumer.run_once()

    # assert
    assert stats.delivered == 1
    assert stats.acked == 1
    sink_mock.send.assert_called_once_with(stream.events[:1])
    assert len(stream.pending) == 0
    assert stats.duration_ms == 100000
