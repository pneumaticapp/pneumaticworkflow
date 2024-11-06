import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user
)
from pneumatic_backend.processes.models import (
    Template
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    FieldType
)

pytestmark = pytest.mark.django_db


class TestCopyFieldSelections:

    @pytest.mark.parametrize('is_active', [True, False])
    def test_clone__ok(self, is_active, api_client):

        user = create_test_user()
        api_client.token_authenticate(user)

        request_data = {
            'value': 'Changed first selection',
            'api_name': 'selection-1'
        }

        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': is_active,
                'template_owners': [user.id],
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                        'fields': [
                            {
                                'name': 'Name',
                                'description': 'Desc',
                                'type': FieldType.RADIO,
                                'is_required': False,
                                'order': 1,
                                'api_name': 'field-name-1',
                                'selections': [request_data]
                            }
                        ]
                    }
                ]
            }
        )
        template = Template.objects.get(id=response.data['id'])
        response_1_data = (
            response.data['tasks'][0]['fields'][0]['selections'][0]
        )

        # act
        response = api_client.post(
            f'/templates/{template.id}/clone'
        )

        # assert
        assert response.status_code == 200
        assert len(
            response.data['tasks'][0]['fields'][0]['selections']
        ) == 1
        response_2_data = (
            response.data['tasks'][0]['fields'][0]['selections'][0]
        )
        assert not response_2_data.get('id')
        assert response_2_data['api_name'].startswith('selection-')
        assert response_2_data['api_name'] == response_1_data['api_name']
        assert response_2_data['value'] == request_data['value']
