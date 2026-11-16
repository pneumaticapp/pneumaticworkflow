"""Compare the public Django REST routes with the generated OpenAPI paths."""

from django.urls import reverse
from drf_spectacular.generators import EndpointEnumerator, SchemaGenerator

from src.openapi.enums import EXCLUDED_OPERATIONS


def test_api_routes__generated_openapi__matches_public_methods():

    # arrange
    generator = SchemaGenerator()
    enumerator = EndpointEnumerator()
    endpoints = enumerator._get_api_endpoints(patterns=None, prefix='')
    docs_paths = {reverse('schema'), reverse('scalar-ui')}
    methods = {'get', 'post', 'put', 'patch', 'delete'}
    # These methods are implemented directly on their legacy views.
    legacy_methods = {
        '/accounts/user': 'put',
        '/tenants/{pk}': 'patch',
    }
    registered = set()

    for path, _regex, method, callback in endpoints:
        if path in docs_paths:
            continue

        view = generator.create_view(callback=callback, method=method)
        api_path = generator.coerce_path(path=path, method=method, view=view)
        registered.add((method, api_path))

        legacy_method = legacy_methods.get(path)
        if (
            legacy_method in view.http_method_names
            and callable(getattr(view, legacy_method, None))
        ):
            registered.add((legacy_method.upper(), api_path))

    expected = registered - EXCLUDED_OPERATIONS

    # act
    schema = generator.get_schema(request=None, public=True)

    documented = {
        (method.upper(), path)
        for path, operations in schema['paths'].items()
        for method in operations
        if method in methods
    }
    stale_exclusions = sorted(EXCLUDED_OPERATIONS - registered)
    missing = sorted(expected - documented)
    extra = sorted(documented - expected)

    # assert
    assert not stale_exclusions, f'Excluded operations without a route: {
        stale_exclusions
    }'
    assert not (missing or extra), (
        f'Undocumented public operations: {missing}\n'
        f'Unexpected operations in public OpenAPI: {extra}'
    )
