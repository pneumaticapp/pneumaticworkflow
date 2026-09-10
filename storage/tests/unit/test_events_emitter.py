"""Tests for the writer of the event stream."""

import asyncio
import logging
from unittest.mock import AsyncMock, call

import pytest

from src.shared_kernel.events.emitter import (
    CIRCUIT_OPEN_SECONDS,
    CONNECT_TIMEOUT,
    SOCKET_TIMEOUT,
    EventEmitter,
    close_event_emitter,
    get_event_emitter,
)
from tests.fixtures.unit import (
    EMITTER_MAXLEN,
    EMITTER_REDIS_HOST,
    EMITTER_REDIS_PASSWORD,
    EMITTER_REDIS_URL,
    EMITTER_STREAM_KEY,
)


@pytest.mark.asyncio
async def test_emit__enabled__record_written(
    events_emitter,
    mock_events_redis_from_url,
    sample_event,
    sample_stream_fields,
):
    # arrange
    client_mock = AsyncMock()
    mock_events_redis_from_url.return_value = client_mock

    # act
    await events_emitter.emit(sample_event)

    # assert
    mock_events_redis_from_url.assert_called_once_with(
        EMITTER_REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=CONNECT_TIMEOUT,
        socket_timeout=SOCKET_TIMEOUT,
    )
    client_mock.xadd.assert_awaited_once_with(
        name=EMITTER_STREAM_KEY,
        fields=sample_stream_fields,
        maxlen=EMITTER_MAXLEN,
        approximate=True,
    )


@pytest.mark.asyncio
async def test_emit__disabled__redis_untouched(
    mock_events_redis_from_url,
    sample_event,
):
    # arrange
    emitter = EventEmitter(
        url=EMITTER_REDIS_URL,
        key=EMITTER_STREAM_KEY,
        maxlen=EMITTER_MAXLEN,
        enabled=False,
    )

    # act
    await emitter.emit(sample_event)

    # assert
    mock_events_redis_from_url.assert_not_called()


@pytest.mark.asyncio
async def test_emit__write_failed__circuit_open_and_no_raise(
    events_emitter,
    mock_events_redis_from_url,
    mock_emitter_now,
    sample_event,
    sample_stream_fields,
    caplog,
):
    # arrange
    caplog.set_level(logging.WARNING)
    client_mock = AsyncMock()
    client_mock.xadd.side_effect = ConnectionError('refused')
    mock_events_redis_from_url.return_value = client_mock
    mock_emitter_now.return_value = 100.0

    # act
    await events_emitter.emit(sample_event)

    # assert
    assert events_emitter.circuit.open_until == 100.0 + CIRCUIT_OPEN_SECONDS
    assert events_emitter.circuit.is_open(100.0 + CIRCUIT_OPEN_SECONDS - 1)
    client_mock.xadd.assert_awaited_once_with(
        name=EMITTER_STREAM_KEY,
        fields=sample_stream_fields,
        maxlen=EMITTER_MAXLEN,
        approximate=True,
    )
    mock_emitter_now.assert_called_once_with()
    assert caplog.messages == [
        'Events stream is unavailable, events are dropped: ConnectionError',
    ]


@pytest.mark.asyncio
async def test_emit__write_failed__password_not_logged(
    events_emitter,
    mock_events_redis_from_url,
    mock_emitter_now,
    sample_event,
    sample_stream_fields,
    caplog,
):
    # arrange
    caplog.set_level(logging.WARNING)
    client_mock = AsyncMock()
    client_mock.xadd.side_effect = ConnectionError(EMITTER_REDIS_URL)
    mock_events_redis_from_url.return_value = client_mock
    mock_emitter_now.return_value = 100.0

    # act
    await events_emitter.emit(sample_event)

    # assert
    assert EMITTER_REDIS_PASSWORD not in caplog.text
    client_mock.xadd.assert_awaited_once_with(
        name=EMITTER_STREAM_KEY,
        fields=sample_stream_fields,
        maxlen=EMITTER_MAXLEN,
        approximate=True,
    )
    mock_emitter_now.assert_called_once_with()


@pytest.mark.asyncio
async def test_emit__write_failed__host_not_logged(
    events_emitter,
    mock_events_redis_from_url,
    mock_emitter_now,
    sample_event,
    sample_stream_fields,
    caplog,
):
    # arrange
    caplog.set_level(logging.WARNING)
    client_mock = AsyncMock()
    client_mock.xadd.side_effect = ConnectionError(EMITTER_REDIS_URL)
    mock_events_redis_from_url.return_value = client_mock
    mock_emitter_now.return_value = 100.0

    # act
    await events_emitter.emit(sample_event)

    # assert
    assert EMITTER_REDIS_HOST not in caplog.text
    client_mock.xadd.assert_awaited_once_with(
        name=EMITTER_STREAM_KEY,
        fields=sample_stream_fields,
        maxlen=EMITTER_MAXLEN,
        approximate=True,
    )
    mock_emitter_now.assert_called_once_with()


@pytest.mark.asyncio
async def test_emit__circuit_open__dropped_not_written(
    events_emitter,
    mock_events_redis_from_url,
    mock_emitter_now,
    sample_event,
    sample_stream_fields,
):
    # arrange
    client_mock = AsyncMock()
    client_mock.xadd.side_effect = [ConnectionError('refused'), None]
    mock_events_redis_from_url.return_value = client_mock
    mock_emitter_now.side_effect = [100.0, 101.0]

    # act
    await events_emitter.emit(sample_event)
    await events_emitter.emit(sample_event)

    # assert
    client_mock.xadd.assert_awaited_once_with(
        name=EMITTER_STREAM_KEY,
        fields=sample_stream_fields,
        maxlen=EMITTER_MAXLEN,
        approximate=True,
    )
    assert events_emitter.circuit.dropped == 1
    assert mock_emitter_now.call_count == 2


@pytest.mark.asyncio
async def test_emit__window_passed__written_and_recovery_logged(
    events_emitter,
    mock_events_redis_from_url,
    mock_emitter_now,
    sample_event,
    sample_stream_fields,
    caplog,
):
    # arrange
    caplog.set_level(logging.WARNING)
    client_mock = AsyncMock()
    client_mock.xadd.side_effect = [ConnectionError('refused'), None]
    mock_events_redis_from_url.return_value = client_mock
    mock_emitter_now.side_effect = [
        100.0,
        101.0,
        100.0 + CIRCUIT_OPEN_SECONDS,
    ]

    # act
    await events_emitter.emit(sample_event)
    await events_emitter.emit(sample_event)
    await events_emitter.emit(sample_event)

    # assert
    assert client_mock.xadd.await_count == 2
    client_mock.xadd.assert_has_awaits(
        [
            call(
                name=EMITTER_STREAM_KEY,
                fields=sample_stream_fields,
                maxlen=EMITTER_MAXLEN,
                approximate=True,
            ),
            call(
                name=EMITTER_STREAM_KEY,
                fields=sample_stream_fields,
                maxlen=EMITTER_MAXLEN,
                approximate=True,
            ),
        ]
    )
    assert events_emitter.circuit.dropped == 0
    assert mock_emitter_now.call_count == 3
    assert caplog.messages == [
        'Events stream is unavailable, events are dropped: ConnectionError',
        'Events stream is back, events dropped meanwhile: 1',
    ]


@pytest.mark.asyncio
async def test_emit__write_hangs__timeout_opens_circuit(
    events_emitter,
    mock_events_redis_from_url,
    mock_emitter_now,
    sample_event,
    sample_stream_fields,
    caplog,
):
    # arrange
    caplog.set_level(logging.WARNING)

    async def hang(**_kwargs):
        await asyncio.sleep(1)

    client_mock = AsyncMock()
    client_mock.xadd.side_effect = hang
    mock_events_redis_from_url.return_value = client_mock
    mock_emitter_now.return_value = 100.0
    events_emitter.timeout = 0.01

    # act
    await events_emitter.emit(sample_event)

    # assert
    assert events_emitter.circuit.is_open(100.0)
    client_mock.xadd.assert_awaited_once_with(
        name=EMITTER_STREAM_KEY,
        fields=sample_stream_fields,
        maxlen=EMITTER_MAXLEN,
        approximate=True,
    )
    mock_emitter_now.assert_called_once_with()
    assert caplog.messages == [
        'Events stream is unavailable, events are dropped: TimeoutError',
    ]


@pytest.mark.asyncio
async def test_emit__healthy_stream__nothing_logged(
    events_emitter,
    mock_events_redis_from_url,
    sample_event,
    sample_stream_fields,
    caplog,
):
    # arrange
    caplog.set_level(logging.WARNING)
    client_mock = AsyncMock()
    mock_events_redis_from_url.return_value = client_mock

    # act
    await events_emitter.emit(sample_event)

    # assert
    assert caplog.messages == []
    client_mock.xadd.assert_awaited_once_with(
        name=EMITTER_STREAM_KEY,
        fields=sample_stream_fields,
        maxlen=EMITTER_MAXLEN,
        approximate=True,
    )


@pytest.mark.asyncio
async def test_close__client_opened__pool_closed(
    events_emitter,
    mock_events_redis_from_url,
    sample_event,
    sample_stream_fields,
):
    # arrange
    client_mock = AsyncMock()
    mock_events_redis_from_url.return_value = client_mock
    await events_emitter.emit(sample_event)

    # act
    await events_emitter.close()

    # assert
    client_mock.aclose.assert_awaited_once_with()
    client_mock.xadd.assert_awaited_once_with(
        name=EMITTER_STREAM_KEY,
        fields=sample_stream_fields,
        maxlen=EMITTER_MAXLEN,
        approximate=True,
    )


@pytest.mark.asyncio
async def test_close__never_opened__nothing_to_close(
    events_emitter,
    mock_events_redis_from_url,
):
    # act
    await events_emitter.close()

    # assert
    mock_events_redis_from_url.assert_not_called()


def test_get_event_emitter__called_twice__same_instance(
    clear_event_emitter_cache,
    mock_emitter_settings,
):
    # arrange
    mock_emitter_settings.return_value.LOGS_REDIS_URL = EMITTER_REDIS_URL
    mock_emitter_settings.return_value.LOGS_STREAM_KEY = EMITTER_STREAM_KEY
    mock_emitter_settings.return_value.LOGS_STREAM_MAXLEN = EMITTER_MAXLEN
    mock_emitter_settings.return_value.logs_enabled = True

    # act
    first = get_event_emitter()
    second = get_event_emitter()

    # assert
    assert first is second
    mock_emitter_settings.assert_called_once_with()


@pytest.mark.asyncio
async def test_close_event_emitter__cached__closed_and_forgotten(
    clear_event_emitter_cache,
    mock_emitter_settings,
    mock_events_redis_from_url,
    sample_event,
    sample_stream_fields,
):
    # arrange
    mock_emitter_settings.return_value.LOGS_REDIS_URL = EMITTER_REDIS_URL
    mock_emitter_settings.return_value.LOGS_STREAM_KEY = EMITTER_STREAM_KEY
    mock_emitter_settings.return_value.LOGS_STREAM_MAXLEN = EMITTER_MAXLEN
    mock_emitter_settings.return_value.logs_enabled = True
    client_mock = AsyncMock()
    mock_events_redis_from_url.return_value = client_mock
    first = get_event_emitter()
    await first.emit(sample_event)

    # act
    await close_event_emitter()

    # assert
    client_mock.aclose.assert_awaited_once_with()
    assert get_event_emitter() is not first
    assert mock_emitter_settings.call_count == 2
    client_mock.xadd.assert_awaited_once_with(
        name=EMITTER_STREAM_KEY,
        fields=sample_stream_fields,
        maxlen=EMITTER_MAXLEN,
        approximate=True,
    )
