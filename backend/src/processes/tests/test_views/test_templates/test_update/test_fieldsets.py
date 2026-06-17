import pytest

from src.processes.enums import (
    OwnerRole,
    OwnerType,
    PerformerType, FieldSetRuleType,
)
from src.processes.models.templates.fieldset import FieldsetTemplate
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_shared_fieldset,
    create_test_template,
)

pytestmark = pytest.mark.django_db

# Kickoff fieldsets


def test_update__kickoff_create_fieldset__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    shared = create_test_shared_fieldset(
        account=account,
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='100',
    )
    field = shared.fields.first()
    rule = shared.rules.first()
    field.rules.add(rule)
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
                        'shared_fieldset_id': shared.id,
                        'order': 3,
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
    fieldset_data = fieldsets[0]
    assert fieldset_data['shared_fieldset_id'] == shared.id
    assert fieldset_data['order'] == 3
    assert fieldset_data['name'] == shared.name
    assert fieldset_data['title'] == shared.title
    assert fieldset_data['description'] == shared.description
    assert fieldset_data['label_position'] == shared.label_position
    assert fieldset_data['layout'] == shared.layout
    assert fieldset_data['api_name']
    assert fieldset_data['api_name'] != shared.api_name
    assert len(fieldset_data['fields']) == 1
    field_data = fieldset_data['fields'][0]
    assert field_data['name'] == field.name
    assert field_data['description'] == ''
    assert field_data['type'] == field.type
    assert field_data['is_required'] == field.is_required
    assert field_data['is_hidden'] == field.is_hidden
    assert field_data['order'] == field.order
    assert field_data['default'] == field.default
    assert field_data['api_name']
    assert len(fieldset_data['rules']) == 1
    rule_data = fieldset_data['rules'][0]
    assert rule_data['type'] == FieldSetRuleType.SUM_EQUAL
    assert rule_data['value'] == '100'
    assert rule_data['api_name']
    assert rule_data['fields'] == [field_data['api_name']]
    assert kickoff.fieldsets.filter(
        shared_fieldset_id=shared.id,
        order=3,
    ).exists()


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
    # create an existing child fieldset linked to kickoff from shared_1
    existing = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        kickoff=kickoff,
        name=shared_1.name,
        shared_fieldset_id=shared_1.id,
        is_shared=True,
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
    assert not kickoff.fieldsets.filter(id=existing.id).exists()
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
    shared = create_test_shared_fieldset(account=account)
    existing = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        kickoff=kickoff,
        name=shared.name,
        shared_fieldset_id=shared.id,
        is_shared=True,
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
    assert not kickoff.fieldsets.filter(id=existing.id).exists()


def test_update__kickoff_skip_fieldsets__no_fieldsets_created(
    mocker,
    api_client,
):

    """ Updating a template without fieldsets key in kickoff does not
        create any kickoff fieldset records. """

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
                },
            ],
        },
    )

    # assert
    assert response.status_code == 200
    assert kickoff.fieldsets.count() == 0


# Task fieldsets


def test_update__task_create_fieldset__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    shared = create_test_shared_fieldset(
        account=account,
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='200',
    )
    field = shared.fields.first()
    rule = shared.rules.first()
    field.rules.add(rule)
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
                            'shared_fieldset_id': shared.id,
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
    fieldset_data = fieldsets[0]
    assert fieldset_data['shared_fieldset_id'] == shared.id
    assert fieldset_data['order'] == 2
    assert len(fieldset_data['fields']) == 1
    field_data = fieldset_data['fields'][0]
    assert field_data['name'] == field.name
    assert field_data['description'] == ''
    assert field_data['type'] == field.type
    assert field_data['is_required'] == field.is_required
    assert field_data['is_hidden'] == field.is_hidden
    assert field_data['order'] == field.order
    assert field_data['default'] == field.default
    assert field_data['api_name']
    assert len(fieldset_data['rules']) == 1
    rule_data = fieldset_data['rules'][0]
    assert rule_data['type'] == FieldSetRuleType.SUM_EQUAL
    assert rule_data['value'] == '200'
    assert rule_data['api_name']
    assert rule_data['fields'] == [field_data['api_name']]
    assert task.fieldsets.filter(
        shared_fieldset_id=shared.id,
        order=2,
    ).exists()


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
    # create an existing child fieldset linked to task from shared_1
    existing = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        task=task,
        name=shared_1.name,
        shared_fieldset_id=shared_1.id,
        is_shared=True,
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
    assert not task.fieldsets.filter(id=existing.id).exists()
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
    shared = create_test_shared_fieldset(account=account)
    existing = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        task=task,
        name=shared.name,
        shared_fieldset_id=shared.id,
        is_shared=True,
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
    assert not task.fieldsets.filter(id=existing.id).exists()


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
