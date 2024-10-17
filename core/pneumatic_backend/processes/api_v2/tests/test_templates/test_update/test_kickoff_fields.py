import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template
)
from pneumatic_backend.processes.models import (
    FieldTemplate
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    FieldType
)


pytestmark = pytest.mark.django_db


class TestUpdateKickoffFields:

    def test_update__all_fields__ok(
        self,
        mocker,
        api_client
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
        FieldTemplate.objects.create(
            name='Name',
            type=FieldType.STRING,
            kickoff=template.kickoff_instance,
            is_required=False,
            order=1,
            api_name='field-name-1',
            template=template,
        )

        request_data = {
            'name': 'Changed name',
            'description': 'Changed desc',
            'type': FieldType.TEXT,
            'is_required': True,
            'order': 2,
            'api_name': 'field-name-1'
        }
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'template_owners': [user.id],
                'kickoff': {
                    'id': kickoff.id,
                    'fields': [request_data]
                },
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
        data = response.json()

        assert len(data['kickoff']['fields']) == 1
        response_data = data['kickoff']['fields'][0]
        assert response_data['type'] == request_data['type']
        assert response_data['name'] == request_data['name']
        assert response_data['description'] == request_data['description']
        assert response_data['is_required'] == request_data['is_required']
        assert response_data['order'] == request_data['order']
        assert response_data['api_name'] == request_data['api_name']

        kickoff.refresh_from_db()
        assert kickoff.fields.count() == 1
        field = kickoff.fields.first()
        assert field.type == request_data['type']
        assert field.name == request_data['name']
        assert field.description == request_data['description']
        assert field.is_required == request_data['is_required']
        assert field.order == request_data['order']
        assert field.api_name == request_data['api_name']

    def test_update__delete__ok(
        self,
        mocker,
        api_client
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
        field = FieldTemplate.objects.create(
            name='Name',
            type=FieldType.STRING,
            kickoff=template.kickoff_instance,
            is_required=False,
            order=1,
            api_name='field-name-1',
            template=template,
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )

        # act
        response = api_client.put(
            f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'template_owners': [user.id],
                'kickoff': {
                    'id': kickoff.id,
                    'fields': []
                },
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
        data = response.json()
        kickoff.refresh_from_db()
        assert kickoff.fields.count() == 0
        assert len(data['kickoff']['fields']) == 0
        assert not FieldTemplate.objects.filter(id=field.id).exists()

    def test_update__fields_with_equal_api_names__save_last(
        self,
        mocker,
        api_client,
    ):

        # arrange
        field_api_name = 'user-field-1'
        field_name = 'Enter next task performer'
        user = create_test_user()
        template = create_test_template(
            user,
            is_active=True,
            tasks_count=1
        )
        kickoff = template.kickoff_instance
        task = template.tasks.first()
        field = FieldTemplate.objects.create(
            name='Name',
            type=FieldType.STRING,
            kickoff=template.kickoff_instance,
            is_required=False,
            order=1,
            api_name=field_api_name,
            template=template,
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'template_owners': [user.id],
                'kickoff': {
                    'id': kickoff.id,
                    'fields': [
                        {
                            'name': 'New name',
                            'description': field.description,
                            'type': FieldType.STRING,
                            'is_required': True,
                            'order': 1,
                            'api_name': field_api_name
                        },
                        {
                            'name': field_name,
                            'type': FieldType.TEXT,
                            'order': 2,
                            'api_name': field_api_name
                        }
                    ]
                },
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
        assert len(response.data['kickoff']['fields']) == 1
        field_data = response.data['kickoff']['fields'][0]
        assert field_data['api_name'] == field.api_name
        assert field_data['type'] == FieldType.TEXT
        assert field_data['order'] == 2
