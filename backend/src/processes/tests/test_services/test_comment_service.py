import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    CommentStatus,
    TaskStatus,
    WorkflowEventActionType,
    WorkflowEventType,
    WorkflowStatus,
)
from src.processes.messages import workflow as messages
from src.processes.models.workflows.event import (
    WorkflowEvent,
    WorkflowEventAction,
)
from src.processes.serializers.workflows.events import (
    TaskEventJsonSerializer,
)
from src.processes.services import exceptions
from src.processes.services.events import (
    CommentService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_attachment,
    create_test_owner,
    create_test_user,
    create_test_workflow,
)
from src.storage.models import Attachment
from src.storage.enums import SourceType, AccessType

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
        is_admin=True,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
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
        task=task,
        user=account_owner,
    )
    comment_created_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.comment_created_event',
        return_value=event,
    )
    clear_text_mock = mocker.patch(
        'src.processes.services.events.'
        'MarkdownService.clear',
        return_value=clear_text,
    )
    refresh_attachments_mock = mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    get_new_comment_recipients_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._get_new_comment_recipients',
        return_value=((), ()),
    )
    send_comment_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_comment_notification.delay',
    )
    send_mention_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_mention_notification.delay',
    )
    comment_added_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_added',
    )
    mention_created_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.mentions_created',
    )
    service = CommentService(
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    result = service.create(
        task=task,
        text=text,
    )

    # assert
    assert result == event
    clear_text_mock.assert_called_once_with(text)
    comment_created_event_mock.assert_called_once_with(
        user=account_owner,
        task=task,
        text=text,
        clear_text=clear_text,
        after_create_actions=False,
    )
    get_new_comment_recipients_mock.assert_called_once_with(task)
    refresh_attachments_mock.assert_called_once_with(
        source=event,
        user=account_owner,
    )
    comment_added_analysis_mock.assert_not_called()
    send_comment_notification_mock.assert_not_called()
    mention_created_analysis_mock.assert_not_called()
    send_mention_notification_mock.assert_not_called()
    task.refresh_from_db()
    assert task.contains_comments is True


@pytest.mark.parametrize(
    'status',
    (
        TaskStatus.ACTIVE,
        TaskStatus.DELAYED,
    ),
)
def test_create__notified_users__ok(mocker, status):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.status = status
    task.save()
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
        task=task,
        task_json=TaskEventJsonSerializer(
            instance=task,
            context={'event_type': WorkflowEventType.COMMENT},
        ).data,
        user=account_owner,
    )
    comment_created_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.comment_created_event',
        return_value=event,
    )
    clear_text_mock = mocker.patch(
        'src.processes.services.events.'
        'MarkdownService.clear',
        return_value=clear_text,
    )
    refresh_attachments_mock = mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    get_new_comment_recipients_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._get_new_comment_recipients',
        return_value=((), (user.id,)),
    )
    send_comment_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_comment_notification.delay',
    )
    send_mention_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_mention_notification.delay',
    )
    comment_added_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_added',
    )
    mention_created_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.mentions_created',
    )
    service = CommentService(
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    result = service.create(
        task=task,
        text=text,
    )

    # assert
    assert result == event
    clear_text_mock.assert_called_once_with(text)
    comment_created_event_mock.assert_called_once_with(
        user=account_owner,
        task=task,
        text=text,
        clear_text=clear_text,
        after_create_actions=False,
    )
    get_new_comment_recipients_mock.assert_called_once_with(task)
    refresh_attachments_mock.assert_called_once_with(
        source=event,
        user=account_owner,
    )
    comment_added_analysis_mock.assert_called_once_with(
        text=clear_text,
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow,
    )
    send_comment_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        logo_lg=account.logo_lg,
        author_id=account_owner.id,
        event_id=event.id,
        account_id=account.id,
        users_ids=(user.id,),
        text=text,
    )
    mention_created_analysis_mock.assert_not_called()
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
        is_admin=True,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
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
        task=task,
        task_json=TaskEventJsonSerializer(
            instance=task,
            context={'event_type': WorkflowEventType.COMMENT},
        ).data,
        user=account_owner,
    )
    comment_created_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.comment_created_event',
        return_value=event,
    )
    clear_text_mock = mocker.patch(
        'src.processes.services.events.'
        'MarkdownService.clear',
        return_value=clear_text,
    )
    refresh_attachments_mock = mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    get_new_comment_recipients_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._get_new_comment_recipients',
        return_value=((user.id,), ()),
    )
    send_comment_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_comment_notification.delay',
    )
    send_mention_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_mention_notification.delay',
    )
    comment_added_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_added',
    )
    mention_created_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.mentions_created',
    )
    service = CommentService(
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    result = service.create(
        task=task,
        text=text,
    )

    # assert
    assert result == event
    clear_text_mock.assert_called_once_with(text)
    comment_created_event_mock.assert_called_once_with(
        user=account_owner,
        task=task,
        text=text,
        clear_text=clear_text,
        after_create_actions=False,
    )
    get_new_comment_recipients_mock.assert_called_once_with(task)
    refresh_attachments_mock.assert_called_once_with(
        source=event,
        user=account_owner,
    )
    mention_created_analysis_mock.assert_called_once_with(
        text=clear_text,
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow,
    )
    send_mention_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        logo_lg=account.logo_lg,
        author_id=account_owner.id,
        event_id=event.id,
        account_id=account.id,
        users_ids=(user.id,),
        text=text,
    )
    comment_added_analysis_mock.assert_not_called()
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
        is_admin=True,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.performers.add(user)

    text = (
        "(![avatar.jpg](https://storage.com/dev/avatar.jpg "
        '"attachment_id:3349 entityType:image")'
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
        task=task,
        user=account_owner,
    )
    comment_created_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.comment_created_event',
        return_value=event,
    )
    clear_text_mock = mocker.patch(
        'src.processes.services.events.'
        'MarkdownService.clear',
        return_value=clear_text,
    )
    refresh_attachments_mock = mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    get_new_comment_recipients_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._get_new_comment_recipients',
        return_value=((), ()),
    )
    send_comment_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_comment_notification.delay',
    )
    send_mention_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_mention_notification.delay',
    )
    comment_added_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_added',
    )
    mention_created_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.mentions_created',
    )
    service = CommentService(
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    result = service.create(
        task=task,
        text=text,
    )

    # assert
    assert result == event
    clear_text_mock.assert_called_once_with(text)
    comment_created_event_mock.assert_called_once_with(
        user=account_owner,
        task=task,
        text=text,
        clear_text=clear_text,
        after_create_actions=False,
    )
    get_new_comment_recipients_mock.assert_called_once_with(task)
    refresh_attachments_mock.assert_called_once_with(
        source=event,
        user=account_owner,
    )
    comment_added_analysis_mock.assert_not_called()
    send_comment_notification_mock.assert_not_called()
    mention_created_analysis_mock.assert_not_called()
    send_mention_notification_mock.assert_not_called()
    task.refresh_from_db()
    assert task.contains_comments is True


@pytest.mark.parametrize(
    'data',
    (
        (
            '(![avatar.jpg](https://storage.com/dev/avatar.jpg '
            '"attachment_id:3349 entityType:image")',
        ),
        (
            '[file.txt](http://file.txt "attachment_id:4187 entityType:file")',
        ),
        (
            '[video.mp4](https://video.mp4 "attachment_id:4188 '
            'entityType:video")',
        ),
        (
            'some [video.mp4](https://video.mp4 "attachment_id:4188 '
            'entityType:video") text \n(![avatar.jpg]'
            '(https://storage.com/dev/avatar.jpg '
            '"attachment_id:3349 entityType:image")',
        ),
        (
            '[ZIP-folder.zip](https://storage.zip "attachment_id:2482")',
        ),
        (
            '[ZIP-folder.zip](https://storage.zip "attachment_id:2482")',
        ),

    ),
)
def test_create__find_attachments_in_text__ok(data, mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.performers.add(user)

    text = f"text {data}\n some text"
    clear_text = 'clear text'
    is_superuser = True
    auth_type = AuthTokenType.API

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text=text,
        with_attachments=False,
        workflow=workflow,
        task=task,
        user=account_owner,
    )
    comment_created_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.comment_created_event',
        return_value=event,
    )
    clear_text_mock = mocker.patch(
        'src.processes.services.events.'
        'MarkdownService.clear',
        return_value=clear_text,
    )
    refresh_attachments_mock = mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    get_new_comment_recipients_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._get_new_comment_recipients',
        return_value=((), ()),
    )
    send_comment_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_comment_notification.delay',
    )
    send_mention_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_mention_notification.delay',
    )
    comment_added_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_added',
    )
    mention_created_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.mentions_created',
    )
    service = CommentService(
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    result = service.create(
        task=task,
        text=text,
    )

    # assert
    assert result == event
    clear_text_mock.assert_called_once_with(text)
    comment_created_event_mock.assert_called_once_with(
        user=account_owner,
        task=task,
        text=text,
        clear_text=clear_text,
        after_create_actions=False,
    )
    get_new_comment_recipients_mock.assert_called_once_with(task)
    refresh_attachments_mock.assert_called_once_with(
        source=event,
        user=account_owner,
    )
    comment_added_analysis_mock.assert_not_called()
    send_comment_notification_mock.assert_not_called()
    mention_created_analysis_mock.assert_not_called()
    send_mention_notification_mock.assert_not_called()
    task.refresh_from_db()
    assert task.contains_comments is True


@pytest.mark.parametrize(
    'text',
    (
        '([avatar.jpg](https://storage.com/dev/avatar.jpg)',
        '[file.txt](http://file.txt "attachment_id:4187 entityType:music")',
        '[video.mp4] (https://v.mp4 "attachment_id:4188 entityType:video")',
        '[video.mp4](ftp://video.mp4 "attachment_id:4188 entityType:video")',
    ),
)
def test_create__not_found_attachments_in_text__ok(text, mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.performers.add(user)

    text = f"text {text}\n some text"
    clear_text = 'clear text'
    is_superuser = True
    auth_type = AuthTokenType.API

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text=text,
        with_attachments=False,
        workflow=workflow,
        task=task,
        user=account_owner,
    )
    comment_created_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.comment_created_event',
        return_value=event,
    )
    clear_text_mock = mocker.patch(
        'src.processes.services.events.'
        'MarkdownService.clear',
        return_value=clear_text,
    )
    refresh_attachments_mock = mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    get_new_comment_recipients_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._get_new_comment_recipients',
        return_value=((), ()),
    )
    send_comment_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_comment_notification.delay',
    )
    send_mention_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_mention_notification.delay',
    )
    comment_added_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_added',
    )
    mention_created_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.mentions_created',
    )
    service = CommentService(
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    result = service.create(
        task=task,
        text=text,
    )

    # assert
    assert result == event
    clear_text_mock.assert_called_once_with(text)
    comment_created_event_mock.assert_called_once_with(
        user=account_owner,
        task=task,
        text=text,
        clear_text=clear_text,
        after_create_actions=False,
    )
    get_new_comment_recipients_mock.assert_called_once_with(task)
    refresh_attachments_mock.assert_called_once_with(
        source=event,
        user=account_owner,
    )
    comment_added_analysis_mock.assert_not_called()
    send_comment_notification_mock.assert_not_called()
    mention_created_analysis_mock.assert_not_called()
    send_mention_notification_mock.assert_not_called()
    task.refresh_from_db()
    assert task.contains_comments is True


def test_create__task_delete__raise_exception(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True,
    )
    workflow = create_test_workflow(
        account_owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.performers.add(user)
    task.delete()
    text = 'Some text'
    clear_text = 'clear text'
    comment_created_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.comment_created_event',
    )
    clear_text_mock = mocker.patch(
        'src.processes.services.events.'
        'MarkdownService.clear',
        return_value=clear_text,
    )
    refresh_attachments_mock = mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    send_notifications_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._get_new_comment_recipients',
        return_value=((), ()),
    )
    send_comment_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_comment_notification.delay',
    )
    send_mention_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_mention_notification.delay',
    )
    comment_added_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_added',
    )
    mention_created_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.mentions_created',
    )
    service = CommentService(user=account_owner)

    # act
    with pytest.raises(exceptions.CommentedNotTask) as ex:
        service.create(
            task=None,
            text=text,
        )

    # assert
    assert ex.value.message == messages.MSG_PW_0077
    clear_text_mock.assert_not_called()
    comment_created_event_mock.assert_not_called()
    refresh_attachments_mock.assert_not_called()
    send_notifications_mock.assert_not_called()
    send_comment_notification_mock.assert_not_called()
    send_mention_notification_mock.assert_not_called()
    comment_added_analysis_mock.assert_not_called()
    mention_created_analysis_mock.assert_not_called()
    task.refresh_from_db()
    assert task.contains_comments is False


def test_create__workflow_ended__raise_exception(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True,
    )
    workflow = create_test_workflow(
        account_owner,
        tasks_count=1,
        status=WorkflowStatus.DONE,
    )
    task = workflow.tasks.get(number=1)
    task.performers.add(user)

    text = 'Some text'
    clear_text = 'clear text'
    comment_created_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.comment_created_event',
    )
    clear_text_mock = mocker.patch(
        'src.processes.services.events.'
        'MarkdownService.clear',
        return_value=clear_text,
    )
    refresh_attachments_mock = mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    get_new_comment_recipients_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._get_new_comment_recipients',
        return_value=((), ()),
    )
    send_comment_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_comment_notification.delay',
    )
    send_mention_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_mention_notification.delay',
    )
    comment_added_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_added',
    )
    mention_created_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.mentions_created',
    )
    service = CommentService(user=account_owner)

    # act
    with pytest.raises(exceptions.CommentedWorkflowNotRunning) as ex:
        service.create(
            task=task,
            text=text,
        )

    # assert
    assert ex.value.message == messages.MSG_PW_0048
    clear_text_mock.assert_not_called()
    comment_created_event_mock.assert_not_called()
    refresh_attachments_mock.assert_not_called()
    get_new_comment_recipients_mock.assert_not_called()
    send_comment_notification_mock.assert_not_called()
    send_mention_notification_mock.assert_not_called()
    comment_added_analysis_mock.assert_not_called()
    mention_created_analysis_mock.assert_not_called()
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
        is_admin=True,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.performers.add(user)

    comment_created_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.comment_created_event',
    )
    clear_text_mock = mocker.patch(
        'src.processes.services.events.'
        'MarkdownService.clear',
    )
    refresh_attachments_mock = mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    get_new_comment_recipients_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._get_new_comment_recipients',
    )
    send_comment_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_comment_notification.delay',
    )
    send_mention_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_mention_notification.delay',
    )
    comment_added_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_added',
    )
    mention_created_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.mentions_created',
    )
    service = CommentService(user=account_owner)

    # act
    with pytest.raises(exceptions.CommentTextRequired) as ex:
        service.create(
            task=task,
            text=None,
        )

    # assert
    assert ex.value.message == messages.MSG_PW_0047
    clear_text_mock.assert_not_called()
    comment_created_event_mock.assert_not_called()
    refresh_attachments_mock.assert_not_called()
    get_new_comment_recipients_mock.assert_not_called()
    comment_added_analysis_mock.assert_not_called()
    send_comment_notification_mock.assert_not_called()
    send_mention_notification_mock.assert_not_called()
    mention_created_analysis_mock.assert_not_called()
    task.refresh_from_db()
    assert task.contains_comments is False


@pytest.mark.parametrize(
    'status',
    (
        TaskStatus.COMPLETED,
        TaskStatus.PENDING,
        TaskStatus.SKIPPED,
    ),
)
def test_create__inactive_task__raise_exception(mocker, status):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(
        account_owner,
        tasks_count=1,
    )
    workflow.tasks.update(status=status)
    task = workflow.tasks.first()
    text = 'Some text'
    clear_text = 'clear text'
    comment_created_event_mock = mocker.patch(
        'src.processes.services.events.'
        'WorkflowEventService.comment_created_event',
    )
    clear_text_mock = mocker.patch(
        'src.processes.services.events.'
        'MarkdownService.clear',
        return_value=clear_text,
    )
    refresh_attachments_mock = mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    get_new_comment_recipients_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._get_new_comment_recipients',
        return_value=((), ()),
    )
    send_comment_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_comment_notification.delay',
    )
    send_mention_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_mention_notification.delay',
    )
    comment_added_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_added',
    )
    mention_created_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.mentions_created',
    )
    service = CommentService(user=account_owner)

    # act
    with pytest.raises(exceptions.CommentedTaskNotActive) as ex:
        service.create(
            task=task,
            text=text,
        )

    # assert
    assert ex.value.message == messages.MSG_PW_0089
    clear_text_mock.assert_not_called()
    comment_created_event_mock.assert_not_called()
    refresh_attachments_mock.assert_not_called()
    get_new_comment_recipients_mock.assert_not_called()
    send_comment_notification_mock.assert_not_called()
    send_mention_notification_mock.assert_not_called()
    comment_added_analysis_mock.assert_not_called()
    mention_created_analysis_mock.assert_not_called()
    task.refresh_from_db()
    assert task.contains_comments is False


def test_get_new_comment_recipients__notify_users__ok():

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True,
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
        task=task,
        user=account_owner,
    )

    service = CommentService(
        user=account_owner,
        instance=event,
    )

    # act
    mentioned, notified = service._get_new_comment_recipients(task=task)

    # assert
    assert len(mentioned) == 0
    assert len(notified) == 1
    assert notified[0] == user.id


def test_get_new_comment_recipients__performer_mentioned__send_notify():

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True,
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
        task=task,
        user=account_owner,
    )

    service = CommentService(
        user=account_owner,
        instance=event,
    )

    # act
    mentioned, notified = service._get_new_comment_recipients(task=task)

    # assert
    assert len(mentioned) == 0
    assert len(notified) == 1
    assert notified[0] == user.id


def test_get_new_comment_recipients__not_performer_mentioned__send_mention():

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True,
    )
    text = f'Go [Joe (Stalin)|{user.id}] testing'
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text=text,
        clear_text=text,
        with_attachments=False,
        workflow=workflow,
        task=task,
        user=account_owner,
    )
    service = CommentService(
        user=account_owner,
        instance=event,
    )

    # act
    mentioned, notified = service._get_new_comment_recipients(task=task)

    # assert
    assert len(mentioned) == 1
    assert len(notified) == 0
    assert mentioned[0] == user.id


def test_get_updated_comment_recipients__new_mentioned__send_mention():

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True,
    )
    text = f'Go [Joe Stalin|{user.id}] testing'
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text=text,
        clear_text=text,
        with_attachments=False,
        workflow=workflow,
        task=task,
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
        account=account,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True,
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
        task=task,
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
        account=account,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    user = create_test_user(
        account=account,
        email='user@test.test',
        is_account_owner=False,
        is_admin=True,
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
        task=task,
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


@pytest.mark.parametrize(
    'status',
    (
        TaskStatus.ACTIVE,
        TaskStatus.DELAYED,
    ),
)
def test_validate_comment_action__ok(status):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user=user,
        status=WorkflowStatus.RUNNING,
    )
    task = workflow.tasks.get(number=1)
    task.status = status
    task.save()
    event = WorkflowEvent.objects.create(
        account=user.account,
        type=WorkflowEventType.COMMENT,
        text='Old text',
        with_attachments=False,
        workflow=workflow,
        task=task,
        user=user,
        status=CommentStatus.CREATED,
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
        status=WorkflowStatus.RUNNING,
    )
    task = workflow.tasks.get(number=1)
    event = WorkflowEvent.objects.create(
        account=user.account,
        type=WorkflowEventType.COMMENT,
        text='Old text',
        with_attachments=False,
        workflow=workflow,
        task=task,
        user=user,
        status=CommentStatus.DELETED,
    )
    service = CommentService(
        instance=event,
    )

    # act
    with pytest.raises(exceptions.CommentIsDeleted) as ex:
        service._validate_comment_action()

    assert ex.value.message == messages.MSG_PW_0049


def test_validate_comment_action__workflow_ended__raise_exception():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user=user,
        status=WorkflowStatus.DONE,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    event = WorkflowEvent.objects.create(
        account=user.account,
        type=WorkflowEventType.COMMENT,
        text='Old text',
        with_attachments=False,
        workflow=workflow,
        task=task,
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
    task = workflow.tasks.get(number=1)

    is_superuser = True
    auth_type = AuthTokenType.API

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Old text',
        with_attachments=False,
        workflow=workflow,
        task=task,
        task_json=TaskEventJsonSerializer(
            instance=task,
            context={'event_type': WorkflowEventType.COMMENT},
        ).data,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )
    refresh_attachments_mock = mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    get_updated_comment_recipients_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._get_updated_comment_recipients',
        return_value=(),
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )
    clear_text = 'clear text'
    clear_text_mock = mocker.patch(
        'src.processes.services.events.'
        'MarkdownService.clear',
        return_value=clear_text,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.events.'
        'BaseModelService.partial_update',
        return_value=event,
    )
    send_mention_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_mention_notification.delay',
    )
    comment_edited_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_edited',
    )

    service = CommentService(
        instance=event,
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    date_updated = timezone.now()
    mocker.patch(
        'src.processes.services.events.'
        'timezone.now',
        return_value=date_updated,
    )
    text = 'Text comment'

    # act
    result = service.update(
        text=text,
        force_save=True,
    )

    # assert
    assert result == event
    validate_comment_action_mock.assert_called_once()
    get_updated_comment_recipients_mock.assert_called_once()
    send_workflow_event_mock.assert_called_once()
    refresh_attachments_mock.assert_called_once_with(
        source=event,
        user=account_owner,
    )
    clear_text_mock.assert_called_once_with(text)
    partial_update_mock.assert_called_once_with(
        text=text,
        clear_text=clear_text,
        status=CommentStatus.UPDATED,
        updated=date_updated,
        with_attachments=False,
        force_save=True,
    )
    send_mention_notification_mock.assert_not_called()
    comment_edited_analysis_mock.assert_called_once_with(
        text=clear_text,
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow,
    )


def test_update__task_delete__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    is_superuser = True
    auth_type = AuthTokenType.API

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Old text',
        with_attachments=False,
        workflow=workflow,
        task=None,
        task_json=TaskEventJsonSerializer(
            instance=task,
            context={'event_type': WorkflowEventType.COMMENT},
        ).data,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )
    refresh_attachments_mock = mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    get_updated_comment_recipients_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._get_updated_comment_recipients',
        return_value=(),
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )
    clear_text = 'clear text'
    clear_text_mock = mocker.patch(
        'src.processes.services.events.'
        'MarkdownService.clear',
        return_value=clear_text,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.events.'
        'BaseModelService.partial_update',
        return_value=event,
    )
    send_mention_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_mention_notification.delay',
    )
    comment_edited_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_edited',
    )

    service = CommentService(
        instance=event,
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    date_updated = timezone.now()
    mocker.patch(
        'src.processes.services.events.'
        'timezone.now',
        return_value=date_updated,
    )
    text = 'Text comment'

    # act
    result = service.update(
        text=text,
        force_save=True,
    )

    # assert
    assert result == event
    validate_comment_action_mock.assert_called_once()
    get_updated_comment_recipients_mock.assert_called_once()
    send_workflow_event_mock.assert_called_once()
    refresh_attachments_mock.assert_called_once_with(
        source=event,
        user=account_owner,
    )
    clear_text_mock.assert_called_once_with(text)
    partial_update_mock.assert_called_once_with(
        text=text,
        clear_text=clear_text,
        status=CommentStatus.UPDATED,
        updated=date_updated,
        with_attachments=False,
        force_save=True,
    )
    send_mention_notification_mock.assert_not_called()
    comment_edited_analysis_mock.assert_called_once_with(
        text=clear_text,
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow,
    )


def test_update__attachments__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)

    is_superuser = True
    auth_type = AuthTokenType.API

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Old text',
        with_attachments=False,
        workflow=workflow,
        task=task,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )
    refresh_attachments_mock = mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    get_updated_comment_recipients_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._get_updated_comment_recipients',
        return_value=(),
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )
    date_updated = timezone.now()
    mocker.patch(
        'src.processes.services.events.'
        'timezone.now',
        return_value=date_updated,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.events.'
        'BaseModelService.partial_update',
        return_value=event,
    )
    clear_text_mock = mocker.patch(
        'src.processes.services.events.'
        'MarkdownService.clear',
    )
    comment_edited_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_edited',
    )
    send_mention_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_mention_notification.delay',
    )

    service = CommentService(
        instance=event,
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    attachments = [1, 2]

    # act
    result = service.update(
        attachments=attachments,
        force_save=True,
    )

    # assert
    assert result == event
    validate_comment_action_mock.assert_called_once()
    get_updated_comment_recipients_mock.assert_called_once()
    send_workflow_event_mock.assert_called_once()
    refresh_attachments_mock.assert_called_once_with(
        source=event,
        user=account_owner,
    )
    partial_update_mock.assert_called_once_with(
        with_attachments=True,
        status=CommentStatus.UPDATED,
        updated=date_updated,
        text=None,
        clear_text=None,
        force_save=True,
    )
    clear_text_mock.assert_not_called()
    comment_edited_analysis_mock.assert_called_once_with(
        text=None,
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow,
    )
    send_mention_notification_mock.assert_not_called()


@pytest.mark.parametrize(
    'data',
    (
        (
            '(![avatar.jpg](https://storage.com/dev/avatar.jpg '
            '"attachment_id:3349 entityType:image")',
        ),
        (
            '[file.txt](http://file.txt "attachment_id:4187 entityType:file")',
        ),
        (
            '[video.mp4](https://video.mp4 "attachment_id:4188 '
            'entityType:video")',
        ),
        (
            'some [video.mp4](https://video.mp4 "attachment_id:4188 '
            'entityType:video") text \n(![avatar.jpg]'
            '(https://storage.com/dev/avatar.jpg '
            '"attachment_id:3349 entityType:image")',
        ),
        (
            '[ZIP-folder.zip](https://storage.zip "attachment_id:2482")',
        ),
        (
            '[ZIP-folder.zip](https://storage.zip "attachment_id:2482")',
        ),
    ),
)
def test_update__find_attachments_in_text__ok(data, mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    is_superuser = True
    auth_type = AuthTokenType.API

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Old text',
        with_attachments=False,
        workflow=workflow,
        task=task,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )
    refresh_attachments_mock = mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    get_updated_comment_recipients_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._get_updated_comment_recipients',
        return_value=(),
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )
    date_updated = timezone.now()
    mocker.patch(
        'src.processes.services.events.'
        'timezone.now',
        return_value=date_updated,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.events.'
        'BaseModelService.partial_update',
        return_value=event,
    )
    clear_text = 'clear text'
    clear_text_mock = mocker.patch(
        'src.processes.services.events.'
        'MarkdownService.clear',
        return_value=clear_text,
    )
    comment_edited_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_edited',
    )
    send_mention_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_mention_notification.delay',
    )

    text = f'*text* \n -(123) {data}text'
    service = CommentService(
        instance=event,
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    result = service.update(
        text=text,
        force_save=True,
    )

    # assert
    assert result == event
    validate_comment_action_mock.assert_called_once()
    get_updated_comment_recipients_mock.assert_called_once()
    send_workflow_event_mock.assert_called_once()
    refresh_attachments_mock.assert_called_once_with(
        source=event,
        user=account_owner,
    )
    partial_update_mock.assert_called_once_with(
        with_attachments=True,
        status=CommentStatus.UPDATED,
        updated=date_updated,
        text=text,
        clear_text=clear_text,
        force_save=True,
    )
    clear_text_mock.assert_called_once_with(text)
    comment_edited_analysis_mock.assert_called_once_with(
        text=clear_text,
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow,
    )
    send_mention_notification_mock.assert_not_called()


@pytest.mark.parametrize(
    'text',
    (
        '([avatar.jpg](https://storage.com/dev/avatar.jpg)',
        '[file.txt](http://file.txt "attachment_id:4187 entityType:music")',
        '[video.mp4] (https://v.mp4 "attachment_id:4188 entityType:video")',
        '[video.mp4](ftp://video.mp4 "attachment_id:4188 entityType:video")',
    ),
)
def test_update__not_found_attachments_in_text__ok(text, mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    is_superuser = True
    auth_type = AuthTokenType.API

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Old text',
        with_attachments=False,
        workflow=workflow,
        task=task,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )
    refresh_attachments_mock = mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    get_updated_comment_recipients_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._get_updated_comment_recipients',
        return_value=(),
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )
    date_updated = timezone.now()
    mocker.patch(
        'src.processes.services.events.'
        'timezone.now',
        return_value=date_updated,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.events.'
        'BaseModelService.partial_update',
        return_value=event,
    )
    clear_text = 'clear text'
    clear_text_mock = mocker.patch(
        'src.processes.services.events.'
        'MarkdownService.clear',
        return_value=clear_text,
    )
    comment_edited_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_edited',
    )
    send_mention_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_mention_notification.delay',
    )

    text = f'*text* \n -(123) {text}text'
    service = CommentService(
        instance=event,
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    result = service.update(
        text=text,
        force_save=True,
    )

    # assert
    assert result == event
    validate_comment_action_mock.assert_called_once()
    get_updated_comment_recipients_mock.assert_called_once()
    send_workflow_event_mock.assert_called_once()
    refresh_attachments_mock.assert_called_once_with(
        source=event,
        user=account_owner,
    )
    partial_update_mock.assert_called_once_with(
        with_attachments=False,
        status=CommentStatus.UPDATED,
        updated=date_updated,
        text=text,
        clear_text=clear_text,
        force_save=True,
    )
    clear_text_mock.assert_called_once_with(text)
    comment_edited_analysis_mock.assert_called_once_with(
        text=clear_text,
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow,
    )
    send_mention_notification_mock.assert_not_called()


def test_update__notified_users__ok(mocker):

    # arrange
    account = create_test_account(log_api_requests=True)
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    user = create_test_user(
        is_account_owner=False,
        account=account,
        email='test@test.test',
    )

    is_superuser = True
    auth_type = AuthTokenType.API

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='text',
        with_attachments=False,
        workflow=workflow,
        task=task,
        task_json=TaskEventJsonSerializer(
            instance=task,
            context={'event_type': WorkflowEventType.COMMENT},
        ).data,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )
    refresh_attachments_mock = mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    get_updated_comment_recipients_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._get_updated_comment_recipients',
        return_value=(user.id,),
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )
    date_updated = timezone.now()
    mocker.patch(
        'src.processes.services.events.'
        'timezone.now',
        return_value=date_updated,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.events.'
        'BaseModelService.partial_update',
        return_value=event,
    )
    clear_text = 'clear text'
    clear_text_mock = mocker.patch(
        'src.processes.services.events.'
        'MarkdownService.clear',
        return_value=clear_text,
    )
    comment_edited_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_edited',
    )
    send_mention_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_mention_notification.delay',
    )

    service = CommentService(
        instance=event,
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    new_text = 'New text'
    attachments = [1, 2]

    # act
    result = service.update(
        text=new_text,
        attachments=attachments,
        force_save=True,
    )

    # assert
    assert result == event
    validate_comment_action_mock.assert_called_once()
    get_updated_comment_recipients_mock.assert_called_once()
    send_workflow_event_mock.assert_called_once()
    refresh_attachments_mock.assert_called_once_with(
        source=event,
        user=account_owner,
    )
    clear_text_mock.assert_called_once_with(new_text)
    partial_update_mock.assert_called_once_with(
        text=new_text,
        clear_text=clear_text,
        with_attachments=True,
        status=CommentStatus.UPDATED,
        updated=date_updated,
        force_save=True,
    )
    comment_edited_analysis_mock.assert_called_once_with(
        text=clear_text,
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow,
    )
    send_mention_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        logo_lg=account.logo_lg,
        author_id=account_owner.id,
        event_id=event.id,
        account_id=account.id,
        users_ids=(user.id,),
        text=event.text,
    )
    assert workflow.members.filter(id=user.id).exists()


def test_update__mentioned_users__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    user = create_test_user(
        email='text@test.text',
        account=account,
        is_account_owner=False,
    )

    is_superuser = True
    auth_type = AuthTokenType.API

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Old text',
        with_attachments=False,
        workflow=workflow,
        task=task,
        task_json=TaskEventJsonSerializer(
            instance=task,
            context={'event_type': WorkflowEventType.COMMENT},
        ).data,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )
    refresh_attachments_mock = mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    get_updated_comment_recipients_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._get_updated_comment_recipients',
        return_value=(user.id,),
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )
    date_updated = timezone.now()
    mocker.patch(
        'src.processes.services.events.'
        'timezone.now',
        return_value=date_updated,
    )
    clear_text = 'clear text'
    clear_text_mock = mocker.patch(
        'src.processes.services.events.'
        'MarkdownService.clear',
        return_value=clear_text,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.events.'
        'BaseModelService.partial_update',
        return_value=event,
    )
    comment_edited_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_edited',
    )

    service = CommentService(
        instance=event,
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    text = 'New text'

    # act
    result = service.update(
        text=text,
        force_save=True,
    )

    # assert
    assert result == event
    validate_comment_action_mock.assert_called_once()
    get_updated_comment_recipients_mock.assert_called_once()
    send_workflow_event_mock.assert_called_once()
    refresh_attachments_mock.assert_called_once_with(
        source=event,
        user=account_owner,
    )
    clear_text_mock.assert_called_once_with(text)
    partial_update_mock.assert_called_once_with(
        text=text,
        clear_text=clear_text,
        status=CommentStatus.UPDATED,
        updated=date_updated,
        with_attachments=False,
        force_save=True,
    )
    assert workflow.members.filter(id=user.id).exists()
    comment_edited_analysis_mock.assert_called_once_with(
        text=clear_text,
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow,
    )


def test_update__remove_text__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    clear_text = 'clear text'
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        task=task,
        clear_text=clear_text,
        text='Old text',
        with_attachments=True,
        workflow=workflow,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )
    refresh_attachments_mock = mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    get_updated_comment_recipients_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._get_updated_comment_recipients',
        return_value=(),
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )
    date_updated = timezone.now()
    mocker.patch(
        'src.processes.services.events.'
        'timezone.now',
        return_value=date_updated,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.events.'
        'BaseModelService.partial_update',
        return_value=event,
    )
    clear_text_mock = mocker.patch(
        'src.processes.services.events.'
        'MarkdownService.clear',
    )
    comment_edited_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_edited',
    )

    service = CommentService(
        instance=event,
        user=account_owner,
    )
    attachments = [1, 2]

    # act
    result = service.update(
        text=None,
        attachments=attachments,
        force_save=True,
    )

    # assert
    assert result == event
    validate_comment_action_mock.assert_called_once()
    get_updated_comment_recipients_mock.assert_called_once()
    send_workflow_event_mock.assert_called_once()
    refresh_attachments_mock.assert_called_once_with(
        source=event,
        user=account_owner,
    )
    partial_update_mock.assert_called_once_with(
        text=None,
        clear_text=None,
        status=CommentStatus.UPDATED,
        updated=date_updated,
        with_attachments=True,
        force_save=True,
    )
    clear_text_mock.assert_not_called()
    comment_edited_analysis_mock.assert_called_once_with(
        text=None,
        user=account_owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
    )


def test_update__remove_attachments__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text=None,
        with_attachments=True,
        workflow=workflow,
        task=task,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )
    refresh_attachments_mock = mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    get_updated_comment_recipients_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._get_updated_comment_recipients',
        return_value=(),
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )
    date_updated = timezone.now()
    mocker.patch(
        'src.processes.services.events.'
        'timezone.now',
        return_value=date_updated,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.events.'
        'BaseModelService.partial_update',
        return_value=event,
    )
    clear_text = 'clear text'
    clear_text_mock = mocker.patch(
        'src.processes.services.events.'
        'MarkdownService.clear',
        return_value=clear_text,
    )
    comment_edited_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_edited',
    )
    text = 'text'

    service = CommentService(
        instance=event,
        user=account_owner,
    )

    # act
    result = service.update(
        text=text,
        force_save=True,
    )

    # assert
    assert result == event
    validate_comment_action_mock.assert_called_once()
    get_updated_comment_recipients_mock.assert_called_once_with()
    send_workflow_event_mock.assert_called_once()
    refresh_attachments_mock.assert_called_once_with(
        source=event,
        user=account_owner,
    )
    clear_text_mock.assert_called_once_with(text)
    partial_update_mock.assert_called_once_with(
        text=text,
        clear_text=clear_text,
        status=CommentStatus.UPDATED,
        updated=date_updated,
        with_attachments=False,
        force_save=True,
    )
    comment_edited_analysis_mock.assert_called_once_with(
        text=clear_text,
        user=account_owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
    )


def test_update__remove_text__raise_exception(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='text',
        with_attachments=False,
        workflow=workflow,
        task=task,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )
    refresh_attachments_mock = mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    get_new_comment_recipients_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._get_new_comment_recipients',
        return_value=((), ()),
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.events.'
        'BaseModelService.partial_update',
    )
    comment_edited_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_edited',
    )
    clear_text_mock = mocker.patch(
        'src.processes.services.events.'
        'MarkdownService.clear',
    )

    service = CommentService(
        instance=event,
        user=account_owner,
    )

    # act
    with pytest.raises(exceptions.CommentTextRequired) as ex:
        service.update(
            text=None,
            force_save=True,
        )

    # assert
    assert ex.value.message == messages.MSG_PW_0047
    validate_comment_action_mock.assert_called_once()
    get_new_comment_recipients_mock.assert_not_called()
    send_workflow_event_mock.assert_not_called()
    refresh_attachments_mock.assert_not_called()
    clear_text_mock.assert_not_called()
    partial_update_mock.assert_not_called()
    comment_edited_analysis_mock.assert_not_called()


def test_update__remove_attachment__raise_exception(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text=None,
        with_attachments=True,
        workflow=workflow,
        task=task,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )
    refresh_attachments_mock = mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    get_updated_comment_recipients_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._get_updated_comment_recipients',
        return_value=(),
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.events.'
        'BaseModelService.partial_update',
    )
    comment_edited_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_edited',
    )

    service = CommentService(
        instance=event,
        user=account_owner,
    )

    # act
    with pytest.raises(exceptions.CommentTextRequired) as ex:
        service.update(
            attachments=None,
            force_save=True,
        )

    # assert
    assert ex.value.message == messages.MSG_PW_0047
    validate_comment_action_mock.assert_called_once()
    get_updated_comment_recipients_mock.assert_not_called()
    send_workflow_event_mock.assert_not_called()
    refresh_attachments_mock.assert_not_called()
    partial_update_mock.assert_not_called()
    comment_edited_analysis_mock.assert_not_called()


@pytest.mark.parametrize(
    'status',
    (
        TaskStatus.COMPLETED,
        TaskStatus.PENDING,
        TaskStatus.SKIPPED,
    ),
)
def test_update_inactive_task__raise_exception(status, mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.status = status
    task.save()

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='text',
        with_attachments=False,
        workflow=workflow,
        task=task,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )
    refresh_attachments_mock = mocker.patch(
        'src.processes.services.events.refresh_attachments',
    )
    get_updated_comment_recipients_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._get_new_comment_recipients',
        return_value=((), ()),
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.events.'
        'BaseModelService.partial_update',
    )
    comment_edited_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_edited',
    )
    clear_text_mock = mocker.patch(
        'src.processes.services.events.'
        'MarkdownService.clear',
    )

    service = CommentService(
        instance=event,
        user=account_owner,
    )

    # act
    with pytest.raises(exceptions.CommentedTaskNotActive) as ex:
        service.update(
            text='text',
            force_save=True,
        )

    # assert
    assert ex.value.message == messages.MSG_PW_0089
    validate_comment_action_mock.assert_called_once()
    get_updated_comment_recipients_mock.assert_not_called()
    send_workflow_event_mock.assert_not_called()
    refresh_attachments_mock.assert_not_called()
    clear_text_mock.assert_not_called()
    partial_update_mock.assert_not_called()
    comment_edited_analysis_mock.assert_not_called()


def test_delete__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Old text',
        clear_text='Clear text',
        with_attachments=False,
        workflow=workflow,
        task=task,
        user=account_owner,
    )
    create_test_attachment(
        account=account,
        file_id='first_template_file.png',
        workflow=workflow,
        event=event,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.events.'
        'BaseModelService.partial_update',
        return_value=event,
    )
    comment_deleted_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_deleted',
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )

    service = CommentService(
        instance=event,
        user=account_owner,
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
        force_save=True,
    )
    assert event.storage_attachments.count() == 0
    comment_deleted_analysis_mock.assert_called_once_with(
        text=event.clear_text,
        user=account_owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
    )
    send_workflow_event_mock.assert_called_once()


def test_delete__task_delete__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Old text',
        clear_text='Clear text',
        with_attachments=False,
        workflow=workflow,
        task=None,
        user=account_owner,
    )
    Attachment.objects.create(
        file_id='test_file_workflow_123.png',
        account=account,
        source_type=SourceType.WORKFLOW,
        access_type=AccessType.RESTRICTED,
        task=None,
        workflow=workflow,
        event=event,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.events.'
        'BaseModelService.partial_update',
        return_value=event,
    )
    comment_deleted_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_deleted',
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )

    service = CommentService(
        instance=event,
        user=account_owner,
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
        force_save=True,
    )
    assert event.storage_attachments.count() == 0
    comment_deleted_analysis_mock.assert_called_once_with(
        text=event.clear_text,
        user=account_owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
    )
    send_workflow_event_mock.assert_called_once()


@pytest.mark.parametrize(
    'status',
    (
        TaskStatus.COMPLETED,
        TaskStatus.PENDING,
        TaskStatus.SKIPPED,
    ),
)
def test_delete_inactive_task__raise_exception(status, mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.status = status
    task.save()

    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Old text',
        clear_text='Clear text',
        with_attachments=False,
        workflow=workflow,
        task=task,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.events.'
        'BaseModelService.partial_update',
        return_value=event,
    )
    comment_deleted_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_deleted',
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )

    service = CommentService(
        instance=event,
        user=account_owner,
    )

    # act
    with pytest.raises(exceptions.CommentedTaskNotActive) as ex:
        service.delete()

    # assert
    assert ex.value.message == messages.MSG_PW_0089
    validate_comment_action_mock.assert_called_once()
    partial_update_mock.assert_not_called()
    comment_deleted_analysis_mock.assert_not_called()
    send_workflow_event_mock.assert_not_called()


def test_watched__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=account,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Comment text',
        with_attachments=False,
        workflow=workflow,
        task=task,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )

    service = CommentService(
        instance=event,
        user=user,
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
    task = workflow.tasks.get(number=1)
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Comment text',
        with_attachments=False,
        workflow=workflow,
        task=task,
        user=account_owner,
    )

    service = CommentService(
        instance=event,
        user=account_owner,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
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
        account=account,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Comment text',
        with_attachments=False,
        workflow=workflow,
        task=task,
        user=account_owner,
    )
    event.watched = [
        {
            'date':  timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'user_id': user.id,
        },
    ]
    event.save()
    service = CommentService(
        instance=event,
        user=user,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
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
        account=account,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
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
    create_reaction_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_reaction_added',
    )
    send_reaction_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_reaction_notification.delay',
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )
    reaction = ':dumb face:'
    is_superuser = True
    auth_type = AuthTokenType.API
    service = CommentService(
        instance=event,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )

    # act
    service.create_reaction(reaction)

    # assert
    validate_comment_action_mock.assert_called_once()
    event.refresh_from_db()
    assert event.reactions[reaction] == [user.id]
    create_reaction_analysis_mock.assert_called_once_with(
        text=reaction,
        user=user,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    send_workflow_event_mock.assert_called_once()
    send_reaction_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
        author_id=user.id,
        event_id=event.id,
        user_id=account_owner.id,
        user_email=account_owner.email,
        author_name=account_owner.name,
        reaction=reaction,
    )


def test_create_reaction__long_comment__cut_off(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=account,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='a',
        clear_text='a'*41,
        with_attachments=False,
        workflow=workflow,
        user=account_owner,
        task=task,
    )
    create_reaction_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_reaction_added',
    )
    send_reaction_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_reaction_notification.delay',
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )
    reaction = ':dumb face:'
    is_superuser = True
    auth_type = AuthTokenType.API
    service = CommentService(
        instance=event,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )

    # act
    service.create_reaction(reaction)

    # assert
    validate_comment_action_mock.assert_called_once()
    event.refresh_from_db()
    assert event.reactions[reaction] == [user.id]
    create_reaction_analysis_mock.assert_called_once_with(
        text=reaction,
        user=user,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    send_workflow_event_mock.assert_called_once()
    send_reaction_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        author_id=user.id,
        event_id=event.id,
        account_id=account.id,
        user_id=account_owner.id,
        user_email=account_owner.email,
        logo_lg=account.logo_lg,
        author_name=account_owner.name,
        reaction=reaction,
    )


def test_create_reaction__not_comment_text__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=account,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        with_attachments=True,
        workflow=workflow,
        user=account_owner,
        task=task,
    )
    create_reaction_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_reaction_added',
    )
    send_reaction_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_reaction_notification.delay',
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )
    reaction = ':dumb face:'
    is_superuser = True
    auth_type = AuthTokenType.API
    service = CommentService(
        instance=event,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )

    # act
    service.create_reaction(reaction)

    # assert
    validate_comment_action_mock.assert_called_once()
    event.refresh_from_db()
    assert event.reactions[reaction] == [user.id]
    create_reaction_analysis_mock.assert_called_once_with(
        text=reaction,
        user=user,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    send_workflow_event_mock.assert_called_once()
    send_reaction_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        author_id=user.id,
        event_id=event.id,
        account_id=account.id,
        user_id=account_owner.id,
        user_email=account_owner.email,
        logo_lg=account.logo_lg,
        author_name=account_owner.name,
        reaction=reaction,
    )


def test_create_reaction__second__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=account,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
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
    create_reaction_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_reaction_added',
    )
    send_reaction_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_reaction_notification.delay',
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    service = CommentService(
        instance=event,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )

    # act
    service.create_reaction(reaction)

    # assert
    validate_comment_action_mock.assert_called_once()
    event.refresh_from_db()
    assert event.reactions[reaction] == [account_owner.id, user.id]
    create_reaction_analysis_mock.assert_called_once_with(
        text=reaction,
        user=user,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    send_workflow_event_mock.assert_called_once()
    send_reaction_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        author_id=user.id,
        user_id=account_owner.id,
        user_email=account_owner.email,
        logo_lg=account.logo_lg,
        event_id=event.id,
        account_id=account.id,
        author_name=account_owner.name,
        reaction=reaction,
    )


def test_create_reaction__duplicate__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=account,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
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

    create_reaction_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_reaction_added',
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )
    send_reaction_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_reaction_notification.delay',
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    service = CommentService(
        instance=event,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )

    # act
    service.create_reaction(reaction)

    # assert
    validate_comment_action_mock.assert_called_once()
    event.refresh_from_db()
    assert event.reactions[reaction] == [user.id]
    create_reaction_analysis_mock.assert_not_called()
    send_workflow_event_mock.assert_not_called()
    send_reaction_notification_mock.assert_not_called()


def test_delete_reaction__last__remove_reaction(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=account,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    reaction = ':dumb face:'
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Comment text',
        with_attachments=False,
        workflow=workflow,
        task=task,
        user=account_owner,
    )
    event.reactions[reaction] = [user.id]
    event.save()

    reaction_deleted_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_reaction_deleted',
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    service = CommentService(
        instance=event,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )

    # act
    service.delete_reaction(reaction)

    # assert
    validate_comment_action_mock.assert_called_once()
    event.refresh_from_db()
    assert reaction not in event.reactions
    reaction_deleted_analysis_mock.assert_called_once_with(
        text=reaction,
        user=user,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    send_workflow_event_mock.assert_called_once()


def test_delete_reaction__not_last__remove_only_user_id(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=account,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    reaction = ':dumb face:'
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Comment text',
        with_attachments=False,
        workflow=workflow,
        task=task,
        user=account_owner,
    )
    event.reactions[reaction] = [user.id, account_owner.id]
    event.save()

    reaction_deleted_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_reaction_deleted',
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    service = CommentService(
        instance=event,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )

    # act
    service.delete_reaction(reaction)

    # assert
    validate_comment_action_mock.assert_called_once()
    event.refresh_from_db()
    assert event.reactions == {reaction: [account_owner.id]}
    reaction_deleted_analysis_mock.assert_called_once_with(
        text=reaction,
        user=user,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    send_workflow_event_mock.assert_called_once()


def test_delete_reaction__not_exist_reaction__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=account,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    reaction = ':dumb face:'
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Comment text',
        with_attachments=False,
        workflow=workflow,
        task=task,
        user=account_owner,
    )

    reaction_deleted_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_reaction_deleted',
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    service = CommentService(
        instance=event,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )

    # act
    service.delete_reaction(reaction)

    # assert
    validate_comment_action_mock.assert_called_once()
    event.refresh_from_db()
    assert event.reactions == {}
    reaction_deleted_analysis_mock.assert_not_called()
    send_workflow_event_mock.assert_not_called()


def test_delete_reaction__not_exist_user_id__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=account,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    reaction = ':dumb face:'
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Comment text',
        with_attachments=False,
        workflow=workflow,
        task=task,
        user=account_owner,
    )

    reaction_deleted_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_reaction_deleted',
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    service = CommentService(
        instance=event,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )

    # act
    service.delete_reaction(reaction)

    # assert
    validate_comment_action_mock.assert_called_once()
    event.refresh_from_db()
    assert event.reactions == {}
    reaction_deleted_analysis_mock.assert_not_called()
    send_workflow_event_mock.assert_not_called()


def test_create_reaction__to_yourself_comment__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(is_account_owner=True, account=account)
    user = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=account,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Comment text',
        clear_text='Clear text',
        with_attachments=False,
        workflow=workflow,
        user=user,
        task=task,
    )
    reaction_deleted_analysis_mock = mocker.patch(
        'src.processes.services.events.'
        'AnalyticService.comment_reaction_added',
    )
    send_reaction_notification_mock = mocker.patch(
        'src.processes.services.events.'
        'send_reaction_notification.delay',
    )
    send_workflow_event_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._send_workflow_event',
    )
    reaction = ':dumb face:'
    is_superuser = True
    auth_type = AuthTokenType.API
    service = CommentService(
        instance=event,
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser,
    )
    validate_comment_action_mock = mocker.patch(
        'src.processes.services.events.'
        'CommentService._validate_comment_action',
    )

    # act
    service.create_reaction(reaction)

    # assert
    validate_comment_action_mock.assert_called_once()
    event.refresh_from_db()
    assert event.reactions[reaction] == [user.id]
    reaction_deleted_analysis_mock.assert_called_once_with(
        text=reaction,
        user=user,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    send_workflow_event_mock.assert_called_once()
    send_reaction_notification_mock.assert_not_called()


@pytest.mark.parametrize(
    'name',
    [
        'John',
        'John *S*',
        'John (Smith)',
        'John [Smith]',
        'John |Smith|',
        'John \\Smith\\',
        'John }Smith{',
        'John )Smith(',
        'User ]Smith[',
    ],
)
def test_get_mentioned_users_ids_with_parentheses__ok(name):

    # arrange
    account_owner = create_test_owner()
    user = create_test_user(
        account=account_owner.account,
        email='user@test.test',
        is_account_owner=False,
    )
    service = CommentService(user=account_owner)
    text = f'Hello [{name}|{user.id}], please check this task.'

    # act
    mentioned_ids = service._get_mentioned_users_ids(
        text=text,
        exclude_ids=[],
    )

    # assert
    assert len(mentioned_ids) == 1
    assert mentioned_ids[0] == user.id


def test_get_mentioned_users_ids__check_timeout__ok():
    account_owner = create_test_owner()
    user = create_test_user(
        account=account_owner.account,
        email='user@test.test',
        is_account_owner=False,
    )
    service = CommentService(user=account_owner)
    text = ('\n [SQL for users  - '
            'M. Graber [2014].pdf](https://storage.googleapis.com/'
            '2756_bn9i0garicp520a9/Lo8VohifLmtLGQq0B5eGnwlfc896'
            'X_SQL9fhrew09wehv2hhhf09whreoif[phhh9HObnvcpedosn'
            '.poifhvc20phv02pjmv29jmv2v2vkj2mwvj2wviumw2vj'
            '.pdf "attachment_id:4782 entityType:file")\n\n'
            f'test [Tim Berzon|{user.id}] ')

    # act
    mentioned_ids = service._get_mentioned_users_ids(
        text=text,
        exclude_ids=[],
    )

    # assert
    assert len(mentioned_ids) == 1
    assert mentioned_ids[0] == user.id
