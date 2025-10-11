import pytest
from src.processes.services.exceptions import (
    CommentServiceException,
)
from src.processes.services.events import (
    WorkflowEventService,
    CommentService,
)
from src.processes.models import (
    TaskPerformer,
)
from src.processes.enums import (
    CommentStatus,
)
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_test_guest,
    create_test_account,
)
from src.authentication.services import GuestJWTAuthService
from src.authentication.enums import AuthTokenType
from src.utils.validation import ErrorCode


pytestmark = pytest.mark.django_db


def test_destroy__account_owner__permission_denied(api_client, mocker):

    # arrange
    owner = create_test_user(is_account_owner=True)
    user = create_test_user(
        is_account_owner=False,
        email='user@test.test',
        account=owner.account,
    )
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.comment_created_event(
        text='Some comment',
        task=task,
        user=user,
        after_create_actions=False,
    )

    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None,
    )
    comment_delete_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.delete',
        return_value=event,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.delete(f'/workflows/comments/{event.id}')

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    comment_delete_mock.assert_not_called()


def test_destroy__author__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.comment_created_event(
        text='Some comment',
        task=task,
        user=user,
        after_create_actions=False,
    )

    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None,
    )
    comment_delete_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.delete',
        return_value=event,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.delete(f'/workflows/comments/{event.id}')

    # assert
    assert response.status_code == 200
    assert response.data['id'] == event.id
    assert response.data['created'] is not None
    assert response.data['updated'] is None
    assert response.data['status'] == CommentStatus.CREATED
    assert response.data['task']['id'] == task.id
    assert response.data['text'] == event.text
    assert response.data['type'] == event.type
    assert response.data['user_id'] == user.id
    assert response.data['target_user_id'] is None
    assert response.data['delay'] is None
    service_init_mock.assert_called_once_with(
        instance=event,
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    comment_delete_mock.assert_called_once()


def test_destroy__admin__ok(api_client, mocker):

    # arrange
    owner = create_test_user(is_account_owner=True)
    user = create_test_user(
        account=owner.account,
        email='admin@test.test',
        is_account_owner=False,
        is_admin=True,
    )
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.comment_created_event(
        text='Some comment',
        task=task,
        user=user,
        after_create_actions=False,
    )

    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None,
    )
    comment_delete_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.delete',
        return_value=event,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.delete(f'/workflows/comments/{event.id}')

    # assert
    assert response.status_code == 200
    assert response.data['id'] == event.id
    assert response.data['created'] is not None
    assert response.data['updated'] is None
    assert response.data['status'] == CommentStatus.CREATED
    assert response.data['task']['id'] == task.id
    assert response.data['text'] == event.text
    assert response.data['type'] == event.type
    assert response.data['user_id'] == user.id
    assert response.data['target_user_id'] is None
    assert response.data['delay'] is None
    service_init_mock.assert_called_once_with(
        instance=event,
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    comment_delete_mock.assert_called_once()


def test_destroy__not_admin__ok(api_client, mocker):

    # arrange
    owner = create_test_user(is_account_owner=True)
    user = create_test_user(
        account=owner.account,
        email='not-admin@test.test',
        is_account_owner=False,
        is_admin=False,
    )
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.comment_created_event(
        text='Some comment',
        task=task,
        user=user,
        after_create_actions=False,
    )

    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None,
    )
    comment_delete_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.delete',
        return_value=event,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.delete(f'/workflows/comments/{event.id}')

    # assert
    assert response.status_code == 200
    assert response.data['id'] == event.id
    assert response.data['created'] is not None
    assert response.data['updated'] is None
    assert response.data['status'] == CommentStatus.CREATED
    assert response.data['task']['id'] == task.id
    assert response.data['text'] == event.text
    assert response.data['type'] == event.type
    assert response.data['user_id'] == user.id
    assert response.data['target_user_id'] is None
    assert response.data['delay'] is None
    service_init_mock.assert_called_once_with(
        instance=event,
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    comment_delete_mock.assert_called_once()


def test_destroy__guest__ok(mocker, api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        account=account,
        email='owner@test.test',
        is_account_owner=True,
    )
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
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.comment_created_event(
        user=guest,
        text='Some comment',
        task=task,
        after_create_actions=False,
    )
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None,
    )
    comment_delete_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.delete',
        return_value=event,
    )

    # act
    response = api_client.delete(
        f'/workflows/comments/{event.id}',
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 200
    service_init_mock.assert_called_once_with(
        instance=event,
        user=guest,
        auth_type=AuthTokenType.GUEST,
        is_superuser=False,
    )
    comment_delete_mock.assert_called_once()


def test_destroy__service_exception__validation_error(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.comment_created_event(
        text='Some comment',
        task=task,
        user=user,
        after_create_actions=False,
    )
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None,
    )
    message = 'some message'
    comment_delete_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.delete',
        side_effect=CommentServiceException(message),
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.delete(f'/workflows/comments/{event.id}')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    service_init_mock.assert_called_once_with(
        instance=event,
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    comment_delete_mock.assert_called_once()


def test_destroy__another_user_comment__permission_denied(api_client, mocker):

    # arrange
    owner = create_test_user(is_account_owner=True)
    user = create_test_user(
        account=owner.account,
        email='admin@test.test',
        is_account_owner=False,
        is_admin=True,
    )
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.comment_created_event(
        text='Some comment',
        task=task,
        user=owner,
        after_create_actions=False,
    )

    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None,
    )
    comment_delete_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.delete',
        return_value=event,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.delete(f'/workflows/comments/{event.id}')

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    comment_delete_mock.assert_not_called()


def test_destroy__not_comment__permission_denied(api_client, mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.task_started_event(task=task)

    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None,
    )
    comment_delete_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.delete',
        return_value=event,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.delete(f'/workflows/comments/{event.id}')

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    comment_delete_mock.assert_not_called()
