"""Use real domain records where legacy tests replaced serializer outputs."""

import pytest

from src.permissions.enums import PermissionObjectType
from src.datasets.models import Dataset
from src.processes.tests.fixtures import (
    create_test_group,
    create_test_owner,
    create_test_user,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_dataset_bulk_post__real_records__matches_contract(
    contract_api_client,
) -> None:
    owner = create_test_owner()
    dataset = Dataset.objects.create(
        account=owner.account, name='Bulk dataset',
    )
    contract_api_client.token_authenticate(owner)
    payload = [{'value': 'First', 'order': 1}, {'value': 'Second', 'order': 2}]

    response = contract_api_client.post(
        f'/datasets/{dataset.id}/items', data=payload, format='json',
    )

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 2
    assert [{key: row[key] for key in ('value', 'order')} for row in rows] == (
        payload
    )
    assert set(dataset.items.values_list('id', flat=True)) == {
        row['id'] for row in rows
    }


@pytest.mark.parametrize('photo', [
    '', None, 'https://example.test/group-photo.png',
])
def test_group_put__real_membership_update__matches_contract(
    contract_api_client, photo,
) -> None:
    owner = create_test_owner()
    member = create_test_user(
        account=owner.account, email='member@example.test',
    )
    group = create_test_group(owner.account, name='Before update')
    contract_api_client.token_authenticate(owner)

    response = contract_api_client.put(
        f'/accounts/groups/{group.id}', data={
            'name': 'After update', 'photo': photo, 'users': [member.id],
        }, format='json',
    )

    assert response.status_code == 200
    assert response.json()['name'] == 'After update'
    assert response.json()['users'] == [member.id]
    assert response.json()['photo'] == (photo or '')
    group.refresh_from_db()
    assert group.name == 'After update'
    assert group.photo == (photo or '')
    assert list(group.users.values_list('id', flat=True)) == [member.id]


def test_object_permissions__real_workflows__matches_contract(
    contract_api_client,
) -> None:
    owner = create_test_owner()
    own_workflow = create_test_workflow(owner, tasks_count=1)
    foreign_owner = create_test_owner(email='other-owner@example.test')
    foreign_workflow = create_test_workflow(foreign_owner, tasks_count=1)
    contract_api_client.token_authenticate(owner)

    response = contract_api_client.get('/accounts/user/permission', data={
        'obj_type': PermissionObjectType.WORKFLOW,
        'obj_ids': f'{own_workflow.id},{foreign_workflow.id}',
    })

    assert response.status_code == 200
    assert response.json() == [
        {'id': own_workflow.id, 'has_view': True, 'has_change': True},
        {'id': foreign_workflow.id, 'has_view': False, 'has_change': False},
    ]
