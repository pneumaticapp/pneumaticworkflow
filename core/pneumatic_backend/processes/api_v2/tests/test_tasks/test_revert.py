import pytest
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.models import (
    TaskPerformer,
)
from pneumatic_backend.processes.services.exceptions import (
    WorkflowActionServiceException
)
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_workflow,
    create_test_account,
    create_test_guest,
    create_test_owner,
    create_test_not_admin,
)
from pneumatic_backend.authentication.services import GuestJWTAuthService
from pneumatic_backend.processes.messages import workflow as messages
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.enums import (
    DirectlyStatus
)


pytestmark = pytest.mark.django_db


def test_revert__account_owner__ok(
    api_client,
    mocker,
):
    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=2,
        active_task_number=2
    )
    task_2 = workflow.tasks.get(number=2)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    service_revert_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.revert'
    )
    api_client.token_authenticate(owner)
    text_comment = 'text_comment'

    # act
    response = api_client.post(
        f'/v2/tasks/{task_2.id}/revert',
        data={
            'comment': text_comment,
        }
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=owner,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    service_revert_mock.assert_called_once_with(
        revert_from_task=task_2,
        comment=text_comment
    )


def test_revert__user_performer__ok(
    api_client,
    mocker,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=owner,
        tasks_count=2,
        active_task_number=2
    )
    task_2 = workflow.tasks.get(number=2)
    performer = create_test_not_admin(account=account)
    TaskPerformer.objects.create(
        task_id=task_2.id,
        user_id=performer.id
    )
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    service_revert_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.revert'
    )
    api_client.token_authenticate(performer)
    text_comment = 'text_comment'

    # act
    response = api_client.post(
        f'/v2/tasks/{task_2.id}/revert',
        data={
            'comment': text_comment,
        }
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=performer,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    service_revert_mock.assert_called_once_with(
        revert_from_task=task_2,
        comment=text_comment
    )


def test_revert__deleted_performer__permission_denied(
    api_client,
    mocker,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=owner,
        tasks_count=2,
        active_task_number=2
    )
    task_2 = workflow.tasks.get(number=2)
    performer = create_test_not_admin(account=account)
    TaskPerformer.objects.create(
        task_id=task_2.id,
        user_id=performer.id,
        directly_status=DirectlyStatus.DELETED
    )
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    service_revert_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.revert'
    )
    api_client.token_authenticate(performer)
    text_comment = 'text_comment'

    # act
    response = api_client.post(
        f'/v2/tasks/{task_2.id}/revert',
        data={
            'comment': text_comment,
        }
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    service_revert_mock.assert_not_called()


def test_revert__user_not_performer__permission_denied(
    api_client,
    mocker,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=owner,
        tasks_count=2,
        active_task_number=2
    )
    task_2 = workflow.tasks.get(number=2)
    performer = create_test_not_admin(account=account)
    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    service_revert_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.revert'
    )
    api_client.token_authenticate(performer)
    text_comment = 'text_comment'

    # act
    response = api_client.post(
        f'/v2/tasks/{task_2.id}/revert',
        data={
            'comment': text_comment,
        }
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    service_revert_mock.assert_not_called()


def test_revert__guest_performer__permission_denied(
    mocker,
    api_client,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        owner,
        tasks_count=2,
        active_task_number=2
    )
    task_2 = workflow.tasks.get(number=2)

    guest = create_test_guest(account=account)
    TaskPerformer.objects.create(
        task_id=task_2.id,
        user_id=guest.id
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task_2.id,
        user_id=guest.id,
        account_id=account.id
    )
    service_revert_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.revert'
    )
    text_comment = 'text_comment'

    # act
    response = api_client.post(
        path=f'/v2/tasks/{task_2.id}/revert',
        data={
            'comment': text_comment,
        },
        **{'X-Guest-Authorization': str_token}
    )

    # assert
    assert response.status_code == 403
    service_revert_mock.assert_not_called()


def test_revert__service_exception__validation_error(
    api_client,
    mocker,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        owner,
        tasks_count=2,
        active_task_number=2
    )
    task_2 = workflow.tasks.get(number=2)

    service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    message = 'Some message'
    ex = WorkflowActionServiceException(message)
    service_revert_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.revert',
        side_effect=ex,
    )
    api_client.token_authenticate(owner)
    text_comment = 'text_comment'

    # act
    response = api_client.post(
        path=f'/v2/tasks/{task_2.id}/revert',
        data={
            'comment': text_comment,
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=owner,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    service_revert_mock.assert_called_once_with(
        revert_from_task=task_2,
        comment=text_comment
    )


@pytest.mark.parametrize('text_comment', ('', '   '))
def test_revert__invalid_comment__validation_error(
    api_client,
    mocker,
    text_comment
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        owner,
        tasks_count=2,
        active_task_number=2
    )
    task_2 = workflow.tasks.get(number=2)
    service_init_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService'
    )
    service_revert_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.revert'
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        path=f'/v2/tasks/{task_2.id}/revert',
        data={
            'comment': text_comment,
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == messages.MSG_PW_0083
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    service_init_mock.assert_not_called()
    service_revert_mock.assert_not_called()
