import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template,
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    FieldType,
)
from pneumatic_backend.processes.models import (
    Template
)
from pneumatic_backend.processes.messages.template import (
    MSG_PT_0023,
)

pytestmark = pytest.mark.django_db


def test_discard_changes__active_template__not_change(api_client):

    # arrange
    user = create_test_user()
    request_data = {
        'name': 'Template',
        'description': 'Desc',
        'template_owners': [user.id],
        'is_active': True,
        'kickoff': {
            'description': 'Desc',
        },
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'description': 'Task desc',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id
                    }
                ]
            }
        ]
    }
    api_client.token_authenticate(user)

    response_create = api_client.post(
        path='/templates',
        data=request_data
    )
    template_id = response_create.data['id']

    # act
    response = api_client.post(f'/templates/{template_id}/discard-changes')

    # assert
    assert response_create.status_code == 200
    assert response.status_code == 204
    request_task = request_data['tasks'][0]
    template = Template.objects.get(id=template_id)
    assert template.name == request_data['name']
    assert template.description == request_data['description']
    assert template.template_owners.count() == 1
    assert template.template_owners.first().id == user.id
    assert template.is_active is True

    assert template.kickoff_instance.description == (
        request_data['kickoff']['description']
    )

    assert template.tasks.count() == 1
    task = template.tasks.first()
    assert task.id
    assert task.number == request_task['number']
    assert task.name == request_task['name']
    assert task.description == request_task['description']
    assert task.raw_performers.count() == 1
    raw_performer = task.raw_performers.first()
    assert raw_performer.type == PerformerType.USER
    assert raw_performer.user.id == user.id


def test_discard_changes__draft_template__discard_changes(api_client):

    # arrange
    user = create_test_user()
    request_data = {
        'name': 'Template',
        'description': 'Desc',
        'template_owners': [user.id],
        'is_active': True,
        'kickoff': {
            'description': 'Desc',
        },
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'description': 'Task desc',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id
                    }
                ]
            }
        ]
    }
    api_client.token_authenticate(user)

    response_create = api_client.post(
        path='/templates',
        data=request_data
    )
    template_id = response_create.data['id']
    template_data = response_create.data
    template_data['name'] = 'Updated name'
    template_data['is_active'] = False
    template_data['kickoff']['description'] = 'Updated description'
    template_data['tasks'][0]['name'] = 'Updated task name'
    template_data['tasks'][0]['raw_performers'][0]['type'] = (
        PerformerType.WORKFLOW_STARTER
    )
    template_data['tasks'][0]['fields'] = [
        {
            'type': FieldType.RADIO,
            'name': 'Radio field',
            'description': 'desc',
            'order': 1,
            'is_required': True,
            'api_name': 'text-field-1',
            'default': 'default value',
            'selections': [
                {'value': 'First selection'}
            ]
        }
    ]

    template_data['tasks'].append(
        {
            'number': 2,
            'name': 'Second step',
            'description': 'Task desc 2',
            'raw_performers': [
                {
                    'type': PerformerType.USER,
                    'source_id': user.id
                }
            ]
        }
    )
    template_data['kickoff']['fields'] = [
        {
            'type': FieldType.USER,
            'name': 'Field performer',
            'description': 'desc',
            'order': 1,
            'is_required': True,
            'api_name': 'user-field-1',
            'default': 'default value'
        }
    ]

    response_update = api_client.put(
        path=f'/templates/{template_id}',
        data=template_data
    )

    # act
    response = api_client.post(f'/templates/{template_id}/discard-changes')

    # assert
    assert response_create.status_code == 200
    assert response_update.status_code == 200
    assert response.status_code == 204
    request_task = request_data['tasks'][0]
    template = Template.objects.get(id=template_id)
    assert template.name == request_data['name']
    assert template.description == request_data['description']
    assert template.template_owners.count() == 1
    assert template.template_owners.first().id == user.id
    assert template.is_active is True

    assert template.kickoff_instance.description == (
        request_data['kickoff']['description']
    )

    assert template.tasks.count() == 1
    task = template.tasks.first()
    assert task.id
    assert task.number == request_task['number']
    assert task.name == request_task['name']
    assert task.description == request_task['description']
    assert task.raw_performers.count() == 1
    raw_performer = task.raw_performers.first()
    assert raw_performer.type == PerformerType.USER
    assert raw_performer.user.id == user.id


def test_retrieve__not_template_owner__permission_denied(api_client):

    # arrange
    user = create_test_user()
    template = create_test_template(user=user, tasks_count=1)
    user2 = create_test_user(
        email='user2@pneumaticapp',
        account=user.account,
        is_admin=True,
        is_account_owner=False
    )
    api_client.token_authenticate(user2)

    # act
    response = api_client.post(f'/templates/{template.id}/discard-changes')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_PT_0023


def test_discard_changes__draft_unused_template__delete_template(api_client):

    # arrange
    user = create_test_user()
    request_data = {
        'name': 'Template',
        'description': 'Desc',
        'template_owners': [user.id],
        'is_active': False,
        'kickoff': {
            'description': 'Desc',
        },
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'description': 'Task desc',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id
                    }
                ]
            }
        ]
    }
    api_client.token_authenticate(user)
    response_create = api_client.post(
        path='/templates',
        data=request_data
    )
    template_id = response_create.data['id']

    # act
    response = api_client.post(f'/templates/{template_id}/discard-changes')

    # assert
    assert response_create.status_code == 200
    assert response.status_code == 204
    assert not Template.objects.filter(id=template_id).exists()
