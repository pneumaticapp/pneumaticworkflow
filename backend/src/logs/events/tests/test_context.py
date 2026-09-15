from contextvars import copy_context

from src.logs.events.context import (
    RequestContext,
    context_from_request,
    get_context,
    reset_context,
    set_context,
)


def test_context_from_request__request__address_and_browser(
    request_factory,
):

    # arrange
    request = request_factory.get(
        '/',
        HTTP_X_REAL_IP='1.2.3.4',
        HTTP_USER_AGENT='Firefox',
    )
    request.request_id = 'abc'

    # act
    context = context_from_request(request=request)

    # assert
    assert context.request_id == 'abc'
    assert context.ip == '1.2.3.4'
    assert context.user_agent == 'Firefox'


def test_context_from_request__no_request_id__none(request_factory):

    # arrange
    request = request_factory.get('/')

    # act
    context = context_from_request(request=request)

    # assert
    assert context.request_id is None


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
