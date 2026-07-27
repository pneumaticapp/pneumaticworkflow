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
from src.processes.messages.fieldset import (
    MSG_FS_0013,
    MSG_FS_0014,
    MSG_FS_0015,
    MSG_FS_0016,
)
from src.processes.models.templates.fields import (
    FieldTemplate,
    FieldTemplateSelection,
)
from src.processes.models.templates.fieldset import FieldsetTemplate
from src.processes.serializers.templates.template import TemplateSerializer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_fieldset_template,
    create_test_owner,
    create_test_shared_fieldset,
    create_test_template,
)
from src.utils.validation import ErrorCode

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


def test_update__create_kickoff_fieldset_all_fieldset_data__ok(
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


def test_update__create_kickoff_two_different_fieldsets__ok(
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


def test_update__create_kickoff_two_similar_fieldsets__ok(
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
                        'order': 0,
                    },
                    {
                        'shared_fieldset_id': shared_fieldset.id,
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
    kickoff_fieldset_1 = fieldsets[0]
    kickoff_fieldset_2 = fieldsets[1]
    assert kickoff_fieldset_1['shared_fieldset_id'] == shared_fieldset.id
    assert kickoff_fieldset_2['shared_fieldset_id'] == shared_fieldset.id
    assert kickoff_fieldset_1['api_name'] != kickoff_fieldset_2['api_name']
    db_fieldset_1 = kickoff.fieldsets.get(
        shared_fieldset_id=shared_fieldset.id,
        order=0,
    )
    db_fieldset_2 = kickoff.fieldsets.get(
        shared_fieldset_id=shared_fieldset.id,
        order=1,
    )
    assert db_fieldset_1.api_name != db_fieldset_2.api_name


def test_update__replace_kickoff_fieldset__ok(
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


def test_update__remove_kickoff_fieldset__ok(
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


@pytest.mark.parametrize('is_active', (True, False))
def test_update__update_kickoff__fieldset_all_fields__ok(
    mocker,
    is_active,
    api_client,
):
    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=is_active, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    shared_fieldset = create_test_shared_fieldset(account=account)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=kickoff,
        shared_fieldset=shared_fieldset,
        order=0,
        title='Old title',
        description='Old desc',
        api_name='fs-kickoff-update',
    )
    fieldset_id = fieldset.id
    new_order = 2
    new_title = 'New title'
    new_description = 'New desc'
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
            'is_active': is_active,
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
                        'api_name': fieldset.api_name,
                        'order': new_order,
                        'title': new_title,
                        'description': new_description,
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
    kickoff_fieldset_1 = fieldsets[0]
    assert kickoff_fieldset_1['api_name'] == fieldset.api_name
    assert kickoff_fieldset_1['order'] == new_order
    assert kickoff_fieldset_1['title'] == new_title
    assert kickoff_fieldset_1['description'] == new_description
    assert kickoff_fieldset_1['name'] == fieldset.name
    assert kickoff_fieldset_1['layout'] == fieldset.layout
    assert kickoff_fieldset_1['label_position'] == fieldset.label_position
    if is_active:
        fieldset.refresh_from_db()
        assert fieldset.id == fieldset_id
        assert fieldset.api_name == 'fs-kickoff-update'
        assert fieldset.order == new_order
        assert fieldset.title == new_title
        assert fieldset.description == new_description
        assert fieldset.name == shared_fieldset.name
        assert fieldset.layout == shared_fieldset.layout
        assert fieldset.label_position == shared_fieldset.label_position


def test_update_kickoff_update_active_template__not_change_fieldset(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    shared_fieldset = create_test_shared_fieldset(
        account=account,
        rule_type=FieldSetRuleType.SUM_EQUAL,
    )
    shared_field = shared_fieldset.fields.first()
    shared_field.type = FieldType.RADIO
    shared_field.save(update_fields=['type'])
    FieldTemplateSelection.objects.create(
        value='Option 1',
        field_template=shared_field,
        template=template,
        api_name=f'{shared_field.api_name}-shared-selection-1',
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=kickoff,
        shared_fieldset=shared_fieldset,
        order=0,
        title='Old title',
        api_name='fs-kickoff-fields',
    )
    rule = fieldset.rules.first()
    field = fieldset.fields.first()
    selection = field.selections.all().first()

    new_title = 'New title'
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
                        'api_name': fieldset.api_name,
                        'order': fieldset.order,
                        'title': new_title,
                        'description': fieldset.description,
                        'fields': [
                            {
                                'name': field.name,
                                'api_name': field.api_name,
                                'type': field.type,
                                'order': field.order,
                                'selections': [
                                    {
                                        'value': selection.value,
                                        'api_name': selection.api_name,
                                    },
                                ],
                            },
                        ],
                        'rules': [
                            {
                                'type': rule.type,
                                'value': rule.value,
                                'api_name': rule.api_name,
                                'fields': [field.api_name],
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
    fieldsets = response.data['kickoff']['fieldsets']
    assert len(fieldsets) == 1

    kickoff_fieldset = fieldsets[0]
    assert kickoff_fieldset['api_name'] == fieldset.api_name
    assert kickoff_fieldset['title'] == new_title

    rule_data = kickoff_fieldset['rules'][0]
    assert rule_data['api_name'] == rule.api_name

    fields = kickoff_fieldset['fields']
    assert len(fields) == 1
    field_1 = fields[0]
    assert field_1['api_name'] == field.api_name

    selections = field_1['selections']
    assert len(selections) == 1
    selection_1 = selections[0]
    assert selection_1['api_name'] == selection.api_name


def test_update_kickoff_update_inactive_template__not_change_fieldset(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=False, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    shared_fieldset = create_test_shared_fieldset(
        account=account,
        rule_type=FieldSetRuleType.SUM_EQUAL,
    )
    shared_field = shared_fieldset.fields.first()
    shared_field.type = FieldType.RADIO
    shared_field.save(update_fields=['type'])
    FieldTemplateSelection.objects.create(
        value='Option 1',
        field_template=shared_field,
        template=template,
        api_name=f'{shared_field.api_name}-shared-selection-1',
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=kickoff,
        shared_fieldset=shared_fieldset,
        order=0,
        title='Old title',
        api_name='fs-kickoff-fields',
    )
    rule = fieldset.rules.first()
    field = fieldset.fields.first()
    selection = field.selections.all().first()

    # Add fieldset data to the template draft
    slz = TemplateSerializer(
        instance=template,
        context={
            'user': user,
            'account': user.account,
        },
    )
    slz.initial_data = slz.data
    slz.save_as_draft()

    new_title = 'New title'
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
            'is_active': False,
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
                        'api_name': fieldset.api_name,
                        'order': fieldset.order,
                        'title': new_title,
                        'description': fieldset.description,
                        'fields': [
                            {
                                'name': field.name,
                                'api_name': field.api_name,
                                'type': field.type,
                                'order': field.order,
                                'selections': [
                                    {
                                        'value': selection.value,
                                        'api_name': selection.api_name,
                                    },
                                ],
                            },
                        ],
                        'rules': [
                            {
                                'type': rule.type,
                                'value': rule.value,
                                'api_name': rule.api_name,
                                'fields': [field.api_name],
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
    fieldsets = response.data['kickoff']['fieldsets']
    assert len(fieldsets) == 1

    kickoff_fieldset = fieldsets[0]
    assert kickoff_fieldset['api_name'] == fieldset.api_name
    assert kickoff_fieldset['title'] == new_title

    rule_data = kickoff_fieldset['rules'][0]
    assert rule_data['api_name'] == rule.api_name

    fields = kickoff_fieldset['fields']
    assert len(fields) == 1
    field_1 = fields[0]
    assert field_1['api_name'] == field.api_name

    selections = field_1['selections']
    assert len(selections) == 1
    selection_1 = selections[0]
    assert selection_1['api_name'] == selection.api_name


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


def test_update__create_task_fieldset_all_fieldset_data__ok(
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


def test_update__create_task_two_fieldsets__ok(
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


def test_update__create_task_two_similar_fieldsets__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    task = template.tasks.first()
    kickoff = template.kickoff_instance
    shared_fieldset = create_test_shared_fieldset(account=account)
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
                            'order': 0,
                        },
                        {
                            'shared_fieldset_id': shared_fieldset.id,
                            'order': 1,
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
    task_fieldset_1 = fieldsets[0]
    task_fieldset_2 = fieldsets[1]
    assert task_fieldset_1['shared_fieldset_id'] == shared_fieldset.id
    assert task_fieldset_2['shared_fieldset_id'] == shared_fieldset.id
    assert task_fieldset_1['api_name'] != task_fieldset_2['api_name']
    db_fieldset_1 = task.fieldsets.get(
        shared_fieldset_id=shared_fieldset.id,
        order=0,
    )
    db_fieldset_2 = task.fieldsets.get(
        shared_fieldset_id=shared_fieldset.id,
        order=1,
    )
    assert db_fieldset_1.api_name != db_fieldset_2.api_name


def test_update__replace_task_fieldset__ok(
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


def test_update__remove_tasks_fieldset__ok(
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


@pytest.mark.parametrize('is_active', (True, False))
def test_update__update_task__fieldset_all_fields__ok(
    mocker,
    is_active,
    api_client,
):
    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=is_active, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.get(number=1)
    shared_fieldset = create_test_shared_fieldset(account=account)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        task=task,
        shared_fieldset=shared_fieldset,
        order=0,
        title='Old title',
        description='Old desc',
        api_name='fs-task-update',
    )
    fieldset_id = fieldset.id
    new_order = 2
    new_title = 'New title'
    new_description = 'New desc'
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
            'is_active': is_active,
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
                            'api_name': fieldset.api_name,
                            'order': new_order,
                            'title': new_title,
                            'description': new_description,
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
    task_fieldset_1 = fieldsets[0]
    assert task_fieldset_1['api_name'] == fieldset.api_name
    assert task_fieldset_1['order'] == new_order
    assert task_fieldset_1['title'] == new_title
    assert task_fieldset_1['description'] == new_description
    assert task_fieldset_1['name'] == fieldset.name
    assert task_fieldset_1['layout'] == fieldset.layout
    assert task_fieldset_1['label_position'] == fieldset.label_position
    if is_active:
        fieldset.refresh_from_db()
        assert fieldset.id == fieldset_id
        assert fieldset.api_name == 'fs-task-update'
        assert fieldset.order == new_order
        assert fieldset.title == new_title
        assert fieldset.description == new_description
        assert fieldset.name == shared_fieldset.name
        assert fieldset.layout == shared_fieldset.layout
        assert fieldset.label_position == shared_fieldset.label_position


@pytest.mark.parametrize('is_active', (True, False))
def test_update__update_task_fieldset_all_fields__ok(
    mocker,
    is_active,
    api_client,
):
    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=is_active, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.get(number=1)
    shared_fieldset = create_test_shared_fieldset(account=account)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        task=task,
        shared_fieldset=shared_fieldset,
        order=0,
        title='Old title',
        description='Old desc',
        api_name='fs-task-update',
    )
    fieldset_id = fieldset.id
    new_order = 2
    new_title = 'New title'
    new_description = 'New desc'
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
            'is_active': is_active,
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
                            'api_name': fieldset.api_name,
                            'order': new_order,
                            'title': new_title,
                            'description': new_description,
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
    task_fieldset_1 = fieldsets[0]
    assert task_fieldset_1['api_name'] == fieldset.api_name
    assert task_fieldset_1['order'] == new_order
    assert task_fieldset_1['title'] == new_title
    assert task_fieldset_1['description'] == new_description
    assert task_fieldset_1['name'] == fieldset.name
    assert task_fieldset_1['layout'] == fieldset.layout
    assert task_fieldset_1['label_position'] == fieldset.label_position
    if is_active:
        fieldset.refresh_from_db()
        assert fieldset.id == fieldset_id
        assert fieldset.api_name == 'fs-task-update'
        assert fieldset.order == new_order
        assert fieldset.title == new_title
        assert fieldset.description == new_description
        assert fieldset.name == shared_fieldset.name
        assert fieldset.layout == shared_fieldset.layout
        assert fieldset.label_position == shared_fieldset.label_position


@pytest.mark.parametrize('is_active', (True, False))
def test_update_task_update_template__not_change_fieldset(
    mocker,
    is_active,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=is_active, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.get(number=1)
    shared_fieldset = create_test_shared_fieldset(account=account)
    shared_field = shared_fieldset.fields.first()
    shared_field.type = FieldType.RADIO
    shared_field.save(update_fields=['type'])
    FieldTemplateSelection.objects.create(
        value='Option 1',
        field_template=shared_field,
        template=template,
        api_name=f'{shared_field.api_name}-shared-selection-1',
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        task=task,
        shared_fieldset=shared_fieldset,
        order=0,
        title='Old title',
        api_name='fieldset-1',
    )
    field = fieldset.fields.first()
    selection = field.selections.all().first()

    slz = TemplateSerializer(
        instance=template,
        context={
            'user': user,
            'account': user.account,
        },
    )
    slz.initial_data = slz.data
    slz.save_as_draft()

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
            'is_active': False,
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
                            'api_name': fieldset.api_name,
                            'order': fieldset.order,
                            'title': fieldset.title,
                            'description': fieldset.description,
                            'fields': [
                                {
                                    'name': field.name,
                                    'api_name': field.api_name,
                                    'type': field.type,
                                    'order': field.order,
                                    'selections': [
                                        {
                                            'value': selection.value,
                                            'api_name': selection.api_name,
                                        },
                                    ],
                                },
                            ],
                        },
                    ],
                    'fields': [
                        {
                            'name': 'New field',
                            'api_name': 'field-123',
                            'type': FieldType.NUMBER,
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

    task_fieldset_1 = fieldsets[0]
    assert task_fieldset_1['api_name'] == fieldset.api_name
    assert task_fieldset_1['title'] == fieldset.title

    fields = task_fieldset_1['fields']
    assert len(fields) == 1
    field_1 = fields[0]
    assert field_1['api_name'] == field.api_name

    selections = field_1['selections']
    assert len(selections) == 1
    selection_1 = selections[0]
    assert selection_1['api_name'] == selection.api_name


# Mixed task and kickoff


def test_update__create_kickoff_and_task_different_fieldsets__ok(
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
                    'fieldsets': [
                        {
                            'shared_fieldset_id': shared_2.id,
                        },
                    ],
                },
            ],
        },
    )

    # assert
    assert response.status_code == 200
    kickoff_fieldsets = response.data['kickoff']['fieldsets']
    task_fieldsets = response.data['tasks'][0]['fieldsets']
    assert len(kickoff_fieldsets) == 1
    assert len(task_fieldsets) == 1
    kickoff_fieldset_1 = kickoff_fieldsets[0]
    task_fieldset_1 = task_fieldsets[0]
    assert kickoff_fieldset_1['shared_fieldset_id'] == shared_1.id
    assert task_fieldset_1['shared_fieldset_id'] == shared_2.id
    assert kickoff.fieldsets.filter(
        shared_fieldset_id=shared_1.id,
    ).count() == 1
    assert task.fieldsets.filter(
        shared_fieldset_id=shared_2.id,
    ).count() == 1


def test_update__create_kickoff_and_task_similar_fieldsets__ok(
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
    kickoff_fieldsets = response.data['kickoff']['fieldsets']
    task_fieldsets = response.data['tasks'][0]['fieldsets']
    assert len(kickoff_fieldsets) == 1
    assert len(task_fieldsets) == 1
    kickoff_fieldset_1 = kickoff_fieldsets[0]
    task_fieldset_1 = task_fieldsets[0]
    assert kickoff_fieldset_1['shared_fieldset_id'] == shared_fieldset.id
    assert task_fieldset_1['shared_fieldset_id'] == shared_fieldset.id
    assert kickoff_fieldset_1['api_name'] != task_fieldset_1['api_name']
    kickoff_fieldset = kickoff.fieldsets.get(
        shared_fieldset_id=shared_fieldset.id,
    )
    task_fieldset = task.fieldsets.get(
        shared_fieldset_id=shared_fieldset.id,
    )
    assert kickoff_fieldset.api_name != task_fieldset.api_name


def test_update__activate_draft_preserves_fs_field_api_names_in_task_text__ok(
    mocker,
    api_client,
):

    """ Draft expands fieldset fields with api_names that may be inserted
        into task title/description. Activating the template must keep
        those api_names instead of regenerating them. """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    shared_fieldset = create_test_shared_fieldset(account=account)
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
    mocker.patch(
        'src.processes.views.template.AnalyticService.templates_created',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    api_client.token_authenticate(user)

    draft_response = api_client.post(
        path='/templates',
        data={
            'name': 'Draft with fieldset',
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
                        'shared_fieldset_id': shared_fieldset.id,
                    },
                ],
            },
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
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
    assert draft_response.status_code == 200
    draft_fieldset = draft_response.data['kickoff']['fieldsets'][0]
    draft_field_api_name = draft_fieldset['fields'][0]['api_name']
    draft_fieldset_api_name = draft_fieldset['api_name']
    task_name = f'Step with {{{{ {draft_field_api_name} }}}}'
    task_description = f'Desc {{{{ {draft_field_api_name} }}}}'

    # act
    response = api_client.put(
        path=f'/templates/{draft_response.data["id"]}',
        data={
            'id': draft_response.data['id'],
            'name': 'Draft with fieldset',
            'is_active': True,
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
                        **draft_fieldset,
                        'shared_fieldset_id': shared_fieldset.id,
                    },
                ],
            },
            'tasks': [
                {
                    'number': 1,
                    'name': task_name,
                    'description': task_description,
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

    # assert
    assert response.status_code == 200
    fieldset = FieldsetTemplate.objects.get(
        kickoff__template_id=draft_response.data['id'],
        shared_fieldset=shared_fieldset,
        is_shared=False,
    )
    field = fieldset.fields.get()
    assert field.api_name == draft_field_api_name
    assert fieldset.api_name == draft_fieldset_api_name

    fieldset_data = response.data['kickoff']['fieldsets'][0]
    field_data = fieldset_data['fields'][0]
    task_data = response.data['tasks'][0]
    assert field_data['api_name'] == draft_field_api_name
    assert task_data['name'] == task_name
    assert task_data['description'] == task_description


def test_update__activate_draft_preserves_task_fieldset_api_names__ok(
    mocker,
    api_client,
):

    """ Draft task fieldset field api_names used in a later task text
        must be preserved on activate. """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    shared_fieldset = create_test_shared_fieldset(account=account)
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
    mocker.patch(
        'src.processes.views.template.AnalyticService.templates_created',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    api_client.token_authenticate(user)

    draft_response = api_client.post(
        path='/templates',
        data={
            'name': 'Draft with task fieldset',
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
                    'name': 'First step',
                    'api_name': 'task-1',
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
                {
                    'number': 2,
                    'name': 'Second step',
                    'api_name': 'task-2',
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
    assert draft_response.status_code == 200
    draft_fieldset = draft_response.data['tasks'][0]['fieldsets'][0]
    draft_field_api_name = draft_fieldset['fields'][0]['api_name']
    task_name = f'Step with {{{{ {draft_field_api_name} }}}}'
    task_description = f'Desc {{{{ {draft_field_api_name} }}}}'

    # act
    response = api_client.put(
        path=f'/templates/{draft_response.data["id"]}',
        data={
            'id': draft_response.data['id'],
            'name': 'Draft with task fieldset',
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
                    'api_name': 'task-1',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                    'fieldsets': [
                        {
                            **draft_fieldset,
                            'shared_fieldset_id': shared_fieldset.id,
                        },
                    ],
                },
                {
                    'number': 2,
                    'name': task_name,
                    'description': task_description,
                    'api_name': 'task-2',
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
        task__template_id=draft_response.data['id'],
        task__api_name='task-1',
        shared_fieldset=shared_fieldset,
        is_shared=False,
    )
    field = fieldset.fields.get()
    task_1_data = response.data['tasks'][0]
    task_2_data = response.data['tasks'][1]
    fieldset_data = task_1_data['fieldsets'][0]
    field_data = fieldset_data['fields'][0]
    assert field.api_name == draft_field_api_name
    assert field_data['api_name'] == draft_field_api_name
    assert task_2_data['name'] == task_name
    assert task_2_data['description'] == task_description


def test_update__activate_draft_preserves_kickoff_fieldset_rule_api_names__ok(
    mocker,
    api_client,
):

    """ Draft kickoff fieldset rule/field/selection api_names must be
        preserved on activate. """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    shared_fieldset = create_test_shared_fieldset(
        account=account,
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='100',
    )
    shared_number_field = shared_fieldset.fields.first()
    shared_rule = shared_fieldset.rules.first()
    shared_rule.fields.add(shared_number_field)
    shared_dropdown_field = FieldTemplate.objects.create(
        fieldset=shared_fieldset,
        account=account,
        name='Dropdown field',
        type=FieldType.DROPDOWN,
        order=2,
        api_name=f'{shared_fieldset.api_name}-field-dropdown',
    )
    FieldTemplateSelection.objects.create(
        field_template=shared_dropdown_field,
        value='Option A',
        api_name=f'{shared_fieldset.api_name}-selection-1',
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
    mocker.patch(
        'src.processes.views.template.AnalyticService.templates_created',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_created',
    )
    api_client.token_authenticate(user)

    draft_response = api_client.post(
        path='/templates',
        data={
            'name': 'Draft with rules',
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
                        'shared_fieldset_id': shared_fieldset.id,
                    },
                ],
            },
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
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
    assert draft_response.status_code == 200
    draft_fieldset = draft_response.data['kickoff']['fieldsets'][0]
    # FieldTemplate ordering is -order: dropdown (2), number (1)
    draft_dropdown_data = draft_fieldset['fields'][0]
    draft_number_data = draft_fieldset['fields'][1]
    draft_selection_data = draft_dropdown_data['selections'][0]
    draft_number_api_name = draft_number_data['api_name']
    draft_dropdown_api_name = draft_dropdown_data['api_name']
    draft_selection_api_name = draft_selection_data['api_name']
    draft_rule_api_name = draft_fieldset['rules'][0]['api_name']
    assert draft_fieldset['rules'][0]['fields'] == [draft_number_api_name]

    # act
    response = api_client.put(
        path=f'/templates/{draft_response.data["id"]}',
        data={
            'id': draft_response.data['id'],
            'name': 'Draft with rules',
            'is_active': True,
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
                        **draft_fieldset,
                    },
                ],
            },
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
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

    # assert
    assert response.status_code == 200
    fieldset = FieldsetTemplate.objects.get(
        kickoff__template_id=draft_response.data['id'],
        shared_fieldset=shared_fieldset,
        is_shared=False,
    )
    number_field = fieldset.fields.get(api_name=draft_number_api_name)
    dropdown_field = fieldset.fields.get(api_name=draft_dropdown_api_name)
    selection = dropdown_field.selections.get(
        api_name=draft_selection_api_name,
    )
    rule = fieldset.rules.get(api_name=draft_rule_api_name)
    rule_field = rule.fields.get(api_name=draft_number_api_name)
    assert selection.value == 'Option A'
    assert rule.api_name == draft_rule_api_name
    assert rule_field == number_field

    fieldset_data = response.data['kickoff']['fieldsets'][0]
    field_1_data = fieldset_data['fields'][0]
    field_2_data = fieldset_data['fields'][1]
    selection_data = field_1_data['selections'][0]
    rule_data = fieldset_data['rules'][0]
    assert field_1_data['api_name'] == draft_dropdown_api_name
    assert field_2_data['api_name'] == draft_number_api_name
    assert selection_data['api_name'] == draft_selection_api_name
    assert rule_data['api_name'] == draft_rule_api_name
    assert rule_data['fields'] == [draft_number_api_name]


def test_update__duplicate_fieldset_api_name__validation_error(
    mocker,
    api_client,
):

    """ Kickoff and task fieldsets must not share api_name. """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    shared_fieldset = create_test_shared_fieldset(account=account)
    fs_api_name = 'fs-duplicate'

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
                'fieldsets': [
                    {
                        'shared_fieldset_id': shared_fieldset.id,
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
                    'fieldsets': [
                        {
                            'shared_fieldset_id': shared_fieldset.id,
                            'api_name': fs_api_name,
                        },
                    ],
                },
            ],
        },
    )

    # assert
    assert response.status_code == 400
    message = MSG_FS_0013(
        name=task.name,
        api_name=fs_api_name,
    )
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['api_name'] == fs_api_name


def test_update__duplicate_fieldset_rule_api_name__validation_error(
    mocker,
    api_client,
):

    """ Duplicate rule api_name across kickoff and task fieldsets
        must fail validation. """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    shared_fieldset = create_test_shared_fieldset(
        account=account,
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='100',
    )
    fs_rule_api_name = 'fs-rule'
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
                'fieldsets': [
                    {
                        'shared_fieldset_id': shared_fieldset.id,
                        'rules': [
                            {
                                'type': FieldSetRuleType.SUM_EQUAL,
                                'value': '100',
                                'api_name': fs_rule_api_name,
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
                    'fieldsets': [
                        {
                            'shared_fieldset_id': shared_fieldset.id,
                            'rules': [
                                {
                                    'type': FieldSetRuleType.SUM_EQUAL,
                                    'value': '100',
                                    'api_name': fs_rule_api_name,
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
    message = MSG_FS_0014(
        name=task.name,
        api_name=fs_rule_api_name,
    )
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['api_name'] == fs_rule_api_name


def test_update__duplicate_fieldset_field_api_name__validation_error(
    mocker,
    api_client,
):

    """ Duplicate field api_name across kickoff and task fieldsets
        must fail validation. """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    shared_fieldset = create_test_shared_fieldset(account=account)
    kickoff_fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=kickoff,
        shared_fieldset=shared_fieldset,
        api_name='fs-kickoff',
    )
    kickoff_field = kickoff_fieldset.fields.first()
    field_api_name = 'field-api-name'
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
                'fieldsets': [
                    {
                        'shared_fieldset_id': shared_fieldset.id,
                        'fields': [
                            {
                                'name': kickoff_field.name,
                                'type': kickoff_field.type,
                                'order': kickoff_field.order,
                                'api_name': field_api_name,
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
                    'fieldsets': [
                        {
                            'shared_fieldset_id': shared_fieldset.id,
                            'fields': [
                                {
                                    'name': kickoff_field.name,
                                    'type': kickoff_field.type,
                                    'order': kickoff_field.order,
                                    'api_name': field_api_name,
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
    message = MSG_FS_0015(
        name=task.name,
        field_name=kickoff_field.name,
        api_name=field_api_name,
    )
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['api_name'] == field_api_name


def test_update__duplicate_fieldset_selection_api_name__validation_error(
    mocker,
    api_client,
):

    """ Duplicate selection api_name across kickoff and task fieldsets
        must fail validation. """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    shared_fieldset = create_test_shared_fieldset(account=account)
    shared_fieldset.fields.all().delete()
    shared_dropdown_field = FieldTemplate.objects.create(
        fieldset=shared_fieldset,
        account=account,
        name='Dropdown field',
        type=FieldType.DROPDOWN,
        order=1,
        api_name=f'{shared_fieldset.api_name}-field-dropdown',
    )
    FieldTemplateSelection.objects.create(
        field_template=shared_dropdown_field,
        value='Option A',
        api_name=f'{shared_fieldset.api_name}-selection-1',
    )
    selection_api_name = 'selection-1'

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
                'fieldsets': [
                    {
                        'shared_fieldset_id': shared_fieldset.id,
                        'fields': [
                            {
                                'name': shared_dropdown_field.name,
                                'type': shared_dropdown_field.type,
                                'order': 1,
                                'selections': [
                                    {
                                        'value': 'Option B',
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
                            'fields': [
                                {
                                    'name': shared_dropdown_field.name,
                                    'order': 1,
                                    'type': shared_dropdown_field.type,
                                    'selections': [
                                        {
                                            'value': 'Option B',
                                            'api_name': selection_api_name,
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
    message = MSG_FS_0016(
        name=task.name,
        api_name=selection_api_name,
    )
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['api_name'] == selection_api_name


def test_update__add_fieldset_with_expanded_fields__preserves_api_names(
    mocker,
    api_client,
):

    """ Adding a fieldset with expanded fields to an active template
        must keep provided api_names. """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user, is_active=True, tasks_count=1)
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    shared_fieldset = create_test_shared_fieldset(account=account)
    fs_api_name = 'added-fs-api-name'
    field_api_name = 'added-field-api-name'
    selection_api_name = 'added-selection-api-name'
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
            'name': template.name,
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
                        'api_name': fs_api_name,
                        'order': 1,
                        'title': 'Added title',
                        'description': 'Added desc',
                        'name': shared_fieldset.name,
                        'fields': [
                            {
                                'name': 'Dropdown field',
                                'type': FieldType.DROPDOWN,
                                'order': 1,
                                'api_name': field_api_name,
                                'is_required': False,
                                'is_hidden': False,
                                'description': '',
                                'default': '',
                                'selections': [
                                    {
                                        'value': 'Option A',
                                        'api_name': selection_api_name,
                                    },
                                ],
                            },
                        ],
                        'rules': [],
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
    field = fieldset.fields.get()
    selection = field.selections.get()
    fieldset_data = response.data['kickoff']['fieldsets'][0]
    field_data = fieldset_data['fields'][0]
    selection_data = field_data['selections'][0]
    assert fieldset.api_name == fs_api_name
    assert field.api_name == field_api_name
    assert selection.api_name == selection_api_name
    assert fieldset_data['api_name'] == fs_api_name
    assert field_data['api_name'] == field_api_name
    assert selection_data['api_name'] == selection_api_name


def test_update__existing_fieldset_ignores_fields_in_payload__ok(
    mocker,
    api_client,
):

    """ Updating an existing fieldset by api_name must ignore fields
        from payload and only apply order/title/description changes. """

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
        title='Original title',
        description='Original desc',
        order=1,
        api_name='existing-fs',
    )
    original_field = fieldset.fields.get()
    original_field_api_name = original_field.api_name
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
    new_title = 'Updated title'
    new_description = 'Updated desc'
    new_order = 5

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data={
            'id': template.id,
            'is_active': True,
            'name': template.name,
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
                        'api_name': fieldset.api_name,
                        'order': new_order,
                        'title': new_title,
                        'description': new_description,
                        'fields': [
                            {
                                'name': 'Tampered field',
                                'type': FieldType.STRING,
                                'order': 99,
                                'api_name': 'tampered-field-api-name',
                                'is_required': True,
                                'is_hidden': False,
                                'description': 'should be ignored',
                                'default': '',
                            },
                        ],
                        'rules': [],
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
    fieldset.refresh_from_db()
    assert fieldset.title == new_title
    assert fieldset.description == new_description
    assert fieldset.order == new_order
    field = fieldset.fields.get()
    fieldset_data = response.data['kickoff']['fieldsets'][0]
    field_data = fieldset_data['fields'][0]
    assert fieldset.fields.count() == 1
    assert field.api_name == original_field_api_name
    assert field_data['api_name'] == original_field_api_name
    assert field.api_name != 'tampered-field-api-name'


def test_update__create_fieldset_with_shared_api_names__preserved_in_response(
    mocker,
    api_client,
):

    """ PUT with expanded fieldset using the same api_names as shared
        must return those api_names in the response. """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    shared_fieldset = create_test_shared_fieldset(
        account=account,
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='100',
    )
    shared_number_field = shared_fieldset.fields.first()
    shared_rule = shared_fieldset.rules.first()
    shared_dropdown_field = FieldTemplate.objects.create(
        fieldset=shared_fieldset,
        account=account,
        name='Dropdown field',
        type=FieldType.DROPDOWN,
        order=2,
        api_name=f'{shared_fieldset.api_name}-field-dropdown',
    )
    shared_selection = FieldTemplateSelection.objects.create(
        field_template=shared_dropdown_field,
        value='Option A',
        api_name=f'{shared_fieldset.api_name}-selection-1',
    )
    shared_rule.fields.add(shared_dropdown_field)

    template = create_test_template(user, is_active=False, tasks_count=1)
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
            'is_active': False,
            'name': template.name,
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
                        'api_name': shared_fieldset.api_name,
                        'order': 1,
                        'title': shared_fieldset.title,
                        'description': shared_fieldset.description,
                        'name': shared_fieldset.name,
                        'label_position': shared_fieldset.label_position,
                        'layout': shared_fieldset.layout,
                        'fields': [
                            {
                                'name': shared_number_field.name,
                                'type': shared_number_field.type,
                                'order': shared_number_field.order,
                                'api_name': shared_number_field.api_name,
                                'is_required': False,
                                'is_hidden': False,
                                'description': '',
                                'default': '',
                            },
                            {
                                'name': shared_dropdown_field.name,
                                'type': shared_dropdown_field.type,
                                'order': shared_dropdown_field.order,
                                'api_name': shared_dropdown_field.api_name,
                                'selections': [
                                    {
                                        'value': shared_selection.value,
                                        'api_name': shared_selection.api_name,
                                    },
                                ],
                            },
                        ],
                        'rules': [
                            {
                                'type': shared_rule.type,
                                'value': shared_rule.value,
                                'api_name': shared_rule.api_name,
                                'fields': [shared_number_field.api_name],
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
    fieldset_data = response.data['kickoff']['fieldsets'][0]
    # FieldTemplate ordering is -order: dropdown (2), number (1)
    dropdown_data = fieldset_data['fields'][0]
    number_data = fieldset_data['fields'][1]
    selection_data = dropdown_data['selections'][0]
    rule_data = fieldset_data['rules'][0]

    assert fieldset_data['api_name'] == shared_fieldset.api_name
    assert number_data['api_name'] != shared_number_field.api_name
    assert dropdown_data['api_name'] != shared_dropdown_field.api_name
    assert selection_data['api_name'] != shared_selection.api_name
    assert rule_data['api_name'] != shared_rule.api_name
    assert rule_data['fields'] != [shared_number_field.api_name]
