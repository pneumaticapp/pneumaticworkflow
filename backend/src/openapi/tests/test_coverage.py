"""Compare the Django REST API routes with the generated OpenAPI paths."""

from django.urls import reverse
from drf_spectacular.generators import EndpointEnumerator, SchemaGenerator


def test_api_routes__generated_openapi__matches_registered_methods():

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

    # act
    schema = generator.get_schema(request=None, public=True)

    # assert
    documented = {
        (method.upper(), path)
        for path, operations in schema['paths'].items()
        for method in operations
        if method in methods
    }
    missing = sorted(registered - documented)
    extra = sorted(documented - registered)
    assert not (missing or extra), (
        f'Undocumented operations: {missing}\n'
        f'Documented operations without a route: {extra}'
    )
