import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.messages import workflow as messages
from pneumatic_backend.processes.services.exceptions import \
    WorkflowActionServiceException
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template,
    create_nonlinear_workflow,
    create_test_workflow,
    create_test_guest,
    create_test_account,
    create_task_completed_webhook,
    create_wf_completed_webhook,
    create_task_returned_webhook,
    create_test_group,
    create_test_owner,
    create_test_admin,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.api_v2.services import WorkflowEventService
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService
)
from pneumatic_backend.processes.enums import (
    WorkflowStatus,
    FieldType,
    TaskStatus,
    DirectlyStatus,
    PerformerType,
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
    task = workflow.tasks.get(number=1)
    service = WorkflowActionService(user=user, workflow=workflow)
    send_removed_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_removed_task_notification'
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'workflows_terminated'
    )
    WorkflowEventService.task_started_event(task)

    deactivate_guest_cache_mock = mocker.patch(
        'pneumatic_backend.authentication.services.'
        'GuestJWTAuthService.deactivate_task_guest_cache'
    )

    # act
    service.terminate_workflow()

    # assert
    workflow.refresh_from_db()
    assert not Workflow.objects.filter(id=workflow.id).exists()
    assert not WorkflowEvent.objects.filter(workflow=workflow).exists()
    assert not Task.objects.filter(workflow=workflow).exists()
    assert not Delay.objects.filter(task=task).exists()
    send_removed_task_notification_mock.assert_called_once_with(
        task=task,
        user_ids=(user.id,)
    )
    deactivate_guest_cache_mock.assert_called_once_with(
        task_id=task.id
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
    task = workflow.tasks.get(number=1)
    deleted_performer = create_test_admin(account=account)
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=deleted_performer.id,
        directly_status=DirectlyStatus.DELETED
    )
    completed_performer = create_test_admin(
        account=account,
        email='user_3@test.test',
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
    user_4 = create_test_admin(
        account=account,
        email='user_4@test.test',
    )
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=user_4.id,
    )

    service = WorkflowActionService(user=user, workflow=workflow)
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
    service.terminate_workflow()

    # assert
    expected_user_ids = {user_4.id, user.id}
    send_removed_task_notification_mock.assert_called_once()
    call_args = send_removed_task_notification_mock.call_args[1]
    assert set(call_args['user_ids']) == expected_user_ids
    assert call_args['task'] == task


def test_delay_workflow__ok(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    delay = Delay.objects.create(
        task=task,
        duration=timedelta(hours=1)
    )
    workflow_delay_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'WorkflowEventService.workflow_delay_event'
    )
    service = WorkflowActionService(user=user, workflow=workflow)

    # act
    service.delay_workflow(delay=delay, task=task)

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.DELAYED
    task.refresh_from_db()
    assert task.status == TaskStatus.DELAYED
    delay.refresh_from_db()
    assert delay.start_date is not None
    workflow_delay_event_mock.assert_called_once_with(
        workflow=workflow,
        delay=delay
    )


def test_force_delay_workflow__update_existent__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)

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
        workflow=workflow,
        user=account_owner,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
    )

    # act
    service.force_delay_workflow(date=new_end_date)

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.DELAYED
    task.refresh_from_db()
    assert task.status == TaskStatus.DELAYED
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
        logo_lg=account_owner.account.logo_lg,
        task_id=task.id,
        author_id=account_owner.id,
        user_id=user.id,
        user_email=user.email,
        account_id=user.account_id,
    )
    send_removed_task_notification_mock.assert_called_once_with(
        user_ids=(user.id,),
        task=task,
    )
    analytics_mock.assert_called_once_with(
        user=account_owner,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        duration=new_duration
    )


def test_force_delay_workflow__notifications__for_not_completed_only(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    deleted_performer = create_test_admin(account=account)
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=deleted_performer.id,
        directly_status=DirectlyStatus.DELETED
    )
    completed_performer = create_test_admin(
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
        workflow=workflow,
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
    )

    # act
    service.force_delay_workflow(date=new_end_date)

    # assert
    send_notifications_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        logo_lg=user.account.logo_lg,
        task_id=task.id,
        author_id=user.id,
        user_id=user.id,
        user_email=user.email,
        account_id=user.account_id,
    )
    send_removed_task_notification_mock.assert_called_once_with(
        user_ids=(user.id,),
        task=task,
    )


def test_force_delay_workflow__create_new__ok(mocker):

    # arrange
    account = create_test_account(log_api_requests=True)
    account_owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
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
        workflow=workflow,
        user=account_owner,
        auth_type=AuthTokenType.USER,
        is_superuser=is_superuser,
    )

    # act
    service.force_delay_workflow(date=new_end_date)

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.DELAYED
    task.refresh_from_db()
    assert task.status == TaskStatus.DELAYED
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
        logo_lg=user.account.logo_lg,
        task_id=task.id,
        author_id=account_owner.id,
        user_id=user.id,
        user_email=user.email,
        account_id=user.account_id,
    )
    send_removed_task_notification_mock.assert_called_once_with(
        user_ids=(user.id,),
        task=task,
    )
    analytics_mock.assert_called_once_with(
        user=account_owner,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        duration=new_duration
    )


def test_force_resume_workflow__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
        status=WorkflowStatus.DELAYED
    )
    task = workflow.tasks.get(number=1)
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
    service = WorkflowActionService(user=account_owner, workflow=workflow)

    # act
    service.force_resume_workflow()

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.RUNNING
    delay.refresh_from_db()
    assert delay.start_date == now
    assert delay.duration == duration
    assert delay.estimated_end_date == now + duration
    assert delay.end_date == end_date
    force_resume_workflow_event_mock.assert_called_once_with(
        user=account_owner,
        workflow=workflow
    )
    send_resumed_workflow_notification_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        logo_lg=user.account.logo_lg,
        task_id=task.id,
        author_id=account_owner.id,
        account_id=user.account_id,
    )
    continue_task_mock.assert_called_once_with(task)


def test_force_resume_workflow__running_workflow__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(account=account)
    user = create_test_admin(account=account)
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
    service = WorkflowActionService(user=account_owner, workflow=workflow)

    # act
    service.force_resume_workflow()

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.RUNNING
    force_resume_workflow_event_mock.assert_not_called()
    send_resumed_workflow_notification_mock.assert_not_called()
    continue_task_mock.assert_not_called()


def test_force_resume_workflow__ended_workflow__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(user=user, tasks_count=1)
    workflow.status = WorkflowStatus.DONE
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
    service = WorkflowActionService(user=account_owner, workflow=workflow)

    # act
    with pytest.raises(exceptions.ResumeNotDelayedWorkflow) as ex:
        service.force_resume_workflow()

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
    workflow_starter = create_test_admin(
        account=account,
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
    deleted_performer = create_test_admin(
        email='deleted@test.test',
        account=account
    )
    unsubscribed_performer = create_test_admin(
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
    service = WorkflowActionService(workflow=workflow, user=user, sync=sync)

    # act
    service.continue_task(task=task)

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
        account_id=user.account_id,
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
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user, tasks_count=3)
    performer = create_test_admin(account=account)
    deleted_performer = create_test_admin(
        email='deleted@t.t',
        account=account
    )
    guest = create_test_guest(account=user.account)
    workflow.current_task = 2
    workflow.is_urgent = True
    workflow.save(update_fields=['current_task', 'is_urgent'])
    prev_task = workflow.tasks.get(number=1)
    task = workflow.tasks.get(number=2)
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
    service = WorkflowActionService(workflow=workflow, user=user, sync=sync)

    # act
    service.continue_task(task=task)

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
        account_id=user.account_id,
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
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(user=user, tasks_count=3)
    one_performer = create_test_admin(
        email='one@t.t',
        account=account
    )
    guest = create_test_guest(account=user.account)
    workflow.save(update_fields=['current_task', 'is_urgent'])
    task = workflow.tasks.get(number=1)
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
    service = WorkflowActionService(workflow=workflow, user=user, sync=sync)

    # act
    service.continue_task(task=task)

    # assert
    send_new_task_notification_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        account_id=user.account_id,
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
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(user=user, tasks_count=3)
    one_performer = create_test_admin(
        email='one@t.t',
        account=account
    )
    guest = create_test_guest(account=owner.account)
    workflow.save(update_fields=['current_task', 'is_urgent'])
    task = workflow.tasks.get(number=1)
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
    service = WorkflowActionService(workflow=workflow, user=user, sync=sync)

    # act
    service.continue_task(task=task, is_returned=True)

    # assert
    send_new_task_notification_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        account_id=user.account_id,
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
    task = workflow.tasks.get(number=2)
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
    service = WorkflowActionService(
        workflow=workflow,
        user=user,
        sync=sync
    )

    # act
    service.continue_task(task=task, is_returned=True)

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
        account_id=user.account_id,
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

    task = workflow.tasks.get(number=1)
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
    service = WorkflowActionService(workflow=workflow, user=user, sync=sync)

    # act
    service.continue_task(task=task)

    # assert
    send_new_task_notification_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        account_id=user.account_id,
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

    task = workflow.tasks.get(number=1)
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
    service = WorkflowActionService(workflow=workflow, user=user, sync=sync)

    # act
    service.continue_task(task=task)

    # assert
    send_new_task_notification_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        account_id=user.account_id,
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
    create_wf_completed_webhook(user)
    workflow = create_test_workflow(user, tasks_count=1, is_urgent=True)
    task = workflow.tasks.get(number=1)
    service = WorkflowActionService(workflow=workflow, user=user)
    deactivate_guest_cache_mock = mocker.patch(
        'pneumatic_backend.authentication.services.'
        'GuestJWTAuthService.deactivate_task_guest_cache'
    )
    workflow_ended_by_condition_event = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowEventService.workflow_ended_by_condition_event'
    )
    webhook_payload = mocker.Mock()
    mocker.patch(
        'pneumatic_backend.processes.models.workflows.workflow.Workflow'
        '.webhook_payload',
        return_value=webhook_payload
    )
    send_workflow_completed_webhook_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'send_workflow_completed_webhook.delay'
    )

    # act
    service.end_process()

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
        task_id=task.id
    )
    send_workflow_completed_webhook_mock.assert_called_once_with(
        user_id=user.id,
        account_id=user.account_id,
        payload=webhook_payload
    )


def test_complete_task__performer_complete_current_task__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(account=account)
    user = create_test_admin(account=account)
    deleted_user = create_test_admin(
        email="deleted@test.test",
        account=account
    )
    completed_performer = create_test_admin(
        email="completed@test.test",
        account=account
    )
    workflow = create_test_workflow(user=user, tasks_count=2)
    task = workflow.tasks.get(number=1)
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
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay'
    )
    send_complete_task_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.'
        'tasks.send_complete_task_notification.delay'
    )
    end_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.end_process'
    )
    task_complete_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'task_completed'
    )
    task_complete_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'task_complete_event'
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
        workflow=workflow,
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
        date_started=task.date_started,
        status=TaskStatus.COMPLETED,
        date_completed=current_date,
        force_save=True
    )
    remove_task_ws_mock.assert_called_once_with(
        task=task,
        user_ids={account_owner.id, user.id},
        sync=True
    )
    send_complete_task_notification_mock.assert_called_once_with(
        author_id=user.id,
        account_id=account.id,
        recipients=[(account_owner.id, account_owner.email)],
        task_id=task.id,
        logo_lg=account.logo_lg,
        logging=account.log_api_requests,
    )
    complete_task_webhook_mock.assert_not_called()
    end_workflow_mock.assert_not_called()
    next_task = workflow.tasks.get(number=2)
    action_method_mock.assert_called_once_with(next_task)
    action_method.assert_called_once_with(
        task=next_task,
        by_complete_task=True,
        is_returned=False,
        by_condition=True
    )
    task_complete_analytics_mock.assert_not_called()
    task_complete_event_mock.assert_not_called()


def test_complete_task__last__end_workflow(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
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
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay'
    )
    send_complete_task_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.'
        'tasks.send_complete_task_notification.delay'
    )
    end_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.end_process'
    )
    task_complete_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'task_completed'
    )
    task_complete_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'task_complete_event'
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
        workflow=workflow,
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
        status=TaskStatus.COMPLETED,
        date_completed=current_date,
        date_started=task.date_started,
        force_save=True
    )
    send_complete_task_notification_mock.assert_not_called()
    remove_task_ws_mock.assert_called_once_with(
        task=task,
        user_ids={user.id},
        sync=True
    )
    complete_task_webhook_mock.assert_not_called()
    end_workflow_mock.assert_called_once_with(
        by_condition=False,
        by_complete_task=True
    )
    action_method_mock.assert_not_called()
    action_method.assert_not_called()
    task_complete_analytics_mock.assert_not_called()
    task_complete_event_mock.assert_not_called()


# New style tests
@pytest.mark.skip
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
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay'
    )
    send_complete_task_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.'
        'tasks.send_complete_task_notification.delay'
    )
    end_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.end_process'
    )
    task_complete_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'task_completed'
    )
    task_complete_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'task_complete_event'
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
        workflow=workflow,
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
        date_started=task.date_started,
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
    task_complete_analytics_mock.assert_not_called()
    task_complete_event_mock.assert_not_called()


# New style tests
@pytest.mark.skip
def test_complete_task__multiple_tasks_all_running__ok(mocker):

    # arrange
    account = create_test_account()
    create_test_user(account=account)
    user = create_test_admin(account=account)
    workflow = create_nonlinear_workflow(user=user, tasks_count=2)
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
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay'
    )
    send_complete_task_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.'
        'tasks.send_complete_task_notification.delay'
    )
    end_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.end_process'
    )
    task_complete_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'task_completed'
    )
    task_complete_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'task_complete_event'
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
        workflow=workflow,
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
        date_started=task.date_started,
        date_completed=current_date,
        force_save=True
    )
    send_complete_task_notification_mock.assert_not_called()
    remove_task_ws_mock.assert_called_once_with(
        task=task,
        user_ids=(user.id,),
        sync=True
    )
    complete_task_webhook_mock.assert_not_called()
    end_workflow_mock.assert_not_called()
    action_method_mock.assert_not_called()
    action_method.assert_not_called()
    task_complete_analytics_mock.assert_not_called()
    task_complete_event_mock.assert_not_called()


def test_complete_task__before_current__not_started__ok(mocker):

    # arrange
    user = create_test_user()
    create_task_completed_webhook(user)
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
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay'
    )
    send_complete_task_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.'
        'tasks.send_complete_task_notification.delay'
    )
    end_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.end_process'
    )
    task_complete_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'task_completed'
    )
    task_complete_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'task_complete_event'
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
        workflow=workflow,
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
        status=TaskStatus.COMPLETED,
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
    task_complete_analytics_mock.assert_not_called()
    task_complete_event_mock.assert_not_called()


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
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay'
    )
    send_complete_task_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.'
        'tasks.send_complete_task_notification.delay'
    )
    end_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.end_process'
    )
    task_complete_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'task_completed'
    )
    task_complete_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'task_complete_event'
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
        workflow=workflow,
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
    task_complete_analytics_mock.assert_not_called()
    task_complete_event_mock.assert_not_called()


def test_complete_task__unsubscribed_performer__not_sent(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        account=account,
        is_complete_tasks_subscriber=False
    )
    user = create_test_admin(account=account)
    workflow = create_test_workflow(user=user, tasks_count=2)
    task = workflow.tasks.get(number=1)
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
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay'
    )
    send_complete_task_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.'
        'tasks.send_complete_task_notification.delay'
    )
    end_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.end_process'
    )
    task_complete_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'task_completed'
    )
    task_complete_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'task_complete_event'
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
        workflow=workflow,
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
        status=TaskStatus.COMPLETED,
        date_completed=current_date,
        date_started=task.date_started,
        force_save=True
    )
    send_complete_task_notification_mock.assert_not_called()
    expected_user_ids = {account_owner.id, user.id}
    remove_task_ws_mock.assert_called_once()
    call_args = remove_task_ws_mock.call_args[1]
    assert set(call_args['user_ids']) == expected_user_ids
    assert call_args['task'] == task
    assert call_args['sync'] is True
    complete_task_webhook_mock.assert_not_called()
    end_workflow_mock.assert_not_called()
    next_task = workflow.tasks.get(number=2)
    action_method_mock.assert_called_once_with(next_task)
    action_method.assert_called_once_with(
        task=next_task,
        by_condition=False,
        by_complete_task=True,
        is_returned=False,
    )
    task_complete_analytics_mock.assert_not_called()
    task_complete_event_mock.assert_not_called()


def test_complete_task__by_user__create_workflow_event(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(account=account)
    user = create_test_admin(account=account)
    deleted_user = create_test_admin(
        email="deleted@test.test",
        account=account
    )
    completed_performer = create_test_admin(
        email="completed@test.test",
        account=account
    )
    workflow = create_test_workflow(user=user, tasks_count=2)
    task = workflow.tasks.get(number=1)
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
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay'
    )
    send_complete_task_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.'
        'tasks.send_complete_task_notification.delay'
    )
    end_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.end_process'
    )
    task_complete_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'task_completed'
    )
    task_complete_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'task_complete_event'
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
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    service.complete_task(task=task, by_user=True)

    # assert
    task_service_init_mock.assert_called_once_with(
        instance=task,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user
    )
    task_service_update_mock.assert_called_once_with(
        date_started=task.date_started,
        status=TaskStatus.COMPLETED,
        date_completed=current_date,
        force_save=True
    )
    remove_task_ws_mock.assert_called_once_with(
        task=task,
        user_ids={account_owner.id, user.id},
        sync=True
    )
    send_complete_task_notification_mock.assert_called_once_with(
        author_id=user.id,
        account_id=account.id,
        recipients=[(account_owner.id, account_owner.email)],
        task_id=task.id,
        logo_lg=account.logo_lg,
        logging=account.log_api_requests,
    )
    complete_task_webhook_mock.assert_not_called()
    end_workflow_mock.assert_not_called()
    next_task = workflow.tasks.get(number=2)
    action_method_mock.assert_called_once_with(next_task)
    action_method.assert_called_once_with(
        task=next_task,
        by_complete_task=True,
        is_returned=False,
        by_condition=True
    )
    task_complete_analytics_mock.assert_called_once_with(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow,
        task=task
    )
    task_complete_event_mock.assert_called_once_with(
        task=task,
        user=user
    )


def test_complete_task_for_user__by_account_owner__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(account=account)
    user = create_test_admin(account=account)
    deleted_user = create_test_admin(
        email="deleted@test.test",
        account=account
    )
    completed_performer = create_test_admin(
        email="completed@test.test",
        account=account
    )
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
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
    complete_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.complete_task'
    )
    field_value = 'drop the base'
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True

    service = WorkflowActionService(
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=account_owner,
        sync=sync
    )

    # act
    service.complete_task_for_user(
        task=task,
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
    complete_task_mock.assert_called_once_with(task=task, by_user=True)


def test_complete_task_for_user__by_user_performer__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(account=account)
    user = create_test_admin(account=account)
    deleted_user = create_test_admin(
        email="deleted@test.test",
        account=account
    )
    completed_performer = create_test_admin(
        email="completed@test.test",
        account=account
    )
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
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
    complete_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.complete_task'
    )

    field_value = 'drop the base'
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True

    service = WorkflowActionService(
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    service.complete_task_for_user(
        task=task,
        fields_values={
            task_field.api_name: field_value
        }
    )

    # assert
    task_field_service_init_mock.assert_called_once_with(
        user=user,
        instance=task_field
    )
    task_field_service_update_mock.assert_called_once_with(
        value=field_value,
        force_save=True
    )
    complete_task_mock.assert_called_once_with(task=task, by_user=True)


def test_complete_task_for_user__by_user__rcba__first_completion__ok(mocker):

    """ task with require completion by all completed by first performer """

    # arrange
    account = create_test_account()
    account_owner = create_test_user(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
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
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync,
    )

    # act
    service.complete_task_for_user(
        task=task,
    )

    # assert
    task_performer = task.taskperformer_set.get(user_id=user.id)
    assert task_performer.is_completed is True
    assert task_performer.date_completed == current_date
    task_field_service_init_mock.assert_not_called()
    task_field_service_update_mock.assert_not_called()
    complete_task_mock.assert_not_called()
    send_removed_task_notification_mock.assert_called_once_with(
        task=task,
        user_ids=(user.id,),
        sync=True
    )


def test_complete_task_for_user__by_user__rcba__last_completion__ok(mocker):

    """ task with require completion by all completed by last performer """

    # arrange
    account = create_test_account()
    account_owner = create_test_user(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
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
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    service.complete_task_for_user(
        task=task,
    )

    # assert
    task_field_service_init_mock.assert_not_called()
    task_field_service_update_mock.assert_not_called()
    complete_task_mock.assert_called_once_with(task=task, by_user=True)
    send_removed_task_notification_mock.assert_not_called()


def test_complete_task_for_user__by_guest_performer__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(account=account)
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(user=account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
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
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=guest,
        sync=sync
    )

    # act
    service.complete_task_for_user(
        task=task,
        fields_values={
            task_field.api_name: field_value
        }
    )

    # assert
    task_field_service_init_mock.assert_called_once_with(
        user=guest,
        instance=task_field
    )
    task_field_service_update_mock.assert_called_once_with(
        value=field_value,
        force_save=True
    )
    complete_task_mock.assert_called_once_with(task=task, by_user=True)


def test_complete_task_for_user__by_guest__rcba_first_completion__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(account=account)
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(user=account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
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
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=guest,
        sync=sync
    )

    # act
    service.complete_task_for_user(task=task)

    # assert
    task_performer = task.taskperformer_set.get(user_id=guest.id)
    assert task_performer.is_completed is True
    assert task_performer.date_completed == current_date

    task_field_service_init_mock.assert_not_called()
    task_field_service_update_mock.assert_not_called()
    complete_task_mock.assert_not_called()
    send_removed_task_notification_mock.assert_not_called()


def test_complete_task_for_user__by_guest_rcba_last_completion__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(account=account)
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(user=account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
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
    complete_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.complete_task'
    )
    is_superuser = False
    auth_type = AuthTokenType.GUEST
    sync = True

    service = WorkflowActionService(
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=guest,
        sync=sync
    )

    # act
    service.complete_task_for_user(task=task)

    # assert
    task_field_service_init_mock.assert_not_called()
    task_field_service_update_mock.assert_not_called()
    complete_task_mock.assert_called_once_with(task=task, by_user=True)


def test_complete_task_for_user__by_group_performer__ok(mocker):

    # arrange
    account = create_test_account()
    user = create_test_admin(account=account)
    performer = create_test_admin(
        account=account,
        email='test@test.test',
    )
    group = create_test_group(account, users=[performer])

    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
        directly_status=DirectlyStatus.CREATED
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
    complete_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.complete_task'
    )
    field_value = 'drop the base'
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True

    service = WorkflowActionService(
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=performer,
        sync=sync
    )

    # act
    service.complete_task_for_user(
        task=task,
        fields_values={
            task_field.api_name: field_value
        }
    )

    # assert
    task_field_service_init_mock.assert_called_once_with(
        user=performer,
        instance=task_field
    )
    task_field_service_update_mock.assert_called_once_with(
        value=field_value,
        force_save=True
    )
    complete_task_mock.assert_called_once_with(task=task, by_user=True)


def test_complete_task_for_user_by_group__rcba_first_completion__ok(mocker):

    # arrange
    account = create_test_account()
    user = create_test_admin(account=account)
    performer = create_test_admin(
        account=account,
        email='test@test.test',
    )
    group = create_test_group(account, users=[performer])

    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.require_completion_by_all = True
    task.save(update_fields=['require_completion_by_all'])
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
        directly_status=DirectlyStatus.CREATED
    )
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
    send_removed_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_removed_task_notification'
    )
    complete_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.complete_task'
    )

    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True

    service = WorkflowActionService(
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=performer,
        sync=sync
    )

    # act
    service.complete_task_for_user(task=task)

    # assert
    task_group_performer = task.taskperformer_set.get(group_id=group.id)
    assert task_group_performer.is_completed is True
    assert task_group_performer.date_completed == current_date
    task_field_service_init_mock.assert_not_called()
    task_field_service_update_mock.assert_not_called()
    complete_task_mock.assert_not_called()
    send_removed_task_notification_mock.assert_called_once_with(
        task=task,
        user_ids=(performer.id,),
        sync=True
    )


def test_complete_task_for_user_by_group__rcba_last_completion__ok(mocker):

    # arrange
    account = create_test_account()
    user = create_test_admin(account=account)
    performer = create_test_user(
        account=account,
        email='test@test.test',
    )
    group = create_test_group(account, users=[performer])
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.require_completion_by_all = True
    task.save(update_fields=['require_completion_by_all'])
    TaskPerformer.objects.filter(
        task_id=task.id,
        type=PerformerType.USER,
        user_id=user.id,
    ).update(is_completed=True)
    TaskPerformer.objects.create(
        task=task,
        type=PerformerType.GROUP,
        group_id=group.id,
    )
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
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=performer,
        sync=sync
    )

    # act
    service.complete_task_for_user(task=task)

    # assert
    task_field_service_init_mock.assert_not_called()
    task_field_service_update_mock.assert_not_called()
    complete_task_mock.assert_called_once_with(task=task, by_user=True)
    send_removed_task_notification_mock.assert_not_called()


def test_complete_task_for_user__delayed_workflow__raise_exception(mocker):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
        status=WorkflowStatus.DELAYED
    )
    task = workflow.tasks.get(number=1)
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None
    )
    task_field_service_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.field'
        '.TaskFieldService.partial_update'
    )
    complete_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.complete_task'
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True

    service = WorkflowActionService(
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    with pytest.raises(WorkflowActionServiceException) as ex:
        service.complete_task_for_user(task=task)

    # assert
    assert ex.value.message == messages.MSG_PW_0004
    task_field_service_init_mock.assert_not_called()
    task_field_service_update_mock.assert_not_called()
    complete_task_mock.assert_not_called()


def test_complete_task_for_user__completed_workflow__raise_exception(mocker):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
        status=WorkflowStatus.DONE
    )
    task = workflow.tasks.get(number=1)
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None
    )
    task_field_service_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.field'
        '.TaskFieldService.partial_update'
    )
    complete_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.complete_task'
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True

    service = WorkflowActionService(
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    with pytest.raises(WorkflowActionServiceException) as ex:
        service.complete_task_for_user(task=task)

    # assert
    assert ex.value.message == messages.MSG_PW_0008
    task_field_service_init_mock.assert_not_called()
    task_field_service_update_mock.assert_not_called()
    complete_task_mock.assert_not_called()


@pytest.mark.parametrize('status', TaskStatus.INACTIVE_STATUS)
def test_complete_task_for_user__inactive_task__raise_exception(
    mocker,
    status
):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    workflow = create_test_workflow(
        user=user,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task.status = status
    task.save()
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None
    )
    task_field_service_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.field'
        '.TaskFieldService.partial_update'
    )
    complete_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.complete_task'
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True

    service = WorkflowActionService(
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    with pytest.raises(WorkflowActionServiceException) as ex:
        service.complete_task_for_user(task=task)

    # assert
    assert ex.value.message == messages.MSG_PW_0086
    task_field_service_init_mock.assert_not_called()
    task_field_service_update_mock.assert_not_called()
    complete_task_mock.assert_not_called()


def test_complete_task_for_user__already_completed__raise_exception(mocker):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.filter(
        task=task,
        user=user
    ).update(
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
    complete_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.complete_task'
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True

    service = WorkflowActionService(
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    with pytest.raises(WorkflowActionServiceException) as ex:
        service.complete_task_for_user(task=task)

    # assert
    assert ex.value.message == messages.MSG_PW_0007
    task_field_service_init_mock.assert_not_called()
    task_field_service_update_mock.assert_not_called()
    complete_task_mock.assert_not_called()


def test_complete_task_for_user__not_acc_owner_not_performer__raise_exception(
    mocker
):

    # arrange
    account = create_test_account()
    owner = create_test_user(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    user = create_test_admin(account)
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None
    )
    task_field_service_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.field'
        '.TaskFieldService.partial_update'
    )
    complete_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.complete_task'
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True

    service = WorkflowActionService(
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    with pytest.raises(WorkflowActionServiceException) as ex:
        service.complete_task_for_user(task=task)

    # assert
    assert ex.value.message == messages.MSG_PW_0087
    task_field_service_init_mock.assert_not_called()
    task_field_service_update_mock.assert_not_called()
    complete_task_mock.assert_not_called()


def test_complete_task_for_user__deleted_performer__raise_exception(
    mocker
):

    # arrange
    account = create_test_account()
    owner = create_test_user(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    user = create_test_admin(account)
    TaskPerformer.objects.create(
        task=task,
        user=user,
        directly_status=DirectlyStatus.DELETED
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
    complete_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.complete_task'
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True

    service = WorkflowActionService(
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    with pytest.raises(WorkflowActionServiceException) as ex:
        service.complete_task_for_user(task=task)

    # assert
    assert ex.value.message == messages.MSG_PW_0087
    task_field_service_init_mock.assert_not_called()
    task_field_service_update_mock.assert_not_called()
    complete_task_mock.assert_not_called()


def test_complete_task_for_user__checklist_incompleted__raise_exception(
    mocker
):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.checklists_marked = 1
    task.checklists_total = 2
    task.save(update_fields=['checklists_marked', 'checklists_total'])

    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None
    )
    task_field_service_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.field'
        '.TaskFieldService.partial_update'
    )
    complete_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.complete_task'
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True

    service = WorkflowActionService(
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    with pytest.raises(WorkflowActionServiceException) as ex:
        service.complete_task_for_user(task=task)

    # assert
    assert ex.value.message == messages.MSG_PW_0006
    task_field_service_init_mock.assert_not_called()
    task_field_service_update_mock.assert_not_called()
    complete_task_mock.assert_not_called()


def test_complete_task_for_user__sub_workflows_incompleted__raise_exception(
    mocker
):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    create_test_workflow(
        user=user,
        tasks_count=1,
        ancestor_task=task
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
    complete_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.complete_task'
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True

    service = WorkflowActionService(
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    with pytest.raises(WorkflowActionServiceException) as ex:
        service.complete_task_for_user(task=task)

    # assert
    assert ex.value.message == messages.MSG_PW_0070
    task_field_service_init_mock.assert_not_called()
    task_field_service_update_mock.assert_not_called()
    complete_task_mock.assert_not_called()


def test_revert__to_default_revert_task__ok(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user,
        tasks_count=3,
        active_task_number=2
    )
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    task_revert_event_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowEventService.task_revert_event'
    )
    task_revert_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'task_returned'
    )
    return_workflow_to_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService._return_workflow_to_task'
    )
    start_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.start_task'
    )
    text_comment = 'text_comment'
    start_task_mock.__name__ = 'start_task'

    service = WorkflowActionService(user=user, workflow=workflow)

    # act
    service.revert(
        comment=text_comment,
        revert_from_task=task_2
    )

    # assert
    task_revert_event_mock.assert_called_once_with(
        task=task_1,
        user=user,
        text=text_comment,
        clear_text=text_comment
    )
    return_workflow_to_task_mock.assert_called_once_with(
        revert_from_task=task_2,
        revert_to_task=task_1,
    )
    task_revert_analytics_mock.assert_called_once_with(
        user=user,
        task=task_2,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )


def test_revert__to_custom_revert_task__ok(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user,
        tasks_count=3,
        active_task_number=3
    )
    task_1 = workflow.tasks.get(number=1)
    task_3 = workflow.tasks.get(number=3)
    task_3.revert_task = task_1.api_name
    task_3.save()
    workflow.save()
    task_revert_event_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowEventService.task_revert_event'
    )
    task_revert_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'task_returned'
    )
    return_workflow_to_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService._return_workflow_to_task'
    )
    start_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.start_task'
    )
    text_comment = 'text_comment'
    start_task_mock.__name__ = 'start_task'

    service = WorkflowActionService(workflow=workflow, user=user)

    # act
    service.revert(
        comment=text_comment,
        revert_from_task=task_3
    )

    # assert
    task_revert_event_mock.assert_called_once_with(
        task=task_1,
        user=user,
        text=text_comment,
        clear_text=text_comment
    )
    return_workflow_to_task_mock.assert_called_once_with(
        revert_from_task=task_3,
        revert_to_task=task_1,
    )
    task_revert_analytics_mock.assert_called_once_with(
        user=user,
        task=task_3,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )


def test_revert__snoozed_workflow__raise_exception(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user,
        status=WorkflowStatus.DELAYED,
        tasks_count=2,
        active_task_number=2
    )
    task_2 = workflow.tasks.get(number=2)
    task_revert_event_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowEventService.task_revert_event'
    )
    task_revert_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'task_returned'
    )
    return_workflow_to_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService._return_workflow_to_task'
    )
    start_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.start_task'
    )
    start_task_mock.__name__ = 'start_task'
    text_comment = 'text_comment'
    service = WorkflowActionService(user=user, workflow=workflow)

    # act
    with pytest.raises(exceptions.DelayedWorkflowCannotBeChanged) as ex:
        service.revert(
            comment=text_comment,
            revert_from_task=task_2
        )

    # assert
    assert ex.value.message == messages.MSG_PW_0072
    return_workflow_to_task_mock.assert_not_called()
    task_revert_event_mock.assert_not_called()
    task_revert_analytics_mock.assert_not_called()
    start_task_mock.assert_not_called()


def test_revert__completed_workflow__raise_exception(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user,
        status=WorkflowStatus.DONE,
        tasks_count=2,
        active_task_number=2,
    )
    task_2 = workflow.tasks.get(number=2)
    task_revert_event_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowEventService.task_revert_event'
    )
    task_revert_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'task_returned'
    )
    return_workflow_to_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService._return_workflow_to_task'
    )
    start_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.start_task'
    )
    start_task_mock.__name__ = 'start_task'
    text_comment = 'text_comment'
    service = WorkflowActionService(workflow=workflow, user=user)

    # act
    with pytest.raises(exceptions.CompletedWorkflowCannotBeChanged) as ex:
        service.revert(
            comment=text_comment,
            revert_from_task=task_2
        )

    # assert
    assert ex.value.message == messages.MSG_PW_0017
    return_workflow_to_task_mock.assert_not_called()
    task_revert_event_mock.assert_not_called()
    task_revert_analytics_mock.assert_not_called()
    start_task_mock.assert_not_called()


def test_revert__to_skipped_first_task__raise_exception(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user,
        tasks_count=2,
        active_task_number=2
    )
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    task_revert_event_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowEventService.task_revert_event'
    )
    task_revert_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'task_returned'
    )
    return_workflow_to_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService._return_workflow_to_task'
    )
    skip_task_mock = mocker.Mock()
    skip_task_mock.__name__ = 'skip_task'

    execute_condition_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.execute_condition',
        return_value=(skip_task_mock, None)
    )
    text_comment = 'text_comment'
    service = WorkflowActionService(workflow=workflow, user=user)

    # act
    with pytest.raises(exceptions.WorkflowActionServiceException) as ex:
        service.revert(
            comment=text_comment,
            revert_from_task=task_2,
        )

    # assert
    assert ex.value.message == messages.MSG_PW_0079(task_1.name)
    execute_condition_mock.assert_called_once_with(task_1)
    return_workflow_to_task_mock.assert_not_called()
    task_revert_event_mock.assert_not_called()
    task_revert_analytics_mock.assert_not_called()
    skip_task_mock.assert_not_called()


def test_revert__task_is_not_returnable__raise_exception(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user,
        tasks_count=3,
        active_task_number=3
    )
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    task_3 = workflow.tasks.get(number=3)
    task_revert_event_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowEventService.task_revert_event'
    )
    task_revert_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'task_returned'
    )
    return_workflow_to_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService._return_workflow_to_task'
    )
    skip_task_mock = mocker.Mock()
    skip_task_mock.__name__ = 'skip_task'
    execute_condition_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.execute_condition',
        return_value=(skip_task_mock, None)
    )
    task_is_returnable_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService._task_is_returnable',
        return_value=False
    )
    text_comment = 'text_comment'
    service = WorkflowActionService(workflow=workflow, user=user)

    # act
    with pytest.raises(exceptions.WorkflowActionServiceException) as ex:
        service.revert(
            comment=text_comment,
            revert_from_task=task_3
        )

    # assert
    assert ex.value.message == messages.MSG_PW_0080(task_2.name)
    execute_condition_mock.assert_called_once_with(task_2)
    task_is_returnable_mock.assert_called_once_with(task_1)
    return_workflow_to_task_mock.assert_not_called()
    task_revert_event_mock.assert_not_called()
    task_revert_analytics_mock.assert_not_called()
    skip_task_mock.assert_not_called()


@pytest.mark.parametrize('status', TaskStatus.INACTIVE_STATUS)
def test_revert__from_inactive_task__raise_exception(mocker, status):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user,
        tasks_count=3,
        active_task_number=2
    )
    task_2 = workflow.tasks.get(number=2)
    task_2.status = status
    task_2.save()
    task_revert_event_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowEventService.task_revert_event'
    )
    task_revert_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'task_returned'
    )
    return_workflow_to_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService._return_workflow_to_task'
    )
    start_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.start_task'
    )
    text_comment = 'text_comment'
    start_task_mock.__name__ = 'start_task'

    service = WorkflowActionService(user=user, workflow=workflow)

    # act
    with pytest.raises(WorkflowActionServiceException) as ex:
        service.revert(
            comment=text_comment,
            revert_from_task=task_2
        )

    # assert
    assert ex.value.message == messages.MSG_PW_0086
    task_revert_event_mock.assert_not_called()
    return_workflow_to_task_mock.assert_not_called()
    task_revert_analytics_mock.assert_not_called()


def test_revert__by_account_owner__ok(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(
        user,
        tasks_count=3,
        active_task_number=2
    )
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    task_revert_event_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowEventService.task_revert_event'
    )
    task_revert_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'task_returned'
    )
    return_workflow_to_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService._return_workflow_to_task'
    )
    start_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.start_task'
    )
    text_comment = 'text_comment'
    start_task_mock.__name__ = 'start_task'

    service = WorkflowActionService(user=user, workflow=workflow)

    # act
    service.revert(
        comment=text_comment,
        revert_from_task=task_2
    )

    # assert
    task_revert_event_mock.assert_called_once_with(
        task=task_1,
        user=user,
        text=text_comment,
        clear_text=text_comment
    )
    return_workflow_to_task_mock.assert_called_once_with(
        revert_from_task=task_2,
        revert_to_task=task_1,
    )
    task_revert_analytics_mock.assert_called_once_with(
        user=user,
        task=task_2,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )


def test_revert__by_user_performer__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        owner,
        tasks_count=3,
        active_task_number=2
    )
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    performer = create_test_admin(account=account)
    TaskPerformer.objects.create(
        task=task_2,
        user=performer,
    )
    task_revert_event_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowEventService.task_revert_event'
    )
    task_revert_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'task_returned'
    )
    return_workflow_to_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService._return_workflow_to_task'
    )
    start_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.start_task'
    )
    text_comment = 'text_comment'
    start_task_mock.__name__ = 'start_task'

    service = WorkflowActionService(user=performer, workflow=workflow)

    # act
    service.revert(
        comment=text_comment,
        revert_from_task=task_2
    )

    # assert
    task_revert_event_mock.assert_called_once_with(
        task=task_1,
        user=performer,
        text=text_comment,
        clear_text=text_comment
    )
    return_workflow_to_task_mock.assert_called_once_with(
        revert_from_task=task_2,
        revert_to_task=task_1,
    )
    task_revert_analytics_mock.assert_called_once_with(
        user=performer,
        task=task_2,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )


def test_revert__by_group_performer__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        owner,
        tasks_count=3,
        active_task_number=2
    )
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    task_2.performers.clear()
    performer = create_test_admin(account=account)
    group = create_test_group(account, users=[performer])
    TaskPerformer.objects.create(
        task=task_2,
        type=PerformerType.GROUP,
        group_id=group.id,
    )
    task_revert_event_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowEventService.task_revert_event'
    )
    task_revert_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'task_returned'
    )
    return_workflow_to_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService._return_workflow_to_task'
    )
    start_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.start_task'
    )
    text_comment = 'text_comment'
    start_task_mock.__name__ = 'start_task'
    service = WorkflowActionService(user=performer, workflow=workflow)

    # act
    service.revert(
        comment=text_comment,
        revert_from_task=task_2
    )

    # assert
    task_revert_event_mock.assert_called_once_with(
        task=task_1,
        user=performer,
        text=text_comment,
        clear_text=text_comment
    )
    return_workflow_to_task_mock.assert_called_once_with(
        revert_from_task=task_2,
        revert_to_task=task_1,
    )
    task_revert_analytics_mock.assert_called_once_with(
        user=performer,
        task=task_2,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )


def test_revert__by_guest_performer__validation_error(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_user(account=account)
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(
        owner,
        tasks_count=3,
        active_task_number=2
    )
    task_2 = workflow.tasks.get(number=2)
    task_2.performers.clear()
    task_2.performers.add(guest)
    task_revert_event_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowEventService.task_revert_event'
    )
    task_revert_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'task_returned'
    )
    return_workflow_to_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService._return_workflow_to_task'
    )
    start_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.start_task'
    )
    text_comment = 'text_comment'
    start_task_mock.__name__ = 'start_task'
    service = WorkflowActionService(user=guest, workflow=workflow)

    # act
    with pytest.raises(WorkflowActionServiceException) as ex:
        service.revert(
            comment=text_comment,
            revert_from_task=task_2
        )

    # assert
    assert ex.value.message == messages.MSG_PW_0011
    task_revert_event_mock.assert_not_called()
    return_workflow_to_task_mock.assert_not_called()
    task_revert_analytics_mock.assert_not_called()


def test_revert__not_performer__validation_error(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_user(account=account)
    workflow = create_test_workflow(
        owner,
        tasks_count=3,
        active_task_number=2
    )
    task_2 = workflow.tasks.get(number=2)
    user = create_test_admin(account=account)
    task_revert_event_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowEventService.task_revert_event'
    )
    task_revert_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'task_returned'
    )
    return_workflow_to_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService._return_workflow_to_task'
    )
    start_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.start_task'
    )
    text_comment = 'text_comment'
    start_task_mock.__name__ = 'start_task'
    service = WorkflowActionService(user=user, workflow=workflow)

    # act
    with pytest.raises(WorkflowActionServiceException) as ex:
        service.revert(
            comment=text_comment,
            revert_from_task=task_2
        )

    # assert
    assert ex.value.message == messages.MSG_PW_0087
    task_revert_event_mock.assert_not_called()
    return_workflow_to_task_mock.assert_not_called()
    task_revert_analytics_mock.assert_not_called()


def test_revert__deleted_performer__validation_error(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_user(account=account)
    workflow = create_test_workflow(
        owner,
        tasks_count=3,
        active_task_number=2
    )
    task_2 = workflow.tasks.get(number=2)
    performer = create_test_admin(account=account)
    TaskPerformer.objects.create(
        task=task_2,
        user=performer,
        directly_status=DirectlyStatus.DELETED
    )
    task_revert_event_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowEventService.task_revert_event'
    )
    task_revert_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'task_returned'
    )
    return_workflow_to_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService._return_workflow_to_task'
    )
    start_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.start_task'
    )
    text_comment = 'text_comment'
    start_task_mock.__name__ = 'start_task'
    service = WorkflowActionService(user=performer, workflow=workflow)

    # act
    with pytest.raises(WorkflowActionServiceException) as ex:
        service.revert(
            comment=text_comment,
            revert_from_task=task_2
        )

    # assert
    assert ex.value.message == messages.MSG_PW_0087
    task_revert_event_mock.assert_not_called()
    return_workflow_to_task_mock.assert_not_called()
    task_revert_analytics_mock.assert_not_called()


def test_return_to__ok(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user, tasks_count=4)
    task_1 = workflow.tasks.get(number=1)
    task_3 = workflow.tasks.get(number=3)

    workflow.current_task = 3
    workflow.save()
    workflow_revert_event_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowEventService.workflow_revert_event'
    )
    workflow_returned_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'workflow_returned'
    )
    return_workflow_to_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService._return_workflow_to_task'
    )
    start_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.start_task'
    )
    start_task_mock.__name__ = 'start_task'
    service = WorkflowActionService(user=user, workflow=workflow)

    # act
    service.return_to(revert_to_task=task_1)

    # assert
    return_workflow_to_task_mock.assert_called_once_with(
        revert_from_task=task_3,
        revert_to_task=task_1,
    )
    workflow_revert_event_mock.assert_called_once_with(
        task=task_3,
        user=user
    )
    workflow_returned_analytics_mock.assert_called_once_with(
        user=user,
        task=task_1,
        workflow=workflow,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )


def test_return_to__skipped_task__raise_exception(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user, tasks_count=3)
    workflow.current_task = 3
    workflow.save()
    task_2 = workflow.tasks.get(number=2)
    workflow_revert_event_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowEventService.workflow_revert_event'
    )
    workflow_returned_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'workflow_returned'
    )
    return_workflow_to_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService._return_workflow_to_task'
    )
    skip_task_mock = mocker.Mock()
    skip_task_mock.__name__ = 'skip_task'
    execute_condition_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.execute_condition',
        return_value=(skip_task_mock, None)
    )
    service = WorkflowActionService(user=user, workflow=workflow)

    # act
    with pytest.raises(exceptions.WorkflowActionServiceException) as ex:
        service.return_to(revert_to_task=task_2)

    # assert
    assert ex.value.message == messages.MSG_PW_0079(task_2.name)
    execute_condition_mock.assert_called_once_with(task_2)
    return_workflow_to_task_mock.assert_not_called()
    workflow_revert_event_mock.assert_not_called()
    workflow_returned_analytics_mock.assert_not_called()
    skip_task_mock.assert_not_called()


def test_return_workflow_to_task__is_revert__ok(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    current_date = timezone.now()
    workflow = create_test_workflow(user, tasks_count=3)
    create_task_returned_webhook(user)
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    task_2.date_started = current_date
    task_2.date_first_started = current_date
    task_2.save()
    (
        TaskPerformer.objects
        .filter(task_id__in=(2, 3))
        .update(is_completed=True, date_completed=current_date)
    )
    workflow.current_task = 2
    workflow.save()

    workflow_revert_event_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowEventService.workflow_revert_event'
    )
    start_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.start_task'
    )
    start_task_mock.__name__ = 'start_task'
    send_removed_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_removed_task_notification'
    )
    workflow_returned_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'workflow_returned'
    )
    send_task_returned_webhook_mock = mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay',
    )

    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True
    service = WorkflowActionService(
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync,
    )

    # act
    service._return_workflow_to_task(
        revert_from_task=task_2,
        revert_to_task=task_1,
    )

    # assert
    workflow.refresh_from_db()
    assert workflow.current_task == 1
    task_1.refresh_from_db()
    assert task_1.date_completed is None
    assert task_1.is_completed is False
    task_2.refresh_from_db()
    assert task_2.date_started is None
    assert task_2.date_first_started is not None
    task_3 = workflow.tasks.get(number=3)
    assert TaskPerformer.objects.filter(
        task__in=(task_3, task_2),
        user_id=user.id,
        is_completed=False,
        date_completed=None
    ).count() == 2
    workflow_revert_event_mock.assert_not_called()
    start_task_mock.assert_called_once_with(
        task=task_1,
        is_returned=True,
        by_condition=False,
    )
    send_removed_task_notification_mock.assert_called_once_with(task_2)
    workflow_returned_analytics_mock.assert_not_called()
    send_task_returned_webhook_mock.assert_called_once_with(
        user_id=user.id,
        account_id=user.account_id,
        payload=task_2.webhook_payload()
    )


def test_return_workflow_to_task__ok(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    create_task_returned_webhook(user)

    current_date = timezone.now()
    workflow = create_test_workflow(user, tasks_count=4)
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=1)
    task_3 = workflow.tasks.get(number=3)
    task_3.date_started = current_date
    task_3.date_first_started = current_date
    task_3.date_started = current_date
    task_3.status = TaskStatus.COMPLETED
    task_3.save()

    task_4 = workflow.tasks.get(number=4)
    task_4.date_completed = current_date
    task_4.date_first_started = current_date
    task_4.date_started = current_date
    task_4.status = TaskStatus.COMPLETED
    task_4.save()
    (
        TaskPerformer.objects
        .filter(task_id__in=(2, 3, 4))
        .update(is_completed=True, date_completed=current_date)
    )
    workflow.current_task = 3
    workflow.save()

    start_task_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.start_task'
    )
    start_task_mock.__name__ = 'start_task'
    send_removed_task_notification_mock = mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_removed_task_notification'
    )
    task_revert_analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'task_returned'
    )
    send_task_returned_webhook_mock = mocker.patch(
        'pneumatic_backend.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay',
    )

    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True
    service = WorkflowActionService(
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    service._return_workflow_to_task(
        revert_from_task=task_3,
        revert_to_task=task_1,
    )

    # assert
    workflow.refresh_from_db()
    assert workflow.current_task == 1
    task_4.refresh_from_db()
    assert task_4.date_started is None
    assert task_4.date_first_started is not None
    assert task_4.date_completed is None
    assert task_4.is_completed is False
    assert task_4.is_skipped is False
    task_3.refresh_from_db()
    assert task_3.date_started is None
    assert task_3.date_first_started is not None
    assert task_3.date_completed is None
    assert task_3.is_completed is False
    assert task_3.is_skipped is False
    assert TaskPerformer.objects.filter(
        task__in=(task_2, task_3, task_4),
        user_id=user.id,
        is_completed=False,
        date_completed=None
    ).count() == 3

    start_task_mock.assert_called_once_with(
        task=task_1,
        is_returned=True,
        by_condition=False,
    )
    send_removed_task_notification_mock.assert_called_once_with(task_3)
    task_revert_analytics_mock.assert_not_called()
    send_task_returned_webhook_mock.assert_called_once_with(
        user_id=user.id,
        account_id=user.account_id,
        payload=task_3.webhook_payload()
    )


@pytest.mark.parametrize('by_complete_task', (True, False))
def test_start_next_tasks__not_next_task__end_workflow(
    mocker,
    by_complete_task
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user, tasks_count=1)

    action_method = mocker.Mock()
    by_condition = True
    execute_condition_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.execute_condition',
        return_value=(action_method, by_condition)
    )
    end_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.end_process'
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True
    service = WorkflowActionService(
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    service.start_next_tasks(by_complete_task=by_complete_task)

    # assert
    execute_condition_mock.assert_not_called()
    end_workflow_mock.assert_called_once_with(
        by_condition=False,
        by_complete_task=by_complete_task,
    )


def test_start_next_tasks__revert_not_task__do_nothing(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user, tasks_count=1)

    action_method = mocker.Mock()
    by_condition = True
    execute_condition_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.execute_condition',
        return_value=(action_method, by_condition)
    )
    end_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.end_process'
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True
    service = WorkflowActionService(
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )

    # act
    service.start_next_tasks(is_returned=True)

    # assert
    execute_condition_mock.assert_not_called()
    end_workflow_mock.assert_not_called()


@pytest.mark.parametrize('by_complete_task', (True, False))
def test_start_next_tasks__task_exist__call_action_method(
    mocker,
    by_complete_task
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user, tasks_count=1)

    action_method = mocker.Mock()
    by_condition = False
    execute_condition_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.execute_condition',
        return_value=(action_method, by_condition)
    )
    end_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.end_process'
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True
    service = WorkflowActionService(
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )
    task = workflow.tasks.get(number=1)

    # act
    service.start_next_tasks(task=task, by_complete_task=by_complete_task)

    # assert
    execute_condition_mock.assert_called_once_with(task)
    action_method.assert_called_once_with(
        task=task,
        is_returned=False,
        by_condition=by_condition,
        by_complete_task=by_complete_task,
    )
    end_workflow_mock.assert_not_called()


def test_start_next_tasks__revert__call_action_method(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user, tasks_count=1)

    action_method = mocker.Mock()
    by_condition = False
    execute_condition_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.execute_condition',
        return_value=(action_method, by_condition)
    )
    end_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action'
        '.WorkflowActionService.end_process'
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    sync = True
    service = WorkflowActionService(
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=user,
        sync=sync
    )
    task = workflow.tasks.get(number=1)

    # act
    service.start_next_tasks(
        task=task,
        is_returned=True
    )

    # assert
    execute_condition_mock.assert_called_once_with(task)
    action_method.assert_called_once_with(
        task=task,
        is_returned=True,
    )
    end_workflow_mock.assert_not_called()
