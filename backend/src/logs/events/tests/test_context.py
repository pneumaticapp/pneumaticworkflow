from src.authentication.enums import AuthTokenType
from src.logs.events.context import (
    RequestContext,
    context_from_request,
    get_context,
    merge_context,
    reset_context,
    set_context,
)
from src.logs.events.enums import ActorType
from src.logs.events.schema import Actor


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
    assert context.actor is None


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
    assert context.actor == Actor(
        type=ActorType.API_KEY,
        id=13,
        email='owner@test.test',
    )


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
    assert context.actor.type == ActorType.USER


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


def test_merge_context__request_and_no_context__request_only(
    request_factory,
):

    """ emit() called with a request outside the middleware (a test
        client, a management command building one): the request is
        all there is. """

    # arrange
    request = request_factory.get(
        '/',
        HTTP_X_REAL_IP='1.2.3.4',
        HTTP_USER_AGENT='Firefox',
    )

    # act
    context = merge_context(request)

    # assert
    assert get_context() is None
    assert context == RequestContext(ip='1.2.3.4', user_agent='Firefox')
