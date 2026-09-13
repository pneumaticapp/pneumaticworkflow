import pytest

from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.enums import WorkflowEventType
from src.processes.services.events import CommentService
from src.processes.services.exceptions import (
    CommentServiceException,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_event,
    create_test_owner,
    create_test_workflow,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_partial_update__comment__emit_comment_update(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    comment = create_test_event(
        workflow=workflow,
        user=owner,
        type_event=WorkflowEventType.COMMENT,
        task=task,
    )
    comment_service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None,
    )
    comment_update_mock = mocker.patch(
        'src.processes.services.events.CommentService.update',
        return_value=comment,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/workflows/comments/{comment.id}',
        data={'text': 'New comment text'},
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TASK_COMMENT_UPDATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.COMMENT,
        id=comment.id,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_name': task.name,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id
    comment_service_init_mock.assert_called_once_with(
        instance=comment,
        user=owner,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    comment_update_mock.assert_called_once_with(
        text='New comment text',
        force_save=True,
    )


def test_partial_update__comment_without_task__no_task_name(
    mocker,
    api_client,
    fake_stream,
):

    """ The task of a comment is SET_NULL on delete. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    comment = create_test_event(
        workflow=workflow,
        user=owner,
        type_event=WorkflowEventType.COMMENT,
    )
    comment.task = None
    comment.save(update_fields=['task'])
    comment_service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None,
    )
    comment_update_mock = mocker.patch(
        'src.processes.services.events.CommentService.update',
        return_value=comment,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/workflows/comments/{comment.id}',
        data={'text': 'New comment text'},
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TASK_COMMENT_UPDATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.COMMENT,
        id=comment.id,
    )
    assert event.payload == {'workflow_name': workflow.name}
    assert event.workflow_id == workflow.id
    assert event.task_id is None
    comment_service_init_mock.assert_called_once_with(
        instance=comment,
        user=owner,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    comment_update_mock.assert_called_once_with(
        text='New comment text',
        force_save=True,
    )


def test_partial_update__service_exception__no_comment_update_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    comment = create_test_event(
        workflow=workflow,
        user=owner,
        type_event=WorkflowEventType.COMMENT,
    )
    message = 'some message'
    comment_service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None,
    )
    comment_update_mock = mocker.patch(
        'src.processes.services.events.CommentService.update',
        side_effect=CommentServiceException(message),
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/workflows/comments/{comment.id}',
        data={'text': 'New comment text'},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details'] == {}
    assert fake_stream.events == []
    comment_service_init_mock.assert_called_once_with(
        instance=comment,
        user=owner,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    comment_update_mock.assert_called_once_with(
        text='New comment text',
        force_save=True,
    )
