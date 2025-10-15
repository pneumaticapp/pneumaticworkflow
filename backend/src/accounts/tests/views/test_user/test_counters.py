import pytest

from src.processes.enums import (
    DirectlyStatus,
    PerformerType,
)
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_account,
    create_test_group,
    create_test_user,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_counters__ok(api_client):

    # arrange
    user = create_test_user()
    create_test_workflow(user)
    create_test_workflow(user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/user/counters')

    # assert
    assert response.status_code == 200
    assert response.data['tasks_count'] == 2


def test_counters__with_group__ok(api_client):

    # arrange
    user = create_test_user()
    group = create_test_group(user.account, users=[user])
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
        directly_status=DirectlyStatus.CREATED,
    )
    create_test_workflow(user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/user/counters')

    # assert
    assert response.status_code == 200
    assert response.data['tasks_count'] == 2


def test_counters__different_user__ok(api_client):

    # arrange
    user = create_test_user()
    other_user = create_invited_user(user)
    create_test_workflow(user)
    create_test_workflow(user)
    create_test_workflow(user)
    create_test_workflow(other_user)
    create_test_workflow(other_user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/user/counters')

    # assert
    assert response.status_code == 200
    assert response.data['tasks_count'] == 3


def test_counters__complete_by_all__ok(api_client):

    # arrange
    user = create_test_user()
    other_user = create_invited_user(user)
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    task.require_completion_by_all = True
    raw_performer = task.add_raw_performer(other_user)
    task.update_performers(raw_performer)
    TaskPerformer.objects.by_task(task.id).by_user(user.id).update(
        is_completed=True,
    )
    task.save()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/user/counters')

    # assert
    assert response.status_code == 200
    assert response.data['tasks_count'] == 0


def test_counters__task_performer_changed__ok(mocker, api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
        email='owner@test.test',
    )
    user_performer = create_test_user(
        is_account_owner=False,
        account=account,
        email='performer@test.test',
    )
    workflow = create_test_workflow(
        user=account_owner,
        tasks_count=2,
    )
    task = workflow.tasks.get(number=1)
    mocker.patch(
        'src.processes.services.tasks.performers.'
        'send_new_task_notification.delay',
    )
    api_client.token_authenticate(account_owner)
    response_create = api_client.post(
        f'/v2/tasks/{task.id}/create-performer',
        data={'user_id': user_performer.id},
    )
    response_delete = api_client.post(
        f'/v2/tasks/{task.id}/delete-performer',
        data={'user_id': account_owner.id},
    )

    api_client.token_authenticate(user_performer)

    # act
    response = api_client.get('/accounts/user/counters')

    # assert
    assert response_create.status_code == 204
    assert response_delete.status_code == 204
    assert response.status_code == 200
    assert response.data['tasks_count'] == 1
