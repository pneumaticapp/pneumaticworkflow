import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user
)
from pneumatic_backend.processes.models import (
    Template
)
from pneumatic_backend.processes.enums import PerformerType

pytestmark = pytest.mark.django_db


class TestCopyKickoff:

    @pytest.mark.parametrize('is_active', [True, False])
    def test_clone__ok(self, is_active, api_client):

        user = create_test_user()
        api_client.token_authenticate(user)

        request_data = {
            'description': 'Desc'
        }

        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': is_active,
                'template_owners': [user.id],
                'kickoff': request_data,
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
                    }
                ]
            }
        )
        template = Template.objects.get(id=response.data['id'])

        # act
        response = api_client.post(
            f'/templates/{template.id}/clone'
        )

        template = Template.objects.get(id=response.data['id'])
        kickoff = template.kickoff_instance

        # assert
        assert response.status_code == 200
        response_data = response.data['kickoff']
        assert response_data['id'] == kickoff.id
        assert response_data['fields'] == []
        assert response_data['description'] == request_data['description']
