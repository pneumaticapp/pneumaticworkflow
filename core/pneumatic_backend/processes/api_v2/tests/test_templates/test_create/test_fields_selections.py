import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user
)
from pneumatic_backend.processes.models import (
    FieldTemplateSelection,
    Kickoff
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    FieldType
)
from pneumatic_backend.processes.messages import template as messages


pytestmark = pytest.mark.django_db


class TestCreateFieldSelections:

    def test_create__all_fields__ok(
        self,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        request_data = {
            'value': 'First selection'
        }

        # act
        response = api_client.post('/templates', data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
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
                            'type': FieldType.RADIO,
                            'name': 'Radio field',
                            'order': 1,
                            'api_name': 'radio-field-1',
                            'selections': [request_data]
                        }
                    ]
                }
            ]
        })
        # assert
        assert response.status_code == 200
        data = response.json()

        field_data = data['tasks'][0]['fields'][0]
        assert 'selections' in field_data
        assert len(field_data['selections']) == 1

        response_data = field_data['selections'][0]
        selection = FieldTemplateSelection.objects.get(
            api_name=response_data['api_name'],
            value=request_data['value']
        )
        assert response_data['id'] == selection.id
        assert response_data['api_name'] == selection.api_name
        assert response_data['value'] == selection.value

    def test_create__types_with_selections__ok(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        request_data = [
            {
                'type': FieldType.CHECKBOX,
                'name': 'first kickoff name',
                'order': 1,
                'description': 'Some kickoff description',
                'is_required': True,
                'selections': [
                    {'value': 'First'},
                    {'value': 'Second'}
                ]
            },
            {
                'type': FieldType.RADIO,
                'name': 'second kickoff name',
                'order': 2,
                'description': 'Some kickoff description',
                'is_required': True,
                'selections': [
                    {'value': 'First'},
                    {'value': 'Second'}
                ]
            },
            {
                'type': FieldType.DROPDOWN,
                'name': 'third kickoff name',
                'order': 3,
                'description': 'Some dropdown description',
                'is_required': True,
                'selections': [
                    {'value': 'First'},
                    {'value': 'Second'}
                ]
            }
        ]

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'template_owners': [user.id],
                'is_active': True,
                'kickoff': {
                    'fields': request_data
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
        response_data = response.json()['kickoff']['fields']
        assert len(response_data) == len(request_data)

        for response_field in response_data:
            assert len(response_field['selections']) == 2

        kickoff = Kickoff.objects.get(id=response.data['kickoff']['id'])
        kickoff_fields = kickoff.fields.all()
        assert kickoff_fields.count() == len(request_data)
        for field in kickoff_fields:
            assert field.selections.count() == 2

    def test_create__selection_with_equal_api_names__validation_error(
        self,
        api_client,
    ):

        # arrange
        step_name = 'Second step'
        selection_api_name = 'selection-1'
        field_name = 'Enter next task performer'
        selection_value = 'Yes'
        user = create_test_user()
        api_client.token_authenticate(user)
        request_data = {
            'value': selection_value,
            'api_name': selection_api_name,
        }

        # act
        response = api_client.post('/templates', data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
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
                            'type': FieldType.RADIO,
                            'name': 'Radio field',
                            'order': 1,
                            'api_name': 'radio-field-1',
                            'selections': [request_data]
                        }
                    ]
                },
                {
                    'number': 2,
                    'name': step_name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ],
                    'fields': [
                        {
                            'type': FieldType.RADIO,
                            'name': field_name,
                            'order': 1,
                            'api_name': 'radio-field-2',
                            'selections': [request_data]
                        }
                    ]
                }
            ]
        })

        # assert
        assert response.status_code == 400
        message = messages.MSG_PT_0054(
            step_name=f'Step "{step_name}"',
            name=field_name,
            value=selection_value,
            api_name=selection_api_name
        )
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['api_name'] == selection_api_name
