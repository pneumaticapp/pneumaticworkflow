from contextvars import copy_context

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
    context = context_from_request(request=request)

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
    context = context_from_request(request=request)

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
    context = context_from_request(request=request)

    # assert
    assert context.actor.type == ActorType.USER


def test_context_from_request__empty_token_type__user_actor(
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
    request.token_type = ''

    # act
    context = context_from_request(request=request)

    # assert
    assert context.actor == Actor(
        type=ActorType.USER,
        id=13,
        email='owner@test.test',
    )


def test_set_context__context__returned_by_get_context():

    """ Run in a copy of the context so that nothing leaks into the
        next test of the thread. """

    # arrange
    context = RequestContext(request_id='first')
    run_context = copy_context()

    # act
    run_context.run(set_context, context)

    # assert
    assert run_context.run(get_context) is context
    assert get_context() is None


def test_reset_context__token__previous_context_restored():

    # arrange
    first = RequestContext(request_id='first')
    second = RequestContext(request_id='second')
    run_context = copy_context()
    run_context.run(set_context, first)
    token = run_context.run(set_context, second)

    # act
    run_context.run(reset_context, token)

    # assert
    assert run_context.run(get_context) is first
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
    context = merge_context(request=request)

    # assert
    assert get_context() is None
    assert context == RequestContext(ip='1.2.3.4', user_agent='Firefox')


def test_merge_context__no_request_with_context__context(request_context):

    """ A call made deep in a service gets what the middleware
        published for the request being handled. """

    # arrange
    request = None

    # act
    context = merge_context(request=request)

    # assert
    assert context == RequestContext(
        request_id='ctx-request',
        ip='9.9.9.9',
        user_agent='Chrome',
        actor=Actor(
            type=ActorType.USER,
            id=77,
            email='ctx@test.test',
        ),
    )


def test_merge_context__no_request_no_context__empty_context():

    """ A Celery task or a management command: nothing is known. """

    # arrange
    request = None

    # act
    context = merge_context(request=request)

    # assert
    assert context == RequestContext()
    assert get_context() is None
