from datetime import timedelta

import pytest
from django.utils import timezone

from src.accounts.enums import BillingPlanType

from src.authentication.enums import AuthTokenType
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.processes.enums import (
    DirectlyStatus,
    PerformerType,
)
from src.processes.messages import workflow as messages
from src.processes.models.workflows.task import TaskPerformer
from src.processes.services.exceptions import (
    WorkflowActionServiceException,
)
from src.processes.services.workflow_action import (
    WorkflowActionService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_guest,
    create_test_not_admin,
    create_test_owner,
    create_test_user,
    create_test_workflow,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


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
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_api_name': task.api_name,
        },
    )

    # assert
    assert response.status_code == 204
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


def test_complete__user_performer__ok(
    mocker,
    api_client,
):
    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.first()
    user = create_test_user(account=account)
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=user.id,
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
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_api_name': task.api_name,
        },
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    complete_task_for_user_mock.assert_called_once_with(
        task=task,
        fields_values=None,
    )


def test_complete__user_not_performer__call_service(
    mocker,
    api_client,
):
    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.first()
    user = create_test_user(account=account)

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
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_api_name': task.api_name,
        },
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    complete_task_for_user_mock.assert_called_once_with(
        task=task,
        fields_values=None,
    )


def test_complete__guest__ok(
    mocker,
    api_client,
):
    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
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
    )

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_api_name': task.api_name,
        },
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 204
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


def test_complete__task_id__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user, tasks_count=1)
    performer = create_test_user(
        account=account,
        email='test@test.test',
        is_account_owner=False,
    )
    task = workflow.tasks.get(number=1)
    task.performers.add(performer)
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
    api_client.token_authenticate(performer)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_id': task.id,
        },
    )

    # assert
    assert response.status_code == 204
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


def test_complete__task_performer_is_group__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    performer = create_test_user(
        account=account,
        email='test@test.test',
        is_account_owner=False,
    )
    group = create_test_group(account, users=[performer])
    workflow = create_test_workflow(owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
        directly_status=DirectlyStatus.CREATED,
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
    api_client.token_authenticate(performer)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_api_name': task.api_name,
        },
    )

    # assert
    assert response.status_code == 204
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


def test_complete__task_api_name__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    performer = create_test_user(
        account=account,
        email='test@test.test',
        is_account_owner=False,
    )
    workflow = create_test_workflow(owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.performers.add(performer)
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
    api_client.token_authenticate(performer)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_api_name': task.api_name,
        },
    )

    # assert
    assert response.status_code == 204
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


def test_complete__fields_values__ok(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    performer = create_test_user(
        account=account,
        email='test@test.test',
        is_account_owner=False,
    )
    workflow = create_test_workflow(owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
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
    )
    fields_data = {
        'field_1': 'value_1',
        'field_2': 2,
    }
    api_client.token_authenticate(performer)
    task = workflow.tasks.get(number=1)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_api_name': task.api_name,
            'output': fields_data,
        },
    )

    # assert
    assert response.status_code == 204
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


def test_complete__empty_fields_data__ok(
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
    complete_task_by_user_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_task_for_user',
        return_value=task,
    )
    api_client.token_authenticate(owner)
    task = workflow.tasks.get(number=1)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_api_name': task.api_name,
            'output': {},
        },
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=owner,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    complete_task_by_user_mock.assert_called_once_with(
        task=task,
        fields_values={},
    )


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
    api_client.token_authenticate(owner)
    task = workflow.tasks.get(number=1)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_api_name': task.api_name,
            'output': output,
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    service_init_mock.assert_not_called()
    complete_task_by_user_mock.assert_not_called()


def test_complete__not_active_task__validation_error(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user, tasks_count=2)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    task = workflow.tasks.get(number=2)
    complete_task_for_user_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_task_for_user',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_api_name': task.api_name,
            'task_id': task.id,
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PW_0086
    service_init_mock.assert_not_called()
    complete_task_for_user_mock.assert_not_called()


def test_complete__guest_another_workflow__permission_denied(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
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

    # act
    response = api_client.post(
        f'/workflows/{workflow_1.id}/task-complete',
        data={
            'task_api_name': task_1.api_name,
        },
        **{'X-Guest-Authorization': str_token_2},
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    complete_task_for_user_mock.assert_not_called()


def test_complete__guest_another_workflow_task__permission_denied(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=account_owner,
        tasks_count=2,
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

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': task_1.id},
        **{'X-Guest-Authorization': str_token_2},
    )

    # assert
    assert response.status_code == 401
    service_init_mock.assert_not_called()
    complete_task_for_user_mock.assert_not_called()


def test_complete__not_authenticated__permission_denied(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': task.id},
    )

    # assert
    assert response.status_code == 401


def test_complete__expired_subscription__permission_denied(api_client):

    # arrange
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() - timedelta(hours=1),
    )
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': task.id},
    )

    # assert
    assert response.status_code == 403


def test_complete__billing_plan__permission_denied(api_client):

    # arrange
    account = create_test_account(plan=None)
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': task.id},
    )
    # assert
    assert response.status_code == 403


def test_complete__users_overlimited__permission_denied(api_client):

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        max_users=1,
    )
    owner = create_test_owner(account=account)
    create_test_not_admin(account=account)
    account.active_users = 2
    account.save()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': task.id},
    )

    # assert
    assert response.status_code == 403


def test_complete__not_found__not_found(api_client):

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/workflows/99999999/task-complete',
        data={'task_api_name': 'some-task'},
    )

    # assert
    assert response.status_code == 404


def test_complete__no_task_id_no_api_name__validation_error(api_client):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PW_0076


def test_complete__task_not_found__validation_error(api_client):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_api_name': 'non-existent-task-api-name'},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PW_0077


def test_complete__service_exception__validation_error(mocker, api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    message = 'Service error occurred'
    ex = WorkflowActionServiceException(message)
    complete_task_for_user_mock = mocker.patch(
        'src.processes.services.'
        'workflow_action.WorkflowActionService.'
        'complete_task_for_user',
        side_effect=ex,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': task.id},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    service_init_mock.assert_called_once()
    complete_task_for_user_mock.assert_called_once()
