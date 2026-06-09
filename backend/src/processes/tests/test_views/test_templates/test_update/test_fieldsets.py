import pytest

from src.processes.enums import (
    OwnerRole,
    OwnerType,
    PerformerType,
)
from src.processes.models.templates.fieldset import FieldsetTemplate
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_fieldset_template,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db

# Kickoff fieldsets


def test_update__kickoff_with_one_fieldset__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user,
        is_active=True,
        tasks_count=1,
    )
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        api_name='fieldset-update-1',
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
        'src.processes.views.template.'
        'AnalyticService.templates_updated',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    request_data = {
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
                    'api_name': fieldset.api_name,
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
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['kickoff'] == {
        'fields': [],
        'fieldsets': [
            {
                'api_name': fieldset.api_name,
                'order': 3,
            },
        ],
    }
    assert FieldsetTemplate.objects.get(
        kickoff=kickoff,
        fieldset=fieldset,
        order=3,
    )


def test_update__kickoff_create_two_fieldsets__ok(
    mocker,
    api_client,
):

    """ Updating a template with multiple fieldsets linked to
        kickoff creates multiple FieldsetTemplateKickoff records. """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user,
        is_active=True,
        tasks_count=1,
    )
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    fieldset_1 = create_test_fieldset_template(
        account=account,
        template=template,
        api_name='fieldset-x',
    )
    fieldset_2 = create_test_fieldset_template(
        account=account,
        template=template,
        api_name='fieldset-y',
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
        'src.processes.views.template.'
        'AnalyticService.templates_updated',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    request_data = {
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
                    'api_name': fieldset_1.api_name,
                    'order': 0,
                },
                {
                    'api_name': fieldset_2.api_name,
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
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['kickoff'] == {
        'fields': [],
        'fieldsets': [
            {
                'api_name': fieldset_1.api_name,
                'order': 0,
            },
            {
                'api_name': fieldset_2.api_name,
                'order': 1,
            },
        ],
    }
    assert FieldsetTemplateKickoff.objects.filter(
        fieldset=fieldset_1,
        kickoff=kickoff,
        order=0,
    ).count() == 1
    assert FieldsetTemplateKickoff.objects.filter(
        fieldset=fieldset_2,
        kickoff=kickoff,
        order=1,
    ).count() == 1


def test_update__kickoff_replace_fieldset__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user,
        is_active=True,
        tasks_count=1,
    )
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    fieldset_1 = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=kickoff,
    )
    fieldset_2 = create_test_fieldset_template(
        account=account,
        template=template,
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
        'src.processes.views.template.'
        'AnalyticService.templates_updated',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    request_data = {
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
                    'api_name': fieldset_2.api_name,
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
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['kickoff'] == {
        'fields': [],
        'fieldsets': [
            {
                'api_name': fieldset_2.api_name,
                'order': 2,
            },
        ],
    }
    assert FieldsetTemplateKickoff.objects.filter(
        fieldset=fieldset_1,
        kickoff=kickoff,
    ).count() == 0
    assert FieldsetTemplateKickoff.objects.filter(
        fieldset=fieldset_2,
        kickoff=kickoff,
        order=2,
    ).count() == 1


def test_update__kickoff_remove_fieldset__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user,
        is_active=True,
        tasks_count=1,
    )
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=kickoff,
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
        'src.processes.views.template.'
        'AnalyticService.templates_updated',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    request_data = {
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
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['kickoff'] == {
        'fields': [],
        'fieldsets': [],
    }
    fieldset.refresh_from_db()
    assert FieldsetTemplateKickoff.objects.filter(
        fieldset=fieldset,
        kickoff=kickoff,
    ).count() == 0


def test_update__kickoff_skip_fieldsets__no_fieldsets_created(
    mocker,
    api_client,
):

    """ Updating a template without fieldsets key in kickoff does not
        create any FieldsetTemplateKickoff records. """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user,
        is_active=True,
        tasks_count=1,
    )
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
        'src.processes.views.template.'
        'AnalyticService.templates_updated',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    request_data = {
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
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    assert FieldsetTemplateKickoff.objects.filter(
        kickoff=kickoff,
    ).count() == 0


# Task fieldsets


def test_update__task_with_one_fieldset__ok(
    mocker,
    api_client,
):

    """ Updating a template with one fieldset linked to a task
        creates a FieldsetTemplateTaskTemplate record. """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user,
        is_active=True,
        tasks_count=1,
    )
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        api_name='fieldset-task-update-1',
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
        'src.processes.views.template.'
        'AnalyticService.templates_updated',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    request_data = {
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
                        'api_name': fieldset.api_name,
                        'order': 2,
                    },
                ],
            },
        ],
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['tasks'][0]['fieldsets'] == [
        {
            'api_name': fieldset.api_name,
            'order': 2,
        },
    ]
    assert FieldsetTemplateTaskTemplate.objects.get(
        task=task,
        fieldset=fieldset,
        order=2,
    )


def test_update__task_create_two_fieldsets__ok(
    mocker,
    api_client,
):

    """ Updating a template with multiple fieldsets linked to a task
        creates multiple FieldsetTemplateTaskTemplate records. """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user,
        is_active=True,
        tasks_count=1,
    )
    task = template.tasks.first()
    kickoff = template.kickoff_instance
    fieldset_1 = create_test_fieldset_template(
        account=account,
        template=template,
        api_name='fieldset-x',
    )
    fieldset_2 = create_test_fieldset_template(
        account=account,
        template=template,
        api_name='fieldset-y',
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
        'src.processes.views.template.'
        'AnalyticService.templates_updated',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    request_data = {
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
                        'api_name': fieldset_1.api_name,
                        'order': 1,
                    },
                    {
                        'api_name': fieldset_2.api_name,
                        'order': 0,
                    },
                ],
            },
        ],
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['tasks'][0]['fieldsets'] == [
        {
            'api_name': fieldset_2.api_name,
            'order': 0,
        },
        {
            'api_name': fieldset_1.api_name,
            'order': 1,
        },
    ]
    assert FieldsetTemplateTaskTemplate.objects.get(
        task=task,
        fieldset=fieldset_1,
        order=1,
    )
    assert FieldsetTemplateTaskTemplate.objects.get(
        task=task,
        fieldset=fieldset_2,
        order=0,
    )


def test_update__task_replace_fieldset__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user,
        is_active=True,
        tasks_count=1,
    )
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    fieldset_1 = create_test_fieldset_template(
        account=account,
        template=template,
        task=task,
    )
    fieldset_2 = create_test_fieldset_template(
        account=account,
        template=template,
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
        'src.processes.views.template.'
        'AnalyticService.templates_updated',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    request_data = {
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
                        'api_name': fieldset_2.api_name,
                        'order': 2,
                    },
                ],
            },
        ],
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['tasks'][0]['fieldsets'] == [
        {
            'api_name': fieldset_2.api_name,
            'order': 2,
        },
    ]
    fieldset_1.refresh_from_db()
    assert FieldsetTemplateTaskTemplate.objects.filter(
        task=task,
        fieldset=fieldset_1,
    ).count() == 0
    assert FieldsetTemplateTaskTemplate.objects.filter(
        task=task,
        fieldset=fieldset_2,
        order=2,
    ).count() == 1


def test_update__tasks_remove_fieldset__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user,
        is_active=True,
        tasks_count=1,
    )
    kickoff = template.kickoff_instance
    task = template.tasks.first()
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        task=task,
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
        'src.processes.views.template.'
        'AnalyticService.templates_updated',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    request_data = {
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
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['tasks'][0]['fieldsets'] == []
    assert FieldsetTemplateTaskTemplate.objects.filter(
        task=task,
        fieldset=fieldset,
    ).count() == 0


def test_update__task_with_empty_fieldsets__no_create_fieldsets(
    mocker,
    api_client,
):

    """ Updating a template with empty fieldsets list in task does not
        create any FieldsetTemplateTaskTemplate records. """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user,
        is_active=True,
        tasks_count=1,
    )
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
        'src.processes.views.template.'
        'AnalyticService.templates_updated',
    )
    mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    request_data = {
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
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data=request_data,
    )

    # assert
    assert response.status_code == 200
    assert FieldsetTemplateTaskTemplate.objects.filter(task=task).count() == 0
