import pytest

from src.processes.enums import (
    FieldSetLayout,
    FieldSetRuleType,
    LabelPosition,
    OwnerRole,
    OwnerType,
    PerformerType,
)
from src.processes.models.templates.fieldset import FieldsetTemplate
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_fieldset_template,
    create_test_owner,
    create_test_shared_fieldset,
    create_test_template,
)

pytestmark = pytest.mark.django_db

# Kickoff fieldsets


def test_update__create_kickoff_fieldset_only_required_data__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    fs_title = 'Some title'
    fs_description = 'Some desc'
    fs_name = 'Some name'
    fs_order = 3
    label_position = LabelPosition.LEFT
    layout = FieldSetLayout.HORIZONTAL
    rule_type = FieldSetRuleType.SUM_EQUAL
    rule_value = '100'
    shared_fieldset = create_test_shared_fieldset(
        account=account,
        title=fs_title,
        description=fs_description,
        name=fs_name,
        order=fs_order,
        label_position=label_position,
        layout=layout,
        rule_type=rule_type,
        rule_value=rule_value,
    )
    shared_field = shared_fieldset.fields.first()
    shared_rule = shared_fieldset.rules.first()
    shared_field.rules.add(shared_rule)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated',
    )
    mocker.patch(
        'src.processes.views.template.AnalyticService.templates_updated',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data={
            'id': template.id,
            'is_active': True,
            'name': 'Updated template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {
                'id': kickoff.id,
                'fieldsets': [
                    {
                        'shared_fieldset_id': shared_fieldset.id,
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
    fieldset = FieldsetTemplate.objects.get(
        kickoff=kickoff,
        shared_fieldset=shared_fieldset,
        is_shared=False,
    )
    field = fieldset.fields.first()
    rule = fieldset.rules.first()

    fieldsets = response.data['kickoff']['fieldsets']
    assert len(fieldsets) == 1
    fieldset_data = fieldsets[0]
    assert fieldset_data['shared_fieldset_id'] == shared_fieldset.id
    assert fieldset_data['order'] == 0
    assert fieldset_data['name'] == fs_name
    assert fieldset_data['title'] == fs_title
    assert fieldset_data['description'] == fs_description
    assert fieldset_data['label_position'] == label_position
    assert fieldset_data['layout'] == layout
    assert fieldset_data['api_name'] == fieldset.api_name
    assert len(fieldset_data['fields']) == 1
    field_data = fieldset_data['fields'][0]
    assert field_data['name'] == shared_field.name
    assert field_data['description'] == ''
    assert field_data['type'] == shared_field.type
    assert field_data['is_required'] == shared_field.is_required
    assert field_data['is_hidden'] == shared_field.is_hidden
    assert field_data['order'] == shared_field.order
    assert field_data['default'] == shared_field.default
    assert field_data['api_name'] == field.api_name
    assert len(fieldset_data['rules']) == 1
    rule_data = fieldset_data['rules'][0]
    assert rule_data['type'] == rule_type
    assert rule_data['value'] == rule_value
    assert rule_data['api_name'] == rule.api_name
    assert rule_data['fields'] == [field.api_name]


def test_update__kickoff_fieldset_all_fieldset_data__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    fs_title = 'Some title'
    fs_description = 'Some desc'
    fs_order = 3
    fs_api_name = 'fs-some-api-name'
    shared_fieldset = create_test_shared_fieldset(account=account)
    shared_fieldset.fields.all().delete()
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated',
    )
    mocker.patch(
        'src.processes.views.template.AnalyticService.templates_updated',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data={
            'id': template.id,
            'is_active': True,
            'name': 'Updated template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {
                'id': kickoff.id,
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
    assert FieldsetTemplate.objects.get(
        kickoff=kickoff,
        shared_fieldset=shared_fieldset,
        is_shared=False,
        api_name=fs_api_name,
    )

    fieldsets = response.data['kickoff']['fieldsets']
    assert len(fieldsets) == 1
    fieldset_data = fieldsets[0]
    assert fieldset_data['shared_fieldset_id'] == shared_fieldset.id
    assert fieldset_data['order'] == fs_order
    assert fieldset_data['title'] == fs_title
    assert fieldset_data['description'] == fs_description
    assert fieldset_data['name'] == shared_fieldset.name
    assert fieldset_data['api_name'] == fs_api_name
    assert fieldset_data['label_position'] == shared_fieldset.label_position
    assert fieldset_data['layout'] == shared_fieldset.layout
    assert fieldset_data['rules'] == []
    assert fieldset_data['fields'] == []


def test_update__kickoff_create_two_fieldsets__ok(
    mocker,
    api_client,
):

    """ Updating a template with multiple fieldsets linked to
        kickoff creates multiple child fieldset records. """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    shared_1 = create_test_shared_fieldset(account=account)
    shared_2 = create_test_shared_fieldset(account=account)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated',
    )
    mocker.patch(
        'src.processes.views.template.AnalyticService.templates_updated',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data={
            'id': template.id,
            'is_active': True,
            'name': 'Updated template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {
                'id': kickoff.id,
                'fieldsets': [
                    {
                        'shared_fieldset_id': shared_1.id,
                        'order': 0,
                    },
                    {
                        'shared_fieldset_id': shared_2.id,
                        'order': 1,
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
    fieldsets = response.data['kickoff']['fieldsets']
    assert len(fieldsets) == 2
    assert kickoff.fieldsets.filter(
        shared_fieldset_id=shared_1.id,
        order=0,
    ).count() == 1
    assert kickoff.fieldsets.filter(
        shared_fieldset_id=shared_2.id,
        order=1,
    ).count() == 1


def test_update__kickoff_replace_fieldset__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    shared_1 = create_test_shared_fieldset(account=account)
    shared_2 = create_test_shared_fieldset(account=account)
    # create an fieldset child fieldset linked to kickoff from shared_1
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=kickoff,
        shared_fieldset=shared_1,
        order=0,
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated',
    )
    mocker.patch(
        'src.processes.views.template.AnalyticService.templates_updated',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data={
            'id': template.id,
            'is_active': True,
            'name': 'Updated template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {
                'id': kickoff.id,
                'fieldsets': [
                    {
                        'shared_fieldset_id': shared_2.id,
                        'order': 2,
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
    fieldsets = response.data['kickoff']['fieldsets']
    assert len(fieldsets) == 1
    assert fieldsets[0]['shared_fieldset_id'] == shared_2.id
    assert fieldsets[0]['order'] == 2
    assert not kickoff.fieldsets.filter(id=fieldset.id).exists()
    assert kickoff.fieldsets.filter(
        shared_fieldset_id=shared_2.id,
        order=2,
    ).count() == 1


def test_update__kickoff_remove_fieldset__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    shared_fieldset = create_test_shared_fieldset(account=account)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=kickoff,
        shared_fieldset=shared_fieldset,
        order=0,
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated',
    )
    mocker.patch(
        'src.processes.views.template.AnalyticService.templates_updated',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data={
            'id': template.id,
            'is_active': True,
            'name': 'Updated template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {
                'id': kickoff.id,
                'fieldsets': [],
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
    assert response.data['kickoff']['fieldsets'] == []
    assert not kickoff.fieldsets.filter(id=fieldset.id).exists()


# Task fieldsets


def test_update__create_task_fieldset_only_required_data__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    fs_title = 'Some title'
    fs_description = 'Some desc'
    fs_name = 'Some name'
    fs_order = 3
    label_position = LabelPosition.LEFT
    layout = FieldSetLayout.HORIZONTAL
    rule_type = FieldSetRuleType.SUM_EQUAL
    rule_value = '200'
    shared_fieldset = create_test_shared_fieldset(
        account=account,
        title=fs_title,
        description=fs_description,
        name=fs_name,
        order=fs_order,
        label_position=label_position,
        layout=layout,
        rule_type=rule_type,
        rule_value=rule_value,
    )
    shared_field = shared_fieldset.fields.first()
    shared_rule = shared_fieldset.rules.first()
    shared_field.rules.add(shared_rule)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated',
    )
    mocker.patch(
        'src.processes.views.template.AnalyticService.templates_updated',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data={
            'id': template.id,
            'is_active': True,
            'name': 'Updated template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {
                'id': kickoff.id,
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
                    'fieldsets': [
                        {
                            'shared_fieldset_id': shared_fieldset.id,
                        },
                    ],
                },
            ],
        },
    )

    # assert
    assert response.status_code == 200
    fieldset = FieldsetTemplate.objects.get(
        task=task,
        shared_fieldset=shared_fieldset,
        is_shared=False,
    )
    field = fieldset.fields.first()
    rule = fieldset.rules.first()

    fieldsets = response.data['tasks'][0]['fieldsets']
    assert len(fieldsets) == 1
    fieldset_data = fieldsets[0]
    assert fieldset_data['shared_fieldset_id'] == shared_fieldset.id
    assert fieldset_data['order'] == 0
    assert fieldset_data['name'] == fs_name
    assert fieldset_data['title'] == fs_title
    assert fieldset_data['description'] == fs_description
    assert fieldset_data['label_position'] == label_position
    assert fieldset_data['layout'] == layout
    assert fieldset_data['api_name'] == fieldset.api_name
    assert len(fieldset_data['fields']) == 1
    field_data = fieldset_data['fields'][0]
    assert field_data['name'] == shared_field.name
    assert field_data['description'] == ''
    assert field_data['type'] == shared_field.type
    assert field_data['is_required'] == shared_field.is_required
    assert field_data['is_hidden'] == shared_field.is_hidden
    assert field_data['order'] == shared_field.order
    assert field_data['default'] == shared_field.default
    assert field_data['api_name'] == field.api_name
    assert len(fieldset_data['rules']) == 1
    rule_data = fieldset_data['rules'][0]
    assert rule_data['type'] == rule_type
    assert rule_data['value'] == rule_value
    assert rule_data['api_name'] == rule.api_name
    assert rule_data['fields'] == [field.api_name]


def test_update__task_fieldset_all_fieldset_data__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    fs_title = 'Some title'
    fs_description = 'Some desc'
    fs_order = 3
    fs_api_name = 'fs-some-api-name'
    shared_fieldset = create_test_shared_fieldset(account=account)
    shared_fieldset.fields.all().delete()
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated',
    )
    mocker.patch(
        'src.processes.views.template.AnalyticService.templates_updated',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data={
            'id': template.id,
            'is_active': True,
            'name': 'Updated template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {
                'id': kickoff.id,
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
        },
    )

    # assert
    assert response.status_code == 200
    assert FieldsetTemplate.objects.get(
        task=task,
        shared_fieldset=shared_fieldset,
        is_shared=False,
        api_name=fs_api_name,
    )

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
    assert fieldset_data['rules'] == []
    assert fieldset_data['fields'] == []


def test_update__task_create_two_fieldsets__ok(
    mocker,
    api_client,
):

    """ Updating a template with multiple fieldsets linked to a task
        creates multiple child fieldset records. """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    task = template.tasks.first()
    kickoff = template.kickoff_instance
    shared_1 = create_test_shared_fieldset(account=account)
    shared_2 = create_test_shared_fieldset(account=account)
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated',
    )
    mocker.patch(
        'src.processes.views.template.AnalyticService.templates_updated',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data={
            'id': template.id,
            'is_active': True,
            'name': 'Updated template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {
                'id': kickoff.id,
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
                    'fieldsets': [
                        {
                            'shared_fieldset_id': shared_1.id,
                            'order': 1,
                        },
                        {
                            'shared_fieldset_id': shared_2.id,
                            'order': 0,
                        },
                    ],
                },
            ],
        },
    )

    # assert
    assert response.status_code == 200
    fieldsets = response.data['tasks'][0]['fieldsets']
    assert len(fieldsets) == 2
    assert task.fieldsets.filter(
        shared_fieldset_id=shared_1.id,
        order=1,
    ).count() == 1
    assert task.fieldsets.filter(
        shared_fieldset_id=shared_2.id,
        order=0,
    ).count() == 1


def test_update__task_replace_fieldset__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    shared_1 = create_test_shared_fieldset(account=account)
    shared_2 = create_test_shared_fieldset(account=account)
    # create an fieldset child fieldset linked to task from shared_1
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        task=task,
        shared_fieldset=shared_1,
        order=0,
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated',
    )
    mocker.patch(
        'src.processes.views.template.AnalyticService.templates_updated',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data={
            'id': template.id,
            'is_active': True,
            'name': 'Updated template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {
                'id': kickoff.id,
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
                    'fieldsets': [
                        {
                            'shared_fieldset_id': shared_2.id,
                            'order': 2,
                        },
                    ],
                },
            ],
        },
    )

    # assert
    assert response.status_code == 200
    fieldsets = response.data['tasks'][0]['fieldsets']
    assert len(fieldsets) == 1
    assert fieldsets[0]['shared_fieldset_id'] == shared_2.id
    assert fieldsets[0]['order'] == 2
    assert not task.fieldsets.filter(id=fieldset.id).exists()
    assert task.fieldsets.filter(
        shared_fieldset_id=shared_2.id,
        order=2,
    ).count() == 1


def test_update__tasks_remove_fieldset__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    shared_fieldset = create_test_shared_fieldset(account=account)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        task=task,
        shared_fieldset=shared_fieldset,
        order=0,
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated',
    )
    mocker.patch(
        'src.processes.views.template.AnalyticService.templates_updated',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data={
            'id': template.id,
            'is_active': True,
            'name': 'Updated template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {
                'id': kickoff.id,
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
                    'fieldsets': [],
                },
            ],
        },
    )

    # assert
    assert response.status_code == 200
    assert response.data['tasks'][0]['fieldsets'] == []
    assert not task.fieldsets.filter(id=fieldset.id).exists()


def test_update__task_with_empty_fieldsets__no_create_fieldsets(
    mocker,
    api_client,
):

    """ Updating a template with empty fieldsets list in task does not
        create any task fieldset records. """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.'
        'create_integrations_for_template',
    )
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated',
    )
    mocker.patch(
        'src.processes.views.template.AnalyticService.templates_updated',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data={
            'id': template.id,
            'is_active': True,
            'name': 'Updated template',
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {
                'id': kickoff.id,
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
                    'fieldsets': [],
                },
            ],
        },
    )

    # assert
    assert response.status_code == 200
    assert task.fieldsets.count() == 0
