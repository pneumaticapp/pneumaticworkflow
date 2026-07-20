import pytest

from src.processes.enums import (
    PerformerType,
)
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_counters__ok(api_client):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_admin(account=account)
    create_test_workflow(user, tasks_count=1)
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/user/counters')

    # assert
    assert response.status_code == 200
    assert response.data['tasks_count'] == 2


def test_counters__user_and_group_performer__ok(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    group = create_test_group(account, users=[user])
    workflow = create_test_workflow(owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
    )
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/user/counters')

    # assert
    assert response.status_code == 200
    assert response.data['tasks_count'] == 2


def test_counters__group_performer__ok(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    group = create_test_group(account, users=[user])
    workflow = create_test_workflow(owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/user/counters')

    # assert
    assert response.status_code == 200
    assert response.data['tasks_count'] == 1


def test_counters__group_performer_completed_for_user__ok(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(owner, tasks_count=1)
    group = create_test_group(account, users=[user])
    task = workflow.tasks.get(number=1)
    task.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
        completed_users=[user.id],
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/user/counters')

    # assert
    assert response.status_code == 200
    assert response.data['tasks_count'] == 0


def test_counters__different_user__ok(api_client):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_admin(account=account)
    other_user = create_test_admin(
        account=account,
        email='other@pneumatic.app',
    )
    create_test_workflow(user, tasks_count=1)
    create_test_workflow(user, tasks_count=1)
    create_test_workflow(user, tasks_count=1)
    create_test_workflow(other_user, tasks_count=1)
    create_test_workflow(other_user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/user/counters')

    # assert
    assert response.status_code == 200
    assert response.data['tasks_count'] == 3


def test_counters__complete_by_all__ok(api_client):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_admin(account=account)
    other_user = create_test_admin(
        account=account,
        email='other@pneumatic.app',
    )
    workflow = create_test_workflow(user, tasks_count=1)
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
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(
        user=owner,
        tasks_count=2,
    )
    task = workflow.tasks.get(number=1)
    mocker.patch(
        'src.processes.services.tasks.performers.'
        'send_new_task_notification.delay',
    )
    api_client.token_authenticate(owner)
    response_create = api_client.post(
        f'/v2/tasks/{task.id}/create-performer',
        data={'user_id': user.id},
    )
    response_delete = api_client.post(
        f'/v2/tasks/{task.id}/delete-performer',
        data={'user_id': owner.id},
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/user/counters')

    # assert
    assert response_create.status_code == 204
    assert response_delete.status_code == 204
    assert response.status_code == 200
    assert response.data['tasks_count'] == 1
