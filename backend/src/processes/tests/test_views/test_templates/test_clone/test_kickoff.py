import pytest
from src.processes.tests.fixtures import (
    create_test_user,
)
from src.processes.models.templates.template import Template
from src.processes.enums import (
    PerformerType,
    OwnerType,
)

pytestmark = pytest.mark.django_db


class TestCopyKickoff:

    @pytest.mark.parametrize('is_active', [True, False])
    def test_clone__ok(self, is_active, api_client):

        user = create_test_user()
        api_client.token_authenticate(user)

        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': is_active,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                            },
                        ],
                    },
                ],
            },
        )
        template = Template.objects.get(id=response.data['id'])

        # act
        response = api_client.post(
            f'/templates/{template.id}/clone',
        )

        # assert
        assert response.status_code == 200
        response_data = response.data['kickoff']
        assert response_data['fields'] == []
