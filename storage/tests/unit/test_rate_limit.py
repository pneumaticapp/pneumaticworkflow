"""Tests for rate limiting middleware."""

import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.requests import Request
from starlette.responses import Response

from src.shared_kernel.middleware.rate_limit import (
    _CLEANUP_INTERVAL_SECONDS,
    RateLimitMiddleware,
    _classify_route,
    _get_client_ip,
    _RateLimit,
    _SlidingWindow,
)


def test_classify_route__upload_post__upload():
    # act
    result = _classify_route('/upload', 'POST')

    # assert
    assert result == 'upload'


def test_classify_route__file_get__download():
    # act
    result = _classify_route(
        '/12345678-1234-5678-1234-567812345678',
        'GET',
    )

    # assert
    assert result == 'download'


def test_classify_route__upload_get__none():
    # act
    result = _classify_route('/upload', 'GET')

    # assert
    assert result is None


def test_classify_route__root_get__none():
    # act
    result = _classify_route('/', 'GET')

    # assert
    assert result is None


def test_classify_route__random_post__none():
    # act
    result = _classify_route('/random', 'POST')

    # assert
    assert result is None


def test_classify_route__health_get__none():
    # act
    result = _classify_route('/health', 'GET')

    # assert
    assert result is None


def test_get_client_ip__no_proxy__use_client_host():
    # arrange
    request = MagicMock(spec=Request)
    request.headers = {}
    request.client = MagicMock()
    request.client.host = '192.168.1.1'

    # act
    result = _get_client_ip(request)

    # assert
    assert result == '192.168.1.1'


def test_get_client_ip__x_forwarded__first_ip():
    # arrange
    request = MagicMock(spec=Request)
    request.headers = {
        'x-forwarded-for': '10.0.0.1, 172.16.0.1',
    }

    # act
    result = _get_client_ip(request)

    # assert
    assert result == '10.0.0.1'


def test_get_client_ip__single_forwarded__use_it():
    # arrange
    request = MagicMock(spec=Request)
    request.headers = {'x-forwarded-for': '203.0.113.5'}

    # act
    result = _get_client_ip(request)

    # assert
    assert result == '203.0.113.5'


def test_get_client_ip__no_client__fallback():
    # arrange
    request = MagicMock(spec=Request)
    request.headers = {}
    request.client = None

    # act
    result = _get_client_ip(request)

    # assert
    assert result == '0.0.0.0'


def test_sliding_window__empty__zero_count():
    # arrange
    window = _SlidingWindow()

    # act
    count = window.count_in_window(time.monotonic(), 60)

    # assert
    assert count == 0


def test_sliding_window__one_request__count_one():
    # arrange
    window = _SlidingWindow()
    now = time.monotonic()
    window.record(now)

    # act
    count = window.count_in_window(now, 60)

    # assert
    assert count == 1


def test_sliding_window__expired__count_zero():
    # arrange
    window = _SlidingWindow()
    old = time.monotonic() - 120
    window.record(old)

    # act
    now = time.monotonic()
    count = window.count_in_window(now, 60)

    # assert
    assert count == 0


def test_sliding_window__mixed__count_recent_only():
    # arrange
    window = _SlidingWindow()
    now = time.monotonic()
    window.record(now - 120)
    window.record(now - 30)
    window.record(now - 5)

    # act
    count = window.count_in_window(now, 60)

    # assert
    assert count == 2


@pytest.mark.asyncio
async def test_dispatch__under_limit__pass(
    fast_rate_limits,
    make_rate_request,
):
    # arrange
    mw = RateLimitMiddleware(
        app=AsyncMock(),
        rate_limits=fast_rate_limits,
    )
    request = make_rate_request()
    expected = Response(status_code=200)
    call_next_mock = AsyncMock(return_value=expected)

    # act
    response = await mw.dispatch(request, call_next_mock)

    # assert
    assert response.status_code == 200
    call_next_mock.assert_called_once_with(request)


@pytest.mark.asyncio
async def test_dispatch__over_limit__return_429(
    fast_rate_limits,
    make_rate_request,
):
    # arrange
    mw = RateLimitMiddleware(
        app=AsyncMock(),
        rate_limits=fast_rate_limits,
    )
    call_next_mock = AsyncMock(
        return_value=Response(status_code=200),
    )

    # act
    for _ in range(2):
        req = make_rate_request()
        await mw.dispatch(req, call_next_mock)

    req = make_rate_request()
    response = await mw.dispatch(req, call_next_mock)

    # assert
    assert response.status_code == 429
    assert call_next_mock.call_count == 2


@pytest.mark.asyncio
async def test_dispatch__different_ips__independent(
    fast_rate_limits,
    make_rate_request,
):
    # arrange
    mw = RateLimitMiddleware(
        app=AsyncMock(),
        rate_limits=fast_rate_limits,
    )
    call_next_mock = AsyncMock(
        return_value=Response(status_code=200),
    )
    responses = []

    # act
    for ip in ('10.0.0.1', '10.0.0.2'):
        for _ in range(2):
            req = make_rate_request(client_ip=ip)
            resp = await mw.dispatch(req, call_next_mock)
            responses.append(resp)

    # assert
    assert all(r.status_code == 200 for r in responses)
    assert call_next_mock.call_count == 4


@pytest.mark.asyncio
async def test_dispatch__non_limited_route__pass(
    fast_rate_limits,
    make_rate_request,
):
    # arrange
    mw = RateLimitMiddleware(
        app=AsyncMock(),
        rate_limits=fast_rate_limits,
    )
    call_next_mock = AsyncMock(
        return_value=Response(status_code=200),
    )
    responses = []

    # act
    for _ in range(10):
        req = make_rate_request(path='/', method='GET')
        resp = await mw.dispatch(req, call_next_mock)
        responses.append(resp)

    # assert
    assert all(r.status_code == 200 for r in responses)


@pytest.mark.asyncio
async def test_dispatch__429_has_retry_after(
    fast_rate_limits,
    make_rate_request,
):
    # arrange
    mw = RateLimitMiddleware(
        app=AsyncMock(),
        rate_limits=fast_rate_limits,
    )
    call_next_mock = AsyncMock(
        return_value=Response(status_code=200),
    )
    for _ in range(2):
        req = make_rate_request()
        await mw.dispatch(req, call_next_mock)

    # act
    req = make_rate_request()
    response = await mw.dispatch(req, call_next_mock)

    # assert
    assert response.status_code == 429
    assert response.headers.get('retry-after') == '60'


@pytest.mark.asyncio
async def test_dispatch__download_higher_limit(
    fast_rate_limits,
    make_rate_request,
):
    # arrange
    mw = RateLimitMiddleware(
        app=AsyncMock(),
        rate_limits=fast_rate_limits,
    )
    call_next_mock = AsyncMock(
        return_value=Response(status_code=200),
    )
    responses = []

    # act — 3 downloads OK, 4th blocked
    for _ in range(3):
        req = make_rate_request(
            path='/some-file-id',
            method='GET',
        )
        resp = await mw.dispatch(req, call_next_mock)
        responses.append(resp)

    req = make_rate_request(
        path='/some-file-id',
        method='GET',
    )
    response = await mw.dispatch(req, call_next_mock)

    # assert
    assert all(r.status_code == 200 for r in responses)
    assert response.status_code == 429


def test_evict_stale__removes_expired_windows():
    """Stale windows are removed after cleanup interval."""
    # arrange

    mw = RateLimitMiddleware(
        app=AsyncMock(),
        rate_limits={
            'upload': _RateLimit(max_requests=10, window_seconds=60),
        },
    )
    now = time.monotonic()
    # Simulate old entries
    for i in range(100):
        key = f'upload:10.0.0.{i}'
        win = _SlidingWindow()
        win.record(now - 200)  # 200s ago, well past 60s window
        mw._windows[key] = win

    assert len(mw._windows) == 100

    # act — force cleanup by advancing past interval
    mw._last_cleanup = now - _CLEANUP_INTERVAL_SECONDS - 1
    mw._maybe_evict_stale(now)

    # assert
    assert len(mw._windows) == 0


def test_evict_stale__keeps_recent_windows():
    """Recent windows survive eviction."""
    # arrange

    mw = RateLimitMiddleware(
        app=AsyncMock(),
        rate_limits={
            'upload': _RateLimit(max_requests=10, window_seconds=60),
        },
    )
    now = time.monotonic()
    # Old entry
    old_win = _SlidingWindow()
    old_win.record(now - 200)
    mw._windows['upload:10.0.0.1'] = old_win
    # Recent entry
    new_win = _SlidingWindow()
    new_win.record(now - 5)
    mw._windows['upload:10.0.0.2'] = new_win

    # act
    mw._last_cleanup = now - _CLEANUP_INTERVAL_SECONDS - 1
    mw._maybe_evict_stale(now)

    # assert
    assert 'upload:10.0.0.1' not in mw._windows
    assert 'upload:10.0.0.2' in mw._windows
