"""Targeted regressions for the API documentation review findings."""

from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from django.utils import timezone
from drf_spectacular.generators import SchemaGenerator
from jsonschema import Draft4Validator, RefResolver, validators
from jsonschema.exceptions import ValidationError as SchemaValidationError

from src.accounts.tokens import InviteToken
from src.ai.enums import AIVendor
from src.ai.exceptions import AIProviderException
from src.ai.models import AIProvider
from src.ai.services.provider import AIProviderService
from src.ai.tests.fixtures import create_test_prompt
from src.authentication.enums import AuthTokenType
from src.datasets.models import Dataset
from src.openapi.examples import (
    TEMPLATE_CREATE_EXAMPLE,
    TEMPLATE_DRAFT_EXAMPLE,
)
from src.processes.enums import (
    PredicateType,
    SysTemplateType,
    TaskStatus,
    WorkflowStatus,
)
from src.processes.models.templates.system_template import SystemTemplate
from src.processes.models.workflows.task import Delay
from src.processes.services.events import WorkflowEventService
from src.processes.services.templates.ai import OpenAiService
from src.processes.serializers.templates.template import TemplateSerializer
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def _nullable_type(validator, types, instance, schema):
    if instance is None and schema.get('nullable'):
        return
    yield from Draft4Validator.VALIDATORS['type'](
        validator, types, instance, schema,
    )


ContractValidator = validators.extend(
    Draft4Validator, {'type': _nullable_type},
)


@pytest.fixture(scope='module')
def review_schema() -> dict:
    return SchemaGenerator().get_schema(request=None, public=True)


def _validate(document: dict, schema: dict, value: Any) -> None:
    validator = ContractValidator(
        schema, resolver=RefResolver.from_schema(document),
    )
    errors = list(validator.iter_errors(value))
    if errors:
        pending = errors.copy()
        details = []
        while pending:
            error = pending.pop()
            if error.context:
                pending.extend(error.context)
            else:
                details.append(
                    f'{list(error.absolute_path)} {error.message[:160]}',
                )
        raise SchemaValidationError('\n'.join(details))


def _response(
    document: dict, path: str, method: str, response,
) -> Any:
    operation = document['paths'][path][method]
    contract = operation['responses'][str(response.status_code)]
    if not response.content:
        assert not contract.get('content')
        return None
    media_type = response['Content-Type'].split(';')[0]
    value = response.json()
    _validate(document, contract['content'][media_type]['schema'], value)
    return value


def _request(document: dict, path: str, method: str, value: Any) -> None:
    operation = document['paths'][path][method]
    schema = operation['requestBody']['content']['application/json']['schema']
    _validate(document, schema, value)


@pytest.mark.parametrize('action', ['retrieve', 'accept', 'decline'])
def test_invitation__uuid_round_trip__matches_schema(
    review_schema, api_client, action,
) -> None:
    # arrange
    owner = create_test_owner()
    invited = create_invited_user(owner)
    token = str(InviteToken.for_user(invited))

    # act
    response = api_client.get('/accounts/invites/token', {'token': token})
    data = _response(
        review_schema, '/accounts/invites/token', 'get', response,
    )
    invite_id = data['id']

    # assert
    assert response.status_code == 200
    assert UUID(invite_id) == invited.invite.id
    for path, method in [
        ('/accounts/invites/{id}', 'get'),
        ('/accounts/invites/{id}/accept', 'post'),
    ]:
        param = next(
            p for p in review_schema['paths'][path][method]['parameters']
            if p['in'] == 'path'
        )
        assert param['schema'] == {'type': 'string', 'format': 'uuid'}
    resend = review_schema['paths']['/accounts/invites/{id}/resend']['post']
    assert next(
        p for p in resend['parameters'] if p['in'] == 'path'
    )['schema']['type'] == 'integer'
    if action == 'retrieve':
        result = api_client.get(f'/accounts/invites/{invite_id}')
        assert result.status_code == 200
        _response(review_schema, '/accounts/invites/{id}', 'get', result)
    elif action == 'accept':
        payload = {
            'first_name': 'Jane', 'last_name': 'Doe',
            'password': 'local-test-password',
        }
        _request(
            review_schema, '/accounts/invites/{id}/accept', 'post', payload,
        )
        result = api_client.post(
            f'/accounts/invites/{invite_id}/accept', payload,
        )
        assert result.status_code == 200
        _response(
            review_schema, '/accounts/invites/{id}/accept', 'post', result,
        )
    else:
        api_client.token_authenticate(owner)
        payload = {'invite_id': invite_id}
        _request(
            review_schema, '/accounts/invites/decline', 'post', payload,
        )
        result = api_client.post('/accounts/invites/decline', payload)
        assert result.status_code == 204
        _response(
            review_schema, '/accounts/invites/decline', 'post', result,
        )


@pytest.mark.parametrize('limit', [None, 1])
@pytest.mark.parametrize('path,key', [
    ('/accounts/user', 'id'),
    ('/auth/context', 'account'),
    ('/auth/reset-password', 'status'),
])
def test_single_response__with_and_without_limit__matches_schema(
    review_schema, api_client, path, key, limit,
) -> None:
    # arrange
    owner = create_test_owner()
    api_client.token_authenticate(owner)
    params = {'token': 'invalid'} if 'reset-password' in path else {}
    if limit is not None:
        params['limit'] = limit

    # act
    response = api_client.get(path, params)
    data = _response(review_schema, path, 'get', response)

    # assert
    assert response.status_code == 200
    assert key in data
    operation = review_schema['paths'][path]['get']
    assert not {
        p['name'] for p in operation.get('parameters', [])
    } & {'limit', 'offset'}
    with pytest.raises(SchemaValidationError, match='is not of type'):
        _validate(
            review_schema,
            operation['responses']['200']['content'][
                'application/json'
            ]['schema'],
            [],
        )


@pytest.mark.parametrize('limit', [None, 1])
@pytest.mark.parametrize('path', [
    '/accounts/user/contacts',
    '/templates/export',
    '/templates/titles-by-owners',
    '/v2/tasks/{id}/events',
    '/workflows/{id}/events',
    '/workflows/fields',
])
def test_collection__real_pagination__matches_schema(
    review_schema, api_client, path, limit,
) -> None:
    # arrange
    owner = create_test_owner()
    template = create_test_template(owner, is_active=True)
    workflow = create_test_workflow(owner, template=template)
    task = workflow.tasks.get(number=1)
    WorkflowEventService.task_started_event(task)
    api_client.token_authenticate(owner)
    identifier = task.id if path.startswith('/v2/tasks') else workflow.id
    params = {} if limit is None else {'limit': limit}

    # act
    response = api_client.get(path.format(id=identifier), params)
    data = _response(review_schema, path, 'get', response)

    # assert
    assert response.status_code == 200
    if limit is not None or path == '/workflows/fields':
        assert {'count', 'next', 'previous', 'results'} <= data.keys()
    else:
        assert isinstance(data, list)


@pytest.mark.parametrize('method', ['post', 'put'])
def test_dataset_items__limit_ignored__plain_array(
    review_schema, api_client, method,
) -> None:
    # arrange
    owner = create_test_owner()
    dataset = Dataset.objects.create(account=owner.account, name='Departments')
    api_client.token_authenticate(owner)
    initial = [{'value': 'First'}, {'value': 'Second'}]
    if method == 'put':
        created = api_client.post(f'/datasets/{dataset.id}/items', initial)
        initial = created.json()
    path = '/datasets/{id}/items'
    _request(review_schema, path, method, initial)

    # act
    response = getattr(api_client, method)(
        f'/datasets/{dataset.id}/items?limit=1&offset=1', initial,
    )
    data = _response(review_schema, path, method, response)

    # assert
    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) == 2
    operation = review_schema['paths'][path][method]
    assert not {
        p['name'] for p in operation.get('parameters', [])
    } & {'limit', 'offset'}


@pytest.mark.parametrize('path', [
    '/accounts/user/permission',
    '/templates/{id}/steps',
    '/templates/{id}/presets',
    '/templates/titles-by-events',
    '/templates/titles-by-tasks',
    '/templates/titles-by-workflows',
    '/templates/integrations',
    '/workflows/count/by-current-performer',
    '/workflows/count/by-template-task',
    '/workflows/count/by-workflow-starter',
])
def test_manual_lists__pagination_not_advertised(
    review_schema, path,
) -> None:
    # arrange
    operation = review_schema['paths'][path]['get']

    # act
    schema = operation['responses']['200']['content'][
        'application/json'
    ]['schema']

    # assert
    assert schema['type'] == 'array'
    assert not {
        p['name'] for p in operation.get('parameters', [])
    } & {'limit', 'offset'}


@pytest.mark.parametrize('path', [
    '/workflows/{id}/resume',
    '/workflows/comments/{id}/watched',
    '/templates/{id}/clone',
    '/templates/{id}/discard-changes',
    '/templates/system/{id}/fill',
    '/fieldsets/{id}/clone',
    '/webhooks/unsubscribe',
    '/webhooks/events/{event}/unsubscribe',
    '/accounts/user/deactivate-vacation',
    '/accounts/users/{id}/deactivate-vacation',
])
def test_bodyless_commands__no_request_schema(
    review_schema, path,
) -> None:
    assert 'requestBody' not in review_schema['paths'][path]['post']


def test_resume__empty_request_and_nullable_delay__match_schema(
    review_schema, api_client,
) -> None:
    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(owner, status=WorkflowStatus.DELAYED)
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.DELAYED
    task.save(update_fields=['status'])
    Delay.objects.create(
        task=task, workflow=workflow, start_date=timezone.now(),
        duration=timedelta(days=1),
    )
    api_client.token_authenticate(owner)
    delayed = api_client.get(f'/v2/tasks/{task.id}')
    assert _response(
        review_schema, '/v2/tasks/{id}', 'get', delayed,
    )['delay'] is not None

    # act
    response = api_client.post(f'/workflows/{workflow.id}/resume')
    data = _response(
        review_schema, '/workflows/{id}/resume', 'post', response,
    )

    # assert
    assert response.status_code == 200
    assert data['tasks'][0]['delay'] is None
    task_response = api_client.get(f'/v2/tasks/{task.id}')
    assert task_response.status_code == 200
    assert _response(
        review_schema, '/v2/tasks/{id}', 'get', task_response,
    )['delay'] is None


@pytest.mark.parametrize('example', [
    TEMPLATE_CREATE_EXAMPLE, TEMPLATE_DRAFT_EXAMPLE,
])
def test_template_examples__create_update_retrieve__work(
    review_schema, api_client, example,
) -> None:
    # arrange
    owner = create_test_owner()
    api_client.token_authenticate(owner)
    payload = deepcopy(example.value)
    if payload['is_active']:
        payload['owners'][0]['source_id'] = str(owner.id)
        payload['tasks'][0]['raw_performers'][0]['source_id'] = str(owner.id)
    _request(review_schema, '/templates', 'post', payload)

    # act
    created = api_client.post('/templates', payload)
    data = _response(review_schema, '/templates', 'post', created)

    # assert
    assert created.status_code == 200, created.data
    assert data['is_active'] is payload['is_active']
    _request(review_schema, '/templates/{id}', 'put', payload)
    updated = api_client.put(f'/templates/{data["id"]}', payload)
    assert updated.status_code == 200, updated.data
    _response(review_schema, '/templates/{id}', 'put', updated)
    retrieved = api_client.get(f'/templates/{data["id"]}')
    assert retrieved.status_code == 200
    _response(review_schema, '/templates/{id}', 'get', retrieved)


def test_empty_draft__request_and_response__match_schema(
    review_schema, api_client,
) -> None:
    # arrange
    api_client.token_authenticate(create_test_owner())
    _request(review_schema, '/templates', 'post', {})

    # act
    response = api_client.post('/templates', {})
    data = _response(review_schema, '/templates', 'post', response)

    # assert
    assert response.status_code == 200
    assert data['is_active'] is False


@pytest.mark.parametrize('method', ['post', 'put'])
def test_draft__nullable_name__matches_schema(
    review_schema, api_client, method,
) -> None:
    # arrange
    owner = create_test_owner()
    api_client.token_authenticate(owner)
    payload = {'name': None, 'is_active': False}
    path = '/templates'
    url = path
    if method == 'put':
        initial = api_client.post('/templates', {})
        assert initial.status_code == 200
        path = '/templates/{id}'
        url = path.format(id=initial.json()['id'])

    # act
    response = getattr(api_client, method)(url, payload)

    # assert
    assert response.status_code == 200
    _request(review_schema, path, method, payload)
    data = _response(review_schema, path, method, response)
    assert data['name'] is None
    retrieved = api_client.get(f'/templates/{data["id"]}')
    assert retrieved.status_code == 200
    assert _response(
        review_schema, '/templates/{id}', 'get', retrieved,
    )['name'] is None


@pytest.mark.parametrize('method', ['post', 'put'])
@pytest.mark.parametrize('values', [
    {
        'name': 'Draft settings',
        'description': '**Draft description**',
        'wf_name_template': 'Onboarding {{ employee }}',
        'public_success_url': 'https://example.com/done',
        'finalizable': False,
        'reminder_notification': True,
        'completion_notification': False,
    },
    {
        'name': None,
        'description': None,
        'wf_name_template': None,
        'public_success_url': None,
        'finalizable': None,
        'reminder_notification': None,
        'completion_notification': None,
        'is_public': None,
        'is_embedded': None,
    },
    {
        'name': 55,
        'description': {'blocks': []},
        'wf_name_template': ['unfinished'],
        'public_success_url': 'unfinished',
        'finalizable': 'unfinished',
        'reminder_notification': 'later',
        'completion_notification': 0,
        'is_public': 'unfinished',
        'is_embedded': [],
    },
], ids=['settings', 'nulls', 'unfinished'])
def test_draft__known_settings_and_metadata__documented_round_trip(
    review_schema, api_client, method, values,
) -> None:
    # arrange
    owner = create_test_owner()
    api_client.token_authenticate(owner)
    payload = {
        'is_active': False, 'is_public': True, 'is_embedded': True,
        **deepcopy(values),
    }
    path = '/templates'
    url = path
    if method == 'put':
        initial = api_client.post('/templates', {})
        assert initial.status_code == 200
        path = '/templates/{id}'
        url = path.format(id=initial.json()['id'])

    # act
    response = getattr(api_client, method)(url, payload)

    # assert
    assert response.status_code == 200
    schemas = review_schema['components']['schemas']
    request_fields = schemas['TemplateDraftRequest']['properties']
    response_fields = schemas['TemplateDraft']['properties']
    assert payload.keys() <= request_fields.keys()
    assert set(TemplateSerializer.Meta.fields) <= response_fields.keys()
    assert response_fields['date_updated']['format'] == 'date-time'
    assert response_fields['date_updated_tsp']['type'] == 'number'
    assert response_fields['date_updated']['readOnly'] is True
    assert response_fields['date_updated_tsp']['readOnly'] is True
    assert response_fields['is_public']['type'] == 'boolean'
    assert response_fields['is_embedded']['type'] == 'boolean'
    _request(review_schema, path, method, payload)
    data = _response(review_schema, path, method, response)
    expected = {
        **payload, 'is_public': bool(payload['is_public']),
        'is_embedded': bool(payload['is_embedded']),
    }
    assert {key: data[key] for key in payload} == expected
    assert datetime.fromisoformat(data['date_updated']).timestamp() == (
        pytest.approx(data['date_updated_tsp'])
    )
    retrieved = api_client.get(f'/templates/{data["id"]}')
    assert retrieved.status_code == 200
    assert _response(
        review_schema, '/templates/{id}', 'get', retrieved,
    ) == data


@pytest.mark.parametrize('method', ['post', 'put'])
@pytest.mark.parametrize('field', ['tasks', 'owners'])
def test_active_template__empty_required_collection__rejected(
    review_schema, api_client, method, field,
) -> None:
    # arrange
    owner = create_test_owner()
    api_client.token_authenticate(owner)
    payload = deepcopy(TEMPLATE_CREATE_EXAMPLE.value)
    payload['owners'][0]['source_id'] = str(owner.id)
    payload['tasks'][0]['raw_performers'][0]['source_id'] = str(owner.id)
    path = '/templates'
    url = path
    if method == 'put':
        template = create_test_template(owner, is_active=True)
        path = '/templates/{id}'
        url = path.format(id=template.id)
    _request(review_schema, path, method, payload)
    payload[field] = []

    # act
    response = getattr(api_client, method)(url, payload)

    # assert
    assert response.status_code == 400
    _response(review_schema, path, method, response)
    with pytest.raises(SchemaValidationError):
        _request(review_schema, path, method, payload)


@pytest.mark.parametrize('tasks_count', [0, 1])
def test_discard_changes__empty_request__matches_schema(
    review_schema, api_client, tasks_count,
) -> None:
    # arrange
    owner = create_test_owner()
    template = create_test_template(owner, tasks_count=tasks_count)
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(f'/templates/{template.id}/discard-changes')

    # assert
    assert response.status_code == 204
    path = '/templates/{id}/discard-changes'
    assert 'requestBody' not in review_schema['paths'][path]['post']
    assert _response(review_schema, path, 'post', response) is None


@pytest.mark.parametrize('performer', [
    None,
    {'type': 'field', 'source_id': 'employee', 'label': 'Employee'},
    {'type': 'workflow_starter', 'source_id': None},
])
def test_system_template__unsaved_preview__matches_schema(
    review_schema, api_client, performer,
) -> None:
    # arrange
    owner = create_test_owner()
    api_client.token_authenticate(owner)
    task = {
        'name': 'Review request', 'number': 1,
        'fields': [{'name': 'Notes', 'type': 'text', 'order': 0}],
    }
    if performer is not None:
        task['raw_performers'] = [performer]
    system = SystemTemplate.objects.create(
        name='Preview', type=SysTemplateType.LIBRARY, is_active=True,
        template={
            'name': 'Preview', 'tasks': [task],
            'kickoff': {
                'fields': [{'name': 'Employee', 'type': 'user', 'order': 0}],
            },
        },
    )

    # act
    response = api_client.post(f'/templates/system/{system.id}/fill')

    # assert
    assert response.status_code == 200
    path = '/templates/system/{id}/fill'
    data = _response(review_schema, path, 'post', response)
    assert 'requestBody' not in review_schema['paths'][path]['post']
    assert not {'id', 'date_updated', 'public_url'} & data.keys()
    assert 'id' not in data['tasks'][0]
    source_id = data['tasks'][0]['raw_performers'][0]['source_id']
    expected_id = owner.id if performer is None else performer['source_id']
    assert source_id == expected_id


@pytest.mark.parametrize('shared_id', ['omitted', None, 7])
def test_system_template__nested_preview_fields__match_schema(
    review_schema, api_client, shared_id,
) -> None:
    # arrange
    owner = create_test_owner()
    api_client.token_authenticate(owner)
    field = {'name': 'Notes', 'type': 'text'}
    fieldset = {
        'title': 'Contact details', 'api_name': 'contact-details',
        'fields': [deepcopy(field)],
    }
    if shared_id != 'omitted':
        fieldset['shared_fieldset_id'] = shared_id
    system = SystemTemplate.objects.create(
        name='Nested preview', type=SysTemplateType.LIBRARY, is_active=True,
        template={
            'name': 'Nested preview',
            'kickoff': {
                'fields': [deepcopy(field)],
                'fieldsets': [deepcopy(fieldset)],
            },
            'tasks': [{
                'name': 'Review', 'number': 1,
                'fields': [deepcopy(field)],
                'fieldsets': [deepcopy(fieldset)],
            }],
        },
    )

    # act
    response = api_client.post(f'/templates/system/{system.id}/fill')

    # assert
    assert response.status_code == 200
    data = _response(
        review_schema, '/templates/system/{id}/fill', 'post', response,
    )
    for container in [data['kickoff'], data['tasks'][0]]:
        assert 'order' not in container['fields'][0]
        nested = container['fieldsets'][0]
        assert 'order' not in nested['fields'][0]
        assert nested['fields'][0]['api_name'].startswith('field-')
        if shared_id == 'omitted':
            assert 'shared_fieldset_id' not in nested
        else:
            assert nested['shared_fieldset_id'] == shared_id
    schemas = review_schema['components']['schemas']
    assert 'order' in schemas['FieldTemplateRequest']['required']
    assert 'shared_fieldset_id' in (
        schemas['FieldsetTemplateRequest']['required']
    )


def test_ai_template__real_preview_builder__matches_schema(
    review_schema, api_client, mocker,
) -> None:
    # arrange
    owner = create_test_owner()
    prompt = create_test_prompt()
    description = 'Handle a request'
    response_mock = mocker.patch.object(
        OpenAiService, '_get_response',
        return_value=(
            '1. Review | Review the request.\n2. Approve | Approve it.'
        ),
    )
    mocker.patch(
        'src.processes.views.template.AIPermission.has_permission',
        return_value=True,
    )
    api_client.token_authenticate(owner)
    payload = {'description': description}
    _request(review_schema, '/templates/ai', 'post', payload)

    # act
    response = api_client.post('/templates/ai', payload)

    # assert
    assert response.status_code == 200
    data = _response(review_schema, '/templates/ai', 'post', response)
    assert data['name'] == description
    assert len(data['tasks']) == 2
    assert 'id' not in data
    assert all('id' not in task for task in data['tasks'])
    assert data['tasks'][0]['raw_performers'][0]['source_id'] == owner.id
    response_mock.assert_called_once_with(
        prompt=prompt, user_description=description,
    )


def test_provider__custom_vendor_and_empty_error_details__match_schema(
    review_schema, api_client, mocker,
) -> None:
    # arrange
    owner = create_test_owner()
    provider = AIProvider(
        account=owner.account, name='External',
        base_url='https://example.com/v1', vendor=AIVendor.CUSTOM,
    )
    provider.api_key = 'local-provider-test-key'
    provider.save()
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(f'/ai/providers/{provider.id}')
    data = _response(review_schema, '/ai/providers/{id}', 'get', response)

    # assert
    assert response.status_code == 200
    assert data['vendor'] == 'custom'
    mocker.patch.object(
        AIProviderService, 'get_models',
        side_effect=AIProviderException(message='Provider unavailable'),
    )
    response = api_client.get(f'/ai/providers/{provider.id}/models')
    assert response.status_code == 400
    assert _response(
        review_schema, '/ai/providers/{id}/models', 'get', response,
    )['details'] == {}


def test_api_key__field_validation_error__matches_schema(
    review_schema, api_client,
) -> None:
    api_client.token_authenticate(create_test_owner())
    response = api_client.post('/accounts/api-keys', {'name': 'x' * 201})
    assert response.status_code == 400
    assert 'name' in _response(
        review_schema, '/accounts/api-keys', 'post', response,
    )


@pytest.mark.parametrize('path', [
    '/auth/token/obtain', '/auth/change-password',
])
def test_sso_restriction__message_array__matches_schema(
    review_schema, api_client, settings, path,
) -> None:
    # arrange
    user = create_test_not_admin()
    user.set_password('old-local-password')
    user.save()
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'SSO_AUTH': True}
    payload = {'username': user.email, 'password': 'old-local-password'}
    if path == '/auth/change-password':
        api_client.token_authenticate(user)
        payload = {
            'old_password': 'old-local-password',
            'new_password': 'new-local-password',
            'confirm_new_password': 'new-local-password',
        }

    # act
    response = api_client.post(path, payload)
    data = _response(review_schema, path, 'post', response)

    # assert
    assert response.status_code == 400
    assert isinstance(data, list)
    assert all(isinstance(message, str) for message in data)


@pytest.mark.parametrize('path,schema_path', [
    ('/webhooks/unsubscribe', '/webhooks/unsubscribe'),
    (
        '/webhooks/events/workflow_started/unsubscribe',
        '/webhooks/events/{event}/unsubscribe',
    ),
])
def test_webhook_unsubscribe__empty_request__matches_schema(
    review_schema, api_client, path, schema_path,
) -> None:
    api_client.token_authenticate(create_test_owner())
    response = api_client.post(path)
    assert response.status_code == 204
    _response(review_schema, schema_path, 'post', response)


@pytest.mark.parametrize('method', ['get', 'post'])
def test_public_template__missing_token__documented_401(
    review_schema, api_client, method,
) -> None:
    path = '/templates/public' + ('/run' if method == 'post' else '')
    response = getattr(api_client, method)(path)
    assert response.status_code == 401
    _response(review_schema, path, method, response)


@pytest.mark.parametrize('path,params', [
    ('/datasets', {'ordering': 'invalid'}),
    ('/tenants', {'ordering': 'invalid'}),
    ('/workflows/fields', {'template_id': 'invalid'}),
])
def test_bad_query__documented_400(
    review_schema, api_client, path, params,
) -> None:
    owner = create_test_owner()
    api_client.token_authenticate(owner)
    response = api_client.get(path, params)
    assert response.status_code == 400
    _response(review_schema, path, 'get', response)


@pytest.mark.parametrize('path', [
    '/v2/tasks/webhook-example', '/workflows/webhook-example',
])
def test_missing_webhook_example__empty_404__matches_schema(
    review_schema, api_client, path,
) -> None:
    api_client.token_authenticate(create_test_owner())
    response = api_client.get(path)
    assert response.status_code == 404
    assert _response(review_schema, path, 'get', response) is None


@pytest.mark.parametrize('check_ip', [False, True])
def test_private_api_key__ip_gate__matches_security(
    api_client, settings, check_ip,
) -> None:
    # arrange
    settings.PRIVATE_API_CHECK_IP = check_ip
    settings.PRIVATE_API_IP_WHITELIST = ['192.168.0.1']
    owner = create_test_owner()
    api_client.token_authenticate(owner, token_type=AuthTokenType.API)
    schema = SchemaGenerator().get_schema(request=None, public=True)

    # act
    response = api_client.post('/auth/signout', HTTP_REMOTE_ADDR='192.168.0.1')
    operation = schema['paths']['/auth/signout']['post']

    # assert
    assert response.status_code == (403 if check_ip else 204)
    assert ({'apiKeyAuth': []} in operation['security']) is not check_ip
    _response(schema, '/auth/signout', 'post', response)


def test_published_json_examples__conform_to_schemas(
    review_schema,
) -> None:
    for path, operations in review_schema['paths'].items():
        for method, operation in operations.items():
            media = operation.get('requestBody', {}).get('content', {}).get(
                'application/json', {},
            )
            for example in media.get('examples', {}).values():
                if 'value' in example:
                    _request(review_schema, path, method, example['value'])
            for response in operation['responses'].values():
                media = response.get('content', {}).get(
                    'application/json', {},
                )
                for example in media.get('examples', {}).values():
                    if 'value' in example:
                        _validate(
                            review_schema, media['schema'], example['value'],
                        )


def test_predicate_types__distinct_from_form_fields__preserved(
    review_schema,
) -> None:
    schemas = review_schema['components']['schemas']
    field = schemas['PredicateTemplate']['properties']['field_type']
    choices = schemas[field['$ref'].rsplit('/', 1)[1]]['enum']
    assert set(choices) == {value for value, _ in PredicateType.CHOICES}
