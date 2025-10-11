import pytest
from src.accounts.models import (
    UserInvite,
)
from src.processes.models import (
    Template,
    TemplateOwner,
)
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_workflow,
    create_test_template,
    create_test_user,
)
from src.processes.enums import (
    PerformerType,
    OwnerType,
)


pytestmark = pytest.mark.django_db


def test_count_templates__user_from_another_acc__404(api_client):
    # arrange
    user = create_test_user()
    another_user = create_test_user(email='another@pneumatic.app')
    invited_user = create_invited_user(another_user)

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/users/{invited_user.id}/count-workflows',
    )

    # assert
    assert response.status_code == 404


def test_count_templates__invited_user_from_another_account__ok(api_client):
    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    invited_user = create_test_user(email='another@pneumatic.app')
    UserInvite.objects.create(
        email=invited_user.email,
        account=user.account,
        invited_by=user,
        invited_user=invited_user,
    )

    # act
    response = api_client.get(
        f'/accounts/users/{invited_user.id}/count-workflows',
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 0


def test_count_templates(api_client):
    # arrange
    user = create_test_user()
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
        f'/accounts/users/{invited_user.id}/count-workflows',
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 3


def test_count_templates__only_template_owners__ok(api_client):
    # arrange
    user = create_test_user()
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
        f'/accounts/users/{invited_user.id}/count-workflows',
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 1


def test_count_templates__template_owners_is_deleted__ok(api_client):
    # arrange
    user = create_test_user()
    create_test_template(
        user=user,
        is_active=True,
    )
    TemplateOwner.objects.filter(user_id=user.id).delete()
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/users/{user.id}/count-workflows',
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 0


def test_count_templates__only_template_performer__ok(api_client):

    # arrange
    user = create_test_user()
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
        f'/accounts/users/{invited_user.id}/count-workflows',
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 1


def test_count_templates__raw_performer__ok(api_client):
    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    request_template_owners = [
        {
            'type': OwnerType.USER,
            'source_id': f'{user.id}',
        },
    ]
    # act
    response_create = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'owners': request_template_owners,
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
                            'source_id': user.id,
                        },
                    ],
                },
            ],
        },
    )
    # act
    response = api_client.get(
        f'/accounts/users/{user.id}/count-workflows',
    )

    # assert
    assert response_create.status_code == 200
    template = Template.objects.get(id=response_create.data['id'])
    assert template.raw_performers.all().count() == 1
    assert template.raw_performers.get(user_id=user.id)
    assert response.status_code == 200
    assert response.data['count'] == 1


def test_count_templates__only_task_performer__ok(api_client):
    # arrange
    user = create_test_user()
    invited_user = create_invited_user(user)
    workflow = create_test_workflow(invited_user)
    api_client.token_authenticate(user)
    api_client.delete(f'/templates/{workflow.template.id}')

    # act
    response = api_client.get(
        f'/accounts/users/{invited_user.id}/count-workflows',
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 1
