import pytest

from src.processes.enums import (
    FieldRuleOperator,
    FieldRuleType,
    FieldType,
    OwnerRole,
    OwnerType,
    PerformerType,
)
from src.processes.messages.template import MSG_PT_0075, MSG_PT_0079
from src.processes.models.templates.fields import (
    FieldTemplate,
    FieldTemplateRuleGroupAnd,
    FieldTemplateRuleGroupOr,
    FieldTemplateRuleSet,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


def _field_by_api_name(fields, api_name):
    return next(field for field in fields if field['api_name'] == api_name)


def _create_show_ruleset(
    account,
    template,
    field,
    source_field_api_name,
    ruleset_api_name='field-ruleset-1',
    group_or_api_name='field-group-or-1',
    group_and_api_name='field-group-and-1',
    name='Show ruleset',
    message=None,
    order=0,
    operator=FieldRuleOperator.EQUAL,
    value='yes',
):
    ruleset = FieldTemplateRuleSet.objects.create(
        account=account,
        template=template,
        field=field,
        api_name=ruleset_api_name,
        name=name,
        type=FieldRuleType.SHOW,
        message=message,
        order=order,
    )
    group_or = FieldTemplateRuleGroupOr.objects.create(
        account=account,
        template=template,
        ruleset=ruleset,
        api_name=group_or_api_name,
    )
    group_and = FieldTemplateRuleGroupAnd.objects.create(
        account=account,
        template=template,
        group_or=group_or,
        api_name=group_and_api_name,
        field=source_field_api_name,
        operator=operator,
        value=value,
    )
    return ruleset, group_or, group_and


@pytest.mark.parametrize('is_active', (True, False))
def test_update__task_field_ruleset_all_data__ok(
    mocker,
    is_active,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=is_active, tasks_count=1)
    task = template.tasks.first()
    source_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Source field',
        order=1,
        task=task,
        api_name='field-1',
        template=template,
        account=account,
    )
    extra_source_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Extra source field',
        order=0,
        task=task,
        api_name='field-3',
        template=template,
        account=account,
    )
    target_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Target field',
        order=2,
        task=task,
        api_name='field-2',
        template=template,
        account=account,
    )
    ruleset, group_or, group_and = _create_show_ruleset(
        account=account,
        template=template,
        field=target_field,
        source_field_api_name=source_field.api_name,
    )
    ruleset_id = ruleset.id
    group_or_id = group_or.id
    group_and_id = group_and.id
    new_name = 'Validate when value is no'
    new_message = 'Value must not be no'
    new_order = 2
    new_value = 'no'
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
            'is_active': is_active,
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
                    'id': task.id,
                    'api_name': task.api_name,
                    'number': task.number,
                    'name': task.name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [
                        {
                            'name': source_field.name,
                            'type': source_field.type,
                            'order': source_field.order,
                            'api_name': source_field.api_name,
                        },
                        {
                            'name': extra_source_field.name,
                            'type': extra_source_field.type,
                            'order': extra_source_field.order,
                            'api_name': extra_source_field.api_name,
                        },
                        {
                            'name': target_field.name,
                            'type': target_field.type,
                            'order': target_field.order,
                            'api_name': target_field.api_name,
                            'rulesets': [
                                {
                                    'api_name': ruleset.api_name,
                                    'name': new_name,
                                    'type': FieldRuleType.VALIDATOR,
                                    'message': new_message,
                                    'order': new_order,
                                    'groups_or': [
                                        {
                                            'api_name': group_or.api_name,
                                            'groups_and': [
                                                {
                                                    'api_name': (
                                                        group_and.api_name
                                                    ),
                                                    'field': (
                                                        extra_source_field
                                                        .api_name
                                                    ),
                                                    'operator': (
                                                        FieldRuleOperator
                                                        .NOT_EQUAL
                                                    ),
                                                    'value': new_value,
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
    assert response.status_code == 200
    field_data = _field_by_api_name(
        response.data['tasks'][0]['fields'],
        target_field.api_name,
    )
    assert len(field_data['rulesets']) == 1
    ruleset_data = field_data['rulesets'][0]
    assert ruleset_data['api_name'] == ruleset.api_name
    assert ruleset_data['name'] == new_name
    assert ruleset_data['type'] == FieldRuleType.VALIDATOR
    assert ruleset_data['message'] == new_message
    assert ruleset_data['order'] == new_order
    assert len(ruleset_data['groups_or']) == 1
    group_or_data = ruleset_data['groups_or'][0]
    assert group_or_data['api_name'] == group_or.api_name
    assert len(group_or_data['groups_and']) == 1
    group_and_data = group_or_data['groups_and'][0]
    assert group_and_data['api_name'] == group_and.api_name
    assert group_and_data['field'] == extra_source_field.api_name
    assert group_and_data['operator'] == FieldRuleOperator.NOT_EQUAL
    assert group_and_data['value'] == new_value

    if is_active:
        ruleset.refresh_from_db()
        group_or.refresh_from_db()
        group_and.refresh_from_db()
        assert ruleset.id == ruleset_id
        assert ruleset.api_name == 'field-ruleset-1'
        assert ruleset.name == new_name
        assert ruleset.type == FieldRuleType.VALIDATOR
        assert ruleset.message == new_message
        assert ruleset.order == new_order
        assert group_or.id == group_or_id
        assert group_or.api_name == 'field-group-or-1'
        assert group_and.id == group_and_id
        assert group_and.api_name == 'field-group-and-1'
        assert group_and.field == extra_source_field.api_name
        assert group_and.operator == FieldRuleOperator.NOT_EQUAL
        assert group_and.value == new_value


def test_update__kickoff_field_ruleset_all_data__ok(mocker, api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    source_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Source field',
        order=1,
        kickoff=kickoff,
        api_name='field-1',
        template=template,
        account=account,
    )
    extra_source_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Extra source field',
        order=0,
        kickoff=kickoff,
        api_name='field-3',
        template=template,
        account=account,
    )
    target_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Target field',
        order=2,
        kickoff=kickoff,
        api_name='field-2',
        template=template,
        account=account,
    )
    ruleset, group_or, group_and = _create_show_ruleset(
        account=account,
        template=template,
        field=target_field,
        source_field_api_name=source_field.api_name,
    )
    ruleset_id = ruleset.id
    group_or_id = group_or.id
    group_and_id = group_and.id
    new_name = 'Validate when value is no'
    new_message = 'Value must not be no'
    new_order = 2
    new_value = 'no'
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
                'id': kickoff.id,
                'fields': [
                    {
                        'name': source_field.name,
                        'type': source_field.type,
                        'order': source_field.order,
                        'api_name': source_field.api_name,
                    },
                    {
                        'name': extra_source_field.name,
                        'type': extra_source_field.type,
                        'order': extra_source_field.order,
                        'api_name': extra_source_field.api_name,
                    },
                    {
                        'name': target_field.name,
                        'type': target_field.type,
                        'order': target_field.order,
                        'api_name': target_field.api_name,
                        'rulesets': [
                            {
                                'api_name': ruleset.api_name,
                                'name': new_name,
                                'type': FieldRuleType.VALIDATOR,
                                'message': new_message,
                                'order': new_order,
                                'groups_or': [
                                    {
                                        'api_name': group_or.api_name,
                                        'groups_and': [
                                            {
                                                'api_name': group_and.api_name,
                                                'field': (
                                                    extra_source_field.api_name
                                                ),
                                                'operator': (
                                                    FieldRuleOperator.NOT_EQUAL
                                                ),
                                                'value': new_value,
                                            },
                                        ],
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
            'tasks': [
                {
                    'id': task.id,
                    'api_name': task.api_name,
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
    field_data = _field_by_api_name(
        response.data['kickoff']['fields'],
        target_field.api_name,
    )
    assert len(field_data['rulesets']) == 1
    ruleset_data = field_data['rulesets'][0]
    assert ruleset_data['api_name'] == ruleset.api_name
    assert ruleset_data['name'] == new_name
    assert ruleset_data['type'] == FieldRuleType.VALIDATOR
    assert ruleset_data['message'] == new_message
    assert ruleset_data['order'] == new_order
    assert len(ruleset_data['groups_or']) == 1
    group_or_data = ruleset_data['groups_or'][0]
    assert group_or_data['api_name'] == group_or.api_name
    assert len(group_or_data['groups_and']) == 1
    group_and_data = group_or_data['groups_and'][0]
    assert group_and_data['api_name'] == group_and.api_name
    assert group_and_data['field'] == extra_source_field.api_name
    assert group_and_data['operator'] == FieldRuleOperator.NOT_EQUAL
    assert group_and_data['value'] == new_value

    ruleset.refresh_from_db()
    group_or.refresh_from_db()
    group_and.refresh_from_db()
    assert ruleset.id == ruleset_id
    assert ruleset.api_name == 'field-ruleset-1'
    assert ruleset.name == new_name
    assert ruleset.type == FieldRuleType.VALIDATOR
    assert ruleset.message == new_message
    assert ruleset.order == new_order
    assert group_or.id == group_or_id
    assert group_or.api_name == 'field-group-or-1'
    assert group_and.id == group_and_id
    assert group_and.api_name == 'field-group-and-1'
    assert group_and.field == extra_source_field.api_name
    assert group_and.operator == FieldRuleOperator.NOT_EQUAL
    assert group_and.value == new_value


def test_update__task_preserve_ruleset_api_names__ok(mocker, api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    task = template.tasks.first()
    source_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Source field',
        order=1,
        task=task,
        api_name='field-1',
        template=template,
        account=account,
    )
    target_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Target field',
        order=2,
        task=task,
        api_name='field-2',
        template=template,
        account=account,
    )
    ruleset, group_or, group_and = _create_show_ruleset(
        account=account,
        template=template,
        field=target_field,
        source_field_api_name=source_field.api_name,
    )
    new_name = 'Updated show ruleset'
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
            'kickoff': {},
            'tasks': [
                {
                    'id': task.id,
                    'api_name': task.api_name,
                    'number': task.number,
                    'name': task.name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [
                        {
                            'name': source_field.name,
                            'type': source_field.type,
                            'order': source_field.order,
                            'api_name': source_field.api_name,
                        },
                        {
                            'name': target_field.name,
                            'type': target_field.type,
                            'order': target_field.order,
                            'api_name': target_field.api_name,
                            'rulesets': [
                                {
                                    'api_name': ruleset.api_name,
                                    'name': new_name,
                                    'type': ruleset.type,
                                    'message': ruleset.message,
                                    'order': ruleset.order,
                                    'groups_or': [
                                        {
                                            'api_name': group_or.api_name,
                                            'groups_and': [
                                                {
                                                    'api_name': (
                                                        group_and.api_name
                                                    ),
                                                    'field': group_and.field,
                                                    'operator': (
                                                        group_and.operator
                                                    ),
                                                    'value': group_and.value,
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
    assert response.status_code == 200
    field_data = _field_by_api_name(
        response.data['tasks'][0]['fields'],
        target_field.api_name,
    )
    ruleset_data = field_data['rulesets'][0]
    assert ruleset_data['api_name'] == ruleset.api_name
    assert ruleset_data['name'] == new_name
    group_or_data = ruleset_data['groups_or'][0]
    assert group_or_data['api_name'] == group_or.api_name
    group_and_data = group_or_data['groups_and'][0]
    assert group_and_data['api_name'] == group_and.api_name

    ruleset.refresh_from_db()
    group_or.refresh_from_db()
    group_and.refresh_from_db()
    assert ruleset.api_name == 'field-ruleset-1'
    assert ruleset.name == new_name
    assert group_or.api_name == 'field-group-or-1'
    assert group_and.api_name == 'field-group-and-1'


def test_update__add_group_or_to_existing_ruleset__ok(mocker, api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    task = template.tasks.first()
    source_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Source field',
        order=1,
        task=task,
        api_name='field-1',
        template=template,
        account=account,
    )
    target_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Target field',
        order=2,
        task=task,
        api_name='field-2',
        template=template,
        account=account,
    )
    ruleset, group_or, group_and = _create_show_ruleset(
        account=account,
        template=template,
        field=target_field,
        source_field_api_name=source_field.api_name,
    )
    new_group_or_api_name = 'field-group-or-2'
    new_group_and_api_name = 'field-group-and-2'
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
            'kickoff': {},
            'tasks': [
                {
                    'id': task.id,
                    'api_name': task.api_name,
                    'number': task.number,
                    'name': task.name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [
                        {
                            'name': source_field.name,
                            'type': source_field.type,
                            'order': source_field.order,
                            'api_name': source_field.api_name,
                        },
                        {
                            'name': target_field.name,
                            'type': target_field.type,
                            'order': target_field.order,
                            'api_name': target_field.api_name,
                            'rulesets': [
                                {
                                    'api_name': ruleset.api_name,
                                    'name': ruleset.name,
                                    'type': ruleset.type,
                                    'groups_or': [
                                        {
                                            'api_name': group_or.api_name,
                                            'groups_and': [
                                                {
                                                    'api_name': (
                                                        group_and.api_name
                                                    ),
                                                    'field': group_and.field,
                                                    'operator': (
                                                        group_and.operator
                                                    ),
                                                    'value': group_and.value,
                                                },
                                            ],
                                        },
                                        {
                                            'api_name': new_group_or_api_name,
                                            'groups_and': [
                                                {
                                                    'api_name': (
                                                        new_group_and_api_name
                                                    ),
                                                    'field': (
                                                        source_field.api_name
                                                    ),
                                                    'operator': (
                                                        FieldRuleOperator
                                                        .NOT_EQUAL
                                                    ),
                                                    'value': 'no',
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
    assert response.status_code == 200
    field_data = _field_by_api_name(
        response.data['tasks'][0]['fields'],
        target_field.api_name,
    )
    groups_or = field_data['rulesets'][0]['groups_or']
    assert len(groups_or) == 2
    group_or_api_names = {item['api_name'] for item in groups_or}
    assert group_or.api_name in group_or_api_names
    assert new_group_or_api_name in group_or_api_names

    group_or.refresh_from_db()
    assert FieldTemplateRuleGroupOr.objects.filter(
        id=group_or.id,
        api_name=group_or.api_name,
        ruleset=ruleset,
    ).exists()
    assert FieldTemplateRuleGroupOr.objects.filter(
        api_name=new_group_or_api_name,
        ruleset=ruleset,
    ).exists()
    assert ruleset.groups_or.count() == 2


def test_update__add_group_and_to_existing_group_or__ok(mocker, api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    task = template.tasks.first()
    source_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Source field',
        order=1,
        task=task,
        api_name='field-1',
        template=template,
        account=account,
    )
    target_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Target field',
        order=2,
        task=task,
        api_name='field-2',
        template=template,
        account=account,
    )
    ruleset, group_or, group_and = _create_show_ruleset(
        account=account,
        template=template,
        field=target_field,
        source_field_api_name=source_field.api_name,
    )
    new_group_and_api_name = 'field-group-and-2'
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
            'kickoff': {},
            'tasks': [
                {
                    'id': task.id,
                    'api_name': task.api_name,
                    'number': task.number,
                    'name': task.name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [
                        {
                            'name': source_field.name,
                            'type': source_field.type,
                            'order': source_field.order,
                            'api_name': source_field.api_name,
                        },
                        {
                            'name': target_field.name,
                            'type': target_field.type,
                            'order': target_field.order,
                            'api_name': target_field.api_name,
                            'rulesets': [
                                {
                                    'api_name': ruleset.api_name,
                                    'name': ruleset.name,
                                    'type': ruleset.type,
                                    'groups_or': [
                                        {
                                            'api_name': group_or.api_name,
                                            'groups_and': [
                                                {
                                                    'api_name': (
                                                        group_and.api_name
                                                    ),
                                                    'field': group_and.field,
                                                    'operator': (
                                                        group_and.operator
                                                    ),
                                                    'value': group_and.value,
                                                },
                                                {
                                                    'api_name': (
                                                        new_group_and_api_name
                                                    ),
                                                    'field': (
                                                        source_field.api_name
                                                    ),
                                                    'operator': (
                                                        FieldRuleOperator
                                                        .NOT_EQUAL
                                                    ),
                                                    'value': 'no',
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
    assert response.status_code == 200
    field_data = _field_by_api_name(
        response.data['tasks'][0]['fields'],
        target_field.api_name,
    )
    groups_and = field_data['rulesets'][0]['groups_or'][0]['groups_and']
    assert len(groups_and) == 2
    group_and_api_names = {item['api_name'] for item in groups_and}
    assert group_and.api_name in group_and_api_names
    assert new_group_and_api_name in group_and_api_names

    group_and.refresh_from_db()
    assert FieldTemplateRuleGroupAnd.objects.filter(
        id=group_and.id,
        api_name=group_and.api_name,
        group_or=group_or,
    ).exists()
    assert FieldTemplateRuleGroupAnd.objects.filter(
        api_name=new_group_and_api_name,
        group_or=group_or,
    ).exists()
    assert group_or.groups_and.count() == 2


def test_update__remove_group_and__ok(mocker, api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    task = template.tasks.first()
    source_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Source field',
        order=1,
        task=task,
        api_name='field-1',
        template=template,
        account=account,
    )
    target_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Target field',
        order=2,
        task=task,
        api_name='field-2',
        template=template,
        account=account,
    )
    ruleset, group_or, group_and = _create_show_ruleset(
        account=account,
        template=template,
        field=target_field,
        source_field_api_name=source_field.api_name,
    )
    extra_group_and = FieldTemplateRuleGroupAnd.objects.create(
        account=account,
        template=template,
        group_or=group_or,
        api_name='field-group-and-2',
        field=source_field.api_name,
        operator=FieldRuleOperator.NOT_EQUAL,
        value='no',
    )
    extra_group_and_id = extra_group_and.id
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
            'kickoff': {},
            'tasks': [
                {
                    'id': task.id,
                    'api_name': task.api_name,
                    'number': task.number,
                    'name': task.name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [
                        {
                            'name': source_field.name,
                            'type': source_field.type,
                            'order': source_field.order,
                            'api_name': source_field.api_name,
                        },
                        {
                            'name': target_field.name,
                            'type': target_field.type,
                            'order': target_field.order,
                            'api_name': target_field.api_name,
                            'rulesets': [
                                {
                                    'api_name': ruleset.api_name,
                                    'name': ruleset.name,
                                    'type': ruleset.type,
                                    'groups_or': [
                                        {
                                            'api_name': group_or.api_name,
                                            'groups_and': [
                                                {
                                                    'api_name': (
                                                        group_and.api_name
                                                    ),
                                                    'field': group_and.field,
                                                    'operator': (
                                                        group_and.operator
                                                    ),
                                                    'value': group_and.value,
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
    assert response.status_code == 200
    field_data = _field_by_api_name(
        response.data['tasks'][0]['fields'],
        target_field.api_name,
    )
    groups_and = field_data['rulesets'][0]['groups_or'][0]['groups_and']
    assert len(groups_and) == 1
    assert groups_and[0]['api_name'] == group_and.api_name
    assert group_or.groups_and.count() == 1
    assert not FieldTemplateRuleGroupAnd.objects.filter(
        id=extra_group_and_id,
    ).exists()


def test_update__remove_group_or__ok(mocker, api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    task = template.tasks.first()
    source_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Source field',
        order=1,
        task=task,
        api_name='field-1',
        template=template,
        account=account,
    )
    target_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Target field',
        order=2,
        task=task,
        api_name='field-2',
        template=template,
        account=account,
    )
    ruleset, group_or, group_and = _create_show_ruleset(
        account=account,
        template=template,
        field=target_field,
        source_field_api_name=source_field.api_name,
    )
    extra_group_or = FieldTemplateRuleGroupOr.objects.create(
        account=account,
        template=template,
        ruleset=ruleset,
        api_name='field-group-or-2',
    )
    extra_group_and = FieldTemplateRuleGroupAnd.objects.create(
        account=account,
        template=template,
        group_or=extra_group_or,
        api_name='field-group-and-2',
        field=source_field.api_name,
        operator=FieldRuleOperator.NOT_EQUAL,
        value='no',
    )
    extra_group_or_id = extra_group_or.id
    extra_group_and_id = extra_group_and.id
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
            'kickoff': {},
            'tasks': [
                {
                    'id': task.id,
                    'api_name': task.api_name,
                    'number': task.number,
                    'name': task.name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [
                        {
                            'name': source_field.name,
                            'type': source_field.type,
                            'order': source_field.order,
                            'api_name': source_field.api_name,
                        },
                        {
                            'name': target_field.name,
                            'type': target_field.type,
                            'order': target_field.order,
                            'api_name': target_field.api_name,
                            'rulesets': [
                                {
                                    'api_name': ruleset.api_name,
                                    'name': ruleset.name,
                                    'type': ruleset.type,
                                    'groups_or': [
                                        {
                                            'api_name': group_or.api_name,
                                            'groups_and': [
                                                {
                                                    'api_name': (
                                                        group_and.api_name
                                                    ),
                                                    'field': group_and.field,
                                                    'operator': (
                                                        group_and.operator
                                                    ),
                                                    'value': group_and.value,
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
    assert response.status_code == 200
    field_data = _field_by_api_name(
        response.data['tasks'][0]['fields'],
        target_field.api_name,
    )
    groups_or = field_data['rulesets'][0]['groups_or']
    assert len(groups_or) == 1
    assert groups_or[0]['api_name'] == group_or.api_name
    assert ruleset.groups_or.count() == 1
    assert not FieldTemplateRuleGroupOr.objects.filter(
        id=extra_group_or_id,
    ).exists()
    assert not FieldTemplateRuleGroupAnd.objects.filter(
        id=extra_group_and_id,
    ).exists()


def test_update__remove_ruleset__ok(mocker, api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    task = template.tasks.first()
    source_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Source field',
        order=1,
        task=task,
        api_name='field-1',
        template=template,
        account=account,
    )
    target_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Target field',
        order=2,
        task=task,
        api_name='field-2',
        template=template,
        account=account,
    )
    ruleset, group_or, group_and = _create_show_ruleset(
        account=account,
        template=template,
        field=target_field,
        source_field_api_name=source_field.api_name,
    )
    extra_ruleset, extra_group_or, extra_group_and = _create_show_ruleset(
        account=account,
        template=template,
        field=target_field,
        source_field_api_name=source_field.api_name,
        ruleset_api_name='field-ruleset-2',
        group_or_api_name='field-group-or-2',
        group_and_api_name='field-group-and-2',
        name='Second ruleset',
        order=1,
    )
    extra_ruleset_id = extra_ruleset.id
    extra_group_or_id = extra_group_or.id
    extra_group_and_id = extra_group_and.id
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
            'kickoff': {},
            'tasks': [
                {
                    'id': task.id,
                    'api_name': task.api_name,
                    'number': task.number,
                    'name': task.name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [
                        {
                            'name': source_field.name,
                            'type': source_field.type,
                            'order': source_field.order,
                            'api_name': source_field.api_name,
                        },
                        {
                            'name': target_field.name,
                            'type': target_field.type,
                            'order': target_field.order,
                            'api_name': target_field.api_name,
                            'rulesets': [
                                {
                                    'api_name': ruleset.api_name,
                                    'name': ruleset.name,
                                    'type': ruleset.type,
                                    'groups_or': [
                                        {
                                            'api_name': group_or.api_name,
                                            'groups_and': [
                                                {
                                                    'api_name': (
                                                        group_and.api_name
                                                    ),
                                                    'field': group_and.field,
                                                    'operator': (
                                                        group_and.operator
                                                    ),
                                                    'value': group_and.value,
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
    assert response.status_code == 200
    field_data = _field_by_api_name(
        response.data['tasks'][0]['fields'],
        target_field.api_name,
    )
    assert len(field_data['rulesets']) == 1
    assert field_data['rulesets'][0]['api_name'] == ruleset.api_name
    assert target_field.rulesets.count() == 1
    assert not FieldTemplateRuleSet.objects.filter(
        id=extra_ruleset_id,
    ).exists()
    assert not FieldTemplateRuleGroupOr.objects.filter(
        id=extra_group_or_id,
    ).exists()
    assert not FieldTemplateRuleGroupAnd.objects.filter(
        id=extra_group_and_id,
    ).exists()


def test_update__replace_ruleset_new_api_name__ok(mocker, api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    task = template.tasks.first()
    source_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Source field',
        order=1,
        task=task,
        api_name='field-1',
        template=template,
        account=account,
    )
    target_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Target field',
        order=2,
        task=task,
        api_name='field-2',
        template=template,
        account=account,
    )
    ruleset, group_or, group_and = _create_show_ruleset(
        account=account,
        template=template,
        field=target_field,
        source_field_api_name=source_field.api_name,
    )
    old_ruleset_id = ruleset.id
    new_api_name = 'field-ruleset-new'
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
            'kickoff': {},
            'tasks': [
                {
                    'id': task.id,
                    'api_name': task.api_name,
                    'number': task.number,
                    'name': task.name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [
                        {
                            'name': source_field.name,
                            'type': source_field.type,
                            'order': source_field.order,
                            'api_name': source_field.api_name,
                        },
                        {
                            'name': target_field.name,
                            'type': target_field.type,
                            'order': target_field.order,
                            'api_name': target_field.api_name,
                            'rulesets': [
                                {
                                    'api_name': new_api_name,
                                    'name': ruleset.name,
                                    'type': ruleset.type,
                                    'groups_or': [
                                        {
                                            'api_name': group_or.api_name,
                                            'groups_and': [
                                                {
                                                    'api_name': (
                                                        group_and.api_name
                                                    ),
                                                    'field': group_and.field,
                                                    'operator': (
                                                        group_and.operator
                                                    ),
                                                    'value': group_and.value,
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
    assert response.status_code == 200
    field_data = _field_by_api_name(
        response.data['tasks'][0]['fields'],
        target_field.api_name,
    )
    assert len(field_data['rulesets']) == 1
    ruleset_data = field_data['rulesets'][0]
    assert ruleset_data['api_name'] == new_api_name
    assert not FieldTemplateRuleSet.objects.filter(id=old_ruleset_id).exists()
    new_ruleset = FieldTemplateRuleSet.objects.get(api_name=new_api_name)
    assert new_ruleset.id != old_ruleset_id
    assert new_ruleset.field_id == target_field.id


def test_update__unspecified_ruleset_api_name__create_new(mocker, api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    task = template.tasks.first()
    source_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Source field',
        order=1,
        task=task,
        api_name='field-1',
        template=template,
        account=account,
    )
    target_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Target field',
        order=2,
        task=task,
        api_name='field-2',
        template=template,
        account=account,
    )
    ruleset, _group_or, group_and = _create_show_ruleset(
        account=account,
        template=template,
        field=target_field,
        source_field_api_name=source_field.api_name,
    )
    old_ruleset_id = ruleset.id
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
            'kickoff': {},
            'tasks': [
                {
                    'id': task.id,
                    'api_name': task.api_name,
                    'number': task.number,
                    'name': task.name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [
                        {
                            'name': source_field.name,
                            'type': source_field.type,
                            'order': source_field.order,
                            'api_name': source_field.api_name,
                        },
                        {
                            'name': target_field.name,
                            'type': target_field.type,
                            'order': target_field.order,
                            'api_name': target_field.api_name,
                            'rulesets': [
                                {
                                    'name': ruleset.name,
                                    'type': ruleset.type,
                                    'groups_or': [
                                        {
                                            'groups_and': [
                                                {
                                                    'field': group_and.field,
                                                    'operator': (
                                                        group_and.operator
                                                    ),
                                                    'value': group_and.value,
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
    assert response.status_code == 200
    field_data = _field_by_api_name(
        response.data['tasks'][0]['fields'],
        target_field.api_name,
    )
    assert len(field_data['rulesets']) == 1
    ruleset_data = field_data['rulesets'][0]
    assert ruleset_data['api_name']
    assert ruleset_data['api_name'] != ruleset.api_name
    assert not FieldTemplateRuleSet.objects.filter(id=old_ruleset_id).exists()
    new_ruleset = FieldTemplateRuleSet.objects.get(
        api_name=ruleset_data['api_name'],
    )
    assert new_ruleset.id != old_ruleset_id


def test_update__two_rulesets_on_field__ok(mocker, api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    task = template.tasks.first()
    source_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Source field',
        order=1,
        task=task,
        api_name='field-1',
        template=template,
        account=account,
    )
    target_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Target field',
        order=2,
        task=task,
        api_name='field-2',
        template=template,
        account=account,
    )
    ruleset_1, group_or_1, group_and_1 = _create_show_ruleset(
        account=account,
        template=template,
        field=target_field,
        source_field_api_name=source_field.api_name,
        ruleset_api_name='field-ruleset-1',
        group_or_api_name='field-group-or-1',
        group_and_api_name='field-group-and-1',
        name='First ruleset',
        order=0,
    )
    ruleset_2, group_or_2, group_and_2 = _create_show_ruleset(
        account=account,
        template=template,
        field=target_field,
        source_field_api_name=source_field.api_name,
        ruleset_api_name='field-ruleset-2',
        group_or_api_name='field-group-or-2',
        group_and_api_name='field-group-and-2',
        name='Second ruleset',
        order=1,
    )
    new_name_1 = 'Updated first ruleset'
    new_name_2 = 'Updated second ruleset'
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
            'kickoff': {},
            'tasks': [
                {
                    'id': task.id,
                    'api_name': task.api_name,
                    'number': task.number,
                    'name': task.name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [
                        {
                            'name': source_field.name,
                            'type': source_field.type,
                            'order': source_field.order,
                            'api_name': source_field.api_name,
                        },
                        {
                            'name': target_field.name,
                            'type': target_field.type,
                            'order': target_field.order,
                            'api_name': target_field.api_name,
                            'rulesets': [
                                {
                                    'api_name': ruleset_1.api_name,
                                    'name': new_name_1,
                                    'type': ruleset_1.type,
                                    'order': ruleset_1.order,
                                    'groups_or': [
                                        {
                                            'api_name': group_or_1.api_name,
                                            'groups_and': [
                                                {
                                                    'api_name': (
                                                        group_and_1.api_name
                                                    ),
                                                    'field': group_and_1.field,
                                                    'operator': (
                                                        group_and_1.operator
                                                    ),
                                                    'value': group_and_1.value,
                                                },
                                            ],
                                        },
                                    ],
                                },
                                {
                                    'api_name': ruleset_2.api_name,
                                    'name': new_name_2,
                                    'type': ruleset_2.type,
                                    'order': ruleset_2.order,
                                    'groups_or': [
                                        {
                                            'api_name': group_or_2.api_name,
                                            'groups_and': [
                                                {
                                                    'api_name': (
                                                        group_and_2.api_name
                                                    ),
                                                    'field': group_and_2.field,
                                                    'operator': (
                                                        group_and_2.operator
                                                    ),
                                                    'value': group_and_2.value,
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
    assert response.status_code == 200
    field_data = _field_by_api_name(
        response.data['tasks'][0]['fields'],
        target_field.api_name,
    )
    assert len(field_data['rulesets']) == 2
    ruleset_by_api_name = {
        item['api_name']: item for item in field_data['rulesets']
    }
    assert ruleset_by_api_name[ruleset_1.api_name]['name'] == new_name_1
    assert ruleset_by_api_name[ruleset_2.api_name]['name'] == new_name_2

    ruleset_1.refresh_from_db()
    ruleset_2.refresh_from_db()
    assert ruleset_1.id == FieldTemplateRuleSet.objects.get(
        api_name=ruleset_1.api_name,
    ).id
    assert ruleset_2.id == FieldTemplateRuleSet.objects.get(
        api_name=ruleset_2.api_name,
    ).id
    assert ruleset_1.name == new_name_1
    assert ruleset_2.name == new_name_2


def test_update__show_missing_field__validation_error(mocker, api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    task = template.tasks.first()
    source_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Source field',
        order=1,
        task=task,
        api_name='field-1',
        template=template,
        account=account,
    )
    target_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Target field',
        order=2,
        task=task,
        api_name='field-2',
        template=template,
        account=account,
    )
    ruleset, group_or, group_and = _create_show_ruleset(
        account=account,
        template=template,
        field=target_field,
        source_field_api_name=source_field.api_name,
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
            'kickoff': {},
            'tasks': [
                {
                    'id': task.id,
                    'api_name': task.api_name,
                    'number': task.number,
                    'name': task.name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [
                        {
                            'name': source_field.name,
                            'type': source_field.type,
                            'order': source_field.order,
                            'api_name': source_field.api_name,
                        },
                        {
                            'name': target_field.name,
                            'type': target_field.type,
                            'order': target_field.order,
                            'api_name': target_field.api_name,
                            'rulesets': [
                                {
                                    'api_name': ruleset.api_name,
                                    'name': ruleset.name,
                                    'type': FieldRuleType.SHOW,
                                    'groups_or': [
                                        {
                                            'api_name': group_or.api_name,
                                            'groups_and': [
                                                {
                                                    'api_name': (
                                                        group_and.api_name
                                                    ),
                                                    'operator': (
                                                        group_and.operator
                                                    ),
                                                    'value': group_and.value,
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


def test_update__show_field_null__validation_error(mocker, api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    task = template.tasks.first()
    source_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Source field',
        order=1,
        task=task,
        api_name='field-1',
        template=template,
        account=account,
    )
    target_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Target field',
        order=2,
        task=task,
        api_name='field-2',
        template=template,
        account=account,
    )
    ruleset, group_or, group_and = _create_show_ruleset(
        account=account,
        template=template,
        field=target_field,
        source_field_api_name=source_field.api_name,
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
            'kickoff': {},
            'tasks': [
                {
                    'id': task.id,
                    'api_name': task.api_name,
                    'number': task.number,
                    'name': task.name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [
                        {
                            'name': source_field.name,
                            'type': source_field.type,
                            'order': source_field.order,
                            'api_name': source_field.api_name,
                        },
                        {
                            'name': target_field.name,
                            'type': target_field.type,
                            'order': target_field.order,
                            'api_name': target_field.api_name,
                            'rulesets': [
                                {
                                    'api_name': ruleset.api_name,
                                    'name': ruleset.name,
                                    'type': FieldRuleType.SHOW,
                                    'groups_or': [
                                        {
                                            'api_name': group_or.api_name,
                                            'groups_and': [
                                                {
                                                    'api_name': (
                                                        group_and.api_name
                                                    ),
                                                    'field': None,
                                                    'operator': (
                                                        group_and.operator
                                                    ),
                                                    'value': group_and.value,
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


def test_update__missing_name__validation_error(mocker, api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    task = template.tasks.first()
    source_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Source field',
        order=1,
        task=task,
        api_name='field-1',
        template=template,
        account=account,
    )
    target_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Target field',
        order=2,
        task=task,
        api_name='field-2',
        template=template,
        account=account,
    )
    ruleset, group_or, group_and = _create_show_ruleset(
        account=account,
        template=template,
        field=target_field,
        source_field_api_name=source_field.api_name,
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
            'kickoff': {},
            'tasks': [
                {
                    'id': task.id,
                    'api_name': task.api_name,
                    'number': task.number,
                    'name': task.name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [
                        {
                            'name': source_field.name,
                            'type': source_field.type,
                            'order': source_field.order,
                            'api_name': source_field.api_name,
                        },
                        {
                            'name': target_field.name,
                            'type': target_field.type,
                            'order': target_field.order,
                            'api_name': target_field.api_name,
                            'rulesets': [
                                {
                                    'api_name': ruleset.api_name,
                                    'type': ruleset.type,
                                    'groups_or': [
                                        {
                                            'api_name': group_or.api_name,
                                            'groups_and': [
                                                {
                                                    'api_name': (
                                                        group_and.api_name
                                                    ),
                                                    'field': group_and.field,
                                                    'operator': (
                                                        group_and.operator
                                                    ),
                                                    'value': group_and.value,
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
    assert response.data['message'] == 'Name: this field is required.'


def test_update__duplicate_ruleset_api_name__validation_error(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    task = template.tasks.first()
    step_name = task.name
    ruleset_api_name = 'field-ruleset-1'
    field_name = 'Broken field'
    source_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Source field',
        order=1,
        task=task,
        api_name='field-1',
        template=template,
        account=account,
    )
    target_field = FieldTemplate.objects.create(
        type=FieldType.STRING,
        name='Target field',
        order=2,
        task=task,
        api_name='field-2',
        template=template,
        account=account,
    )
    ruleset, group_or, group_and = _create_show_ruleset(
        account=account,
        template=template,
        field=target_field,
        source_field_api_name=source_field.api_name,
        ruleset_api_name=ruleset_api_name,
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
            'kickoff': {},
            'tasks': [
                {
                    'id': task.id,
                    'api_name': task.api_name,
                    'number': task.number,
                    'name': step_name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fields': [
                        {
                            'name': source_field.name,
                            'type': source_field.type,
                            'order': source_field.order,
                            'api_name': source_field.api_name,
                        },
                        {
                            'name': target_field.name,
                            'type': target_field.type,
                            'order': target_field.order,
                            'api_name': target_field.api_name,
                            'rulesets': [
                                {
                                    'api_name': ruleset.api_name,
                                    'name': ruleset.name,
                                    'type': ruleset.type,
                                    'groups_or': [
                                        {
                                            'api_name': group_or.api_name,
                                            'groups_and': [
                                                {
                                                    'api_name': (
                                                        group_and.api_name
                                                    ),
                                                    'field': group_and.field,
                                                    'operator': (
                                                        group_and.operator
                                                    ),
                                                    'value': group_and.value,
                                                },
                                            ],
                                        },
                                    ],
                                },
                            ],
                        },
                        {
                            'name': field_name,
                            'type': FieldType.STRING,
                            'order': 3,
                            'api_name': 'field-3',
                            'rulesets': [
                                {
                                    'api_name': ruleset_api_name,
                                    'name': 'Duplicate ruleset',
                                    'type': FieldRuleType.SHOW,
                                    'groups_or': [
                                        {
                                            'groups_and': [
                                                {
                                                    'field': (
                                                        source_field.api_name
                                                    ),
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
    message = MSG_PT_0075(
        task_name=step_name,
        field_name=field_name,
        api_name=ruleset_api_name,
    )
    assert response.data['message'] == message
