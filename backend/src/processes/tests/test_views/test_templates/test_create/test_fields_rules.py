import pytest

from src.processes.enums import (
    FieldRuleOperator,
    FieldRuleType,
    FieldType,
    OwnerRole,
    OwnerType,
    PerformerType,
)
from src.processes.models.templates.fields import (
    FieldTemplateRuleGroupAnd,
    FieldTemplateRuleGroupOr,
    FieldTemplateRuleSet,
)
from src.processes.messages.template import MSG_PT_0079, MSG_PT_0080
from src.processes.tests.fixtures import (
    create_test_account, create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_create_task_field_rules__active_template_all_data__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    field_1_api_name = 'field-1'
    field_2_api_name = 'field-2'
    ruleset_api_name = 'field-ruleset-1'
    group_or_api_name = 'field-group-or-1'
    group_and_api_name = 'field-group-and-1'
    rule_name = 'Show when value is yes'
    rule_message = 'Show when value is yes'
    rule_order = 1
    rule_value = 'yes'
    request_rules = [
        {
            'api_name': ruleset_api_name,
            'name': rule_name,
            'type': FieldRuleType.SHOW,
            'message': rule_message,
            'order': rule_order,
            'groups_or': [
                {
                    'api_name': group_or_api_name,
                    'groups_and': [
                        {
                            'api_name': group_and_api_name,
                            'field': field_1_api_name,
                            'operator': FieldRuleOperator.EQUAL,
                            'value': rule_value,
                        },
                    ],
                },
            ],
        },
    ]
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/templates',
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
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [
                        {
                            'type': FieldType.NUMBER,
                            'name': 'Number field',
                            'order': 1,
                            'api_name': field_1_api_name,
                        },
                        {
                            'type': FieldType.STRING,
                            'name': 'String field',
                            'order': 2,
                            'api_name': field_2_api_name,
                            'rulesets': request_rules,
                        },
                    ],
                },
            ],
        },
    )

    # assert
    assert response.status_code == 200

    # FieldTemplate ordering is -order
    field_2_data = response.data['tasks'][0]['fields'][0]
    assert field_2_data['api_name'] == field_2_api_name
    assert len(field_2_data['rulesets']) == 1
    field_1_data = response.data['tasks'][0]['fields'][1]
    assert field_1_data['api_name'] == field_1_api_name
    assert field_1_data['rulesets'] == []

    ruleset_data = field_2_data['rulesets'][0]
    assert ruleset_data['api_name'] == ruleset_api_name
    assert ruleset_data['name'] == rule_name
    assert ruleset_data['type'] == FieldRuleType.SHOW
    assert ruleset_data['message'] == rule_message
    assert ruleset_data['order'] == rule_order
    assert len(ruleset_data['groups_or']) == 1

    group_or_data = ruleset_data['groups_or'][0]
    assert group_or_data['api_name'] == group_or_api_name
    assert len(group_or_data['groups_and']) == 1

    group_and_data = group_or_data['groups_and'][0]
    assert group_and_data['api_name'] == group_and_api_name
    assert group_and_data['field'] == field_1_api_name
    assert group_and_data['operator'] == FieldRuleOperator.EQUAL
    assert group_and_data['value'] == rule_value

    ruleset = FieldTemplateRuleSet.objects.get(api_name=ruleset_api_name)
    assert ruleset.name == rule_name
    assert ruleset.type == FieldRuleType.SHOW
    assert ruleset.message == rule_message
    assert ruleset.order == rule_order
    assert ruleset.field.api_name == field_2_api_name

    group_or = FieldTemplateRuleGroupOr.objects.get(
        api_name=group_or_api_name,
        ruleset=ruleset,
    )

    group_and = FieldTemplateRuleGroupAnd.objects.get(
        api_name=group_and_api_name,
        group_or=group_or,
    )
    assert group_and.field == field_1_api_name
    assert group_and.operator == FieldRuleOperator.EQUAL
    assert group_and.value == rule_value


def test_create_task_field_rules__missing_name__validation_error(api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/templates',
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
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [
                        {
                            'type': FieldType.STRING,
                            'name': 'String field',
                            'order': 1,
                            'api_name': 'field-1',
                            'rulesets': [
                                {
                                    'type': FieldRuleType.SHOW,
                                    'groups_or': [],
                                },
                            ],
                        },
                    ],
                },
            ],
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == 'Name: this field is required.'


def test_create_task_field_rules__show_missing_field__validation_error(
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/templates',
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
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [
                        {
                            'type': FieldType.STRING,
                            'name': 'String field',
                            'order': 1,
                            'api_name': 'field-1',
                            'rulesets': [
                                {
                                    'name': 'Show ruleset',
                                    'type': FieldRuleType.SHOW,
                                    'groups_or': [
                                        {
                                            'groups_and': [
                                                {
                                                    'operator': (
                                                        FieldRuleOperator.EQUAL
                                                    ),
                                                    'value': 'yes',
                                                },
                                            ],
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
    assert response.status_code == 400
    assert response.data['message'] == MSG_PT_0079


def test_create_task_field_rules__show_field_null__validation_error(
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/templates',
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
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [
                        {
                            'type': FieldType.STRING,
                            'name': 'String field',
                            'order': 1,
                            'api_name': 'field-1',
                            'rulesets': [
                                {
                                    'name': 'Show ruleset',
                                    'type': FieldRuleType.SHOW,
                                    'groups_or': [
                                        {
                                            'groups_and': [
                                                {
                                                    'field': None,
                                                    'operator': (
                                                        FieldRuleOperator.EQUAL
                                                    ),
                                                    'value': 'yes',
                                                },
                                            ],
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
    assert response.status_code == 400
    assert response.data['message'] == MSG_PT_0079


@pytest.mark.parametrize(
    ('field_type', 'operator', 'value'),
    (
        (FieldType.STRING, FieldRuleOperator.EQUAL, 'yes'),
        (FieldType.TEXT, FieldRuleOperator.CONTAIN, 'text'),
        (FieldType.URL, FieldRuleOperator.NOT_EQUAL, 'http://example.com'),
        (FieldType.DATE, FieldRuleOperator.GREATER_THAN, '1577836800'),
        (FieldType.NUMBER, FieldRuleOperator.LESS_THAN, '10'),
        (FieldType.FILE, FieldRuleOperator.EXIST, None),
    ),
)
def test_create_task_field_rules__validator_by_field_type__ok(
    api_client,
    field_type,
    operator,
    value,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    rule_message = 'Value is invalid'
    field_data = {
        'type': field_type,
        'name': 'Field',
        'order': 1,
        'rulesets': [
            {
                'name': 'Some name',
                'type': FieldRuleType.VALIDATOR,
                'message': rule_message,
                'order': 1,
                'groups_or': [
                    {
                        'groups_and': [
                            {
                                'operator': operator,
                                'value': value,
                                'field': None,
                            },
                        ],
                    },
                ],
            },
        ],
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/templates',
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
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [field_data],
                },
            ],
        },
    )

    # assert
    assert response.status_code == 200
    field_response = response.data['tasks'][0]['fields'][0]
    ruleset_data = field_response['rulesets'][0]
    assert ruleset_data['type'] == FieldRuleType.VALIDATOR
    group_or_data = ruleset_data['groups_or'][0]
    group_and_data = group_or_data['groups_and'][0]
    assert group_and_data['field'] is None
    assert group_and_data['operator'] == operator
    assert group_and_data['value'] == value


def test_create_task_field_rules__date_invalid_value__validation_error(
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/templates',
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
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [
                        {
                            'type': FieldType.DATE,
                            'name': 'Field',
                            'order': 1,
                            'rulesets': [
                                {
                                    'name': 'Some name',
                                    'type': FieldRuleType.VALIDATOR,
                                    'groups_or': [
                                        {
                                            'groups_and': [
                                                {
                                                    'operator': (
                                                        FieldRuleOperator
                                                        .GREATER_THAN
                                                    ),
                                                    'value': '2020-01-01',
                                                },
                                            ],
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
    assert response.status_code == 400
    assert response.data['message'] == MSG_PT_0080


def test_create_task_field_rules__validator_user_field__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    operator = FieldRuleOperator.EQUAL
    value = '1'
    rule_message = 'Value is invalid'
    field_data = {
        'type': FieldType.USER,
        'name': 'Field',
        'order': 1,
        'is_required': True,
        'rulesets': [
            {
                'name': 'Some name',
                'type': FieldRuleType.VALIDATOR,
                'message': rule_message,
                'order': 1,
                'groups_or': [
                    {
                        'groups_and': [
                            {
                                'operator': operator,
                                'value': value,
                            },
                        ],
                    },
                ],
            },
        ],
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/templates',
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
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [field_data],
                },
            ],
        },
    )

    # assert
    assert response.status_code == 200
    field_response = response.data['tasks'][0]['fields'][0]
    ruleset_data = field_response['rulesets'][0]
    assert ruleset_data['type'] == FieldRuleType.VALIDATOR
    group_or_data = ruleset_data['groups_or'][0]
    group_and_data = group_or_data['groups_and'][0]
    assert group_and_data['field'] is None
    assert group_and_data['operator'] == operator
    assert group_and_data['value'] == value


@pytest.mark.parametrize(
    ('field_type', 'operator', 'value'),
    (
        (FieldType.CHECKBOX, FieldRuleOperator.CONTAIN, 'First'),
        (FieldType.RADIO, FieldRuleOperator.EQUAL, 'First'),
        (FieldType.DROPDOWN, FieldRuleOperator.NOT_EQUAL, 'First'),
    ),
)
def test_create_task_field_rules__validator_types_with_selections__ok(
    api_client,
    field_type,
    operator,
    value,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    rule_message = 'Value is invalid'
    field_data = {
        'type': field_type,
        'name': 'Field',
        'order': 1,
        'selections': [
            {'value': 'First'},
            {'value': 'Second'},
        ],
        'rulesets': [
            {
                'name': 'Some name',
                'type': FieldRuleType.VALIDATOR,
                'message': rule_message,
                'order': 1,
                'groups_or': [
                    {
                        'groups_and': [
                            {
                                'operator': operator,
                                'value': value,
                            },
                        ],
                    },
                ],
            },
        ],
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/templates',
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
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [field_data],
                },
            ],
        },
    )

    # assert
    assert response.status_code == 200
    field_response = response.data['tasks'][0]['fields'][0]
    ruleset_data = field_response['rulesets'][0]
    assert ruleset_data['type'] == FieldRuleType.VALIDATOR
    group_or_data = ruleset_data['groups_or'][0]
    group_and_data = group_or_data['groups_and'][0]
    assert group_and_data['field'] is None
    assert group_and_data['operator'] == operator
    assert group_and_data['value'] == value
