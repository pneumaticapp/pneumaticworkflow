import pytest
from src.processes.services.exceptions import (
    CommentServiceException
)
from src.processes.services.events import (
    WorkflowEventService,
    CommentService
)
from src.processes.models import (
    TaskPerformer,
)
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_test_guest,
    create_test_account,
    create_test_admin,
    create_test_group,
)
from src.authentication.services import GuestJWTAuthService
from src.authentication.enums import AuthTokenType
from src.utils.validation import ErrorCode
from src.processes.enums import PerformerType

pytestmark = pytest.mark.django_db


def test_watched__account_owner__ok(api_client, mocker):

    # arrange
    owner = create_test_user(is_account_owner=True)
    user = create_test_user(
        account=owner.account,
        email='member@test.test',
        is_account_owner=False,
    )
    workflow = create_test_workflow(user)
    workflow.members.remove(owner)
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.comment_created_event(
        text='Some comment',
        task=task,
        user=user,
        after_create_actions=False
    )

    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    comment_watched_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.watched'
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(f'/workflows/comments/{event.id}/watched')

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        instance=event,
        user=owner,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    comment_watched_mock.assert_called_once()
    assert not workflow.members.filter(id=owner.id).exists()


def test_watched__workflow_member__ok(api_client, mocker):

    # arrange
    owner = create_test_user(is_account_owner=True)
    user = create_test_user(
        account=owner.account,
        email='member@test.test',
        is_account_owner=False
    )
    workflow = create_test_workflow(owner)
    workflow.members.add(user)
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.comment_created_event(
        text='Some comment',
        task=task,
        user=owner,
        after_create_actions=False
    )

    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    comment_watched_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.watched'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(f'/workflows/comments/{event.id}/watched')

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        instance=event,
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    comment_watched_mock.assert_called_once()


def test_watched__user_in_group_task_performer__ok(api_client, mocker):

    # arrange
    user = create_test_user(is_account_owner=True)
    group_user = create_test_admin(
        account=user.account,
        email='group_user@test.test',
    )
    group = create_test_group(user.account, users=[group_user])
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
    )
    event = WorkflowEventService.comment_created_event(
        text='Some comment',
        task=task,
        user=user,
        after_create_actions=False
    )

    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    comment_watched_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.watched'
    )
    api_client.token_authenticate(group_user)

    # act
    response = api_client.post(f'/workflows/comments/{event.id}/watched')

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        instance=event,
        user=group_user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    comment_watched_mock.assert_called_once()


def test_watched__user_not_member__permission_denied(api_client, mocker):

    # arrange
    owner = create_test_user(is_account_owner=True)
    workflow = create_test_workflow(owner)
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.comment_created_event(
        text='Some comment',
        task=task,
        user=owner,
        after_create_actions=False
    )
    user = create_test_user(
        account=owner.account,
        email='not-member@test.test',
        is_account_owner=False,
    )
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    comment_watched_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.watched'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(f'/workflows/comments/{event.id}/watched')

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    comment_watched_mock.assert_not_called()


def test_watched__guest__ok(mocker, api_client):

    # arrange
    account = create_test_account()
    owner = create_test_user(
        account=account,
        email='owner@test.test',
        is_account_owner=True,
    )
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(owner, tasks_count=1)
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id
    )
    event = WorkflowEventService.comment_created_event(
        user=owner,
        text='Some comment',
        task=task,
        after_create_actions=False
    )
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    comment_watched_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.watched'
    )

    # act
    response = api_client.post(
        f'/workflows/comments/{event.id}/watched',
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        instance=event,
        user=guest,
        auth_type=AuthTokenType.GUEST,
        is_superuser=False
    )
    comment_watched_mock.assert_called_once()


def test_watched__another_task_guest__permission_denied(mocker, api_client):

    # arrange
    account = create_test_account()
    owner = create_test_user(
        account=account,
        email='owner@test.test',
        is_account_owner=True,
    )
    workflow = create_test_workflow(owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    guest = create_test_guest(account=account)
    workflow_2 = create_test_workflow(owner, tasks_count=1)
    task_2 = workflow_2.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task_2.id,
        user_id=guest.id
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task_2.id,
        user_id=guest.id,
        account_id=account.id
    )
    event = WorkflowEventService.comment_created_event(
        user=owner,
        text='Some comment',
        task=task,
        after_create_actions=False
    )
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    comment_watched_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.watched'
    )

    # act
    response = api_client.post(
        f'/workflows/comments/{event.id}/watched',
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    comment_watched_mock.assert_not_called()


def test_watched__not_active_task_guest__not_authentcated(
    mocker,
    api_client
):

    # arrange
    account = create_test_account()
    owner = create_test_user(
        account=account,
        email='owner@test.test',
        is_account_owner=True,
    )
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(owner, tasks_count=2)
    task = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    TaskPerformer.objects.create(
        task_id=task_2.id,
        user_id=guest.id
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task_2.id,
        user_id=guest.id,
        account_id=account.id
    )
    event = WorkflowEventService.comment_created_event(
        user=owner,
        text='Some comment',
        task=task,
        after_create_actions=False
    )
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    comment_watched_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.watched'
    )

    # act
    response = api_client.post(
        f'/workflows/comments/{event.id}/watched',
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 401
    service_init_mock.assert_not_called()
    comment_watched_mock.assert_not_called()


def test_watched__guest_another_workflow__permission_denied(
    mocker,
    api_client
):

    # arrange
    account = create_test_account()
    owner = create_test_user(
        account=account,
        email='owner@test.test',
        is_account_owner=True,
    )
    workflow_1 = create_test_workflow(owner, tasks_count=1)
    task = workflow_1.tasks.get(number=1)
    event = WorkflowEventService.comment_created_event(
        text='Some comment',
        task=task,
        user=owner,
        after_create_actions=False
    )
    task_1 = workflow_1.tasks.get(number=1)
    guest_1 = create_test_guest(account=account)
    TaskPerformer.objects.create(
        task_id=task_1.id,
        user_id=guest_1.id
    )
    GuestJWTAuthService.get_str_token(
        task_id=task_1.id,
        user_id=guest_1.id,
        account_id=account.id
    )

    workflow_2 = create_test_workflow(owner, tasks_count=1)
    task_2 = workflow_2.tasks.get(number=1)
    guest_2 = create_test_guest(
        account=account,
        email='guest2@test.test'
    )
    TaskPerformer.objects.create(
        task_id=task_2.id,
        user_id=guest_2.id
    )
    str_token_2 = GuestJWTAuthService.get_str_token(
        task_id=task_2.id,
        user_id=guest_2.id,
        account_id=account.id
    )
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    comment_watched_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.watched'
    )

    # act
    response = api_client.post(
        f'/workflows/comments/{event.id}/watched',
        **{'X-Guest-Authorization': str_token_2}
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    comment_watched_mock.assert_not_called()


def test_watched__not_comment__permission_denied(api_client, mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.task_complete_event(
        user=user,
        task=task
    )

    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    comment_watched_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.watched'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(f'/workflows/comments/{event.id}/watched')

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    comment_watched_mock.assert_not_called()


def test_watched__service_exception__validation_error(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.comment_created_event(
        text='Some comment',
        task=task,
        user=user,
        after_create_actions=False
    )
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    message = 'some message'
    comment_watched_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.watched',
        side_effect=CommentServiceException(message)
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(f'/workflows/comments/{event.id}/watched')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    service_init_mock.assert_called_once_with(
        instance=event,
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    comment_watched_mock.assert_called_once()
