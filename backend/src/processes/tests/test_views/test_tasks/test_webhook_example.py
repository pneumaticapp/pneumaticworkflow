from collections import OrderedDict

import pytest

from src.processes.enums import TaskStatus, WorkflowStatus
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
    create_test_workflow,
)
from src.webhooks.enums import HookEvent

pytestmark = pytest.mark.django_db


def test_webhook_example__body__ok(api_client):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    template = workflow.template
    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v2/tasks/webhook-example')

    # assert
    assert response.status_code == 200
    hook_data = response.data['hook']
    assert hook_data['id'] == 123
    assert hook_data['event'] == HookEvent.TASK_RETURNED
    assert hook_data['target'] == 'https://example.com/webhooks/'
    assert response.data['task'] == {
        'id': task.id,
        'name': 'Task №1',
        'api_name': task.api_name,
        'description': None,
        'contains_comments': False,
        'require_completion_by_all': False,
        'output': [],
        'delay': None,
        'date_started_tsp': task.date_started.timestamp(),
        'date_completed_tsp': None,
        'due_date_tsp': None,
        'is_completed': False,
        'performers': [
            OrderedDict([
                ('is_completed', False),
                ('date_completed_tsp', None),
                ('type', 'user'),
                ('source_id', user.id),
            ]),
        ],
        'is_urgent': False,
        'checklists_marked': 0,
        'checklists_total': 0,
        'checklists': [],
        'sub_workflows': [],
        'status': TaskStatus.ACTIVE,
        'revert_tasks': [],
        'workflow': {
            'id': workflow.id,
            'name': 'Test workflow',
            'due_date_tsp': None,
            'status': WorkflowStatus.RUNNING,
            'description': None,
            'finalizable': False,
            'is_external': False,
            'is_urgent': False,
            'date_created_tsp': workflow.date_created.timestamp(),
            'date_completed_tsp': None,
            'workflow_starter': user.id,
            'ancestor_task_id': None,
            'is_legacy_template': False,
            'legacy_template_name': None,
            'owners': [user.id],
            'template': OrderedDict([
                ('id', template.id),
                ('name', 'Test workflow'),
                ('is_active', True),
                ('wf_name_template', None),
            ]),
            'kickoff': {
                'id': workflow.kickoff_instance.id,
                'output': [],
            },
            'tasks': [
                OrderedDict([
                    ('id', task.id),
                    ('name', 'Task №1'),
                    ('api_name', task.api_name),
                    ('description', None),
                    ('number', 1),
                    ('delay', None),
                    ('due_date_tsp', None),
                    ('date_started_tsp', task.date_started.timestamp()),
                    ('date_completed_tsp', None),
                    ('performers', [
                        OrderedDict([
                            ('is_completed', False),
                            ('date_completed_tsp', None),
                            ('type', 'user'),
                            ('source_id', user.id),
                        ]),
                    ]),
                    ('checklists_total', 0),
                    ('checklists_marked', 0),
                    ('status', 'active'),
                ]),
            ],
        },
    }


def test_webhook_example__filter_status_completed__ok(api_client):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.COMPLETED
    task.save()
    create_test_workflow(user=user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/v2/tasks/webhook-example?status={TaskStatus.COMPLETED}',
    )

    # assert
    assert response.status_code == 200
    hook_data = response.data['hook']
    assert hook_data['id'] == 123
    assert hook_data['event'] == HookEvent.TASK_COMPLETED
    assert hook_data['target'] == 'https://example.com/webhooks/'
    assert response.data['task']['id'] == task.id
    assert response.data['task']['status'] == TaskStatus.COMPLETED


def test_webhook_example__filter_status_active__ok(api_client):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)

    completed_workflow = create_test_workflow(user=user, tasks_count=1)
    completed_task = completed_workflow.tasks.get(number=1)
    completed_task.status = TaskStatus.COMPLETED
    completed_task.save()
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/v2/tasks/webhook-example?status={TaskStatus.ACTIVE}',
    )

    # assert
    assert response.status_code == 200
    hook_data = response.data['hook']
    assert hook_data['id'] == 123
    assert hook_data['event'] == HookEvent.TASK_RETURNED
    assert hook_data['target'] == 'https://example.com/webhooks/'
    assert response.data['task']['id'] == task.id
    assert response.data['task']['status'] == TaskStatus.ACTIVE


def test_webhook_example__filter_ordering_date_created__ok(api_client):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)

    create_test_workflow(user=user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/v2/tasks/webhook-example?ordering=date_started',
    )

    # assert
    assert response.status_code == 200
    hook_data = response.data['hook']
    assert hook_data['id'] == 123
    assert hook_data['event'] == HookEvent.TASK_RETURNED
    assert hook_data['target'] == 'https://example.com/webhooks/'
    assert response.data['task']['id'] == task.id
    assert response.data['task']['status'] == TaskStatus.ACTIVE


def test_webhook_example__filter_ordering_date_created_reverse__ok(api_client):

    # arrange
    user = create_test_owner()
    create_test_workflow(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/v2/tasks/webhook-example?ordering=-date_started',
    )

    # assert
    assert response.status_code == 200
    hook_data = response.data['hook']
    assert hook_data['id'] == 123
    assert hook_data['event'] == HookEvent.TASK_RETURNED
    assert hook_data['target'] == 'https://example.com/webhooks/'
    assert response.data['task']['id'] == task.id
    assert response.data['task']['status'] == TaskStatus.ACTIVE


def test_webhook_example__not_owner__not_found(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    user = create_test_admin(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v2/tasks/webhook-example')

    # assert
    assert response.status_code == 404
