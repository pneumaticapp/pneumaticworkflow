from src.utils.http import (
    USER_AGENT_MAX,
    get_client_ip,
    get_user_agent_header,
)


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


def test_get_client_ip__private_server_header__used(request_factory):

    """ The private server of nginx names the client in a REMOTE_ADDR
        header of its own, the one the private api permissions read:
        without it every request of that server would carry the
        address of nginx. """

    # arrange
    request = request_factory.get(
        '/',
        HTTP_REMOTE_ADDR='203.0.113.9',
        REMOTE_ADDR='172.18.0.5',
    )

    # act
    result = get_client_ip(request)

    # assert
    assert result == '203.0.113.9'


def test_get_client_ip__spoofed_private_server_header__socket_address(
    request_factory,
):

    # arrange
    request = request_factory.get(
        '/',
        HTTP_REMOTE_ADDR='not an address',
        REMOTE_ADDR='172.18.0.5',
    )

    # act
    result = get_client_ip(request)

    # assert
    assert result == '172.18.0.5'


def test_get_client_ip__real_ip_and_private_header__real_ip_wins(
    request_factory,
):

    # arrange
    request = request_factory.get(
        '/',
        HTTP_X_REAL_IP='198.51.100.4',
        HTTP_REMOTE_ADDR='203.0.113.9',
    )

    # act
    result = get_client_ip(request)

    # assert
    assert result == '198.51.100.4'
