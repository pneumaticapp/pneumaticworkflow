import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user
)
from pneumatic_backend.processes.enums import (
    PerformerType,
)

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('is_active', [True, False])
def test_clone__ok(is_active, api_client):

    user = create_test_user()
    api_client.token_authenticate(user)
    response_1 = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': is_active,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'checklists': [
                        {
                            'api_name': 'checklist-1',
                            'selections': [
                                {
                                    'api_name': 'cl-selection-1',
                                    'value': 'some value 1'
                                }
                            ]
                        }
                    ],
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )
    origin_checklist_data = response_1.data['tasks'][0]['checklists'][0]

    # act
    response = api_client.post(
        f'/templates/{response_1.data["id"]}/clone'
    )

    # assert
    assert response.status_code == 200
    checklist_data = response.data['tasks'][0]['checklists'][0]
    assert checklist_data.get('id') is None
    assert origin_checklist_data['api_name'] == checklist_data['api_name']
