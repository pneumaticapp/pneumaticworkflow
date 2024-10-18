import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template
)
from pneumatic_backend.processes.models import (
    ChecklistTemplate,
    ChecklistTemplateSelection
)
from pneumatic_backend.processes.enums import (
    PerformerType,
)
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.messages import template as messages


pytestmark = pytest.mark.django_db


def test_update__create__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True
    )
    task = template.tasks.first()
    checklist = ChecklistTemplate.objects.create(
        template=template,
        task=task,
        api_name='checklist-1'
    )
    checklist_selection = ChecklistTemplateSelection.objects.create(
        checklist=checklist,
        template=template,
        value='some value',
        api_name='cl-selection-1'
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated'
    )
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.checklist_created'
    )
    checklists_data = [
        {
            'id': checklist.id,
            'api_name': checklist.api_name,
            'selections': [
                {
                    'id': checklist_selection.id,
                    'api_name': checklist_selection.api_name,
                    'value': checklist_selection.value
                },
                {
                    'api_name': 'selection-2',
                    'value': 'some value 2'
                }
            ]
        }
    ]

    # act
    response = api_client.put(
        f'/templates/{template.id}',
        data={
            'id': template.id,
            'name': template.name,
            'is_active': True,
            'template_owners': [user.id],
            'kickoff': {'id': template.kickoff_instance.id},
            'tasks': [
                {
                    'id': task.id,
                    'number': task.number,
                    'name': task.name,
                    'api_name': task.api_name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ],
                    'checklists': checklists_data
                }
            ]
        }
    )

    # assert
    assert response.status_code == 200
    checklist_1_data = response.data['tasks'][0]['checklists'][0]
    assert len(checklist_1_data['selections']) == 2

    selection_1_data = checklist_1_data['selections'][0]
    assert selection_1_data.get('id') is None
    assert selection_1_data['api_name'] == checklist_selection.api_name
    assert selection_1_data['value'] == checklist_selection.value

    selection_2_data = checklist_1_data['selections'][1]
    assert selection_2_data.get('id') is None
    assert selection_2_data['api_name'] == 'selection-2'
    assert selection_2_data['value'] == 'some value 2'

    template_id = response.data['id']
    assert ChecklistTemplateSelection.objects.filter(
        template_id=template_id,
        checklist_id=checklist.id,
        api_name='selection-2',
        value='some value 2'
    ).exists()


def test_update__delete__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True
    )
    task = template.tasks.first()
    checklist = ChecklistTemplate.objects.create(
        template=template,
        task=task,
        api_name='checklist-1'
    )
    checklist_selection = ChecklistTemplateSelection.objects.create(
        checklist=checklist,
        template=template,
        value='some value',
        api_name='cl-selection-1'
    )
    checklist_selection_2 = ChecklistTemplateSelection.objects.create(
        checklist=checklist,
        template=template,
        value='some value 2',
        api_name='cl-selection-2'
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated'
    )
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.checklist_created'
    )
    checklists_data = [
        {
            'id': checklist.id,
            'api_name': checklist.api_name,
            'selections': [
                {
                    'id': checklist_selection.id,
                    'api_name': checklist_selection.api_name,
                    'value': checklist_selection.value
                }
            ]
        }
    ]

    # act
    response = api_client.put(
        f'/templates/{template.id}',
        data={
            'id': template.id,
            'name': template.name,
            'is_active': True,
            'template_owners': [user.id],
            'kickoff': {'id': template.kickoff_instance.id},
            'tasks': [
                {
                    'id': task.id,
                    'number': task.number,
                    'name': task.name,
                    'api_name': task.api_name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ],
                    'checklists': checklists_data
                }
            ]
        }
    )

    # assert
    assert response.status_code == 200
    checklist_data = response.data['tasks'][0]['checklists'][0]
    assert len(checklist_data['selections']) == 1
    selection_1_data = checklist_data['selections'][0]
    assert selection_1_data.get('id') is None
    assert selection_1_data['api_name'] == checklist_selection.api_name
    assert selection_1_data['value'] == checklist_selection.value
    assert not ChecklistTemplateSelection.objects.filter(
        id=checklist_selection_2.id
    ).exists()


def test_update__api_name_null__validation_error(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True
    )
    task = template.tasks.first()
    checklist = ChecklistTemplate.objects.create(
        template=template,
        task=task,
        api_name='checklist-1'
    )
    checklist_selection = ChecklistTemplateSelection.objects.create(
        checklist=checklist,
        template=template,
        value='some value',
        api_name='cl-selection-1'
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated'
    )
    checklists_data = [
        {
            'id': checklist.id,
            'api_name': checklist.api_name,
            'selections': [
                {
                    'id': checklist_selection.id,
                    'value': checklist_selection.value,
                    'api_name': None,
                }
            ]
        }
    ]

    # act
    response = api_client.put(
        f'/templates/{template.id}',
        data={
            'id': template.id,
            'name': template.name,
            'is_active': True,
            'template_owners': [user.id],
            'kickoff': {'id': template.kickoff_instance.id},
            'tasks': [
                {
                    'id': task.id,
                    'number': task.number,
                    'name': task.name,
                    'api_name': task.api_name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ],
                    'checklists': checklists_data
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    message = 'Api_name: this field may not be null.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['api_name'] == 'checklist-1'


def test_update__union_two_checklists__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True
    )
    task = template.tasks.first()
    checklist = ChecklistTemplate.objects.create(
        template=template,
        task=task,
        api_name='checklist-1'
    )
    checklist_selection = ChecklistTemplateSelection.objects.create(
        checklist=checklist,
        template=template,
        value='some value',
        api_name='cl-selection-1'
    )
    checklist_2 = ChecklistTemplate.objects.create(
        template=template,
        task=task,
        api_name='checklist-2'
    )
    checklist_selection_2 = ChecklistTemplateSelection.objects.create(
        checklist=checklist_2,
        template=template,
        value='some value 2',
        api_name='cl-selection-2'
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated'
    )
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.checklist_created'
    )
    checklists_data = [
        {
            'api_name': checklist.api_name,
            'selections': [
                {
                    'api_name': checklist_selection.api_name,
                    'value': checklist_selection.value
                },
                {
                    'api_name': checklist_selection_2.api_name,
                    'value': checklist_selection_2.value
                }
            ]
        }
    ]

    # act
    response = api_client.put(
        f'/templates/{template.id}',
        data={
            'id': template.id,
            'name': template.name,
            'is_active': True,
            'template_owners': [user.id],
            'kickoff': {'id': template.kickoff_instance.id},
            'tasks': [
                {
                    'id': task.id,
                    'number': task.number,
                    'name': task.name,
                    'api_name': task.api_name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ],
                    'checklists': checklists_data
                }
            ]
        }
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['tasks'][0]['checklists']) == 1
    checklist_data = response.data['tasks'][0]['checklists'][0]

    assert len(checklist_data['selections']) == 2
    selection_data = checklist_data['selections'][0]
    assert selection_data['api_name'] == checklist_selection.api_name
    assert selection_data['value'] == checklist_selection.value

    selection_data_2 = checklist_data['selections'][1]
    assert selection_data_2['api_name'] == checklist_selection_2.api_name
    assert selection_data_2['value'] == checklist_selection_2.value


def test_update__move_selection_to_another_checklist__ok(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True
    )
    task = template.tasks.first()
    checklist = ChecklistTemplate.objects.create(
        template=template,
        task=task,
        api_name='checklist-1'
    )
    checklist_selection = ChecklistTemplateSelection.objects.create(
        checklist=checklist,
        template=template,
        value='some value',
        api_name='cl-selection-1'
    )
    checklist_2 = ChecklistTemplate.objects.create(
        template=template,
        task=task,
        api_name='checklist-2'
    )
    checklist_selection_2 = ChecklistTemplateSelection.objects.create(
        checklist=checklist_2,
        template=template,
        value='some value 2',
        api_name='cl-selection-2'
    )
    checklist_selection_3 = ChecklistTemplateSelection.objects.create(
        checklist=checklist_2,
        template=template,
        value='some value 3',
        api_name='cl-selection-3'
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated'
    )
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.checklist_created'
    )
    checklists_data = [
        {
            'api_name': checklist.api_name,
            'selections': [
                {
                    'api_name': checklist_selection.api_name,
                    'value': checklist_selection.value
                },
                {
                    'api_name': checklist_selection_2.api_name,
                    'value': checklist_selection_2.value
                }
            ]
        },
        {
            'api_name': checklist_2.api_name,
            'selections': [
                {
                    'api_name': checklist_selection_3.api_name,
                    'value': checklist_selection_3.value
                }
            ]
        }
    ]

    # act
    response = api_client.put(
        f'/templates/{template.id}',
        data={
            'id': template.id,
            'name': template.name,
            'is_active': True,
            'template_owners': [user.id],
            'kickoff': {'id': template.kickoff_instance.id},
            'tasks': [
                {
                    'id': task.id,
                    'number': task.number,
                    'name': task.name,
                    'api_name': task.api_name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ],
                    'checklists': checklists_data
                }
            ]
        }
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['tasks'][0]['checklists']) == 2
    checklist_data = response.data['tasks'][0]['checklists'][0]
    checklist_data_2 = response.data['tasks'][0]['checklists'][1]

    assert len(checklist_data['selections']) == 2
    selection_data = checklist_data['selections'][0]
    assert selection_data['api_name'] == checklist_selection.api_name
    assert selection_data['value'] == checklist_selection.value

    selection_data_2 = checklist_data['selections'][1]
    assert selection_data_2['api_name'] == checklist_selection_2.api_name
    assert selection_data_2['value'] == checklist_selection_2.value

    assert len(checklist_data_2['selections']) == 1
    selection_data_3 = checklist_data_2['selections'][0]
    assert selection_data_3['api_name'] == checklist_selection_3.api_name
    assert selection_data_3['value'] == checklist_selection_3.value


def test_update__move_selection_to_new_checklist__ok(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True
    )
    task = template.tasks.first()
    checklist = ChecklistTemplate.objects.create(
        template=template,
        task=task,
        api_name='checklist-1'
    )
    checklist_selection = ChecklistTemplateSelection.objects.create(
        checklist=checklist,
        template=template,
        value='some value',
        api_name='cl-selection-1'
    )
    checklist_selection_2 = ChecklistTemplateSelection.objects.create(
        checklist=checklist,
        template=template,
        value='some value 2',
        api_name='cl-selection-2'
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated'
    )
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.checklist_created'
    )
    checklists_data = [
        {
            'api_name': 'new-checklist',
            'selections': [
                {
                    'api_name': checklist_selection_2.api_name,
                    'value': checklist_selection_2.value
                },
                {
                    'api_name': 'new-selection',
                    'value': 'new value'
                }
            ]
        },
        {
            'api_name': checklist.api_name,
            'selections': [
                {
                    'api_name': checklist_selection.api_name,
                    'value': checklist_selection.value
                }
            ]
        }
    ]

    # act
    response = api_client.put(
        f'/templates/{template.id}',
        data={
            'id': template.id,
            'name': template.name,
            'is_active': True,
            'template_owners': [user.id],
            'kickoff': {'id': template.kickoff_instance.id},
            'tasks': [
                {
                    'id': task.id,
                    'number': task.number,
                    'name': task.name,
                    'api_name': task.api_name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ],
                    'checklists': checklists_data
                }
            ]
        }
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['tasks'][0]['checklists']) == 2
    checklist_data = response.data['tasks'][0]['checklists'][1]
    checklist_data_2 = response.data['tasks'][0]['checklists'][0]

    assert len(checklist_data['selections']) == 2
    selection_data = checklist_data['selections'][0]
    assert selection_data['api_name'] == checklist_selection_2.api_name
    assert selection_data['value'] == checklist_selection_2.value

    selection_data_2 = checklist_data['selections'][1]
    assert selection_data_2['api_name'] == 'new-selection'
    assert selection_data_2['value'] == 'new value'

    assert len(checklist_data_2['selections']) == 1
    selection_data_3 = checklist_data_2['selections'][0]
    assert selection_data_3['api_name'] == checklist_selection.api_name
    assert selection_data_3['value'] == checklist_selection.value


def test_update__duplicate_api_name_in_one_checklist__save_last(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True
    )
    task = template.tasks.first()
    checklist = ChecklistTemplate.objects.create(
        template=template,
        task=task,
        api_name='checklist-1'
    )
    checklist_selection = ChecklistTemplateSelection.objects.create(
        checklist=checklist,
        template=template,
        value='some value',
        api_name='cl-selection-1'
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated'
    )
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.checklist_created'
    )
    checklists_data = [
        {
            'api_name': 'new-checklist',
            'selections': [
                {
                    'api_name': checklist_selection.api_name,
                    'value': checklist_selection.value
                },
                {
                    'api_name': checklist_selection.api_name,
                    'value': 'new value'
                }
            ]
        }
    ]

    # act
    response = api_client.put(
        f'/templates/{template.id}',
        data={
            'id': template.id,
            'name': template.name,
            'is_active': True,
            'template_owners': [user.id],
            'kickoff': {'id': template.kickoff_instance.id},
            'tasks': [
                {
                    'id': task.id,
                    'number': task.number,
                    'name': task.name,
                    'api_name': task.api_name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ],
                    'checklists': checklists_data
                }
            ]
        }
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['tasks'][0]['checklists']) == 1
    checklist_data = response.data['tasks'][0]['checklists'][0]

    assert len(checklist_data['selections']) == 1
    selection_data = checklist_data['selections'][0]
    assert selection_data['api_name'] == checklist_selection.api_name
    assert selection_data['value'] == 'new value'


def test_update__equal_api_names_in_different_checklists__validation_error(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.checklist_created'
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    step = 'First step'
    checklist_item_api_name = 'cl-selection-1'
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True
    )
    task = template.tasks.first()
    checklist = ChecklistTemplate.objects.create(
        template=template,
        task=task,
        api_name='checklist-1'
    )
    checklist_selection = ChecklistTemplateSelection.objects.create(
        checklist=checklist,
        template=template,
        value='some value',
        api_name=checklist_item_api_name
    )

    # act
    response = api_client.put(
        f'/templates/{template.id}',
        data={
            'id': template.id,
            'name': template.name,
            'is_active': True,
            'template_owners': [user.id],
            'kickoff': {'id': template.kickoff_instance.id},
            'tasks': [
                {
                    'id': task.id,
                    'number': task.number,
                    'name': step,
                    'api_name': task.api_name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ],
                    'checklists': [
                        {
                            'api_name': checklist.api_name,
                            'selections': [
                                {
                                    'api_name': checklist_selection.api_name,
                                    'value': checklist_selection.value
                                }
                            ]
                        },
                        {
                            'api_name': 'checklist-2',
                            'selections': [
                                {
                                    'api_name': checklist_selection.api_name,
                                    'value': 'another value'
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    message = messages.MSG_PT_0048(
        step_name=step,
        api_name=checklist_item_api_name
    )
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['api_name'] == checklist_item_api_name
