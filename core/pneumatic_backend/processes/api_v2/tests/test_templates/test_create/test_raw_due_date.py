import pytest
from datetime import timedelta
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user
)
from pneumatic_backend.processes.models import (
    RawDueDateTemplate,
    TaskTemplate,
)
from pneumatic_backend.processes.enums import (
    DueDateRule,
    PerformerType,
    FieldType,
)
from pneumatic_backend.processes.messages import template as messages
from pneumatic_backend.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_create__after_task_started__ok(api_client):

    # arrange
    user = create_test_user()
    raw_due_date_data = {
        'api_name': 'raw-due-date-1',
        'duration': '01:00:00',
        'duration_months': 2,
        'rule': DueDateRule.AFTER_TASK_STARTED,
        'source_id': 'task-1'
    }
    task_api_name = 'task-2'
    api_client.token_authenticate(user)

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
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                },
                {
                    'number': 2,
                    'name': 'Second step',
                    'api_name': task_api_name,
                    'raw_due_date': raw_due_date_data,
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
    data = response.data['tasks'][1]['raw_due_date']
    assert data == raw_due_date_data

    template_id = response.data['id']
    task_template = TaskTemplate.objects.get(api_name=task_api_name)
    raw_due_date = RawDueDateTemplate.objects.get(
        api_name=data['api_name'],
        template_id=template_id,
        task=task_template,
    )
    assert raw_due_date.duration == timedelta(hours=1)
    assert raw_due_date.duration_months == 2
    assert raw_due_date.rule == raw_due_date_data['rule']
    assert raw_due_date.source_id == raw_due_date_data['source_id']
    assert raw_due_date.task == task_template


def test_create__after_task_started__current_task__ok(
    api_client,
):
    # arrange
    user = create_test_user()
    api_name = 'raw-due-date-1'
    raw_due_date_data = {
        'api_name': api_name,
        'duration': '01:00:00',
        'duration_months': 0,
        'rule': DueDateRule.AFTER_TASK_STARTED,
        'source_id': 'task-1'
    }
    api_client.token_authenticate(user)

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
                    'raw_due_date': raw_due_date_data,
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
    data = response.data['tasks'][0]['raw_due_date']
    assert data == raw_due_date_data

    template_id = response.data['id']
    raw_due_date = RawDueDateTemplate.objects.get(
        api_name=data['api_name'],
        template_id=template_id,
    )
    assert raw_due_date.duration == timedelta(hours=1)
    assert raw_due_date.duration_months == 0
    assert raw_due_date.rule == raw_due_date_data['rule']
    assert raw_due_date.source_id == raw_due_date_data['source_id']


def test_create__after_task_started__next_task__validation_error(
    api_client
):

    # arrange
    user = create_test_user()
    api_name = 'raw-due-date-1'
    raw_due_date_data = {
        'api_name': api_name,
        'duration': '01:00:00',
        'duration_months': 0,
        'rule': DueDateRule.AFTER_TASK_STARTED,
        'source_id': 'task-2'
    }
    api_client.token_authenticate(user)

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
                    'raw_due_date': raw_due_date_data,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                },
                {
                    'number': 2,
                    'api_name': 'task-2',
                    'name': 'Second step',
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
    assert response.data['message'] == messages.MSG_PT_0031
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == api_name
    assert response.data['details']['reason'] == messages.MSG_PT_0031


def test_create__after_task_started__not_existent_task__validation_error(
    api_client
):

    # arrange
    user = create_test_user()
    api_name = 'raw-due-date-1'
    raw_due_date_data = {
        'api_name': api_name,
        'duration': '01:00:00',
        'duration_months': 10,
        'rule': DueDateRule.AFTER_TASK_STARTED,
        'source_id': 'task-undefined'
    }
    api_client.token_authenticate(user)

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
                    'raw_due_date': raw_due_date_data,
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
    assert response.data['message'] == messages.MSG_PT_0031
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == api_name
    assert response.data['details']['reason'] == messages.MSG_PT_0031


def test_create__after_task_completed__ok(api_client):

    # arrange
    user = create_test_user()
    raw_due_date_data = {
        'api_name': 'raw-due-date-1',
        'duration': '01:00:00',
        'duration_months': 10,
        'rule': DueDateRule.AFTER_TASK_COMPLETED,
        'source_id': 'task-1'
    }
    api_client.token_authenticate(user)

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
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                },
                {
                    'number': 2,
                    'name': 'Second step',
                    'raw_due_date': raw_due_date_data,
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
    data = response.data['tasks'][1]['raw_due_date']
    assert data == raw_due_date_data

    template_id = response.data['id']
    raw_due_date = RawDueDateTemplate.objects.get(
        api_name=data['api_name'],
        template_id=template_id,
    )
    assert raw_due_date.duration == timedelta(hours=1)
    assert raw_due_date.duration_months == 10
    assert raw_due_date.rule == raw_due_date_data['rule']
    assert raw_due_date.source_id == raw_due_date_data['source_id']


def test_create__after_task_completed__current_task__validation_error(
    api_client
):

    # arrange
    user = create_test_user()
    api_name = 'raw-due-date-1'
    raw_due_date_data = {
        'api_name': api_name,
        'duration': '01:00:00',
        'duration_months': 10,
        'rule': DueDateRule.AFTER_TASK_COMPLETED,
        'source_id': 'task-1'
    }
    api_client.token_authenticate(user)

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
                    'raw_due_date': raw_due_date_data,
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
    assert response.data['message'] == messages.MSG_PT_0030
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == api_name
    assert response.data['details']['reason'] == messages.MSG_PT_0030


def test_create__after_task_completed__next_task__validation_error(
    api_client
):

    # arrange
    user = create_test_user()
    api_name = 'raw-due-date-1'
    raw_due_date_data = {
        'api_name': api_name,
        'duration': '01:00:00',
        'duration_months': 10,
        'rule': DueDateRule.AFTER_TASK_COMPLETED,
        'source_id': 'task-2'
    }
    api_client.token_authenticate(user)

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
                    'raw_due_date': raw_due_date_data,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                },
                {
                    'number': 2,
                    'api_name': 'task-2',
                    'name': 'Second step',
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
    assert response.data['message'] == messages.MSG_PT_0030
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == api_name
    assert response.data['details']['reason'] == messages.MSG_PT_0030


def test_create__after_task_completed__not_existent_task__validation_error(
    api_client
):

    # arrange
    user = create_test_user()
    api_name = 'raw-due-date-1'
    raw_due_date_data = {
        'api_name': api_name,
        'duration': '01:00:00',
        'duration_months': 10,
        'rule': DueDateRule.AFTER_TASK_COMPLETED,
        'source_id': 'task-undefined'
    }
    api_client.token_authenticate(user)

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
                    'raw_due_date': raw_due_date_data,
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
    assert response.data['message'] == messages.MSG_PT_0030
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == api_name
    assert response.data['details']['reason'] == messages.MSG_PT_0030


def test_create__after_workflow_started__ok(api_client):

    # arrange
    user = create_test_user()
    raw_due_date_data = {
        'api_name': 'raw-due-date-1',
        'duration': '01:00:00',
        'duration_months': 10,
        'rule': DueDateRule.AFTER_WORKFLOW_STARTED,
        'source_id': None
    }
    api_client.token_authenticate(user)

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
                    'raw_due_date': raw_due_date_data,
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
    data = response.data['tasks'][0]['raw_due_date']
    assert data == raw_due_date_data

    template_id = response.data['id']
    raw_due_date = RawDueDateTemplate.objects.get(
        api_name=data['api_name'],
        template_id=template_id,
    )
    assert raw_due_date.duration == timedelta(hours=1)
    assert raw_due_date.duration_months == 10
    assert raw_due_date.rule == raw_due_date_data['rule']
    assert raw_due_date.source_id is None


@pytest.mark.parametrize('is_required', (True, False))
def test_create__after_field__ok(is_required, api_client):

    # arrange
    user = create_test_user()
    raw_due_date_data = {
        'api_name': 'raw-due-date-1',
        'duration': '01:00:00',
        'duration_months': 10,
        'rule': DueDateRule.AFTER_FIELD,
        'source_id': 'field-1'
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
            'kickoff': {
                'fields': [
                    {
                        'name': 'Date field',
                        'order': 1,
                        'type': FieldType.DATE,
                        'is_required': is_required,
                        'api_name': 'field-1'
                    }
                ]
            },
            'tasks': [
                {
                    'number': 1,
                    'api_name': 'task-1',
                    'name': 'First step',
                    'raw_due_date': raw_due_date_data,
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
    data = response.data['tasks'][0]['raw_due_date']
    assert data == raw_due_date_data

    template_id = response.data['id']
    raw_due_date = RawDueDateTemplate.objects.get(
        api_name=data['api_name'],
        template_id=template_id,
    )
    assert raw_due_date.duration == timedelta(hours=1)
    assert raw_due_date.duration_months == 10
    assert raw_due_date.rule == raw_due_date_data['rule']
    assert raw_due_date.source_id == raw_due_date_data['source_id']


def test_create__after_field__not_source_id__validation_error(
    api_client
):

    # arrange
    user = create_test_user()
    api_name = 'raw-due-date-1'
    raw_due_date_data = {
        'api_name': 'raw-due-date-1',
        'duration': '01:00:00',
        'duration_months': 10,
        'rule': DueDateRule.AFTER_FIELD,
    }
    api_client.token_authenticate(user)

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
                    'raw_due_date': raw_due_date_data,
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
    assert response.data['message'] == messages.MSG_PT_0027
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == api_name
    assert response.data['details']['reason'] == messages.MSG_PT_0027


def test_create__after_field__source_id_is_null__validation_error(
    api_client
):
    # arrange
    user = create_test_user()
    api_name = 'raw-due-date-1'
    raw_due_date_data = {
        'api_name': 'raw-due-date-1',
        'duration': '01:00:00',
        'duration_months': 10,
        'rule': DueDateRule.AFTER_FIELD,
        'source_id': None
    }
    api_client.token_authenticate(user)

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
                    'raw_due_date': raw_due_date_data,
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
    assert response.data['message'] == messages.MSG_PT_0027
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == api_name
    assert response.data['details']['reason'] == messages.MSG_PT_0027


def test_create__after_field__current_task_field__validation_error(
    api_client
):

    # arrange
    user = create_test_user()
    api_name = 'raw-due-date-1'
    raw_due_date_data = {
        'api_name': 'raw-due-date-1',
        'duration': '01:00:00',
        'duration_months': 10,
        'rule': DueDateRule.AFTER_FIELD,
        'source_id': 'field-1'
    }
    api_client.token_authenticate(user)

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
                    'fields': [
                        {
                            'name': 'Date field',
                            'order': 1,
                            'type': FieldType.DATE,
                            'api_name': 'field-1'
                        }
                    ],
                    'raw_due_date': raw_due_date_data,
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
    assert response.data['message'] == messages.MSG_PT_0028
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == api_name
    assert response.data['details']['reason'] == messages.MSG_PT_0028


def test_create__after_field__next_task_field__validation_error(
    api_client
):

    # arrange
    user = create_test_user()
    api_name = 'raw-due-date-1'
    raw_due_date_data = {
        'api_name': 'raw-due-date-1',
        'duration': '01:00:00',
        'duration_months': 10,
        'rule': DueDateRule.AFTER_FIELD,
        'source_id': 'field-1'
    }
    api_client.token_authenticate(user)

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
                    'raw_due_date': raw_due_date_data,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                },
                {
                    'number': 2,
                    'name': 'Second step',
                    'fields': [
                        {
                            'name': 'Date field',
                            'order': 1,
                            'type': FieldType.DATE,
                            'api_name': 'field-1'
                        }
                    ],
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
    assert response.data['message'] == messages.MSG_PT_0028
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == api_name
    assert response.data['details']['reason'] == messages.MSG_PT_0028


def test_create__after_field__not_existent_field__validation_error(
    api_client
):

    # arrange
    user = create_test_user()
    api_name = 'raw-due-date-1'
    raw_due_date_data = {
        'api_name': 'raw-due-date-1',
        'duration': '01:00:00',
        'duration_months': 10,
        'rule': DueDateRule.AFTER_FIELD,
        'source_id': 'field-1'
    }
    api_client.token_authenticate(user)

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
                    'raw_due_date': raw_due_date_data,
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
    assert response.data['message'] == messages.MSG_PT_0028
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == api_name
    assert response.data['details']['reason'] == messages.MSG_PT_0028


def test_create__after_field__field_type_is_not_date__validation_error(
    api_client
):

    # arrange
    user = create_test_user()
    api_name = 'raw-due-date-1'
    raw_due_date_data = {
        'api_name': 'raw-due-date-1',
        'duration': '01:00:00',
        'duration_months': 10,
        'rule': DueDateRule.AFTER_FIELD,
        'source_id': 'field-1'
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
            'kickoff': {
                'fields': [
                    {
                        'name': 'Date field',
                        'order': 1,
                        'type': FieldType.TEXT,
                        'api_name': 'field-1'
                    }
                ]
            },
            'tasks': [
                {
                    'number': 1,
                    'api_name': 'task-1',
                    'name': 'First step',
                    'raw_due_date': raw_due_date_data,
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
    assert response.data['message'] == messages.MSG_PT_0028
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == api_name
    assert response.data['details']['reason'] == messages.MSG_PT_0028


@pytest.mark.parametrize('is_required', (True, False))
def test_create__before_field__ok(is_required, api_client):

    # arrange
    user = create_test_user()
    raw_due_date_data = {
        'api_name': 'raw-due-date-1',
        'duration': '01:00:00',
        'duration_months': 10,
        'rule': DueDateRule.BEFORE_FIELD,
        'source_id': 'field-1'
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
            'kickoff': {
                'fields': [
                    {
                        'name': 'Date field',
                        'order': 1,
                        'type': FieldType.DATE,
                        'is_required': is_required,
                        'api_name': 'field-1'
                    }
                ]
            },
            'tasks': [
                {
                    'number': 1,
                    'api_name': 'task-1',
                    'name': 'First step',
                    'raw_due_date': raw_due_date_data,
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
    data = response.data['tasks'][0]['raw_due_date']
    assert data == raw_due_date_data

    template_id = response.data['id']
    raw_due_date = RawDueDateTemplate.objects.get(
        api_name=data['api_name'],
        template_id=template_id,
    )
    assert raw_due_date.duration == timedelta(hours=1)
    assert raw_due_date.duration_months == 10
    assert raw_due_date.rule == raw_due_date_data['rule']
    assert raw_due_date.source_id == raw_due_date_data['source_id']


def test_create__before_field__not_source_id__validation_error(
    api_client
):

    # arrange
    user = create_test_user()
    api_name = 'raw-due-date-1'
    raw_due_date_data = {
        'api_name': 'raw-due-date-1',
        'duration': '01:00:00',
        'duration_months': 10,
        'rule': DueDateRule.BEFORE_FIELD,
    }
    api_client.token_authenticate(user)

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
                    'raw_due_date': raw_due_date_data,
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
    assert response.data['message'] == messages.MSG_PT_0027
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == api_name
    assert response.data['details']['reason'] == messages.MSG_PT_0027


def test_create__before_field__current_task_field__validation_error(
    api_client
):
    # arrange
    user = create_test_user()
    api_name = 'raw-due-date-1'
    raw_due_date_data = {
        'api_name': 'raw-due-date-1',
        'duration': '01:00:00',
        'duration_months': 10,
        'rule': DueDateRule.BEFORE_FIELD,
        'source_id': None
    }
    api_client.token_authenticate(user)

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
                    'raw_due_date': raw_due_date_data,
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
    assert response.data['message'] == messages.MSG_PT_0027
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == api_name
    assert response.data['details']['reason'] == messages.MSG_PT_0027


def test_create__before_field__next_task_field__validation_error(
    api_client
):

    # arrange
    user = create_test_user()
    api_name = 'raw-due-date-1'
    raw_due_date_data = {
        'api_name': 'raw-due-date-1',
        'duration': '01:00:00',
        'duration_months': 10,
        'rule': DueDateRule.BEFORE_FIELD,
        'source_id': 'field-1'
    }
    api_client.token_authenticate(user)

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
                    'raw_due_date': raw_due_date_data,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                },
                {
                    'number': 2,
                    'name': 'Second step',
                    'fields': [
                        {
                            'name': 'Date field',
                            'order': 1,
                            'type': FieldType.DATE,
                            'api_name': 'field-1'
                        }
                    ],
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
    assert response.data['message'] == messages.MSG_PT_0028
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == api_name
    assert response.data['details']['reason'] == messages.MSG_PT_0028


def test_create__before_field__not_existent_field__validation_error(
    api_client
):

    # arrange
    user = create_test_user()
    api_name = 'raw-due-date-1'
    raw_due_date_data = {
        'api_name': 'raw-due-date-1',
        'duration': '01:00:00',
        'duration_months': 10,
        'rule': DueDateRule.BEFORE_FIELD,
        'source_id': 'field-1'
    }
    api_client.token_authenticate(user)

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
                    'raw_due_date': raw_due_date_data,
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
    assert response.data['message'] == messages.MSG_PT_0028
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == api_name
    assert response.data['details']['reason'] == messages.MSG_PT_0028


def test_create__before_field__field_is_not_date__validation_error(
    api_client
):

    # arrange
    user = create_test_user()
    api_name = 'raw-due-date-1'
    raw_due_date_data = {
        'api_name': 'raw-due-date-1',
        'duration': '01:00:00',
        'duration_months': 10,
        'rule': DueDateRule.BEFORE_FIELD,
        'source_id': 'field-1'
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
            'kickoff': {
                'fields': [
                    {
                        'name': 'Date field',
                        'order': 1,
                        'type': FieldType.TEXT,
                        'api_name': 'field-1'
                    }
                ]
            },
            'tasks': [
                {
                    'number': 1,
                    'api_name': 'task-1',
                    'name': 'First step',
                    'raw_due_date': raw_due_date_data,
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
    assert response.data['message'] == messages.MSG_PT_0028
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == api_name
    assert response.data['details']['reason'] == messages.MSG_PT_0028


def test_create__non_existent_rule__validation_error(
    api_client
):

    # arrange
    user = create_test_user()
    api_name = 'raw-due-date-1'
    raw_due_date_data = {
        'api_name': 'raw-due-date-1',
        'duration': '01:00:00',
        'duration_months': 10,
        'rule': 'undefined',
        'source_id': 'field-1'
    }
    api_client.token_authenticate(user)

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
                    'raw_due_date': raw_due_date_data,
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
    message = 'Rule: "undefined" is not a valid choice.'
    assert response.status_code == 400
    assert response.data['message'] == message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == api_name
    assert response.data['details']['reason'] == message


def test_create__rule_is_null__validation_error(
    api_client
):

    # arrange
    user = create_test_user()
    api_name = 'raw-due-date-1'
    raw_due_date_data = {
        'api_name': 'raw-due-date-1',
        'duration': '01:00:00',
        'duration_months': 10,
        'rule': None,
    }
    api_client.token_authenticate(user)

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
                    'raw_due_date': raw_due_date_data,
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
    message = 'Rule: this field may not be null.'
    assert response.status_code == 400
    assert response.data['message'] == message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == api_name
    assert response.data['details']['reason'] == message


def test_create__invalid_duration__validation_error(
    api_client
):

    # arrange
    user = create_test_user()
    api_name = 'raw-due-date-1'
    raw_due_date_data = {
        'api_name': 'raw-due-date-1',
        'duration': '1 hour 5 minutes',
        'duration_months': 10,
        'rule': DueDateRule.BEFORE_FIELD,
    }
    api_client.token_authenticate(user)

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
                    'raw_due_date': raw_due_date_data,
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
    message = (
        'Duration: duration has wrong format. '
        'use one of these formats instead: [dd] [hh:[mm:]]ss[.uuuuuu].'
    )
    assert response.status_code == 400
    assert response.data['message'] == message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == api_name
    assert response.data['details']['reason'] == message


def test_create__duration_is_null__validation_error(
    api_client
):

    # arrange
    user = create_test_user()
    api_name = 'raw-due-date-1'
    raw_due_date_data = {
        'api_name': 'raw-due-date-1',
        'duration': None,
        'duration_months': 10,
        'rule': DueDateRule.BEFORE_FIELD,
    }
    api_client.token_authenticate(user)

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
                    'raw_due_date': raw_due_date_data,
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
    message = 'Duration: this field may not be null.'
    assert response.status_code == 400
    assert response.data['message'] == message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == api_name
    assert response.data['details']['reason'] == message


def test_create__equal_api_names__validation_error(api_client):

    # arrange
    user = create_test_user()
    step = 'Second step'
    due_date_api_name = 'due-date-1'
    api_client.token_authenticate(user)

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
                    'raw_due_date': {
                        'api_name': due_date_api_name,
                        'duration': '01:00:00',
                        'duration_months': 0,
                        'rule': DueDateRule.AFTER_TASK_STARTED,
                        'source_id': 'task-1'
                    },
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                },
                {
                    'number': 2,
                    'api_name': 'task-2',
                    'name': step,
                    'raw_due_date': {
                        'api_name': due_date_api_name,
                        'duration': '01:00:00',
                        'duration_months': 0,
                        'rule': DueDateRule.AFTER_TASK_STARTED,
                        'source_id': 'task-2'
                    },
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
    message = messages.MSG_PT_0052(
        step_name=step,
        api_name=due_date_api_name
    )
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['api_name'] == due_date_api_name
