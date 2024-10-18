import pytest
from datetime import timedelta
from django.utils import timezone
from pneumatic_backend.processes.api_v2.services.exceptions import (
    CommentServiceException
)
from pneumatic_backend.processes.api_v2.services import (
    WorkflowEventService,
    CommentService
)
from pneumatic_backend.processes.models import (
    FileAttachment,
    TaskPerformer,
)
from pneumatic_backend.processes.enums import (
    CommentStatus,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_test_guest,
    create_test_account,
)
from pneumatic_backend.authentication.services import GuestJWTAuthService
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.utils.validation import ErrorCode


pytestmark = pytest.mark.django_db
datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'


def test_update__author__only_text__ok(api_client, mocker):

    # arrange
    owner = create_test_user(is_account_owner=True)
    user = create_test_user(
        is_account_owner=False,
        email='user@test.test',
        account=owner.account
    )
    workflow = create_test_workflow(user)
    event = WorkflowEventService.comment_created_event(
        text='Some comment',
        workflow=workflow,
        user=user,
        after_create_actions=False
    )

    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    comment_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.'
        'CommentService.update',
        return_value=event
    )
    api_client.token_authenticate(owner)
    new_text = 'New comment text'

    # act
    response = api_client.patch(
        f'/workflows/comments/{event.id}',
        data={'text': new_text}
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    comment_update_mock.assert_not_called()


def test_update_text_and_attachment__ok(mocker, api_client):

    # assert
    user = create_test_user()
    workflow = create_test_workflow(user)
    event = WorkflowEventService.comment_created_event(
        user=user,
        text='Some comment',
        workflow=workflow,
        attachments=[1, 2],
        after_create_actions=False
    )
    attach_1 = FileAttachment.objects.create(
        account_id=user.account_id,
        name='filename.png',
        size=384812,
        url='https://cloud.google.com/bucket/filename_salt.png',
        thumbnail_url='https://cloud.google.com/bucket/filename_thumb.png',
        event=event
    )
    attach_2 = FileAttachment.objects.create(
        account_id=user.account_id,
        name='doc.docx',
        size=2412413,
        url='https://cloud.google.com/bucket/doc_salt.docx',
        event=event
    )
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    comment_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.'
        'CommentService.update',
        return_value=event
    )
    api_client.token_authenticate(user)
    new_text = 'New comment text'

    # act
    response = api_client.patch(
        f'/workflows/comments/{event.id}',
        data={
            'text': new_text,
            'attachments': [
                attach_1.id,
                attach_2.id
            ]
        }
    )

    # arrange
    assert response.status_code == 200
    assert len(response.data['attachments']) == 2
    attach_data = response.data['attachments'][0]
    assert attach_data['id'] == attach_1.id
    assert attach_data['name'] == attach_1.name
    assert attach_data['url'] == attach_1.url
    assert attach_data['thumbnail_url'] == attach_1.thumbnail_url
    assert attach_data['thumbnail_url'] == attach_1.thumbnail_url
    assert attach_data['size'] == attach_1.size

    service_init_mock.assert_called_once_with(
        instance=event,
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    comment_update_mock.assert_called_once_with(
        text=new_text,
        attachments=[attach_1.id, attach_2.id],
        force_save=True,
    )


def test_update__remove_attachment__null__ok(mocker, api_client):

    # assert
    user = create_test_user()
    workflow = create_test_workflow(user)
    event = WorkflowEventService.comment_created_event(
        user=user,
        text='Some comment',
        workflow=workflow,
        attachments=[1],
        after_create_actions=False
    )
    FileAttachment.objects.create(
        account_id=user.account_id,
        name='filename.png',
        size=384812,
        url='https://cloud.google.com/bucket/filename_salt.png',
        thumbnail_url='https://cloud.google.com/bucket/filename_thumb.png',
        event=event
    )
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    comment_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.'
        'CommentService.update',
        return_value=event
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.patch(
        f'/workflows/comments/{event.id}',
        data={
            'attachments': None
        }
    )

    # arrange
    assert response.status_code == 200
    service_init_mock.assert_called_once_with(
        instance=event,
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    comment_update_mock.assert_called_once_with(
        attachments=None,
        force_save=True,
    )


def test_update__remove_attachment__empty_list__ok(mocker, api_client):

    # assert
    user = create_test_user()
    workflow = create_test_workflow(user)
    event = WorkflowEventService.comment_created_event(
        user=user,
        text='Some comment',
        workflow=workflow,
        attachments=[1],
        after_create_actions=False
    )
    FileAttachment.objects.create(
        account_id=user.account_id,
        name='filename.png',
        size=384812,
        url='https://cloud.google.com/bucket/filename_salt.png',
        thumbnail_url='https://cloud.google.com/bucket/filename_thumb.png',
        event=event
    )
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    comment_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.'
        'CommentService.update',
        return_value=event
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.patch(
        f'/workflows/comments/{event.id}',
        data={
            'attachments': []
        }
    )

    # arrange
    assert response.status_code == 200
    service_init_mock.assert_called_once_with(
        instance=event,
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    comment_update_mock.assert_called_once_with(
        attachments=None,
        force_save=True,
    )


def test_update_remove_text__null__ok(mocker, api_client):

    # assert
    user = create_test_user()
    workflow = create_test_workflow(user)
    event = WorkflowEventService.comment_created_event(
        user=user,
        text='Some comment',
        workflow=workflow,
        attachments=[1, 2],
        after_create_actions=False
    )
    attach_1 = FileAttachment.objects.create(
        account_id=user.account_id,
        name='filename.png',
        size=384812,
        url='https://cloud.google.com/bucket/filename_salt.png',
        thumbnail_url='https://cloud.google.com/bucket/filename_thumb.png',
        event=event
    )
    attach_2 = FileAttachment.objects.create(
        account_id=user.account_id,
        name='doc.docx',
        size=2412413,
        url='https://cloud.google.com/bucket/doc_salt.docx',
        event=event
    )
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    comment_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.'
        'CommentService.update',
        return_value=event
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.patch(
        f'/workflows/comments/{event.id}',
        data={
            'text': None,
            'attachments': [
                attach_1.id,
                attach_2.id
            ]
        }
    )

    # arrange
    assert response.status_code == 200
    assert len(response.data['attachments']) == 2
    attach_data = response.data['attachments'][0]
    assert attach_data['id'] == attach_1.id
    assert attach_data['name'] == attach_1.name
    assert attach_data['url'] == attach_1.url
    assert attach_data['thumbnail_url'] == attach_1.thumbnail_url
    assert attach_data['thumbnail_url'] == attach_1.thumbnail_url
    assert attach_data['size'] == attach_1.size

    service_init_mock.assert_called_once_with(
        instance=event,
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    comment_update_mock.assert_called_once_with(
        text=None,
        attachments=[attach_1.id, attach_2.id],
        force_save=True,
    )


def test_update_remove_text__blank__ok(mocker, api_client):

    # assert
    user = create_test_user()
    workflow = create_test_workflow(user)
    event = WorkflowEventService.comment_created_event(
        user=user,
        text='Some comment',
        workflow=workflow,
        attachments=[1, 2],
        after_create_actions=False
    )
    attach_1 = FileAttachment.objects.create(
        account_id=user.account_id,
        name='filename.png',
        size=384812,
        url='https://cloud.google.com/bucket/filename_salt.png',
        thumbnail_url='https://cloud.google.com/bucket/filename_thumb.png',
        event=event
    )
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    comment_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.'
        'CommentService.update',
        return_value=event
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.patch(
        f'/workflows/comments/{event.id}',
        data={
            'text': ' ',
            'attachments': [
                attach_1.id,
            ]
        }
    )

    # arrange
    assert response.status_code == 200
    assert len(response.data['attachments']) == 1
    attach_data = response.data['attachments'][0]
    assert attach_data['id'] == attach_1.id
    assert attach_data['name'] == attach_1.name
    assert attach_data['url'] == attach_1.url
    assert attach_data['thumbnail_url'] == attach_1.thumbnail_url
    assert attach_data['thumbnail_url'] == attach_1.thumbnail_url
    assert attach_data['size'] == attach_1.size

    service_init_mock.assert_called_once_with(
        instance=event,
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    comment_update_mock.assert_called_once_with(
        text=None,
        attachments=[attach_1.id],
        force_save=True,
    )


def test_update__admin__ok(api_client, mocker):

    # arrange
    owner = create_test_user(is_account_owner=True)
    user = create_test_user(
        account=owner.account,
        email='admin@test.test',
        is_account_owner=False,
        is_admin=True
    )
    workflow = create_test_workflow(owner)
    task = workflow.current_task_instance
    task.performers.add(user)
    workflow.members.add(user)
    event = WorkflowEventService.comment_created_event(
        text='Some comment',
        workflow=workflow,
        user=user,
        after_create_actions=False
    )
    event.updated = timezone.now() + timedelta(hours=1)
    event.save()
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    comment_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.'
        'CommentService.update',
        return_value=event
    )
    api_client.token_authenticate(user)
    new_text = 'New comment text'

    # act
    response = api_client.patch(
        f'/workflows/comments/{event.id}',
        data={'text': new_text}
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == event.id
    assert response.data['created'] == event.created.strftime(datetime_format)
    assert response.data['created_tsp'] == event.created.timestamp()
    assert response.data['updated'] == event.updated.strftime(datetime_format)
    assert response.data['updated_tsp'] == event.updated.timestamp()
    assert response.data['status'] == CommentStatus.CREATED
    assert response.data['task']['id'] == workflow.current_task_instance.id
    assert response.data['task']['due_date'] is None
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
        is_superuser=False
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
        is_admin=False
    )
    workflow = create_test_workflow(owner)
    task = workflow.current_task_instance
    task.performers.add(user)
    workflow.members.add(user)
    event = WorkflowEventService.comment_created_event(
        text='Some comment',
        workflow=workflow,
        user=user,
        after_create_actions=False
    )
    event.updated = timezone.now() + timedelta(hours=1)
    event.save()
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    comment_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.'
        'CommentService.update',
        return_value=event
    )
    api_client.token_authenticate(user)
    new_text = 'New comment text'

    # act
    response = api_client.patch(
        f'/workflows/comments/{event.id}',
        data={'text': new_text}
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == event.id
    assert response.data['created'] == event.created.strftime(datetime_format)
    assert response.data['created_tsp'] == event.created.timestamp()
    assert response.data['updated'] == event.updated.strftime(datetime_format)
    assert response.data['updated_tsp'] == event.updated.timestamp()
    assert response.data['status'] == CommentStatus.CREATED
    assert response.data['task']['id'] == workflow.current_task_instance.id
    assert response.data['text'] == event.text
    assert response.data['type'] == event.type
    assert response.data['user_id'] == user.id
    assert response.data['target_user_id'] is None
    assert response.data['delay'] is None
    service_init_mock.assert_called_once_with(
        instance=event,
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
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
        user=guest,
        text='Some comment',
        workflow=workflow,
        after_create_actions=False
    )
    event.updated = timezone.now() + timedelta(hours=1)
    event.save()
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    comment_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.'
        'CommentService.update',
        return_value=event
    )
    new_text = 'New comment text'

    # act
    response = api_client.patch(
        f'/workflows/comments/{event.id}',
        data={'text': new_text},
        **{'X-Guest-Authorization': str_token}
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == event.id
    assert response.data['created'] == event.created.strftime(datetime_format)
    assert response.data['created_tsp'] == event.created.timestamp()
    assert response.data['updated'] == event.updated.strftime(datetime_format)
    assert response.data['updated_tsp'] == event.updated.timestamp()
    assert response.data['status'] == CommentStatus.CREATED
    assert response.data['task']['id'] == workflow.current_task_instance.id
    assert response.data['text'] == event.text
    assert response.data['type'] == event.type
    assert response.data['user_id'] == guest.id
    assert response.data['target_user_id'] is None
    assert response.data['delay'] is None
    service_init_mock.assert_called_once_with(
        instance=event,
        user=guest,
        auth_type=AuthTokenType.GUEST,
        is_superuser=False
    )
    comment_update_mock.assert_called_once_with(
        text=new_text,
        force_save=True,
    )


def test_update__guest_another_workflow__permission_denied(
    mocker,
    api_client
):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        account=account,
        email='owner@test.test',
        is_account_owner=True,
    )
    workflow_1 = create_test_workflow(account_owner, tasks_count=1)
    event = WorkflowEventService.comment_created_event(
        text='Some comment',
        workflow=workflow_1,
        user=account_owner,
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

    workflow_2 = create_test_workflow(account_owner, tasks_count=1)
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
    comment_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.'
        'CommentService.update'
    )

    # act
    response = api_client.patch(
        f'/workflows/comments/{event.id}',
        data={'text': 'Test text'},
        **{'X-Guest-Authorization': str_token_2}
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    comment_update_mock.assert_not_called()


def test_update__service_exception__validation_error(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    event = WorkflowEventService.comment_created_event(
        text='Some comment',
        workflow=workflow,
        user=user,
        after_create_actions=False
    )
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    message = 'some message'
    comment_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.'
        'CommentService.update',
        side_effect=CommentServiceException(message)
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.patch(
        f'/workflows/comments/{event.id}',
        data={'text': 'Raise'}
    )

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
        is_admin=True
    )
    workflow = create_test_workflow(owner)
    task = workflow.current_task_instance
    task.performers.add(user)
    event = WorkflowEventService.comment_created_event(
        text='Some comment',
        workflow=workflow,
        user=owner,
        after_create_actions=False
    )

    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    comment_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.'
        'CommentService.update',
        return_value=event
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.patch(
        f'/workflows/comments/{event.id}',
        data={'text': 'New comment text'}
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    comment_update_mock.assert_not_called()


def test_update__not_comment__permission_denied(api_client, mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    event = WorkflowEventService.task_complete_event(
        user=user,
        task=workflow.current_task_instance
    )

    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    comment_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.'
        'CommentService.update',
        return_value=event
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.patch(
        f'/workflows/comments/{event.id}',
        data={'text': 'New comment text'}
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    comment_update_mock.assert_not_called()
