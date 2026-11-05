"""Regression contracts for formerly hidden product and provider endpoints."""

from typing import Any, Dict

import pytest
from drf_spectacular.generators import SchemaGenerator

pytestmark = pytest.mark.django_db

Schema = Dict[str, Any]


@pytest.fixture(scope='module')
def internal_schema() -> Schema:
    return SchemaGenerator().get_schema(request=None, public=True)


def _resolve_schema(document: Schema, schema: Schema) -> Schema:
    while '$ref' in schema:
        name = schema['$ref'].rsplit('/', 1)[1]
        schema = document['components']['schemas'][name]
    if len(schema.get('allOf', [])) == 1:
        schema = {
            **_resolve_schema(document, schema['allOf'][0]),
            **{key: value for key, value in schema.items() if key != 'allOf'},
        }
    return schema


def _request_schema(document: Schema, operation: Schema) -> Schema:
    schema = operation['requestBody']['content']['application/json']['schema']
    return _resolve_schema(document, schema)


def _response_schema(
    document: Schema,
    operation: Schema,
    status: str = '200',
    media_type: str = 'application/json',
) -> Schema:
    schema = operation['responses'][status]['content'][media_type]['schema']
    return _resolve_schema(document, schema)


def _assert_unpaginated(operation: Schema):
    query_names = {
        parameter['name']
        for parameter in operation.get('parameters', [])
        if parameter['in'] == 'query'
    }
    assert not query_names & {'limit', 'offset'}


def test_invites__list_create_detail__distinct_shapes(internal_schema):
    """Invitation list is an array; create and detail return objects."""
    # arrange
    paths = internal_schema['paths']
    list_operation = paths['/accounts/invites']['get']
    create_operation = paths['/accounts/invites']['post']
    detail_operation = paths['/accounts/invites/{id}']['get']

    # act
    listing = _response_schema(internal_schema, list_operation)
    created = _response_schema(internal_schema, create_operation)
    detail = _response_schema(internal_schema, detail_operation)
    item = _resolve_schema(internal_schema, listing['items'])

    # assert
    assert listing['type'] == 'array'
    assert {'id', 'email', 'status'} <= item['properties'].keys()
    assert created['type'] == 'object'
    assert created['properties']['already_accepted']['type'] == 'array'
    assert detail['type'] == 'object'
    assert {'id', 'email', 'status'} <= detail['properties'].keys()
    _assert_unpaginated(list_operation)


def test_public_account__single_object_and_public_token__ok(internal_schema):
    """The list-named public action returns one account, not an array."""
    # arrange
    operation = internal_schema['paths']['/accounts/public/account']['get']

    # act
    response = _response_schema(internal_schema, operation)
    properties = response['properties']

    # assert
    assert response['type'] == 'object'
    assert {'id', 'name', 'language', 'timezone'} <= properties.keys()
    assert properties['date_fdw']['type'] == 'integer'
    assert properties['language']['type'] == 'string'
    assert operation['security'] == [{'publicTemplateAuth': []}]
    _assert_unpaginated(operation)


def test_products__plain_array_with_prices__ok(internal_schema):
    """The catalog is an array, with a nested price array per product."""
    # arrange
    operation = internal_schema['paths']['/payment/products']['get']

    # act
    response = _response_schema(internal_schema, operation)
    product = _resolve_schema(internal_schema, response['items'])
    prices = product['properties']['prices']

    # assert
    assert response['type'] == 'array'
    assert {'code', 'name', 'prices'} <= product['properties'].keys()
    assert prices['type'] == 'array'
    price = _resolve_schema(internal_schema, prices['items'])
    assert {'code', 'price', 'currency'} <= price['properties'].keys()
    _assert_unpaginated(operation)


@pytest.mark.parametrize('path', ['/auth/signup', '/auth/reset-password'])
def test_conditional_captcha__optional_string_with_requirement__ok(
    internal_schema,
    path,
):
    """Captcha is conditional, not unconditionally required by the schema."""
    # arrange
    operation = internal_schema['paths'][path]['post']

    # act
    request = _request_schema(internal_schema, operation)
    captcha = request['properties']['captcha']

    # assert
    assert captcha['type'] == 'string'
    assert 'captcha' not in request.get('required', [])
    assert 'show_captcha=true' in captcha['description']
    assert not operation.get('security')


def test_signup_captcha__flag_and_access_gates__documented(internal_schema):
    # arrange
    operation = internal_schema['paths']['/auth/signup']['get']

    # act
    response = _response_schema(internal_schema, operation)

    # assert
    assert response['properties']['show_captcha']['type'] == 'boolean'
    assert 'source-IP' in operation['description']
    assert 'Signup must be enabled' in operation['description']
    assert not operation.get('security')


def test_password_reset__empty_204_success__ok(internal_schema):
    """Both known and unknown email paths acknowledge with no content."""
    # arrange
    operation = internal_schema['paths']['/auth/reset-password']['post']

    # act
    responses = operation['responses']

    # assert
    assert '204' in responses
    assert 'content' not in responses['204']
    assert '200' not in responses
    assert {'400', '429'} <= responses.keys()
    assert 'unknown email' in operation['description']


def test_password_signin__session_token_not_jwt_pair__ok(internal_schema):
    """Password login returns an opaque token and bad credentials are 403."""
    # arrange
    operation = internal_schema['paths']['/auth/token/obtain']['post']

    # act
    request = _request_schema(internal_schema, operation)
    response = _response_schema(internal_schema, operation)

    # assert
    assert {'username', 'password'} <= set(request['required'])
    assert request['properties']['password']['writeOnly'] is True
    assert response['properties']['token']['type'] == 'string'
    assert not {'access', 'refresh'} & response['properties'].keys()
    assert '403' in operation['responses']
    assert '401' not in operation['responses']
    assert not operation.get('security')


@pytest.mark.parametrize(
    'provider, status',
    [('google', '200'), ('microsoft', '204'), ('auth0', '204')],
)
def test_provider_logout__different_success_bodies__ok(
    internal_schema,
    provider,
    status,
):
    # arrange
    operation = internal_schema['paths'][f'/auth/{provider}/logout']['get']

    # act
    response = operation['responses'][status]

    # assert
    assert not operation.get('security')
    if status == '200':
        body = _response_schema(internal_schema, operation)
        assert body['type'] == 'object'
        assert body.get('properties', {}) == {}
        assert body['additionalProperties'] is False
    else:
        assert 'content' not in response
        assert '200' not in operation['responses']


@pytest.mark.parametrize(
    'path',
    ['/accounts/digest/unsubscribe', '/accounts/emails/unsubscribe'],
)
def test_unsubscribe__html_200_not_http_redirect__ok(internal_schema, path):
    # arrange
    operation = internal_schema['paths'][path]['get']

    # act
    response = _response_schema(
        internal_schema,
        operation,
        media_type='text/html',
    )

    # assert
    assert response['type'] == 'string'
    assert '302' not in operation['responses']
    assert not operation.get('security')


def test_legacy_transfer__html_and_redirect_outcomes__ok(internal_schema):
    # arrange
    path = '/accounts/users/{id}/transfer'
    operation = internal_schema['paths'][path]['get']

    # act
    response = _response_schema(
        internal_schema,
        operation,
        media_type='text/html',
    )
    redirect = operation['responses']['302']
    query_token = next(
        parameter
        for parameter in operation['parameters']
        if parameter['in'] == 'query' and parameter['name'] == 'token'
    )

    # assert
    assert response['type'] == 'string'
    assert redirect['headers']['Location']['schema']['type'] == 'string'
    assert 'content' not in redirect
    assert query_token['required'] is True
    assert not operation.get('security')


def test_customerio__provider_signature_and_timestamp__required(
    internal_schema,
):
    """The signature and its timestamp are a provider-specific contract."""
    # arrange
    operation = internal_schema['paths']['/analytics/customerio/webhooks'][
        'post'
    ]

    # act
    signature = internal_schema['components']['securitySchemes'][
        'customerIOSignature'
    ]
    timestamp = next(
        parameter
        for parameter in operation['parameters']
        if parameter['in'] == 'header'
        and parameter['name'] == 'X-CIO-Timestamp'
    )

    # assert
    assert operation['security'] == [{'customerIOSignature': []}]
    assert signature['type'] == 'apiKey'
    assert signature['in'] == 'header'
    assert signature['name'] == 'X-CIO-Signature'
    assert timestamp['required'] is True
    assert 'HMAC-SHA256' in operation['description']
    assert 'exact raw request bytes' in operation['description']
    assert 'content' not in operation['responses']['400']


def test_okta_logout__provider_token_and_async_acknowledgement__ok(
    internal_schema,
):
    # arrange
    operation = internal_schema['paths']['/auth/okta/logout']['post']

    # act
    scheme = internal_schema['components']['securitySchemes']['oktaLogoutAuth']

    # assert
    assert operation['security'] == [{'oktaLogoutAuth': []}]
    assert scheme['type'] == 'http'
    assert scheme['scheme'] == 'bearer'
    assert scheme['bearerFormat'] == 'JWT'
    assert 'content' not in operation['responses']['204']
    assert '403' in operation['responses']
    assert 'malformed' in operation['description']
    assert 'asynchronous' in operation['description']


def test_stripe_webhook__ip_gate_and_receipt_only__documented(internal_schema):
    """Do not advertise signature verification that the handler lacks."""
    # arrange
    operation = internal_schema['paths']['/payment/stripe/webhooks']['post']

    # act
    description = operation['description']

    # assert
    assert not operation.get('security')
    assert 'source-IP allowlist' in description
    assert 'does not verify' in description
    assert 'Stripe-Signature' in description
    assert 'content' not in operation['responses']['204']
    assert not any(
        parameter['in'] == 'header'
        and parameter['name'] == 'Stripe-Signature'
        and parameter.get('required')
        for parameter in operation.get('parameters', [])
    )
