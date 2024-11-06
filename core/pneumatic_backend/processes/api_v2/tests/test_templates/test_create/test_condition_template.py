import pytest

from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.messages import template as messages
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    PredicateOperator,
    FieldType,
    PredicateType,
)
from pneumatic_backend.processes.models import Template, ConditionTemplate
from pneumatic_backend.authentication.enums import AuthTokenType


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
        condition_create_analytics_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.serializers.template.'
            'condition.AnalyticService.templates_task_condition_created'
        )
        user = create_test_user()
        account = user.account
        account.billing_plan = BillingPlanType.PREMIUM
        account.save()
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'template_owners': [user.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                            'is_required': True,
                        }
                    ]
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
                                'source_id': user.id
                            }
                        ]
                    },
                ]
            }
        )

        # assert
        message = 'Conditions: this field may not be null.'
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['api_name'] == 'task-55'
        assert response.data['details']['reason'] == message
        assert 'name' not in response.data['details']
        condition_create_analytics_mock.assert_not_called()

    def test_create__conditions_in_second_task_is_null__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        condition_create_analytics_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.serializers.template.'
            'condition.AnalyticService.templates_task_condition_created'
        )
        user = create_test_user()
        account = user.account
        account.billing_plan = BillingPlanType.PREMIUM
        account.save()
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'template_owners': [user.id],
                'kickoff': {},
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'api_name': 'task-54',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ]
                    },
                    {
                        'number': 2,
                        'name': 'Second step',
                        'api_name': 'task-55',
                        'conditions': None,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ]
                    },
                ]
            }
        )

        # assert
        message = 'Conditions: this field may not be null.'
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['api_name'] == 'task-55'
        assert response.data['details']['reason'] == message
        assert 'name' not in response.data['details']
        condition_create_analytics_mock.assert_not_called()

    def test_create__conditions_second_is_null__validation_error(
        self,
        mocker,
        api_client,
    ):

        # arrange
        condition_create_analytics_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.serializers.template.'
            'condition.AnalyticService.templates_task_condition_created'
        )
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        api_client.token_authenticate(user)
        conditions = [
            {
                'order': 1,
                'action': 'skip_task',
                'rules': [
                    {
                        'predicates': [
                            {
                                'field': 'user-field-1',
                                'field_type': PredicateType.USER,
                                'operator': PredicateOperator.EQUAL,
                                'value': user.id,
                            }
                        ]
                    }
                ]
            },
            None
        ]

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'template_owners': [user.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                            'is_required': True,
                        }
                    ]
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'api_name': 'task-66',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                        'conditions': conditions
                    }
                ]
            }
        )

        # assert
        message = 'Conditions: this field may not be null.'
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['api_name'] == 'task-66'
        assert response.data['details']['reason'] == message
        assert 'name' not in response.data['details']
        condition_create_analytics_mock.assert_not_called()

    def test_create__conditions_two_errors__validation_error(
        self,
        mocker,
        api_client,
    ):

        # arrange
        condition_create_analytics_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.serializers.template.'
            'condition.AnalyticService.templates_task_condition_created'
        )
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        api_client.token_authenticate(user)
        conditions = [
            {
                'order': 1,
                'action': 'skip_task',
                'rules': None
            },
            None
        ]

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'template_owners': [user.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                            'is_required': True,
                        }
                    ]
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'api_name': 'task-66',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                        'conditions': conditions
                    }
                ]
            }
        )

        # assert
        message = {
            'Conditions: this field may not be null.',
            'Rules: this field may not be null.'
        }
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] in message
        assert response.data['details']['api_name'] == 'task-66'
        assert response.data['details']['reason'] in message
        assert 'name' not in response.data['details']
        condition_create_analytics_mock.assert_not_called()

    def test_create__conditions_is_string__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        condition_create_analytics_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.serializers.template.'
            'condition.AnalyticService.templates_task_condition_created'
        )
        user = create_test_user()
        account = user.account
        account.billing_plan = BillingPlanType.PREMIUM
        account.save()
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'template_owners': [user.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                            'is_required': True,
                        }
                    ]
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
                                'source_id': user.id
                            }
                        ],
                    },
                ]
            }
        )

        # assert
        message = 'Conditions: expected a list of items but got type "str".'
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['api_name'] == 'task-55'
        assert response.data['details']['reason'] == message
        assert 'name' not in response.data['details']
        condition_create_analytics_mock.assert_not_called()

    def test_create__conditions_is_integer__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        condition_create_analytics_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.serializers.template.'
            'condition.AnalyticService.templates_task_condition_created'
        )
        user = create_test_user()
        account = user.account
        account.billing_plan = BillingPlanType.PREMIUM
        account.save()
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'template_owners': [user.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                            'is_required': True,
                        }
                    ]
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
                                'source_id': user.id
                            }
                        ],
                    },
                ]
            }
        )

        # assert
        message = 'Conditions: expected a list of items but got type "int".'
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['api_name'] == 'task-55'
        assert response.data['details']['reason'] == message
        assert 'name' not in response.data['details']
        condition_create_analytics_mock.assert_not_called()

    def test_create__without_rules__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        condition_create_analytics_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.serializers.template.'
            'condition.AnalyticService.templates_task_condition_created'
        )
        user = create_test_user()
        account = user.account
        account.billing_plan = BillingPlanType.PREMIUM
        account.save()
        api_client.token_authenticate(user)
        request_data = {
            'api_name': 'condition-66',
            'rules': [],
            'order': 1,
            'action': 'skip_task',
        }

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'template_owners': [user.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                            'is_required': True,
                        }
                    ]
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
                                'source_id': user.id
                            }
                        ],
                    },
                ]
            }
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == 'Rules: this list may not be empty.'
        assert response.data['details']['api_name'] == 'condition-66'
        assert 'name' not in response.data['details']
        condition_create_analytics_mock.assert_not_called()

    def test_create__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        condition_create_analytics_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.serializers.template.'
            'condition.AnalyticService.templates_task_condition_created'
        )
        user = create_test_user()
        account = user.account
        account.billing_plan = BillingPlanType.PREMIUM
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
                        }
                    ]
                }
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
                'template_owners': [user.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                            'is_required': True,
                        }
                    ]
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'conditions': [request_data],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                    },
                ]
            }
        )

        # assert
        assert response.status_code == 200
        condition_data = response.data['tasks'][0]['conditions'][0]
        assert condition_data['api_name']
        assert condition_data['rules'][0]['api_name']
        assert condition_data['rules'][0]['predicates'][0]['api_name']

        template = Template.objects.get(id=response.data['id'])
        condition = ConditionTemplate.objects.get(
            api_name=condition_data['api_name']
        )
        condition_create_analytics_mock.assert_called_once_with(
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
            (PredicateOperator.COMPLETED, PredicateType.TASK),
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
            'pneumatic_backend.processes.api_v2.serializers.template.'
            'condition.AnalyticService.templates_task_condition_created'
        )
        user = create_test_user()
        account = user.account
        account.billing_plan = BillingPlanType.PREMIUM
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
                        }
                    ]
                }
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
                'template_owners': [user.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                            'is_required': True,
                        }
                    ]
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'conditions': [request_data],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                    },
                ]
            }
        )

        # assert
        assert response.status_code == 200
        condition = response.data['tasks'][0]['conditions'][0]
        assert condition['api_name']
        assert condition['rules'][0]['api_name']
        assert condition['rules'][0]['predicates'][0]['api_name']

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
        condition_create_analytics_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.serializers.template.'
            'condition.AnalyticService.templates_task_condition_created'
        )
        user = create_test_user()
        account = user.account
        account.billing_plan = BillingPlanType.PREMIUM
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
                        }
                    ]
                }
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
                'template_owners': [user.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                            'is_required': True,
                        }
                    ]
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': task_name,
                        'conditions': [request_data],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                    },
                ]
            }
        )

        # assert
        assert response.status_code == 400
        message = messages.MSG_PT_0043(task=task_name, user_id=value)
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['api_name'] == api_name
        assert response.data['details']['reason'] == message
        condition_create_analytics_mock.assert_not_called()

    @pytest.mark.parametrize(
        ('field_type', 'value'),
        [
            (FieldType.RADIO, '123'),
            (FieldType.DROPDOWN, '123'),
            (FieldType.CHECKBOX, '123'),
            (FieldType.RADIO, 'disallowed-api-name'),
            (FieldType.DROPDOWN, 'disallowed-api-name'),
            (FieldType.CHECKBOX, 'disallowed-api-name'),
        ]
    )
    def test_create__selection_field_incorrect_value__validation_error(
        self,
        mocker,
        api_client,
        field_type,
        value,
    ):
        # arrange
        condition_create_analytics_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.serializers.template.'
            'condition.AnalyticService.templates_task_condition_created'
        )
        field = 'selection-field-1'
        user = create_test_user()
        account = user.account
        account.billing_plan = BillingPlanType.PREMIUM
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
                            'api_name': predicate_api_name
                        }
                    ]
                }
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
                'template_owners': [user.id],
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
                            ]
                        }
                    ]
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': task_name,
                        'conditions': [request_data],
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
        assert response.status_code == 400
        message = messages.MSG_PT_0045(
            task=task_name,
            selection_api_name=value
        )
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['api_name'] == predicate_api_name
        assert response.data['details']['reason'] == message
        condition_create_analytics_mock.assert_not_called()

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
        ]
    )
    def test_create__disallowed_operator__validation_error(
        self,
        mocker,
        api_client,
        field_type,
        operator,
    ):
        # arrange
        condition_create_analytics_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.serializers.template.'
            'condition.AnalyticService.templates_task_condition_created'
        )
        field = 'selection-field-1'
        user = create_test_user()
        account = user.account
        account.billing_plan = BillingPlanType.PREMIUM
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
                        }
                    ]
                }
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
                'template_owners': [user.id],
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
                            ]
                        }
                    ]
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': task_name,
                        'conditions': [request_data],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                    },
                ]
            }
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
        condition_create_analytics_mock.assert_not_called()

    def test_create__not_subscribed__validation_error(
        self,
        mocker,
        api_client
    ):
        # arrange
        condition_create_analytics_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.serializers.template.'
            'condition.AnalyticService.templates_task_condition_created'
        )
        user = create_test_user()
        api_client.token_authenticate(user)
        api_name = 'cond-api-name'
        request_data = {
            'rules': [
                {
                    'predicates': [
                        {
                            'field': 'user-field-1',
                            'field_type': PredicateType.USER,
                            'operator': PredicateOperator.EQUAL,
                            'value': user.id,
                        }
                    ]
                }
            ],
            'order': 1,
            'action': 'skip_task',
            'api_name': api_name,
        }

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'template_owners': [user.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                            'is_required': True,
                        }
                    ]
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'conditions': [request_data],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                    },
                ]
            }
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == messages.MSG_PT_0042
        condition_create_analytics_mock.assert_not_called()

    def test_create__with_non_existing_field__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        condition_create_analytics_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.serializers.template.'
            'condition.AnalyticService.templates_task_condition_created'
        )
        user = create_test_user()
        account = user.account
        account.billing_plan = BillingPlanType.PREMIUM
        account.save()
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
                        }
                    ]
                }
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
                'template_owners': [user.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                            'is_required': True,
                        }
                    ]
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'conditions': [request_data],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                    },
                ]
            }
        )

        # assert
        assert response.status_code == 400
        condition_create_analytics_mock.assert_not_called()

    def test_create__conditions_with_equal_api_names__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        mocker.patch(
            'pneumatic_backend.processes.api_v2.serializers.template.'
            'condition.AnalyticService.templates_task_condition_created'
        )
        step = 'First step'
        condition_api_name = 'cond-1'
        user = create_test_user()
        account = user.account
        account.billing_plan = BillingPlanType.PREMIUM
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
                        }
                    ]
                }
            ],
            'order': 1,
            'action': 'skip_task',
            'api_name': condition_api_name
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
                        }
                    ]
                }
            ],
            'order': 1,
            'action': 'skip_task',
            'api_name': condition_api_name
        }

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'template_owners': [user.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                            'is_required': True,
                        }
                    ]
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'conditions': [condition_1],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                    },
                    {
                        'number': 2,
                        'name': step,
                        'conditions': [condition_2],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                    },
                ]
            }
        )

        # assert
        assert response.status_code == 400
        message = messages.MSG_PT_0049(
            step_name=step,
            api_name=condition_api_name
        )
        assert response.data['message'] == message
        assert response.data['details']['reason'] == message
        assert response.data['details']['api_name'] == condition_api_name

    def test_create__rules_with_equal_api_names__rename_create(
        self,
        mocker,
        api_client,
    ):
        # arrange
        mocker.patch(
            'pneumatic_backend.processes.api_v2.serializers.template.'
            'condition.AnalyticService.templates_task_condition_created'
        )
        rule_api_name = 'rule-1'
        step = 'First step'
        user = create_test_user()
        account = user.account
        account.billing_plan = BillingPlanType.PREMIUM
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
                        }
                    ],
                    'api_name': rule_api_name
                }
            ],
            'order': 1,
            'action': 'skip_task',
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
                        }
                    ],
                    'api_name': rule_api_name
                }
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
                'template_owners': [user.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                            'is_required': True,
                        }
                    ]
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'conditions': [condition_1],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                    },
                    {
                        'number': 2,
                        'name': 'First step',
                        'conditions': [condition_2],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                    },
                ]
            }
        )

        # assert
        assert response.status_code == 400
        message = messages.MSG_PT_0053(
            step_name=step,
            api_name=rule_api_name
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
            'pneumatic_backend.processes.api_v2.serializers.template.'
            'condition.AnalyticService.templates_task_condition_created'
        )
        predicate_api_name = 'predicate-1'
        step = 'First step'
        user = create_test_user()
        account = user.account
        account.billing_plan = BillingPlanType.PREMIUM
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
                        }
                    ]
                }
            ],
            'order': 1,
            'action': 'skip_task',
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
                        }
                    ]
                }
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
                'template_owners': [user.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                            'is_required': True,
                        }
                    ]
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'conditions': [condition_1],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                    },
                    {
                        'number': 2,
                        'name': step,
                        'conditions': [condition_2],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ],
                    },
                ]
            }
        )

        # assert
        assert response.status_code == 400
        message = messages.MSG_PT_0051(
            step_name=step,
            api_name=predicate_api_name
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
            'pneumatic_backend.processes.api_v2.serializers.template.'
            'condition.AnalyticService.templates_task_condition_created'
        )
        predicate_api_name = 'predicate-1'
        condition_data = {
            'order': 1,
            'action': 'skip_task',
            'rules': [
                {
                    'predicates': [
                        {
                            'field_type': PredicateType.KICKOFF,
                            'operator': PredicateOperator.COMPLETED,
                            'api_name': predicate_api_name,
                            'field': None,
                            'value': None,
                        }
                    ]
                }
            ]
        }
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'template_owners': [user.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                            'is_required': True,
                        }
                    ]
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'Step 1',
                        'conditions': [condition_data],
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
            'pneumatic_backend.processes.api_v2.serializers.template.'
            'condition.AnalyticService.templates_task_condition_created'
        )
        predicate_api_name = 'predicate-1'
        task_api_name = 'task-1'
        condition_data = {
            'order': 1,
            'action': 'skip_task',
            'rules': [
                {
                    'predicates': [
                        {
                            'field_type': PredicateType.TASK,
                            'operator': PredicateOperator.COMPLETED,
                            'api_name': predicate_api_name,
                            'field': task_api_name,
                            'value': None,
                        }
                    ]
                }
            ]
        }
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': True,
                'template_owners': [user.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': 'user-field-1',
                            'is_required': True,
                        }
                    ]
                },
                'tasks': [
                    {
                        'number': 1,
                        'name': 'Step 1',
                        'api_name': task_api_name,
                        'conditions': [condition_data],
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
        condition = response.data['tasks'][0]['conditions'][0]
        predicate = condition['rules'][0]['predicates'][0]
        assert predicate['field_type'] == PredicateType.TASK
        assert predicate['api_name'] == predicate_api_name
        assert predicate['operator'] == PredicateOperator.COMPLETED
        assert predicate['value'] is None
        assert predicate['field'] == task_api_name
