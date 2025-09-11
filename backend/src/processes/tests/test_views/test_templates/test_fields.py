import pytest

from src.authentication.services import GuestJWTAuthService
from src.authentication.tokens import PublicToken
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_template,
    create_test_workflow,
    create_test_owner,
    create_test_admin,
    create_test_not_admin, create_test_guest,
)
from src.processes.models import (
    Template,
    TemplateOwner,
    FieldTemplate, TaskPerformer,
)
from src.processes.enums import (
    PerformerType,
    FieldType,
)
from src.processes.enums import OwnerType


pytestmark = pytest.mark.django_db


def test_fields__active_template__ok(api_client):

    # arrange
    user = create_test_owner()
    template = create_test_template(user, tasks_count=1, is_active=True)
    api_client.token_authenticate(user)
    kickoff = template.kickoff_instance
    kickoff_field = FieldTemplate.objects.create(
        name='First task performer',
        description='Some description',
        type=FieldType.USER,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='field-1'
    )
    task = template.tasks.first()
    task_field = FieldTemplate.objects.create(
        name='First task performer 2',
        description='Some description 2',
        type=FieldType.NUMBER,
        task=task,
        template=template,
        order=2,
        api_name='field-2'
    )

    # act
    response = api_client.get(f'/templates/{template.id}/fields')

    # assert
    assert response.status_code == 200
    data = response.data
    assert data['id'] == template.id
    assert len(data['kickoff']['fields']) == 1

    field_1_data = data['kickoff']['fields'][0]
    assert field_1_data['name'] == kickoff_field.name
    assert field_1_data['type'] == kickoff_field.type
    assert field_1_data['order'] == kickoff_field.order
    assert field_1_data['description'] == kickoff_field.description
    assert field_1_data['api_name'] == kickoff_field.api_name

    assert len(data['tasks']) == 1
    task_data = data['tasks'][0]
    assert task_data['id'] == task.id
    assert task_data['name'] == task.name
    assert task_data['number'] == task.number
    assert task_data['api_name'] == task.api_name
    assert len(task_data['fields']) == 1

    field_2_data = task_data['fields'][0]
    assert field_2_data['name'] == task_field.name
    assert field_2_data['type'] == task_field.type
    assert field_2_data['order'] == task_field.order
    assert field_2_data['description'] == task_field.description
    assert field_2_data['api_name'] == task_field.api_name


def test_fields__draft_template__return_from_db(api_client):

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Template',
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id
            }
        ],
        'is_active': False,
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
                'description': 'Task desc',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id
                    }
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
    assert response.data['kickoff'] == {'fields': []}
    assert response.data['tasks'] == []


def test_fields__workflow_member__ok(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(user=owner, tasks_count=1)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(user=owner, template=template)
    workflow.members.add(user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/templates/{template.id}/fields')

    # assert
    assert response.status_code == 200


def test_fields__template_owner__ok(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(user=owner, tasks_count=1)
    user = create_test_not_admin(account=account)
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


def test_fields__not_workflow_member_not_owner__not_found(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(user=owner, tasks_count=1)
    create_test_workflow(user=owner, template=template)
    user = create_test_owner(
        email='user2@pneumaticapp',
        account=account,
        is_account_owner=False
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/templates/{template.id}/fields')

    # assert
    assert response.status_code == 404


def test_fields__workflow_member_and_template_owner__ok(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(user=owner, tasks_count=1)
    workflow = create_test_workflow(user=owner, template=template)
    request_user = create_test_not_admin(account=account)
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.USER,
        user_id=request_user.id,
    )
    workflow.members.add(request_user)
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(f'/templates/{template.id}/fields')

    # assert
    assert response.status_code == 200


def test_fields__not_authenticated__permission_denied(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(user=owner, tasks_count=1)
    workflow = create_test_workflow(user=owner, template=template)
    request_user = create_test_not_admin(account=account)
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.USER,
        user_id=request_user.id,
    )
    workflow.members.add(request_user)

    # act
    response = api_client.get(f'/templates/{template.id}/fields')

    # assert
    assert response.status_code == 401


def test_fields__guest_performer__permission_denied(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        owner,
        is_active=True,
        tasks_count=1
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    guest = create_test_guest(account=account)
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    # Extra case
    create_test_admin(email=guest.email, account=account)
    workflow.members.add(guest)
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id
    )

    # act
    response = api_client.get(
        f'/templates/{template.id}/fields',
        **{'X-Guest-Authorization': str_token}
    )

    # assert
    assert response.status_code == 403


def test_fields__public_auth__permission_denied(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        owner,
        is_active=True,
        is_public=True,
        tasks_count=1
    )
    auth_header_value = f'Token {template.public_id}'
    token = PublicToken(template.public_id)
    mocker.patch(
        'src.authentication.services.public_auth.'
        'PublicAuthService.get_token',
        return_value=token
    )
    mocker.patch(
        'src.authentication.services.public_auth.'
        'PublicAuthService.get_template',
        return_value=template
    )

    # act
    response = api_client.get(
        f'/templates/{template.id}/fields',
        **{'X-Public-Authorization': auth_header_value}
    )

    # assert
    assert response.status_code == 403


def test_fields__ordering__ok(api_client):

    # arrange
    user = create_test_owner()
    template = create_test_template(user, tasks_count=2, is_active=True)
    api_client.token_authenticate(user)
    kickoff = template.kickoff_instance
    kickoff_field_2 = FieldTemplate.objects.create(
        name='Field',
        type=FieldType.USER,
        kickoff=kickoff,
        template=template,
        order=2,
    )
    kickoff_field_1 = FieldTemplate.objects.create(
        name='Field',
        type=FieldType.USER,
        kickoff=kickoff,
        template=template,
        order=1,
    )
    task_1 = template.tasks.get(number=1)
    task_1_field_1 = FieldTemplate.objects.create(
        name='Field',
        type=FieldType.NUMBER,
        task=task_1,
        template=template,
        order=1,
    )
    task_1_field_2 = FieldTemplate.objects.create(
        name='Field',
        type=FieldType.NUMBER,
        task=task_1,
        template=template,
        order=2,
    )
    task_2 = template.tasks.get(number=2)
    task_2_field_1 = FieldTemplate.objects.create(
        name='Field',
        type=FieldType.NUMBER,
        task=task_2,
        template=template,
        order=1,
    )
    task_2_field_2 = FieldTemplate.objects.create(
        name='Field',
        type=FieldType.NUMBER,
        task=task_2,
        template=template,
        order=2,
    )
    # act
    response = api_client.get(f'/templates/{template.id}/fields')

    # assert
    assert response.status_code == 200
    data = response.data
    assert data['kickoff']['fields'][0]['api_name'] == kickoff_field_2.api_name
    assert data['kickoff']['fields'][0]['order'] == 2
    assert data['kickoff']['fields'][1]['api_name'] == kickoff_field_1.api_name
    assert data['kickoff']['fields'][1]['order'] == 1

    assert data['tasks'][0]['fields'][0]['api_name'] == task_1_field_2.api_name
    assert data['tasks'][0]['fields'][0]['order'] == 2
    assert data['tasks'][0]['fields'][1]['api_name'] == task_1_field_1.api_name
    assert data['tasks'][0]['fields'][1]['order'] == 1

    assert data['tasks'][1]['fields'][0]['api_name'] == task_2_field_2.api_name
    assert data['tasks'][1]['fields'][0]['order'] == 2
    assert data['tasks'][1]['fields'][1]['api_name'] == task_2_field_1.api_name
    assert data['tasks'][1]['fields'][1]['order'] == 1
