import pytest

from src.processes.enums import (
    OwnerRole,
    FieldType,
    OwnerType,
    PerformerType,
)
from src.processes.models.templates.fields import FieldTemplate
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_dataset,
    create_test_owner,
    create_test_template,
    create_test_user,
)

pytestmark = pytest.mark.django_db


class TestUpdateKickoffFields:

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
            account=user.account,
        )

        request_data = {
            'name': 'Changed name',
            'description': 'Changed desc',
            'type': FieldType.TEXT,
            'is_required': True,
            'is_hidden': False,
            'order': 2,
            'api_name': 'field-name-1',
        }
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

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
                        'role': OwnerRole.OWNER,
                    },
                ],
                'kickoff': {
                    'fields': [request_data],
                },
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
        data = response.json()

        assert len(data['kickoff']['fields']) == 1
        response_data = data['kickoff']['fields'][0]
        assert response_data['type'] == request_data['type']
        assert response_data['name'] == request_data['name']
        assert response_data['description'] == request_data['description']
        assert response_data['is_required'] == request_data['is_required']
        assert response_data['is_hidden'] == request_data['is_hidden']
        assert response_data['order'] == request_data['order']
        assert response_data['api_name'] == request_data['api_name']

        kickoff.refresh_from_db()
        assert kickoff.fields.count() == 1
        field = kickoff.fields.first()
        assert field.type == request_data['type']
        assert field.name == request_data['name']
        assert field.description == request_data['description']
        assert field.is_required == request_data['is_required']
        assert field.is_hidden == request_data['is_hidden']
        assert field.order == request_data['order']
        assert field.api_name == request_data['api_name']

    def test_update__kickoff_field_is_hidden__ok(
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
            account=user.account,
        )
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        request_data = {
            'name': 'Hidden field',
            'description': '',
            'type': FieldType.STRING,
            'is_required': False,
            'is_hidden': True,
            'order': 1,
            'api_name': 'field-name-1',
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
                        'source_id': user.id,
                        'role': OwnerRole.OWNER,
                    },
                ],
                'kickoff': {
                    'fields': [request_data],
                },
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
        data = response.json()
        assert len(data['kickoff']['fields']) == 1
        response_data = data['kickoff']['fields'][0]
        assert response_data['is_hidden'] is True

        kickoff.refresh_from_db()
        field = kickoff.fields.first()
        assert field.is_hidden is True

    def test_update__delete__ok(
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
            account=user.account,
        )
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )

        # act
        response = api_client.put(
            f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                        'role': OwnerRole.OWNER,
                    },
                ],
                'kickoff': {
                    'fields': [],
                },
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
            tasks_count=1,
        )
        task = template.tasks.first()
        field = FieldTemplate.objects.create(
            name='Name',
            type=FieldType.STRING,
            kickoff=template.kickoff_instance,
            is_required=False,
            order=1,
            api_name=field_api_name,
            template=template,
            account=user.account,
        )
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        api_client.token_authenticate(user)

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
                        'role': OwnerRole.OWNER,
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'name': 'New name',
                            'description': field.description,
                            'type': FieldType.STRING,
                            'is_required': True,
                            'order': 1,
                            'api_name': field_api_name,
                        },
                        {
                            'name': field_name,
                            'type': FieldType.TEXT,
                            'order': 2,
                            'api_name': field_api_name,
                        },
                    ],
                },
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
        assert len(response.data['kickoff']['fields']) == 1
        field_data = response.data['kickoff']['fields'][0]
        assert field_data['api_name'] == field.api_name
        assert field_data['type'] == FieldType.TEXT
        assert field_data['order'] == 2

    def test_update__kickoff_field_set_dataset__ok(
        self,
        mocker,
        api_client,
    ):

        """
        Updating a template to add a dataset to an existing kickoff field
        saves the dataset FK and returns dataset id in the response.
        """

        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        dataset = create_test_dataset(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1,
        )
        task = template.tasks.first()
        FieldTemplate.objects.create(
            name='Text field',
            type=FieldType.TEXT,
            kickoff=template.kickoff_instance,
            is_required=False,
            order=1,
            api_name='text-field-1',
            template=template,
            account=account,
        )
        template_updated_mock = mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        api_client.token_authenticate(user)
        request_data = {
            'name': 'Text field',
            'type': FieldType.TEXT,
            'is_required': False,
            'is_hidden': False,
            'order': 1,
            'api_name': 'text-field-1',
            'dataset': dataset.id,
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
                        'source_id': user.id,
                        'role': OwnerRole.OWNER,
                    },
                ],
                'kickoff': {
                    'fields': [request_data],
                },
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
        data = response.json()
        assert len(data['kickoff']['fields']) == 1

        response_data = data['kickoff']['fields'][0]
        assert response_data['dataset'] == dataset.id

        field = FieldTemplate.objects.get(
            api_name=request_data['api_name'],
        )
        assert field.dataset_id == dataset.id

        template_updated_mock.assert_called_once_with(
            template=template,
        )

    def test_update__kickoff_field_clear_dataset__ok(
        self,
        mocker,
        api_client,
    ):

        """
        Updating a template to set dataset=null on a kickoff field that
        previously had a dataset clears the FK and returns null
        in the response.
        """

        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        dataset = create_test_dataset(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1,
        )
        task = template.tasks.first()
        FieldTemplate.objects.create(
            name='Text field',
            type=FieldType.TEXT,
            kickoff=template.kickoff_instance,
            is_required=False,
            order=1,
            api_name='text-field-1',
            template=template,
            account=account,
            dataset=dataset,
        )
        template_updated_mock = mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        api_client.token_authenticate(user)
        request_data = {
            'name': 'Text field',
            'type': FieldType.TEXT,
            'is_required': False,
            'is_hidden': False,
            'order': 1,
            'api_name': 'text-field-1',
            'dataset': None,
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
                        'source_id': user.id,
                        'role': OwnerRole.OWNER,
                    },
                ],
                'kickoff': {
                    'fields': [request_data],
                },
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
        data = response.json()
        assert len(data['kickoff']['fields']) == 1

        response_data = data['kickoff']['fields'][0]
        assert response_data['dataset'] is None

        field = FieldTemplate.objects.get(
            api_name=request_data['api_name'],
        )
        assert field.dataset_id is None

        template_updated_mock.assert_called_once_with(
            template=template,
        )

    def test_update__kickoff_field_dataset_other_account__validation_error(
        self,
        mocker,
        api_client,
    ):

        """
        Updating a template with a kickoff field referencing a dataset from
        another account returns a 400 validation error.
        """

        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        other_account = create_test_account(name='Other Company')
        other_dataset = create_test_dataset(account=other_account)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1,
        )
        task = template.tasks.first()
        FieldTemplate.objects.create(
            name='Text field',
            type=FieldType.TEXT,
            kickoff=template.kickoff_instance,
            is_required=False,
            order=1,
            api_name='text-field-1',
            template=template,
            account=account,
        )
        template_updated_mock = mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        api_client.token_authenticate(user)
        request_data = {
            'name': 'Text field',
            'type': FieldType.TEXT,
            'is_required': False,
            'order': 1,
            'api_name': 'text-field-1',
            'dataset': other_dataset.id,
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
                        'source_id': user.id,
                        'role': OwnerRole.OWNER,
                    },
                ],
                'kickoff': {
                    'fields': [request_data],
                },
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
        assert response.status_code == 400
        template_updated_mock.assert_not_called()
