import pytest

from src.accounts.enums import BillingPlanType
from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    ConditionAction,
    FieldType,
    OwnerType,
    PerformerType,
    PredicateOperator,
    PredicateType,
)
from src.processes.messages import template as messages
from src.processes.models.templates.conditions import (
    ConditionTemplate,
    PredicateTemplate,
)
from src.processes.models.templates.template import Template
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_owner,
    create_test_user,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


class TestCreateConditionTemplate:

    @pytest.mark.parametrize('value', (None, [None]))
    def test_create__conditions_is_null__validation_error(
        self,
        value,
        mocker,
        api_client,
    ):
        # arrange
        condition_create_analysis_mock = mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        user = create_test_user()
        account = user.account
        account.save()
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
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'api_name': 'task-55',
                        'conditions': value,
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
        message = 'Conditions: this field may not be null.'
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['api_name'] == 'task-55'
        assert response.data['details']['reason'] == message
        assert 'name' not in response.data['details']
        condition_create_analysis_mock.assert_not_called()

    def test_create__conditions_in_second_task_is_null__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        condition_create_analysis_mock = mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        user = create_test_user()
        account = user.account
        account.save()
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
                        'name': 'First step',
                        'api_name': 'task-54',
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
                        'api_name': 'task-55',
                        'conditions': None,
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
        message = 'Conditions: this field may not be null.'
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['api_name'] == 'task-55'
        assert response.data['details']['reason'] == message
        assert 'name' not in response.data['details']
        condition_create_analysis_mock.assert_not_called()

    def test_create__conditions_second_is_null__validation_error(
        self,
        mocker,
        api_client,
    ):

        # arrange
        condition_create_analysis_mock = mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        account = create_test_account()
        user = create_test_user(account=account)
        api_client.token_authenticate(user)
        conditions = [
            {
                'order': 1,
                'action': ConditionAction.SKIP_TASK,
                'rules': [
                    {
                        'predicates': [
                            {
                                'field': 'user-field-1',
                                'field_type': PredicateType.USER,
                                'operator': PredicateOperator.EQUAL,
                                'value': user.id,
                            },
                        ],
                    },
                ],
            },
            None,
        ]

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
                            'api_name': 'user-field-1',
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'api_name': 'task-66',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                            },
                        ],
                        'conditions': conditions,
                    },
                ],
            },
        )

        # assert
        message = 'Conditions: this field may not be null.'
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['api_name'] == 'task-66'
        assert response.data['details']['reason'] == message
        assert 'name' not in response.data['details']
        condition_create_analysis_mock.assert_not_called()

    def test_create__conditions_two_errors__validation_error(
        self,
        mocker,
        api_client,
    ):

        # arrange
        condition_create_analysis_mock = mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        account = create_test_account()
        user = create_test_user(account=account)
        api_client.token_authenticate(user)
        conditions = [
            {
                'order': 1,
                'action': ConditionAction.SKIP_TASK,
                'rules': None,
            },
            None,
        ]

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
                            'api_name': 'user-field-1',
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'api_name': 'task-66',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                            },
                        ],
                        'conditions': conditions,
                    },
                ],
            },
        )

        # assert
        message = {
            'Conditions: this field may not be null.',
            'Rules: this field may not be null.',
        }
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] in message
        assert response.data['details']['api_name'] == 'task-66'
        assert response.data['details']['reason'] in message
        assert 'name' not in response.data['details']
        condition_create_analysis_mock.assert_not_called()

    def test_create__conditions_is_string__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        condition_create_analysis_mock = mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        user = create_test_user()
        account = user.account
        account.save()
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
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'api_name': 'task-55',
                        'conditions': 'undefined',
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
        message = 'Conditions: expected a list of items but got type "str".'
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['api_name'] == 'task-55'
        assert response.data['details']['reason'] == message
        assert 'name' not in response.data['details']
        condition_create_analysis_mock.assert_not_called()

    def test_create__conditions_is_integer__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        condition_create_analysis_mock = mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        user = create_test_user()
        account = user.account
        account.save()
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
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'api_name': 'task-55',
                        'conditions': 123,
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
        message = 'Conditions: expected a list of items but got type "int".'
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['api_name'] == 'task-55'
        assert response.data['details']['reason'] == message
        assert 'name' not in response.data['details']
        condition_create_analysis_mock.assert_not_called()

    def test_create__without_rules__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        condition_create_analysis_mock = mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        user = create_test_user()
        account = user.account
        account.save()
        api_client.token_authenticate(user)
        request_data = {
            'api_name': 'condition-66',
            'rules': [],
            'order': 1,
            'action': ConditionAction.SKIP_TASK,
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
                            'api_name': 'user-field-1',
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'api_name': 'task-55',
                        'conditions': [request_data],
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
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == 'Rules: this list may not be empty.'
        assert response.data['details']['api_name'] == 'condition-66'
        assert 'name' not in response.data['details']
        condition_create_analysis_mock.assert_not_called()

    def test_create__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        condition_create_analysis_mock = mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        user = create_test_user()
        account = user.account
        account.save()
        api_client.token_authenticate(user)
        request_data = {
            'rules': [
                {
                    'predicates': [
                        {
                            'field': 'user-field-1',
                            'field_type': PredicateType.USER,
                            'operator': PredicateOperator.EQUAL,
                            'value': user.id,
                        },
                    ],
                },
            ],
            'order': 1,
            'action': ConditionAction.SKIP_TASK,
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
                            'api_name': 'user-field-1',
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'conditions': [request_data],
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
        condition_data = response.data['tasks'][0]['conditions'][0]
        assert condition_data['api_name']
        assert condition_data['rules'][0]['api_name']
        assert condition_data['rules'][0]['predicates'][0]['api_name']
        predicate_data = condition_data['rules'][0]['predicates'][0]
        assert predicate_data['field_type'] == PredicateType.USER
        assert predicate_data['operator'] == PredicateOperator.EQUAL
        assert predicate_data['value'] == str(user.id)
        assert predicate_data['field'] == 'user-field-1'

        template = Template.objects.get(id=response.data['id'])
        condition = ConditionTemplate.objects.get(
            api_name=condition_data['api_name'],
        )
        predicate = PredicateTemplate.objects.get(
            rule__condition=condition,
            field_type=PredicateType.USER,
            operator=PredicateOperator.EQUAL,
            value=str(user.id),
            field='user-field-1',
        )
        assert predicate.user_id == user.id
        condition_create_analysis_mock.assert_called_once_with(
            user=user,
            template=template,
            task=template.tasks.get(number=1),
            condition=condition,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )

    @pytest.mark.parametrize(
        'data',
        (
            (PredicateOperator.EXIST, PredicateType.USER),
            (PredicateOperator.NOT_EXIST, PredicateType.USER),
        ),
    )
    def test_create__unary_operators_with_none_value__ok(
        self,
        mocker,
        api_client,
        data,
    ):
        # arrange
        mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        user = create_test_user()
        account = user.account
        account.save()
        api_client.token_authenticate(user)
        request_data = {
            'rules': [
                {
                    'predicates': [
                        {
                            'field': 'user-field-1',
                            'field_type': data[1],
                            'operator': data[0],
                        },
                    ],
                },
            ],
            'order': 1,
            'action': ConditionAction.SKIP_TASK,
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
                            'api_name': 'user-field-1',
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'conditions': [request_data],
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
        condition = response.data['tasks'][0]['conditions'][0]
        assert condition['api_name']
        assert condition['rules'][0]['api_name']
        assert condition['rules'][0]['predicates'][0]['api_name']
        predicate_data = condition['rules'][0]['predicates'][0]
        assert predicate_data['field_type'] == data[1]
        assert predicate_data['operator'] == data[0]
        assert predicate_data['value'] is None

    @pytest.mark.parametrize(
        'value',
        ['123', 'not integer'],
    )
    def test_create__user_field_incorrect_value__validation_error(
        self,
        mocker,
        api_client,
        value,
    ):
        # arrange
        condition_create_analysis_mock = mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        user = create_test_user()
        account = user.account
        account.save()
        api_client.token_authenticate(user)
        api_name = 'predicate-api-name'
        task_name = 'First step'
        request_data = {
            'rules': [
                {
                    'predicates': [
                        {
                            'field': 'user-field-1',
                            'field_type': PredicateType.USER,
                            'operator': PredicateOperator.EQUAL,
                            'value': value,
                            'api_name': api_name,
                        },
                    ],
                },
            ],
            'order': 1,
            'action': ConditionAction.SKIP_TASK,
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
                            'api_name': 'user-field-1',
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': task_name,
                        'conditions': [request_data],
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
        message = messages.MSG_PT_0043(task=task_name, user_id=value)
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['api_name'] == api_name
        assert response.data['details']['reason'] == message
        condition_create_analysis_mock.assert_not_called()

    @pytest.mark.parametrize(
        'value',
        ['123', 'not integer'],
    )
    def test_create__group_field_incorrect_value__validation_error(
        self,
        mocker,
        api_client,
        value,
    ):
        # arrange
        condition_create_analysis_mock = mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        user = create_test_owner()
        account = user.account
        account.save()
        api_client.token_authenticate(user)
        api_name = 'predicate-api-name'
        task_name = 'First step'
        request_data = {
            'rules': [
                {
                    'predicates': [
                        {
                            'field': 'group-field-1',
                            'field_type': PredicateType.GROUP,
                            'operator': PredicateOperator.EQUAL,
                            'value': value,
                            'api_name': api_name,
                        },
                    ],
                },
            ],
            'order': 1,
            'action': 'skip_task',
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
                            'api_name': 'group-field-1',
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': task_name,
                        'conditions': [request_data],
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
        message = messages.MSG_PT_0062(task=task_name, group_id=value)
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['api_name'] == api_name
        assert response.data['details']['reason'] == message
        condition_create_analysis_mock.assert_not_called()

    def test_create__group_field_valid_value__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        condition_create_analysis_mock = mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        user = create_test_owner()
        account = user.account
        account.save()
        group = create_test_group(account=account)
        api_client.token_authenticate(user)
        api_name = 'predicate-api-name'
        task_name = 'First step'
        request_data = {
            'rules': [
                {
                    'predicates': [
                        {
                            'field': 'group-field-1',
                            'field_type': PredicateType.GROUP,
                            'operator': PredicateOperator.EQUAL,
                            'value': str(group.id),
                            'api_name': api_name,
                        },
                    ],
                },
            ],
            'order': 1,
            'action': 'skip_task',
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
                            'api_name': 'group-field-1',
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': task_name,
                        'conditions': [request_data],
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
        condition_data = response.data['tasks'][0]['conditions'][0]
        predicate_data = condition_data['rules'][0]['predicates'][0]
        assert predicate_data['field_type'] == PredicateType.GROUP
        assert predicate_data['operator'] == PredicateOperator.EQUAL
        assert predicate_data['value'] == str(group.id)
        assert predicate_data['field'] == 'group-field-1'
        assert predicate_data['api_name'] == api_name

        template = Template.objects.get(id=response.data['id'])
        condition = ConditionTemplate.objects.get(
            api_name=condition_data['api_name'],
        )
        predicate = PredicateTemplate.objects.get(
            rule__condition=condition,
            field_type=PredicateType.GROUP,
            operator=PredicateOperator.EQUAL,
            value=str(group.id),
            field='group-field-1',
        )
        assert predicate.group_id == group.id
        condition_create_analysis_mock.assert_called_once_with(
            user=user,
            template=template,
            task=template.tasks.get(number=1),
            condition=condition,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
        )

    @pytest.mark.parametrize(
        ('field_type', 'value'),
        [
            (FieldType.RADIO, '123'),
            (FieldType.DROPDOWN, '123'),
            (FieldType.CHECKBOX, '123'),
            (FieldType.RADIO, 'disallowed-api-name'),
            (FieldType.DROPDOWN, 'disallowed-api-name'),
            (FieldType.CHECKBOX, 'disallowed-api-name'),
        ],
    )
    def test_create__selection_field_incorrect_value__validation_error(
        self,
        mocker,
        api_client,
        field_type,
        value,
    ):
        # arrange
        condition_create_analysis_mock = mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        field = 'selection-field-1'
        user = create_test_user()
        account = user.account
        account.save()
        api_client.token_authenticate(user)
        predicate_api_name = 'predicate-api-name'
        task_name = 'First step'
        request_data = {
            'rules': [
                {
                    'predicates': [
                        {
                            'field': field,
                            'field_type': field_type,
                            'operator': PredicateOperator.EQUAL,
                            'value': value,
                            'api_name': predicate_api_name,
                        },
                    ],
                },
            ],
            'order': 1,
            'action': ConditionAction.SKIP_TASK,
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
                            'type': field_type,
                            'api_name': field,
                            'selections': [
                                {'value': 1},
                                {'value': 2},
                            ],
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': task_name,
                        'conditions': [request_data],
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
        message = messages.MSG_PT_0045(
            task=task_name,
            selection_api_name=value,
        )
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['api_name'] == predicate_api_name
        assert response.data['details']['reason'] == message
        condition_create_analysis_mock.assert_not_called()

    @pytest.mark.parametrize(
        ('field_type', 'operator'),
        [
            (FieldType.RADIO, PredicateOperator.CONTAIN),
            (FieldType.DROPDOWN, PredicateOperator.MORE_THAN),
            (FieldType.CHECKBOX, PredicateOperator.LESS_THAN),
            (FieldType.USER, PredicateOperator.NOT_CONTAIN),
            (FieldType.URL, PredicateOperator.LESS_THAN),
            (FieldType.FILE, PredicateOperator.EQUAL),
            (FieldType.STRING, PredicateOperator.MORE_THAN),
            (FieldType.TEXT, PredicateOperator.LESS_THAN),
            (FieldType.DATE, PredicateOperator.CONTAIN),
        ],
    )
    def test_create__disallowed_operator__validation_error(
        self,
        mocker,
        api_client,
        field_type,
        operator,
    ):
        # arrange
        condition_create_analysis_mock = mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        field = 'selection-field-1'
        user = create_test_user()
        account = user.account
        account.save()
        api_client.token_authenticate(user)
        predicate_api_name = 'predicate-api-name'
        task_name = 'First step'
        request_data = {
            'rules': [
                {
                    'predicates': [
                        {
                            'field': field,
                            'field_type': field_type,
                            'operator': operator,
                            'value': 1,
                            'api_name': predicate_api_name,
                        },
                    ],
                },
            ],
            'order': 1,
            'action': ConditionAction.SKIP_TASK,
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
                            'type': field_type,
                            'api_name': field,
                            'is_required': True,
                            'selections': [
                                {'value': 1},
                                {'value': 2},
                            ],
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': task_name,
                        'conditions': [request_data],
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
        message = messages.MSG_PT_0044(
            field_type=field_type,
            operator=operator,
            task=task_name,
        )
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['api_name'] == predicate_api_name
        assert response.data['details']['reason'] == message
        condition_create_analysis_mock.assert_not_called()

    def test_create__with_non_existing_field__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        condition_create_analysis_mock = mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        user = create_test_owner()
        task_name = 'Task 1'
        task_api_name = 'task-1'
        api_client.token_authenticate(user)
        request_data = {
            'rules': [
                {
                    'predicates': [
                        {
                            'field': 'non-existing-field',
                            'field_type': PredicateType.USER,
                            'operator': PredicateOperator.EQUAL,
                            'value': user.id,
                        },
                    ],
                },
            ],
            'order': 1,
            'action': ConditionAction.SKIP_TASK,
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
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': task_name,
                        'api_name': task_api_name,
                        'conditions': [request_data],
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
        error_message = messages.MSG_PT_0004(name=task_name)
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == error_message
        condition_create_analysis_mock.assert_not_called()

    def test_create__field_and_condition_together__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        user = create_test_owner()
        task_name = 'Task 1'
        task_api_name = 'task-1'
        field_api_name = 'field-1'
        field_type = FieldType.USER
        api_client.token_authenticate(user)
        request_data = {
            'rules': [
                {
                    'predicates': [
                        {
                            'field': field_api_name,
                            'field_type': field_type,
                            'operator': PredicateOperator.EQUAL,
                            'value': user.id,
                        },
                    ],
                },
            ],
            'order': 1,
            'action': ConditionAction.SKIP_TASK,
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
                        'conditions': [request_data],
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

    def test_create__conditions_with_equal_api_names__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        step = 'First step'
        condition_api_name = 'cond-1'
        user = create_test_user()
        account = user.account
        account.save()
        api_client.token_authenticate(user)
        condition_1 = {
            'rules': [
                {
                    'predicates': [
                        {
                            'field': 'user-field-1',
                            'field_type': PredicateType.USER,
                            'operator': PredicateOperator.EQUAL,
                            'value': user.id,
                        },
                    ],
                },
            ],
            'order': 1,
            'action': ConditionAction.SKIP_TASK,
            'api_name': condition_api_name,
        }
        condition_2 = {
            'rules': [
                {
                    'predicates': [
                        {
                            'field': 'user-field-1',
                            'field_type': PredicateType.USER,
                            'operator': PredicateOperator.EQUAL,
                            'value': user.id,
                        },
                    ],
                },
            ],
            'order': 1,
            'action': ConditionAction.SKIP_TASK,
            'api_name': condition_api_name,
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
                            'api_name': 'user-field-1',
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'conditions': [condition_1],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                            },
                        ],
                    },
                    {
                        'number': 2,
                        'name': step,
                        'conditions': [condition_2],
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
        message = messages.MSG_PT_0049(
            name=step,
            api_name=condition_api_name,
        )
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['api_name'] == condition_api_name

    def test_create__rules_with_equal_api_names__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        rule_api_name = 'rule-1'
        step = 'First step'
        user = create_test_user()
        account = user.account
        account.save()
        api_client.token_authenticate(user)
        condition_1 = {
            'rules': [
                {
                    'predicates': [
                        {
                            'field': 'user-field-1',
                            'field_type': PredicateType.USER,
                            'operator': PredicateOperator.EQUAL,
                            'value': user.id,
                        },
                    ],
                    'api_name': rule_api_name,
                },
            ],
            'order': 1,
            'action': ConditionAction.SKIP_TASK,
        }
        condition_2 = {
            'rules': [
                {
                    'predicates': [
                        {
                            'field': 'user-field-1',
                            'field_type': PredicateType.USER,
                            'operator': PredicateOperator.EQUAL,
                            'value': user.id,
                        },
                    ],
                    'api_name': rule_api_name,
                },
            ],
            'order': 1,
            'action': ConditionAction.SKIP_TASK,
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
                            'api_name': 'user-field-1',
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'conditions': [condition_1],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                            },
                        ],
                    },
                    {
                        'number': 2,
                        'name': step,
                        'conditions': [condition_2],
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
        message = messages.MSG_PT_0053(
            name=step,
            api_name=rule_api_name,
        )
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['api_name'] == rule_api_name

    def test_create__predicates_with_equal_api_names__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        predicate_api_name = 'predicate-1'
        step = 'First step'
        user = create_test_user()
        account = user.account
        account.save()
        api_client.token_authenticate(user)
        condition_1 = {
            'rules': [
                {
                    'predicates': [
                        {
                            'field': 'user-field-1',
                            'field_type': PredicateType.USER,
                            'operator': PredicateOperator.EQUAL,
                            'value': user.id,
                            'api_name': predicate_api_name,
                        },
                    ],
                },
            ],
            'order': 1,
            'action': ConditionAction.SKIP_TASK,
        }
        condition_2 = {
            'rules': [
                {
                    'predicates': [
                        {
                            'field': 'user-field-1',
                            'field_type': PredicateType.USER,
                            'operator': PredicateOperator.EQUAL,
                            'value': user.id,
                            'api_name': predicate_api_name,
                        },
                    ],
                },
            ],
            'order': 1,
            'action': ConditionAction.SKIP_TASK,
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
                            'api_name': 'user-field-1',
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'conditions': [condition_1],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                            },
                        ],
                    },
                    {
                        'number': 2,
                        'name': step,
                        'conditions': [condition_2],
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
        message = messages.MSG_PT_0051(
            name=step,
            api_name=predicate_api_name,
        )
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['api_name'] == predicate_api_name

    def test_create__predicate_type_kickoff_completed__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account(plan=BillingPlanType.UNLIMITED)
        user = create_test_user(account=account)
        mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        predicate_api_name = 'predicate-1'
        condition_data = {
            'order': 1,
            'action': ConditionAction.SKIP_TASK,
            'rules': [
                {
                    'predicates': [
                        {
                            'field_type': PredicateType.KICKOFF,
                            'operator': PredicateOperator.COMPLETED,
                            'api_name': predicate_api_name,
                            'field': None,
                            'value': None,
                        },
                    ],
                },
            ],
        }
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
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'Step 1',
                        'conditions': [condition_data],
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
        condition = response.data['tasks'][0]['conditions'][0]
        predicate = condition['rules'][0]['predicates'][0]
        assert predicate['field_type'] == PredicateType.KICKOFF
        assert predicate['api_name'] == predicate_api_name
        assert predicate['operator'] == PredicateOperator.COMPLETED
        assert predicate['value'] is None
        assert predicate['field'] is None

    def test_create__predicate_type_task__completed__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account(plan=BillingPlanType.UNLIMITED)
        user = create_test_user(account=account)
        mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        predicate_api_name = 'predicate-1'
        task_1_api_name = 'task-1'
        task_2_api_name = 'task-2'
        condition_data = {
            'order': 1,
            'action': ConditionAction.START_TASK,
            'rules': [
                {
                    'predicates': [
                        {
                            'field_type': PredicateType.TASK,
                            'operator': PredicateOperator.COMPLETED,
                            'api_name': predicate_api_name,
                            'field': task_1_api_name,
                            'value': None,
                        },
                    ],
                },
            ],
        }
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
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'Step 1',
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
                        'conditions': [condition_data],
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
        condition = response.data['tasks'][1]['conditions'][0]
        predicate = condition['rules'][0]['predicates'][0]
        assert predicate['field_type'] == PredicateType.TASK
        assert predicate['api_name'] == predicate_api_name
        assert predicate['operator'] == PredicateOperator.COMPLETED
        assert predicate['value'] is None
        assert predicate['field'] == task_1_api_name

    @pytest.mark.parametrize(
        'case', (
            (PredicateOperator.EQUAL, FieldType.STRING, 'yes'),
            (PredicateOperator.NOT_EQUAL, FieldType.STRING, 'yes'),
            (PredicateOperator.MORE_THAN, FieldType.NUMBER, 2),
            (PredicateOperator.LESS_THAN, FieldType.NUMBER, 2),
            (PredicateOperator.EXIST, FieldType.STRING, 'yes'),
            (PredicateOperator.NOT_EXIST, FieldType.STRING, 'yes'),
            (PredicateOperator.CONTAIN, FieldType.STRING, 'yes'),
            (PredicateOperator.NOT_CONTAIN, FieldType.STRING, 'yes'),
        ),
    )
    def test_create__action_start_task_with_incompatible_operators__ok(
        self,
        mocker,
        case,
        api_client,
    ):
        # arrange
        operator, field_type, value = case
        account = create_test_account(plan=BillingPlanType.UNLIMITED)
        user = create_test_user(account=account)
        mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        task_name = 'Task 1'
        predicate_api_name = 'predicate-1'
        field_api_name = 'skip-field-1'
        condition_data = {
            'order': 1,
            'action': ConditionAction.START_TASK,
            'rules': [
                {
                    'predicates': [
                        {
                            'field_type': field_type,
                            'operator': operator,
                            'api_name': predicate_api_name,
                            'field': field_api_name,
                            'value': value,
                        },
                    ],
                },
            ],
        }
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
                            'name': 'Skip',
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
                        'conditions': [condition_data],
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
        message = messages.MSG_PT_0064(name=task_name)
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['api_name'] == predicate_api_name

    @pytest.mark.parametrize(
        'operator', (
            PredicateOperator.EQUAL,
            PredicateOperator.NOT_EQUAL,
            PredicateOperator.MORE_THAN,
            PredicateOperator.LESS_THAN,
            PredicateOperator.EXIST,
            PredicateOperator.NOT_EXIST,
        ),
    )
    def test_create__predicate_type_number_allowed_operators__ok(
        self,
        mocker,
        operator,
        api_client,
    ):
        # arrange
        account = create_test_account(plan=BillingPlanType.UNLIMITED)
        user = create_test_user(account=account)
        mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        predicate_api_name = 'predicate-1'
        field_api_name = 'number-field-1'
        value = '31.6'
        condition_data = {
            'order': 1,
            'action': ConditionAction.SKIP_TASK,
            'rules': [
                {
                    'predicates': [
                        {
                            'field_type': PredicateType.NUMBER,
                            'operator': operator,
                            'api_name': predicate_api_name,
                            'field': field_api_name,
                            'value': value,
                        },
                    ],
                },
            ],
        }
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
                            'name': 'Price',
                            'type': FieldType.NUMBER,
                            'api_name': field_api_name,
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'Step 1',
                        'conditions': [condition_data],
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
        condition = response.data['tasks'][0]['conditions'][0]
        predicate = condition['rules'][0]['predicates'][0]
        assert predicate['field_type'] == PredicateType.NUMBER
        assert predicate['api_name'] == predicate_api_name
        assert predicate['operator'] == operator
        assert predicate['value'] == value
        assert predicate['field'] == field_api_name

    @pytest.mark.parametrize(
        'operator', (
            PredicateOperator.CONTAIN,
            PredicateOperator.NOT_CONTAIN,
            PredicateOperator.COMPLETED,
        ),
    )
    def test_create__predicate_type_number_not_allowed_operators__valid_error(
        self,
        mocker,
        operator,
        api_client,
    ):
        # arrange
        account = create_test_account(plan=BillingPlanType.UNLIMITED)
        user = create_test_user(account=account)
        mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        predicate_api_name = 'predicate-1'
        field_api_name = 'number-field-1'
        step_name = 'Step 1'
        value = '31.6'
        condition_data = {
            'order': 1,
            'action': ConditionAction.SKIP_TASK,
            'rules': [
                {
                    'predicates': [
                        {
                            'field_type': PredicateType.NUMBER,
                            'operator': operator,
                            'api_name': predicate_api_name,
                            'field': field_api_name,
                            'value': value,
                        },
                    ],
                },
            ],
        }
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
                            'name': 'Price',
                            'type': FieldType.NUMBER,
                            'api_name': field_api_name,
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': step_name,
                        'conditions': [condition_data],
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
        message = messages.MSG_PT_0044(
            field_type=FieldType.NUMBER,
            operator=operator,
            task=step_name,
        )
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['api_name'] == predicate_api_name

    @pytest.mark.parametrize(
        'value', (
            ('1-', messages.MSG_PT_0063),
            (None, 'Task "Step 1": operator "equals" should have some value.'),
            ('', 'Value: this field may not be blank.'),
        ),
    )
    def test_create__predicate_type_number_invalid_value__validation_error(
        self,
        mocker,
        value,
        api_client,
    ):
        # arrange
        value, error_message = value
        account = create_test_account(plan=BillingPlanType.UNLIMITED)
        user = create_test_user(account=account)
        condition_create_analysis_mock = mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        predicate_api_name = 'predicate-1'
        field_api_name = 'number-field-1'
        condition_data = {
            'order': 1,
            'action': ConditionAction.SKIP_TASK,
            'rules': [
                {
                    'predicates': [
                        {
                            'field_type': PredicateType.NUMBER,
                            'operator': PredicateOperator.EQUAL,
                            'api_name': predicate_api_name,
                            'field': field_api_name,
                            'value': value,
                        },
                    ],
                },
            ],
        }
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
                            'name': 'Price',
                            'type': FieldType.NUMBER,
                            'api_name': field_api_name,
                        },
                    ],
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'Step 1',
                        'conditions': [condition_data],
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
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == error_message
        assert response.data['details']['api_name'] == predicate_api_name
        assert response.data['details']['reason'] == error_message
        assert 'name' not in response.data['details']
        condition_create_analysis_mock.assert_not_called()

    def test_create__cyclic_dependency__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        predicate_1_api_name = 'predicate-1'
        task_1_api_name = 'task-1'
        task_2_api_name = 'task-2'
        task_1_name = 'Task 1'
        condition_1_data = {
            'order': 1,
            'action': ConditionAction.START_TASK,
            'rules': [
                {
                    'predicates': [
                        {
                            'field_type': PredicateType.TASK,
                            'operator': PredicateOperator.COMPLETED,
                            'api_name': task_2_api_name,
                            'field': task_1_api_name,
                            'value': None,
                        },
                    ],
                },
            ],
        }
        condition_2_data = {
            'order': 1,
            'action': ConditionAction.START_TASK,
            'rules': [
                {
                    'predicates': [
                        {
                            'field_type': PredicateType.TASK,
                            'operator': PredicateOperator.COMPLETED,
                            'api_name': predicate_1_api_name,
                            'field': task_1_api_name,
                            'value': None,
                        },
                    ],
                },
            ],
        }
        api_client.token_authenticate(owner)

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': owner.id,
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': task_1_name,
                        'api_name': task_1_api_name,
                        'conditions': [condition_1_data],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': owner.id,
                            },
                        ],
                    },
                    {
                        'number': 2,
                        'name': 'Step 2',
                        'api_name': task_2_api_name,
                        'conditions': [condition_2_data],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': owner.id,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 400
        error_message = messages.MSG_PT_0065(name=task_1_name)
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == error_message

    def test_create__start_task__points_to_not_existent_task__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        predicate_1_api_name = 'predicate-1'
        not_existent_api_name = 'not-existent'
        task_api_name = 'task-1'
        task_name = 'Task 1'
        condition_data = {
            'order': 1,
            'action': ConditionAction.START_TASK,
            'rules': [
                {
                    'predicates': [
                        {
                            'field_type': PredicateType.TASK,
                            'operator': PredicateOperator.COMPLETED,
                            'api_name': predicate_1_api_name,
                            'field': not_existent_api_name,
                            'value': None,
                        },
                    ],
                },
            ],
        }
        api_client.token_authenticate(owner)

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': owner.id,
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': task_name,
                        'api_name': task_api_name,
                        'conditions': [condition_data],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': owner.id,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 400
        error_message = messages.MSG_PT_0066(name=task_name)
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['details']['reason'] == error_message
        assert response.data['details']['api_name'] == predicate_1_api_name
        assert response.data['message'] == error_message

    def test_create__skip_task__points_to_not_existent_task__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        predicate_1_api_name = 'predicate-1'
        not_existent_api_name = 'not-existent'
        task_api_name = 'task-1'
        task_name = 'Task 1'
        condition_data = {
            'order': 1,
            'action': ConditionAction.SKIP_TASK,
            'rules': [
                {
                    'predicates': [
                        {
                            'field_type': PredicateType.TASK,
                            'operator': PredicateOperator.COMPLETED,
                            'api_name': predicate_1_api_name,
                            'field': not_existent_api_name,
                            'value': None,
                        },
                    ],
                },
            ],
        }
        api_client.token_authenticate(owner)

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': owner.id,
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': task_name,
                        'api_name': task_api_name,
                        'conditions': [condition_data],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': owner.id,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 400
        error_message = messages.MSG_PT_0067(name=task_name)
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['details']['reason'] == error_message
        assert response.data['details']['api_name'] == predicate_1_api_name
        assert response.data['message'] == error_message

    def test_create__skip_task_points_to_not_ancestor_task__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        predicate_1_api_name = 'predicate-1'
        task_api_name = 'task-1'
        task_2_api_name = 'task-2'
        task_name = 'Task 1'
        condition_data = {
            'order': 1,
            'action': ConditionAction.SKIP_TASK,
            'rules': [
                {
                    'predicates': [
                        {
                            'field_type': PredicateType.TASK,
                            'operator': PredicateOperator.COMPLETED,
                            'api_name': predicate_1_api_name,
                            'field': task_api_name,
                            'value': None,
                        },
                    ],
                },
            ],
        }
        api_client.token_authenticate(owner)

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': owner.id,
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': 'Task 1',
                        'api_name': task_api_name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': owner.id,
                            },
                        ],
                    },
                    {
                        'number': 2,
                        'name': task_name,
                        'api_name': task_2_api_name,
                        'conditions': [condition_data],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': owner.id,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 400
        error_message = messages.MSG_PT_0068(name=task_name)
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['details']['reason'] == error_message
        assert response.data['details']['api_name'] == predicate_1_api_name
        assert response.data['message'] == error_message
