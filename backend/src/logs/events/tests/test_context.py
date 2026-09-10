from src.authentication.enums import AuthTokenType
from src.logs.events.context import (
    USER_AGENT_MAX,
    RequestContext,
    context_from_request,
    get_context,
    get_user_agent_header,
    reset_context,
    set_context,
)
from src.logs.events.enums import ActorType
from src.utils.http import get_client_ip


def test_get_client_ip__real_ip__wins(request_factory):

    # arrange
    request = request_factory.get(
        '/',
        HTTP_X_REAL_IP='1.2.3.4',
        HTTP_X_FORWARDED_FOR='5.6.7.8',
        REMOTE_ADDR='127.0.0.1',
    )

    # act
    ip = get_client_ip(request)

    # assert
    assert ip == '1.2.3.4'


def test_get_client_ip__forwarded_for__first_hop(request_factory):

    # arrange
    request = request_factory.get(
        '/',
        HTTP_X_FORWARDED_FOR='5.6.7.8, 10.0.0.1',
        REMOTE_ADDR='127.0.0.1',
    )

    # act
    ip = get_client_ip(request)

    # assert
    assert ip == '5.6.7.8'


def test_get_client_ip__no_headers__remote_addr(request_factory):

    # arrange
    request = request_factory.get('/', REMOTE_ADDR='127.0.0.1')

    # act
    ip = get_client_ip(request)

    # assert
    assert ip == '127.0.0.1'


def test_get_client_ip__spoofed_real_ip__socket_address(request_factory):

    """ Behind somebody else's balancer the header is client
        controlled: anything that is not an address would ride in
        every event of the request at the length the client chose. """

    # arrange
    request = request_factory.get(
        '/',
        HTTP_X_REAL_IP='not-an-address',
        REMOTE_ADDR='127.0.0.1',
    )

    # act
    ip = get_client_ip(request)

    # assert
    assert ip == '127.0.0.1'


def test_get_client_ip__spoofed_forwarded_for__socket_address(
    request_factory,
):

    # arrange
    request = request_factory.get(
        '/',
        HTTP_X_FORWARDED_FOR='not-an-address, 5.6.7.8',
        REMOTE_ADDR='127.0.0.1',
    )

    # act
    ip = get_client_ip(request)

    # assert
    assert ip == '127.0.0.1'


def test_get_client_ip__nothing__none(request_factory):

    # arrange
    request = request_factory.get('/')
    request.META.pop('REMOTE_ADDR', None)

    # act
    ip = get_client_ip(request)

    # assert
    assert ip is None


def test_get_user_agent_header__long_value__trimmed(request_factory):

    # arrange
    request = request_factory.get(
        '/',
        HTTP_USER_AGENT='a' * (USER_AGENT_MAX + 100),
    )

    # act
    user_agent = get_user_agent_header(request)

    # assert
    assert user_agent == 'a' * USER_AGENT_MAX


def test_get_user_agent_header__raw_value__not_parsed(request_factory):

    # arrange
    value = 'Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0'
    request = request_factory.get('/', HTTP_USER_AGENT=value)

    # act
    user_agent = get_user_agent_header(request)

    # assert
    assert user_agent == value


def test_get_user_agent_header__no_header__none(request_factory):

    # arrange
    request = request_factory.get('/')

    # act
    user_agent = get_user_agent_header(request)

    # assert
    assert user_agent is None


def test_context_from_request__anonymous__system_actor(request_factory):

    # arrange
    request = request_factory.get(
        '/',
        HTTP_X_REAL_IP='1.2.3.4',
        HTTP_USER_AGENT='Firefox',
    )

    # act
    context = context_from_request(request)

    # assert
    assert context.ip == '1.2.3.4'
    assert context.user_agent == 'Firefox'
    assert context.actor_type == ActorType.SYSTEM
    assert context.actor_id is None
    assert context.account_id is None


def test_context_from_request__authenticated__actor_filled(
    mocker,
    request_factory,
):

    # arrange
    request = request_factory.get('/')
    request.user = mocker.Mock(
        is_authenticated=True,
        id=13,
        email='owner@test.test',
        account_id=42,
    )
    request.token_type = AuthTokenType.API
    request.request_id = 'abc'

    # act
    context = context_from_request(request)

    # assert
    assert context.request_id == 'abc'
    assert context.actor_type == ActorType.API_KEY
    assert context.actor_id == 13
    assert context.actor_email == 'owner@test.test'
    assert context.account_id == 42


def test_context_from_request__no_token_type__user_actor(
    mocker,
    request_factory,
):

    # arrange
    request = request_factory.get('/')
    request.user = mocker.Mock(
        is_authenticated=True,
        id=13,
        email='owner@test.test',
        account_id=42,
    )

    # act
    context = context_from_request(request)

    # assert
    assert context.actor_type == ActorType.USER


def test_set_context__token__restores_previous():

    # arrange
    first = RequestContext(request_id='first')
    second = RequestContext(request_id='second')

    # act
    first_token = set_context(first)
    second_token = set_context(second)
    inner = get_context()
    reset_context(second_token)
    outer = get_context()
    reset_context(first_token)

    # assert
    assert inner.request_id == 'second'
    assert outer.request_id == 'first'
    assert get_context() is None
