import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user
)
from pneumatic_backend.processes.models import (
    Template,
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    FieldType
)
from pneumatic_backend.authentication.enums import AuthTokenType


pytestmark = pytest.mark.django_db


class TestCopyTemplateTask:

    @pytest.mark.parametrize('is_active', [True, False])
    def test_clone__ok(self, is_active, api_client):

        user = create_test_user()
        api_client.token_authenticate(user)

        request_data = {
            'number': 1,
            'name': '{{field-2}}',
            'description': '{{field-2}}',
            'delay': None,
            'require_completion_by_all': False,
            'raw_performers': [
                {
                    'type': PerformerType.USER,
                    'source_id': str(user.id)
                }
            ]
        }

        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': is_active,
                'template_owners': [user.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'Task name',
                            'type': FieldType.STRING,
                            'api_name': 'field-2',
                            'is_required': True,
                        },
                        {
                            'order': 0,
                            'name': 'User name',
                            'type': FieldType.USER,
                            'api_name': 'without_prefix_name',
                            'is_required': True,
                        }
                    ]
                },
                'tasks': [request_data]
            }
        )
        template = Template.objects.get(id=response.data['id'])

        # act
        response = api_client.post(
            f'/templates/{template.id}/clone'
        )

        # assert
        assert response.status_code == 200
        assert len(response.data['tasks']) == 1
        task_data = response.data['tasks'][0]
        assert not task_data.get('id')
        assert task_data['number'] == request_data['number']
        assert task_data['name'] == '{{field-2}}'
        assert task_data['description'] == '{{field-2}}'
        assert task_data['delay'] == request_data['delay']
        assert task_data['require_completion_by_all'] == (
            request_data['require_completion_by_all']
        )
        performers = task_data['raw_performers']
        assert len(performers) == 1
        assert performers[0]['type'] == PerformerType.USER
        assert performers[0]['source_id'] == str(user.id)

    def test_clone__due_date__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        analytics_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.serializers.template.task.'
            'AnalyticService.templates_task_due_date_created'
        )
        user = create_test_user()
        api_client.token_authenticate(user)
        duration = '10:00:00'

        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'template_owners': [user.id],
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First Step',
                        'api_name': 'task-1',
                        'raw_performers': [{
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }],
                        'raw_due_date': {
                            'api_name': 'raw-due-date-bwybf0',
                            'rule': 'after task started',
                            'duration_months': 0,
                            'duration': duration,
                            'source_id': 'task-1'
                        }
                    }
                ]
            }
        )
        template = Template.objects.get(id=response.data['id'])

        # act
        response = api_client.post(
            f'/templates/{template.id}/clone'
        )

        # assert
        assert response.status_code == 200
        task_data = response.data['tasks'][0]
        assert task_data['raw_due_date']['duration'] == duration
        analytics_mock.assert_called_once_with(
            user=user,
            template=template,
            task=template.tasks.get(number=1),
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )
