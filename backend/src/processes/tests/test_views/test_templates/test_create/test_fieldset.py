import pytest

from src.processes.enums import (
    FieldType,
    OwnerRole,
    OwnerType,
    PerformerType, FieldSetRuleOperator,
)
from src.processes.models.templates.fieldset import FieldsetTemplate
from src.processes.models.templates.template import Template
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_fieldset_template,
    create_test_shared_fieldset,
    create_test_template,
    create_test_user,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_create__kickoff_fieldset_only_required_data__ok(
    mocker,
    api_client,
):

    """ Creating a template with one fieldset linked to kickoff
        creates FieldsetTemplate linked to the kickoff. """

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    shared_fieldset = create_test_shared_fieldset(account=account)
    shared_fieldset.fields.all().delete()
    request_data = {
        'name': 'Template with fieldset',
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
                'role': OwnerRole.OWNER,
            },
        ],
        'is_active': True,
        'kickoff': {
            'fieldsets': [
                {
                    'shared_fieldset_id': shared_fieldset.id,
                },
            ],
        },
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
    template = Template.objects.get(id=response.data['id'])
    kickoff = template.kickoff_instance
    assert FieldsetTemplate.objects.get(
        kickoff=kickoff,
        shared_fieldset=shared_fieldset,
        is_shared=False,
    )

    kickoff_data = response.data['kickoff']
    assert len(kickoff_data['fieldsets']) == 1
    fieldset_data = kickoff_data['fieldsets'][0]
    assert fieldset_data['shared_fieldset_id'] == shared_fieldset.id
    assert fieldset_data['order'] == 0
    assert fieldset_data['name'] == shared_fieldset.name
    assert fieldset_data['description'] == shared_fieldset.description
    assert fieldset_data['title'] == shared_fieldset.name
    assert fieldset_data['api_name'] != shared_fieldset.api_name
    assert fieldset_data['label_position'] == shared_fieldset.label_position
    assert fieldset_data['layout'] == shared_fieldset.layout

    assert fieldset_data['rulesets'] == []
    assert fieldset_data['fields'] == []


def test_create__kickoff_fieldset_all_fieldset_data__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    fs_title = 'Some title'
    fs_description = 'Some desc'
    fs_order = 3
    fs_api_name = 'fs-some-api-name'
    shared_fieldset = create_test_shared_fieldset(
        account=account,
        rule_value='500',
        rule_operator=FieldSetRuleOperator.SUM_EQUAL,
    )
    shared_field = shared_fieldset.fields.first()
    shared_ruleset = shared_fieldset.rulesets.first()
    shared_ruleset.fields.add(shared_field)
    shared_group_or = shared_ruleset.groups_or.first()
    shared_group_and = shared_group_or.groups_and.first()
    request_data = {
        'name': 'Template with fieldset',
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
                'role': OwnerRole.OWNER,
            },
        ],
        'is_active': True,
        'kickoff': {
            'fieldsets': [
                {
                    'shared_fieldset_id': shared_fieldset.id,
                    'order': fs_order,
                    'title': fs_title,
                    'description': fs_description,
                    'api_name': fs_api_name,
                },
            ],
        },
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
    template = Template.objects.get(id=response.data['id'])
    kickoff = template.kickoff_instance
    fieldset = FieldsetTemplate.objects.get(
        kickoff=kickoff,
        shared_fieldset=shared_fieldset,
        is_shared=False,
        api_name=fs_api_name,
    )
    field = fieldset.fields.first()
    ruleset = fieldset.rulesets.first()
    group_or = ruleset.groups_or.first()
    group_and = group_or.groups_and.first()

    kickoff_data = response.data['kickoff']
    assert len(kickoff_data['fieldsets']) == 1
    fieldset_data = kickoff_data['fieldsets'][0]
    assert fieldset_data['shared_fieldset_id'] == shared_fieldset.id
    assert fieldset_data['order'] == fs_order
    assert fieldset_data['title'] == fs_title
    assert fieldset_data['description'] == fs_description
    assert fieldset_data['name'] == shared_fieldset.name
    assert fieldset_data['api_name'] == fs_api_name
    assert fieldset_data['label_position'] == shared_fieldset.label_position
    assert fieldset_data['layout'] == shared_fieldset.layout

    assert len(fieldset_data['rulesets']) == 1
    ruleset_data = fieldset_data['rulesets'][0]
    assert ruleset_data['type'] == shared_ruleset.type
    assert ruleset_data['api_name'] != shared_ruleset.api_name
    assert ruleset_data['fields'] == [field.api_name]

    assert len(ruleset_data['groups_or']) == 1
    groups_or_data = ruleset_data['groups_or'][0]
    assert groups_or_data['api_name'] != shared_group_or.api_name
    assert groups_or_data['api_name'] == group_or.api_name

    assert len(groups_or_data['groups_and']) == 1
    group_and_data = groups_or_data['groups_and'][0]
    assert group_and_data['api_name'] != shared_group_and.api_name
    assert group_and_data['api_name'] == group_and.api_name
    assert group_and_data['operator'] == group_and.operator
    assert group_and_data['value'] == group_and.value

    assert len(fieldset_data['fields']) == 1
    field_data = fieldset_data['fields'][0]
    assert field_data['name'] == shared_field.name
    assert field_data['type'] == shared_field.type
    assert field_data['order'] == shared_field.order
    assert field_data['is_required'] == shared_field.is_required
    assert field_data['is_hidden'] == shared_field.is_hidden
    assert field_data['description'] == ''
    assert field_data['default'] == ''
    assert field_data['api_name'] != shared_field.api_name
    assert field_data['api_name'] == field.api_name


def test_create__kickoff_with_empty_fieldsets__no_created(
    mocker,
    api_client,
):

    """ Creating a template with empty fieldsets list does not
        create any FieldsetTemplateKickoff records. """

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    request_data = {
        'name': 'Template no fieldsets',
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
                'role': OwnerRole.OWNER,
            },
        ],
        'is_active': True,
        'kickoff': {
            'fieldsets': [],
        },
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
    template = Template.objects.get(id=response.data['id'])
    kickoff = template.kickoff_instance
    assert FieldsetTemplate.objects.filter(
        kickoff=kickoff,
    ).count() == 0


def test_create__task_fieldset_only_required_data__ok(
    mocker,
    api_client,
):

    """ Creating a template with one fieldset linked to a task
        creates FieldsetTemplate linked to the task. """

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    shared_fieldset = create_test_shared_fieldset(account=account)
    shared_fieldset.fields.all().delete()

    request_data = {
        'name': 'Template with task fieldset',
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
                'fieldsets': [
                    {
                        'shared_fieldset_id': shared_fieldset.id,
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
    template = Template.objects.get(id=response.data['id'])
    task = template.tasks.first()
    assert FieldsetTemplate.objects.get(
        task=task,
        shared_fieldset=shared_fieldset,
        is_shared=False,
    )

    task_data = response.data['tasks'][0]
    assert len(task_data['fieldsets']) == 1
    fieldset_data = task_data['fieldsets'][0]
    assert fieldset_data['shared_fieldset_id'] == shared_fieldset.id
    assert fieldset_data['order'] == 0
    assert fieldset_data['name'] == shared_fieldset.name
    assert fieldset_data['description'] == shared_fieldset.description
    assert fieldset_data['title'] == shared_fieldset.name
    assert fieldset_data['api_name'] != shared_fieldset.api_name
    assert fieldset_data['label_position'] == shared_fieldset.label_position
    assert fieldset_data['layout'] == shared_fieldset.layout

    assert fieldset_data['rulesets'] == []
    assert fieldset_data['fields'] == []


def test_create__task_fieldset_all_fieldset_data__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    fs_title = 'Some title'
    fs_description = 'Some desc'
    fs_order = 3
    fs_api_name = 'fs-some-api-name'
    shared_fieldset = create_test_shared_fieldset(
        account=account,
        rule_value='500',
        rule_operator=FieldSetRuleOperator.SUM_EQUAL,
    )
    shared_field = shared_fieldset.fields.first()
    shared_ruleset = shared_fieldset.rulesets.first()
    shared_ruleset.fields.add(shared_field)
    shared_group_or = shared_ruleset.groups_or.first()
    shared_group_and = shared_group_or.groups_and.first()

    request_data = {
        'name': 'Template with task fieldset',
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
                'fieldsets': [
                    {
                        'shared_fieldset_id': shared_fieldset.id,
                        'order': fs_order,
                        'title': fs_title,
                        'description': fs_description,
                        'api_name': fs_api_name,
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
    template = Template.objects.get(id=response.data['id'])
    task = template.tasks.first()
    fieldset = FieldsetTemplate.objects.get(
        task=task,
        shared_fieldset=shared_fieldset,
        is_shared=False,
        api_name=fs_api_name,
    )
    field = fieldset.fields.first()
    ruleset = fieldset.rulesets.first()
    group_or = ruleset.groups_or.first()
    group_and = group_or.groups_and.first()

    task_data = response.data['tasks'][0]
    assert len(task_data['fieldsets']) == 1
    fieldset_data = task_data['fieldsets'][0]
    assert fieldset_data['shared_fieldset_id'] == shared_fieldset.id
    assert fieldset_data['order'] == fs_order
    assert fieldset_data['title'] == fs_title
    assert fieldset_data['description'] == fs_description
    assert fieldset_data['name'] == shared_fieldset.name
    assert fieldset_data['api_name'] == fs_api_name
    assert fieldset_data['label_position'] == shared_fieldset.label_position
    assert fieldset_data['layout'] == shared_fieldset.layout

    assert len(fieldset_data['rulesets']) == 1
    ruleset_data = fieldset_data['rulesets'][0]
    assert ruleset_data['type'] == shared_ruleset.type
    assert ruleset_data['api_name'] != shared_ruleset.api_name
    assert ruleset_data['fields'] == [field.api_name]

    assert len(ruleset_data['groups_or']) == 1
    groups_or_data = ruleset_data['groups_or'][0]
    assert groups_or_data['api_name'] != shared_group_or.api_name
    assert groups_or_data['api_name'] == group_or.api_name

    assert len(groups_or_data['groups_and']) == 1
    group_and_data = groups_or_data['groups_and'][0]
    assert group_and_data['api_name'] != shared_group_and.api_name
    assert group_and_data['api_name'] == group_and.api_name
    assert group_and_data['operator'] == group_and.operator
    assert group_and_data['value'] == group_and.value

    assert len(fieldset_data['fields']) == 1
    field_data = fieldset_data['fields'][0]
    assert field_data['name'] == shared_field.name
    assert field_data['type'] == shared_field.type
    assert field_data['order'] == shared_field.order
    assert field_data['is_required'] == shared_field.is_required
    assert field_data['is_hidden'] == shared_field.is_hidden
    assert field_data['description'] == ''
    assert field_data['default'] == ''
    assert field_data['api_name'] != shared_field.api_name
    assert field_data['api_name'] == field.api_name


def test_create__task_with_empty_fieldsets__no_created(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    request_data = {
        'name': 'Template without task fieldsets',
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
                'fieldsets': [],
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
    template = Template.objects.get(id=response.data['id'])
    task = template.tasks.first()
    assert FieldsetTemplate.objects.filter(
        task=task,
    ).count() == 0


def test_create__kickoff_fieldset_non_shared_id__validation_error(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    existing_template = create_test_template(
        user,
        is_active=True,
        tasks_count=1,
    )
    non_shared_fieldset = create_test_fieldset_template(
        account=account,
        template=existing_template,
        kickoff=existing_template.kickoff_instance,
    )
    request_data = {
        'name': 'Template with non-shared fieldset source',
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
                'role': OwnerRole.OWNER,
            },
        ],
        'is_active': True,
        'kickoff': {
            'fieldsets': [
                {
                    'shared_fieldset_id': non_shared_fieldset.id,
                },
            ],
        },
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
            },
        ],
    }

    # act
    response = api_client.post(
        path='/templates',
        data=request_data,
    )

    # assert
    assert response.status_code == 400
    message = (
        f'Invalid pk "{non_shared_fieldset.id}" - object does not exist.'
    )
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'fieldsets'
    assert response.data['details']['reason'] == message
    assert FieldsetTemplate.objects.filter(
        is_shared=False,
        shared_fieldset=non_shared_fieldset,
    ).count() == 0


def test_create__draft_fieldset_from_another_account__excluded(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    account = create_test_account(name='Account 1')
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    other_account = create_test_account(name='Account 2')
    other_shared_fieldset = create_test_shared_fieldset(
        account=other_account,
        title='Private title',
        description='Private description',
        name='Private fieldset',
        rule_operator=FieldSetRuleOperator.SUM_EQUAL,
        rule_value='100',
    )
    request_data = {
        'name': 'Draft with foreign fieldset',
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
                'role': OwnerRole.OWNER,
            },
        ],
        'is_active': False,
        'kickoff': {
            'fieldsets': [
                {
                    'shared_fieldset_id': other_shared_fieldset.id,
                },
            ],
        },
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
                'fieldsets': [
                    {
                        'shared_fieldset_id': other_shared_fieldset.id,
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
    template = Template.objects.get(id=response.data['id'])
    draft = template.draft.draft
    assert draft['kickoff']['fieldsets'] == []
    assert draft['tasks'][0]['fieldsets'] == []
    assert response.data['kickoff']['fieldsets'] == []
    assert response.data['tasks'][0]['fieldsets'] == []


def test_create__kickoff_fieldset_with_expanded_fields__preserves_api_names(
    mocker,
    api_client,
):

    """ Creating an active template with already expanded fieldset fields
        must keep provided field/ruleset api_names
        (create path, not clone). """

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    shared_fieldset = create_test_shared_fieldset(account=account)
    fs_api_name = 'draft-fs-api-name'
    field_api_name = 'draft-field-api-name'
    selection_api_name = 'draft-selection-api-name'
    request_data = {
        'name': 'Template with expanded kickoff fieldset',
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
                'role': OwnerRole.OWNER,
            },
        ],
        'is_active': True,
        'kickoff': {
            'fieldsets': [
                {
                    'shared_fieldset_id': shared_fieldset.id,
                    'api_name': fs_api_name,
                    'fields': [
                        {
                            'name': 'Dropdown field',
                            'type': FieldType.DROPDOWN,
                            'order': 1,
                            'api_name': field_api_name,
                            'selections': [
                                {
                                    'value': 'Option A',
                                    'api_name': selection_api_name,
                                },
                            ],
                        },
                    ],
                },
            ],
        },
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
    fieldset = FieldsetTemplate.objects.get(
        kickoff__template_id=response.data['id'],
        shared_fieldset=shared_fieldset,
        is_shared=False,
    )
    field = fieldset.fields.get()
    assert fieldset.api_name == fs_api_name
    assert field.api_name == field_api_name
    assert field.selections.get().api_name == selection_api_name

    fieldset_data = response.data['kickoff']['fieldsets'][0]
    field_data = fieldset_data['fields'][0]
    assert fieldset_data['api_name'] == fs_api_name
    assert field_data['api_name'] == field_api_name
    assert field_data['selections'][0]['api_name'] == selection_api_name


def test_create__task_fieldset_with_expanded_fields__preserves_api_names(
    mocker,
    api_client,
):

    """ Creating an active template with already expanded task fieldset
        fields must keep provided field/ruleset api_names. """

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    shared_fieldset = create_test_shared_fieldset(account=account)
    fs_api_name = 'draft-task-fs-api-name'
    field_api_name = 'draft-task-field-api-name'
    selection_api_name = 'draft-task-selection-api-name'
    request_data = {
        'name': 'Template with expanded task fieldset',
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
                'fieldsets': [
                    {
                        'shared_fieldset_id': shared_fieldset.id,
                        'api_name': fs_api_name,
                        'fields': [
                            {
                                'name': 'Dropdown field',
                                'type': FieldType.DROPDOWN,
                                'order': 1,
                                'api_name': field_api_name,
                                'selections': [
                                    {
                                        'value': 'Option A',
                                        'api_name': selection_api_name,
                                    },
                                ],
                            },
                        ],
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
    fieldset = FieldsetTemplate.objects.get(
        task__template_id=response.data['id'],
        shared_fieldset=shared_fieldset,
        is_shared=False,
    )
    field = fieldset.fields.get()
    assert fieldset.api_name == fs_api_name
    assert field.api_name == field_api_name
    assert field.selections.get().api_name == selection_api_name

    fieldset_data = response.data['tasks'][0]['fieldsets'][0]
    field_data = fieldset_data['fields'][0]
    assert fieldset_data['api_name'] == fs_api_name
    assert field_data['api_name'] == field_api_name
    assert field_data['selections'][0]['api_name'] == selection_api_name


def test_create__kickoff_fieldset_expanded_fields_used_in_task_text__ok(
    mocker,
    api_client,
):

    """ Expanded kickoff field api_names used in task title/description
        must remain valid after create. """

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_created',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    shared_fieldset = create_test_shared_fieldset(account=account)
    field_api_name = 'kickoff-expanded-field'
    task_name = f'Step with {{{{ {field_api_name} }}}}'
    task_description = f'Desc {{{{ {field_api_name} }}}}'
    request_data = {
        'name': 'Template with field vars',
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
                'role': OwnerRole.OWNER,
            },
        ],
        'is_active': True,
        'kickoff': {
            'fieldsets': [
                {
                    'shared_fieldset_id': shared_fieldset.id,
                    'api_name': 'kickoff-expanded-fs',
                    'order': 0,
                    'title': shared_fieldset.title,
                    'description': shared_fieldset.description,
                    'name': shared_fieldset.name,
                    'fields': [
                        {
                            'name': 'Fieldset field',
                            'type': FieldType.STRING,
                            'order': 1,
                            'api_name': field_api_name,
                            'is_required': False,
                            'is_hidden': False,
                            'description': '',
                            'default': '',
                        },
                    ],
                    'rulesets': [],
                },
            ],
        },
        'tasks': [
            {
                'number': 1,
                'name': task_name,
                'description': task_description,
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
    fieldset = FieldsetTemplate.objects.get(
        kickoff__template_id=response.data['id'],
        shared_fieldset=shared_fieldset,
        is_shared=False,
    )
    assert fieldset.fields.get().api_name == field_api_name
    assert (
        response.data['kickoff']['fieldsets'][0]['fields'][0]['api_name']
        == field_api_name
    )
    assert response.data['tasks'][0]['name'] == task_name
    assert response.data['tasks'][0]['description'] == task_description
