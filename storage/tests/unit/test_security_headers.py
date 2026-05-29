"""Tests for security headers middleware."""


def test_headers__x_content_type__nosniff(sec_headers_client):

    # act
    response = sec_headers_client.get('/')

    # assert
    assert response.headers['X-Content-Type-Options'] == 'nosniff'


def test_headers__x_frame_options__deny(sec_headers_client):

    # act
    response = sec_headers_client.get('/')

    # assert
    assert response.headers['X-Frame-Options'] == 'DENY'


def test_headers__csp__default_none(sec_headers_client):

    # act
    response = sec_headers_client.get('/')

    # assert
    assert (
        response.headers['Content-Security-Policy']
        == "default-src 'none'"
    )


def test_headers__xss_protection__enabled(sec_headers_client):

    # act
    response = sec_headers_client.get('/')

    # assert
    assert (
        response.headers['X-XSS-Protection'] == '1; mode=block'
    )


def test_headers__referrer_policy__strict(sec_headers_client):

    # act
    response = sec_headers_client.get('/')

    # assert
    assert (
        response.headers['Referrer-Policy']
        == 'strict-origin-when-cross-origin'
    )


def test_headers__permissions_policy__restrictive(
    sec_headers_client,
):

    # act
    response = sec_headers_client.get('/')

    # assert
    assert 'Permissions-Policy' in response.headers


def test_headers__no_hsts__by_default(sec_headers_client):

    # act
    response = sec_headers_client.get('/')

    # assert
    assert 'Strict-Transport-Security' not in response.headers


def test_headers__hsts__when_enabled(sec_headers_client_hsts):

    # act
    response = sec_headers_client_hsts.get('/')

    # assert
    assert 'Strict-Transport-Security' in response.headers
    assert '31536000' in response.headers[
        'Strict-Transport-Security'
    ]


def test_headers__all_present__single_response(
    sec_headers_client,
):

    # act
    response = sec_headers_client.get('/')

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


def test_headers__response_body__unchanged(sec_headers_client):

    # act
    response = sec_headers_client.get('/')

    # assert
    assert response.text == 'ok'
    assert response.status_code == 200
