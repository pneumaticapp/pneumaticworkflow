from datetime import timedelta

import pytest
from django.utils import timezone

from src.authentication.enums import AuthTokenType
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.processes.enums import (
    CommentStatus,
)
from src.processes.models.workflows.task import TaskPerformer
from src.processes.services.events import (
    CommentService,
    WorkflowEventService,
)
from src.processes.services.exceptions import (
    CommentServiceException,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_attachment,
    create_test_guest,
    create_test_user,
    create_test_workflow,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db
datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'


def test_update__author__only_text__ok(api_client, mocker):

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
    comment_update_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.update',
        return_value=event,
    )
    api_client.token_authenticate(owner)
    new_text = 'New comment text'

    # act
    response = api_client.patch(
        f'/workflows/comments/{event.id}',
        data={'text': new_text},
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    comment_update_mock.assert_not_called()


def test_update_text_and_attachment__ok(mocker, api_client):

    # assert
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    comment_text = (
        'Some comment with files: '
        '[first_file.txt]'
        '(https://files.example.com/files/first_template_file) and '
        '[first_file2.txt]'
        '(https://files.example.com/files/first_template_file2)'
    )
    event = WorkflowEventService.comment_created_event(
        user=user,
        text=comment_text,
        task=task,
        after_create_actions=False,
    )
    create_test_attachment(
        account=user.account,
        file_id='task_file_1',
        workflow=workflow,
        event=event,
    )
    create_test_attachment(
        account=user.account,
        file_id='task_file_2',
        workflow=workflow,
        event=event,
    )
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None,
    )
    comment_update_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.update',
        return_value=event,
    )
    api_client.token_authenticate(user)
    new_text = 'New comment text'

    # act
    response = api_client.patch(
        f'/workflows/comments/{event.id}',
        data={
            'text': new_text,
        },
    )

    # arrange
    assert response.status_code == 200
    service_init_mock.assert_called_once_with(
        instance=event,
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    comment_update_mock.assert_called_once_with(
        text=new_text,
        force_save=True,
    )


def test_update__admin__ok(api_client, mocker):

    # arrange
    owner = create_test_user(is_account_owner=True)
    user = create_test_user(
        account=owner.account,
        email='admin@test.test',
        is_account_owner=False,
        is_admin=True,
    )
    workflow = create_test_workflow(owner)
    task = workflow.tasks.get(number=1)
    task.performers.add(user)
    workflow.members.add(user)
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.comment_created_event(
        text='Some comment',
        task=task,
        user=user,
        after_create_actions=False,
    )
    event.updated = timezone.now() + timedelta(hours=1)
    event.save()
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None,
    )
    comment_update_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.update',
        return_value=event,
    )
    api_client.token_authenticate(user)
    new_text = 'New comment text'

    # act
    response = api_client.patch(
        f'/workflows/comments/{event.id}',
        data={'text': new_text},
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == event.id
    assert response.data['created'] == event.created.strftime(datetime_format)
    assert response.data['created_tsp'] == event.created.timestamp()
    assert response.data['updated'] == event.updated.strftime(datetime_format)
    assert response.data['updated_tsp'] == event.updated.timestamp()
    assert response.data['status'] == CommentStatus.CREATED
    assert response.data['task']['id'] == task.id
    assert response.data['task']['due_date_tsp'] is None
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
    comment_update_mock.assert_called_once_with(
        text=new_text,
        force_save=True,
    )


def test_update__not_admin__ok(api_client, mocker):

    # arrange
    owner = create_test_user(is_account_owner=True)
    user = create_test_user(
        account=owner.account,
        email='admin@test.test',
        is_account_owner=False,
        is_admin=False,
    )
    workflow = create_test_workflow(owner)
    task = workflow.tasks.get(number=1)
    task.performers.add(user)
    workflow.members.add(user)
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.comment_created_event(
        text='Some comment',
        task=task,
        user=user,
        after_create_actions=False,
    )
    event.updated = timezone.now() + timedelta(hours=1)
    event.save()
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None,
    )
    comment_update_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.update',
        return_value=event,
    )
    api_client.token_authenticate(user)
    new_text = 'New comment text'

    # act
    response = api_client.patch(
        f'/workflows/comments/{event.id}',
        data={'text': new_text},
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == event.id
    assert response.data['created'] == event.created.strftime(datetime_format)
    assert response.data['created_tsp'] == event.created.timestamp()
    assert response.data['updated'] == event.updated.strftime(datetime_format)
    assert response.data['updated_tsp'] == event.updated.timestamp()
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
    comment_update_mock.assert_called_once_with(
        text=new_text,
        force_save=True,
    )


def test_update__guest__ok(mocker, api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        account=account,
        email='owner@test.test',
        is_account_owner=True,
    )
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id,
    )
    event = WorkflowEventService.comment_created_event(
        user=guest,
        text='Some comment',
        task=task,
        after_create_actions=False,
    )
    event.updated = timezone.now() + timedelta(hours=1)
    event.save()
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None,
    )
    comment_update_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.update',
        return_value=event,
    )
    new_text = 'New comment text'

    # act
    response = api_client.patch(
        f'/workflows/comments/{event.id}',
        data={'text': new_text},
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == event.id
    assert response.data['created'] == event.created.strftime(datetime_format)
    assert response.data['created_tsp'] == event.created.timestamp()
    assert response.data['updated'] == event.updated.strftime(datetime_format)
    assert response.data['updated_tsp'] == event.updated.timestamp()
    assert response.data['status'] == CommentStatus.CREATED
    assert response.data['task']['id'] == task.id
    assert response.data['text'] == event.text
    assert response.data['type'] == event.type
    assert response.data['user_id'] == guest.id
    assert response.data['target_user_id'] is None
    assert response.data['delay'] is None
    service_init_mock.assert_called_once_with(
        instance=event,
        user=guest,
        auth_type=AuthTokenType.GUEST,
        is_superuser=False,
    )
    comment_update_mock.assert_called_once_with(
        text=new_text,
        force_save=True,
    )


def test_update__guest_another_workflow__permission_denied(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        account=account,
        email='owner@test.test',
        is_account_owner=True,
    )
    workflow_1 = create_test_workflow(account_owner, tasks_count=1)
    task = workflow_1.tasks.get(number=1)
    event = WorkflowEventService.comment_created_event(
        text='Some comment',
        task=task,
        user=account_owner,
        after_create_actions=False,
    )
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
        CommentService,
        attribute='__init__',
        return_value=None,
    )
    comment_update_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.update',
    )

    # act
    response = api_client.patch(
        f'/workflows/comments/{event.id}',
        data={'text': 'Test text'},
        **{'X-Guest-Authorization': str_token_2},
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    comment_update_mock.assert_not_called()


def test_update__service_exception__validation_error(
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
    comment_update_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.update',
        side_effect=CommentServiceException(message),
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.patch(
        f'/workflows/comments/{event.id}',
        data={'text': 'Raise'},
    )

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
    comment_update_mock.assert_called_once_with(
        text='Raise',
        force_save=True,
    )


def test_update__another_user_comment__permission_denied(api_client, mocker):

    # arrange
    owner = create_test_user(is_account_owner=True)
    user = create_test_user(
        account=owner.account,
        email='admin@test.test',
        is_account_owner=False,
        is_admin=True,
    )
    workflow = create_test_workflow(owner)
    task = workflow.tasks.get(number=1)
    task.performers.add(user)
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
    comment_update_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.update',
        return_value=event,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.patch(
        f'/workflows/comments/{event.id}',
        data={'text': 'New comment text'},
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    comment_update_mock.assert_not_called()


def test_update__not_comment__permission_denied(api_client, mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.task_complete_event(
        user=user,
        task=task,
    )

    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None,
    )
    comment_update_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService.update',
        return_value=event,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.patch(
        f'/workflows/comments/{event.id}',
        data={'text': 'New comment text'},
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    comment_update_mock.assert_not_called()
