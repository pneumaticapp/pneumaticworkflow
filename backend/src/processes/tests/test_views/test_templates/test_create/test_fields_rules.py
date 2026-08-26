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
from src.processes.messages.template import MSG_PT_0079
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
