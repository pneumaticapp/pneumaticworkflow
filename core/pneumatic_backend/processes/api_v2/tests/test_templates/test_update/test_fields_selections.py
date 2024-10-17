import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template
)
from pneumatic_backend.processes.models import (
    FieldTemplate,
    FieldTemplateSelection,
)
from pneumatic_backend.processes.messages import template as messages
from pneumatic_backend.processes.enums import (
    PerformerType,
    FieldType
)

pytestmark = pytest.mark.django_db


class TestUpdateFieldSelections:

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
        task = template.tasks.first()
        field = FieldTemplate.objects.create(
            type=FieldType.RADIO,
            name='Text field',
            order=1,
            task=task,
            api_name='radio-field-1',
            template=template,
        )
        selection = FieldTemplateSelection.objects.create(
            value='First selection',
            field_template=field,
            template=template,
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        request_data = {
            'value': 'Changed first selection',
            'api_name': selection.api_name
        }

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'kickoff': {
                    'id': template.kickoff_instance.id
                },
                'template_owners': [user.id],
                'tasks': [
                    {
                        'id': task.id,
                        'number': task.number,
                        'name': task.name,
                        'api_name': task.api_name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                        'fields': [
                            {
                                'name': field.name,
                                'api_name': field.api_name,
                                'type': field.type,
                                'order': field.order,
                                'selections': [request_data]
                            }
                        ]
                    }
                ]
            }
        )
        # assert
        assert response.status_code == 200
        data = response.json()

        field_data = data['tasks'][0]['fields'][0]
        assert 'selections' in field_data
        assert len(field_data['selections']) == 1

        response_data = field_data['selections'][0]
        assert response_data['api_name'] == request_data['api_name']
        assert response_data['value'] == request_data['value']

        assert FieldTemplateSelection.objects.get(
            api_name=request_data['api_name'],
            value=request_data['value']
        )

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
        task = template.tasks.first()
        field = FieldTemplate.objects.create(
            type=FieldType.RADIO,
            name='Text field',
            order=1,
            task=task,
            api_name='radio-field-1',
            template=template,
        )
        selection = FieldTemplateSelection.objects.create(
            value='First selection',
            field_template=field,
            template=template,
        )
        selection2 = FieldTemplateSelection.objects.create(
            value='Second selection',
            field_template=field,
            template=template,
        )
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
                    'id': template.kickoff_instance.id
                },
                'tasks': [
                    {
                        'id': task.id,
                        'number': task.number,
                        'name': task.name,
                        'api_name': task.api_name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                        'fields': [
                            {
                                'name': field.name,
                                'type': field.type,
                                'api_name': field.api_name,
                                'order': field.order,
                                'selections': [
                                    {
                                        'value': selection.value,
                                        'api_name': selection.api_name
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        )

        # assert
        assert response.status_code == 200
        data = response.json()
        field.refresh_from_db()
        assert field.selections.count() == 1
        assert len(data['tasks'][0]['fields'][0]['selections']) == 1
        assert not FieldTemplateSelection.objects.filter(
            api_name=selection2.api_name
        ).exists()

    def test_update__change_selection_api_name__create_new(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=1,
            is_active=True
        )
        kickoff = template.kickoff_instance
        task = template.tasks.first()
        field = FieldTemplate.objects.create(
            type=FieldType.RADIO,
            name='Text field',
            order=1,
            task=task,
            api_name='radio-field-1',
            template=template,
        )
        selection = FieldTemplateSelection.objects.create(
            value='First selection',
            field_template=field,
            template=template,
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )
        new_api_name = 'new-api-name'

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'template_owners': [user.id],
                'kickoff': {
                    'id': kickoff.id
                },
                'tasks': [
                    {
                        'id': task.id,
                        'number': task.number,
                        'api_name': task.api_name,
                        'name': task.name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                        'fields': [
                            {
                                'name': field.name,
                                'description': field.description,
                                'type': field.type,
                                'is_required': field.is_required,
                                'order': field.order,
                                'api_name': field.api_name,
                                'selections': [
                                    {
                                        'value': selection.value,
                                        'api_name': new_api_name,
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        )

        # assert
        assert response.status_code == 200
        assert not (
            FieldTemplateSelection.objects.filter(id=selection.id).exists()
        )
        field_data = response.data['tasks'][0]['fields'][0]
        assert len(field_data['selections']) == 1
        selection_data = field_data['selections'][0]
        assert selection_data['api_name'] == new_api_name
        assert selection_data['value'] == selection.value

    def test_update__unspecified_selection_api_name__create_new(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=1,
            is_active=True
        )
        kickoff = template.kickoff_instance
        task = template.tasks.first()
        field = FieldTemplate.objects.create(
            type=FieldType.RADIO,
            name='Text field',
            order=1,
            task=task,
            api_name='radio-field-1',
            template=template,
        )
        selection = FieldTemplateSelection.objects.create(
            value='First selection',
            field_template=field,
            template=template,
        )
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
                    'id': kickoff.id
                },
                'tasks': [
                    {
                        'id': task.id,
                        'number': task.number,
                        'api_name': task.api_name,
                        'name': task.name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                        'fields': [
                            {
                                'name': field.name,
                                'description': field.description,
                                'type': field.type,
                                'is_required': field.is_required,
                                'order': field.order,
                                'api_name': field.api_name,
                                'selections': [
                                    {
                                        'value': selection.value,
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        )

        # assert
        assert response.status_code == 200
        assert not (
            FieldTemplateSelection.objects.filter(id=selection.id).exists()
        )
        field_data = response.data['tasks'][0]['fields'][0]
        assert len(field_data['selections']) == 1
        selection_data = field_data['selections'][0]
        assert selection_data['api_name']
        assert selection_data['value'] == selection.value

    def test_update__selection_with_equal_api_names__validation_error(
        self,
        mocker,
        api_client
    ):

        # arrange
        step_name = 'Second step'
        selection_api_name = 'selection-1'
        selection_value = 'Some text'
        field_name = 'Broken field'
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user,
            is_active=True,
            tasks_count=1
        )
        task = template.tasks.first()
        field = FieldTemplate.objects.create(
            type=FieldType.RADIO,
            name='Text field',
            order=1,
            task=task,
            api_name='radio-field-1',
            template=template,
        )
        selection = FieldTemplateSelection.objects.create(
            value='First selection',
            field_template=field,
            template=template,
            api_name=selection_api_name,
        )
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
                'kickoff': {
                    'id': template.kickoff_instance.id
                },
                'template_owners': [user.id],
                'tasks': [
                    {
                        'id': task.id,
                        'number': task.number,
                        'name': step_name,
                        'api_name': task.api_name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                        'fields': [
                            {
                                'id': field.id,
                                'name': field.name,
                                'api_name': field.api_name,
                                'type': field.type,
                                'order': field.order,
                                'selections': [
                                    {
                                        'id': selection.id,
                                        'value': 'Changed first selection',
                                        'api_name': selection_api_name
                                    }
                                ]
                            },
                            {
                                'name': field_name,
                                'type': FieldType.TEXT,
                                'order': 2,
                                'selections': [
                                    {
                                        'value': selection_value,
                                        'api_name': selection_api_name
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        )

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
