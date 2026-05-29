"""Tests for rate limiting middleware."""

import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.requests import Request
from starlette.responses import Response

from src.shared_kernel.middleware.rate_limit import (
    RateLimitMiddleware,
    _RateLimit,
    _SlidingWindow,
    _classify_route,
    _get_client_ip,
)


class TestClassifyRoute:
    """Test route classification."""

    def test_classify__upload_post__upload(self):
        """POST /upload → upload bucket."""
        # act & assert
        assert _classify_route('/upload', 'POST') == 'upload'

    def test_classify__file_get__download(self):
        """GET /{file_id} → download bucket."""
        # act & assert
        assert _classify_route(
            '/12345678-1234-5678-1234-567812345678', 'GET',
        ) == 'download'

    def test_classify__upload_get__none(self):
        """GET /upload → not rate-limited."""
        # act & assert
        assert _classify_route('/upload', 'GET') is None

    def test_classify__root_get__none(self):
        """GET / → not rate-limited (path too short)."""
        # act & assert
        assert _classify_route('/', 'GET') is None

    def test_classify__random_post__none(self):
        """POST /random → not rate-limited."""
        # act & assert
        assert _classify_route('/random', 'POST') is None

    def test_classify__health_get__none(self):
        """GET /health → not rate-limited (excluded)."""
        # act & assert
        assert _classify_route('/health', 'GET') is None


class TestGetClientIp:
    """Test client IP extraction."""

    def test_ip__no_proxy__use_client_host(self):
        """Direct connection returns client.host."""
        # arrange
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = MagicMock()
        request.client.host = '192.168.1.1'

        # act & assert
        assert _get_client_ip(request) == '192.168.1.1'

    def test_ip__x_forwarded_for__use_first_ip(self):
        """X-Forwarded-For returns first IP."""
        # arrange
        request = MagicMock(spec=Request)
        request.headers = {
            'x-forwarded-for': '10.0.0.1, 172.16.0.1',
        }

        # act & assert
        assert _get_client_ip(request) == '10.0.0.1'

    def test_ip__single_forwarded__use_it(self):
        """Single X-Forwarded-For IP."""
        # arrange
        request = MagicMock(spec=Request)
        request.headers = {'x-forwarded-for': '203.0.113.5'}

        # act & assert
        assert _get_client_ip(request) == '203.0.113.5'

    def test_ip__no_client__fallback(self):
        """No client object returns fallback."""
        # arrange
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = None

        # act & assert
        assert _get_client_ip(request) == '0.0.0.0'


class TestSlidingWindow:
    """Test sliding window counter."""

    def test_window__empty__zero_count(self):
        """Empty window returns 0."""
        # arrange
        window = _SlidingWindow()

        # act & assert
        assert window.count_in_window(time.monotonic(), 60) == 0

    def test_window__one_request__count_one(self):
        """One request within window."""
        # arrange
        window = _SlidingWindow()
        now = time.monotonic()
        window.record(now)

        # act & assert
        assert window.count_in_window(now, 60) == 1

    def test_window__expired__count_zero(self):
        """Expired requests are evicted."""
        # arrange
        window = _SlidingWindow()
        old = time.monotonic() - 120  # 2 minutes ago
        window.record(old)

        # act
        now = time.monotonic()
        count = window.count_in_window(now, 60)

        # assert
        assert count == 0

    def test_window__mixed__count_recent_only(self):
        """Only recent requests counted."""
        # arrange
        window = _SlidingWindow()
        now = time.monotonic()
        window.record(now - 120)  # expired
        window.record(now - 30)   # recent
        window.record(now - 5)    # recent

        # act & assert
        assert window.count_in_window(now, 60) == 2


class TestRateLimitMiddleware:
    """Test rate limit middleware dispatch."""

    @pytest.fixture
    def _fast_limits(self):
        """Low limits for fast testing."""
        return {
            'upload': _RateLimit(
                max_requests=2, window_seconds=60,
            ),
            'download': _RateLimit(
                max_requests=3, window_seconds=60,
            ),
        }

    def _make_request(
        self,
        path: str = '/upload',
        method: str = 'POST',
        client_ip: str = '127.0.0.1',
    ) -> MagicMock:
        """Create a mock request."""
        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = path
        request.method = method
        request.headers = {}
        request.client = MagicMock()
        request.client.host = client_ip
        return request

    @pytest.mark.asyncio
    async def test_dispatch__under_limit__pass_through(
        self, _fast_limits,
    ):
        """Requests under limit pass through."""
        # arrange
        middleware = RateLimitMiddleware(
            app=AsyncMock(), rate_limits=_fast_limits,
        )
        request = self._make_request()
        expected = Response(status_code=200)
        call_next = AsyncMock(return_value=expected)

        # act
        response = await middleware.dispatch(
            request, call_next,
        )

        # assert
        assert response.status_code == 200
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_dispatch__over_limit__return_429(
        self, _fast_limits,
    ):
        """Requests over limit return 429."""
        # arrange
        middleware = RateLimitMiddleware(
            app=AsyncMock(), rate_limits=_fast_limits,
        )
        call_next = AsyncMock(
            return_value=Response(status_code=200),
        )

        # act — 2 allowed, 3rd blocked
        for _ in range(2):
            request = self._make_request()
            await middleware.dispatch(request, call_next)

        request = self._make_request()
        response = await middleware.dispatch(
            request, call_next,
        )

        # assert
        assert response.status_code == 429
        assert call_next.call_count == 2

    @pytest.mark.asyncio
    async def test_dispatch__different_ips__independent(
        self, _fast_limits,
    ):
        """Different IPs have independent limits."""
        # arrange
        middleware = RateLimitMiddleware(
            app=AsyncMock(), rate_limits=_fast_limits,
        )
        call_next = AsyncMock(
            return_value=Response(status_code=200),
        )

        # act — 2 from IP-A, 2 from IP-B (all under limit)
        for ip in ('10.0.0.1', '10.0.0.2'):
            for _ in range(2):
                request = self._make_request(client_ip=ip)
                response = await middleware.dispatch(
                    request, call_next,
                )
                assert response.status_code == 200

        # assert — all 4 passed
        assert call_next.call_count == 4

    @pytest.mark.asyncio
    async def test_dispatch__non_limited_route__pass(
        self, _fast_limits,
    ):
        """Non-rate-limited routes always pass."""
        # arrange
        middleware = RateLimitMiddleware(
            app=AsyncMock(), rate_limits=_fast_limits,
        )
        call_next = AsyncMock(
            return_value=Response(status_code=200),
        )

        # act — 10 requests to /docs (no limit)
        for _ in range(10):
            request = self._make_request(
                path='/', method='GET',
            )
            response = await middleware.dispatch(
                request, call_next,
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_dispatch__429_has_retry_after(
        self, _fast_limits,
    ):
        """429 response includes Retry-After header."""
        # arrange
        middleware = RateLimitMiddleware(
            app=AsyncMock(), rate_limits=_fast_limits,
        )
        call_next = AsyncMock(
            return_value=Response(status_code=200),
        )

        # exhaust limit
        for _ in range(2):
            request = self._make_request()
            await middleware.dispatch(request, call_next)

        # act
        request = self._make_request()
        response = await middleware.dispatch(
            request, call_next,
        )

        # assert
        assert response.status_code == 429
        assert response.headers.get('retry-after') == '60'

    @pytest.mark.asyncio
    async def test_dispatch__download_higher_limit(
        self, _fast_limits,
    ):
        """Download has higher limit than upload."""
        # arrange
        middleware = RateLimitMiddleware(
            app=AsyncMock(), rate_limits=_fast_limits,
        )
        call_next = AsyncMock(
            return_value=Response(status_code=200),
        )

        # act — 3 downloads OK, 4th blocked
        for _ in range(3):
            request = self._make_request(
                path='/some-file-id', method='GET',
            )
            response = await middleware.dispatch(
                request, call_next,
            )
            assert response.status_code == 200

        request = self._make_request(
            path='/some-file-id', method='GET',
        )
        response = await middleware.dispatch(
            request, call_next,
        )

        # assert
        assert response.status_code == 429
