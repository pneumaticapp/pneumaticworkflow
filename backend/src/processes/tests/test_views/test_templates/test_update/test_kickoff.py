import pytest
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_template,
)
from src.processes.models.templates.template import Template
from src.processes.enums import (
    PerformerType,
    OwnerType,
)
from src.authentication.enums import AuthTokenType

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
            tasks_count=1,
        )
        task = template.tasks.first()
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        kickoff_update_mock = mocker.patch(
            'src.processes.views.template.'
            'AnalyticService.templates_kickoff_updated',
        )
        request_data = {}
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
                        'source_id': user.id,
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
                                'source_id': user.id,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        kickoff_update_mock.assert_called_once_with(
            user=user,
            template=template,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )

    def test_update__create_second_kickoff__validation_error(
        self,
        mocker,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'description': '',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': True,
                'finalizable': True,
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
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        kickoff_update_mock = mocker.patch(
            'src.processes.views.template.'
            'AnalyticService.templates_kickoff_updated',
        )
        request_data = {
            'id': template.id,
            'is_active': True,
            'description': '',
            'name': 'Template',
            'template_owners': [user.id],
            'finalizable': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step changed',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                },
            ],
        }

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data=request_data,
        )

        # assert
        assert response.status_code == 400
        kickoff_update_mock.assert_not_called()

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
            tasks_count=1,
        )
        task = template.tasks.first()
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        kickoff_update_mock = mocker.patch(
            'src.processes.views.template.'
            'AnalyticService.templates_kickoff_updated',
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
                        'source_id': user.id,
                    },
                ],
                'tasks': [
                    {
                        'number': task.number,
                        'name': task.name,
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        assert response.data['kickoff'] == {
            'fields': [],
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
            tasks_count=1,
        )
        task = template.tasks.first()
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        kickoff_update_mock = mocker.patch(
            'src.processes.views.template.'
            'AnalyticService.templates_kickoff_updated',
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
                        'source_id': user.id,
                    },
                ],
                'tasks': [
                    {
                        'number': task.number,
                        'name': task.name,
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        assert response.data['kickoff'] == {
            'fields': [],
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
            tasks_count=1,
        )
        template.is_active = False
        template.save()

        response = api_client.get(f'/templates/{template.id}')
        data = response.data
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        kickoff_update_mock = mocker.patch(
            'src.processes.views.template.'
            'AnalyticService.templates_kickoff_updated',
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data=data,
        )

        # assert
        assert response.status_code == 200
        assert response.data['kickoff'] == {
            'fields': [],
        }
        kickoff_update_mock.assert_not_called()
