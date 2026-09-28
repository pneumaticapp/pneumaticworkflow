from uuid import UUID

import pytest
from django.http import HttpResponse

from src.logs.events.context import get_context
from src.logs.events.middleware import (
    REQUEST_ID_HEADER,
    USER_AGENT_MAX,
    EventContextMiddleware,
)


def test_call__request_id_header__reused(request_factory, mocker):

    # arrange
    request = request_factory.get('/', HTTP_X_REQUEST_ID='abc')
    uuid4_mock = mocker.patch('src.logs.events.middleware.uuid4')
    middleware = EventContextMiddleware(lambda inner: HttpResponse())

    # act
    response = middleware(request=request)

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
    response = middleware(request=request)

    # assert
    assert request.request_id == generated.hex
    assert response[REQUEST_ID_HEADER] == generated.hex
    uuid4_mock.assert_called_once_with()


def test_call__two_requests__different_ids(request_factory, mocker):

    # arrange
    first_request = request_factory.get('/')
    second_request = request_factory.get('/')
    first_uuid = UUID('11111111111111111111111111111111')
    second_uuid = UUID('22222222222222222222222222222222')
    uuid4_mock = mocker.patch(
        'src.logs.events.middleware.uuid4',
        side_effect=[first_uuid, second_uuid],
    )
    middleware = EventContextMiddleware(lambda inner: HttpResponse())

    # act
    first = middleware(request=first_request)
    second = middleware(request=second_request)

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
    response = middleware(request=request)

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
    response = middleware(request=request)

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
    request_id = EventContextMiddleware._request_id(request=request)

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
    request_id = EventContextMiddleware._request_id(request=request)

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
    request_id = EventContextMiddleware._request_id(request=request)

    # assert
    assert request_id == generated.hex
    uuid4_mock.assert_called_once_with()


def test_process_response__no_request_id__no_header(request_factory):

    """ A request that skipped process_request (an exception in an
        outer middleware) has no id, and the header is left out
        rather than filled with "None". """

    # arrange
    request = request_factory.get('/')
    response = HttpResponse()
    middleware = EventContextMiddleware(lambda inner: HttpResponse())

    # act
    result = middleware.process_response(
        request=request,
        response=response,
    )

    # assert
    assert result.has_header(REQUEST_ID_HEADER) is False
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
    middleware(request=request)

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
        middleware(request=request)

    # assert
    assert str(ex.value) == 'boom'
    assert get_context() is None
    uuid4_mock.assert_not_called()


def test_call__context_build_failed__original_error_raised(
    request_factory,
    mocker,
):

    """ process_request raised before the token was stored: the reset
        finds no token and lets the original error out instead of
        hiding it under one of its own. """

    # arrange
    request = request_factory.get('/', HTTP_X_REQUEST_ID='abc')
    user_ip_mock = mocker.patch.object(
        EventContextMiddleware,
        attribute='_user_ip',
        side_effect=ValueError('boom'),
    )
    uuid4_mock = mocker.patch('src.logs.events.middleware.uuid4')
    get_response_mock = mocker.Mock()
    middleware = EventContextMiddleware(get_response_mock)

    # act
    with pytest.raises(ValueError) as ex:
        middleware(request=request)

    # assert
    assert str(ex.value) == 'boom'
    assert get_context() is None
    user_ip_mock.assert_called_once_with(request)
    get_response_mock.assert_not_called()
    uuid4_mock.assert_not_called()


@pytest.mark.django_db
def test_call__installed_in_the_project__request_id_in_response(api_client):

    # arrange
    request_id = 'abc'

    # act
    response = api_client.get(
        '/accounts/users/privileges',
        HTTP_X_REQUEST_ID=request_id,
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
    response = middleware(request=request)

    # assert
    assert request.request_id == given
    assert response[REQUEST_ID_HEADER] == given
    uuid4_mock.assert_not_called()


def test_user_ip__real_ip_and_forwarded_for__real_ip_wins(request_factory):

    """ X-Real-IP is the address our nginx writes; X-Forwarded-For
        keeps whatever the client sent in front of it. """

    # arrange
    request = request_factory.get(
        '/',
        HTTP_X_REAL_IP='1.2.3.4',
        HTTP_X_FORWARDED_FOR='5.6.7.8,10.0.0.1',
        REMOTE_ADDR='10.0.0.2',
    )
    middleware = EventContextMiddleware(lambda inner: HttpResponse())

    # act
    ip = middleware._user_ip(request=request)

    # assert
    assert ip == '1.2.3.4'


def test_user_ip__empty_real_ip__forwarded_for_first_hop(request_factory):

    # arrange
    request = request_factory.get(
        '/',
        HTTP_X_REAL_IP='',
        HTTP_X_FORWARDED_FOR='5.6.7.8,10.0.0.1',
    )
    middleware = EventContextMiddleware(lambda inner: HttpResponse())

    # act
    ip = middleware._user_ip(request=request)

    # assert
    assert ip == '5.6.7.8'


def test_user_ip__no_real_ip__address_of_the_mixin(request_factory, mocker):

    """ A request that came around nginx has no X-Real-IP: the address
        is the one AnonymousMixin reads. """

    # arrange
    request = request_factory.get('/')
    get_user_ip_mock = mocker.patch.object(
        EventContextMiddleware,
        attribute='get_user_ip',
        return_value='5.6.7.8',
    )
    middleware = EventContextMiddleware(lambda inner: HttpResponse())

    # act
    ip = middleware._user_ip(request=request)

    # assert
    assert ip == '5.6.7.8'
    get_user_ip_mock.assert_called_once_with(request)


def test_user_ip__garbage_real_ip__kept_as_sent(request_factory):

    """ The address is not validated on purpose: X-Real-IP is written
        by our nginx, and the value goes into the record as it came,
        the same as AnonymousMixin hands it to the tokens. """

    # arrange
    request = request_factory.get(
        '/',
        HTTP_X_REAL_IP='<script>not-an-ip</script>',
    )
    middleware = EventContextMiddleware(lambda inner: HttpResponse())

    # act
    ip = middleware._user_ip(request=request)

    # assert
    assert ip == '<script>not-an-ip</script>'


def test_user_ip__long_real_ip__kept_whole(request_factory):

    """ No length limit either, unlike the user agent. """

    # arrange
    request = request_factory.get('/', HTTP_X_REAL_IP='1' * 1000)
    middleware = EventContextMiddleware(lambda inner: HttpResponse())

    # act
    ip = middleware._user_ip(request=request)

    # assert
    assert ip == '1' * 1000


def test_user_ip__garbage_forwarded_for__first_hop_as_sent(
    request_factory,
):

    """ Without X-Real-IP the first hop of X-Forwarded-For is the
        address, whatever the client put there. """

    # arrange
    request = request_factory.get(
        '/',
        HTTP_X_FORWARDED_FOR='not-an-ip,10.0.0.1',
    )
    middleware = EventContextMiddleware(lambda inner: HttpResponse())

    # act
    ip = middleware._user_ip(request=request)

    # assert
    assert ip == 'not-an-ip'


def test_user_ip__long_forwarded_for__first_hop_kept_whole(
    request_factory,
):

    # arrange
    request = request_factory.get(
        '/',
        HTTP_X_FORWARDED_FOR=f'{"2" * 1000},10.0.0.1',
    )
    middleware = EventContextMiddleware(lambda inner: HttpResponse())

    # act
    ip = middleware._user_ip(request=request)

    # assert
    assert ip == '2' * 1000


def test_user_agent__longer_than_the_limit__trimmed(request_factory):

    """ Every event of the request carries the header, and a client
        sends whatever length it likes. """

    # arrange
    request = request_factory.get(
        '/',
        HTTP_USER_AGENT='a' * (USER_AGENT_MAX + 100),
    )
    middleware = EventContextMiddleware(lambda inner: HttpResponse())

    # act
    user_agent = middleware._user_agent(request=request)

    # assert
    assert user_agent == 'a' * USER_AGENT_MAX


def test_user_agent__at_the_limit__kept(request_factory):

    # arrange
    request = request_factory.get('/', HTTP_USER_AGENT='a' * USER_AGENT_MAX)
    middleware = EventContextMiddleware(lambda inner: HttpResponse())

    # act
    user_agent = middleware._user_agent(request=request)

    # assert
    assert user_agent == 'a' * USER_AGENT_MAX


def test_user_agent__empty_header__none(request_factory):

    # arrange
    request = request_factory.get('/', HTTP_USER_AGENT='')
    middleware = EventContextMiddleware(lambda inner: HttpResponse())

    # act
    user_agent = middleware._user_agent(request=request)

    # assert
    assert user_agent is None


def test_user_agent__no_header__none(request_factory):

    # arrange
    request = request_factory.get('/')
    middleware = EventContextMiddleware(lambda inner: HttpResponse())

    # act
    user_agent = middleware._user_agent(request=request)

    # assert
    assert user_agent is None
