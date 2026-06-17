import pytest

from src.processes.enums import (
    FieldSetLayout,
    FieldSetRuleType,
    FieldType,
    LabelPosition,
    OwnerRole,
    OwnerType,
    PerformerType,
)
from src.processes.tests.fixtures import (
    create_test_shared_fieldset,
    create_test_owner,
    create_test_account,
)
from src.processes.models.templates.fields import (
    FieldTemplate,
    FieldTemplateSelection,
)

pytestmark = pytest.mark.django_db


def test_clone__kickoff_and_task_fieldsets__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    shared = create_test_shared_fieldset(
        account=account,
        name='My Fieldset',
        description='Some description',
        label_position=LabelPosition.TOP,
        layout=FieldSetLayout.VERTICAL,
    )
    api_client.token_authenticate(user)

    create_response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'is_active': False,
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {
                'fieldsets': [
                    {
                        'shared_fieldset_id': shared.id,
                        'order': 1,
                        'title': 'My Fieldset Title',
                        'description': 'My Fieldset Description',
                    },
                ],
            },
            'tasks': [
                {
                    'number': 1,
                    'name': 'Step 1',
                    'api_name': 'task-1',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fieldsets': [
                        {
                            'shared_fieldset_id': shared.id,
                            'order': 2,
                            'title': 'My Fieldset Title 2',
                            'description': 'My Fieldset Description 2',
                        },
                    ],
                },
            ],
        },
    )
    assert create_response.status_code == 200
    template_id = create_response.data['id']

    # act
    response = api_client.post(f'/templates/{template_id}/clone')

    # assert
    assert response.status_code == 200
    assert response.data['id'] != template_id

    assert len(response.data['kickoff']['fieldsets']) == 1
    clone_fieldsets_1 = response.data['kickoff']['fieldsets'][0]
    assert clone_fieldsets_1['name'] == shared.name
    assert clone_fieldsets_1['title'] == 'My Fieldset Title'
    assert clone_fieldsets_1['description'] == 'My Fieldset Description'
    assert clone_fieldsets_1['label_position'] == LabelPosition.TOP
    assert clone_fieldsets_1['layout'] == FieldSetLayout.VERTICAL
    assert clone_fieldsets_1['order'] == 1
    assert isinstance(clone_fieldsets_1['fields'], list)
    assert clone_fieldsets_1['rules'] == []
    assert clone_fieldsets_1['shared_fieldset_id'] == shared.id

    assert len(response.data['tasks'][0]['fieldsets']) == 1
    clone_fieldsets_2 = response.data['tasks'][0]['fieldsets'][0]
    assert clone_fieldsets_2['name'] == shared.name
    assert clone_fieldsets_2['title'] == 'My Fieldset Title 2'
    assert clone_fieldsets_2['description'] == 'My Fieldset Description 2'
    assert clone_fieldsets_2['label_position'] == LabelPosition.TOP
    assert clone_fieldsets_2['layout'] == FieldSetLayout.VERTICAL
    assert clone_fieldsets_2['order'] == 2
    assert isinstance(clone_fieldsets_2['fields'], list)
    assert clone_fieldsets_2['rules'] == []
    assert clone_fieldsets_2['shared_fieldset_id'] == shared.id


def test_clone__fieldset_with_fields__ok(api_client):

    """Cloning copies field records belonging to the fieldset."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    shared = create_test_shared_fieldset(account=account)
    api_client.token_authenticate(user)

    create_response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'is_active': False,
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {
                'fieldsets': [
                    {
                        'shared_fieldset_id': shared.id,
                        'order': 1,
                        'title': 'Fields Fieldset Title',
                        'description': 'Fields Fieldset Description',
                    },
                ],
            },
            'tasks': [
                {
                    'number': 1,
                    'name': 'Step 1',
                    'api_name': 'task-1',
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
    assert create_response.status_code == 200
    template_id = create_response.data['id']

    # act
    response = api_client.post(f'/templates/{template_id}/clone')

    # assert
    assert response.status_code == 200
    field = shared.fields.first()
    fields = response.data['kickoff']['fieldsets'][0]['fields']
    assert len(fields) == 1
    assert fields[0]['name'] == field.name
    assert fields[0]['description'] == (field.description or '')
    assert fields[0]['type'] == field.type
    assert fields[0]['is_required'] == field.is_required
    assert fields[0]['is_hidden'] == field.is_hidden
    assert fields[0]['order'] == field.order
    assert fields[0]['default'] == field.default


def test_clone__fieldset_with_selections__ok(api_client):

    """Cloning copies FieldTemplateSelection records
    for dropdown fields in a fieldset."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    shared = create_test_shared_fieldset(
        account=user.account,
        name='Fieldset with dropdown',
    )
    shared.fields.all().delete()
    field = FieldTemplate.objects.create(
        fieldset=shared,
        account=user.account,
        name='Dropdown field',
        type=FieldType.DROPDOWN,
        order=1,
    )
    FieldTemplateSelection.objects.create(
        field_template=field,
        value='Option A',
    )
    FieldTemplateSelection.objects.create(
        field_template=field,
        value='Option B',
    )
    api_client.token_authenticate(user)

    create_response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'is_active': False,
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {
                'fieldsets': [
                    {
                        'shared_fieldset_id': shared.id,
                    },
                ],
            },
            'tasks': [
                {
                    'number': 1,
                    'name': 'Step 1',
                    'api_name': 'task-1',
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
    assert create_response.status_code == 200
    template_id = create_response.data['id']

    # act
    response = api_client.post(f'/templates/{template_id}/clone')

    # assert
    assert response.status_code == 200
    field = response.data['kickoff']['fieldsets'][0]['fields'][0]
    assert field['type'] == FieldType.DROPDOWN
    selections = field['selections']
    assert len(selections) == 2
    assert selections[0]['value'] == 'Option A'
    assert selections[1]['value'] == 'Option B'


def test_clone__fieldset_with_rules__ok(api_client):

    """Cloning copies rules and preserves the rule-field relationships."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    shared = create_test_shared_fieldset(
        account=user.account,
        name='Fieldset with rules',
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='100',
    )
    field = shared.fields.first()
    rule = shared.rules.first()
    field.rules.add(rule)
    api_client.token_authenticate(user)

    create_response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'is_active': False,
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {
                'fieldsets': [
                    {
                        'shared_fieldset_id': shared.id,
                    },
                ],
            },
            'tasks': [
                {
                    'number': 1,
                    'name': 'Step 1',
                    'api_name': 'task-1',
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
    assert create_response.status_code == 200
    template_id = create_response.data['id']

    # act
    response = api_client.post(f'/templates/{template_id}/clone')

    # assert
    assert response.status_code == 200
    fieldset = response.data['kickoff']['fieldsets'][0]
    rules = fieldset['rules']
    assert len(rules) == 1
    rule_data = rules[0]
    assert rule_data['type'] == FieldSetRuleType.SUM_EQUAL
    assert rule_data['value'] == '100'
    clone_field_api_names = [f['api_name'] for f in fieldset['fields']]
    assert len(clone_field_api_names) == 1
    assert rule_data['fields'] == clone_field_api_names


def test_clone__kickoff_multiple_fieldsets__ok(api_client):

    """Cloning a template with multiple fieldsets copies all of them."""

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)

    shared_1 = create_test_shared_fieldset(
        account=user.account,
        name='Fieldset One',
    )
    shared_2 = create_test_shared_fieldset(
        account=user.account,
        name='Fieldset Two',
    )

    create_response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'is_active': False,
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {
                'fieldsets': [
                    {
                        'shared_fieldset_id': shared_1.id,
                        'order': 1,
                        'title': 'Fieldset One Title',
                        'description': 'Fieldset One Description',
                    },
                    {
                        'shared_fieldset_id': shared_2.id,
                        'order': 2,
                        'title': 'Fieldset Two Title',
                        'description': 'Fieldset Two Description',
                    },
                ],
            },
            'tasks': [
                {
                    'number': 1,
                    'name': 'Step 1',
                    'api_name': 'task-1',
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
    assert create_response.status_code == 200
    template_id = create_response.data['id']

    # act
    response = api_client.post(f'/templates/{template_id}/clone')

    # assert
    assert response.status_code == 200
    fieldsets = response.data['kickoff']['fieldsets']
    assert len(fieldsets) == 2
    fieldset_1 = fieldsets[0]
    assert fieldset_1['name'] == shared_1.name
    fieldset_2 = fieldsets[1]
    assert fieldset_2['name'] == shared_2.name


def test_clone__no_fieldsets__ok(api_client):

    """Cloning a template without fieldsets still works
    and creates no fieldsets on the clone."""

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)

    create_response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'is_active': False,
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
                    'name': 'Step 1',
                    'api_name': 'task-1',
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
    assert create_response.status_code == 200
    template_id = create_response.data['id']

    # act
    response = api_client.post(f'/templates/{template_id}/clone')

    # assert
    assert response.status_code == 200
    assert response.data['kickoff']['fieldsets'] == []


def test_clone__fieldset_rule_multi_fields__ok(api_client):

    """Cloning preserves a rule linked to multiple fields."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    shared = create_test_shared_fieldset(
        account=account,
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='200',
    )
    shared.fields.all().delete()
    field_1 = FieldTemplate.objects.create(
        fieldset=shared,
        account=user.account,
        name='Amount A',
        type=FieldType.NUMBER,
        order=3,
    )
    field_2 = FieldTemplate.objects.create(
        fieldset=shared,
        account=user.account,
        name='Amount B',
        type=FieldType.NUMBER,
        order=2,
    )
    rule = shared.rules.first()
    field_1.rules.add(rule)
    field_2.rules.add(rule)

    api_client.token_authenticate(user)
    create_response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'is_active': False,
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {
                'fieldsets': [
                    {
                        'shared_fieldset_id': shared.id,
                        'order': 1,
                        'title': 'Multi-field Fieldset Title',
                        'description': 'Multi-field Fieldset Description',
                    },
                ],
            },
            'tasks': [
                {
                    'number': 1,
                    'name': 'Step 1',
                    'api_name': 'task-1',
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
    assert create_response.status_code == 200
    template_id = create_response.data['id']

    # act
    response = api_client.post(f'/templates/{template_id}/clone')

    # assert
    assert response.status_code == 200
    clone_fieldsets = response.data['kickoff']['fieldsets'][0]
    rule_data = clone_fieldsets['rules'][0]
    assert rule_data['type'] == FieldSetRuleType.SUM_EQUAL
    assert rule_data['value'] == '200'
    clone_fields = clone_fieldsets['fields']
    clone_field_api_names = [f['api_name'] for f in clone_fields]
    assert set(rule_data['fields']) == set(clone_field_api_names)
