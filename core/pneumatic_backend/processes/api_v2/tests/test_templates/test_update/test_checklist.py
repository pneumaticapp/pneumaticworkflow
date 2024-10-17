import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template
)
from pneumatic_backend.processes.models import (
    ChecklistTemplate,
    ChecklistTemplateSelection,
    TaskTemplate,
)
from pneumatic_backend.processes.enums import (
    PerformerType,
)
from pneumatic_backend.authentication.enums import AuthTokenType
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
    analytics_mock = mocker.patch(
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
                }
            ]
        },
        {
            'api_name': 'checklist-2',
            'selections': [
                {
                    'api_name': 'cl-selection-2',
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
    assert len(response.data['tasks'][0]['checklists']) == 2
    checklist_1_data = response.data['tasks'][0]['checklists'][0]
    assert checklist_1_data['api_name'] == checklist.api_name

    checklist_2_data = response.data['tasks'][0]['checklists'][1]
    assert checklist_2_data.get('id') is None
    assert checklist_2_data['api_name'] == 'checklist-2'

    template_id = response.data['id']
    task_template = TaskTemplate.objects.get(api_name=task.api_name)
    assert ChecklistTemplate.objects.filter(
        template_id=template_id,
        api_name='checklist-2',
        task=task_template,
    ).exists()
    analytics_mock.assert_called_once_with(
        user=user,
        template=template,
        task=task,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )


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
    checklist_2 = ChecklistTemplate.objects.create(
        template=template,
        task=task,
        api_name='checklist-2'
    )
    ChecklistTemplateSelection.objects.create(
        checklist=checklist_2,
        template=template,
        value='some value 2',
        api_name='cl-selection-21'
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated'
    )
    analytics_mock = mocker.patch(
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
    checklist_1_data = response.data['tasks'][0]['checklists'][0]
    assert checklist_1_data['api_name'] == checklist.api_name
    assert not ChecklistTemplate.objects.filter(id=checklist_2.id).exists()
    analytics_mock.assert_not_called()


def test_update__fields_with_equal_api_names__validation_error(
    mocker,
    api_client,
):

    # arrange
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.checklist_created'
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated'
    )
    user = create_test_user()
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True
    )
    task = template.tasks.first()
    checklist_api_name = 'checklist-1'
    step = 'Second step'
    checklist = ChecklistTemplate.objects.create(
        template=template,
        task=task,
        api_name=checklist_api_name
    )
    checklist_selection = ChecklistTemplateSelection.objects.create(
        checklist=checklist,
        template=template,
        value='some value',
        api_name='cl-selection-1'
    )
    api_client.token_authenticate(user)

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
                    'checklists': [
                        {
                            'api_name': checklist_api_name,
                            'selections': [
                                {
                                    'api_name': checklist_selection.api_name,
                                    'value': checklist_selection.value
                                }
                            ]
                        }
                    ]
                },
                {
                    'number': 2,
                    'name': step,
                    'api_name': 'task-2',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ],
                    'checklists': [
                        {
                            'api_name': checklist_api_name,
                            'selections': [
                                {
                                    'api_name': 'cl-selection-2',
                                    'value': 'Some option'
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
    message = messages.MSG_PT_0047(
        step_name=step,
        api_name=checklist_api_name
    )
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['api_name'] == checklist_api_name
