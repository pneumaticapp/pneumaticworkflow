import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.messages import workflow as messages
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template,
    create_test_workflow,
    create_test_guest,
    create_test_account,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.api_v2.services import WorkflowEventService
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService
)
from pneumatic_backend.processes.enums import (
    WorkflowStatus,
    FieldType,
    DirectlyStatus
)
from pneumatic_backend.processes.models import (
    Task,
    Delay,
    TaskPerformer,
    WorkflowEvent,
    Workflow,
)
from pneumatic_backend.processes.services import exceptions
from pneumatic_backend.processes.api_v2.services.task.task import TaskService
from pneumatic_backend.processes.models import (
    TaskField,
)
from pneumatic_backend.processes.api_v2.services.task.field import (
    TaskFieldService
)


UserModel = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "status",
    [
        WorkflowStatus.RUNNING,
        WorkflowStatus.DONE,
        WorkflowStatus.DELAYED,
    ],
)
def test_terminate__all_status__ok(status, mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user,
        tasks_count=1,
        status=status
    )
    current_task = workflow.current_task_instance
    service = WorkflowActionService(user=user)
    send_removed_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_removed_task_notification'
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'workflows_terminated'
    )
    WorkflowEventService.task_started_event(current_task)

    deactivate_guest_cache_mock = mocker.patch(
        'pneumatic_backend.authentication.services.'
        'GuestJWTAuthService.deactivate_task_guest_cache'
    )

    # act
    service.terminate_workflow(workflow=workflow)

    # assert
    workflow.refresh_from_db()
    assert not Workflow.objects.filter(id=workflow.id).exists()
    assert not WorkflowEvent.objects.filter(workflow=workflow).exists()
    assert not Task.objects.filter(workflow=workflow).exists()
    assert not Delay.objects.filter(task=current_task).exists()
    send_removed_task_notification_mock.assert_called_once_with(
        task=current_task,
        user_ids=(user.id,)
    )
    deactivate_guest_cache_mock.assert_called_once_with(
        task_id=current_task.id
    )
    analytics_mock.assert_called_once_with(
        user=user,
        workflow=workflow,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )


def test_terminate_notification__for_not_completed_only(
    mocker
):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    deleted_performer = create_test_user(
        account=account,
        email='user_2@test.test',
        is_account_owner=False
    )
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=deleted_performer.id,
        directly_status=DirectlyStatus.DELETED
    )
    completed_performer = create_test_user(
        account=account,
        email='user_3@test.test',
        is_account_owner=False
    )
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=completed_performer.id,
        is_completed=True
    )
    guest = create_test_guest(account=account)
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    user_4 = create_test_user(
        account=account,
        email='user_4@test.test',
        is_account_owner=False
    )
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=user_4.id,
    )

    service = WorkflowActionService(user=user)
    send_removed_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_removed_task_notification'
    )
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'workflows_terminated'
    )
    mocker.patch(
        'pneumatic_backend.authentication.services.'
        'GuestJWTAuthService.deactivate_task_guest_cache'
    )

    # act
    service.terminate_workflow(workflow=workflow)

    # assert
    send_removed_task_notification_mock.assert_called_once_with(
        task=task,
        user_ids=(user.id, user_4.id)
    )


def test_delay_workflow__ok(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.current_task_instance
    delay = Delay.objects.create(
        task=task,
        duration=timedelta(hours=1)
    )
    workflow_delay_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'WorkflowEventService.workflow_delay_event'
    )

    # act
    WorkflowActionService().delay_workflow(
        workflow=workflow,
        delay=delay
    )

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.DELAYED
    delay.refresh_from_db()
    assert delay.start_date is not None
    workflow_delay_event_mock.assert_called_once_with(
        workflow=workflow,
        delay=delay
    )


def test_force_delay_workflow__update_existent__ok(mocker):

    # arrange
    account_owner = create_test_user(is_account_owner=True)
    user = create_test_user(
        is_account_owner=False,
        email='t@t.t',
        account=account_owner.account
    )
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.current_task_instance

    now = timezone.now()
    old_duration = timedelta(hours=1)
    delay = Delay.objects.create(
        task=task,
        duration=old_duration,
        start_date=now
    )
    new_duration = timedelta(days=7)
    new_end_date = now + new_duration
    is_superuser = True
    auth_type = AuthTokenType.USER
    force_delay_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'force_delay_workflow_event'
    )
    send_notifications_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks.'
        'send_delayed_workflow_notification.delay'
    )
    send_removed_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_removed_task_notification'
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.workflow_delayed'
    )
    mocker.patch(
        'pneumatic_backend.processes.'
        'services.workflow_action.timezone.now',
        return_value=now
    )
    service = WorkflowActionService(
        user=account_owner,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser
    )

    # act
    service.force_delay_workflow(
        workflow=workflow,
        date=new_end_date,
    )

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.DELAYED
    delay.refresh_from_db()
    assert delay.start_date == now
    assert delay.duration == new_duration
    assert delay.estimated_end_date == now + new_duration
    assert delay.directly_status == DirectlyStatus.CREATED
    force_delay_workflow_event_mock.assert_called_once_with(
        user=account_owner,
        workflow=workflow,
        delay=delay,
    )
    send_notifications_mock.assert_called_once_with(
        logging=account_owner.account.log_api_requests,
        task_id=task.id,
        author_id=account_owner.id,
        user_id=user.id,
        account_id=user.account_id,
        workflow_name=workflow.name,
    )
    send_removed_task_notification_mock.assert_called_once_with(
        user_ids=(user.id,),
        task=task,
    )
    analytics_mock.assert_called_once_with(
        user=account_owner,
        workflow=workflow,
        task=task,
        is_superuser=is_superuser,
        auth_type=auth_type,
        duration=new_duration
    )


def test_force_delay_workflow__notifications__for_not_completed_only(mocker):

    # arrange
    account = create_test_account()
    user = create_test_user(
        is_account_owner=True,
        email='first@test.test',
        account=account
    )
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.current_task_instance
    deleted_performer = create_test_user(
        is_account_owner=False,
        email='deleted@test.test',
        account=account
    )
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=deleted_performer.id,
        directly_status=DirectlyStatus.DELETED
    )
    completed_performer = create_test_user(
        is_account_owner=False,
        email='completed@test.test',
        account=account
    )
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=completed_performer.id,
        is_completed=True
    )
    guest = create_test_guest(account=account)
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )

    now = timezone.now()
    old_duration = timedelta(hours=1)
    Delay.objects.create(
        task=task,
        duration=old_duration,
        start_date=now
    )
    new_duration = timedelta(days=7)
    new_end_date = now + new_duration
    is_superuser = True
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'force_delay_workflow_event'
    )
    send_notifications_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks.'
        'send_delayed_workflow_notification.delay'
    )
    send_removed_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_removed_task_notification'
    )
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.workflow_delayed'
    )
    mocker.patch(
        'pneumatic_backend.processes.'
        'services.workflow_action.timezone.now',
        return_value=now
    )
    service = WorkflowActionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser
    )

    # act
    service.force_delay_workflow(
        workflow=workflow,
        date=new_end_date,
    )

    # assert
    send_notifications_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        task_id=task.id,
        author_id=user.id,
        user_id=user.id,
        account_id=user.account_id,
        workflow_name=workflow.name,
    )
    send_removed_task_notification_mock.assert_called_once_with(
        user_ids=(user.id,),
        task=task,
    )


def test_force_delay_workflow__create_new__ok(mocker):

    # arrange
    account = create_test_account(log_api_requests=True)
    account_owner = create_test_user(
        account=account,
        is_account_owner=True
    )
    user = create_test_user(
        is_account_owner=False,
        email='t@t.t',
        account=account
    )
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.current_task_instance
    now = timezone.now()

    # ended delay
    Delay.objects.create(
        task=task,
        duration=timedelta(days=14),
        start_date=now,
        end_date=now + timedelta(days=14)
    )
    new_duration = timedelta(days=7)
    new_end_date = now + new_duration
    is_superuser = True
    auth_type = AuthTokenType.USER
    force_delay_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'force_delay_workflow_event'
    )
    send_notifications_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks.'
        'send_delayed_workflow_notification.delay'
    )
    send_removed_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_removed_task_notification'
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.workflow_delayed'
    )
    mocker.patch(
        'pneumatic_backend.processes.'
        'services.workflow_action.timezone.now',
        return_value=now
    )
    service = WorkflowActionService(
        user=account_owner,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser
    )

    # act
    service.force_delay_workflow(
        workflow=workflow,
        date=new_end_date,
    )

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.DELAYED
    delay = Delay.objects.get(task=task, end_date=None)
    assert delay.start_date == now
    assert delay.duration == new_duration
    assert delay.estimated_end_date == now + new_duration
    assert delay.directly_status == DirectlyStatus.CREATED
    force_delay_workflow_event_mock.assert_called_once_with(
        user=account_owner,
        workflow=workflow,
        delay=delay,
    )
    send_notifications_mock.assert_called_once_with(
        logging=account.log_api_requests,
        task_id=task.id,
        author_id=account_owner.id,
        user_id=user.id,
        account_id=user.account_id,
        workflow_name=workflow.name,
    )
    send_removed_task_notification_mock.assert_called_once_with(
        user_ids=(user.id,),
        task=task,
    )
    analytics_mock.assert_called_once_with(
        user=account_owner,
        workflow=workflow,
        task=task,
        is_superuser=is_superuser,
        auth_type=auth_type,
        duration=new_duration
    )


def test_force_resume_workflow__ok(mocker):

    # arrange
    account_owner = create_test_user(is_account_owner=True)
    user = create_test_user(
        is_account_owner=False,
        email='t@t.t',
        account=account_owner.account
    )
    workflow = create_test_workflow(user=user, tasks_count=1)
    workflow.status = WorkflowStatus.DELAYED
    workflow.save(update_fields=['status'])
    task = workflow.current_task_instance
    now = timezone.now()
    duration = timedelta(days=7)
    end_date = now + timedelta(days=1)
    delay = Delay.objects.create(
        task=task,
        duration=duration,
        start_date=now,
    )
    force_resume_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'force_resume_workflow_event'
    )
    send_resumed_workflow_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks.'
        'send_resumed_workflow_notification.delay'
    )
    mocker.patch(
        'pneumatic_backend.processes.'
        'services.workflow_action.timezone.now',
        return_value=end_date
    )
    continue_task_mock = mocker.patch(
        'pneumatic_backend.processes.'
        'services.workflow_action.WorkflowActionService.continue_task',
        return_value=now
    )
    service = WorkflowActionService(user=account_owner)

    # act
    service.force_resume_workflow(workflow=workflow)

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.RUNNING
    delay.refresh_from_db()
    assert delay.start_date == now
    assert delay.duration == duration
    assert delay.estimated_end_date == now + duration
    assert delay.end_date == end_date
    force_resume_workflow_event_mock.assert_called_once_with(
        workflow=workflow,
        user=account_owner,
    )
    send_resumed_workflow_notification_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        task_id=task.id,
        author_id=account_owner.id,
        account_id=user.account_id,
        workflow_name=workflow.name,
    )
    continue_task_mock.assert_called_once_with(
        workflow=workflow,
        task=task,
    )


def test_force_resume_workflow__running_workflow__skip(mocker):

    # arrange
    account_owner = create_test_user(is_account_owner=True)
    user = create_test_user(
        is_account_owner=False,
        email='t@t.t',
        account=account_owner.account
    )
    workflow = create_test_workflow(user=user, tasks_count=1)
    force_resume_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'force_resume_workflow_event'
    )
    send_resumed_workflow_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks.'
        'send_resumed_workflow_notification.delay'
    )
    continue_task_mock = mocker.patch(
        'pneumatic_backend.processes.'
        'services.workflow_action.WorkflowActionService.continue_task',
    )
    service = WorkflowActionService(user=account_owner)

    # act
    service.force_resume_workflow(workflow=workflow)

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.RUNNING
    force_resume_workflow_event_mock.assert_not_called()
    send_resumed_workflow_notification_mock.assert_not_called()
    continue_task_mock.assert_not_called()


@pytest.mark.parametrize('status', WorkflowStatus.END_STATUSES)
def test_force_resume_workflow__ended_workflow__skip(status, mocker):

    # arrange
    account_owner = create_test_user(is_account_owner=True)
    user = create_test_user(
        is_account_owner=False,
        email='t@t.t',
        account=account_owner.account
    )
    workflow = create_test_workflow(user=user, tasks_count=1)
    workflow.status = status
    workflow.save(update_fields=['status'])
    force_resume_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'force_resume_workflow_event'
    )
    send_resumed_workflow_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks.'
        'send_resumed_workflow_notification.delay'
    )
    continue_task_mock = mocker.patch(
        'pneumatic_backend.processes.'
        'services.workflow_action.WorkflowActionService.continue_task',
    )
    service = WorkflowActionService(user=account_owner)

    # act
    with pytest.raises(exceptions.ResumeNotDelayedWorkflow) as ex:
        service.force_resume_workflow(workflow=workflow)

    # assert
    assert ex.value.message == messages.MSG_PW_0003
    force_resume_workflow_event_mock.assert_not_called()
    send_resumed_workflow_notification_mock.assert_not_called()
    continue_task_mock.assert_not_called()


def test_continue_task__current_task_not_started__ok(mocker):

    # arrange
    logo_lg = 'https://some.com/image.png'
    account = create_test_account(logo_lg=logo_lg, log_api_requests=True)
    photo = 'http://image.com/avatar.png'
    workflow_starter = create_test_user(
        account=account,
        is_account_owner=False,
        email='wf@starter.com',
        photo=photo
    )
    user = create_test_user(account=account)
    template = create_test_template(
        user=workflow_starter,
        name='Some template',
        tasks_count=3,
    )
    workflow = create_test_workflow(
        user=workflow_starter,
        template=template
    )
    deleted_performer = create_test_user(
        is_account_owner=False,
        email='deleted@test.test',
        account=account
    )
    unsubscribed_performer = create_test_user(
        is_account_owner=False,
        email='unsubscribed@test.test',
        account=account,
        is_new_tasks_subscriber=False,
    )
    guest = create_test_guest(account=user.account)

    workflow.current_task = 2
    workflow.is_urgent = True
    workflow.save(update_fields=['current_task', 'is_urgent'])
    prev_task = workflow.tasks.get(number=1)
    next_task = workflow.tasks.get(number=3)
    TaskPerformer.objects.filter(task=next_task).update(
        is_completed=True,
        date_completed=timezone.now()
    )

    task = workflow.tasks.get(number=2)
    task.performers.clear()
    task.performers.add(user)
    task.due_date = timezone.now() + timedelta(hours=1)
    task.save(update_fields=['due_date'])
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    # users who should not be on the workflow members
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=deleted_performer.id,
        directly_status=DirectlyStatus.DELETED
    )
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=unsubscribed_performer.id,
        directly_status=DirectlyStatus.CREATED
    )
    task_started_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'task_started_event'
    )
    send_ws_new_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_new_task_notification'
    )
    send_new_task_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.'
        'tasks.send_new_task_notification.delay'
    )
    now = timezone.now()
    mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.timezone.now',
        return_value=now
    )
    set_due_date_from_template_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.TaskService.'
        'set_due_date_from_template'
    )
    delete_task_guest_cache_mock = mocker.patch(
        'pneumatic_backend.authentication.services.'
        'GuestJWTAuthService.delete_task_guest_cache'
    )
    sync = True
    service = WorkflowActionService(sync=sync)

    # act
    service.continue_task(
        workflow=workflow,
        task=task,
        is_returned=False,
    )

    # assert
    workflow.refresh_from_db()
    task.refresh_from_db()
    assert task.is_urgent is True
    assert task.is_completed is False
    assert task.date_completed is None
    assert task.date_started == now
    assert not TaskPerformer.objects.filter(
        task=next_task,
        is_completed=True,
    ).exclude(date_completed=None).exists()
    assert not workflow.members.filter(
        id=guest.id
    ).exists()
    task_started_event_mock.assert_called_once_with(task)
    send_ws_new_task_notification_mock.assert_called_once_with(
        task=task,
        sync=sync
    )
    set_due_date_from_template_mock.assert_called_once()
    send_new_task_notification_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        recipients=[
            (user.id, user.email),
            (guest.id, guest.email)
        ],
        task_id=task.id,
        task_name=task.name,
        task_description=task.description,
        workflow_name=workflow.name,
        template_name=template.name,
        workflow_starter_name=workflow_starter.name,
        workflow_starter_photo=workflow_starter.photo,
        due_date_timestamp=task.due_date.timestamp(),
        logo_lg=logo_lg,
        is_returned=False,
    )
    delete_task_guest_cache_mock.has_calls([
        mocker.call(task_id=prev_task.id),
        mocker.call(task_id=task.id)
    ])


def test_continue_task__current_started__ok(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=3)
    performer = create_test_user(
        is_account_owner=False,
        email='performer@t.t',
        account=user.account
    )
    deleted_performer = create_test_user(
        is_account_owner=False,
        email='deleted@t.t',
        account=user.account
    )
    guest = create_test_guest(account=user.account)
    workflow.current_task = 2
    workflow.is_urgent = True
    workflow.save(update_fields=['current_task', 'is_urgent'])
    prev_task = workflow.tasks.get(number=1)
    task = workflow.current_task_instance
    date_started = timezone.now()
    task.date_started = date_started
    task.date_first_started = date_started
    task.save(update_fields=['date_started', 'date_first_started'])
    next_task = workflow.tasks.get(number=3)
    TaskPerformer.objects.filter(task=next_task).update(
        is_completed=True,
        date_completed=timezone.now()
    )
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=performer.id,
    )
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    # users who should not be on the workflow members
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=deleted_performer.id,
        directly_status=DirectlyStatus.DELETED
    )
    task_started_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'task_started_event'
    )
    send_ws_new_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_new_task_notification'
    )
    send_new_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'send_new_task_notification.delay'
    )
    now = timezone.now()
    mocker.patch(
        'pneumatic_backend.processes.'
        'services.workflow_action.timezone.now',
        return_value=now
    )
    delete_task_guest_cache_mock = mocker.patch(
        'pneumatic_backend.authentication.services.'
        'GuestJWTAuthService.delete_task_guest_cache'
    )
    sync = True
    service = WorkflowActionService(sync=sync)

    # act
    service.continue_task(
        workflow=workflow,
        task=task,
        is_returned=False,
    )

    # assert
    workflow.refresh_from_db()
    task.refresh_from_db()
    assert task.is_urgent is True
    assert task.is_completed is False
    assert task.date_completed is None
    assert task.date_started == now
    assert not TaskPerformer.objects.filter(
        task=next_task,
        is_completed=True,
    ).exclude(date_completed=None).exists()
    assert not workflow.members.filter(
        id=guest.id
    ).exists()
    task_started_event_mock.assert_not_called()
    send_ws_new_task_notification_mock.assert_called_once_with(
        task=task,
        sync=sync
    )
    send_new_task_notification_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        recipients=[
            (user.id, user.email),
            (performer.id, performer.email),
            (guest.id, guest.email)
        ],
        task_id=task.id,
        task_name=task.name,
        task_description=task.description,
        workflow_name=workflow.name,
        template_name=workflow.template.name,
        workflow_starter_name=user.name,
        workflow_starter_photo=None,
        due_date_timestamp=None,
        logo_lg=None,
        is_returned=False,
    )
    delete_task_guest_cache_mock.has_calls([
        mocker.call(task_id=prev_task.id),
        mocker.call(task_id=task.id)
    ])


def test_continue_task__current_started_task_1_with_performer_and_guest__ok(
    mocker
):

    # arrange
    owner = create_test_user()
    user = create_test_user(
        is_account_owner=False,
        email='start_user@t.t',
        account=owner.account
    )
    workflow = create_test_workflow(user=user, tasks_count=3)
    one_performer = create_test_user(
        is_account_owner=False,
        email='one@t.t',
        account=owner.account
    )
    guest = create_test_guest(account=user.account)
    workflow.save(update_fields=['current_task', 'is_urgent'])
    task = workflow.current_task_instance
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=one_performer.id
    )
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id
    )
    send_new_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'send_new_task_notification.delay'
    )
    sync = True
    service = WorkflowActionService(sync=sync)

    # act
    service.continue_task(
        workflow=workflow,
        task=task,
        is_returned=False,
    )

    # assert
    send_new_task_notification_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        recipients=[
            (one_performer.id, one_performer.email),
            (guest.id, guest.email)
        ],
        task_id=task.id,
        task_name=task.name,
        task_description=task.description,
        workflow_name=workflow.name,
        template_name=workflow.template.name,
        workflow_starter_name=user.name,
        workflow_starter_photo=None,
        due_date_timestamp=None,
        logo_lg=None,
        is_returned=False,
    )


def test_continue_task__returned_task_1_with_performer_and_guest__ok(mocker):

    # arrange
    owner = create_test_user()
    user = create_test_user(
        is_account_owner=False,
        email='start_user@t.t',
        account=owner.account
    )
    workflow = create_test_workflow(user=user, tasks_count=3)
    one_performer = create_test_user(
        is_account_owner=False,
        email='one@t.t',
        account=owner.account
    )
    guest = create_test_guest(account=owner.account)
    workflow.save(update_fields=['current_task', 'is_urgent'])
    task = workflow.current_task_instance
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=one_performer.id
    )
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id
    )
    send_new_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'send_new_task_notification.delay'
    )
    sync = True
    service = WorkflowActionService(sync=sync)

    # act
    service.continue_task(
        workflow=workflow,
        task=task,
        is_returned=True,
    )

    # assert
    send_new_task_notification_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        recipients=[
            (user.id, user.email),
            (one_performer.id, one_performer.email),
            (guest.id, guest.email)
        ],
        task_id=task.id,
        task_name=task.name,
        task_description=task.description,
        workflow_name=workflow.name,
        template_name=workflow.template.name,
        workflow_starter_name=user.name,
        workflow_starter_photo=None,
        due_date_timestamp=None,
        logo_lg=None,
        is_returned=True,
    )


def test_continue_task__returned_task__ok(mocker):

    # arrange
    user = create_test_user()
    guest = create_test_guest(account=user.account)
    workflow = create_test_workflow(user=user, tasks_count=3)
    workflow.current_task = 2
    workflow.save(update_fields=['current_task', 'is_urgent'])
    prev_task = workflow.tasks.get(number=1)
    task = workflow.current_task_instance
    date_started = timezone.now()
    task.date_started = date_started
    task.date_first_started = date_started
    task.save(update_fields=['date_started', 'date_first_started'])
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id
    )
    next_task = workflow.tasks.get(number=3)
    TaskPerformer.objects.filter(task=next_task).update(
        is_completed=True,
        date_completed=timezone.now()
    )
    task_started_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'task_started_event'
    )
    send_ws_new_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_new_task_notification'
    )
    send_new_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'send_new_task_notification.delay'
    )
    now = timezone.now()
    mocker.patch(
        'pneumatic_backend.processes.'
        'services.workflow_action.timezone.now',
        return_value=now
    )
    delete_task_guest_cache_mock = mocker.patch(
        'pneumatic_backend.authentication.services.'
        'GuestJWTAuthService.delete_task_guest_cache'
    )
    sync = True
    service = WorkflowActionService(sync=sync)

    # act
    service.continue_task(
        workflow=workflow,
        task=task,
        is_returned=True,
    )

    # assert
    workflow.refresh_from_db()
    task.refresh_from_db()
    assert task.is_completed is False
    assert task.date_completed is None
    assert task.date_started == now
    task_started_event_mock.assert_called_once_with(task)
    send_ws_new_task_notification_mock.assert_called_once_with(
        task=task,
        sync=sync
    )
    send_new_task_notification_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        recipients=[
            (user.id, user.email),
            (guest.id, guest.email)
        ],
        task_id=task.id,
        task_name=task.name,
        task_description=task.description,
        workflow_name=workflow.name,
        template_name=workflow.template.name,
        workflow_starter_name=user.name,
        workflow_starter_photo=None,
        due_date_timestamp=None,
        logo_lg=None,
        is_returned=True,
    )
    delete_task_guest_cache_mock.has_calls([
        mocker.call(task_id=prev_task.id),
        mocker.call(task_id=task.id)
    ])


def test_continue_task__legacy_workflow__ok(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=3)
    legacy_template_name = 'Legacy'
    workflow.template.delete()
    workflow.legacy_template_name = legacy_template_name
    workflow.is_legacy_template = True
    workflow.save()

    task = workflow.current_task_instance
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'task_started_event'
    )
    mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_new_task_notification'
    )
    send_new_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'send_new_task_notification.delay'
    )
    mocker.patch(
        'pneumatic_backend.authentication.services.'
        'GuestJWTAuthService.delete_task_guest_cache'
    )
    sync = True
    service = WorkflowActionService(sync=sync)

    # act
    service.continue_task(
        workflow=workflow,
        task=task,
        is_returned=False,
    )

    # assert
    send_new_task_notification_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        recipients=[],
        task_id=task.id,
        task_name=task.name,
        task_description=task.description,
        workflow_name=workflow.name,
        template_name=legacy_template_name,
        workflow_starter_name=user.name,
        workflow_starter_photo=None,
        due_date_timestamp=None,
        logo_lg=None,
        is_returned=False,
    )


def test_continue_task__external_workflow__ok(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=3)
    workflow.workflow_starter = None
    workflow.save()

    task = workflow.current_task_instance
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'task_started_event'
    )
    mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_new_task_notification'
    )
    send_new_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'send_new_task_notification.delay'
    )
    mocker.patch(
        'pneumatic_backend.authentication.services.'
        'GuestJWTAuthService.delete_task_guest_cache'
    )
    sync = True
    service = WorkflowActionService(sync=sync)

    # act
    service.continue_task(
        workflow=workflow,
        task=task,
        is_returned=False,
    )

    # assert
    send_new_task_notification_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        recipients=[(user.id, user.email)],
        task_id=task.id,
        task_name=task.name,
        task_description=task.description,
        workflow_name=workflow.name,
        template_name=workflow.template.name,
        workflow_starter_name=None,
        workflow_starter_photo=None,
        due_date_timestamp=None,
        logo_lg=None,
        is_returned=False,
    )


def test_end_process__disable_urgent__ok(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1, is_urgent=True)
    current_task = workflow.current_task_instance
    service = WorkflowActionService(user=user)
    deactivate_guest_cache_mock = mocker.patch(
        'pneumatic_backend.authentication.services.'
        'GuestJWTAuthService.deactivate_task_guest_cache'
    )
    workflow_ended_by_condition_event = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowEventService.workflow_ended_by_condition_event'
    )
    send_workflow_completed_webhook_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'send_workflow_completed_webhook.delay'
    )

    # act
    service.end_process(
        workflow=workflow,
        user=user
    )

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.DONE
    assert workflow.is_urgent is False
    assert not Task.objects.filter(
        workflow=workflow,
        is_urgent=True
    ).exists()
    workflow_ended_by_condition_event.assert_called_once_with(
        workflow=workflow,
        user=user
    )
    deactivate_guest_cache_mock.assert_called_once_with(
        task_id=current_task.id
    )
    send_workflow_completed_webhook_mock.assert_called_once_with(
        user_id=user.id,
        instance_id=workflow.id
    )


def test_complete_task__performer_complete_current_task__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        email='owner@test.test',
        account=account
    )
    user = create_test_user(
        is_account_owner=False,
        account=account
    )
    deleted_user = create_test_user(
        is_account_owner=False,
        email="deleted@test.test",
        account=account
    )
    completed_performer = create_test_user(
        is_account_owner=False,
        email="completed@test.test",
        account=account
    )
    workflow = create_test_workflow(user=user, tasks_count=2)
    task = workflow.current_task_instance
    task.performers.add(account_owner)
    TaskPerformer.objects.create(
        task=task,
        user=deleted_user,
        directly_status=DirectlyStatus.DELETED,
    )
    TaskPerformer.objects.create(
        task=task,
        user=completed_performer,
        is_completed=True,
        date_completed=timezone.now()
    )
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None
    )
    current_date = timezone.now()
    mocker.patch('django.utils.timezone.now', return_value=current_date)
    task_service_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.task.TaskService'
        '.partial_update'
    )
    remove_task_ws_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender'
        '.send_removed_task_notification'
    )
    complete_task_webhook_mock = mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.send_task_webhook.delay'
    )
    send_complete_task_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.'
        'tasks.send_complete_task_notification.delay'
    )
    end_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.end_process'
    )
    action_method = mocker.Mock()
    by_condition = True
    action_method_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.execute_condition',
        return_value=(action_method, by_condition)
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True

    service = WorkflowActionService(
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    service.complete_task(task=task)

    # assert
    task_service_init_mock.assert_called_once_with(
        instance=task,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user
    )
    task_service_update_mock.assert_called_once_with(
        is_completed=True,
        date_completed=current_date,
        force_save=True
    )
    remove_task_ws_mock.assert_called_once_with(
        task=task,
        user_ids=(account_owner.id, user.id),
        sync=True
    )
    send_complete_task_notification_mock.assert_called_once_with(
        author_id=user.id,
        account_id=account.id,
        recipients=[(account_owner.id, account_owner.email)],
        task_id=task.id,
        task_name=task.name,
        workflow_name=workflow.name,
        logo_lg=account.logo_lg,
        logging=account.log_api_requests,
    )
    complete_task_webhook_mock.assert_called_once_with(
        event_name='task_completed_v2',
        user_id=user.id,
        instance_id=task.id
    )
    end_workflow_mock.assert_not_called()
    next_task = workflow.tasks.get(number=2)
    action_method_mock.assert_called_once_with(next_task)
    action_method.assert_called_once_with(
        workflow=workflow,
        task=next_task,
        user=user,
        by_condition=by_condition
    )


def test_complete_task__last__end_workflow(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        email='owner@test.test',
        account=account
    )
    user = create_test_user(
        is_account_owner=False,
        account=account
    )
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.remove(account_owner)

    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None
    )
    current_date = timezone.now()
    mocker.patch('django.utils.timezone.now', return_value=current_date)
    task_service_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.task.TaskService'
        '.partial_update'
    )
    remove_task_ws_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender'
        '.send_removed_task_notification'
    )
    complete_task_webhook_mock = mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.send_task_webhook.delay'
    )
    send_complete_task_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.'
        'tasks.send_complete_task_notification.delay'
    )
    end_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.end_process'
    )
    action_method = mocker.Mock()
    action_method_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.execute_condition',
        return_value=(action_method, False)
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True

    service = WorkflowActionService(
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    service.complete_task(task=task)

    # assert
    task_service_init_mock.assert_called_once_with(
        instance=task,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user
    )
    task_service_update_mock.assert_called_once_with(
        is_completed=True,
        date_completed=current_date,
        force_save=True
    )
    send_complete_task_notification_mock.assert_not_called()
    remove_task_ws_mock.assert_called_once_with(
        task=task,
        user_ids=(user.id,),
        sync=True
    )
    complete_task_webhook_mock.assert_called_once_with(
        event_name='task_completed_v2',
        user_id=user.id,
        instance_id=task.id
    )
    end_workflow_mock.assert_called_once_with(
        workflow=workflow,
        user=user,
        by_condition=False,
        by_complete_task=True
    )
    action_method_mock.assert_not_called()
    action_method.assert_not_called()


def test_complete_task__before_current__skip_actions(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=2)
    workflow.current_task = 2
    workflow.save(update_fields=['current_task'])
    task = workflow.tasks.get(number=1)

    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None
    )
    current_date = timezone.now()
    mocker.patch('django.utils.timezone.now', return_value=current_date)
    task_service_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.task.TaskService'
        '.partial_update'
    )
    remove_task_ws_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender'
        '.send_removed_task_notification'
    )
    complete_task_webhook_mock = mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.send_task_webhook.delay'
    )
    send_complete_task_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.'
        'tasks.send_complete_task_notification.delay'
    )
    end_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.end_process'
    )
    action_method = mocker.Mock()
    action_method_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.execute_condition',
        return_value=(action_method, True)
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True

    service = WorkflowActionService(
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    service.complete_task(task=task)

    # assert
    task_service_init_mock.assert_called_once_with(
        instance=task,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user
    )
    task_service_update_mock.assert_called_once_with(
        is_completed=True,
        date_completed=current_date,
        force_save=True
    )
    remove_task_ws_mock.assert_not_called()
    send_complete_task_notification_mock.assert_not_called()
    complete_task_webhook_mock.assert_not_called()
    end_workflow_mock.assert_not_called()
    action_method_mock.assert_not_called()
    action_method.assert_not_called()


def test_complete_task__before_current__not_started__ok(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=2)
    workflow.current_task = 2
    workflow.save(update_fields=['current_task'])
    task = workflow.tasks.get(number=1)
    task.date_started = None
    task.save(update_fields=['date_started'])

    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None
    )
    current_date = timezone.now()
    mocker.patch('django.utils.timezone.now', return_value=current_date)
    task_service_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.task.TaskService'
        '.partial_update'
    )
    remove_task_ws_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender'
        '.send_removed_task_notification'
    )
    complete_task_webhook_mock = mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.send_task_webhook.delay'
    )
    send_complete_task_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.'
        'tasks.send_complete_task_notification.delay'
    )
    end_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.end_process'
    )
    action_method = mocker.Mock()
    action_method_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.execute_condition',
        return_value=(action_method, False)
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True

    service = WorkflowActionService(
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    service.complete_task(task=task)

    # assert
    task_service_init_mock.assert_called_once_with(
        instance=task,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user
    )
    task_service_update_mock.assert_called_once_with(
        is_completed=True,
        date_completed=current_date,
        date_started=current_date,
        force_save=True
    )
    remove_task_ws_mock.assert_not_called()
    send_complete_task_notification_mock.assert_not_called()
    complete_task_webhook_mock.assert_not_called()
    end_workflow_mock.assert_not_called()
    action_method_mock.assert_not_called()
    action_method.assert_not_called()


def test_complete_task__after_current__skip(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=2)
    task = workflow.tasks.get(number=2)

    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None
    )
    current_date = timezone.now()
    mocker.patch('django.utils.timezone.now', return_value=current_date)
    task_service_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.task.TaskService'
        '.partial_update'
    )
    remove_task_ws_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender'
        '.send_removed_task_notification'
    )
    complete_task_webhook_mock = mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.send_task_webhook.delay'
    )
    send_complete_task_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.'
        'tasks.send_complete_task_notification.delay'
    )
    end_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.end_process'
    )
    action_method = mocker.Mock()
    action_method_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.execute_condition',
        return_value=(action_method, True)
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True

    service = WorkflowActionService(
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    service.complete_task(task=task)

    # assert
    task_service_init_mock.assert_not_called()
    task_service_update_mock.assert_not_called()
    remove_task_ws_mock.assert_not_called()
    send_complete_task_notification_mock.assert_not_called()
    complete_task_webhook_mock.assert_not_called()
    end_workflow_mock.assert_not_called()
    action_method_mock.assert_not_called()
    action_method.assert_not_called()


def test_complete_task__unsubscribed_performer__not_sent(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        email='owner@test.test',
        account=account,
        is_complete_tasks_subscriber=False
    )
    user = create_test_user(
        is_account_owner=False,
        email="performer@test.test",
        account=account
    )

    workflow = create_test_workflow(user=user, tasks_count=2)
    task = workflow.current_task_instance
    task.performers.add(account_owner)
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None
    )
    current_date = timezone.now()
    mocker.patch('django.utils.timezone.now', return_value=current_date)
    task_service_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.task.TaskService'
        '.partial_update'
    )
    remove_task_ws_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender'
        '.send_removed_task_notification'
    )
    complete_task_webhook_mock = mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.send_task_webhook.delay'
    )
    send_complete_task_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.'
        'tasks.send_complete_task_notification.delay'
    )
    end_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.end_process'
    )
    action_method = mocker.Mock()
    by_condition = False
    action_method_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.execute_condition',
        return_value=(action_method, by_condition)
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True

    service = WorkflowActionService(
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    service.complete_task(task=task)

    # assert
    task_service_init_mock.assert_called_once_with(
        instance=task,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user
    )
    task_service_update_mock.assert_called_once_with(
        is_completed=True,
        date_completed=current_date,
        force_save=True
    )
    send_complete_task_notification_mock.assert_not_called()
    remove_task_ws_mock.assert_called_once_with(
        task=task,
        user_ids=(account_owner.id, user.id),
        sync=True
    )
    complete_task_webhook_mock.assert_called_once_with(
        event_name='task_completed_v2',
        user_id=user.id,
        instance_id=task.id
    )
    end_workflow_mock.assert_not_called()
    next_task = workflow.tasks.get(number=2)
    action_method_mock.assert_called_once_with(next_task)
    action_method.assert_called_once_with(
        workflow=workflow,
        task=next_task,
        user=user,
        by_condition=by_condition,
    )


def test_complete_current_task_by_account_owner__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        account=account,
        is_account_owner=True,
        email='owner@test.test'
    )
    user = create_test_user(account=account, is_account_owner=False)
    deleted_user = create_test_user(
        is_account_owner=False,
        email="deleted@test.test",
        account=account
    )
    completed_performer = create_test_user(
        is_account_owner=False,
        email="completed@test.test",
        account=account
    )
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.remove(account_owner)
    TaskPerformer.objects.create(
        task=task,
        user=deleted_user,
        directly_status=DirectlyStatus.DELETED,
    )
    TaskPerformer.objects.create(
        task=task,
        user=completed_performer,
        is_completed=True,
        date_completed=timezone.now()
    )
    task_field = TaskField.objects.create(
        order=1,
        type=FieldType.STRING,
        name='string',
        task=task,
        workflow=workflow
    )

    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None
    )
    task_field_service_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.field'
        '.TaskFieldService.partial_update'
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.accounts.views.users.AnalyticService.'
        'task_completed'
    )
    complete_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.complete_task'
    )
    task_complete_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'task_complete_event'
    )
    field_value = 'drop the base'
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True

    service = WorkflowActionService(
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=account_owner,
        sync=sync
    )

    # act
    service.complete_current_task_for_user(
        workflow=workflow,
        fields_values={
            task_field.api_name: field_value
        }
    )

    # assert
    task_performer = task.taskperformer_set.get(user_id=user.id)
    assert task_performer.is_completed is False
    assert task_performer.date_completed is None
    task_field_service_init_mock.assert_called_once_with(
        user=account_owner,
        instance=task_field
    )
    task_field_service_update_mock.assert_called_once_with(
        value=field_value,
        force_save=True
    )
    analytics_mock.assert_called_once_with(
        user=account_owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow,
        task=task
    )
    complete_task_mock.assert_called_once_with(task=task)
    task_complete_event_mock.assert_called_once_with(
        task=task,
        user=account_owner
    )


def test_complete_current_task_by_user_performer__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        account=account,
        is_account_owner=True,
        email='owner@test.test'
    )
    user = create_test_user(account=account, is_account_owner=False)
    deleted_user = create_test_user(
        is_account_owner=False,
        email="deleted@test.test",
        account=account
    )
    completed_performer = create_test_user(
        is_account_owner=False,
        email="completed@test.test",
        account=account
    )
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.add(account_owner)
    TaskPerformer.objects.create(
        task=task,
        user=deleted_user,
        directly_status=DirectlyStatus.DELETED,
    )
    TaskPerformer.objects.create(
        task=task,
        user=completed_performer,
        is_completed=True,
        date_completed=timezone.now()
    )
    task_field = TaskField.objects.create(
        order=1,
        type=FieldType.STRING,
        name='string',
        task=task,
        workflow=workflow
    )

    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None
    )
    task_field_service_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.field'
        '.TaskFieldService.partial_update'
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.accounts.views.users.AnalyticService.'
        'task_completed'
    )
    complete_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.complete_task'
    )
    task_complete_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'task_complete_event'
    )

    field_value = 'drop the base'
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True

    service = WorkflowActionService(
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    service.complete_current_task_for_user(
        workflow=workflow,
        fields_values={
            task_field.api_name: field_value
        }
    )

    # assert
    task_performer_1 = task.taskperformer_set.get(user_id=user.id)
    assert task_performer_1.is_completed is True
    assert task_performer_1.date_completed is not None

    task_performer_2 = task.taskperformer_set.get(user_id=account_owner.id)
    assert task_performer_2.is_completed is True
    assert task_performer_2.date_completed is not None
    task_field_service_init_mock.assert_called_once_with(
        user=user,
        instance=task_field
    )
    task_field_service_update_mock.assert_called_once_with(
        value=field_value,
        force_save=True
    )
    analytics_mock.assert_called_once_with(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow,
        task=task
    )
    complete_task_mock.assert_called_once_with(task=task)
    task_complete_event_mock.assert_called_once_with(task=task, user=user)


def test_complete_current_task_by_user__rc_by_all__first__ok(mocker):

    """ task with require completion by all completed by first performer """

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        account=account,
        is_account_owner=True,
        email='owner@test.test'
    )
    user = create_test_user(account=account, is_account_owner=False)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.current_task_instance
    task.require_completion_by_all = True
    task.save(update_fields=['require_completion_by_all'])
    task.performers.add(account_owner)

    current_date = timezone.now()
    mocker.patch('django.utils.timezone.now', return_value=current_date)

    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None
    )
    task_field_service_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.field'
        '.TaskFieldService.partial_update'
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.accounts.views.users.AnalyticService.'
        'task_completed'
    )
    complete_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.complete_task'
    )
    send_removed_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_removed_task_notification'
    )

    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True

    service = WorkflowActionService(
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    service.complete_current_task_for_user(
        workflow=workflow,
    )

    # assert
    task_performer = task.taskperformer_set.get(user_id=user.id)
    assert task_performer.is_completed is True
    assert task_performer.date_completed == current_date
    task_field_service_init_mock.assert_not_called()
    task_field_service_update_mock.assert_not_called()
    analytics_mock.assert_called_once_with(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow,
        task=task
    )
    complete_task_mock.assert_not_called()
    send_removed_task_notification_mock.assert_called_once_with(
        task=task,
        user_ids=(user.id,),
        sync=True
    )


def test_complete_current_task_by_user__rc_by_all__last__ok(mocker):

    """ task with require completion by all completed by last performer """

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        account=account,
        is_account_owner=True,
        email='owner@test.test'
    )
    user = create_test_user(account=account, is_account_owner=False)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.current_task_instance
    task.require_completion_by_all = True
    task.save(update_fields=['require_completion_by_all'])
    TaskPerformer.objects.create(
        user=account_owner,
        task=task,
        is_completed=True
    )

    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None
    )
    task_field_service_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.field'
        '.TaskFieldService.partial_update'
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.accounts.views.users.AnalyticService.'
        'task_completed'
    )
    complete_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.complete_task'
    )
    send_removed_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_removed_task_notification'
    )

    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True

    service = WorkflowActionService(
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    service.complete_current_task_for_user(
        workflow=workflow,
    )

    # assert
    task_performer = task.taskperformer_set.get(user_id=user.id)
    assert task_performer.is_completed is True
    assert task_performer.date_completed is not None
    task_field_service_init_mock.assert_not_called()
    task_field_service_update_mock.assert_not_called()
    analytics_mock.assert_called_once_with(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow,
        task=task
    )
    complete_task_mock.assert_called_once_with(task=task)
    send_removed_task_notification_mock.assert_not_called()


def test_complete_current_task_by_guest_performer__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        account=account,
        is_account_owner=True,
        email='owner@test.test'
    )
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(user=account_owner, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.clear()
    task.performers.add(guest)
    task_field = TaskField.objects.create(
        order=1,
        type=FieldType.STRING,
        name='string',
        task=task,
        workflow=workflow
    )

    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None
    )
    task_field_service_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.field'
        '.TaskFieldService.partial_update'
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.accounts.views.users.AnalyticService.'
        'task_completed'
    )
    complete_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.complete_task'
    )
    current_date = timezone.now()
    mocker.patch('django.utils.timezone.now', return_value=current_date)

    field_value = 'drop the base'
    is_superuser = False
    auth_type = AuthTokenType.GUEST
    sync = True

    service = WorkflowActionService(
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=guest,
        sync=sync
    )

    # act
    service.complete_current_task_for_user(
        workflow=workflow,
        fields_values={
            task_field.api_name: field_value
        }
    )

    # assert
    assert task.taskperformer_set.get(
        user_id=guest.id,
        is_completed=True,
        date_completed=current_date
    )

    task_field_service_init_mock.assert_called_once_with(
        user=guest,
        instance=task_field
    )
    task_field_service_update_mock.assert_called_once_with(
        value=field_value,
        force_save=True
    )
    analytics_mock.assert_called_once_with(
        user=guest,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow,
        task=task
    )
    complete_task_mock.assert_called_once_with(task=task)


def test_complete_current_task_by_guest__rcba_first_completion__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        account=account,
        is_account_owner=True,
        email='owner@test.test'
    )
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(user=account_owner, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.add(guest)
    task.require_completion_by_all = True
    task.save(update_fields=['require_completion_by_all'])

    current_date = timezone.now()
    mocker.patch('django.utils.timezone.now', return_value=current_date)

    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None
    )
    task_field_service_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.field'
        '.TaskFieldService.partial_update'
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.accounts.views.users.AnalyticService.'
        'task_completed'
    )
    complete_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.complete_task'
    )
    send_removed_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_removed_task_notification'
    )

    is_superuser = False
    auth_type = AuthTokenType.GUEST
    sync = True

    service = WorkflowActionService(
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=guest,
        sync=sync
    )

    # act
    service.complete_current_task_for_user(
        workflow=workflow
    )

    # assert
    task_performer = task.taskperformer_set.get(user_id=guest.id)
    assert task_performer.is_completed is True
    assert task_performer.date_completed == current_date

    task_field_service_init_mock.assert_not_called()
    task_field_service_update_mock.assert_not_called()
    analytics_mock.assert_called_once_with(
        user=guest,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow,
        task=task
    )
    complete_task_mock.assert_not_called()
    send_removed_task_notification_mock.assert_not_called()


def test_complete_current_task__by_guest_rcba_last_completion__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        account=account,
        is_account_owner=True,
        email='owner@test.test'
    )
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(user=account_owner, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.add(guest)
    task.require_completion_by_all = True
    task.save(update_fields=['require_completion_by_all'])
    TaskPerformer.objects.filter(
        user=account_owner,
        task=task,
    ).update(
        is_completed=True,
        date_completed=timezone.now()
    )

    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None
    )
    task_field_service_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.field'
        '.TaskFieldService.partial_update'
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.accounts.views.users.AnalyticService.'
        'task_completed'
    )
    task_complete_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'task_complete_event'
    )
    complete_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.complete_task'
    )

    is_superuser = False
    auth_type = AuthTokenType.GUEST
    sync = True

    service = WorkflowActionService(
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=guest,
        sync=sync
    )

    # act
    service.complete_current_task_for_user(
        workflow=workflow
    )

    # assert
    task_performer = task.taskperformer_set.get(user_id=guest.id)
    assert task_performer.is_completed is True
    assert task_performer.date_completed is not None
    task_field_service_init_mock.assert_not_called()
    task_field_service_update_mock.assert_not_called()
    analytics_mock.assert_called_once_with(
        user=guest,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow,
        task=task
    )
    complete_task_mock.assert_called_once_with(task=task)
    task_complete_event_mock.assert_called_once_with(
        task=task,
        user=guest
    )


def test_complete_current_task__task_rcba_and_first_completion__ok(mocker):

    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True
    )
    user = create_test_user(
        account=account,
        is_account_owner=False
    )
    user_2 = create_test_user(
        email='testinguser@pneumatic.app',
        account=account,
        is_account_owner=False

    )
    workflow = create_test_workflow(user)
    task = workflow.current_task_instance
    task.require_completion_by_all = True
    task.save()
    task.performers.add(user_2)
    current_date = timezone.now()
    mocker.patch('django.utils.timezone.now', return_value=current_date)
    analytics_mock = mocker.patch(
        'pneumatic_backend.accounts.views.users.AnalyticService.'
        'task_completed'
    )
    task_complete_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'task_complete_event'
    )
    complete_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.complete_task'
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True
    service = WorkflowActionService(
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    service.complete_current_task_for_user(
        workflow=workflow,
    )

    # assert
    complete_task_mock.assert_not_called()
    assert task.taskperformer_set.get(
        user_id=user.id,
        is_completed=True,
        date_completed=current_date
    )
    assert task.taskperformer_set.get(
        user_id=user_2.id,
        is_completed=False,
        date_completed=None
    )
    analytics_mock.assert_called_once_with(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow,
        task=task
    )
    complete_task_mock.assert_not_called()
    task_complete_event_mock.assert_called_once_with(
        task=task,
        user=user
    )


def test_complete_current_task__task_rcba_and_last_completion__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True
    )
    user = create_test_user(
        account=account,
        is_account_owner=False
    )
    deleted_user = create_test_user(
        is_account_owner=False,
        email="deleted@test.test",
        account=account
    )
    completed_performer = create_test_user(
        is_account_owner=False,
        email="completed@test.test",
        account=account
    )
    workflow = create_test_workflow(user)
    task = workflow.current_task_instance
    task.require_completion_by_all = True
    task.save()
    TaskPerformer.objects.create(
        task=task,
        user=account_owner,
        is_completed=True,
        date_completed=timezone.now()
    )
    TaskPerformer.objects.create(
        task=task,
        user=deleted_user,
        directly_status=DirectlyStatus.DELETED,
    )
    TaskPerformer.objects.create(
        task=task,
        user=completed_performer,
        is_completed=True,
        date_completed=timezone.now()
    )
    current_date = timezone.now()
    mocker.patch('django.utils.timezone.now', return_value=current_date)
    analytics_mock = mocker.patch(
        'pneumatic_backend.accounts.views.users.AnalyticService.'
        'task_completed'
    )
    task_complete_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'task_complete_event'
    )
    complete_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.complete_task'
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True
    service = WorkflowActionService(
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    service.complete_current_task_for_user(
        workflow=workflow,
    )

    # assert
    assert task.taskperformer_set.get(
        user_id=user.id,
        is_completed=True,
        date_completed=current_date
    )
    analytics_mock.assert_called_once_with(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow,
        task=task
    )
    complete_task_mock.assert_called_once_with(task=task)
    task_complete_event_mock.assert_called_once_with(
        task=task,
        user=user
    )
