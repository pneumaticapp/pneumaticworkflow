from uuid import UUID

import pytest
from django.http import HttpResponse

from src.logs.events.context import get_context
from src.logs.events.middleware import (
    REQUEST_ID_HEADER,
    EventContextMiddleware,
)


def test_call__request_id_header__reused(request_factory, mocker):

    # arrange
    request = request_factory.get('/', HTTP_X_REQUEST_ID='abc')
    uuid4_mock = mocker.patch('src.logs.events.middleware.uuid4')
    middleware = EventContextMiddleware(lambda inner: HttpResponse())

    # act
    response = middleware(request)

    # assert
    assert request.request_id == 'abc'
    assert response[REQUEST_ID_HEADER] == 'abc'
    uuid4_mock.assert_not_called()


def test_call__no_request_id__uuid_generated(request_factory, mocker):

    # arrange
    request = request_factory.get('/')
    generated = UUID('12345678123456781234567812345678')
    uuid4_mock = mocker.patch(
        'src.logs.events.middleware.uuid4',
        return_value=generated,
    )
    middleware = EventContextMiddleware(lambda inner: HttpResponse())

    # act
    response = middleware(request)

    # assert
    assert request.request_id == generated.hex
    assert response[REQUEST_ID_HEADER] == generated.hex
    uuid4_mock.assert_called_once_with()


def test_call__two_requests__different_ids(request_factory, mocker):

    # arrange
    first_uuid = UUID('11111111111111111111111111111111')
    second_uuid = UUID('22222222222222222222222222222222')
    uuid4_mock = mocker.patch(
        'src.logs.events.middleware.uuid4',
        side_effect=[first_uuid, second_uuid],
    )
    middleware = EventContextMiddleware(lambda inner: HttpResponse())

    # act
    first = middleware(request_factory.get('/'))
    second = middleware(request_factory.get('/'))

    # assert
    assert first[REQUEST_ID_HEADER] == first_uuid.hex
    assert second[REQUEST_ID_HEADER] == second_uuid.hex
    assert uuid4_mock.call_count == 2
    uuid4_mock.assert_has_calls([mocker.call(), mocker.call()])


def test_call__unsafe_request_id__generated_instead(
    request_factory,
    mocker,
):

    """ The value goes into every event and into a response header,
        so a long or exotic one is replaced, not trimmed. """

    # arrange
    request = request_factory.get('/', HTTP_X_REQUEST_ID='x' * 100)
    generated = UUID('12345678123456781234567812345678')
    uuid4_mock = mocker.patch(
        'src.logs.events.middleware.uuid4',
        return_value=generated,
    )
    middleware = EventContextMiddleware(lambda inner: HttpResponse())

    # act
    response = middleware(request)

    # assert
    assert response[REQUEST_ID_HEADER] == generated.hex
    uuid4_mock.assert_called_once_with()


def test_call__request_id_with_a_new_line__generated_instead(
    request_factory,
    mocker,
):

    # arrange
    request = request_factory.get('/', HTTP_X_REQUEST_ID='ab\ncd')
    generated = UUID('12345678123456781234567812345678')
    uuid4_mock = mocker.patch(
        'src.logs.events.middleware.uuid4',
        return_value=generated,
    )
    middleware = EventContextMiddleware(lambda inner: HttpResponse())

    # act
    response = middleware(request)

    # assert
    assert response[REQUEST_ID_HEADER] == generated.hex
    uuid4_mock.assert_called_once_with()


def test_request_id__sixty_four_characters__accepted(
    request_factory,
    mocker,
):

    # arrange
    given = 'a' * 64
    request = request_factory.get('/', HTTP_X_REQUEST_ID=given)
    uuid4_mock = mocker.patch('src.logs.events.middleware.uuid4')

    # act
    request_id = EventContextMiddleware._request_id(request)

    # assert
    assert request_id == given
    uuid4_mock.assert_not_called()


def test_request_id__sixty_five_characters__generated_instead(
    request_factory,
    mocker,
):

    # arrange
    request = request_factory.get('/', HTTP_X_REQUEST_ID='a' * 65)
    generated = UUID('12345678123456781234567812345678')
    uuid4_mock = mocker.patch(
        'src.logs.events.middleware.uuid4',
        return_value=generated,
    )

    # act
    request_id = EventContextMiddleware._request_id(request)

    # assert
    assert request_id == generated.hex
    uuid4_mock.assert_called_once_with()


def test_request_id__trailing_new_line__generated_instead(
    request_factory,
    mocker,
):

    """ "$" of a pattern matches before a trailing new line, so the
        header "abc\\n" would pass with it: the pattern ends with
        "\\Z" on purpose. """

    # arrange
    request = request_factory.get('/', HTTP_X_REQUEST_ID='abc\n')
    generated = UUID('12345678123456781234567812345678')
    uuid4_mock = mocker.patch(
        'src.logs.events.middleware.uuid4',
        return_value=generated,
    )

    # act
    request_id = EventContextMiddleware._request_id(request)

    # assert
    assert request_id == generated.hex
    uuid4_mock.assert_called_once_with()


def test_process_response__no_request_id__no_header(request_factory):

    """ A request that skipped process_request (an exception in an
        outer middleware) has no id, and the header is left out
        rather than filled with "None". """

    # arrange
    request = request_factory.get('/')
    middleware = EventContextMiddleware(lambda inner: HttpResponse())

    # act
    response = middleware.process_response(request, HttpResponse())

    # assert
    assert response.has_header(REQUEST_ID_HEADER) is False
    assert get_context() is None


def test_call__inside_the_view__context_available(
    request_factory,
    mocker,
):

    # arrange
    captured = {}

    def view(inner_request):
        captured['context'] = get_context()
        return HttpResponse()

    request = request_factory.get(
        '/',
        HTTP_X_REAL_IP='1.2.3.4',
        HTTP_X_REQUEST_ID='abc',
        HTTP_USER_AGENT='Firefox',
    )
    uuid4_mock = mocker.patch('src.logs.events.middleware.uuid4')
    middleware = EventContextMiddleware(view)

    # act
    middleware(request)

    # assert
    assert captured['context'].ip == '1.2.3.4'
    assert captured['context'].request_id == 'abc'
    assert captured['context'].user_agent == 'Firefox'
    assert get_context() is None
    uuid4_mock.assert_not_called()


def test_call__view_exception__context_reset(request_factory, mocker):

    """ process_response is skipped when an inner middleware raises,
        so the context must not leak into the next request. """

    # arrange
    def view(inner_request):
        raise ValueError('boom')

    request = request_factory.get('/', HTTP_X_REQUEST_ID='abc')
    uuid4_mock = mocker.patch('src.logs.events.middleware.uuid4')
    middleware = EventContextMiddleware(view)

    # act
    with pytest.raises(ValueError) as ex:
        middleware(request)

    # assert
    assert str(ex.value) == 'boom'
    assert get_context() is None
    uuid4_mock.assert_not_called()


@pytest.mark.django_db
def test_call__installed_in_the_project__request_id_in_response(api_client):

    # act
    response = api_client.get(
        '/accounts/users/privileges',
        HTTP_X_REQUEST_ID='abc',
        HTTP_X_REAL_IP='1.2.3.4',
    )

    # assert
    assert response.status_code == 401
    assert response[REQUEST_ID_HEADER] == 'abc'
    assert get_context() is None


@pytest.mark.parametrize(
    'given',
    ('a.b', 'a_b', 'a~b', 'a+b', 'a/b', 'a=b', 'a-b', 'A1'),
)
def test_request_id__allowed_punctuation__reused(
    request_factory,
    mocker,
    given,
):

    """ The characters of a base64 or a uuid with separators pass,
        the id of a caller is kept as it came. """

    # arrange
    request = request_factory.get('/', HTTP_X_REQUEST_ID=given)
    uuid4_mock = mocker.patch('src.logs.events.middleware.uuid4')
    middleware = EventContextMiddleware(lambda inner: HttpResponse())

    # act
    response = middleware(request)

    # assert
    assert request.request_id == given
    assert response[REQUEST_ID_HEADER] == given
    uuid4_mock.assert_not_called()
