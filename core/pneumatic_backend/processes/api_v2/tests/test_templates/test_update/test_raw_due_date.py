import pytest
from datetime import timedelta
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template
)
from pneumatic_backend.processes.models import (
    RawDueDateTemplate,
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    DueDateRule,
)
from pneumatic_backend.processes.messages import template as messages


pytestmark = pytest.mark.django_db


def test_update__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True
    )
    task_template = template.tasks.first()
    raw_due_date = RawDueDateTemplate.objects.create(
        duration=timedelta(hours=1),
        duration_months=2,
        rule=DueDateRule.AFTER_WORKFLOW_STARTED,
        template=template,
        task=task_template
    )
    new_duration = timedelta(minutes=1)
    new_duration_months = 0
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated'
    )

    # act
    response = api_client.put(
        f'/templates/{template.id}',
        data={
            'id': template.id,
            'name': template.name,
            'is_active': template.is_active,
            'template_owners': [user.id],
            'kickoff': {'id': template.kickoff_instance.id},
            'tasks': [
                {
                    'id': task_template.id,
                    'number': task_template.number,
                    'name': task_template.name,
                    'api_name': task_template.api_name,
                    'raw_due_date': {
                        'api_name': raw_due_date.api_name,
                        'duration': new_duration,
                        'duration_months': new_duration_months,
                        'rule': raw_due_date.rule,
                    },
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 200
    data = response.data['tasks'][0]['raw_due_date']
    assert data['duration'] == '00:01:00'
    assert data['duration_months'] == new_duration_months
    raw_due_date.refresh_from_db()
    assert raw_due_date.duration == new_duration
    assert raw_due_date.duration_months == new_duration_months


def test_update__create__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True
    )
    task_template = template.tasks.first()
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated'
    )
    api_name = 'raw-due-date-1'
    duration = '01:00:00'
    duration_months = 2

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
                    'id': task_template.id,
                    'number': task_template.number,
                    'name': task_template.name,
                    'api_name': task_template.api_name,
                    'raw_due_date': {
                        'api_name': api_name,
                        'duration': duration,
                        'duration_months': duration_months,
                        'rule': DueDateRule.AFTER_WORKFLOW_STARTED,
                    },
                    'raw_performers': [
                        {
                            'api_name': 'raw_due_date-1',
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 200
    data = response.data['tasks'][0]['raw_due_date']
    assert data['api_name'] == api_name
    assert data['rule'] == DueDateRule.AFTER_WORKFLOW_STARTED
    assert data['duration'] == duration
    assert data['duration_months'] == duration_months
    assert RawDueDateTemplate.objects.filter(
        api_name=api_name,
        template_id=template.id,
        task_id=task_template.id,
        rule=DueDateRule.AFTER_WORKFLOW_STARTED,
        source_id=None,
        duration=timedelta(hours=1),
        duration_months=duration_months
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
    task_template = template.tasks.first()
    raw_due_date = RawDueDateTemplate.objects.create(
        duration=timedelta(hours=1),
        rule=DueDateRule.AFTER_WORKFLOW_STARTED,
        template=template,
        task=task_template
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated'
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
                    'id': task_template.id,
                    'number': task_template.number,
                    'name': task_template.name,
                    'api_name': task_template.api_name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ],
                    'raw_due_date': None
                }
            ]
        }
    )

    # assert
    assert response.status_code == 200
    assert response.data['tasks'][0]['raw_due_date'] is None
    assert not RawDueDateTemplate.objects.filter(id=raw_due_date.id).exists()


def test_update__change_api_name__validation_error(api_client, mocker):

    # arrange
    user = create_test_user()
    step = 'Second step'
    due_date_api_name = 'due-date-1'
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=False
    )
    task_template = template.tasks.first()
    raw_due_date = RawDueDateTemplate.objects.create(
        duration=timedelta(hours=1),
        rule=DueDateRule.AFTER_WORKFLOW_STARTED,
        template=template,
        task=task_template,
        api_name=due_date_api_name,
    )
    new_duration = timedelta(minutes=1)
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated'
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
                    'id': task_template.id,
                    'number': task_template.number,
                    'name': 'First step',
                    'api_name': task_template.api_name,
                    'raw_due_date': {
                        'api_name': due_date_api_name,
                        'duration': new_duration,
                        'rule': raw_due_date.rule,
                    },
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                },
                {
                    'number': 2,
                    'api_name': 'task-2',
                    'name': step,
                    'raw_due_date': {
                        'api_name': due_date_api_name,
                        'duration': '01:00:00',
                        'duration_months': 0,
                        'rule': DueDateRule.AFTER_TASK_STARTED,
                        'source_id': 'task-2'
                    },
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    message = messages.MSG_PT_0052(
        step_name=step,
        api_name=due_date_api_name
    )
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['api_name'] == due_date_api_name
