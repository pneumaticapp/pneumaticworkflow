import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
)


pytestmark = pytest.mark.django_db


def test_list__status_completed__return_recent_completed(
    mocker,
    api_client
):
    # arrange
    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay'
    )
    user = create_test_user()
    workflow = create_test_workflow(user)
    api_client.token_authenticate(user)

    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id},
    )
    task = workflow.tasks.get(number=2)
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': task.id},
    )

    # act
    response = api_client.get('/recent-task?status=completed')

    # assert
    assert response.data['id'] == task.id


def test_list__status_running__return_recent_running(
    mocker,
    api_client
):
    # arrange
    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay'
    )
    user = create_test_user()
    workflow = create_test_workflow(user)
    create_test_workflow(user)

    api_client.token_authenticate(user)

    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id},
    )

    # act
    response = api_client.get('/recent-task?status=running')

    # assert
    task = workflow.tasks.get(number=2)
    assert response.data['id'] == task.id


def test_list__default__return_recent_running(
    mocker,
    api_client
):
    # arrange
    mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay'
    )
    user = create_test_user()
    workflow = create_test_workflow(user)
    create_test_workflow(user)

    api_client.token_authenticate(user)

    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id},
    )

    # act
    response = api_client.get('/recent-task')

    # assert
    task = workflow.tasks.get(number=2)
    assert response.data['id'] == task.id
