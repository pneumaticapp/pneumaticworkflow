"""HTTP and schema regressions for the seven final-review findings."""

from copy import deepcopy

from django.urls import resolve
from drf_spectacular.generators import SchemaGenerator
import pytest

from src.accounts.enums import BillingPlanType, LeaseLevel
from src.accounts.serializers.tenant import TenantSerializer
from src.accounts.tokens import ResetPasswordToken
from src.authentication.entities import UserData
from src.authentication.messages import MSG_AU_0016
from src.authentication.services.microsoft import MicrosoftAuthService
from src.openapi.preprocessing import include_legacy_http_methods
from src.processes.serializers.templates.template import TemplateListSerializer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('url,method', [
    ('/accounts/user', 'PUT'), ('/tenants/1', 'PATCH'),
])
def test_legacy_methods__schema_generation__preserves_runtime_callback(
    url, method,
) -> None:
    # arrange
    callback = resolve(url).func
    original_class = callback.cls
    original_actions = callback.actions
    actions = original_actions.copy()

    # act
    generator = SchemaGenerator()
    document = generator.get_schema(request=None, public=True)
    endpoints = generator.endpoints
    repeated = include_legacy_http_methods(endpoints)

    # assert
    path = '/tenants/{id}' if url.startswith('/tenants/') else url
    assert method.lower() in document['paths'][path]
    assert callback.cls is original_class
    assert callback.actions is original_actions
    assert callback.actions == actions
    assert method.lower() not in callback.actions
    assert len(repeated) == len(endpoints)
    operation = next(
        entry for entry in endpoints
        if entry[0].replace('{pk}', '{id}') == path and entry[2] == method
    )
    assert operation[3] is not callback
    assert operation[3].actions[method.lower()] == method.lower()


def test_legacy_methods__only_canonical_paths__documented(
    http_contract,
) -> None:
    paths = http_contract.document['paths']
    assert 'put' not in paths['/accounts/user/permission']
    assert 'patch' not in paths['/tenants']
    assert 'patch' not in paths['/tenants/{id}/token']


def test_profile__legacy_put__updates_real_user(contract_api_client) -> None:
    # arrange
    account = create_test_account(billing_sync=False)
    owner = create_test_owner(account=account)
    contract_api_client.token_authenticate(owner)

    # act
    response = contract_api_client.put(
        '/accounts/user',
        data={'email': owner.email, 'first_name': 'Updated'}, format='json',
    )

    # assert
    assert response.status_code == 200
    owner.refresh_from_db()
    assert owner.first_name == response.json()['first_name'] == 'Updated'


def test_tenant__legacy_patch__updates_real_tenant(
    contract_api_client,
) -> None:
    # arrange
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED, billing_sync=False,
    )
    owner = create_test_owner(account=account)
    tenant = create_test_account(
        master_account=account, lease_level=LeaseLevel.TENANT,
        plan=BillingPlanType.UNLIMITED, billing_sync=False,
    )
    contract_api_client.token_authenticate(owner)

    # act
    response = contract_api_client.patch(
        f'/tenants/{tenant.id}',
        data={'tenant_name': 'Renamed'}, format='json',
    )

    # assert
    assert response.status_code == 200
    tenant.refresh_from_db()
    assert tenant.tenant_name == response.json()['tenant_name'] == 'Renamed'


@pytest.mark.parametrize('limit', [None, 1])
def test_tenant__nullable_response__input_still_rejects_null(
    contract_api_client, limit,
) -> None:
    # arrange
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED, billing_sync=False,
    )
    owner = create_test_owner(account=account)
    create_test_account(
        master_account=account, lease_level=LeaseLevel.TENANT,
        plan=BillingPlanType.UNLIMITED, tenant_name=None,
    )
    contract_api_client.token_authenticate(owner)

    # act
    response = contract_api_client.get(
        '/tenants', data={} if limit is None else {'limit': limit},
    )
    invalid = contract_api_client.post(
        '/tenants', data={'tenant_name': None}, format='json',
    )

    # assert
    assert response.status_code == 200
    data = response.json()
    tenants = data['results'] if isinstance(data, dict) else data
    assert tenants[0]['tenant_name'] is None
    assert invalid.status_code == 400
    assert TenantSerializer().fields['tenant_name'].allow_null is False


@pytest.mark.parametrize('query,body_type', [
    ({'type': 'invalid-type'}, list),
    ({'ordering': 'invalid-ordering'}, dict),
])
def test_users__invalid_filter__matches_documented_400(
    contract_api_client, query, body_type,
) -> None:
    # arrange
    owner = create_test_owner()
    contract_api_client.token_authenticate(owner)

    # act
    response = contract_api_client.get('/accounts/users', data=query)

    # assert
    assert response.status_code == 400
    assert isinstance(response.json(), body_type)


@pytest.mark.parametrize('path', [
    '/auth/reset-password', '/auth/reset-password/confirm',
    '/auth/microsoft/token',
])
def test_sso_restriction__actual_error_array__matches_contract(
    contract_api_client, path, settings, mocker,
) -> None:
    # arrange
    user = create_test_admin()
    settings.PROJECT_CONF = {
        **settings.PROJECT_CONF,
        'SSO_AUTH': True, 'MS_AUTH': True, 'CAPTCHA': False,
    }
    if path.endswith('/confirm'):
        payload = {
            'token': str(ResetPasswordToken.for_user(user)),
            'new_password': 'New-strong-password-123',
            'confirm_new_password': 'New-strong-password-123',
        }
    else:
        payload = {'email': user.email}
    if path == '/auth/microsoft/token':
        # Replace only the external identity provider, not the HTTP response.
        mocker.patch.object(MicrosoftAuthService, '_build_msal_app')
        mocker.patch.object(
            MicrosoftAuthService, 'get_user_data',
            return_value=UserData(
                email=user.email, first_name='Test', last_name='User',
                company_name='', photo=None, job_title='',
            ),
        )
        payload = {
            'code': 'provider-code', 'state': 'provider-state',
            'client_info': 'client-info', 'session_state': 'session-state',
        }

    # act
    if path == '/auth/microsoft/token':
        response = contract_api_client.get(path, data=payload)
    else:
        response = contract_api_client.post(path, data=payload, format='json')

    # assert
    assert response.status_code == 400
    assert response.json() == [str(MSG_AU_0016)]


def test_sso_error_union__field_error_object__still_valid(
    contract_api_client,
) -> None:
    response = contract_api_client.post(
        '/auth/reset-password', data={'email': 'invalid-email'}, format='json',
    )
    assert response.status_code == 400
    assert isinstance(response.json(), dict)


def test_response_metadata__only_schema_changes__runtime_flags_preserved(
    http_contract,
) -> None:
    # arrange
    fields = deepcopy(TemplateListSerializer().fields)
    document = http_contract.document
    components = document['components']['schemas']

    # assert
    template = components['TemplateList']
    assert 'workflows_count' not in template['required']
    assert template['properties']['workflows_count'] == {
        'type': 'integer', 'readOnly': True,
    }
    runtime = TemplateListSerializer().fields['workflows_count']
    assert runtime.required == fields['workflows_count'].required
    assert runtime.read_only == fields['workflows_count'].read_only is True
    tenant = components['Tenant']['properties']['tenant_name']
    assert tenant['nullable'] is True
    assert 'nullable' not in components['TenantRequest']['properties'][
        'tenant_name'
    ]
    assert 'token' in components['APIKey']['required']
    assert 'token' not in components['APIKeyReadResponse']['properties']


@pytest.mark.parametrize('path,method', [
    ('/accounts/users', 'get'),
    ('/auth/reset-password', 'post'),
    ('/auth/reset-password/confirm', 'post'),
    ('/auth/microsoft/token', 'get'),
])
def test_error_examples__match_published_response_schema(
    http_contract, path, method,
) -> None:
    media = http_contract.document['paths'][path][method]['responses'][
        '400'
    ]['content']['application/json']
    assert media['examples']
    for example in media['examples'].values():
        http_contract.validate(media['schema'], example['value'],
                               response=True)
