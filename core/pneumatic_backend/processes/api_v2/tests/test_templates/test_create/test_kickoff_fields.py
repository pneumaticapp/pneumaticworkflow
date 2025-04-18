import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user
)
from pneumatic_backend.processes.models import (
    FieldTemplate
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    FieldType,
    OwnerType
)


pytestmark = pytest.mark.django_db


class TestCreateKickoffFields:

    def test_create__only_required_fields__defaults_ok(
        self,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        request_data = {
            'type': FieldType.TEXT,
            'name': 'Text field',
            'order': 1,
            'api_name': 'text-field-1'
        }

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id
                    },
                ],
                'is_active': True,
                'kickoff': {
                    'fields': [request_data]
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
        # assert
        assert response.status_code == 200
        data = response.json()
        assert len(data['kickoff']['fields']) == 1

        response_data = data['kickoff']['fields'][0]
        assert response_data['type'] == request_data['type']
        assert response_data['name'] == request_data['name']
        assert response_data['order'] == request_data['order']
        assert response_data['api_name'] == request_data['api_name']
        assert response_data['description'] == ''
        assert response_data['is_required'] is False
        assert response_data['default'] == ''
        assert 'selections' not in response_data

        field = FieldTemplate.objects.get(api_name=response_data['api_name'])
        assert field.type == request_data['type']
        assert field.name == request_data['name']
        assert field.order == request_data['order']
        assert field.api_name == request_data['api_name']
        assert field.description is None
        assert field.is_required is False
        assert field.default == ''
        assert not field.selections.exists()

    def test_create__all_fields__ok(
        self,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        request_data = {
            'type': FieldType.TEXT,
            'name': 'Text field',
            'description': 'desc',
            'order': 1,
            'is_required': True,
            'api_name': 'text-field-1',
            'default': 'default value'
        }

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id
                    },
                ],
                'kickoff': {
                    'fields': [request_data]
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
        # assert
        assert response.status_code == 200
        data = response.json()
        assert len(data['kickoff']['fields']) == 1

        response_data = data['kickoff']['fields'][0]
        assert response_data['type'] == request_data['type']
        assert response_data['name'] == request_data['name']
        assert response_data['order'] == request_data['order']
        assert response_data['api_name'] == request_data['api_name']
        assert response_data['description'] == request_data['description']
        assert response_data['is_required'] == request_data['is_required']
        assert response_data['default'] == request_data['default']
        assert 'selections' not in response_data

        field = FieldTemplate.objects.get(api_name=response_data['api_name'])
        assert field.type == request_data['type']
        assert field.name == request_data['name']
        assert field.order == request_data['order']
        assert field.api_name == request_data['api_name']
        assert field.description == request_data['description']
        assert field.is_required == request_data['is_required']
        assert field.default == request_data['default']
        assert not field.selections.exists()

    def test_create__fields_with_equal_api_names__save_last(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        field_api_name = 'user-field-1'
        field_name = 'Enter next task performer'
        request_data = {
            'type': FieldType.USER,
            'order': 1,
            'name': field_name,
            'is_required': True,
            'api_name': field_api_name
        }

        # act
        response = api_client.post('/templates', data={
            'name': 'Template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id
                },
            ],
            'is_active': True,
            'kickoff': {
                'fields': [
                    request_data,
                    request_data,
                ]
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
                    ],
                },
            ]
        })
        # assert
        assert response.status_code == 200
        assert len(response.data['kickoff']['fields']) == 1
        data = response.data['kickoff']['fields'][0]
        assert data['api_name'] == request_data['api_name']
