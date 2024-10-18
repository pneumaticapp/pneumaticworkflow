import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
    create_test_workflow,
)
from pneumatic_backend.processes.api_v2.services import exceptions
from pneumatic_backend.processes.api_v2.services.events import (
    CommentService
)
from pneumatic_backend.processes.enums import (
    WorkflowEventType,
    WorkflowStatus,
    CommentStatus,
    WorkflowEventActionType,
)
from pneumatic_backend.processes.models import (
    WorkflowEvent,
    WorkflowEventAction,
    FileAttachment,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.messages import workflow as messages


UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_create__not_another_performers__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.add(user)

    text = 'Text comment'
    clear_text = 'clear text'
    is_superuser = True
    auth_type = AuthTokenType.API

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text=text,
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    comment_created_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'WorkflowEventService.comment_created_event',
        return_value=event
    )
    clear_text_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'MarkdownService.clear',
        return_value=clear_text
    )
    update_attachments_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._update_attachments'
    )
    send_notifications_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._get_new_comment_recipients',
        return_value=((), ())
    )
    send_comment_notification_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'send_comment_notification.delay'
    )
    send_mention_notification_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'send_mention_notification.delay'
    )
    comment_added_analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_added'
    )
    mention_created_analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.mentions_created'
    )
    service = CommentService(
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type
    )

    # act
    result = service.create(
        workflow=workflow,
        text=text,
    )

    # assert
    assert result == event
    clear_text_mock.assert_called_once_with(text)
    comment_created_event_mock.assert_called_once_with(
        user=account_owner,
        workflow=workflow,
        text=text,
        clear_text=clear_text,
        attachments=None
    )
    send_notifications_mock.assert_called_once_with()
    update_attachments_mock.assert_not_called()
    comment_added_analytics_mock.assert_not_called()
    send_comment_notification_mock.assert_not_called()
    mention_created_analytics_mock.assert_not_called()
    send_mention_notification_mock.assert_not_called()
    task.refresh_from_db()
    assert task.contains_comments is True


def test_create__notified_users__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.add(user)

    text = 'Text comment'
    clear_text = 'clear text'
    is_superuser = True
    auth_type = AuthTokenType.API

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text=text,
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    comment_created_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'WorkflowEventService.comment_created_event',
        return_value=event
    )
    clear_text_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'MarkdownService.clear',
        return_value=clear_text
    )
    update_attachments_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._update_attachments'
    )
    send_notifications_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._get_new_comment_recipients',
        return_value=((), (user.id,))
    )
    send_comment_notification_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'send_comment_notification.delay'
    )
    send_mention_notification_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'send_mention_notification.delay'
    )
    comment_added_analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_added'
    )
    mention_created_analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.mentions_created'
    )
    service = CommentService(
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type
    )

    # act
    result = service.create(
        workflow=workflow,
        text=text,
    )

    # assert
    assert result == event
    clear_text_mock.assert_called_once_with(text)
    comment_created_event_mock.assert_called_once_with(
        user=account_owner,
        workflow=workflow,
        text=text,
        clear_text=clear_text,
        attachments=None
    )
    send_notifications_mock.assert_called_once_with()
    update_attachments_mock.assert_not_called()
    comment_added_analytics_mock.assert_called_once_with(
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow
    )
    send_comment_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        author_id=account_owner.id,
        task_id=task.id,
        account_id=account.id,
        users_ids=(user.id,),
        text=text
    )
    mention_created_analytics_mock.assert_not_called()
    send_mention_notification_mock.assert_not_called()
    task.refresh_from_db()
    assert task.contains_comments is True


def test_create_mentioned_users__ok(mocker):

    # arrange
    account = create_test_account(log_api_requests=True)
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.add(user)

    text = f'Go [Joe Stalin|{user.id}] testing'
    clear_text = 'clear text'
    is_superuser = True
    auth_type = AuthTokenType.API

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text=text,
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    comment_created_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'WorkflowEventService.comment_created_event',
        return_value=event
    )
    clear_text_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'MarkdownService.clear',
        return_value=clear_text
    )
    update_attachments_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._update_attachments'
    )
    send_notifications_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._get_new_comment_recipients',
        return_value=((user.id,), ())
    )
    send_comment_notification_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'send_comment_notification.delay'
    )
    send_mention_notification_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'send_mention_notification.delay'
    )
    comment_added_analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_added'
    )
    mention_created_analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.mentions_created'
    )
    service = CommentService(
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type
    )

    # act
    result = service.create(
        workflow=workflow,
        text=text,
    )

    # assert
    assert result == event
    clear_text_mock.assert_called_once_with(text)
    comment_created_event_mock.assert_called_once_with(
        user=account_owner,
        workflow=workflow,
        text=text,
        clear_text=clear_text,
        attachments=None
    )
    send_notifications_mock.assert_called_once_with()
    update_attachments_mock.assert_not_called()
    mention_created_analytics_mock.assert_called_once_with(
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow
    )
    send_mention_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        author_id=account_owner.id,
        task_id=workflow.current_task_instance.id,
        account_id=account.id,
        users_ids=(user.id,),
        text=text
    )
    comment_added_analytics_mock.assert_not_called()
    send_comment_notification_mock.assert_not_called()
    assert workflow.members.filter(id=user.id).exists()
    task.refresh_from_db()
    assert task.contains_comments is True


def test_create__with_attachments__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.add(user)

    text = (
        "(![avatar.jpg](https://storage.com/dev/avatar.jpg "
        "\"attachment_id:3349 entityType:image\")"
    )
    clear_text = 'clear text'
    is_superuser = True
    auth_type = AuthTokenType.API

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text=text,
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    attachments = [1, 2, 3]
    comment_created_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'WorkflowEventService.comment_created_event',
        return_value=event
    )
    clear_text_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'MarkdownService.clear',
        return_value=clear_text
    )
    update_attachments_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._update_attachments'
    )
    send_notifications_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._get_new_comment_recipients',
        return_value=((), ())
    )
    send_comment_notification_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'send_comment_notification.delay'
    )
    send_mention_notification_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'send_mention_notification.delay'
    )
    comment_added_analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_added'
    )
    mention_created_analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.mentions_created'
    )
    service = CommentService(
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type
    )

    # act
    result = service.create(
        workflow=workflow,
        text=text,
        attachments=attachments
    )

    # assert
    assert result == event
    clear_text_mock.assert_called_once_with(text)
    comment_created_event_mock.assert_called_once_with(
        user=account_owner,
        workflow=workflow,
        text=text,
        clear_text=clear_text,
        attachments=attachments
    )
    send_notifications_mock.assert_called_once_with()
    update_attachments_mock.assert_called_once_with(attachments)
    comment_added_analytics_mock.assert_not_called()
    send_comment_notification_mock.assert_not_called()
    mention_created_analytics_mock.assert_not_called()
    send_mention_notification_mock.assert_not_called()
    task.refresh_from_db()
    assert task.contains_comments is True


@pytest.mark.parametrize('status', WorkflowStatus.END_STATUSES)
def test_create__workflow_ended__raise_exception(mocker, status):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True
    )
    workflow = create_test_workflow(
        account_owner,
        tasks_count=1,
        status=status
    )
    task = workflow.current_task_instance
    task.performers.add(user)

    text = 'Some text'
    clear_text = 'clear text'
    comment_created_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'WorkflowEventService.comment_created_event',
    )
    clear_text_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'MarkdownService.clear',
        return_value=clear_text
    )
    update_attachments_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._update_attachments'
    )
    send_notifications_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._get_new_comment_recipients',
        return_value=((), ())
    )
    send_comment_notification_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'send_comment_notification.delay'
    )
    send_mention_notification_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'send_mention_notification.delay'
    )
    comment_added_analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_added'
    )
    mention_created_analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.mentions_created'
    )
    service = CommentService(user=account_owner)

    # act
    with pytest.raises(exceptions.CommentedWorkflowNotRunning) as ex:
        service.create(
            workflow=workflow,
            text=text,
        )

    # assert
    assert ex.value.message == messages.MSG_PW_0048
    clear_text_mock.assert_not_called()
    comment_created_event_mock.assert_not_called()
    update_attachments_mock.assert_not_called()
    send_notifications_mock.assert_not_called()
    send_comment_notification_mock.assert_not_called()
    send_mention_notification_mock.assert_not_called()
    comment_added_analytics_mock.assert_not_called()
    mention_created_analytics_mock.assert_not_called()
    task.refresh_from_db()
    assert task.contains_comments is False


def test_create__not_text_and_attachment__raise_exception(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.add(user)

    comment_created_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'WorkflowEventService.comment_created_event',
    )
    clear_text_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'MarkdownService.clear'
    )
    update_attachments_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._update_attachments'
    )
    send_notifications_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._get_new_comment_recipients'
    )
    send_comment_notification_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'send_comment_notification.delay'
    )
    send_mention_notification_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'send_mention_notification.delay'
    )
    comment_added_analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_added'
    )
    mention_created_analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.mentions_created'
    )
    service = CommentService(user=account_owner)

    # act
    with pytest.raises(exceptions.CommentTextRequired) as ex:
        service.create(
            workflow=workflow,
            text=None,
            attachments=None
        )

    # assert
    assert ex.value.message == messages.MSG_PW_0047
    clear_text_mock.assert_not_called()
    comment_created_event_mock.assert_not_called()
    update_attachments_mock.assert_not_called()
    send_notifications_mock.assert_not_called()
    comment_added_analytics_mock.assert_not_called()
    send_comment_notification_mock.assert_not_called()
    send_mention_notification_mock.assert_not_called()
    mention_created_analytics_mock.assert_not_called()
    task.refresh_from_db()
    assert task.contains_comments is False


def test_update_attachments__create_new_attachments__ok():

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='text',
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    attachment = FileAttachment.objects.create(
        name='filename.png',
        url='https://path.to.file/filename.png',
        size=141352,
        account_id=account.id,
    )

    service = CommentService(
        user=account_owner,
        instance=event
    )

    # act
    service._update_attachments([attachment.id])

    # assert
    attachment.refresh_from_db()
    assert attachment.workflow == workflow
    assert attachment.event == event


def test_update_attachments__delete_old_attachments__ok():

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='text',
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    deleted_attachment = FileAttachment.objects.create(
        name='filename2.png',
        url='https://path.to.file/filename2.png',
        size=123,
        account_id=account.id,
        event=event
    )
    attachment = FileAttachment.objects.create(
        name='filename.png',
        url='https://path.to.file/filename.png',
        size=141352,
        account_id=account.id,
    )

    service = CommentService(
        user=account_owner,
        instance=event
    )

    # act
    service._update_attachments([attachment.id])

    # assert
    assert not FileAttachment.objects.by_id(deleted_attachment.id).exists()
    attachment.refresh_from_db()
    assert attachment.workflow == workflow
    assert attachment.event == event


def test_update_attachments__already_attached__ok():

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='text',
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    existent_attachment = FileAttachment.objects.create(
        name='filename2.png',
        url='https://path.to.file/filename2.png',
        size=123,
        account_id=account.id,
        event=event
    )
    new_attachment = FileAttachment.objects.create(
        name='filename.png',
        url='https://path.to.file/filename.png',
        size=141352,
        account_id=account.id,
    )

    service = CommentService(
        user=account_owner,
        instance=event
    )

    # act
    service._update_attachments([existent_attachment.id, new_attachment.id])

    # assert
    existent_attachment.refresh_from_db()
    assert existent_attachment.workflow == workflow
    assert existent_attachment.event == event
    new_attachment.refresh_from_db()
    assert new_attachment.workflow == workflow
    assert new_attachment.event == event


def test_update_attachments__attachments_is_null__not_update():

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='text',
        with_attachments=True,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    another_attachment = FileAttachment.objects.create(
        name='filename.png',
        url='https://path.to.file/filename.png',
        size=141352,
        account_id=account.id,
    )
    deleted_attachment = FileAttachment.objects.create(
        name='filename.png',
        url='https://path.to.file/filename.png',
        size=141352,
        account_id=account.id,
        event=event
    )

    service = CommentService(
        user=account_owner,
        instance=event
    )

    # act
    service._update_attachments(ids=None)

    # assert
    another_attachment.refresh_from_db()
    assert another_attachment.workflow is None
    assert another_attachment.event is None
    assert not FileAttachment.objects.by_id(deleted_attachment.id).exists()


def test_update_attachments__not_found__raise_exception():

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='text',
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    another_account = create_test_account()
    FileAttachment.objects.create(
        name='filename.png',
        url='https://path.to.file/filename.png',
        size=141352,
        account_id=another_account.id,
    )

    service = CommentService(
        user=account_owner,
        instance=event
    )

    # act
    with pytest.raises(exceptions.AttachmentNotFound) as ex:
        service._update_attachments([0])

    # assert
    assert ex.value.message == messages.MSG_PW_0037


def test_get_new_comment_recipients__notify_users__ok():

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True
    )
    task.performers.add(user)
    text = 'New comment'
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text=text,
        clear_text=text,
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )

    service = CommentService(
        user=account_owner,
        instance=event,
    )

    # act
    mentioned, notified = service._get_new_comment_recipients()

    # assert
    assert len(mentioned) == 0
    assert len(notified) == 1
    assert notified[0] == user.id


def test_get_new_comment_recipients__performer_mentioned__send_notify():

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True
    )
    task.performers.add(user)
    text = f'Go [Joe Stalin|{user.id}] testing'
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text=text,
        clear_text=text,
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )

    service = CommentService(
        user=account_owner,
        instance=event,
    )

    # act
    mentioned, notified = service._get_new_comment_recipients()

    # assert
    assert len(mentioned) == 0
    assert len(notified) == 1
    assert notified[0] == user.id


def test_get_new_comment_recipients__not_performer_mentioned__send_mention():

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True
    )
    text = f'Go [Joe Stalin|{user.id}] testing'
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text=text,
        clear_text=text,
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    service = CommentService(
        user=account_owner,
        instance=event,
    )

    # act
    mentioned, notified = service._get_new_comment_recipients()

    # assert
    assert len(mentioned) == 1
    assert len(notified) == 0
    assert mentioned[0] == user.id


def test_get_updated_comment_recipients__new_mentioned__send_mention():

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True
    )
    text = f'Go [Joe Stalin|{user.id}] testing'
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text=text,
        clear_text=text,
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    service = CommentService(
        user=account_owner,
        instance=event,
    )

    # act
    mentioned = service._get_updated_comment_recipients()

    # assert
    assert len(mentioned) == 1
    assert mentioned[0] == user.id


def test_get_updated_comment_recipients__already_mentioned__not_send():

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True
    )
    workflow.members.add(user)
    text = f'Go [Joe Stalin|{user.id}] testing'
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text=text,
        clear_text=text,
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    service = CommentService(
        user=account_owner,
        instance=event,
    )

    # act
    mentioned = service._get_updated_comment_recipients()

    # assert
    assert len(mentioned) == 0


def test_get_updated_comment_recipients__not_mention__not_send():

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True
    )
    workflow.members.add(user)
    text = f'Go {user.name} testing'
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text=text,
        clear_text=text,
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    service = CommentService(
        user=account_owner,
        instance=event,
    )

    # act
    mentioned = service._get_updated_comment_recipients()

    # assert
    assert len(mentioned) == 0


def test_validate_comment_action__ok():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user=user,
        status=WorkflowStatus.RUNNING
    )
    event = WorkflowEvent.objects.create(
        account=user.account,
        type=WorkflowEventType.COMMENT,
        text='Old text',
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=user,
        status=CommentStatus.CREATED
    )
    service = CommentService(
        instance=event,
    )

    # act
    service._validate_comment_action()


def test_validate_comment_action__deleted__raise_exception():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user=user,
        status=WorkflowStatus.RUNNING
    )
    event = WorkflowEvent.objects.create(
        account=user.account,
        type=WorkflowEventType.COMMENT,
        text='Old text',
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=user,
        status=CommentStatus.DELETED
    )
    service = CommentService(
        instance=event,
    )

    # act
    with pytest.raises(exceptions.CommentIsDeleted) as ex:
        service._validate_comment_action()

    assert ex.value.message == messages.MSG_PW_0049


@pytest.mark.parametrize('status', WorkflowStatus.END_STATUSES)
def test_validate_comment__workflow_ended__raise_exception(status):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user=user,
        status=status
    )
    event = WorkflowEvent.objects.create(
        account=user.account,
        type=WorkflowEventType.COMMENT,
        text='Old text',
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=user,
    )
    service = CommentService(
        instance=event,
    )

    # act
    with pytest.raises(exceptions.CommentedWorkflowNotRunning) as ex:
        service._validate_comment_action()

    assert ex.value.message == messages.MSG_PW_0048


def test_update__text__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)

    is_superuser = True
    auth_type = AuthTokenType.API

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Old text',
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._validate_comment_action'
    )
    update_attachments_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._update_attachments'
    )
    get_updated_comment_recipients_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._get_updated_comment_recipients',
        return_value=()
    )
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._send_workflow_event'
    )
    clear_text = 'clear text'
    clear_text_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'MarkdownService.clear',
        return_value=clear_text
    )
    partial_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'BaseModelService.partial_update',
        return_value=event
    )
    send_mention_notification_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'send_mention_notification.delay'
    )
    comment_edited_analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_edited'
    )

    service = CommentService(
        instance=event,
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    date_updated = timezone.now()
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'timezone.now',
        return_value=date_updated
    )
    text = 'Text comment'

    # act
    result = service.update(
        text=text,
        force_save=True
    )

    # assert
    assert result == event
    validate_comment_action_mock.assert_called_once()
    get_updated_comment_recipients_mock.assert_called_once()
    send_workflow_event_mock.assert_called_once()
    update_attachments_mock.assert_not_called()
    clear_text_mock.assert_called_once_with(text)
    partial_update_mock.assert_called_once_with(
        text=text,
        clear_text=clear_text,
        status=CommentStatus.UPDATED,
        updated=date_updated,
        force_save=True
    )
    send_mention_notification_mock.assert_not_called()
    comment_edited_analytics_mock.assert_called_once_with(
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow
    )


def test_update__attachments__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)

    is_superuser = True
    auth_type = AuthTokenType.API

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Old text',
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._validate_comment_action'
    )
    update_attachments_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._update_attachments'
    )
    get_updated_comment_recipients_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._get_updated_comment_recipients',
        return_value=()
    )
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._send_workflow_event'
    )
    date_updated = timezone.now()
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'timezone.now',
        return_value=date_updated
    )
    partial_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'BaseModelService.partial_update',
        return_value=event
    )
    clear_text_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'MarkdownService.clear'
    )
    comment_edited_analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_edited'
    )
    send_mention_notification_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'send_mention_notification.delay'
    )

    service = CommentService(
        instance=event,
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    attachments = [1, 2]

    # act
    result = service.update(
        attachments=attachments,
        force_save=True
    )

    # assert
    assert result == event
    validate_comment_action_mock.assert_called_once()
    get_updated_comment_recipients_mock.assert_called_once()
    send_workflow_event_mock.assert_called_once()
    update_attachments_mock.assert_called_once_with(attachments)
    partial_update_mock.assert_called_once_with(
        with_attachments=True,
        status=CommentStatus.UPDATED,
        updated=date_updated,
        force_save=True
    )
    clear_text_mock.assert_not_called()
    comment_edited_analytics_mock.assert_called_once_with(
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow
    )
    send_mention_notification_mock.assert_not_called()


def test_update__notified_users__ok(mocker):

    # arrange
    account = create_test_account(log_api_requests=True)
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    user = create_test_user(
        is_account_owner=False,
        account=account,
        email='test@test.test'
    )

    is_superuser = True
    auth_type = AuthTokenType.API

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='text',
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._validate_comment_action'
    )
    update_attachments_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._update_attachments'
    )
    get_updated_comment_recipients_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._get_updated_comment_recipients',
        return_value=(user.id,)
    )
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._send_workflow_event'
    )
    date_updated = timezone.now()
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'timezone.now',
        return_value=date_updated
    )
    partial_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'BaseModelService.partial_update',
        return_value=event
    )
    clear_text = 'clear text'
    clear_text_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'MarkdownService.clear',
        return_value=clear_text
    )
    comment_edited_analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_edited'
    )
    send_mention_notification_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'send_mention_notification.delay'
    )

    service = CommentService(
        instance=event,
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    new_text = 'New text'
    attachments = [1, 2]

    # act
    result = service.update(
        text=new_text,
        attachments=attachments,
        force_save=True
    )

    # assert
    assert result == event
    validate_comment_action_mock.assert_called_once()
    get_updated_comment_recipients_mock.assert_called_once()
    send_workflow_event_mock.assert_called_once()
    update_attachments_mock.assert_called_once_with(attachments)
    clear_text_mock.assert_called_once_with(new_text)
    partial_update_mock.assert_called_once_with(
        text=new_text,
        clear_text=clear_text,
        with_attachments=True,
        status=CommentStatus.UPDATED,
        updated=date_updated,
        force_save=True
    )
    comment_edited_analytics_mock.assert_called_once_with(
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow
    )
    send_mention_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        author_id=account_owner.id,
        task_id=workflow.current_task_instance.id,
        account_id=account.id,
        users_ids=(user.id,),
        text=event.text
    )
    assert workflow.members.filter(id=user.id).exists()


def test_update__mentioned_users__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    user = create_test_user(
        email='text@test.text',
        account=account,
        is_account_owner=False
    )

    is_superuser = True
    auth_type = AuthTokenType.API

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Old text',
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._validate_comment_action'
    )
    update_attachments_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._update_attachments'
    )
    get_updated_comment_recipients_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._get_updated_comment_recipients',
        return_value=(user.id,)
    )
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._send_workflow_event'
    )
    date_updated = timezone.now()
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'timezone.now',
        return_value=date_updated
    )
    clear_text = 'clear text'
    clear_text_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'MarkdownService.clear',
        return_value=clear_text
    )
    partial_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'BaseModelService.partial_update',
        return_value=event
    )
    comment_edited_analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_edited'
    )

    service = CommentService(
        instance=event,
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    text = 'New text'

    # act
    result = service.update(
        text=text,
        force_save=True
    )

    # assert
    assert result == event
    validate_comment_action_mock.assert_called_once()
    get_updated_comment_recipients_mock.assert_called_once()
    send_workflow_event_mock.assert_called_once()
    update_attachments_mock.assert_not_called()
    clear_text_mock.assert_called_once_with(text)
    partial_update_mock.assert_called_once_with(
        text=text,
        clear_text=clear_text,
        status=CommentStatus.UPDATED,
        updated=date_updated,
        force_save=True
    )
    assert workflow.members.filter(id=user.id).exists()
    comment_edited_analytics_mock.assert_called_once_with(
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow
    )


def test_update__remove_text__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        task=workflow.current_task_instance,
        text='Old text',
        with_attachments=True,
        workflow=workflow,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._validate_comment_action'
    )
    update_attachments_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._update_attachments'
    )
    get_updated_comment_recipients_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._get_updated_comment_recipients',
        return_value=()
    )
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._send_workflow_event'
    )
    date_updated = timezone.now()
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'timezone.now',
        return_value=date_updated
    )
    partial_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'BaseModelService.partial_update',
        return_value=event
    )
    clear_text_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'MarkdownService.clear'
    )
    comment_edited_analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_edited'
    )

    service = CommentService(
        instance=event,
        user=account_owner,
    )

    # act
    result = service.update(
        text=None,
        force_save=True
    )

    # assert
    assert result == event
    validate_comment_action_mock.assert_called_once()
    get_updated_comment_recipients_mock.assert_called_once()
    send_workflow_event_mock.assert_called_once()
    update_attachments_mock.assert_not_called()
    partial_update_mock.assert_called_once_with(
        text=None,
        clear_text=None,
        status=CommentStatus.UPDATED,
        updated=date_updated,
        force_save=True
    )
    clear_text_mock.assert_not_called()
    comment_edited_analytics_mock.assert_called_once_with(
        user=account_owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        workflow=workflow
    )


def test_update__remove_attachments__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text=None,
        with_attachments=True,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._validate_comment_action'
    )
    update_attachments_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._update_attachments'
    )
    get_updated_comment_recipients_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._get_updated_comment_recipients',
        return_value=()
    )
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._send_workflow_event'
    )
    date_updated = timezone.now()
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'timezone.now',
        return_value=date_updated
    )
    partial_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'BaseModelService.partial_update',
        return_value=event
    )
    clear_text_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'MarkdownService.clear'
    )
    comment_edited_analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_edited'
    )

    service = CommentService(
        instance=event,
        user=account_owner,
    )

    # act
    result = service.update(
        text=None,
        force_save=True
    )

    # assert
    assert result == event
    validate_comment_action_mock.assert_called_once()
    get_updated_comment_recipients_mock.assert_called_once_with()
    send_workflow_event_mock.assert_called_once()
    update_attachments_mock.assert_not_called()
    clear_text_mock.assert_not_called()
    partial_update_mock.assert_called_once_with(
        text=None,
        clear_text=None,
        status=CommentStatus.UPDATED,
        updated=date_updated,
        force_save=True
    )
    comment_edited_analytics_mock.assert_called_once_with(
        user=account_owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        workflow=workflow
    )


def test_update__remove_text__raise_exception(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='text',
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._validate_comment_action'
    )
    update_attachments_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._update_attachments'
    )
    get_updated_comment_recipients_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._get_new_comment_recipients',
        return_value=((), ())
    )
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._send_workflow_event'
    )
    partial_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'BaseModelService.partial_update'
    )
    comment_edited_analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_edited'
    )
    clear_text_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'MarkdownService.clear'
    )

    service = CommentService(
        instance=event,
        user=account_owner,
    )

    # act
    with pytest.raises(exceptions.CommentTextRequired) as ex:
        service.update(
            text=None,
            force_save=True
        )

    # assert
    assert ex.value.message == messages.MSG_PW_0047
    validate_comment_action_mock.assert_called_once()
    get_updated_comment_recipients_mock.assert_not_called()
    send_workflow_event_mock.assert_not_called()
    update_attachments_mock.assert_not_called()
    clear_text_mock.assert_not_called()
    partial_update_mock.assert_not_called()
    comment_edited_analytics_mock.assert_not_called()


def test_update__remove_attachment__raise_exception(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text=None,
        with_attachments=True,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._validate_comment_action'
    )
    update_attachments_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._update_attachments'
    )
    get_updated_comment_recipients_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._get_updated_comment_recipients',
        return_value=()
    )
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._send_workflow_event'
    )
    partial_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'BaseModelService.partial_update'
    )
    comment_edited_analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_edited'
    )

    service = CommentService(
        instance=event,
        user=account_owner,
    )

    # act
    with pytest.raises(exceptions.CommentTextRequired) as ex:
        service.update(
            attachments=None,
            force_save=True
        )

    # assert
    assert ex.value.message == messages.MSG_PW_0047
    validate_comment_action_mock.assert_called_once()
    get_updated_comment_recipients_mock.assert_not_called()
    send_workflow_event_mock.assert_not_called()
    update_attachments_mock.assert_not_called()
    partial_update_mock.assert_not_called()
    comment_edited_analytics_mock.assert_not_called()


def test_delete__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Old text',
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    FileAttachment.objects.create(
        name='filename.png',
        url='https://path.to.file/filename.png',
        size=141352,
        account_id=account.id,
        event=event
    )
    validate_comment_action_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._validate_comment_action'
    )
    partial_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'BaseModelService.partial_update',
        return_value=event
    )
    comment_deleted_analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_deleted'
    )
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._send_workflow_event'
    )

    service = CommentService(
        instance=event,
        user=account_owner
    )

    # act
    result = service.delete()

    # assert
    event.refresh_from_db()
    assert result == event
    validate_comment_action_mock.assert_called_once()
    partial_update_mock.assert_called_once_with(
        status=CommentStatus.DELETED,
        with_attachments=False,
        text=None,
        force_save=True
    )
    assert event.attachments.count() == 0
    comment_deleted_analytics_mock.assert_called_once_with(
        user=account_owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        workflow=workflow
    )
    send_workflow_event_mock.assert_called_once()


def test_watched__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Comment text',
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._validate_comment_action'
    )

    service = CommentService(
        instance=event,
        user=user
    )

    # act
    service.watched()

    # assert
    validate_comment_action_mock.assert_called_once()
    assert WorkflowEventAction.objects.get(
        event=event,
        user=user,
        type=WorkflowEventActionType.WATCHED,
    )


def test_watched__comment_author__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Comment text',
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )

    service = CommentService(
        instance=event,
        user=account_owner
    )
    validate_comment_action_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._validate_comment_action'
    )

    # act
    service.watched()

    # assert
    validate_comment_action_mock.assert_called_once()
    assert not WorkflowEventAction.objects.filter(
        event=event,
        user=account_owner,
        type=WorkflowEventActionType.WATCHED,
    ).exists()


def test_watched__already_watched__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Comment text',
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    event.watched = [
        {
            'date':  timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'user_id': user.id
        }
    ]
    event.save()
    service = CommentService(
        instance=event,
        user=user
    )
    validate_comment_action_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._validate_comment_action'
    )

    # act
    service.watched()

    # assert
    validate_comment_action_mock.assert_called_once()
    assert not WorkflowEventAction.objects.filter(
        event=event,
        user=user,
        type=WorkflowEventActionType.WATCHED,
    ).exists()


def test_create_reaction__first__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Comment text',
        clear_text='Clear text',
        with_attachments=False,
        workflow=workflow,
        user=account_owner,
        task=task
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_reaction_added'
    )
    send_reaction_notification_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'send_reaction_notification.delay'
    )
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._send_workflow_event'
    )
    reaction = ':dumb face:'
    is_superuser = True
    auth_type = AuthTokenType.API
    service = CommentService(
        instance=event,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser
    )
    validate_comment_action_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._validate_comment_action'
    )

    # act
    service.create_reaction(reaction)

    # assert
    validate_comment_action_mock.assert_called_once()
    event.refresh_from_db()
    assert event.reactions[reaction] == [user.id]
    analytics_mock.assert_called_once_with(
        user=user,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    send_workflow_event_mock.assert_called_once()
    send_reaction_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        author_id=user.id,
        task_id=task.id,
        account_id=account.id,
        user_id=account_owner.id,
        author_name=account_owner.name,
        reaction=reaction,
        workflow_name=workflow.name
    )


def test_create_reaction__long_comment__cut_off(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='a',
        clear_text='a'*41,
        with_attachments=False,
        workflow=workflow,
        user=account_owner,
        task=task
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_reaction_added'
    )
    send_reaction_notification_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'send_reaction_notification.delay'
    )
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._send_workflow_event'
    )
    reaction = ':dumb face:'
    is_superuser = True
    auth_type = AuthTokenType.API
    service = CommentService(
        instance=event,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser
    )
    validate_comment_action_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._validate_comment_action'
    )

    # act
    service.create_reaction(reaction)

    # assert
    validate_comment_action_mock.assert_called_once()
    event.refresh_from_db()
    assert event.reactions[reaction] == [user.id]
    analytics_mock.assert_called_once_with(
        user=user,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    send_workflow_event_mock.assert_called_once()
    send_reaction_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        author_id=user.id,
        task_id=task.id,
        account_id=account.id,
        user_id=account_owner.id,
        author_name=account_owner.name,
        reaction=reaction,
        workflow_name=workflow.name
    )


def test_create_reaction__not_comment_text__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        with_attachments=True,
        workflow=workflow,
        user=account_owner,
        task=task
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_reaction_added'
    )
    send_reaction_notification_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'send_reaction_notification.delay'
    )
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._send_workflow_event'
    )
    reaction = ':dumb face:'
    is_superuser = True
    auth_type = AuthTokenType.API
    service = CommentService(
        instance=event,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser
    )
    validate_comment_action_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._validate_comment_action'
    )

    # act
    service.create_reaction(reaction)

    # assert
    validate_comment_action_mock.assert_called_once()
    event.refresh_from_db()
    assert event.reactions[reaction] == [user.id]
    analytics_mock.assert_called_once_with(
        user=user,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    send_workflow_event_mock.assert_called_once()
    send_reaction_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        author_id=user.id,
        task_id=task.id,
        account_id=account.id,
        user_id=account_owner.id,
        author_name=account_owner.name,
        reaction=reaction,
        workflow_name=workflow.name
    )


def test_create_reaction__second__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Comment text',
        clear_text='Clear text',
        with_attachments=False,
        workflow=workflow,
        user=account_owner,
        task=task,
    )
    reaction = ':dumb face:'
    event.reactions[reaction] = [account_owner.id]
    event.reactions['=D'] = [user.id]
    event.save()
    analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_reaction_added'
    )
    send_reaction_notification_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'send_reaction_notification.delay'
    )
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._send_workflow_event'
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    service = CommentService(
        instance=event,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser
    )
    validate_comment_action_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._validate_comment_action'
    )

    # act
    service.create_reaction(reaction)

    # assert
    validate_comment_action_mock.assert_called_once()
    event.refresh_from_db()
    assert event.reactions[reaction] == [account_owner.id, user.id]
    analytics_mock.assert_called_once_with(
        user=user,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    send_workflow_event_mock.assert_called_once()
    send_reaction_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        author_id=user.id,
        task_id=task.id,
        account_id=account.id,
        user_id=account_owner.id,
        author_name=account_owner.name,
        reaction=reaction,
        workflow_name=workflow.name
    )


def test_create_reaction__duplicate__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance
    reaction = ':dumb face:'
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Comment text',
        task=task,
        with_attachments=False,
        workflow=workflow,
        user=account_owner,
    )
    event.reactions[reaction] = [user.id]
    event.save()

    analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_reaction_added'
    )
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._send_workflow_event'
    )
    send_reaction_notification_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'send_reaction_notification.delay'
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    service = CommentService(
        instance=event,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser
    )
    validate_comment_action_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._validate_comment_action'
    )

    # act
    service.create_reaction(reaction)

    # assert
    validate_comment_action_mock.assert_called_once()
    event.refresh_from_db()
    assert event.reactions[reaction] == [user.id]
    analytics_mock.assert_not_called()
    send_workflow_event_mock.assert_not_called()
    send_reaction_notification_mock.assert_not_called()


def test_delete_reaction__last__remove_reaction(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    reaction = ':dumb face:'
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Comment text',
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    event.reactions[reaction] = [user.id]
    event.save()

    analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_reaction_deleted'
    )
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._send_workflow_event'
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    service = CommentService(
        instance=event,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser
    )
    validate_comment_action_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._validate_comment_action'
    )

    # act
    service.delete_reaction(reaction)

    # assert
    validate_comment_action_mock.assert_called_once()
    event.refresh_from_db()
    assert reaction not in event.reactions.keys()
    analytics_mock.assert_called_once_with(
        user=user,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    send_workflow_event_mock.assert_called_once()


def test_delete_reaction__not_last__remove_only_user_id(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    reaction = ':dumb face:'
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Comment text',
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )
    event.reactions[reaction] = [user.id, account_owner.id]
    event.save()

    analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_reaction_deleted'
    )
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._send_workflow_event'
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    service = CommentService(
        instance=event,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser
    )
    validate_comment_action_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._validate_comment_action'
    )

    # act
    service.delete_reaction(reaction)

    # assert
    validate_comment_action_mock.assert_called_once()
    event.refresh_from_db()
    assert event.reactions == {reaction: [account_owner.id]}
    analytics_mock.assert_called_once_with(
        user=user,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    send_workflow_event_mock.assert_called_once()


def test_delete_reaction__not_exist_reaction__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    reaction = ':dumb face:'
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Comment text',
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )

    analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_reaction_deleted'
    )
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._send_workflow_event'
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    service = CommentService(
        instance=event,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser
    )
    validate_comment_action_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._validate_comment_action'
    )

    # act
    service.delete_reaction(reaction)

    # assert
    validate_comment_action_mock.assert_called_once()
    event.refresh_from_db()
    assert event.reactions == {}
    analytics_mock.assert_not_called()
    send_workflow_event_mock.assert_not_called()


def test_delete_reaction__not_exist_user_id__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    reaction = ':dumb face:'
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Comment text',
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        user=account_owner,
    )

    analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_reaction_deleted'
    )
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._send_workflow_event'
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    service = CommentService(
        instance=event,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser
    )
    validate_comment_action_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._validate_comment_action'
    )

    # act
    service.delete_reaction(reaction)

    # assert
    validate_comment_action_mock.assert_called_once()
    event.refresh_from_db()
    assert event.reactions == {}
    analytics_mock.assert_not_called()
    send_workflow_event_mock.assert_not_called()


def test_create_reaction__to_yourself_comment__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Comment text',
        clear_text='Clear text',
        with_attachments=False,
        workflow=workflow,
        user=user,
        task=task
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'AnalyticService.comment_reaction_added'
    )
    send_reaction_notification_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'send_reaction_notification.delay'
    )
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._send_workflow_event'
    )
    reaction = ':dumb face:'
    is_superuser = True
    auth_type = AuthTokenType.API
    service = CommentService(
        instance=event,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser
    )
    validate_comment_action_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'CommentService._validate_comment_action'
    )

    # act
    service.create_reaction(reaction)

    # assert
    validate_comment_action_mock.assert_called_once()
    event.refresh_from_db()
    assert event.reactions[reaction] == [user.id]
    analytics_mock.assert_called_once_with(
        user=user,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    send_workflow_event_mock.assert_called_once()
    send_reaction_notification_mock.assert_not_called()
