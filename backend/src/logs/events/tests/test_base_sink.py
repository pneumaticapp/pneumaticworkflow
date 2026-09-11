import pytest

from src.logs.events.exceptions import (
    SinkPermanentError,
    SinkTemporaryError,
)
from src.logs.events.tests.fakes import FakeSink, make_event


def test_send__no_records__nothing_sent():

    # arrange
    sink = FakeSink()

    # act
    sink.send([])

    # assert
    assert sink.handled == []


def test_send__records_delivered__no_error():

    # arrange
    sink = FakeSink()
    records = [('1-0', make_event())]

    # act
    sink.send(records)

    # assert
    assert sink.handled == []


def test_send__transport_error__classified_by_the_subclass():

    # arrange
    error = OSError('connection reset')
    sink = FakeSink(error=error)
    records = [('1-0', make_event())]

    # act
    with pytest.raises(SinkTemporaryError) as ex:
        sink.send(records)

    # assert
    assert str(ex.value) == 'connection reset'
    assert sink.handled == [error]


def test_send__handler_returns__temporary_error_raised():

    """ A subclass whose _handle_error returns instead of raising
        would have the consumer ack records nobody received. """

    # arrange
    error = OSError('connection reset')
    sink = FakeSink(error=error, classify=False)
    records = [('1-0', make_event())]

    # act
    with pytest.raises(SinkTemporaryError) as ex:
        sink.send(records)

    # assert
    assert str(ex.value) == (
        'FakeSink did not classify the delivery error: '
        "OSError('connection reset')"
    )
    assert sink.handled == [error]


def test_send__handler_returns__original_error_kept_as_cause():

    # arrange
    error = OSError('connection reset')
    sink = FakeSink(error=error, classify=False)
    records = [('1-0', make_event())]

    # act
    with pytest.raises(SinkTemporaryError) as ex:
        sink.send(records)

    # assert
    assert ex.value.__cause__ is error


def test_send__permanent_error_from_the_handler__not_wrapped():

    """ The template method must let a classified error through
        untouched, whichever of the two it is. """

    # arrange
    sink = FakeSink(
        error=OSError('bad batch'),
        raises=SinkPermanentError('rejected for good'),
    )
    records = [('1-0', make_event())]

    # act
    with pytest.raises(SinkPermanentError) as ex:
        sink.send(records)

    # assert
    assert str(ex.value) == 'rejected for good'
