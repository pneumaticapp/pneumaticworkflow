import pytest
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.processes.models.workflows.task import (
    TaskPerformer,
)
from src.processes.models.workflows.attachment import FileAttachment
from src.processes.models.workflows.fields import (
    TaskField,
    FieldSelection,
)
from src.processes.tests.fixtures import (
    create_test_owner,
    create_test_workflow,
    create_test_template, create_test_account, create_test_admin,
    create_test_not_admin, create_test_guest,
)
from src.processes.enums import (
    FieldType,
    WorkflowApiStatus,
    WorkflowStatus,
)
from src.utils.validation import ErrorCode


pytestmark = pytest.mark.django_db


def test_fields__workflow_data__ok(api_client):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(
        user,
        tasks_count=1,
        status=WorkflowStatus.DONE,
    )
    date_completed_tsp = workflow.date_completed.timestamp()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/workflows/fields')

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['next'] is None
    assert response.data['previous'] is None
    assert len(response.data['results']) == 1
    data = response.data['results'][0]
    assert data['id'] == workflow.id
    assert data['name'] == workflow.name
    assert data['status'] == workflow.status
    assert data['date_created_tsp'] == workflow.date_created.timestamp()
    assert data['date_completed_tsp'] == date_completed_tsp
    assert len(data['fields']) == 0


def test_fields__many_templates__ok(api_client):

    # arrange
    user = create_test_owner()
    workflow_1 = create_test_workflow(
        user,
        tasks_count=1,
        status=WorkflowStatus.DONE,
    )
    workflow_2 = create_test_workflow(
        user,
        tasks_count=1,
        status=WorkflowStatus.DONE,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/workflows/fields')

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 2
    assert response.data['results'][0]['id'] == workflow_2.id
    assert response.data['results'][1]['id'] == workflow_1.id


def test_fields__filter_by_template_id__ok(api_client):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(
        user,
        tasks_count=1,
        status=WorkflowStatus.DONE,
    )
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/workflows/fields',
        data={
            'template_id': workflow.template.id,
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id


def test_fields__filter_not_existent_template_id__ok(api_client):

    # arrange
    user = create_test_owner()
    create_test_workflow(user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/workflows/fields',
        data={
            'template_id': 1233123312123,
        },
    )

    # assert
    assert response.status_code == 200
    assert response.data['results'] == []


def test_fields__filter_invalid_template_id__validation_error(api_client):

    # arrange
    user = create_test_owner()
    create_test_workflow(user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/workflows/fields',
        data={
            'template_id': 'invalid',
        },
    )

    # assert
    assert response.status_code == 400
    message = 'A valid integer is required.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'template_id'


def test_fields__filter_template_id_is_null__validation_error(api_client):

    # arrange
    user = create_test_owner()
    create_test_workflow(user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/workflows/fields?template_id=null')

    # assert
    assert response.status_code == 400
    message = 'A valid integer is required.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'template_id'


@pytest.mark.parametrize('field_type', FieldType.SIMPLE_TYPES)
def test_fields__simple_field_types__ok(api_client, field_type):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    field = TaskField.objects.create(
        order=1,
        type=field_type,
        name='text',
        task=task,
        value='some text',
        markdown_value='**bold** text',
        clear_value='bold text',
        workflow=workflow,
        is_required=True,
        description='Some description',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/workflows/fields')

    # assert
    assert response.status_code == 200
    fields_data = response.data['results'][0]['fields']
    assert len(fields_data) == 1
    assert fields_data[0]['id'] == field.id
    assert fields_data[0]['order'] == 1
    assert fields_data[0]['is_required'] == field.is_required
    assert fields_data[0]['task_id'] == task.id
    assert fields_data[0]['kickoff_id'] is None
    assert fields_data[0]['type'] == field_type
    assert fields_data[0]['api_name'] == field.api_name
    assert fields_data[0]['name'] == field.name
    assert fields_data[0]['description'] == field.description
    assert fields_data[0]['value'] == field.value
    assert fields_data[0]['markdown_value'] == field.markdown_value
    assert fields_data[0]['clear_value'] == field.clear_value
    assert fields_data[0]['user_id'] == field.user_id
    assert fields_data[0]['group_id'] is None


@pytest.mark.parametrize('field_type', FieldType.TYPES_WITH_SELECTIONS)
def test_fields__field_types_with_selections__ok(api_client, field_type):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)

    field = TaskField.objects.create(
        order=3,
        type=field_type,
        name='dropdown',
        task=task,
        value='don\'t lovely value',
        clear_value='don\'t lovely value',
        markdown_value='don\'t lovely value',
        workflow=workflow,
        is_required=True,
        description='Some description',
    )
    FieldSelection.objects.create(
        field=field,
        value='don\'t lovely value',
        is_selected=True,
    )
    FieldSelection.objects.create(
        field=field,
        value='don\'t lovely value',
        is_selected=False,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/workflows/fields')

    # assert
    assert response.status_code == 200
    fields_data = response.data['results'][0]['fields']
    assert len(fields_data) == 1
    assert fields_data[0]['id'] == field.id
    assert fields_data[0]['value'] == field.value
    assert fields_data[0]['markdown_value'] == field.markdown_value
    assert fields_data[0]['clear_value'] == field.clear_value


def test_fields__type_file__ok(api_client):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    field = TaskField.objects.create(
        name='file',
        task=task,
        type=FieldType.FILE,
        value='value',
        markdown_value='[file](https://john.cena/john.cena)',
        clear_value='https://john.cena/john.cena',
        workflow=workflow,
        is_required=True,
        description='Some description',
    )
    FileAttachment.objects.create(
        name='file',
        url='https://john.cena/john.cena',
        account_id=user.account_id,
        output=field,
        workflow=workflow,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/workflows/fields')

    # assert
    assert response.status_code == 200
    fields_data = response.data['results'][0]['fields']
    assert len(fields_data) == 1
    assert fields_data[0]['id'] == field.id
    assert fields_data[0]['value'] == field.value
    assert fields_data[0]['markdown_value'] == field.markdown_value
    assert fields_data[0]['clear_value'] == field.clear_value


def test_fields__filter_by_status_running__ok(api_client):

    # arrange
    user = create_test_owner()
    template = create_test_template(
        user,
        is_active=True,
        finalizable=True,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    create_test_workflow(
        user=user,
        template=template,
        status=WorkflowStatus.DONE,
    )
    create_test_workflow(
        user=user,
        template=template,
        status=WorkflowStatus.DELAYED,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/workflows/fields',
        data={
            'status': WorkflowApiStatus.RUNNING,
        },
    )

    # assert
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == workflow.id


def test_fields__filter_by_status_delayed__ok(api_client):

    # arrange
    user = create_test_owner()
    template = create_test_template(
        user,
        is_active=True,
        tasks_count=1,
    )
    create_test_workflow(user, template=template)
    create_test_workflow(
        user=user,
        template=template,
        status=WorkflowStatus.DONE,
    )
    delayed_workflow = create_test_workflow(
        user=user,
        template=template,
        status=WorkflowStatus.DELAYED,
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/workflows/fields',
        data={
            'status': WorkflowApiStatus.DELAYED,
        },
    )

    # assert
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == delayed_workflow.id


def test_fields__filter_by_status_done__ok(api_client):

    # arrange
    user = create_test_owner()
    template = create_test_template(
        user,
        is_active=True,
        tasks_count=1,
    )
    create_test_workflow(user, template=template)
    done_workflow = create_test_workflow(
        user=user,
        template=template,
        status=WorkflowStatus.DONE,
    )
    create_test_workflow(
        user=user,
        template=template,
        status=WorkflowStatus.DELAYED,
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/workflows/fields',
        data={
            'status': WorkflowApiStatus.DONE,
        },
    )

    # assert
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == done_workflow.id


def test_fields__filter_by_invalid_status__validation__error(api_client):

    # arrange
    user = create_test_owner()
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/workflows/fields',
        data={
            'status': 'non-existing-status',
        },
    )

    # assert
    assert response.status_code == 400
    message = '"non-existing-status" is not a valid choice.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'status'


def test_fields__filter_by_fields__ok(api_client):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    field = TaskField.objects.create(
        order=1,
        type=FieldType.TEXT,
        name='text',
        task=task,
        value='text',
        api_name='field-1',
        workflow=workflow,
    )
    TaskField.objects.create(
        order=2,
        type=FieldType.TEXT,
        name='text 2',
        task=task,
        value='text 2',
        api_name='field-2',
        workflow=workflow,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/workflows/fields',
        data={
            'fields': [field.api_name],
        },
    )

    # assert
    assert response.status_code == 200
    data = response.data['results']
    assert len(data) == 1
    assert data[0]['id'] == workflow.id
    fields_data = data[0]['fields']
    assert len(fields_data) == 1
    assert fields_data[0]['id'] == field.id


def test_fields__filter_by_multiple_fields__ok(api_client):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.tasks.get(number=1)
    field = TaskField.objects.create(
        order=1,
        type=FieldType.TEXT,
        name='text',
        kickoff=workflow.kickoff_instance,
        value='text',
        api_name='field-1',
        workflow=workflow,
    )
    field_2 = TaskField.objects.create(
        order=2,
        type=FieldType.STRING,
        name='text 2',
        task=task_1,
        value='text 2',
        api_name='field-2',
        workflow=workflow,
    )
    TaskField.objects.create(
        order=2,
        type=FieldType.TEXT,
        name='text 2',
        task=task_1,
        value='text 2',
        api_name='field-non-selected',
        workflow=workflow,
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/workflows/fields',
        data={
            'fields': (
                f'{field.api_name},'
                f'{field_2.api_name}'
            ),
        },
    )

    # assert
    assert response.status_code == 200
    assert response.status_code == 200
    data = response.data['results']
    assert len(data) == 1
    assert data[0]['id'] == workflow.id

    fields_data = data[0]['fields']
    assert len(fields_data) == 2
    assert fields_data[0]['id'] == field_2.id
    assert fields_data[0]['task_id'] == task_1.id
    assert fields_data[1]['id'] == field.id
    assert fields_data[1]['kickoff_id'] == workflow.kickoff_instance.id


def test_fields__multiple_workflows_and_multiple_fields__ok(api_client):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user, tasks_count=2)
    field = TaskField.objects.create(
        order=1,
        type=FieldType.TEXT,
        name='text',
        kickoff=workflow.kickoff_instance,
        value='text',
        api_name='field-1',
        workflow=workflow,
    )
    workflow_2 = create_test_workflow(user, tasks_count=2)
    field_2 = TaskField.objects.create(
        order=2,
        type=FieldType.STRING,
        name='text 2',
        kickoff=workflow_2.kickoff_instance,
        value='text 2',
        api_name='field-2',
        workflow=workflow_2,
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/workflows/fields',
        data={
            'fields': (
                f'{field.api_name},'
                f'{field_2.api_name}'
            ),
        },
    )

    # assert
    assert response.status_code == 200
    data = response.data['results']
    assert len(data) == 2
    assert data[0]['id'] == workflow_2.id
    fields_data = data[0]['fields']
    assert len(fields_data) == 1
    assert fields_data[0]['id'] == field_2.id

    assert data[1]['id'] == workflow.id
    fields_data = data[1]['fields']
    assert len(fields_data) == 1
    assert fields_data[0]['id'] == field.id


def test_fields__filter_by_invalid_fields__ok(api_client):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    TaskField.objects.create(
        order=1,
        type=FieldType.TEXT,
        name='text',
        task=task,
        value='text',
        api_name='field-1',
        workflow=workflow,
    )
    TaskField.objects.create(
        order=2,
        type=FieldType.TEXT,
        name='text 2',
        task=task,
        value='text 2',
        api_name='field-2',
        workflow=workflow,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/workflows/fields',
        data={
            'fields': 'field-non-existing',
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    data = response.data['results'][0]
    assert data['id'] == workflow.id
    assert len(data['fields']) == 0


def test_fields__pagination__ok(api_client):

    # arrange
    user = create_test_owner()
    create_test_workflow(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, tasks_count=1)
    create_test_workflow(user=user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/workflows/fields',
        data={
            'limit': 1,
            'offset': 1,
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    data = response.data['results'][0]
    assert data['id'] == workflow.id


def test_fields__user_admin__permission_denied(api_client):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_admin(account=account)
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/workflows/fields')

    # assert
    assert response.status_code == 403


def test_fields__user_not_admin__permission_denied(api_client):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/workflows/fields')

    # assert
    assert response.status_code == 403


def test_fields__user_guest__permission_denied(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(owner, tasks_count=1)
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id,
    )

    # act
    response = api_client.get(
        '/workflows/fields',
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 403


def test_fields__public_auth__permission_denied(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        is_public=True,
        tasks_count=1,
    )
    token = f'Token {template.public_id}'
    create_test_workflow(owner, template=template)

    # act
    response = api_client.get(
        '/workflows/fields',
        **{'X-Public-Authorization': token},
    )

    # assert
    assert response.status_code == 403


def test_fields__not_auth__not_authenticated(api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    create_test_workflow(user, tasks_count=1)

    # act
    response = api_client.get('/workflows/fields')

    # assert
    assert response.status_code == 401
