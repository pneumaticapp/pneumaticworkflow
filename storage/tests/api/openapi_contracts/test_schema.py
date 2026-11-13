from fastapi.routing import APIRoute

from src.main import app


def test_openapi__all_file_operations__covered():
    # arrange
    methods = {
        'get',
        'put',
        'post',
        'delete',
        'options',
        'head',
        'patch',
        'trace',
    }
    expected = {
        (method.upper(), f'/files{route.path}')
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in route.methods
    }

    # act
    schema = app.openapi()
    actual = {
        (method.upper(), path)
        for path, item in schema['paths'].items()
        for method in item
        if method in methods
    }

    # assert
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    assert actual == expected, (
        f'Undocumented operations: {missing}\n'
        f'Documented operations without a route: {extra}'
    )
