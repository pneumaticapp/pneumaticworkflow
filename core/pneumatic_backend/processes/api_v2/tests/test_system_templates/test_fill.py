import pytest
from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.processes.models import (
    SystemTemplate,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    FieldType,
    DueDateRule,
)

pytestmark = pytest.mark.django_db


def test_fill__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)

    system_template = {
        'name': 'Clients requests processing',
        'kickoff': {
            'fields': [
                {
                    'name': 'Client name',
                    'type': FieldType.USER,
                    'order': 0,
                    'required': True,
                    'description': 'Enter client name',
                    'api_name': 'client-name-4',
                },
                {
                    'name': 'Kind of client activity',
                    'type':  FieldType.CHECKBOX,
                    'order': 1,
                    'required': True,
                    'api_name': 'kind-of-client-activity-5',
                    'selections': [
                        {'value': 'Sales'},
                        {'value': 'B2B'},
                        {'value': 'IT'},
                        {'value': 'Other'}
                    ],
                }
            ],
        },
        'tasks': [
            {
                'name': 'Checking data',
                'number': 1,
                'raw_performers': [
                    {
                        'type': PerformerType.FIELD,
                        'source_id': 'client-name-4',
                        'label': 'Client name'
                    }
                ],
                'raw_due_date': {
                    'api_name': 'raw-due-date-1',
                    'duration': '01:00:00',
                    'rule': DueDateRule.AFTER_WORKFLOW_STARTED,
                },
            },
            {
                'name': 'Finding reasons of request',
                'number': 2,
                'fields': [
                    {
                        'name': 'Reasons',
                        'order': 0,
                        'type': 'text',
                        'description': 'Reasons of client requesting',
                        'is_required': False,
                        'api_name': 'reasons-3',
                    }
                ],
                'require_completion_by_all': False
            },
            {
                'name': 'Responsing to client',
                'number': 3,
                'require_completion_by_all': False,
                'description': 'Show him {{ reasons-3 }}',
                'raw_performers': [
                    {
                        'type': PerformerType.WORKFLOW_STARTER,
                        'source_id': None,
                        'label': 'Workflow starter'
                    }
                ]
            },
            {
                'name': 'Creating report',
                'number': 4,
                'require_completion_by_all': False
            },
            {
                'name': 'Create card',
                'number': 5,
                'require_completion_by_all': False
            }
        ]
    }
    template = SystemTemplate.objects.create(
        is_active=True,
        name='System template',
        template=system_template
    )

    # act
    response = api_client.post(f'/templates/system/{template.id}/fill')
    response = api_client.post(
        path=f'/templates',
        data=response.data
    )

    # assert
    assert response.status_code == 200
    response_data = response.data
    assert response_data['name'] == system_template['name']
    assert response_data['wf_name_template'] is None
    assert response_data['is_active'] is False
    assert response_data['is_public'] is False
    assert response_data['public_url'] is not None
    assert response_data['template_owners'] == [user.id]
    tasks_data = response_data['tasks']
    assert len(tasks_data) == 5
    task_1 = tasks_data[0]
    task_2 = tasks_data[1]
    task_3 = tasks_data[2]
    assert task_1['api_name']
    assert task_1['raw_performers'][0]['type'] == PerformerType.FIELD
    assert task_1['raw_performers'][0]['source_id'] == 'client-name-4'
    assert task_1['raw_performers'][0]['label'] == 'Client name'

    raw_due_date = task_1['raw_due_date']
    assert raw_due_date['duration'] == '01:00:00'
    assert raw_due_date['rule'] == DueDateRule.AFTER_WORKFLOW_STARTED
    assert raw_due_date['api_name'] == 'raw-due-date-1'

    assert task_2['api_name']
    assert task_2['raw_performers'][0]['type'] == PerformerType.USER
    assert task_2['raw_performers'][0]['label'] == user.name_by_status
    assert task_2['raw_performers'][0]['source_id'] == str(user.id)
    assert len(task_2['fields']) == 1

    assert task_3['api_name']
    assert task_3['raw_performers'][0]['type'] == (
        PerformerType.WORKFLOW_STARTER
    )
    assert task_3['raw_performers'][0]['label'] == 'Workflow starter'


def test_fill__set_wf_name_template__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)

    system_template = {
        'name': 'B2B Sales',
        'wf_name_template': '{{ client-name }} request. {{ date }}',
        'kickoff': {
            'fields': [
                {
                    'name': 'Client name',
                    'type': FieldType.USER,
                    'order': 0,
                    'required': True,
                    'api_name': 'client-name',
                },
            ],
        },
        'tasks': [
            {
                'name': 'Checking data',
                'number': 1,
                'raw_performers': [
                    {
                        'type': PerformerType.WORKFLOW_STARTER,
                    }
                ],
            },
        ]
    }
    template = SystemTemplate.objects.create(
        is_active=True,
        name='System template',
        template=system_template
    )

    # act
    response = api_client.post(f'/templates/system/{template.id}/fill')
    response = api_client.post(
        path=f'/templates',
        data=response.data
    )

    # assert
    assert response.status_code == 200
    response_data = response.data
    assert response_data['name'] == system_template['name']
    assert response_data['wf_name_template'] == (
        system_template['wf_name_template']
    )


def test_create__save_task_api_name__ok(api_client):
    user = create_test_user()
    api_client.token_authenticate(user)
    task_api_name = 'task-api-name'
    system_template = {
        'name': 'Clients requests processing',
        'kickoff': {},
        'tasks': [
            {
                'name': 'Checking data',
                'api_name': task_api_name,
                'number': 1,
                'raw_performers': [
                    {
                        'type': PerformerType.FIELD,
                        'source_id': 'client-name-4',
                        'label': 'Client name'
                    }
                ],
            },
        ]
    }
    template = SystemTemplate.objects.create(
        is_active=True,
        name='System template',
        template=system_template
    )

    response = api_client.post(f'/templates/system/{template.id}/fill')
    response = api_client.post(
        path=f'/templates',
        data=response.data
    )
    assert response.status_code == 200
    task_data = response.data['tasks'][0]
    assert task_data['api_name'] == task_api_name


def test_create_public__ok(api_client):

    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)

    system_template = {
        'name': 'Clients requests processing',
        'is_public': True,
        'kickoff': {
            'fields': [
                {
                    'name': 'Client name',
                    'type': FieldType.USER,
                    'order': 0,
                    'required': True,
                    'description': 'Enter client name',
                    'api_name': 'client-name-4',
                },
                {
                    'name': 'Kind of client activity',
                    'type':  FieldType.CHECKBOX,
                    'order': 1,
                    'required': True,
                    'api_name': 'kind-of-client-activity-5',
                    'selections': [
                        {'value': 'Sales'},
                        {'value': 'B2B'},
                        {'value': 'IT'},
                        {'value': 'Other'}
                    ],
                }
            ],
        },
        'tasks': [
            {
                'name': 'Checking data',
                'number': 1,
                'raw_performers': [
                    {
                        'type': PerformerType.FIELD,
                        'source_id': 'client-name-4',
                        'label': 'Client name'
                    }
                ]
            },
            {
                'name': 'Finding reasons of request',
                'number': 2,
                'fields': [
                    {
                        'name': 'Reasons',
                        'order': 0,
                        'type': 'text',
                        'description': 'Reasons of client requesting',
                        'is_required': False,
                        'api_name': 'reasons-3',
                    }
                ],
                'require_completion_by_all': False
            },
            {
                'name': 'Responsing to client',
                'number': 3,
                'require_completion_by_all': False,
                'description': 'Show him {{ reasons-3 }}',
                'raw_performers': [
                    {
                        'type': PerformerType.WORKFLOW_STARTER,
                        'source_id': None,
                        'label': 'Workflow starter'
                    }
                ]
            },
            {
                'name': 'Creating report',
                'number': 4,
                'require_completion_by_all': False
            },
            {
                'name': 'Create card',
                'number': 5,
                'require_completion_by_all': False
            }
        ]
    }
    system_template = SystemTemplate.objects.create(
        is_active=True,
        name='System template',
        template=system_template
    )

    response = api_client.post(
        path=f'/templates/system/{system_template.id}/fill'
    )
    response = api_client.post(
        path=f'/templates',
        data=response.data
    )
    assert response.status_code == 200
    response_data = response.data
    assert response_data['template_owners'] == [user.id]
    assert response_data['is_active'] is False
    assert response_data['is_public'] is True
    assert response_data['public_url'] is not None

    tasks_data = response_data['tasks']
    assert len(tasks_data) == 5
    task_1 = tasks_data[0]
    task_2 = tasks_data[1]
    task_3 = tasks_data[2]
    assert task_1['raw_performers'][0]['type'] == PerformerType.FIELD
    assert task_1['raw_performers'][0]['source_id'] == 'client-name-4'
    assert task_1['raw_performers'][0]['label'] == 'Client name'

    assert task_2['raw_performers'][0]['type'] == PerformerType.USER
    assert task_2['raw_performers'][0]['source_id'] == str(user.id)
    assert task_2['raw_performers'][0]['label'] == user.name_by_status
    assert len(task_2['fields']) == 1

    assert task_3['raw_performers'][0]['type'] == (
        PerformerType.WORKFLOW_STARTER
    )
    assert task_3['raw_performers'][0]['label'] == 'Workflow starter'
