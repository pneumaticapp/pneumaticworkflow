import pytest

from src.processes.enums import (
    FieldType,
    OwnerRole,
    OwnerType,
    PerformerType,
)
from src.processes.messages import template as messages
from src.processes.models.templates.fields import FieldTemplate
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_dataset,
    create_test_owner,
    create_test_user,
)

pytestmark = pytest.mark.django_db


class TestCreateTemplateTaskFields:

    def test_create__only_required_fields__defaults_ok(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        request_data = {
            'type': FieldType.TEXT,
            'name': 'Text field',
            'order': 1,
            'api_name': 'text-field-1',
        }

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                        'role': OwnerRole.OWNER,
                    },
                ],
                'is_active': True,
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'fields': [request_data],
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
        assert len(data['tasks'][0]['fields']) == 1

        response_data = data['tasks'][0]['fields'][0]
        assert response_data['type'] == request_data['type']
        assert response_data['name'] == request_data['name']
        assert response_data['order'] == request_data['order']
        assert response_data['api_name'] == request_data['api_name']
        assert response_data['description'] == ''
        assert response_data['is_required'] is False
        assert response_data['is_hidden'] is False
        assert response_data['default'] == ''
        assert 'selections' not in response_data

        field = FieldTemplate.objects.get(api_name=response_data['api_name'])
        assert field.type == request_data['type']
        assert field.name == request_data['name']
        assert field.order == request_data['order']
        assert field.api_name == request_data['api_name']
        assert field.description is None
        assert field.is_required is False
        assert field.is_hidden is False
        assert field.default == ''
        assert not field.selections.exists()

    def test_create__all_fields__ok(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        request_data = {
            'type': FieldType.TEXT,
            'name': 'Text field',
            'description': 'desc',
            'order': 1,
            'is_required': True,
            'is_hidden': False,
            'api_name': 'text-field-1',
            'default': 'default value',
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
                        'source_id': user.id,
                        'role': OwnerRole.OWNER,
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'fields': [request_data],
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
        assert len(data['tasks'][0]['fields']) == 1

        response_data = data['tasks'][0]['fields'][0]
        assert response_data['type'] == request_data['type']
        assert response_data['name'] == request_data['name']
        assert response_data['order'] == request_data['order']
        assert response_data['api_name'] == request_data['api_name']
        assert response_data['description'] == request_data['description']
        assert response_data['is_required'] == request_data['is_required']
        assert response_data['is_hidden'] == request_data['is_hidden']
        assert response_data['default'] == request_data['default']
        assert 'selections' not in response_data

        field = FieldTemplate.objects.get(api_name=response_data['api_name'])
        assert field.type == request_data['type']
        assert field.name == request_data['name']
        assert field.order == request_data['order']
        assert field.api_name == request_data['api_name']
        assert field.description == request_data['description']
        assert field.is_required == request_data['is_required']
        assert field.is_hidden == request_data['is_hidden']
        assert field.default == request_data['default']
        assert not field.selections.exists()

    def test_create__task_field_is_hidden__ok(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        request_data = {
            'type': FieldType.TEXT,
            'name': 'Hidden field',
            'order': 1,
            'is_required': False,
            'is_hidden': True,
            'api_name': 'hidden-field-1',
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
                        'source_id': user.id,
                        'role': OwnerRole.OWNER,
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'fields': [request_data],
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
        assert len(data['tasks'][0]['fields']) == 1

        response_data = data['tasks'][0]['fields'][0]
        assert response_data['is_hidden'] is True
        assert response_data['is_required'] is False

        field = FieldTemplate.objects.get(api_name=request_data['api_name'])
        assert field.is_hidden is True
        assert field.is_required is False

    def test_create__type_user__ok(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user=user)
        request_data = {
            'type': FieldType.USER,
            'order': 1,
            'name': 'Enter next task performer',
            'is_required': True,
            'api_name': 'user-field-1',
        }

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                        'role': OwnerRole.OWNER,
                    },
                ],
                'is_active': True,
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'fields': [request_data],
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
        response_data = response.data['tasks'][0]['fields'][0]
        assert response_data['type'] == request_data['type']
        assert response_data['name'] == request_data['name']
        assert response_data['is_required'] == request_data['is_required']
        assert response_data['api_name'] == request_data['api_name']

        field = FieldTemplate.objects.get(api_name=response_data['api_name'])
        assert field.type == request_data['type']
        assert field.name == request_data['name']
        assert field.is_required == request_data['is_required']
        assert field.api_name == request_data['api_name']

    def test_create__the_same_api_names_for_performer_field__do_not_duplicate(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user=user)
        request_data = {
            'type': FieldType.USER,
            'order': 1,
            'name': 'Enter next task performer',
            'is_required': True,
            'api_name': 'user-field-1',
        }

        api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                        'role': OwnerRole.OWNER,
                    },
                ],
                'is_active': True,
                'kickoff': {
                    'fields': [request_data],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'fields': [],
                        'raw_performers': [
                            {
                                'type': PerformerType.FIELD,
                                'source_id': 'user-field-1',
                            },
                        ],
                    },
                ],
            },
        )

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                        'role': OwnerRole.OWNER,
                    },
                ],
                'is_active': True,
                'kickoff': {
                    'fields': [request_data],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'fields': [],
                        'raw_performers': [
                            {
                                'type': PerformerType.FIELD,
                                'source_id': 'user-field-1',
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        assert len(response.data['tasks'][0]['raw_performers']) == 1

    def test_create__fields_with_equal_api_names__validation_error(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        step_name = 'Second step'
        field_api_name = 'user-field-1'
        field_name = 'Enter next task performer'
        request_data = {
            'type': FieldType.USER,
            'order': 1,
            'name': field_name,
            'is_required': True,
            'api_name': field_api_name,
        }

        # act
        response = api_client.post('/templates', data={
            'name': 'Template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'is_active': True,
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
                    'fields': [request_data],
                },
                {
                    'number': 2,
                    'name': step_name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [request_data],
                },
            ],
        })
        # assert
        assert response.status_code == 400
        message = messages.MSG_PT_0050(
            name=step_name,
            field_name=field_name,
            api_name=field_api_name,
        )
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['api_name'] == field_api_name

    def test_create__task_field_with_dataset__ok(
        self,
        api_client,
    ):

        """
        Creating a template with a task field that references a dataset
        saves the dataset FK and returns dataset id in the response.
        """

        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        dataset = create_test_dataset(account=account)
        api_client.token_authenticate(user)
        request_data = {
            'type': FieldType.TEXT,
            'name': 'Dataset field',
            'order': 1,
            'api_name': 'text-field-1',
            'dataset': dataset.id,
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
                        'source_id': user.id,
                        'role': OwnerRole.OWNER,
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'fields': [request_data],
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
        assert len(data['tasks'][0]['fields']) == 1

        response_data = data['tasks'][0]['fields'][0]
        assert response_data['dataset'] == dataset.id

        field = FieldTemplate.objects.get(
            api_name=response_data['api_name'],
        )
        assert field.dataset_id == dataset.id

    def test_create__task_field_dataset_null__ok(
        self,
        api_client,
    ):

        """
        Creating a template with a task field where dataset is explicitly
        null saves the field with dataset=None and returns null
        in the response.
        """

        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        api_client.token_authenticate(user)
        request_data = {
            'type': FieldType.TEXT,
            'name': 'Text field',
            'order': 1,
            'api_name': 'text-field-1',
            'dataset': None,
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
                        'source_id': user.id,
                        'role': OwnerRole.OWNER,
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'fields': [request_data],
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
        assert len(data['tasks'][0]['fields']) == 1

        response_data = data['tasks'][0]['fields'][0]
        assert response_data['dataset'] is None

        field = FieldTemplate.objects.get(
            api_name=response_data['api_name'],
        )
        assert field.dataset_id is None

    def test_create__task_field_dataset_other_account__validation_error(
        self,
        api_client,
    ):

        """
        Creating a template with a task field that references a dataset
        belonging to another account returns a 400 validation error.
        """

        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        other_account = create_test_account(name='Other Company')
        other_dataset = create_test_dataset(account=other_account)
        api_client.token_authenticate(user)
        request_data = {
            'type': FieldType.TEXT,
            'name': 'Text field',
            'order': 1,
            'api_name': 'text-field-1',
            'dataset': other_dataset.id,
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
                        'source_id': user.id,
                        'role': OwnerRole.OWNER,
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'fields': [request_data],
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
