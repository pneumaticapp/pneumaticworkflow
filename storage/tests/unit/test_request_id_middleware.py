"""Tests for the request id middleware."""


def test_dispatch__no_header__fresh_id_stored_and_returned(
    request_id_client,
):
    # act
    response = request_id_client.get('/')

    # assert
    assert response.status_code == 200
    assert len(response.headers['x-request-id']) == 32
    assert response.text == response.headers['x-request-id']


def test_dispatch__safe_header__kept(request_id_client):
    # act
    response = request_id_client.get(
        '/',
        headers={'X-Request-ID': 'trace-42'},
    )

    # assert
    assert response.headers['x-request-id'] == 'trace-42'
    assert response.text == 'trace-42'


def test_dispatch__unsafe_header__replaced(request_id_client):
    # act
    response = request_id_client.get(
        '/',
        headers={'X-Request-ID': 'a' * 65},
    )

    # assert
    assert response.headers['x-request-id'] != 'a' * 65
    assert len(response.headers['x-request-id']) == 32
    assert response.text == response.headers['x-request-id']


def test_dispatch__unauthenticated_request__id_on_the_401(test_client):
    # act
    response = test_client.get('/12345678-1234-5678-1234-567812345678')

    # assert
    assert response.status_code == 401
    assert len(response.headers['x-request-id']) == 32
