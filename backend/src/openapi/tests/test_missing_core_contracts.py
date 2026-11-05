"""Exercise legacy mutations through their real serializers and services."""

from django.contrib.auth import get_user_model
import pytest

from src.accounts.enums import BillingPlanType
from src.datasets.models import Dataset, DatasetItem
from src.processes.enums import PresetType
from src.processes.models.templates.preset import TemplatePreset
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_template,
    create_test_template_preset,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db
UserModel = get_user_model()


@pytest.fixture
def mutation_owner(contract_api_client) -> UserModel:
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED, billing_sync=False,
    )
    owner = create_test_owner(account=account)
    contract_api_client.token_authenticate(owner)
    return owner


@pytest.fixture
def mutation_dataset(mutation_owner) -> Dataset:
    return Dataset.objects.create(
        account=mutation_owner.account, name='Contract dataset',
    )


@pytest.fixture
def mutation_preset(mutation_owner) -> TemplatePreset:
    template = create_test_template(mutation_owner, is_active=True)
    return create_test_template_preset(template, mutation_owner)


def test_dataset_items__real_crud_sequence__matches_contract(
    contract_api_client, mutation_dataset,
) -> None:
    dataset = mutation_dataset
    removed = DatasetItem.objects.create(
        account=dataset.account, dataset=dataset, value='Remove me', order=2,
    )

    created = contract_api_client.post(
        f'/datasets/{dataset.id}/item',
        data={'value': 'Created', 'order': 1}, format='json',
    )

    assert created.status_code == 201
    item_id = created.json()['id']
    assert created.json() == {'id': item_id, 'value': 'Created', 'order': 1}
    assert DatasetItem.objects.get(id=item_id).value == 'Created'

    replaced = contract_api_client.put(
        f'/datasets/{dataset.id}/items',
        data=[
            {'id': item_id, 'value': 'Replaced', 'order': 3},
            {'value': 'Another', 'order': 1},
        ],
        format='json',
    )

    assert replaced.status_code == 200
    rows = replaced.json()
    assert [(row['value'], row['order']) for row in rows] == [
        ('Another', 1), ('Replaced', 3),
    ]
    assert rows[1]['id'] == item_id
    removed.refresh_from_db()
    assert removed.is_deleted

    updated = contract_api_client.patch(
        f'/datasets/items/{item_id}',
        data={'value': 'Patched'}, format='json',
    )

    assert updated.status_code == 200
    assert updated.json() == {'id': item_id, 'value': 'Patched', 'order': 3}
    item = DatasetItem.objects.get(id=item_id)
    assert item.value == 'Patched'

    deleted = contract_api_client.delete(f'/datasets/items/{item_id}')

    assert deleted.status_code == 204
    assert deleted.content == b''
    item.refresh_from_db()
    assert item.is_deleted
    assert dataset.items.filter(is_deleted=False).count() == 1


@pytest.mark.parametrize('method, path, as_list', [
    ('post', '/datasets/{dataset_id}/item', False),
    ('post', '/datasets/{dataset_id}/items', True),
    ('put', '/datasets/{dataset_id}/items', True),
    ('patch', '/datasets/items/{item_id}', False),
])
def test_dataset_items__overlong_value__matches_error_contract(
    contract_api_client, mutation_dataset, method, path, as_list,
) -> None:
    dataset = mutation_dataset
    item = DatasetItem.objects.create(
        account=dataset.account, dataset=dataset, value='Unchanged', order=1,
    )
    payload = {'value': 'x' * 201, 'order': 2}

    response = getattr(contract_api_client, method)(
        path.format(dataset_id=dataset.id, item_id=item.id),
        data=[payload] if as_list else payload, format='json',
    )

    assert response.status_code == 400
    item.refresh_from_db()
    assert item.value == 'Unchanged'
    assert not item.is_deleted
    assert dataset.items.count() == 1


@pytest.mark.parametrize('method, path, payload', [
    ('post', '/datasets/2147483647/item', {'value': 'New'}),
    ('put', '/datasets/2147483647/items', [{'value': 'New'}]),
    ('patch', '/datasets/items/2147483647', {'value': 'New'}),
    ('delete', '/datasets/items/2147483647', None),
])
def test_dataset_items__unknown_resource__matches_error_contract(
    contract_api_client, mutation_owner, method, path, payload,
) -> None:
    response = getattr(contract_api_client, method)(
        path, data=payload, format='json',
    )

    assert response.status_code == 404


def test_workflow_put__real_update__matches_contract(
    contract_api_client, mutation_owner,
) -> None:
    workflow = create_test_workflow(mutation_owner)
    original_urgency = workflow.is_urgent
    original_template = workflow.template_id

    response = contract_api_client.put(
        f'/workflows/{workflow.id}',
        data={'name': 'Updated through PUT'}, format='json',
    )

    assert response.status_code == 200
    assert response.json()['name'] == 'Updated through PUT'
    workflow.refresh_from_db()
    assert workflow.name == 'Updated through PUT'
    assert workflow.name_template == 'Updated through PUT'
    assert workflow.is_urgent == original_urgency
    assert workflow.template_id == original_template


def test_workflow_put__invalid_field__matches_error_contract(
    contract_api_client, mutation_owner,
) -> None:
    workflow = create_test_workflow(mutation_owner)
    original_name = workflow.name

    response = contract_api_client.put(
        f'/workflows/{workflow.id}',
        data={'name': 'Invalid update', 'is_urgent': 'invalid'}, format='json',
    )

    assert response.status_code == 400
    workflow.refresh_from_db()
    assert workflow.name == original_name


def test_workflow_put__unknown_resource__matches_error_contract(
    contract_api_client, mutation_owner,
) -> None:
    response = contract_api_client.put(
        '/workflows/2147483647', data={'name': 'New'}, format='json',
    )

    assert response.status_code == 404


def test_preset_patch__full_payload__matches_contract(
    contract_api_client, mutation_preset,
) -> None:
    preset = mutation_preset
    fields = [{'api_name': 'contract_field', 'order': 0, 'width': 320}]

    response = contract_api_client.patch(
        f'/templates/presets/{preset.id}',
        data={
            'name': 'Updated preset', 'type': PresetType.PERSONAL,
            'is_default': True, 'fields': fields,
        },
        format='json',
    )

    assert response.status_code == 200
    body = response.json()
    assert body['id'] == preset.id
    assert body['name'] == 'Updated preset'
    assert body['is_default'] is True
    assert body['fields'] == fields
    preset.refresh_from_db()
    assert preset.name == 'Updated preset'
    assert preset.is_default
    assert list(preset.fields.values('api_name', 'order', 'width')) == fields


def test_preset_patch__missing_required_fields__matches_error_contract(
    contract_api_client, mutation_preset,
) -> None:
    original_name = mutation_preset.name

    response = contract_api_client.patch(
        f'/templates/presets/{mutation_preset.id}', data={}, format='json',
    )

    assert response.status_code == 400
    mutation_preset.refresh_from_db()
    assert mutation_preset.name == original_name


def test_preset_patch__schema_keeps_full_request_requiredness(
    http_contract,
) -> None:
    operation = http_contract.document['paths'][
        '/templates/presets/{id}'
    ]['patch']
    request = http_contract.resolve(operation['requestBody'])
    schema = http_contract.resolve(
        request['content']['application/json']['schema'],
    )

    assert request['required'] is True
    assert {'name', 'type', 'fields'} <= set(schema['required'])


def test_preset_patch__unknown_resource__matches_error_contract(
    contract_api_client, mutation_owner,
) -> None:
    response = contract_api_client.patch(
        '/templates/presets/2147483647',
        data={'name': 'New', 'type': PresetType.PERSONAL, 'fields': []},
        format='json',
    )

    assert response.status_code == 403


@pytest.mark.parametrize('method, path, payload', [
    ('post', '/datasets/1/item', {'value': 'New'}),
    ('put', '/datasets/1/items', [{'value': 'New'}]),
    ('patch', '/datasets/items/1', {'value': 'New'}),
    ('delete', '/datasets/items/1', None),
    ('put', '/workflows/1', {'name': 'New'}),
    ('patch', '/templates/presets/1', {
        'name': 'New', 'type': PresetType.PERSONAL, 'fields': [],
    }),
])
def test_mutations__missing_auth__matches_error_contract(
    contract_api_client, method, path, payload,
) -> None:
    response = getattr(contract_api_client, method)(
        path, data=payload, format='json',
    )

    assert response.status_code == 401
