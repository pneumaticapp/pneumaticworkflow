import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
    create_test_template,
    create_test_workflow,
)
from pneumatic_backend.processes.models import (
    Template,
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    FieldType
)
from pneumatic_backend.processes.models.templates.owner import (
    TemplateOwner
)
from pneumatic_backend.processes.enums import OwnerType


pytestmark = pytest.mark.django_db


def test_fields__active__ok(api_client):

    # arrange
    user = create_test_user()
    user2 = create_test_user(
        email='user2@pneumaticapp',
        account=user.account
    )
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Template',
        'description': 'Desc',
        'template_owners': [user.id, user2.id],
        'is_active': True,
        'finalizable': True,
        'kickoff': {
            'description': 'Desc',
            'fields': [
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
        },
        'tasks': [
            {
                'number': 1,
                'api_name': 'task-1',
                'name': 'First step',
                'delay': None,
                'description': 'Task desc',
                'require_completion_by_all': True,
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id
                    },
                    {
                        'type': PerformerType.USER,
                        'source_id': user2.id
                    },
                    {
                        'type': PerformerType.WORKFLOW_STARTER,
                        'source_id': None
                    },
                    {
                        'type': PerformerType.FIELD,
                        'source_id': 'user-field-1'
                    },
                ],
                'fields': [
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
            }
        ]
    }
    response = api_client.post(
        path='/templates',
        data=request_data
    )
    template = Template.objects.get(id=response.data['id'])

    # act
    response = api_client.get(f'/templates/{template.id}/fields')

    # assert
    assert response.status_code == 200
    response_data = response.json()

    assert response_data.get('id')

    request_kickoff = request_data['kickoff']
    response_kickoff = response_data['kickoff']
    assert len(response_kickoff['fields']) == len(
        request_kickoff['fields'])
    request_kickoff_field = request_kickoff['fields'][0]
    response_kickoff_field = response_kickoff['fields'][0]
    assert response_kickoff_field.get('api_name')
    assert response_kickoff_field['type'] == (
        request_kickoff_field['type']
    )
    assert response_kickoff_field['name'] == (
        request_kickoff_field['name']
    )
    assert response_kickoff_field['name'] == (
        request_kickoff_field['name']
    )
    assert response_kickoff_field['api_name'] == (
        request_kickoff_field['api_name']
    )
    assert len(response_data['tasks']) == len(
        request_data['tasks'])
    request_task = request_data['tasks'][0]
    response_task = response_data['tasks'][0]
    assert response_task.get('id')
    assert len(response_task['fields']) == len(request_task['fields'])
    response_task_field = response_task['fields'][0]
    request_task_field = request_task['fields'][0]
    assert response_task_field['type'] == request_task_field['type']
    assert response_task_field['name'] == request_task_field['name']
    assert response_task_field['api_name'] == (
        request_task_field['api_name']
    )


def test_fields__draft__return_from_db(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Template',
        'description': 'Desc',
        'template_owners': [user.id],
        'is_active': False,
        'finalizable': True,
        'kickoff': {
            'description': 'Desc',
            'fields': [
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
        },
        'tasks': [
            {
                'number': 1,
                'api_name': 'task-1',
                'name': 'First step',
                'delay': None,
                'description': 'Task desc',
                'require_completion_by_all': True,
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id
                    },
                    {
                        'type': PerformerType.WORKFLOW_STARTER,
                        'source_id': None
                    },
                    {
                        'type': PerformerType.FIELD,
                        'source_id': 'user-field-1'
                    },
                ],
                'fields': [
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
            }
        ]
    }
    response = api_client.post(
        path='/templates',
        data=request_data
    )
    template = Template.objects.get(id=response.data['id'])

    # act
    response = api_client.get(f'/templates/{template.id}/fields')

    # assert
    assert response.status_code == 200
    assert response.data['kickoff'] == {
        'fields': []
    }
    assert response.data['tasks'] == []


def test_fields__workflow_member__ok(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_user(is_account_owner=True, account=account)
    template = create_test_template(user=owner, tasks_count=1)
    workflow = create_test_workflow(user=owner, template=template)
    user = create_test_user(
        email='user2@pneumaticapp',
        account=account
    )
    workflow.members.add(user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/templates/{template.id}/fields')

    # assert
    assert response.status_code == 200


def test_fields__template_owner__ok(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_user(is_account_owner=True, account=account)
    template = create_test_template(user=owner, tasks_count=1)
    user = create_test_user(
        email='user2@pneumaticapp',
        account=account
    )
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.USER,
        user_id=user.id,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/templates/{template.id}/fields')

    # assert
    assert response.status_code == 200


def test_fields__not_workflow_member_not_owner__permission_denied(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_user(is_account_owner=True, account=account)
    template = create_test_template(user=owner, tasks_count=1)
    create_test_workflow(user=owner, template=template)
    user = create_test_user(
        email='user2@pneumaticapp',
        account=account,
        is_account_owner=False
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/templates/{template.id}/fields')

    # assert
    assert response.status_code == 403
