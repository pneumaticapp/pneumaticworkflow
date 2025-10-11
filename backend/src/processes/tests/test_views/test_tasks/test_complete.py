import pytest
from src.processes.models import (
    TaskPerformer,
)
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_guest,
    create_test_workflow,
    create_test_account,
    create_test_group,
    create_test_owner,
    create_test_admin,
)
from src.processes.enums import (
    PerformerType,
    TaskStatus,
)
from src.authentication.services import GuestJWTAuthService
from src.authentication.enums import AuthTokenType
from src.processes.services.workflow_action import (
    WorkflowActionService,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_complete__response_body__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    complete_task_for_user_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_task_for_user',
        return_value=task,
    )
    check_delay_workflow_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'check_delay_workflow',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/complete',
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == task.id
    assert response.data['name'] == task.name
    assert response.data['api_name'] == task.api_name
    assert response.data['description'] == task.description
    assert response.data['is_urgent'] is False
    assert response.data['date_started_tsp'] == (
        task.date_started.timestamp()
    )
    assert response.data['date_completed_tsp'] is None
    assert response.data['due_date_tsp'] is None
    assert response.data['delay'] is None
    assert response.data['sub_workflows'] == []
    assert response.data['checklists'] == []
    assert response.data['status'] == TaskStatus.ACTIVE

    workflow_data = response.data['workflow']
    assert workflow_data['id'] == workflow.id
    assert workflow_data['name'] == workflow.name
    assert workflow_data['status'] == workflow.status
    assert workflow_data['template_name'] == workflow.get_template_name()
    assert workflow_data['date_completed_tsp'] is None
    service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=owner,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    complete_task_for_user_mock.assert_called_once_with(
        task=task,
        fields_values=None,
    )
    check_delay_workflow_mock.assert_called_once()


def test_complete__account_owner_not_performer__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    complete_task_for_user_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_task_for_user',
        return_value=task,
    )
    check_delay_workflow_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'check_delay_workflow',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/complete',
    )

    # assert
    assert response.status_code == 200
    service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=owner,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    complete_task_for_user_mock.assert_called_once_with(
        task=task,
        fields_values=None,
    )
    check_delay_workflow_mock.assert_called_once()


def test_complete__group_performer__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(owner, tasks_count=1)
    performer = create_test_admin(
        account=account,
        email='test@test.test',
    )
    group = create_test_group(account, users=[performer])
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
    )
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    complete_task_for_user_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_task_for_user',
        return_value=task,
    )
    check_delay_workflow_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'check_delay_workflow',
    )
    api_client.token_authenticate(performer)

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/complete',
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == task.id
    service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=performer,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    complete_task_for_user_mock.assert_called_once_with(
        task=task,
        fields_values=None,
    )
    check_delay_workflow_mock.assert_called_once()


def test_complete__user_performer__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    performer = create_test_admin(
        account=account,
        email='test@test.test',
    )
    task.performers.add(performer)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    complete_task_by_user_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_task_for_user',
        return_value=task,
    )
    check_delay_workflow_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'check_delay_workflow',
    )
    api_client.token_authenticate(performer)
    task = workflow.tasks.get(number=1)

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/complete',
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == task.id
    service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=performer,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    complete_task_by_user_mock.assert_called_once_with(
        task=task,
        fields_values=None,
    )
    check_delay_workflow_mock.assert_called_once()


def test_complete__guest__ok(
    mocker,
    api_client,
):
    # arrange
    account = create_test_account()
    account_owner = create_test_user(account=account)
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
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
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    complete_task_for_user_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_task_for_user',
        return_value=task,
    )
    check_delay_workflow_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'check_delay_workflow',
    )

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/complete',
        **{'X-Guest-Authorization': str_token},

    )
    # assert
    assert response.status_code == 200
    assert response.data['id'] == task.id
    service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=guest,
        auth_type=AuthTokenType.GUEST,
        is_superuser=False,
    )
    complete_task_for_user_mock.assert_called_once_with(
        task=task,
        fields_values=None,
    )
    check_delay_workflow_mock.assert_called_once()


def test_complete__user_not_performer__permission_denied(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    user = create_test_admin(account=account)
    workflow.members.add(user)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    complete_task_by_user_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_task_for_user',
        return_value=task,
    )
    check_delay_workflow_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'check_delay_workflow',
    )
    api_client.token_authenticate(user)
    task = workflow.tasks.get(number=1)

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/complete',
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    complete_task_by_user_mock.assert_not_called()
    check_delay_workflow_mock.assert_not_called()


def test_complete__not_authorized__permission_denied(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    complete_task_for_user_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_task_for_user',
        return_value=task,
    )
    check_delay_workflow_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'check_delay_workflow',
    )

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/complete',
    )

    # assert
    assert response.status_code == 401
    service_init_mock.assert_not_called()
    complete_task_for_user_mock.assert_not_called()
    check_delay_workflow_mock.assert_not_called()


def test_complete__fields_values__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    performer = create_test_admin(
        account=account,
        email='test@test.test',
    )
    task.performers.add(performer)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    complete_task_by_user_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_task_for_user',
        return_value=task,
    )
    check_delay_workflow_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'check_delay_workflow',
    )
    fields_data = {
        'field_1': 'value_1',
        'field_2': 2,
    }
    api_client.token_authenticate(performer)
    task = workflow.tasks.get(number=1)

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/complete',
        data={
            'output': fields_data,
        },
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == task.id
    service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=performer,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    complete_task_by_user_mock.assert_called_once_with(
        task=task,
        fields_values=fields_data,
    )
    check_delay_workflow_mock.assert_called_once()


def test_complete__empty_fields_data__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    performer = create_test_admin(
        account=account,
        email='test@test.test',
    )
    task.performers.add(performer)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    complete_task_by_user_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_task_for_user',
        return_value=task,
    )
    check_delay_workflow_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'check_delay_workflow',
    )
    api_client.token_authenticate(performer)
    task = workflow.tasks.get(number=1)

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/complete',
        data={
            'output': {},
        },
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == task.id
    service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=performer,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    complete_task_by_user_mock.assert_called_once_with(
        task=task,
        fields_values={},
    )
    check_delay_workflow_mock.assert_called_once()


def test_complete__guest_another_workflow__permission_denied(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(account=account)
    workflow_1 = create_test_workflow(account_owner, tasks_count=1)
    task_1 = workflow_1.tasks.get(number=1)
    guest_1 = create_test_guest(account=account)
    TaskPerformer.objects.create(
        task_id=task_1.id,
        user_id=guest_1.id,
    )
    GuestJWTAuthService.get_str_token(
        task_id=task_1.id,
        user_id=guest_1.id,
        account_id=account.id,
    )

    workflow_2 = create_test_workflow(account_owner, tasks_count=1)
    task_2 = workflow_2.tasks.get(number=1)
    guest_2 = create_test_guest(
        account=account,
        email='guest2@test.test',
    )
    TaskPerformer.objects.create(
        task_id=task_2.id,
        user_id=guest_2.id,
    )
    str_token_2 = GuestJWTAuthService.get_str_token(
        task_id=task_2.id,
        user_id=guest_2.id,
        account_id=account.id,
    )
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    complete_task_for_user_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_task_for_user',
    )
    check_delay_workflow_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'check_delay_workflow',
    )

    # act
    response = api_client.post(
        f'/v2/tasks/{task_1.id}/complete',
        **{'X-Guest-Authorization': str_token_2},
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    complete_task_for_user_mock.assert_not_called()
    check_delay_workflow_mock.assert_not_called()


def test_complete__guest_another_workflow_task__permission_denied(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        account_owner,
        tasks_count=2,
        active_task_number=2,
    )
    task_1 = workflow.tasks.get(number=1)
    guest_1 = create_test_guest(account=account)
    TaskPerformer.objects.create(
        task_id=task_1.id,
        user_id=guest_1.id,
    )
    GuestJWTAuthService.get_str_token(
        task_id=task_1.id,
        user_id=guest_1.id,
        account_id=account.id,
    )

    task_2 = workflow.tasks.get(number=2)
    guest_2 = create_test_guest(
        account=account,
        email='guest2@test.test',
    )
    TaskPerformer.objects.create(
        task_id=task_2.id,
        user_id=guest_2.id,
    )
    str_token_2 = GuestJWTAuthService.get_str_token(
        task_id=task_2.id,
        user_id=guest_2.id,
        account_id=account.id,
    )
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    complete_task_for_user_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_task_for_user',
    )
    check_delay_workflow_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'check_delay_workflow',
    )

    # act
    response = api_client.post(
        f'/v2/tasks/{task_1.id}/complete',
        **{'X-Guest-Authorization': str_token_2},
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    complete_task_for_user_mock.assert_not_called()
    check_delay_workflow_mock.assert_not_called()


@pytest.mark.parametrize(
    'output',
    (
        ([], 'Expected a dictionary of items but got type "list".'),
        ('null', 'Expected a dictionary of items but got type "str".'),
        (123, 'Expected a dictionary of items but got type "int".'),
    ),
)
def test_complete__invalid_output__validation_error(
    mocker,
    api_client,
    output,
):

    # arrange
    output, message = output
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    complete_task_by_user_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_task_for_user',
        return_value=task,
    )
    check_delay_workflow_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'check_delay_workflow',
    )
    api_client.token_authenticate(owner)
    task = workflow.tasks.get(number=1)

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/complete',
        data={
            'output': output,
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    service_init_mock.assert_not_called()
    complete_task_by_user_mock.assert_not_called()
    check_delay_workflow_mock.assert_not_called()
