import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template
)
from pneumatic_backend.processes.models import (
    FieldTemplate,
    FieldTemplateSelection,
    Workflow
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    FieldType
)


pytestmark = pytest.mark.django_db


class TestUpdateTaskFields:

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
            name='Name',
            type=FieldType.STRING,
            task=task,
            is_required=False,
            order=1,
            api_name='field-name-1',
            template=template,
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated'
        )

        request_data = {
            'name': 'Changed name',
            'description': 'Changed desc',
            'type': FieldType.TEXT,
            'is_required': True,
            'order': 2,
            'api_name': 'field-name-1'
        }

        # act
        response = api_client.put(
            f'/templates/{template.id}',
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
                        'fields': [request_data]
                    }
                ]
            }
        )
        task.refresh_from_db()
        template.refresh_from_db()

        # assert
        assert response.status_code == 200

        fields = task.fields.all()
        assert fields.count() == 1
        field = fields.first()
        assert field.type == request_data['type']
        assert field.name == request_data['name']
        assert field.description == request_data['description']
        assert field.is_required == request_data['is_required']
        assert field.order == request_data['order']
        assert field.api_name == request_data['api_name']

        data = response.json()
        assert len(data['tasks'][0]['fields']) == 1
        response_data = data['tasks'][0]['fields'][0]
        assert response_data['type'] == request_data['type']
        assert response_data['name'] == request_data['name']
        assert response_data['description'] == request_data['description']
        assert response_data['is_required'] == request_data['is_required']
        assert response_data['order'] == request_data['order']
        assert response_data['api_name'] == request_data['api_name']

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
            name='Name',
            type=FieldType.STRING,
            task=task,
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
                        'fields': []
                    }
                ]
            }
        )

        # assert
        assert response.status_code == 200
        data = response.json()
        task.refresh_from_db()
        assert task.fields.count() == 0
        assert len(data['tasks'][0]['fields']) == 0
        assert not FieldTemplate.objects.filter(id=field.id).exists()

    def test_update__ordering__ok(
        self,
        mocker,
        api_client
    ):

        """ Fields should be returned in descending ordering (2,1,0) """

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user,
            is_active=True,
            tasks_count=1
        )
        task = template.tasks.first()
        request_data_3 = {
            'order': 3,
            'type': FieldType.CHECKBOX,
            'name': 'Field 3',
            'description': 'description',
            'is_required': True,
            'selections': [
                {'value': 'First'},
                {'value': 'Second'}
            ],
        }
        request_data_1 = {
            'order': 1,
            'type': FieldType.RADIO,
            'name': 'Field 1',
            'description': 'description',
            'is_required': True,
            'selections': [
                {'value': 'First'},
                {'value': 'Second'}
            ]
        }
        request_data_5 = {
            'order': 5,
            'type': FieldType.DROPDOWN,
            'name': 'Field 5',
            'is_required': True,
            'selections': [
                {'value': 'First'},
                {'value': 'Second'}
            ],
        }
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
                            request_data_3,
                            request_data_5,
                            request_data_1,
                        ]
                    }
                ]
            }
        )

        # assert
        assert response.status_code == 200
        assert task.fields.count() == 3

        response_fields = response.data['tasks'][0]['fields']
        assert len(response_fields) == 3
        assert response_fields[0]['order'] == 5
        assert response_fields[1]['order'] == 3
        assert response_fields[2]['order'] == 1

    def test_update_task_fields_ordering__ok(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1
        )
        template_task = template.tasks.first()
        field_template_1 = FieldTemplate.objects.create(
            name='Field 1',
            order=1,
            type=FieldType.USER,
            is_required=True,
            task=template_task,
            template=template,
        )
        field_template_0 = FieldTemplate.objects.create(
            name='Field 0',
            order=0,
            type=FieldType.STRING,
            is_required=False,
            task=template_task,
            template=template,
        )
        field_template_2 = FieldTemplate.objects.create(
            name='Field 2',
            order=2,
            type=FieldType.DROPDOWN,
            is_required=False,
            task=template_task,
            template=template,
        )
        selection_template = FieldTemplateSelection.objects.create(
            field_template=field_template_2,
            template=template,
            value='value 3',
        )

        response = api_client.post(
            path=f'/templates/{template.id}/run',
            data={
                'name': 'Test name'
            }
        )
        workflow = Workflow.objects.get(id=response.data['workflow_id'])
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
                    'id': template.kickoff_instance.id
                },
                'tasks': [
                    {
                        'id': template_task.id,
                        'number': template_task.number,
                        'name': template_task.name,
                        'api_name': template_task.api_name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                        'fields': [
                            {
                                'id': field_template_1.id,
                                'name': field_template_1.name,
                                'description': field_template_1.description,
                                'type': field_template_1.type,
                                'is_required': field_template_1.is_required,
                                'order': 0,
                                'api_name': field_template_1.api_name
                            },
                            {
                                'id': field_template_2.id,
                                'name': field_template_2.name,
                                'description': field_template_2.description,
                                'type': field_template_2.type,
                                'is_required': field_template_2.is_required,
                                'order': 1,
                                'api_name': field_template_2.api_name,
                                'selections': [
                                    {
                                        'value': selection_template.value
                                    }
                                ]
                            },
                            {
                                'id': field_template_0.id,
                                'name': field_template_0.name,
                                'description': field_template_0.description,
                                'type': field_template_0.type,
                                'is_required': field_template_0.is_required,
                                'order': 2,
                                'api_name': field_template_0.api_name,
                            },
                        ]
                    }
                ]
            }
        )
        task = workflow.tasks.first()

        # assert
        assert response.status_code == 200
        fields = task.output.all()
        assert len(fields) == 3
        assert fields[0].order == 2
        assert fields[0].api_name == field_template_0.api_name
        assert fields[1].order == 1
        assert fields[1].api_name == field_template_2.api_name
        assert fields[2].order == 0
        assert fields[2].api_name == field_template_1.api_name

    def test_update__change_field_api_name__create_new(
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
            name='Name',
            type=FieldType.STRING,
            task=task,
            is_required=False,
            order=1,
            api_name='field-name-1',
            template=template,
            description=''
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
                                'api_name': new_api_name
                            }
                        ]
                    }
                ]
            }
        )

        # assert
        assert response.status_code == 200
        assert not FieldTemplate.objects.filter(id=field.id).exists()
        assert len(response.data['tasks'][0]['fields']) == 1
        field_data = response.data['tasks'][0]['fields'][0]
        assert field_data['api_name'] == new_api_name
        assert field_data['name'] == field.name
        assert field_data['description'] == field.description
        assert field_data['type'] == field.type
        assert field_data['is_required'] == field.is_required

    def test_update__unspecified_field_api_name__create_new(
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
            name='Name',
            type=FieldType.STRING,
            task=task,
            is_required=False,
            order=1,
            api_name='field-name-1',
            template=template,
            description=''
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
                            }
                        ]
                    }
                ]
            }
        )

        # assert
        assert response.status_code == 200
        assert not FieldTemplate.objects.filter(id=field.id).exists()
        assert len(response.data['tasks'][0]['fields']) == 1
        field_data = response.data['tasks'][0]['fields'][0]
        assert field_data['api_name']
        assert field_data['name'] == field.name
        assert field_data['description'] == field.description
        assert field_data['type'] == field.type
        assert field_data['is_required'] == field.is_required

    def test_update__fields_with_equal_api_names__save_last(
        self,
        mocker,
        api_client,
    ):

        # arrange
        step_name = 'Second step'
        field_api_name = 'user-field-1'
        field_name = 'Enter next task performer'

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
            name='Name',
            type=FieldType.STRING,
            task=task,
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
                    'id': kickoff.id
                },
                'tasks': [
                    {
                        'id': task.id,
                        'number': task.number,
                        'api_name': task.api_name,
                        'name': step_name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                        'fields': [
                            {
                                'api_name': field_api_name,
                                'name': field_name,
                                'type': FieldType.USER,
                                'order': 1,
                                'is_required': True,
                            },
                            {
                                'api_name': field_api_name,
                                'name': field.name,
                                'type': field.type,
                                'order': 2,
                                'is_required': field.is_required,
                            }
                        ]
                    }
                ]
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data['tasks'][0]['fields']) == 1
        field_data = response.data['tasks'][0]['fields'][0]
        assert field_data['api_name'] == field.api_name
        assert field_data['type'] == field.type
        assert field_data['order'] == 2
        assert field_data['is_required'] == field.is_required
