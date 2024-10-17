import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template
)
from pneumatic_backend.processes.models import (
    Template
)

from pneumatic_backend.processes.enums import PerformerType
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.messages import template as messages
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
            'id': kickoff.id,
            'description': 'changed desc',
        }

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'template_owners': [user.id],
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
                'template_owners': [user.id],
                'is_active': True,
                'finalizable': True,
                'kickoff': {
                    'description': 'Desc',
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
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        kickoff_update_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.'
            'AnalyticService.templates_kickoff_updated'
        )
        request_data = {
            'id': template.id,
            'is_active': True,
            'description': '',
            'name': 'Template',
            'template_owners': [user.id],
            'finalizable': True,
            'kickoff': {
                'description': 'Desc changed',
            },
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step changed',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data=request_data
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
                'template_owners': [user.id],
                'tasks': [
                    {
                        'number': task.number,
                        'name': task.name,
                    }
                ]
            }
        )
        template = Template.objects.get(id=response.data['id'])
        kickoff = template.kickoff_instance

        # assert
        assert response.status_code == 200
        assert response.data['kickoff'] == {
            'fields': [],
            'description': '',
            'id': kickoff.id
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
                'template_owners': [user.id],
                'tasks': [
                    {
                        'number': task.number,
                        'name': task.name,
                    }
                ]
            }
        )
        template = Template.objects.get(id=response.data['id'])
        kickoff = template.kickoff_instance

        # assert
        assert response.status_code == 200
        assert response.data['kickoff'] == {
            'fields': [],
            'description': '',
            'id': kickoff.id
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
        del(data['kickoff']['id'])
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
            'description': kickoff.description,
            'id': kickoff.id
        }
        kickoff_update_mock.assert_not_called()

    def test_update__send_invalid_kickoff_id__validation_error(
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
        data['kickoff']['id'] = -999
        data['is_active'] = True
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

        # assert
        assert response.status_code == 400
        assert response.data['message'] == messages.MSG_PT_0011
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['details']['reason'] == messages.MSG_PT_0011
        assert response.data['details']['name'] == 'kickoff'
        kickoff_update_mock.assert_not_called()

    def test_update__not_send_kickoff_id__validation_error(
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
        del(data['kickoff']['id'])
        data['is_active'] = True
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

        # assert
        assert response.status_code == 400
        assert response.data['message'] == messages.MSG_PT_0012
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['details']['reason'] == messages.MSG_PT_0012
        assert response.data['details']['name'] == 'kickoff'
        kickoff_update_mock.assert_not_called()
