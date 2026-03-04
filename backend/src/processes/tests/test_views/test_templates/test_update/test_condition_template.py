import pytest

from src.accounts.enums import BillingPlanType
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
    RuleTemplate,
)
from src.processes.models.templates.fields import (
    FieldTemplate,
)
from src.processes.models.templates.template import Template
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_owner,
    create_test_template,
    create_test_user,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


class TestUpdateConditionTemplate:

    def test_update__delete_all_rules__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
        )
        kickoff = template.kickoff_instance
        field = FieldTemplate.objects.create(
            name='Name',
            api_name='name',
            type=FieldType.USER,
            kickoff=kickoff,
            is_required=True,
            template=template,
            account=user.account,
        )
        first_task = template.tasks.order_by('number').first()
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=first_task,
            template=template,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        PredicateTemplate.objects.create(
            rule=rule,
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
        )
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        request_data = {
            'api_name': condition.api_name,
            'rules': [],
            'order': 1,
            'action': 'skip_task',
        }

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'id': field.id,
                            'order': field.order,
                            'name': field.name,
                            'type': field.type,
                            'api_name': field.api_name,
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': first_task.id,
                        'api_name': first_task.api_name,
                        'number': first_task.number,
                        'name': first_task.name,
                        'conditions': [request_data],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                            },
                        ],
                    },
                ],
                'is_active': True,
            },
        )

        # assert
        message = 'Rules: this list may not be empty.'
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['api_name'] == condition.api_name
        assert response.data['details']['reason'] == message
        assert 'name' not in response.data['details']

    def test_update__delete_one_rule_of_two__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
        )
        kickoff = template.kickoff_instance
        field = FieldTemplate.objects.create(
            name='Name',
            api_name='name',
            type=FieldType.USER,
            kickoff=kickoff,
            is_required=True,
            template=template,
            account=user.account,
        )
        first_task = template.tasks.order_by('number').first()
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=first_task,
            template=template,
        )
        first_rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        PredicateTemplate.objects.create(
            rule=first_rule,
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
        )
        second_rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        second_predicate = PredicateTemplate.objects.create(
            rule=second_rule,
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
        )
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        request_data = {
            'api_name': condition.api_name,
            'order': 1,
            'action': 'skip_task',
            'rules': [
                {
                    'api_name': second_rule.api_name,
                    'predicates': [
                        {
                            'api_name': second_predicate.api_name,
                            'field_type': second_predicate.field_type,
                            'field': second_predicate.field,
                            'operator': second_predicate.operator,
                        },
                    ],
                },
            ],
        }

        # act
        response = api_client.put(
            path=f'/templates/{template.id}',
            data={
                'id': template.id,
                'name': template.name,
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': user.id,
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'id': field.id,
                            'order': field.order,
                            'name': field.name,
                            'type': field.type,
                            'api_name': field.api_name,
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': first_task.id,
                        'number': first_task.number,
                        'name': first_task.name,
                        'api_name': first_task.api_name,
                        'conditions': [request_data],
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                            },
                        ],
                    },
                ],
                'is_active': True,
            },
        )

        # assert
        assert response.status_code == 200
        assert RuleTemplate.objects.count() == 1
        assert PredicateTemplate.objects.count() == 1

    def test_update__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        api_client.token_authenticate(user)

        template = create_test_template(user, is_active=True)
        field = FieldTemplate.objects.create(
            name='Name',
            api_name='name',
            type=FieldType.USER,
            kickoff=template.kickoff_instance,
            is_required=True,
            template=template,
            account=user.account,
        )
        first_task = template.tasks.order_by('number').first()
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=first_task,
            template=template,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        predicate = PredicateTemplate.objects.create(
            rule=rule,
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
        )
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        request_data = {
            'api_name': condition.api_name,
            'order': condition.order,
            'action': ConditionAction.END_WORKFLOW,
            'rules': [
                {
                    'api_name': rule.api_name,
                    'predicates': [
                        {
                            'api_name': predicate.api_name,
                            'field': predicate.field,
                            'field_type': predicate.field_type,
                            'operator': predicate.operator,
                        },
                    ],
                },
            ],
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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'id': field.id,
                            'order': field.order,
                            'name': field.name,
                            'type': field.type,
                            'api_name': field.api_name,
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': first_task.id,
                        'number': first_task.number,
                        'name': first_task.name,
                        'api_name': first_task.api_name,
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
        condition.refresh_from_db()
        assert condition.action == ConditionAction.END_WORKFLOW

    def test_update__predicate_to_type_kickoff_completed__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account(plan=BillingPlanType.UNLIMITED)
        user = create_test_user(account=account)
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        template = create_test_template(
            user=user,
            tasks_count=3,
            is_active=True,
        )
        first_task = template.tasks.order_by('number').first()
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=first_task,
            template=template,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        predicate = PredicateTemplate.objects.create(
            rule=rule,
            operator=PredicateOperator.COMPLETED,
            field_type=PredicateType.TASK,
            field=None,
            value=None,
            template=template,
        )

        request_data = {
            'api_name': condition.api_name,
            'order': condition.order,
            'action': ConditionAction.END_WORKFLOW,
            'rules': [
                {
                    'api_name': rule.api_name,
                    'predicates': [
                        {
                            'api_name': predicate.api_name,
                            'field_type': PredicateType.KICKOFF,
                            'operator': PredicateOperator.COMPLETED,
                            'field': None,
                            'value': None,
                        },
                    ],
                },
            ],
        }
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
                    },
                ],
                'kickoff': {'id': template.kickoff_instance.id},
                'tasks': [
                    {
                        'id': first_task.id,
                        'number': first_task.number,
                        'name': first_task.name,
                        'api_name': first_task.api_name,
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
        assert predicate_data['field_type'] == PredicateType.KICKOFF
        assert predicate_data['api_name'] == predicate.api_name
        assert predicate_data['operator'] == PredicateOperator.COMPLETED
        assert predicate_data['value'] is None
        assert predicate_data['field'] is None

        predicate.refresh_from_db()
        assert predicate.field_type == PredicateType.KICKOFF
        assert predicate.operator == PredicateOperator.COMPLETED

    def test_update__predicate_to_type_number__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        template = create_test_template(
            user=user,
            tasks_count=3,
            is_active=True,
        )
        first_task = template.tasks.order_by('number').first()
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=first_task,
            template=template,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        predicate_api_name = 'predicate-1'
        predicate = PredicateTemplate.objects.create(
            rule=rule,
            field_type=PredicateType.KICKOFF,
            operator=PredicateOperator.COMPLETED,
            field=None,
            template=template,
            api_name=predicate_api_name,
        )
        field_api_name = 'number-field-1'
        value = '31.6'
        request_data = {
            'api_name': condition.api_name,
            'order': condition.order,
            'action': ConditionAction.END_WORKFLOW,
            'rules': [
                {
                    'api_name': rule.api_name,
                    'predicates': [
                        {
                            'api_name': predicate_api_name,
                            'field_type': PredicateType.NUMBER,
                            'operator': PredicateOperator.EQUAL,
                            'field': field_api_name,
                            'value': value,
                        },
                    ],
                },
            ],
        }
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
                        'id': first_task.id,
                        'number': first_task.number,
                        'name': first_task.name,
                        'api_name': first_task.api_name,
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
        assert predicate_data['field_type'] == PredicateType.NUMBER
        assert predicate_data['api_name'] == predicate_api_name
        assert predicate_data['operator'] == PredicateOperator.EQUAL
        assert predicate_data['value'] == value
        assert predicate_data['field'] == field_api_name

        predicate.refresh_from_db()
        assert predicate.field_type == PredicateType.NUMBER
        assert predicate.operator == PredicateOperator.EQUAL
        assert predicate.field == field_api_name
        assert predicate.value == value

    def test_update__replace_existing_predicate__create_new_predicate(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        api_client.token_authenticate(user)

        template = create_test_template(user, is_active=True)
        field = FieldTemplate.objects.create(
            name='Name',
            api_name='name',
            type=FieldType.USER,
            kickoff=template.kickoff_instance,
            is_required=True,
            template=template,
            account=user.account,
        )
        first_task = template.tasks.order_by('number').first()
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=first_task,
            template=template,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        predicate = PredicateTemplate.objects.create(
            rule=rule,
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
        )
        second_predicate = PredicateTemplate.objects.create(
            rule=rule,
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
        )
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        request_data = {
            'api_name': condition.api_name,
            'order': condition.order,
            'action': ConditionAction.END_WORKFLOW,
            'rules': [
                {
                    'api_name': rule.api_name,
                    'predicates': [
                        {
                            'api_name': predicate.api_name,
                            'field': predicate.field,
                            'field_type': predicate.field_type,
                            'operator': predicate.operator,
                        },
                    ],
                },
                {
                    'predicates': [
                        {
                            'api_name': second_predicate.api_name,
                            'field': second_predicate.field,
                            'field_type': second_predicate.field_type,
                            'operator': second_predicate.operator,
                        },
                    ],
                },
            ],
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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'id': field.id,
                            'order': field.order,
                            'name': field.name,
                            'type': field.type,
                            'api_name': field.api_name,
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': first_task.id,
                        'number': first_task.number,
                        'name': first_task.name,
                        'api_name': first_task.api_name,
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
        condition.refresh_from_db()
        assert condition.action == ConditionAction.END_WORKFLOW
        second_predicate = PredicateTemplate.objects.filter(
            id=second_predicate.id,
        )
        assert second_predicate.exists() is False
        assert condition.rules.last().predicates.exists()

    @pytest.mark.parametrize(
        'data',
        (
            (PredicateOperator.EXIST, PredicateType.USER),
            (PredicateOperator.NOT_EXIST, PredicateType.USER),
        ),
    )
    def test_update__unary_operator_with_none_value__ok(
        self,
        mocker,
        api_client,
        data,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        api_client.token_authenticate(user)

        template = create_test_template(user, is_active=True)
        field = FieldTemplate.objects.create(
            name='Name',
            api_name='name',
            type=FieldType.USER,
            kickoff=template.kickoff_instance,
            is_required=True,
            template=template,
            account=user.account,
        )
        first_task = template.tasks.order_by('number').first()
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=first_task,
            template=template,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        predicate = PredicateTemplate.objects.create(
            rule=rule,
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
        )
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        request_data = {
            'api_name': condition.api_name,
            'order': condition.order,
            'action': ConditionAction.END_WORKFLOW,
            'rules': [
                {
                    'api_name': rule.api_name,
                    'predicates': [
                        {
                            'field': predicate.field,
                            'api_name': predicate.api_name,
                            'field_type': data[1],
                            'operator': data[0],
                        },
                    ],
                },
            ],
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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'id': field.id,
                            'order': field.order,
                            'name': field.name,
                            'type': field.type,
                            'api_name': field.api_name,
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': first_task.id,
                        'number': first_task.number,
                        'name': first_task.name,
                        'api_name': first_task.api_name,
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
        condition.refresh_from_db()
        assert condition.action == ConditionAction.END_WORKFLOW

    @pytest.mark.parametrize(
        'value',
        ['123', 'not integer'],
    )
    def test_update__user_field_incorrect_value__validation_error(
        self,
        mocker,
        api_client,
        value,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        api_client.token_authenticate(user)

        template = create_test_template(user, is_active=True)

        field = FieldTemplate.objects.create(
            name='Name',
            api_name='name',
            type=FieldType.STRING,
            kickoff=template.kickoff_instance,
            template=template,
            account=user.account,
        )
        first_task = template.tasks.order_by('number').first()
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=first_task,
            template=template,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        predicate = PredicateTemplate.objects.create(
            rule=rule,
            operator=PredicateOperator.EQUAL,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
        )
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        request_data = {
            'api_name': condition.api_name,
            'order': condition.order,
            'action': ConditionAction.END_WORKFLOW,
            'rules': [
                {
                    'api_name': rule.api_name,
                    'predicates': [
                        {
                            'api_name': predicate.api_name,
                            'field': predicate.field,
                            'field_type': predicate.field_type,
                            'operator': predicate.operator,
                            'value': value,
                        },
                    ],
                },
            ],
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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'id': field.id,
                            'order': field.order,
                            'name': field.name,
                            'type': field.type,
                            'api_name': field.api_name,
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': first_task.id,
                        'number': first_task.number,
                        'name': first_task.name,
                        'api_name': first_task.api_name,
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
        message = messages.MSG_PT_0043(task=first_task.name, user_id=value)
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['api_name'] == predicate.api_name
        assert response.data['details']['reason'] == message

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
    def test_update__selection_field_incorrect_value__validation_error(
        self,
        mocker,
        api_client,
        field_type,
        value,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        api_client.token_authenticate(user)

        template = create_test_template(user, is_active=True)
        field = FieldTemplate.objects.create(
            name='Name',
            api_name='name',
            type=FieldType.STRING,
            kickoff=template.kickoff_instance,
            template=template,
            account=user.account,
        )
        first_task = template.tasks.order_by('number').first()
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=first_task,
            template=template,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        predicate = PredicateTemplate.objects.create(
            rule=rule,
            operator=PredicateOperator.EQUAL,
            field_type=PredicateType.USER,
            field=field.api_name,
            value=user.id,
            template=template,
        )
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        request_data = {
            'api_name': condition.api_name,
            'rules': [
                {
                    'api_name': rule.api_name,
                    'predicates': [
                        {
                            'api_name': predicate.api_name,
                            'field': predicate.field,
                            'field_type': field_type,
                            'operator': predicate.operator,
                            'value': value,
                        },
                    ],
                },
            ],
            'order': condition.order,
            'action': ConditionAction.END_WORKFLOW,
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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'id': field.id,
                            'order': field.order,
                            'name': field.name,
                            'type': field.type,
                            'api_name': field.api_name,
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': first_task.id,
                        'number': first_task.number,
                        'name': first_task.name,
                        'api_name': first_task.api_name,
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
            task=first_task.name,
            selection_api_name=value,
        )
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['api_name'] == predicate.api_name
        assert response.data['details']['reason'] == message

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
    def test_update__disallowed_operator__validation_error(
        self,
        mocker,
        api_client,
        field_type,
        operator,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        api_client.token_authenticate(user)

        template = create_test_template(user, is_active=True)
        field = FieldTemplate.objects.create(
            name='Name',
            api_name='name',
            type=FieldType.STRING,
            kickoff=template.kickoff_instance,
            template=template,
            account=user.account,
        )
        first_task = template.tasks.order_by('number').first()
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=first_task,
            template=template,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        predicate = PredicateTemplate.objects.create(
            rule=rule,
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
        )
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        request_data = {
            'api_name': condition.api_name,
            'rules': [
                {
                    'api_name': rule.api_name,
                    'predicates': [
                        {
                            'api_name': predicate.api_name,
                            'field': predicate.field,
                            'field_type': field_type,
                            'operator': operator,
                            'value': 1,
                        },
                    ],
                },
            ],
            'order': condition.order,
            'action': ConditionAction.END_WORKFLOW,
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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'id': field.id,
                            'order': field.order,
                            'name': field.name,
                            'type': field.type,
                            'api_name': field.api_name,
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': first_task.id,
                        'number': first_task.number,
                        'name': first_task.name,
                        'api_name': first_task.api_name,
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
            task=first_task.name,
        )
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['api_name'] == predicate.api_name
        assert response.data['details']['reason'] == message

    def test_update__change_condition_api_name__create_new(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=2,
            is_active=True,
        )
        kickoff = template.kickoff_instance
        field = FieldTemplate.objects.create(
            name='Name',
            api_name='name',
            type=FieldType.USER,
            kickoff=kickoff,
            is_required=True,
            template=template,
            account=user.account,
        )
        task = template.tasks.first()
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=task,
            template=template,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        predicate = PredicateTemplate.objects.create(
            rule=rule,
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
        )
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        new_api_name = 'new-api-name'

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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'id': field.id,
                            'order': field.order,
                            'name': field.name,
                            'type': field.type,
                            'api_name': field.api_name,
                            'is_required': field.is_required,
                        },
                    ],
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
                                'source_id': user.id,
                            },
                        ],
                        'conditions': [
                            {
                                'order': 1,
                                'api_name': new_api_name,
                                'action': condition.action,
                                'rules': [
                                    {
                                        'api_name': rule.api_name,
                                        'predicates': [
                                            {
                                                'api_name': predicate.api_name,
                                                'field': predicate.field,
                                                'field_type': (
                                                    predicate.field_type
                                                ),
                                                'operator': predicate.operator,
                                            },
                                        ],
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        assert not ConditionTemplate.objects.filter(id=condition.id).exists()
        assert task.conditions.all().count() == 1
        new_condition = task.conditions.get(
            template=template,
            action=condition.action,
            api_name=new_api_name,
            order=condition.order,
        )

        assert not RuleTemplate.objects.filter(id=rule.id).exists()
        assert new_condition.rules.all().count() == 1
        new_rule = new_condition.rules.get(
            template=template,
            api_name=rule.api_name,
        )

        assert not PredicateTemplate.objects.filter(id=predicate.id).exists()
        assert new_rule.predicates.all().count() == 1
        assert new_rule.predicates.get(
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
            api_name=predicate.api_name,
        )

    def test_update__unspecified_condition_api_name__create_new(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=2,
            is_active=True,
        )
        kickoff = template.kickoff_instance
        field = FieldTemplate.objects.create(
            name='Name',
            api_name='name',
            type=FieldType.USER,
            kickoff=kickoff,
            is_required=True,
            template=template,
            account=user.account,
        )
        task = template.tasks.first()
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=task,
            template=template,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        predicate = PredicateTemplate.objects.create(
            rule=rule,
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
        )
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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'id': field.id,
                            'order': field.order,
                            'name': field.name,
                            'type': field.type,
                            'api_name': field.api_name,
                            'is_required': field.is_required,
                        },
                    ],
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
                                'source_id': user.id,
                            },
                        ],
                        'conditions': [
                            {
                                'order': condition.order,
                                'action': condition.action,
                                'rules': [
                                    {
                                        'api_name': rule.api_name,
                                        'predicates': [
                                            {
                                                'api_name': predicate.api_name,
                                                'field': predicate.field,
                                                'field_type': (
                                                    predicate.field_type
                                                ),
                                                'operator': predicate.operator,
                                            },
                                        ],
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        assert not ConditionTemplate.objects.filter(id=condition.id).exists()
        assert task.conditions.all().count() == 1
        new_condition = task.conditions.get(
            task=task,
            template=template,
            action=ConditionAction.SKIP_TASK,
        )
        assert new_condition.api_name

        assert not RuleTemplate.objects.filter(id=rule.id).exists()
        assert new_condition.rules.all().count() == 1
        new_rule = new_condition.rules.get(
            template=template,
            api_name=rule.api_name,
        )

        assert not PredicateTemplate.objects.filter(id=predicate.id).exists()
        assert new_rule.predicates.all().count() == 1
        assert new_rule.predicates.get(
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
            api_name=predicate.api_name,
        )

    def test_update__change_rule_api_name__create_new(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=2,
            is_active=True,
        )
        kickoff = template.kickoff_instance
        field = FieldTemplate.objects.create(
            name='Name',
            api_name='name',
            type=FieldType.USER,
            kickoff=kickoff,
            is_required=True,
            template=template,
            account=user.account,
        )
        task = template.tasks.first()
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=task,
            template=template,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        predicate = PredicateTemplate.objects.create(
            rule=rule,
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
        )
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        new_api_name = 'new-api-name'

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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'id': field.id,
                            'order': field.order,
                            'name': field.name,
                            'type': field.type,
                            'api_name': field.api_name,
                            'is_required': field.is_required,
                        },
                    ],
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
                                'source_id': user.id,
                            },
                        ],
                        'conditions': [
                            {
                                'action': condition.action,
                                'api_name': condition.api_name,
                                'rules': [
                                    {
                                        'api_name': new_api_name,
                                        'predicates': [
                                            {
                                                'api_name': predicate.api_name,
                                                'field': predicate.field,
                                                'field_type': (
                                                    predicate.field_type
                                                ),
                                                'operator': predicate.operator,
                                            },
                                        ],
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        assert not RuleTemplate.objects.filter(id=rule.id).exists()
        assert condition.rules.all().count() == 1
        new_rule = condition.rules.get(
            template=template,
            api_name=new_api_name,
        )
        assert not PredicateTemplate.objects.filter(id=predicate.id).exists()
        assert new_rule.predicates.all().count() == 1
        assert new_rule.predicates.filter(
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
            api_name=predicate.api_name,
        )

    def test_update__unspecified_rule_api_name__create_new(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=2,
            is_active=True,
        )
        kickoff = template.kickoff_instance
        field = FieldTemplate.objects.create(
            name='Name',
            api_name='name',
            type=FieldType.USER,
            kickoff=kickoff,
            is_required=True,
            template=template,
            account=user.account,
        )
        task = template.tasks.first()
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=task,
            template=template,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        predicate = PredicateTemplate.objects.create(
            rule=rule,
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
        )
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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'id': field.id,
                            'order': field.order,
                            'name': field.name,
                            'type': field.type,
                            'api_name': field.api_name,
                            'is_required': field.is_required,
                        },
                    ],
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
                                'source_id': user.id,
                            },
                        ],
                        'conditions': [
                            {
                                'action': condition.action,
                                'api_name': condition.api_name,
                                'rules': [
                                    {
                                        'predicates': [
                                            {
                                                'api_name': predicate.api_name,
                                                'field': predicate.field,
                                                'field_type': (
                                                    predicate.field_type
                                                ),
                                                'operator': predicate.operator,
                                            },
                                        ],
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        assert not RuleTemplate.objects.filter(id=rule.id).exists()
        assert condition.rules.all().count() == 1
        new_rule = condition.rules.get(template=template)
        assert new_rule.api_name

        assert not PredicateTemplate.objects.filter(id=predicate.id).exists()
        assert new_rule.predicates.all().count() == 1
        assert new_rule.predicates.filter(
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
            api_name=predicate.api_name,
        )

    def test_update__change_predicate_api_name__create_new(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=2,
            is_active=True,
        )
        kickoff = template.kickoff_instance
        field = FieldTemplate.objects.create(
            name='Name',
            api_name='name',
            type=FieldType.USER,
            kickoff=kickoff,
            is_required=True,
            template=template,
            account=user.account,
        )
        task = template.tasks.first()
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=task,
            template=template,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        predicate = PredicateTemplate.objects.create(
            rule=rule,
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
        )
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        new_api_name = 'new-api-name'

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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'id': field.id,
                            'order': field.order,
                            'name': field.name,
                            'type': field.type,
                            'api_name': field.api_name,
                            'is_required': field.is_required,
                        },
                    ],
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
                                'source_id': user.id,
                            },
                        ],
                        'conditions': [
                            {
                                'api_name': condition.api_name,
                                'action': condition.action,
                                'rules': [
                                    {
                                        'api_name': rule.api_name,
                                        'predicates': [
                                            {
                                                'api_name': new_api_name,
                                                'field': predicate.field,
                                                'field_type': (
                                                    predicate.field_type
                                                ),
                                                'operator': predicate.operator,
                                            },
                                        ],
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        rule.refresh_from_db()
        assert not PredicateTemplate.objects.filter(id=predicate.id).exists()
        assert rule.predicates.all().count() == 1
        assert rule.predicates.get(
            api_name=new_api_name,
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
        )

    def test_update__unspecified_predicate_api_name__create_new(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            tasks_count=2,
            is_active=True,
        )
        kickoff = template.kickoff_instance
        field = FieldTemplate.objects.create(
            name='Name',
            api_name='name',
            type=FieldType.USER,
            kickoff=kickoff,
            is_required=True,
            template=template,
            account=user.account,
        )
        task = template.tasks.first()
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=task,
            template=template,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        predicate = PredicateTemplate.objects.create(
            rule=rule,
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
        )
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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'id': field.id,
                            'order': field.order,
                            'name': field.name,
                            'type': field.type,
                            'api_name': field.api_name,
                            'is_required': field.is_required,
                        },
                    ],
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
                                'source_id': user.id,
                            },
                        ],
                        'conditions': [
                            {
                                'api_name': condition.api_name,
                                'action': condition.action,
                                'rules': [
                                    {
                                        'api_name': rule.api_name,
                                        'predicates': [
                                            {
                                                'field': predicate.field,
                                                'field_type': (
                                                    predicate.field_type
                                                ),
                                                'operator': predicate.operator,
                                            },
                                        ],
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        rule.refresh_from_db()
        assert not PredicateTemplate.objects.filter(id=predicate.id).exists()
        assert rule.predicates.all().count() == 1
        assert rule.predicates.get(
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
        )

    def test_update__checklist_service__not_called(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        create_test_user(account=account, email='t@t.t')
        api_client.token_authenticate(user)
        request_data = {
            'rules': [
                {
                    'predicates': [
                        {
                            'field': 'user-field-1',
                            'field_type': 'user',
                            'operator': PredicateOperator.EXIST,
                        },
                    ],
                },
            ],
            'order': 1,
            'action': 'skip_task',
        }

        response_create = api_client.post(
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

        template = Template.objects.get(id=response_create.data['id'])
        kickoff = template.kickoff_instance
        task = template.tasks.first()
        field = kickoff.fields.first()
        condition = task.conditions.first()
        request_data = {
            'rules': [
                {
                    'predicates': [
                        {
                            'field': 'user-field-1',
                            'field_type': 'user',
                            'operator': PredicateOperator.EXIST,
                        },
                    ],
                },
            ],
            'api_name': condition.api_name,
            'order': 1,
            'action': 'skip_task',
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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'id': field.id,
                            'order': 1,
                            'name': 'First step performer',
                            'type': FieldType.USER,
                            'api_name': field.api_name,
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': task.id,
                        'number': task.number,
                        'name': task.name,
                        'api_name': task.api_name,
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

    def test_update__conditions_with_equal_api_names__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        step = 'Second step'
        condition_api_name = 'cond-1'
        account = create_test_account()
        user = create_test_owner(account=account)

        template = create_test_template(user, is_active=True)
        field = FieldTemplate.objects.create(
            name='Name',
            api_name='name',
            type=FieldType.USER,
            kickoff=template.kickoff_instance,
            is_required=True,
            template=template,
            account=user.account,
        )
        first_task = template.tasks.order_by('number').first()
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=first_task,
            template=template,
            api_name=condition_api_name,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        predicate = PredicateTemplate.objects.create(
            rule=rule,
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
        )
        api_client.token_authenticate(user)

        condition_1 = {
            'api_name': condition_api_name,
            'order': condition.order,
            'action': ConditionAction.END_WORKFLOW,
            'rules': [
                {
                    'api_name': rule.api_name,
                    'predicates': [
                        {
                            'api_name': predicate.api_name,
                            'field': predicate.field,
                            'field_type': predicate.field_type,
                            'operator': predicate.operator,
                        },
                    ],
                },
            ],
        }

        condition_2 = {
            'order': 1,
            'action': 'skip_task',
            'api_name': condition_api_name,
            'rules': [
                {
                    'predicates': [
                        {
                            'field': field.api_name,
                            'field_type': FieldType.USER,
                            'operator': PredicateOperator.EXIST,
                        },
                    ],
                },
            ],
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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'id': field.id,
                            'order': field.order,
                            'name': field.name,
                            'type': field.type,
                            'api_name': field.api_name,
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': first_task.id,
                        'number': first_task.number,
                        'name': first_task.name,
                        'api_name': first_task.api_name,
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

    def test_update__rules_with_equal_api_names__validation_error(
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
        account = create_test_account()
        user = create_test_owner(account=account)
        api_client.token_authenticate(user)

        template = create_test_template(user, is_active=True)
        field = FieldTemplate.objects.create(
            name='Name',
            api_name='name',
            type=FieldType.USER,
            kickoff=template.kickoff_instance,
            is_required=True,
            template=template,
            account=user.account,
        )
        first_task = template.tasks.order_by('number').first()
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=first_task,
            template=template,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
            api_name=rule_api_name,
        )
        predicate = PredicateTemplate.objects.create(
            rule=rule,
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
        )
        api_client.token_authenticate(user)

        condition_1 = {
            'api_name': condition.api_name,
            'order': condition.order,
            'action': ConditionAction.END_WORKFLOW,
            'rules': [
                {
                    'api_name': rule_api_name,
                    'predicates': [
                        {
                            'api_name': predicate.api_name,
                            'field': predicate.field,
                            'field_type': predicate.field_type,
                            'operator': predicate.operator,
                        },
                    ],
                },
            ],
        }

        condition_2 = {
            'order': 1,
            'action': 'skip_task',
            'rules': [
                {
                    'api_name': rule_api_name,
                    'predicates': [
                        {
                            'field': field.api_name,
                            'field_type': FieldType.USER,
                            'operator': PredicateOperator.EXIST,
                        },
                    ],
                },
            ],
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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'id': field.id,
                            'order': field.order,
                            'name': field.name,
                            'type': field.type,
                            'api_name': field.api_name,
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': first_task.id,
                        'number': first_task.number,
                        'name': first_task.name,
                        'api_name': first_task.api_name,
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

    def test_update__predicates_with_equal_api_names__validation_error(
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
        account = create_test_account()
        user = create_test_owner(account=account)
        api_client.token_authenticate(user)

        template = create_test_template(user, is_active=True)
        field = FieldTemplate.objects.create(
            name='Name',
            api_name='name',
            type=FieldType.USER,
            kickoff=template.kickoff_instance,
            is_required=True,
            template=template,
            account=user.account,
        )
        first_task = template.tasks.order_by('number').first()
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=first_task,
            template=template,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        predicate = PredicateTemplate.objects.create(
            rule=rule,
            operator=PredicateOperator.EXIST,
            field_type=PredicateType.USER,
            field=field.api_name,
            template=template,
            api_name=predicate_api_name,
        )
        api_client.token_authenticate(user)

        condition_1 = {
            'api_name': condition.api_name,
            'order': condition.order,
            'action': ConditionAction.END_WORKFLOW,
            'rules': [
                {
                    'api_name': rule.api_name,
                    'predicates': [
                        {
                            'api_name': predicate_api_name,
                            'field': predicate.field,
                            'field_type': predicate.field_type,
                            'operator': predicate.operator,
                        },
                    ],
                },
            ],
        }

        condition_2 = {
            'order': 1,
            'action': 'skip_task',
            'rules': [
                {
                    'predicates': [
                        {
                            'api_name': predicate_api_name,
                            'field': field.api_name,
                            'field_type': FieldType.USER,
                            'operator': PredicateOperator.EXIST,
                        },
                    ],
                },
            ],
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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'id': field.id,
                            'order': field.order,
                            'name': field.name,
                            'type': field.type,
                            'api_name': field.api_name,
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': first_task.id,
                        'number': first_task.number,
                        'name': first_task.name,
                        'api_name': first_task.api_name,
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

    def test_update__start_task_points_to_not_existent_task__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        template = create_test_template(user, is_active=True, tasks_count=1)
        task = template.tasks.get(number=1)
        field = FieldTemplate.objects.create(
            name='Key',
            type=FieldType.STRING,
            kickoff=template.kickoff_instance,
            template=template,
            account=user.account,
        )
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=task,
            template=template,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        predicate = PredicateTemplate.objects.create(
            rule=rule,
            operator=PredicateOperator.EXIST,
            field_type=FieldType.STRING,
            field=field.api_name,
            template=template,
        )
        mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        not_existent_api_name = 'not-existent'
        condition_data = {
            'api_name': condition.api_name,
            'order': condition.order,
            'action': ConditionAction.START_TASK,
            'rules': [
                {
                    'api_name': rule.api_name,
                    'predicates': [
                        {
                            'field_type': PredicateType.TASK,
                            'operator': PredicateOperator.COMPLETED,
                            'api_name': predicate.api_name,
                            'field': not_existent_api_name,
                            'value': None,
                        },
                    ],
                },
            ],
        }
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
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'number': task.number,
                        'id': task.id,
                        'name': task.name,
                        'api_name': task.api_name,
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
        error_message = messages.MSG_PT_0066(name=task.name)
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['details']['reason'] == error_message
        assert response.data['details']['api_name'] == predicate.api_name
        assert response.data['message'] == error_message

    def test_update__skip_task_points_to_not_existent_task__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        template = create_test_template(user, is_active=True, tasks_count=1)
        task = template.tasks.get(number=1)
        field = FieldTemplate.objects.create(
            name='Key',
            type=FieldType.STRING,
            kickoff=template.kickoff_instance,
            template=template,
            account=user.account,
        )
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=task,
            template=template,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        predicate = PredicateTemplate.objects.create(
            rule=rule,
            operator=PredicateOperator.EXIST,
            field_type=FieldType.STRING,
            field=field.api_name,
            template=template,
        )
        mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        not_existent_api_name = 'not-existent'
        condition_data = {
            'api_name': condition.api_name,
            'order': condition.order,
            'action': ConditionAction.SKIP_TASK,
            'rules': [
                {
                    'api_name': rule.api_name,
                    'predicates': [
                        {
                            'field_type': PredicateType.TASK,
                            'operator': PredicateOperator.COMPLETED,
                            'api_name': predicate.api_name,
                            'field': not_existent_api_name,
                            'value': None,
                        },
                    ],
                },
            ],
        }
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
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'number': task.number,
                        'id': task.id,
                        'name': task.name,
                        'api_name': task.api_name,
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
        error_message = messages.MSG_PT_0067(name=task.name)
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['details']['reason'] == error_message
        assert response.data['details']['api_name'] == predicate.api_name
        assert response.data['message'] == error_message

    def test_update__skip_task_points_to_not_ancestor_task__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        template = create_test_template(user, is_active=True, tasks_count=2)
        task_1 = template.tasks.get(number=1)
        task_2 = template.tasks.get(number=2)
        field = FieldTemplate.objects.create(
            name='Key',
            type=FieldType.STRING,
            kickoff=template.kickoff_instance,
            template=template,
            account=user.account,
        )
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=task_2,
            template=template,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        predicate = PredicateTemplate.objects.create(
            rule=rule,
            operator=PredicateOperator.EXIST,
            field_type=FieldType.STRING,
            field=field.api_name,
            template=template,
        )
        mocker.patch(
            'src.processes.serializers.templates.'
            'condition.AnalyticService.templates_task_condition_created',
        )
        condition_data = {
            'api_name': condition.api_name,
            'order': condition.order,
            'action': ConditionAction.SKIP_TASK,
            'rules': [
                {
                    'api_name': rule.api_name,
                    'predicates': [
                        {
                            'field_type': PredicateType.TASK,
                            'operator': PredicateOperator.COMPLETED,
                            'api_name': predicate.api_name,
                            'field': task_1.api_name,
                            'value': None,
                        },
                    ],
                },
            ],
        }
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
                    },
                ],
                'kickoff': {},
                'tasks': [
                    {
                        'number': task_1.number,
                        'id': task_1.id,
                        'name': task_1.name,
                        'api_name': task_1.api_name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id,
                            },
                        ],
                    },
                    {
                        'number': task_2.number,
                        'id': task_2.id,
                        'name': task_2.name,
                        'api_name': task_2.api_name,
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
        error_message = messages.MSG_PT_0068(name=task_2.name)
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['details']['reason'] == error_message
        assert response.data['details']['api_name'] == predicate.api_name
        assert response.data['message'] == error_message

    def test_update__predicate_to_type_group__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        group = create_test_group(account=account)
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        template = create_test_template(
            user=user,
            tasks_count=3,
            is_active=True,
        )
        first_task = template.tasks.order_by('number').first()
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=first_task,
            template=template,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        predicate_api_name = 'predicate-1'
        predicate = PredicateTemplate.objects.create(
            rule=rule,
            field_type=PredicateType.KICKOFF,
            operator=PredicateOperator.COMPLETED,
            field=None,
            template=template,
            api_name=predicate_api_name,
        )
        field_api_name = 'group-field-1'
        value = str(group.id)
        request_data = {
            'api_name': condition.api_name,
            'order': condition.order,
            'action': ConditionAction.END_WORKFLOW,
            'rules': [
                {
                    'api_name': rule.api_name,
                    'predicates': [
                        {
                            'api_name': predicate_api_name,
                            'field_type': PredicateType.GROUP,
                            'operator': PredicateOperator.EQUAL,
                            'field': field_api_name,
                            'value': value,
                        },
                    ],
                },
            ],
        }
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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'Name',
                            'type': FieldType.USER,
                            'api_name': field_api_name,
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': first_task.id,
                        'number': first_task.number,
                        'name': first_task.name,
                        'api_name': first_task.api_name,
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
        assert predicate_data['api_name'] == predicate_api_name
        assert predicate_data['operator'] == PredicateOperator.EQUAL
        assert predicate_data['value'] == value
        assert predicate_data['field'] == field_api_name

        predicate.refresh_from_db()
        assert predicate.field_type == PredicateType.GROUP
        assert predicate.operator == PredicateOperator.EQUAL
        assert predicate.field == field_api_name
        assert predicate.value == value
        assert predicate.group_id == group.id

    def test_update__group_field_incorrect_value__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        create_test_group(account=account)
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        template = create_test_template(
            user=user,
            tasks_count=3,
            is_active=True,
        )
        first_task = template.tasks.order_by('number').first()
        condition = ConditionTemplate.objects.create(
            action=ConditionAction.SKIP_TASK,
            order=1,
            task=first_task,
            template=template,
        )
        rule = RuleTemplate.objects.create(
            condition=condition,
            template=template,
        )
        predicate_api_name = 'predicate-1'
        field_api_name = 'group-field-1'
        invalid_value = 'invalid-group-id'
        request_data = {
            'api_name': condition.api_name,
            'order': condition.order,
            'action': ConditionAction.END_WORKFLOW,
            'rules': [
                {
                    'api_name': rule.api_name,
                    'predicates': [
                        {
                            'api_name': predicate_api_name,
                            'field_type': PredicateType.GROUP,
                            'operator': PredicateOperator.EQUAL,
                            'field': field_api_name,
                            'value': invalid_value,
                        },
                    ],
                },
            ],
        }
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
                    },
                ],
                'kickoff': {
                    'fields': [
                        {
                            'order': 1,
                            'name': 'Name',
                            'type': FieldType.USER,
                            'api_name': field_api_name,
                            'is_required': True,
                        },
                    ],
                },
                'tasks': [
                    {
                        'id': first_task.id,
                        'number': first_task.number,
                        'name': first_task.name,
                        'api_name': first_task.api_name,
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
        message = messages.MSG_PT_0062(
            task=first_task.name,
            group_id=invalid_value,
        )
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == message
        assert response.data['details']['api_name'] == predicate_api_name
        assert response.data['details']['reason'] == message
