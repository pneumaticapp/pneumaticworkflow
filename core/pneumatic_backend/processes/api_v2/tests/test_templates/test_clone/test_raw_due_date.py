import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    DueDateRule,
    FieldType,
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
            'kickoff': {
                'fields': [
                    {
                        'name': 'Date field',
                        'order': 1,
                        'type': FieldType.DATE,
                        'api_name': 'field-1'
                    }
                ]
            },
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'raw_due_date': {
                        'api_name': 'raw-due-date-1',
                        'duration': '01:00:00',
                        'duration_months': 10,
                        'rule': DueDateRule.AFTER_FIELD,
                        'source_id': 'field-1'
                    },
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
    origin_data = response_1.data['tasks'][0]['raw_due_date']

    # act
    response = api_client.post(
        f'/templates/{response_1.data["id"]}/clone'
    )

    # assert
    assert response.status_code == 200
    data = response.data['tasks'][0]['raw_due_date']
    assert data.get('id') is None
    assert origin_data['api_name'] == data['api_name']
    assert origin_data['duration'] == data['duration']
    assert origin_data['duration_months'] == data['duration_months']
    assert origin_data['rule'] == data['rule']
    assert origin_data['source_id'] == data['source_id']
