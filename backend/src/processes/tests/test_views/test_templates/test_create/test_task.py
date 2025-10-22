# ruff: noqa: UP031
from datetime import timedelta

import pytest

from src.accounts.models import (
    UserInvite,
)
from src.accounts.services.user import UserService
from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    ConditionAction,
    DueDateRule,
    FieldType,
    OwnerType,
    PerformerType,
    PredicateOperator,
    PredicateType,
    TaskStatus,
)
from src.processes.messages import template as messages
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.templates.raw_due_date import RawDueDateTemplate
from src.processes.models.templates.task import TaskTemplate
from src.processes.models.templates.template import Template
from src.processes.models.workflows.workflow import Workflow
from src.processes.services.workflow_action import (
    WorkflowActionService,
)
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_template,
    create_test_user,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


class TestCreateTemplateTask:

    def test_create__only_required_fields__defaults_ok(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        request_data = {
            'number': 1,
            'name': 'First step',
            'raw_performers': [
                {
                    'type': PerformerType.USER,
                    'source_id': user.id,
                },
            ],
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
                    },
                ],
                'kickoff': {},
                'is_active': True,
                'tasks': [request_data],
            },
        )

        # assert
        assert response.status_code == 200
        data = response.json()
        assert len(data['tasks']) == 1

        response_data = data['tasks'][0]
        assert response_data.get('api_name')
        assert response_data['name'] == request_data['name']
        assert response_data['number'] == request_data['number']
        assert response_data['revert_task'] is None
        assert response_data['description'] == ''
        assert len(response_data['raw_performers']) == (
            len(request_data['raw_performers'])
        )
        assert response_data['require_completion_by_all'] is False
        assert response_data['delay'] is None
        assert response_data['fields'] == []
        assert response_data['parents'] == []
        assert response_data['ancestors'] == []

        task = TaskTemplate.objects.get(api_name=response_data['api_name'])
        assert task.name == request_data['name']
        assert task.number == request_data['number']
        assert task.revert_task is None
        assert task.description is None
        assert task.raw_performers.count() == len(
            request_data['raw_performers'],
        )
        assert task.require_completion_by_all is False
        assert task.delay is None
        assert task.fields.count() == 0
        assert task.account_id == user.account_id

    def test_create__all_fields__ok(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        duration = '10 00:00:00'
        request_data = {
            'number': 1,
            'name': 'First step',
            'api_name': 'task-1',
            'description': 'Desc',
            'require_completion_by_all': True,
            'delay': None,
            'raw_due_date': {
                'api_name': 'raw-due-date-bwybf0',
                'rule': 'after task started',
                'duration_months': 0,
                'duration': duration,
                'source_id': 'task-1',
            },
            'raw_performers': [
                {
                    'type': PerformerType.USER,
                    'source_id': user.id,
                },
                {
                    'type': PerformerType.FIELD,
                    'source_id': 'user-field-1',
                },
            ],
            'fields': [],
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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'is_required': True,
                            'api_name': 'user-field-1',
                        },
                    ],
                },
                'tasks': [request_data],
            },
        )

        # assert
        assert response.status_code == 200
        data = response.json()
        assert len(data['tasks']) == 1

        response_data = data['tasks'][0]
        assert response_data.get('api_name')
        assert response_data['name'] == request_data['name']
        assert response_data['number'] == request_data['number']
        assert response_data['description'] == request_data['description']
        assert len(response_data['raw_performers']) == len(
            request_data['raw_performers'],
        )
        assert response_data['delay'] is None
        assert response_data['raw_due_date']['duration'] == duration
        assert response_data['api_name']
        assert response_data['fields'] == request_data['fields']
        assert response_data['require_completion_by_all'] == (
            request_data['require_completion_by_all']
        )

        task = TaskTemplate.objects.get(api_name=response_data['api_name'])
        assert task.name == request_data['name']
        assert task.number == request_data['number']
        assert task.description == request_data['description']
        assert task.raw_performers.count() == len(
            request_data['raw_performers'],
        )
        assert task.delay is None
        assert task.fields.count() == len(request_data['fields'])
        assert task.require_completion_by_all == (
            request_data['require_completion_by_all']
        )

    def test_create__tasks_not_provided__validation_error(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

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
                    },
                ],
                'kickoff': {},
                'tasks': [],
            },
        )

        # assert
        assert response.status_code == 400
        assert response.data['message'] == messages.MSG_PT_0013
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert not response.data.get('details')

    def test_create__long_task_name__validation_error(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        task_api_name = 'task-1'
        api_client.token_authenticate(user)

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
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'name': 'First' * 300,
                        'number': 1,
                        'api_name': task_api_name,
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
        message = 'Name: ensure this field has no more than 280 characters.'
        assert response.status_code == 400
        assert response.data['message'] == message
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['details']['api_name'] == task_api_name
        assert response.data['details']['reason'] == message
        assert 'name' not in response.data['details']

    def test_create__insert_valid_api_names_to_description__ok(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        kickoff_field_data = {
            'order': 1,
            'name': 'First step performer',
            'type': FieldType.USER,
            'is_required': True,
            'api_name': 'user-field-1',
        }
        task_field_data = {
            'order': 1,
            'name': 'Attached URL',
            'type': FieldType.URL,
            'is_required': False,
            'api_name': 'url-field-1',
        }
        request_data = {
            'is_active': True,
            'name': 'Template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                },
            ],
            'description': 'Test description',
            'kickoff': {
                'description': 'Desc',
                'fields': [kickoff_field_data],
            },
            'tasks': [
                {
                    'name': 'First',
                    'number': 1,
                    'description': '{{%s}}' % kickoff_field_data['api_name'],
                    'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                            },
                        ],
                    'fields': [task_field_data],
                },
                {
                    'name': 'Second',
                    'number': 2,
                    'description': '{{%s}}' % task_field_data['api_name'],
                    'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                            },
                        ],
                },
                {
                    'name': 'Third',
                    'number': 3,
                    'description': '{{%s}} {{%s}}' % (
                        kickoff_field_data['api_name'],
                        task_field_data['api_name'],
                    ),
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
        response = api_client.post(
            path='/templates',
            data=request_data,
        )

        # assert
        assert response.status_code == 200

    def test_create__another_template_api_name_in_desc__validation_error(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        task_api_name = 'task-1'
        task_name = 'Task'
        api_client.token_authenticate(user)
        another_template = create_test_template(
            user=user,
            tasks_count=1,
            is_active=True,
        )
        field_api_name = 'field-1'
        FieldTemplate.objects.create(
            order=1,
            name='Text',
            type=FieldType.TEXT,
            api_name=field_api_name,
            kickoff=another_template.kickoff_instance,
            template=another_template,
        )

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
                    },
                ],
                'description': '',
                'kickoff': {},
                'tasks': [
                    {
                        'name': task_name,
                        'number': 1,
                        'api_name': task_api_name,
                        'description': '{{%s}}' % field_api_name,
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
        message = messages.MSG_PT_0037(1)
        assert response.status_code == 400
        assert response.data['message'] == message
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['details']['api_name'] == task_api_name
        assert response.data['details']['reason'] == message
        assert 'name' not in response.data['details']

    def test_create__insert_valid_api_name_to_task_name__ok(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'String field',
                            'type': FieldType.STRING,
                            'is_required': True,
                            'api_name': 'string-field-1',
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': '{{string-field-1}}',
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

    def test_create__multiple_api_name_in_task_name__ok(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        task_api_name = 'task-1'
        task_name = 'Text {{string-field-1}} - {{string-field-2}}'
        api_client.token_authenticate(user)

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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'String field',
                            'type': FieldType.STRING,
                            'is_required': True,
                            'api_name': 'string-field-1',
                        },
                        {
                            'order': 2,
                            'name': 'String field 2',
                            'type': FieldType.STRING,
                            'is_required': True,
                            'api_name': 'string-field-2',
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': task_name,
                        'api_name': task_api_name,
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

    @pytest.mark.parametrize(
        'field_type',
        {
            FieldType.USER,
            FieldType.STRING,
            FieldType.DATE,
            FieldType.FILE,
            FieldType.URL,
            FieldType.TEXT,
        },
    )
    def test_create__simple_field_in_task_name__ok(
        self,
        field_type,
        api_client,
    ):

        # arrange
        user = create_test_user()
        field_api_name = 'field-1'
        task_api_name = 'task-1'
        task_name = '[{{%s}}] Task name' % field_api_name
        api_client.token_authenticate(user)

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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'Field',
                            'type': field_type,
                            'api_name': field_api_name,
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': task_name,
                        'api_name': task_api_name,
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

    @pytest.mark.parametrize(
        'field_type',
        {
            FieldType.DROPDOWN,
            FieldType.RADIO,
            FieldType.CHECKBOX,
        },
    )
    def test_create__field_with_selections_in_task_name__ok(
        self,
        field_type,
        api_client,
    ):

        # arrange
        user = create_test_user()
        field_api_name = 'field-1'
        task_api_name = 'task-1'
        task_name = '[{{%s}}] Task name' % field_api_name
        api_client.token_authenticate(user)

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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'Field',
                            'type': field_type,
                            'api_name': field_api_name,
                            'is_required': True,
                            'selections': [
                                {
                                    'api_name': 'selection-1',
                                    'value': 'some value',
                                },
                            ],
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': task_name,
                        'api_name': task_api_name,
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

    def test_create__not_existent_field_in_task_name__validation_error(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        task_api_name = 'task-1'
        task_name = '{{string-field-1}} title'
        api_client.token_authenticate(user)

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
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': task_name,
                        'api_name': task_api_name,
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
        message = messages.MSG_PT_0038(task_name)
        assert response.status_code == 400
        assert response.data['message'] == message
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['details']['api_name'] == task_api_name
        assert response.data['details']['reason'] == message
        assert 'name' not in response.data['details']

    def test_create__another_template_field_in_task_name__validation_error(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        field_api_name = 'field-1'
        task_api_name = 'task-1'
        task_name = 'Task'
        task_desc = '{{%s}} task name' % field_api_name

        api_client.token_authenticate(user)
        another_template = create_test_template(user)
        FieldTemplate.objects.create(
            order=1,
            name='Text field',
            type=FieldType.STRING,
            is_required=True,
            api_name=field_api_name,
            template=another_template,
        )

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
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': task_name,
                        'description': task_desc,
                        'api_name': task_api_name,
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
        message = messages.MSG_PT_0037(1)
        assert response.status_code == 400
        assert response.data['message'] == message
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['details']['api_name'] == task_api_name
        assert response.data['details']['reason'] == message
        assert 'name' not in response.data['details']

    def test_create__next_task_field_in_task_name__validation_error(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        field_api_name = 'field-1'
        task_api_name = 'task-1'
        task_name = '{{%s}} title' % field_api_name
        api_client.token_authenticate(user)

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
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': task_name,
                        'api_name': task_api_name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                            },
                        ],
                    },
                    {
                        'number': 2,
                        'name': 'Second step',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                            },
                        ],
                        'fields': [
                            {
                                'order': 1,
                                'name': 'String field',
                                'type': FieldType.STRING,
                                'is_required': True,
                                'api_name': field_api_name,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        message = messages.MSG_PT_0038(task_name)
        assert response.status_code == 400
        assert response.data['message'] == message
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['details']['api_name'] == task_api_name
        assert response.data['details']['reason'] == message
        assert 'name' not in response.data['details']

    def test_create__name_not_required_field__validation_error(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        field_api_name = 'field-1'
        task_api_name = 'task-1'
        task_name = ' {{%s}} ' % field_api_name
        api_client.token_authenticate(user)

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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'String field',
                            'type': FieldType.STRING,
                            'is_required': False,
                            'api_name': field_api_name,
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': task_name,
                        'api_name': task_api_name,
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
        message = messages.MSG_PT_0039(1)
        assert response.status_code == 400
        assert response.data['message'] == message
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['details']['api_name'] == task_api_name
        assert response.data['details']['reason'] == message
        assert 'name' not in response.data['details']

    def test_create__name_not_required_two_fields__validation_error(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        task_api_name = 'task-1'
        field_1_api_name = 'field-1'
        field_2_api_name = 'field-2'
        task_name = ' {{%s}} {{%s}}' % (field_1_api_name, field_2_api_name)
        api_client.token_authenticate(user)

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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'String field',
                            'type': FieldType.STRING,
                            'is_required': False,
                            'api_name': field_1_api_name,
                        },
                        {
                            'order': 2,
                            'name': 'Select field',
                            'type': FieldType.DROPDOWN,
                            'is_required': False,
                            'api_name': field_2_api_name,
                            'selections': [
                                {
                                    'api_name': 'selection-1',
                                    'value': 'some value',
                                },
                            ],
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': task_name,
                        'api_name': task_api_name,
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
        message = messages.MSG_PT_0039(1)
        assert response.status_code == 400
        assert response.data['message'] == message
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['details']['api_name'] == task_api_name
        assert response.data['details']['reason'] == message
        assert 'name' not in response.data['details']

    def test_create__delay_in_first_task__ok(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        task_api_name = 'task-1'
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'is_active': True,
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'delay': '10 00:59:59',
                        'api_name': task_api_name,
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

    def test_create__delay_is_null__ok(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'is_active': True,
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'delay': None,
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

    def test_create__due_date_for_delayed_task__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(user, tasks_count=2, is_active=True)
        template_task_2 = template.tasks.get(number=2)
        template_task_2.delay = timedelta(days=1)
        template_task_2.save()
        RawDueDateTemplate.objects.create(
            task=template_task_2,
            template=template,
            duration=timedelta(hours=1),
            duration_months=0,
            rule=DueDateRule.AFTER_TASK_STARTED,
            source_id=template_task_2.api_name,
        )

        response_run = api_client.post(
            path=f'/templates/{template.id}/run',
            data={},
        )
        workflow = Workflow.objects.get(id=response_run.data['id'])
        task_1 = workflow.tasks.get(number=1)
        response_complete = api_client.post(f'/v2/tasks/{task_1.id}/complete')
        workflow.refresh_from_db()
        task_2 = workflow.tasks.get(number=2)
        service = WorkflowActionService(user=user, workflow=workflow)

        # act
        service.resume_task(task_2)

        # assert
        assert response_complete.status_code == 200
        due_date = task_2.date_first_started + timedelta(hours=1)
        assert task_2.due_date == due_date
        assert task_2.status == TaskStatus.ACTIVE

    def test_create__due_in__event_fired(
        self,
        mocker,
        api_client,
    ):
        # arrange
        analysis_mock = mocker.patch(
            'src.processes.serializers.templates.task.'
            'AnalyticService.templates_task_due_date_created',
        )
        user = create_test_user()
        api_client.token_authenticate(user)
        duration = '10:00:00'

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'is_active': True,
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'api_name': 'task-1',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                            },
                        ],
                        'raw_due_date': {
                            'api_name': 'raw-due-date-bwybf0',
                            'rule': 'after task started',
                            'duration_months': 0,
                            'duration': duration,
                            'source_id': 'task-1',
                        },
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        task_data = response.data['tasks'][0]
        assert task_data['raw_due_date']['duration'] == duration
        template = Template.objects.get(id=response.data['id'])
        analysis_mock.assert_called_once_with(
            user=user,
            template=template,
            task=template.tasks.get(number=1),
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )

    def test_create__draft_due_in__event_not_fired(
        self,
        mocker,
        api_client,
    ):
        # arrange
        analysis_mock = mocker.patch(
            'src.processes.serializers.templates.task.'
            'AnalyticService.templates_task_due_date_created',
        )
        user = create_test_user()
        api_client.token_authenticate(user)
        duration = '10:00:00'

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'is_active': False,
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'api_name': 'task-1',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                            },
                        ],
                        'raw_due_date': {
                            'api_name': 'raw-due-date-bwybf0',
                            'rule': 'after task started',
                            'duration_months': 0,
                            'duration': duration,
                            'source_id': 'task-1',
                        },
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        task_data = response.data['tasks'][0]
        assert task_data['raw_due_date']['duration'] == duration
        analysis_mock.assert_not_called()

    def test_create__equal_api_names__save_last(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        step_name = 'Second step'
        step_api_name = 'step-1'

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'is_active': True,
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'api_name': step_api_name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                            },
                        ],
                    },
                    {
                        'number': 2,
                        'name': step_name,
                        'api_name': step_api_name,
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
        assert len(response.data['tasks']) == 1
        response_data = response.data['tasks'][0]
        assert response_data['name'] == step_name
        assert response_data['number'] == 2
        assert response_data['api_name'] == step_api_name

    def test_create__set_return_to_task__ok(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        revert_task_api_name = 'task-321'
        request_data = [
            {
                'number': 1,
                'name': 'First step',
                'api_name': revert_task_api_name,
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
            {
                'number': 2,
                'name': 'Revert step',
                'revert_task': revert_task_api_name,
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
                'conditions': [
                    {
                        'order': 1,
                        'action': ConditionAction.START_TASK,
                        'rules': [
                            {
                                'predicates': [
                                    {
                                      'field_type': PredicateType.TASK,
                                      'operator': PredicateOperator.COMPLETED,
                                      'field': revert_task_api_name,
                                      'value': None,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ]

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'is_active': True,
                'tasks': request_data,
            },
        )

        # assert
        assert response.status_code == 200
        assert len(response.data['tasks']) == 2
        response_data = response.data['tasks'][1]
        assert response_data['revert_task'] == revert_task_api_name
        task = TaskTemplate.objects.get(api_name=response_data['api_name'])
        assert task.revert_task == revert_task_api_name

    def test_create__set_return_to_task__not_ancestor__validation_error(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        task_1_api_name = 'task-1'
        task_1_name = 'Task 1'
        revert_task_api_name = 'task-321'
        request_data = [
            {
                'number': 1,
                'name': task_1_name,
                'api_name': task_1_api_name,
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
                'revert_task': revert_task_api_name,
            },
            {
                'number': 2,
                'name': 'Revert step',
                'api_name': revert_task_api_name,
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
                'conditions': [
                    {
                        'order': 1,
                        'action': ConditionAction.START_TASK,
                        'rules': [
                            {
                                'predicates': [
                                    {
                                      'field_type': PredicateType.TASK,
                                      'operator': PredicateOperator.COMPLETED,
                                      'field': task_1_api_name,
                                      'value': None,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ]

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'is_active': True,
                'tasks': request_data,
            },
        )

        # assert
        assert response.status_code == 400
        message = messages.MSG_PT_0061(name=task_1_name)
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['api_name'] == task_1_api_name

    def test_create__set_return_to_task__same_level__validation_error(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        revert_task_api_name = 'task-1'
        task_2_api_name = 'task-2'
        task_2_name = 'Task 2'
        request_data = [
            {
                'number': 1,
                'name': 'Task 1',
                'api_name': revert_task_api_name,
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
            {
                'number': 2,
                'name': task_2_name,
                'api_name': task_2_api_name,
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
                'revert_task': revert_task_api_name,
            },
        ]

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'is_active': True,
                'tasks': request_data,
            },
        )

        # assert
        assert response.status_code == 400
        message = messages.MSG_PT_0061(name=task_2_name)
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['api_name'] == task_2_api_name

    def test_create__multiple_ancestors__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        task_1_api_name = 'task-1'
        task_2_api_name = 'task-2'
        request_data = [
            {
                'number': 1,
                'name': 'First step',
                'api_name': task_1_api_name,
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
            {
                'number': 2,
                'name': 'Step 2',
                'api_name': task_2_api_name,
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
                'conditions': [
                    {
                        'order': 1,
                        'action': ConditionAction.START_TASK,
                        'rules': [
                            {
                                'predicates': [
                                    {
                                      'field_type': PredicateType.TASK,
                                      'operator': PredicateOperator.COMPLETED,
                                      'field': task_1_api_name,
                                      'value': None,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                'number': 3,
                'name': 'Step 3',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
                'conditions': [
                    {
                        'order': 1,
                        'action': ConditionAction.START_TASK,
                        'rules': [
                            {
                                'predicates': [
                                    {
                                      'field_type': PredicateType.TASK,
                                      'operator': PredicateOperator.COMPLETED,
                                      'field': task_2_api_name,
                                      'value': None,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ]

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'is_active': True,
                'tasks': request_data,
            },
        )

        # assert
        assert response.status_code == 200
        assert len(response.data['tasks']) == 3
        task_1_data = response.data['tasks'][0]
        assert task_1_data['ancestors'] == []
        task_2_data = response.data['tasks'][1]
        assert task_2_data['ancestors'] == [task_1_api_name]
        task_3_data = response.data['tasks'][2]
        assert set(task_3_data['ancestors']) == {
            task_1_api_name,
            task_2_api_name,
        }

    def test_create__not_existent_return_to_task__validation_error(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        not_existent_api_name = 'task-not_existent_api_name'
        task_1_name = 'First step'
        task_1_api_name = 'task-1'
        request_data = [
            {
                'number': 1,
                'name': task_1_name,
                'api_name': task_1_api_name,
                'revert_task': not_existent_api_name,
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
            {
                'number': 2,
                'api_name': 'task-2',
                'name': 'Revert step',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
        ]

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'is_active': True,
                'tasks': request_data,
            },
        )

        # assert
        assert response.status_code == 400
        message = messages.MSG_PT_0059(
            name=task_1_name,
            api_name=not_existent_api_name,
        )
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['api_name'] == task_1_api_name

    def test_create__return_to_task__to_itself__validation_error(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        api_name = 'task-312'
        task_name = 'First step'
        request_data = [
            {
                'number': 1,
                'name': task_name,
                'api_name': api_name,
                'revert_task': api_name,
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
        ]

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'is_active': True,
                'tasks': request_data,
            },
        )

        # assert
        assert response.status_code == 400
        message = messages.MSG_PT_0060(name=task_name)
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['api_name'] == api_name

    def test_create__set_task_parents__ok(self, api_client):

        # arrange
        user = create_test_user()
        task_1_api_name = 'task-1'
        task_2_api_name = 'task-2'

        tasks_data = [
            {
                'number': 1,
                'name': 'Task 1',
                'api_name': task_1_api_name,
                'conditions': [
                    {
                        'order': 1,
                        'action': ConditionAction.START_TASK,
                        'rules': [
                            {
                                'predicates': [
                                    {
                                      'field_type': PredicateType.KICKOFF,
                                      'operator': PredicateOperator.COMPLETED,
                                      'field': 'task-2-api-name',
                                      'value': None,
                                    },
                                ],
                            },
                        ],
                    },
                ],
                'raw_performers': [
                    {
                        'type': PerformerType.WORKFLOW_STARTER,
                        'source_id': None,
                    },
                ],
            },
            {
                'number': 2,
                'name': 'Task 2',
                'api_name': task_2_api_name,
                'conditions': [
                    {
                        'order': 1,
                        'action': ConditionAction.START_TASK,
                        'rules': [
                            {
                                'predicates': [
                                    {
                                      'field_type': PredicateType.TASK,
                                      'operator': PredicateOperator.COMPLETED,
                                      'field': task_1_api_name,
                                      'value': None,
                                    },
                                ],
                            },
                        ],
                    },
                ],
                'raw_performers': [
                    {
                        'type': PerformerType.WORKFLOW_STARTER,
                        'source_id': None,
                    },
                ],
            },
        ]
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'is_active': True,
                'tasks': tasks_data,
            },
        )

        # assert
        assert response.status_code == 200
        task_1_data = response.data['tasks'][0]
        assert task_1_data['parents'] == []
        task_2_data = response.data['tasks'][1]
        assert task_2_data['parents'] == [task_1_api_name]
        assert task_2_data['ancestors'] == [task_1_api_name]


class TestCreateTemplateRawPerformer:

    def test_create__only_required_fields__defaults_ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': True,
                'description': '',
                'kickoff': {},
                'tasks': [
                    {
                        'name': 'First task',
                        'number': 1,
                        'raw_performers': [
                            {
                                'type': PerformerType.WORKFLOW_STARTER,
                                'source_id': None,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        response_data = response.data['tasks'][0]['raw_performers']
        assert len(response_data) == 1
        assert response_data[0].get('api_name')
        assert response_data[0]['type'] == PerformerType.WORKFLOW_STARTER
        assert response_data[0]['source_id'] is None
        assert response_data[0]['label'] == 'Workflow starter'

        template = Template.objects.get(id=response.data['id'])
        task = template.tasks.first()
        raw_performers = task.raw_performers.all()
        assert raw_performers.count() == 1
        assert raw_performers.first().type == PerformerType.WORKFLOW_STARTER

    def test_create__type_field__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        field_api_name = 'user-field-1'
        field_name = 'First task performer'
        api_name_raw_performer = 'raw-performer-1'

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': True,
                'description': '',
                'kickoff': {
                    'fields': [
                        {
                            'name': field_name,
                            'order': 1,
                            'type': FieldType.USER,
                            'is_required': True,
                            'api_name': field_api_name,
                        },
                    ],
                },
                'tasks': [
                    {
                        'name': 'First task',
                        'number': 1,
                        'raw_performers': [
                            {
                                'type': PerformerType.FIELD,
                                'source_id': field_api_name,
                                'api_name': api_name_raw_performer,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        response_data = response.data['tasks'][0]['raw_performers']
        assert len(response_data) == 1
        assert response_data[0]['api_name'] == api_name_raw_performer
        assert response_data[0]['type'] == PerformerType.FIELD
        assert response_data[0]['source_id'] == field_api_name
        assert response_data[0]['label'] == field_name

        template = Template.objects.get(id=response.data['id'])
        task = template.tasks.first()
        raw_performers = task.raw_performers.all()
        assert raw_performers.count() == 1
        assert raw_performers.first().field.api_name == field_api_name
        assert raw_performers.first().type == PerformerType.FIELD

    def test_create__type_field_value_is_null__validation_error(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        field_api_name = 'user-field-1'
        api_name_raw_performer = 'raw-performer-1'

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': True,
                'description': '',
                'kickoff': {
                    'fields': [
                        {
                            'name': 'First task performer',
                            'order': 1,
                            'type': FieldType.USER,
                            'is_required': True,
                            'api_name': field_api_name,
                        },
                    ],
                },
                'tasks': [
                    {
                        'name': 'First task',
                        'number': 1,
                        'api_name': 'task-66',
                        'raw_performers': [
                            {
                                'type': PerformerType.FIELD,
                                'source_id': None,
                                'api_name': api_name_raw_performer,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == messages.MSG_PT_0036
        assert response.data['details']['reason'] == messages.MSG_PT_0036
        assert response.data['details']['api_name'] == 'task-66'

    def test_create__type_field_not_existing_value__validation_error(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        api_name_raw_performer = 'raw-performer-1'

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': True,
                'description': '',
                'kickoff': {},
                'tasks': [
                    {
                        'name': 'First task',
                        'number': 1,
                        'api_name': 'task-66',
                        'raw_performers': [
                            {
                                'type': PerformerType.FIELD,
                                'source_id': 'not-existing',
                                'api_name': api_name_raw_performer,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 400
        message = 'One or more performers are incorrect.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['api_name'] == 'task-66'

    def test_create__type_field_from_another_account__validation_error(
        self,
        api_client,
    ):
        # arrange
        another_user = create_test_user(email='another@pneumatic,app')
        another_template = create_test_template(
            user=another_user,
            is_active=True,
        )
        unavailable_field = FieldTemplate.objects.create(
            name="Bad performer",
            type=FieldType.USER,
            is_required=True,
            kickoff=another_template.kickoff_instance,
            template=another_template,
        )

        user = create_test_user()
        api_client.token_authenticate(user)
        api_name_raw_performer = 'raw-performer-1'

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': True,
                'description': '',
                'kickoff': {},
                'tasks': [
                    {
                        'name': 'First task',
                        'number': 1,
                        'api_name': 'task-66',
                        'raw_performers': [
                            {
                                'type': PerformerType.FIELD,
                                'source_id': unavailable_field.api_name,
                                'api_name': api_name_raw_performer,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 400
        message = 'One or more performers are incorrect.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['api_name'] == 'task-66'

    def test_create__type_field_from_future_task__validation_error(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        api_name_raw_performer_1 = 'raw-performer-1'
        api_name_raw_performer_2 = 'raw-performer-2'
        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': True,
                'description': '',
                'kickoff': {},
                'tasks': [
                    {
                        'name': 'First task',
                        'number': 1,
                        'api_name': 'task-66',
                        'raw_performers': [
                            {
                                'type': PerformerType.FIELD,
                                'source_id': 'user-field-1',
                                'api_name': api_name_raw_performer_1,
                            },
                        ],
                    },
                    {
                        'name': 'First task',
                        'number': 2,
                        'api_name': 'task-67',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                                'api_name': api_name_raw_performer_2,
                            },
                        ],
                        'fields': [
                            {
                                'order': 1,
                                'name': 'First step performer',
                                'type': FieldType.USER,
                                'is_required': True,
                                'api_name': 'user-field-1',
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 400
        message = 'One or more performers are incorrect.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['api_name'] == 'task-66'

    def test_create__type_field_duplicate__validation_error(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        field_api_name = 'user-field-1'
        api_name_raw_performer_1 = 'raw-performer-1'
        api_name_raw_performer_2 = 'raw-performer-2'

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': True,
                'description': '',
                'kickoff': {
                    'fields': [
                        {
                            'name': 'First task performer',
                            'order': 1,
                            'type': FieldType.USER,
                            'is_required': True,
                            'api_name': field_api_name,
                        },
                    ],
                },
                'tasks': [
                    {
                        'name': 'First task',
                        'number': 1,
                        'api_name': 'task-66',
                        'raw_performers': [
                            {
                                'type': PerformerType.FIELD,
                                'source_id': field_api_name,
                                'api_name': api_name_raw_performer_1,
                            },
                            {
                                'type': PerformerType.FIELD,
                                'source_id': field_api_name,
                                'api_name': api_name_raw_performer_2,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == messages.MSG_PT_0003
        assert response.data['details']['reason'] == messages.MSG_PT_0003
        assert response.data['details']['api_name'] == 'task-66'

    def test_create__type_user__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        api_name_raw_performer = 'raw-performer-1'

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': True,
                'description': '',
                'kickoff': {},
                'tasks': [
                    {
                        'name': 'First task',
                        'number': 1,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                                'api_name': api_name_raw_performer,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        response_data = response.data['tasks'][0]['raw_performers']
        assert len(response_data) == 1
        assert response_data[0]['api_name'] == api_name_raw_performer
        assert response_data[0]['type'] == PerformerType.USER
        assert response_data[0]['label'] == user.name_by_status
        assert response_data[0]['source_id'] == str(user.id)

        template = Template.objects.get(id=response.data['id'])
        task = template.tasks.first()
        raw_performers = task.raw_performers.all()
        assert raw_performers.count() == 1
        assert raw_performers.first().user.id == user.id
        assert raw_performers.first().type == PerformerType.USER

    @pytest.mark.parametrize('is_active', (True, False))
    def test_create__type_user_invited_label__ok(
        self,
        api_client,
        is_active,
    ):
        # arrange
        user = create_test_user()
        invited = create_invited_user(user)
        api_client.token_authenticate(user)
        api_name_raw_performer = 'raw-performer-1'

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                    {
                        'type': OwnerType.USER,
                        'source_id': invited.id,
                    },
                ],
                'is_active': is_active,
                'description': '',
                'kickoff': {},
                'tasks': [
                    {
                        'name': 'First task',
                        'number': 1,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': str(invited.id),
                                'label': f'{invited.email} (invited user)',
                                'api_name': api_name_raw_performer,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        response_data = response.data['tasks'][0]['raw_performers']
        assert len(response_data) == 1
        assert response_data[0]['api_name'] == api_name_raw_performer
        assert response_data[0]['type'] == PerformerType.USER
        assert response_data[0]['label'] == invited.name_by_status
        assert response_data[0]['source_id'] == str(invited.id)

    def test_create__type_user_inactive_user__validation_error(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        inactive_user = create_test_user(
            email='inactive@pneumatic.app',
            account=user.account,
        )
        UserService.deactivate(inactive_user)
        api_client.token_authenticate(user)
        api_name_raw_performer = 'raw-performer-1'

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {},
                'is_active': True,
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'api_name': 'task-66',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': inactive_user.id,
                                'api_name': api_name_raw_performer,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 400
        message = 'One or more performers are incorrect.'
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['api_name'] == 'task-66'

    def test_create__type_user_value_is_null__validation_error(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        api_name_raw_performer = 'raw-performer-1'

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': True,
                'description': '',
                'kickoff': {},
                'tasks': [
                    {
                        'name': 'First task',
                        'number': 1,
                        'api_name': 'task-66',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': None,
                                'api_name': api_name_raw_performer,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == messages.MSG_PT_0032
        assert response.data['details']['reason'] == messages.MSG_PT_0032
        assert response.data['details']['api_name'] == 'task-66'

    def test_create__type_user_not_number_value__validation_error(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        api_name_raw_performer = 'raw-performer-1'

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': True,
                'description': '',
                'kickoff': {},
                'tasks': [
                    {
                        'name': 'First task',
                        'number': 1,
                        'api_name': 'task-66',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': 'abc',
                                'api_name': api_name_raw_performer,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 400
        message = messages.MSG_PT_0033
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['api_name'] == 'task-66'

    def test_create__type_user_not_existing_value__validation_error(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        api_name_raw_performer = 'raw-performer-1'

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': True,
                'description': '',
                'kickoff': {},
                'tasks': [
                    {
                        'name': 'First task',
                        'number': 1,
                        'api_name': 'task-66',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': '-999999999',
                                'api_name': api_name_raw_performer,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        message = 'One or more performers are incorrect.'
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['api_name'] == 'task-66'

    def test_create__type_user_from_another_account__validation_error(
        self,
        api_client,
    ):
        # arrange
        another_user = create_test_user(email='another@pneumatic,app')

        user = create_test_user()
        api_client.token_authenticate(user)
        api_name_raw_performer = 'raw-performer-1'

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': True,
                'description': '',
                'kickoff': {},
                'tasks': [
                    {
                        'name': 'First task',
                        'number': 1,
                        'api_name': 'task-66',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': another_user.id,
                                'api_name': api_name_raw_performer,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        message = 'One or more performers are incorrect.'
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['api_name'] == 'task-66'

    def test_create__type_user_duplicate__validation_error(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        api_name_raw_performer_1 = 'raw-performer-1'
        api_name_raw_performer_2 = 'raw-performer-2'

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': True,
                'description': '',
                'kickoff': {},
                'tasks': [
                    {
                        'name': 'First task',
                        'number': 1,
                        'api_name': 'task-66',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                                'api_name': api_name_raw_performer_1,
                            },
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                                'api_name': api_name_raw_performer_2,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == messages.MSG_PT_0003
        assert response.data['details']['reason'] == messages.MSG_PT_0003
        assert response.data['details']['api_name'] == 'task-66'

    def test_create__type_workflow_starter__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        api_name_raw_performer = 'raw-performer-1'

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': True,
                'description': '',
                'kickoff': {},
                'tasks': [
                    {
                        'name': 'First task',
                        'number': 1,
                        'raw_performers': [
                            {
                                'type': PerformerType.WORKFLOW_STARTER,
                                'source_id': None,
                                'api_name': api_name_raw_performer,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        response_data = response.data['tasks'][0]['raw_performers']
        assert len(response_data) == 1
        assert response_data[0]['api_name'] == api_name_raw_performer
        assert response_data[0]['type'] == PerformerType.WORKFLOW_STARTER
        assert response_data[0]['label'] == 'Workflow starter'

        template = Template.objects.get(id=response.data['id'])
        task = template.tasks.first()
        raw_performers = task.raw_performers.all()
        assert raw_performers.count() == 1
        assert raw_performers.first().type == PerformerType.WORKFLOW_STARTER

    def test_create__type_workflow_starter_duplicate__validation_error(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        api_name_raw_performer_1 = 'raw-performer-1'
        api_name_raw_performer_2 = 'raw-performer-2'

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': True,
                'description': '',
                'kickoff': {},
                'tasks': [
                    {
                        'name': 'First task',
                        'number': 1,
                        'api_name': 'task-66',
                        'raw_performers': [
                            {
                                'type': PerformerType.WORKFLOW_STARTER,
                                'source_id': None,
                                'api_name': api_name_raw_performer_1,
                            },
                            {
                                'type': PerformerType.WORKFLOW_STARTER,
                                'source_id': None,
                                'api_name': api_name_raw_performer_2,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == messages.MSG_PT_0003
        assert response.data['details']['reason'] == messages.MSG_PT_0003
        assert response.data['details']['api_name'] == 'task-66'

    def test_create__type_workflow_starter_public_template__validation_error(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        task_api_name = 'task-1'
        api_name_raw_performer = 'raw-performer-1'

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': True,
                'is_public': True,
                'description': '',
                'kickoff': {},
                'tasks': [
                    {
                        'name': 'First task',
                        'api_name': task_api_name,
                        'number': 1,
                        'raw_performers': [
                            {
                                'type': PerformerType.WORKFLOW_STARTER,
                                'source_id': None,
                                'api_name': api_name_raw_performer,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 400
        assert response.data['message'] == messages.MSG_PT_0035
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['details']['reason'] == messages.MSG_PT_0035
        assert response.data['details']['api_name'] == task_api_name

    def test_create__all_types__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        field_api_name = 'user-field-1'
        api_name_raw_performer_1 = 'raw-performer-1'
        api_name_raw_performer_2 = 'raw-performer-2'
        api_name_raw_performer_3 = 'raw-performer-3'

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': True,
                'description': '',
                'kickoff': {
                    'fields': [
                        {
                            'name': 'First task performer',
                            'order': 1,
                            'type': FieldType.USER,
                            'is_required': True,
                            'api_name': field_api_name,
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First task',
                        'api_name': 'task-66',
                        'raw_performers': [
                            {
                                'type': PerformerType.FIELD,
                                'source_id': field_api_name,
                                'api_name': api_name_raw_performer_1,
                            },
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                                'api_name': api_name_raw_performer_2,
                            },
                            {
                                'type': PerformerType.WORKFLOW_STARTER,
                                'source_id': None,
                                'api_name': api_name_raw_performer_3,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        response_data = response.data['tasks'][0]['raw_performers']
        assert len(response_data) == 3

        template = Template.objects.get(id=response.data['id'])
        task = template.tasks.first()
        assert task.raw_performers.all().count() == 3

    def test_create__pending_transfer__ok(
        self,
        api_client,
    ):

        # arrange
        user = create_test_user()
        invited_user = create_test_user(email='another@pneumatic.app')
        UserInvite.objects.create(
            email=invited_user.email,
            account=user.account,
            invited_by=user,
            invited_user=invited_user,
        )
        api_client.token_authenticate(user)
        api_name_raw_performer = 'raw-performer-1'

        # act
        response = api_client.post(
            '/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                    {
                        'type': OwnerType.USER,
                        'source_id': invited_user.id,
                    },
                ],
                'is_active': True,
                'description': '',
                'kickoff': {},
                'tasks': [
                    {
                        'name': 'First step',
                        'number': 1,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': invited_user.id,
                                'api_name': api_name_raw_performer,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        response_data = response.data['tasks'][0]['raw_performers']
        assert len(response_data) == 1
        assert response_data[0]['api_name'] == api_name_raw_performer
        assert response_data[0]['type'] == PerformerType.USER

    @pytest.mark.parametrize('raw_performers', (
        {
            'type': PerformerType.FIELD,
            'source_id': 'unefined',
            'api_name': 'raw-performer-1',
        },
        [{
            'type': PerformerType.FIELD,
            'source_id': 'unefined',
            'api_name': 'raw-performer-1',
        }],
        [[{
            'type': PerformerType.WORKFLOW_STARTER,
            'source_id': None,
            'api_name': 'raw-performer-1',
        }]],

    ))
    def test_create__incorrect_value_in_draft__skip(
        self,
        raw_performers,
        api_client,
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'is_active': False,
                'description': '',
                'kickoff': {},
                'tasks': [
                    {
                        'name': 'First task',
                        'number': 1,
                        'api_name': 'task-66',
                        'raw_performers': raw_performers,
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
