import pytest
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

datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'
pytestmark = pytest.mark.django_db


def test_create__text__ok(api_client, mocker):

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
    comment_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.'
        'CommentService.create',
        return_value=event
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/comment',
        data={'text': event.text}
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == event.id
    assert response.data['created'] == event.created.strftime(datetime_format)
    assert response.data['created_tsp'] == event.created.timestamp()
    assert response.data['updated'] is None
    assert response.data['updated_tsp'] is None
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
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    comment_create_mock.assert_called_once_with(
        workflow=workflow,
        text=event.text,
    )


def test_create_text_and_attachment__ok(mocker, api_client):

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
    comment_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.'
        'CommentService.create',
        return_value=event
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/comment',
        data={
            'text': event.text,
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
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    comment_create_mock.assert_called_once_with(
        workflow=workflow,
        text=event.text,
        attachments=[attach_1.id, attach_2.id]
    )


def test_create__guest__ok(mocker, api_client):

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
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    comment_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.'
        'CommentService.create',
        return_value=event
    )

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/comment',
        data={'text': 'Test text'},
        **{'X-Guest-Authorization': str_token}
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == event.id
    assert response.data['created'] == event.created.strftime(datetime_format)
    assert response.data['created_tsp'] == event.created.timestamp()
    assert response.data['updated'] is None
    assert response.data['updated_tsp'] is None
    assert response.data['status'] == CommentStatus.CREATED
    assert response.data['task']['id'] == workflow.current_task_instance.id
    assert response.data['task']['due_date'] is None
    assert response.data['task']['due_date_tsp'] is None
    assert response.data['text'] == event.text
    assert response.data['type'] == event.type
    assert response.data['user_id'] == guest.id
    assert response.data['target_user_id'] is None
    assert response.data['delay'] is None
    service_init_mock.assert_called_once_with(
        user=guest,
        auth_type=AuthTokenType.GUEST,
        is_superuser=False
    )
    comment_create_mock.assert_called_once_with(
        workflow=workflow,
        text='Test text',
    )


def test_create__guest_another_workflow__permission_denied(
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
    comment_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.'
        'CommentService.create',
    )

    # act
    response = api_client.post(
        f'/workflows/{workflow_1.id}/comment',
        data={'text': 'Test text'},
        **{'X-Guest-Authorization': str_token_2}
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    comment_create_mock.assert_not_called()


def test_create__service_exception__validation_error(
    api_client,
    mocker
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None
    )
    message = 'some message'
    comment_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.'
        'CommentService.create',
        side_effect=CommentServiceException(message)
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/comment',
        data={'text': 'Raise'}
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    comment_create_mock.assert_called_once_with(
        workflow=workflow,
        text='Raise',
    )
