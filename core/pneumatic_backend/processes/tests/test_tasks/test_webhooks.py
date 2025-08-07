import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from typing_extensions import OrderedDict
from pneumatic_backend.processes.enums import TaskStatus, WorkflowStatus
from pneumatic_backend.processes.models import Workflow
from pneumatic_backend.processes.tests.fixtures import (
    create_test_workflow,
    create_test_owner,
    create_wf_created_webhook,
    create_task_completed_webhook,
    create_task_returned_webhook,
    create_test_template, create_wf_completed_webhook
)


UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_send_task_completed_webhook__ok(api_client, mocker):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(
        user=user,
        tasks_count=2
    )
    template = workflow.template
    create_task_completed_webhook(user)
    task_1 = workflow.tasks.get(number=1)
    api_client.token_authenticate(user)
    complete_task_webhook_mock = mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay'
    )

    # act
    response = api_client.post(
        f'/v2/tasks/{task_1.id}/complete',
    )

    # assert
    assert response.status_code == 200

    # act
    task_1.refresh_from_db()
    task_2 = workflow.tasks.get(number=2)
    task_performer = task_1.taskperformer_set.get(user=user)

    payload = {
        'task': {
            'id': task_1.id,
            'name': 'Task №1',
            'api_name': task_1.api_name,
            'description': None,
            'contains_comments': False,
            'require_completion_by_all': False,
            'output': [],
            'delay': None,
            'date_started_tsp': task_1.date_started.timestamp(),
            'date_completed_tsp': task_1.date_completed.timestamp(),
            'due_date_tsp': None,
            'is_completed': True,
            'performers': [
                OrderedDict([
                    ('is_completed', True),
                    (
                        'date_completed_tsp',
                        task_performer.date_completed.timestamp()
                    ),
                    ('type', 'user'),
                    ('source_id', user.id)
                ])
            ],
            'is_urgent': False,
            'checklists_marked': 0,
            'checklists_total': 0,
            'checklists': [],
            'sub_workflows': [],
            'status': 'completed',
            'workflow': {
                'id': workflow.id,
                'name': 'Test workflow',
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
                'template': {
                    'id': template.id,
                    'name': 'Test workflow',
                    'is_active': True,
                    'wf_name_template': None
                },
                'kickoff': {
                    'output': []
                },
                'current_task': {
                    'id': task_2.id,
                    'name': 'Task №2',
                    'api_name': task_2.api_name,
                    'description': None,
                    'number': 2,
                    'due_date_tsp': None,
                    'date_started_tsp': task_2.date_started.timestamp(),
                    'date_completed_tsp': None,
                    'performers': [
                        {
                            'id': user.id,
                            'first_name': 'John',
                            'last_name': 'Doe'
                        }
                    ]
                },
                'tasks': [
                    OrderedDict([
                        ('id', task_1.id),
                        ('name', 'Task №1'),
                        ('api_name', task_1.api_name),
                        ('description', None),
                        ('number', 1),
                        ('delay', None),
                        ('due_date_tsp', None),
                        ('date_started_tsp', task_1.date_started.timestamp()),
                        (
                            'date_completed_tsp',
                            task_1.date_completed.timestamp()
                        ),
                        ('performers', [
                            OrderedDict([
                                ('is_completed', True),
                                (
                                    'date_completed_tsp',
                                    task_performer.date_completed.timestamp()
                                ),
                                ('type', 'user'),
                                ('source_id', user.id)
                            ])
                        ]),
                        ('checklists_total', 0),
                        ('checklists_marked', 0),
                        ('status', 'completed'),
                    ]),
                    OrderedDict([
                        ('id', task_2.id),
                        ('name', 'Task №2'),
                        ('api_name', task_2.api_name),
                        ('description', None),
                        ('number', 2),
                        ('delay', None),
                        ('due_date_tsp', None),
                        ('date_started_tsp', task_2.date_started.timestamp()),
                        ('date_completed_tsp', None),
                        ('performers', [
                            OrderedDict([
                                ('is_completed', False),
                                ('date_completed_tsp', None),
                                ('type', 'user'),
                                ('source_id', user.id)
                            ])
                        ]),
                        ('checklists_total', 0),
                        ('checklists_marked', 0),
                        ('status', 'active'),
                    ])
                ]
            }
        }
    }
    complete_task_webhook_mock.assert_called_once_with(
        user_id=user.id,
        account_id=user.account_id,
        payload=payload
    )


def test_send_task_completed_webhook__sub_workflows__ok(api_client, mocker):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(
        user=user,
        tasks_count=2
    )
    template = workflow.template
    create_task_completed_webhook(user)
    task_1 = workflow.tasks.get(number=1)
    sub_workflow = create_test_workflow(
        user=user,
        tasks_count=1,
        ancestor_task=task_1,
        status=WorkflowStatus.DONE
    )
    sub_workflow.tasks.update(
        status=TaskStatus.COMPLETED,
        date_completed=timezone.now()
    )
    sub_task = sub_workflow.tasks.first()
    sub_task.taskperformer_set.update(
        is_completed=True,
        date_completed=timezone.now()
    )
    sub_task_performer = sub_task.taskperformer_set.get(user=user)
    api_client.token_authenticate(user)
    complete_task_webhook_mock = mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay'
    )

    # act
    response = api_client.post(
        f'/v2/tasks/{task_1.id}/complete',
    )

    # assert
    assert response.status_code == 200

    # act
    task_1.refresh_from_db()
    task_2 = workflow.tasks.get(number=2)
    task_performer = task_1.taskperformer_set.get(user=user)

    payload = {
        'task': {
            'id': task_1.id,
            'name': 'Task №1',
            'api_name': task_1.api_name,
            'description': None,
            'contains_comments': False,
            'require_completion_by_all': False,
            'output': [],
            'delay': None,
            'date_started_tsp': task_1.date_started.timestamp(),
            'date_completed_tsp': task_1.date_completed.timestamp(),
            'due_date_tsp': None,
            'is_completed': True,
            'performers': [
                OrderedDict([
                    ('is_completed', True),
                    (
                        'date_completed_tsp',
                        task_performer.date_completed.timestamp()
                    ),
                    ('type', 'user'),
                    ('source_id', user.id)
                ])
            ],
            'is_urgent': False,
            'checklists_marked': 0,
            'checklists_total': 0,
            'checklists': [],
            'status': 'completed',
            'sub_workflows': [
                OrderedDict([
                    ('id', sub_workflow.id),
                    ('name', 'Test workflow'),
                    ('status', WorkflowStatus.DONE),
                    ('description', None),
                    ('finalizable', False),
                    ('is_external', False),
                    ('is_urgent', False),
                    (
                        'date_created_tsp',
                        sub_workflow.date_created.timestamp()
                    ),
                    (
                        'date_completed_tsp',
                        sub_workflow.date_completed.timestamp()
                    ),
                    ('workflow_starter', user.id),
                    ('ancestor_task_id', task_1.id),
                    ('is_legacy_template', False),
                    ('legacy_template_name', None),
                    (
                        'template',
                        OrderedDict([
                            ('id', sub_workflow.template_id),
                            ('name', 'Test workflow'),
                            ('is_active', True),
                        ])
                    ),
                    ('owners', [user.id]),
                    ('tasks', [
                        OrderedDict([
                            ('id', sub_task.id),
                            ('name', 'Task №1'),
                            ('api_name', sub_task.api_name),
                            ('description', None),
                            ('number', 1),
                            ('delay', None),
                            ('due_date_tsp', None),
                            (
                                'date_started_tsp',
                                sub_task.date_started.timestamp()
                            ),
                            (
                                'date_completed_tsp',
                                sub_task.date_completed.timestamp()
                            ),
                            ('performers', [
                                OrderedDict([
                                    ('is_completed', True),
                                    (
                                        'date_completed_tsp',
                                        sub_task_performer.
                                        date_completed.timestamp()
                                    ),
                                    ('type', 'user'),
                                    ('source_id', user.id)
                                ])
                            ]),
                            ('checklists_total', 0),
                            ('checklists_marked', 0),
                            ('status', 'completed'),
                        ])
                    ]),
                    ('fields', []),
                    ('due_date_tsp', None),
                    ('tasks_count', 1),
                    ('current_task', 1),
                    ('active_tasks_count', 1),
                    ('active_current_task', 1),
                    (
                        'task', {
                            'id': sub_task.id,
                            'name': 'Task №1',
                            'api_name': sub_task.api_name,
                            'description': None,
                            'number': 1,
                            'delay': None,
                            'due_date_tsp': None,
                            'date_started_tsp': (
                                sub_task.date_started.timestamp()
                            ),
                            'date_completed_tsp': (
                                sub_task.date_completed.timestamp()
                            ),
                            'performers': [
                                {
                                    'is_completed': True,
                                    'date_completed_tsp': (
                                        sub_task_performer.
                                        date_completed.timestamp()
                                    ),
                                    'type': 'user',
                                    'source_id': user.id
                                }
                            ],
                            'checklists_total': 0,
                            'checklists_marked': 0,
                            'status': 'completed',
                        }
                    ),
                    ('passed_tasks', [
                        OrderedDict([
                            ('id', sub_task.id),
                            ('name', sub_task.name),
                            ('number', sub_task.number),
                        ])
                    ]),
                ])
            ],
            'workflow': {
                'id': workflow.id,
                'name': 'Test workflow',
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
                'template': {
                    'id': template.id,
                    'name': 'Test workflow',
                    'is_active': True,
                    'wf_name_template': None
                },
                'kickoff': {
                    'output': []
                },
                'current_task': {
                    'id': task_2.id,
                    'name': 'Task №2',
                    'api_name': task_2.api_name,
                    'description': None,
                    'number': 2,
                    'due_date_tsp': None,
                    'date_started_tsp': task_2.date_started.timestamp(),
                    'date_completed_tsp': None,
                    'performers': [
                        {
                            'id': user.id,
                            'first_name': 'John',
                            'last_name': 'Doe'
                        }
                    ]
                },
                'tasks': [
                    OrderedDict([
                        ('id', task_1.id),
                        ('name', 'Task №1'),
                        ('api_name', task_1.api_name),
                        ('description', None),
                        ('number', 1),
                        ('delay', None),
                        ('due_date_tsp', None),
                        ('date_started_tsp', task_1.date_started.timestamp()),
                        (
                            'date_completed_tsp',
                            task_1.date_completed.timestamp()
                        ),
                        ('performers', [
                            OrderedDict([
                                ('is_completed', True),
                                (
                                    'date_completed_tsp',
                                    task_performer.date_completed.timestamp()
                                ),
                                ('type', 'user'),
                                ('source_id', user.id)
                            ])
                        ]),
                        ('checklists_total', 0),
                        ('checklists_marked', 0),
                        ('status', 'completed'),
                    ]),
                    OrderedDict([
                        ('id', task_2.id),
                        ('name', 'Task №2'),
                        ('api_name', task_2.api_name),
                        ('description', None),
                        ('number', 2),
                        ('delay', None),
                        ('due_date_tsp', None),
                        ('date_started_tsp', task_2.date_started.timestamp()),
                        ('date_completed_tsp', None),
                        ('performers', [
                            OrderedDict([
                                ('is_completed', False),
                                ('date_completed_tsp', None),
                                ('type', 'user'),
                                ('source_id', user.id)
                            ])
                        ]),
                        ('checklists_total', 0),
                        ('checklists_marked', 0),
                        ('status', 'active'),
                    ])
                ]
            }
        }
    }
    complete_task_webhook_mock.assert_called_once_with(
        user_id=user.id,
        account_id=user.account_id,
        payload=payload
    )


def test_send_task_returned_webhook__ok(api_client, mocker):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(
        user=user,
        tasks_count=2,
        active_task_number=2
    )
    template = workflow.template
    create_task_returned_webhook(user)
    task_2 = workflow.tasks.get(number=2)
    api_client.token_authenticate(user)
    send_task_returned_webhook_mock = mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay'
    )

    # act
    response = api_client.post(
        f'/v2/tasks/{task_2.id}/revert',
        data={'comment': 'test'}
    )

    # assert
    assert response.status_code == 204

    # act
    task_2.refresh_from_db()
    task_1 = workflow.tasks.get(number=1)

    payload = {
        'task': {
            'id': task_2.id,
            'name': 'Task №2',
            'api_name': task_2.api_name,
            'description': None,
            'contains_comments': False,
            'require_completion_by_all': False,
            'output': [],
            'delay': None,
            'date_started_tsp': None,
            'date_completed_tsp': None,
            'due_date_tsp': None,
            'is_completed': False,
            'performers': [
                OrderedDict([
                    ('is_completed', False),
                    ('date_completed_tsp', None),
                    ('type', 'user'),
                    ('source_id', user.id)
                ])
            ],
            'is_urgent': False,
            'checklists_marked': 0,
            'checklists_total': 0,
            'checklists': [],
            'sub_workflows': [],
            'status': 'pending',
            'workflow': {
                'id': workflow.id,
                'name': 'Test workflow',
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
                'template': {
                    'id': template.id,
                    'name': 'Test workflow',
                    'is_active': True,
                    'wf_name_template': None
                },
                'kickoff': {
                    'output': []
                },
                'current_task': {
                    'id': task_1.id,
                    'name': 'Task №1',
                    'api_name': task_1.api_name,
                    'description': None,
                    'number': 1,
                    'due_date_tsp': None,
                    'date_started_tsp': task_1.date_started.timestamp(),
                    'date_completed_tsp': None,
                    'performers': [
                        {
                            'id': user.id,
                            'first_name': 'John',
                            'last_name': 'Doe'
                        }
                    ]
                },
                'tasks': [
                    OrderedDict([
                        ('id', task_1.id),
                        ('name', 'Task №1'),
                        ('api_name', task_1.api_name),
                        ('description', None),
                        ('number', 1),
                        ('delay', None),
                        ('due_date_tsp', None),
                        ('date_started_tsp', task_1.date_started.timestamp()),
                        ('date_completed_tsp', None),
                        ('performers', [
                            OrderedDict([
                                ('is_completed', False),
                                ('date_completed_tsp', None),
                                ('type', 'user'),
                                ('source_id', user.id)
                            ])
                        ]),
                        ('checklists_total', 0),
                        ('checklists_marked', 0),
                        ('status', 'active'),
                    ]),
                    OrderedDict([
                        ('id', task_2.id),
                        ('name', 'Task №2'),
                        ('api_name', task_2.api_name),
                        ('description', None),
                        ('number', 2),
                        ('delay', None),
                        ('due_date_tsp', None),
                        ('date_started_tsp', None),
                        ('date_completed_tsp', None),
                        ('performers', [
                            OrderedDict([
                                ('is_completed', False),
                                ('date_completed_tsp', None),
                                ('type', 'user'),
                                ('source_id', user.id)
                            ])
                        ]),
                        ('checklists_total', 0),
                        ('checklists_marked', 0),
                        ('status', 'pending'),
                    ])
                ]
            }
        }
    }
    send_task_returned_webhook_mock.assert_called_once_with(
        user_id=user.id,
        account_id=user.account_id,
        payload=payload
    )


def test_send_workflow_started_webhook__ok(api_client, mocker):

    # arrange
    user = create_test_owner()
    template = create_test_template(user, tasks_count=2, is_active=True)
    create_wf_created_webhook(user)
    api_client.token_authenticate(user)
    send_workflow_started_webhook_mock = mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_workflow_started_webhook.delay'
    )

    # act
    response = api_client.post(f'/templates/{template.id}/run')

    # assert
    assert response.status_code == 200
    workflow = Workflow.objects.get(id=response.data['id'])
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)

    # act
    payload = {
        'workflow': {
            'id': workflow.id,
            'name': workflow.name,
            'status': WorkflowStatus.RUNNING,
            'description': 'Test desc',
            'finalizable': False,
            'is_external': False,
            'is_urgent': False,
            'date_created_tsp': workflow.date_created.timestamp(),
            'date_completed_tsp': None,
            'workflow_starter': user.id,
            'ancestor_task_id': None,
            'is_legacy_template': False,
            'legacy_template_name': None,
            'template': {
                'id': template.id,
                'name': 'Test workflow',
                'is_active': True,
                'wf_name_template': None
            },
            'kickoff': {
                'output': []
            },
            'current_task': {
                'id': task_1.id,
                'name': 'Task №1',
                'api_name': task_1.api_name,
                'description': None,
                'number': 1,
                'due_date_tsp': None,
                'date_started_tsp': task_1.date_started.timestamp(),
                'date_completed_tsp': None,
                'performers': [
                    {
                        'id': user.id,
                        'first_name': 'John',
                        'last_name': 'Doe'
                    }
                ]
            },
            'tasks': [
                OrderedDict([
                    ('id', task_1.id),
                    ('name', 'Task №1'),
                    ('api_name', task_1.api_name),
                    ('description', None),
                    ('number', 1),
                    ('delay', None),
                    ('due_date_tsp', None),
                    ('date_started_tsp', task_1.date_started.timestamp()),
                    ('date_completed_tsp', None),
                    ('performers', [
                        OrderedDict([
                            ('is_completed', False),
                            ('date_completed_tsp', None),
                            ('type', 'user'),
                            ('source_id', user.id)
                        ])
                    ]),
                    ('checklists_total', 0),
                    ('checklists_marked', 0),
                    ('status', 'active'),
                ]),
                OrderedDict([
                    ('id', task_2.id),
                    ('name', 'Task №2'),
                    ('api_name', task_2.api_name),
                    ('description', None),
                    ('number', 2),
                    ('delay', None),
                    ('due_date_tsp', None),
                    ('date_started_tsp', None),
                    ('date_completed_tsp', None),
                    ('performers', []),
                    ('checklists_total', 0),
                    ('checklists_marked', 0),
                    ('status', 'pending'),
                ])
            ]
        }
    }
    send_workflow_started_webhook_mock.assert_called_once_with(
        user_id=user.id,
        account_id=user.account_id,
        payload=payload
    )


def test_send_workflow_completed_webhook__ok(api_client, mocker):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user, tasks_count=2, active_task_number=2)
    task_2 = workflow.tasks.get(number=2)
    create_wf_completed_webhook(user)
    api_client.token_authenticate(user)
    send_workflow_completed_webhook_mock = mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_workflow_completed_webhook.delay'
    )

    # act
    response = api_client.post(
        f'/v2/tasks/{task_2.id}/complete',
    )

    # assert
    assert response.status_code == 200
    workflow.refresh_from_db()
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    performer_1 = task_1.taskperformer_set.first()
    performer_2 = task_2.taskperformer_set.first()

    # act
    payload = {
        'workflow': {
            'id': workflow.id,
            'name': workflow.name,
            'status': WorkflowStatus.DONE,
            'description': workflow.description,
            'finalizable': False,
            'is_external': False,
            'is_urgent': False,
            'date_created_tsp': workflow.date_created.timestamp(),
            'date_completed_tsp': workflow.date_completed.timestamp(),
            'workflow_starter': user.id,
            'ancestor_task_id': None,
            'is_legacy_template': False,
            'legacy_template_name': None,
            'template': {
                'id': workflow.template_id,
                'name': 'Test workflow',
                'is_active': True,
                'wf_name_template': None
            },
            'kickoff': {
                'output': []
            },
            'current_task': {
                'id': task_2.id,
                'name': 'Task №2',
                'api_name': task_2.api_name,
                'description': None,
                'number': 2,
                'due_date_tsp': None,
                'date_started_tsp': task_2.date_started.timestamp(),
                'date_completed_tsp': task_2.date_completed.timestamp(),
                'performers': [
                    {
                        'id': user.id,
                        'first_name': 'John',
                        'last_name': 'Doe'
                    }
                ]
            },
            'tasks': [
                OrderedDict([
                    ('id', task_1.id),
                    ('name', 'Task №1'),
                    ('api_name', task_1.api_name),
                    ('description', None),
                    ('number', 1),
                    ('delay', None),
                    ('due_date_tsp', None),
                    ('date_started_tsp', task_1.date_started.timestamp()),
                    ('date_completed_tsp', task_1.date_completed.timestamp()),
                    ('performers', [
                        OrderedDict([
                            ('is_completed', True),
                            (
                                'date_completed_tsp',
                                performer_1.date_completed.timestamp()
                            ),
                            ('type', 'user'),
                            ('source_id', user.id)
                        ])
                    ]),
                    ('checklists_total', 0),
                    ('checklists_marked', 0),
                    ('status', 'completed'),
                ]),
                OrderedDict([
                    ('id', task_2.id),
                    ('name', 'Task №2'),
                    ('api_name', task_2.api_name),
                    ('description', None),
                    ('number', 2),
                    ('delay', None),
                    ('due_date_tsp', None),
                    ('date_started_tsp', task_2.date_started.timestamp()),
                    ('date_completed_tsp', task_2.date_completed.timestamp()),
                    ('performers', [
                        OrderedDict([
                            ('is_completed', True),
                            (
                                'date_completed_tsp',
                                performer_2.date_completed.timestamp()
                            ),
                            ('type', 'user'),
                            ('source_id', user.id)
                        ])
                    ]),
                    ('checklists_total', 0),
                    ('checklists_marked', 0),
                    ('status', 'completed'),
                ])
            ]
        }
    }
    send_workflow_completed_webhook_mock.assert_called_once_with(
        user_id=user.id,
        account_id=user.account_id,
        payload=payload
    )
