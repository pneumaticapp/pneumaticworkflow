import pytest
from datetime import timedelta

from django.utils import timezone

from src.accounts.enums import BillingPlanType
from src.accounts.messages import MSG_A_0035, MSG_A_0037, MSG_A_0041
from src.processes.enums import (
    FieldType,
    OwnerType,
    OwnerRole,
    PerformerType,
)
from src.processes.messages.template import (
    MSG_PT_0023,
)
from src.processes.models.templates.template import Template
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
    create_test_user,
)

pytestmark = pytest.mark.django_db


def test_discard_changes__active_template__not_change(api_client):

    # arrange
    user = create_test_user()
    request_data = {
        'name': 'Template',
        'description': 'Desc',
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
                'role': OwnerRole.OWNER,
            },
        ],
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
                        'source_id': user.id,
                    },
                ],
            },
        ],
    }
    api_client.token_authenticate(user)

    response_create = api_client.post(
        path='/templates',
        data=request_data,
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
    assert template.owners.count() == 1
    assert template.owners.first().user_id == user.id
    assert template.is_active is True
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
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
                'role': OwnerRole.OWNER,
            },
        ],
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
                        'source_id': user.id,
                    },
                ],
            },
        ],
    }
    api_client.token_authenticate(user)

    response_create = api_client.post(
        path='/templates',
        data=request_data,
    )
    template_id = response_create.data['id']
    template_data = response_create.data
    template_data['name'] = 'Updated name'
    template_data['is_active'] = False
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
                {'value': 'First selection'},
            ],
        },
    ]

    template_data['tasks'].append(
        {
            'number': 2,
            'name': 'Second step',
            'description': 'Task desc 2',
            'raw_performers': [
                {
                    'type': PerformerType.USER,
                    'source_id': user.id,
                },
            ],
        },
    )
    template_data['kickoff']['fields'] = [
        {
            'type': FieldType.USER,
            'name': 'Field performer',
            'description': 'desc',
            'order': 1,
            'is_required': True,
            'api_name': 'user-field-1',
            'default': 'default value',
        },
    ]

    response_update = api_client.put(
        path=f'/templates/{template_id}',
        data=template_data,
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
    assert template.owners.count() == 1
    assert template.owners.first().user_id == user.id
    assert template.is_active is True

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
        is_account_owner=False,
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
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
                'role': OwnerRole.OWNER,
            },
        ],
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
                        'source_id': user.id,
                    },
                ],
            },
        ],
    }
    api_client.token_authenticate(user)
    response_create = api_client.post(
        path='/templates',
        data=request_data,
    )
    template_id = response_create.data['id']

    # act
    response = api_client.post(f'/templates/{template_id}/discard-changes')

    # assert
    assert response_create.status_code == 200
    assert response.status_code == 204
    assert not Template.objects.filter(id=template_id).exists()


def test_discard_changes__unauthenticated__unauthorized(api_client):

    """Unauthenticated user → 401"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )

    # act
    response = api_client.post(
        f'/templates/{template.id}/discard-changes',
    )

    # assert
    assert response.status_code == 401


def test_discard_changes__expired_subscription__permission_denied(api_client):

    """Expired subscription → 403"""

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        plan_expiration=timezone.now() - timedelta(days=1),
    )
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(
        f'/templates/{template.id}/discard-changes',
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0035


def test_discard_changes__billing_plan_limit__permission_denied(api_client):

    """Billing plan limit exceeded → 403"""

    # arrange
    account = create_test_account(plan=None)
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(
        f'/templates/{template.id}/discard-changes',
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0041


def test_discard_changes__users_overlimited__permission_denied(api_client):

    """Users over limit → 403"""

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        max_users=1,
    )
    user = create_test_owner(account=account)
    create_test_not_admin(
        account=account,
        email='extra@pneumatic.app',
    )
    account.active_users = 2
    account.save()
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(
        f'/templates/{template.id}/discard-changes',
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0037


def test_discard_changes__not_admin__permission_denied(api_client):

    """User is not admin or account owner → 403"""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    not_admin = create_test_not_admin(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    api_client.token_authenticate(user=not_admin)

    # act
    response = api_client.post(
        f'/templates/{template.id}/discard-changes',
    )

    # assert
    assert response.status_code == 403


def test_discard_changes__not_found__not_found(api_client):

    """Template not found → 404"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)
    nonexistent_id = 999999

    # act
    response = api_client.post(
        f'/templates/{nonexistent_id}/discard-changes',
    )

    # assert
    assert response.status_code == 404
