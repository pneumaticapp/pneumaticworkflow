import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user
)
from pneumatic_backend.processes.models import (
    Template
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    FieldType,
    OwnerType
)

pytestmark = pytest.mark.django_db


class TestCopyKickoffFields:

    @pytest.mark.parametrize('is_active', [True, False])
    def test_clone__ok(self, is_active, api_client):

        user = create_test_user()
        api_client.token_authenticate(user)

        request_data = {
            'name': 'Name',
            'description': 'Desc',
            'type': FieldType.USER,
            'is_required': True,
            'order': 1,
            'api_name': 'field-1'
        }

        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'wf_name_template': 'Workflow {{ field-1 }}',
                'is_active': is_active,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id
                    },
                ],
                'kickoff': {
                    'fields': [request_data],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
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
        template = Template.objects.get(id=response.data['id'])
        response_1_data = response.data['kickoff']['fields'][0]

        # act
        response = api_client.post(
            f'/templates/{template.id}/clone'
        )

        # assert
        assert response.status_code == 200
        assert response.data['wf_name_template'] == 'Workflow {{ field-1 }}'
        assert len(response.data['kickoff']['fields']) == 1
        response_2_data = response.data['kickoff']['fields'][0]
        assert not response_2_data.get('id')
        assert response_2_data['api_name'] == response_1_data['api_name']
        assert response_2_data['name'] == request_data['name']
        assert response_2_data['description'] == request_data['description']
        assert response_2_data['type'] == request_data['type']
        assert response_2_data['is_required'] == request_data['is_required']
        assert response_2_data['order'] == request_data['order']
