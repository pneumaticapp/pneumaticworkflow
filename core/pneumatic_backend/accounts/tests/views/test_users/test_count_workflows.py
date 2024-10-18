import pytest
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
)
from pneumatic_backend.accounts.models import (
    UserInvite,
)
from pneumatic_backend.accounts.tests.fixtures import (
    create_invited_user,
    create_test_owner,
    create_test_account
)
from pneumatic_backend.processes.models import (
    Template
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_workflow,
    create_test_template,
)
from pneumatic_backend.processes.enums import PerformerType


pytestmark = pytest.mark.django_db


def test_count_templates__user_from_another_acc__404(api_client):
    # arrange
    user = create_test_owner()
    another_user = create_test_owner(email='another@pneumatic.app')
    invited_user = create_invited_user(another_user)

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/users/{invited_user.id}/count-workflows'
    )

    # assert
    assert response.status_code == 404


def test_count_templates__invited_user_from_another_account__ok(api_client):
    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    invited_user = create_test_owner(email='another@pneumatic.app')
    UserInvite.objects.create(
        email=invited_user.email,
        account=user.account,
        invited_by=user,
        invited_user=invited_user,
    )

    # act
    response = api_client.get(
        f'/accounts/users/{invited_user.id}/count-workflows'
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 0


def test_count_templates(api_client):
    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_owner(account=account)
    invited_user = create_invited_user(user)
    create_test_template(
        user=invited_user,
        is_active=True,
    )
    create_test_workflow(invited_user)
    create_test_workflow(user)
    deleted_template = create_test_template(
        user=invited_user,
        is_active=True,
    )
    api_client.token_authenticate(user)
    api_client.delete(f'/templates/{deleted_template.id}')

    # act
    response = api_client.get(
        f'/accounts/users/{invited_user.id}/count-workflows'
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 3


def test_count_templates__only_template_owners__ok(api_client):
    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_owner(account=account)
    invited_user = create_invited_user(user)
    create_test_template(
        user=invited_user,
        is_active=True,
    )
    create_test_template(
        user=user,
        is_active=True,
    )
    deleted_template = create_test_template(
        user=invited_user,
        is_active=True,
    )
    api_client.token_authenticate(user)
    api_client.delete(f'/templates/{deleted_template.id}')

    # act
    response = api_client.get(
        f'/accounts/users/{invited_user.id}/count-workflows'
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 1


def test_count_templates__only_template_performer__ok(api_client):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_owner(account=account)
    invited_user = create_invited_user(user)
    create_test_template(
        user=invited_user,
        is_active=True,
    )
    create_test_template(
        user=user,
        is_active=True,
    )
    deleted_template = create_test_template(
        user=invited_user,
        is_active=True,
    )
    api_client.token_authenticate(user)
    api_client.delete(f'/templates/{deleted_template.id}')

    # act
    response = api_client.get(
        f'/accounts/users/{invited_user.id}/count-workflows'
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 1


def test_count_templates__raw_performer__ok(api_client):
    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)

    # act
    response_create = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
            'description': '',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'First task',
                    'number': 1,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        },
                    ]
                }
            ]
        }
    )
    # act
    response = api_client.get(
        f'/accounts/users/{user.id}/count-workflows'
    )

    # assert
    assert response_create.status_code == 200
    template = Template.objects.get(id=response_create.data['id'])
    assert template.raw_performers.all().count() == 1
    assert template.raw_performers.first().user_id == user.id
    assert response.status_code == 200
    assert response.data['count'] == 1


def test_count_templates__only_task_performer__ok(api_client):
    # arrange
    user = create_test_owner()
    invited_user = create_invited_user(user)
    workflow = create_test_workflow(invited_user)
    api_client.token_authenticate(user)
    api_client.delete(f'/templates/{workflow.template.id}')

    # act
    response = api_client.get(
        f'/accounts/users/{invited_user.id}/count-workflows'
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 1
