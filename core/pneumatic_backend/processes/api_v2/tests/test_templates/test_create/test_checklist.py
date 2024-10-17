import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user
)
from pneumatic_backend.processes.models import (
    ChecklistTemplate,
    Template, TaskTemplate,
)
from pneumatic_backend.processes.enums import (
    PerformerType,
)
from pneumatic_backend.processes.messages import template as messages
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.authentication.enums import AuthTokenType


pytestmark = pytest.mark.django_db


def test_create__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.checklist_created'
    )
    checklists_data = [
        {
            'api_name': 'checklist-1',
            'selections': [
                {
                    'api_name': 'cl-selection-1',
                    'value': 'some value 1'
                }
            ]
        }
    ]
    task_api_name = 'task-1'

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'api_name': task_api_name,
                    'checklists': checklists_data,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['tasks'][0]['checklists']) == 1
    data = response.data['tasks'][0]['checklists'][0]
    assert data.get('id') is None
    assert data['api_name'] == 'checklist-1'

    task_template = TaskTemplate.objects.get(api_name=task_api_name)
    template_id = response.data['id']
    checklist = ChecklistTemplate.objects.get(
        api_name=data['api_name'],
        template_id=template_id
    )
    assert checklist.template_id == template_id
    assert checklist.task == task_template
    assert checklist.api_name == 'checklist-1'
    template = Template.objects.get(id=template_id)
    task = template.tasks.first()
    analytics_mock.assert_called_once_with(
        user=user,
        template=template,
        task=task,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )


def test_create__generate_api_name__ok(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    api_name = 'generated-api-name'
    mocker.patch(
        'pneumatic_backend.processes.models.templates.'
        'checklist.ChecklistTemplate._create_api_name',
        return_value=api_name
    )
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.checklist_created'
    )
    checklists_data = [
        {
            'selections': [
                {
                    'api_name': 'cl-selection-1',
                    'value': 'some value 1'
                }
            ]
        }
    ]

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'checklists': checklists_data,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 200
    data = response.data['tasks'][0]['checklists'][0]
    assert data['api_name'] == api_name
    checklist = ChecklistTemplate.objects.get(
        api_name=data['api_name'],
        template_id=response.data['id']
    )
    assert checklist.api_name == api_name


def test_create__draft__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.checklist_created'
    )
    checklists_data = [
        {
            'api_name': 'checklist-1',
            'selections': [
                {
                    'api_name': 'cl-selection-1',
                    'value': 'some value 1'
                }
            ]
        }
    ]

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': False,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'checklists': checklists_data,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['tasks'][0]['checklists']) == 1
    data = response.data['tasks'][0]['checklists'][0]
    assert data.get('id') is None
    assert data['api_name'] == 'checklist-1'
    analytics_mock.assert_not_called()


def test_create__fields_with_equal_api_names__validation_error(
    mocker,
    api_client,
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.checklist_created'
    )
    checklist_api_name = 'checklist-1'
    step = 'Second step'

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ],
                    'checklists': [
                        {
                            'api_name': checklist_api_name,
                            'selections': [
                                {
                                    'api_name': 'cl-selection-1',
                                    'value': 'some value 1'
                                }
                            ]
                        }
                    ]
                },
                {
                    'number': 2,
                    'name': step,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ],
                    'checklists': [
                        {
                            'api_name': checklist_api_name,
                            'selections': [
                                {
                                    'api_name': 'cl-selection-2',
                                    'value': 'some value 2'
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    message = messages.MSG_PT_0047(
        step_name=step,
        api_name=checklist_api_name
    )
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['api_name'] == checklist_api_name


def test_create__skip_selections__validation_error(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    checklists_data = [{'api_name': 'checklist-1'}]

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'checklists': checklists_data,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    message = 'Selections: this field is required.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['api_name'] == 'checklist-1'
    assert response.data['details']['reason'] == message


def test_create__empty_selections__validation_error(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    checklists_data = [
        {
            'api_name': 'checklist-2',
            'selections': []
        }
    ]

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'api_name': 'task-1',
                    'name': 'First step',
                    'checklists': checklists_data,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PT_0040
    assert response.data['details']['api_name'] == 'checklist-2'
    assert response.data['details']['reason'] == messages.MSG_PT_0040


def test_create__validation_error_with_task_api_name__ok(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    checklists_data = [
        {
            'selections': []
        }
    ]
    api_name = 'generated-api-name'
    mocker.patch(
        'pneumatic_backend.processes.models.templates.'
        'task.TaskTemplate._create_api_name',
        return_value=api_name
    )
    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'checklists': checklists_data,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PT_0040
    assert response.data['details']['api_name'] == api_name
    assert response.data['details']['reason'] == messages.MSG_PT_0040


def test_create__null_selections__validation_error(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    checklists_data = [
        {
            'api_name': 'checklist-1',
            'selections': None
        }
    ]

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'checklists': checklists_data,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    message = 'Selections: this field may not be null.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['api_name'] == 'checklist-1'
    assert response.data['details']['reason'] == message


def test_create__list_without_dict__validation_error(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    checklists_data = [
        [
            {
                'api_name': 'checklist-1',
                'selections': None
            }
        ]
    ]

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'checklists': checklists_data,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    message = 'Invalid data. Expected a dictionary, but got list.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
