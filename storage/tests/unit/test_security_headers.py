"""Tests for security headers middleware."""

import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from src.shared_kernel.middleware.security_headers import (
    SecurityHeadersMiddleware,
)


def _homepage(request):
    """Simple test endpoint."""
    return PlainTextResponse('ok')


def _make_app(*, include_hsts: bool = False) -> Starlette:
    """Create test app with security headers middleware."""
    app = Starlette(routes=[Route('/', _homepage)])
    app.add_middleware(
        SecurityHeadersMiddleware,
        include_hsts=include_hsts,
    )
    return app


class TestSecurityHeaders:
    """Test security headers middleware."""

    @pytest.fixture
    def client(self):
        """Test client without HSTS."""
        return TestClient(_make_app())

    @pytest.fixture
    def client_hsts(self):
        """Test client with HSTS."""
        return TestClient(_make_app(include_hsts=True))

    def test_headers__x_content_type__nosniff(self, client):
        """X-Content-Type-Options is set."""
        # act
        response = client.get('/')

        # assert
        assert response.headers['X-Content-Type-Options'] == 'nosniff'

    def test_headers__x_frame_options__deny(self, client):
        """X-Frame-Options is set to DENY."""
        # act
        response = client.get('/')

        # assert
        assert response.headers['X-Frame-Options'] == 'DENY'

    def test_headers__csp__default_none(self, client):
        """Content-Security-Policy is set."""
        # act
        response = client.get('/')

        # assert
        assert (
            response.headers['Content-Security-Policy']
            == "default-src 'none'"
        )

    def test_headers__xss_protection__enabled(self, client):
        """X-XSS-Protection is set."""
        # act
        response = client.get('/')

        # assert
        assert response.headers['X-XSS-Protection'] == '1; mode=block'

    def test_headers__referrer_policy__strict(self, client):
        """Referrer-Policy is set."""
        # act
        response = client.get('/')

        # assert
        assert (
            response.headers['Referrer-Policy']
            == 'strict-origin-when-cross-origin'
        )

    def test_headers__permissions_policy__restrictive(self, client):
        """Permissions-Policy is set."""
        # act
        response = client.get('/')

        # assert
        assert 'Permissions-Policy' in response.headers

    def test_headers__no_hsts__by_default(self, client):
        """HSTS is NOT included by default."""
        # act
        response = client.get('/')

        # assert
        assert 'Strict-Transport-Security' not in response.headers

    def test_headers__hsts__when_enabled(self, client_hsts):
        """HSTS IS included when enabled."""
        # act
        response = client_hsts.get('/')

        # assert
        assert 'Strict-Transport-Security' in response.headers
        assert '31536000' in response.headers[
            'Strict-Transport-Security'
        ]

    def test_headers__all_present__single_response(self, client):
        """All security headers present in one response."""
        # act
        response = client.get('/')

        # assert
        required = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'Content-Security-Policy',
            'X-XSS-Protection',
            'Referrer-Policy',
            'Permissions-Policy',
        ]
        for header in required:
            assert header in response.headers, (
                f'Missing header: {header}'
            )

    def test_headers__response_body__unchanged(self, client):
        """Middleware does not alter response body."""
        # act
        response = client.get('/')

        # assert
        assert response.text == 'ok'
        assert response.status_code == 200
