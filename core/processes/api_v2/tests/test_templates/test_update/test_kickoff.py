import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template
)
from pneumatic_backend.processes.models import (
    Template
)

from pneumatic_backend.processes.enums import (
    PerformerType,
    OwnerType
)
from pneumatic_backend.authentication.enums import AuthTokenType

pytestmark = pytest.mark.django_db


class TestUpdateKickoff:

    def test_update__all_fields__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user,
            is_active=True,
            tasks_count=1
        )
        kickoff = template.kickoff_instance
        task = template.tasks.first()
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        kickoff_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_kickoff_updated'
        )
        request_data = {
            'description': 'changed desc',
        }

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id
                    },
                ],
                'kickoff': request_data,
                'tasks': [
                    {
                        'number': task.number,
                        'name': task.name,
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

        # assert
        assert response.status_code == 200

        response_data = response.json()['kickoff']
        assert response_data['description'] == request_data['description']

        kickoff.refresh_from_db()
        assert kickoff.description == request_data['description']
        kickoff_update_mock.assert_called_once_with(
            user=user,
            template=template,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )

    def test_update_draft__not_kickoff__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user,
            is_active=True,
            tasks_count=1
        )
        task = template.tasks.first()
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        kickoff_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_kickoff_updated'
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': False,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id
                    },
                ],
                'tasks': [
                    {
                        'number': task.number,
                        'name': task.name,
                    }
                ]
            }
        )

        # assert
        assert response.status_code == 200
        assert response.data['kickoff'] == {
            'fields': [],
            'description': ''
        }
        assert response.data['is_active'] is False
        kickoff_update_mock.assert_not_called()

    def test_update_draft__kickoff_id_null__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user,
            is_active=True,
            tasks_count=1
        )
        task = template.tasks.first()
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        kickoff_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_kickoff_updated'
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'kickoff': None,
                'is_active': False,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id
                    },
                ],
                'tasks': [
                    {
                        'number': task.number,
                        'name': task.name,
                    }
                ]
            }
        )

        # assert
        assert response.status_code == 200
        assert response.data['kickoff'] == {
            'fields': [],
            'description': ''
        }
        assert response.data['is_active'] is False
        kickoff_update_mock.assert_not_called()

    def test_update_draft__not_send_kickoff_id__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user,
            is_active=True,
            tasks_count=1
        )
        template.is_active = False
        template.save()

        response = api_client.get(f'/templates/{template.id}')
        data = response.data
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        kickoff_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_kickoff_updated'
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data=data
        )
        template = Template.objects.get(id=response.data['id'])
        kickoff = template.kickoff_instance

        # assert
        assert response.status_code == 200
        assert response.data['kickoff'] == {
            'fields': [],
            'description': kickoff.description
        }
        kickoff_update_mock.assert_not_called()
