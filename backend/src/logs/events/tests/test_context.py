from contextvars import copy_context

from src.logs.events.entities import RequestContext, request_context


def test_request_context__set__returned_by_get():
    """Run in a copy of the context so that nothing leaks into the
    next test of the thread."""

    # arrange
    context = RequestContext(request_id='first')
    run_context = copy_context()

    # act
    run_context.run(request_context.set, context)

    # assert
    assert run_context.run(request_context.get) is context
    assert request_context.get() is None


def test_request_context__reset_token__previous_context_restored():

    # arrange
    first = RequestContext(request_id='first')
    second = RequestContext(request_id='second')
    run_context = copy_context()
    run_context.run(request_context.set, first)
    token = run_context.run(request_context.set, second)

    # act
    run_context.run(request_context.reset, token)

    # assert
    assert run_context.run(request_context.get) is first
    assert request_context.get() is None
