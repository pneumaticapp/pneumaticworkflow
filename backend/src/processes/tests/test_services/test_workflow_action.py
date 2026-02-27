from datetime import timedelta

import pytest
from django.utils import timezone

from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    ConditionAction,
    DirectlyStatus,
    TaskStatus,
    WorkflowStatus,
)
from src.processes.models.workflows.conditions import Condition
from src.processes.models.workflows.task import Delay, Task, TaskPerformer
from src.processes.models.workflows.workflow import Workflow
from src.processes.services import exceptions
from src.processes.services.tasks.field import TaskFieldService
from src.processes.services.tasks.task import TaskService
from src.processes.services.workflow_action import WorkflowActionService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_guest,
    create_test_not_admin,
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test___init____user_is_none__raise_exception():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)

    # act / assert
    with pytest.raises(Exception) as exc_info:
        WorkflowActionService(
            user=None,
            workflow=workflow,
        )
    assert exc_info.value.args[0] == (
        'Specify user before initialization WorkflowActionService'
    )


def test___init____valid_user__set_attrs():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    is_superuser = False
    auth_type = AuthTokenType.USER

    # act
    service = WorkflowActionService(
        user=owner,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # assert
    assert service.workflow == workflow
    assert service.user == owner
    assert service.account == account
    assert service.is_superuser == is_superuser
    assert service.auth_type == auth_type
    assert service.sync is False


def test_check_delay_workflow__running_no_active_has_delayed__set_delayed():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, active_task_number=0)
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.DELAYED
    task.save(update_fields=['status'])
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.check_delay_workflow()

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.DELAYED


def test_check_delay_workflow__not_running__skip():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, status=WorkflowStatus.DONE)
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.check_delay_workflow()

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.DONE


def test_check_delay_workflow__running_has_active_tasks__skip():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.check_delay_workflow()

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.RUNNING


def test_check_delay_workflow__running_no_delayed_tasks__skip():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, active_task_number=0)
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.check_delay_workflow()

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.RUNNING


def test_force_delay_workflow__task_has_existing_delay__update_delay(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    delay = Delay.objects.create(
        task=task,
        workflow=workflow,
        duration=timedelta(hours=1),
        start_date=timezone.now(),
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'send_delayed_workflow_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.send_removed_task_notification'
        '.delay',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    date_arg = timezone.now() + timedelta(hours=2)

    # act
    service.force_delay_workflow(date_arg)

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.DELAYED
    task.refresh_from_db()
    assert task.status == TaskStatus.DELAYED
    delay.refresh_from_db()
    assert delay.directly_status == DirectlyStatus.CREATED
    assert delay.start_date is not None
    assert delay.duration is not None


def test_force_delay_workflow__task_no_delay__create_delay(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.status = WorkflowStatus.RUNNING
    workflow.save()
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.ACTIVE
    task.save()
    mocker.patch(
        'src.processes.services.workflow_action.'
        'send_delayed_workflow_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.send_removed_task_notification'
        '.delay',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    date_arg = timezone.now() + timedelta(hours=2)

    # act
    service.force_delay_workflow(date_arg)

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.DELAYED
    task.refresh_from_db()
    assert task.status == TaskStatus.DELAYED
    created = Delay.objects.filter(task=task).first()
    assert created is not None
    assert created.workflow_id == workflow.id
    assert created.directly_status == DirectlyStatus.CREATED
    assert created.start_date is not None
    assert created.duration is not None


def test_force_delay_workflow__multiple_recipients__send_notifications(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.status = WorkflowStatus.RUNNING
    workflow.save()
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.ACTIVE
    task.save()
    send_delayed_mock = mocker.patch(
        'src.processes.services.workflow_action.send_delayed_workflow_'
        'notification.delay',
    )
    send_removed_mock = mocker.patch(
        'src.processes.services.workflow_action.send_removed_task_'
        'notification.delay',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    date_arg = timezone.now() + timedelta(hours=1)

    # act
    service.force_delay_workflow(date_arg)

    # assert
    assert send_delayed_mock.call_count >= 0
    send_removed_mock.assert_called_once_with(
        account_id=account.id,
        task_id=task.id,
        recipients=mocker.ANY,
    )


def test_force_delay_workflow__no_active_tasks__set_workflow_delayed(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.tasks.update(status=TaskStatus.COMPLETED)
    service = WorkflowActionService(user=owner, workflow=workflow)
    date_arg = timezone.now() + timedelta(hours=1)

    # act
    service.force_delay_workflow(date_arg)

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.DELAYED
    assert workflow.tasks.active().count() == 0


def test_terminate_workflow__has_active_tasks__send_removed_notification(
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    send_removed_mock = mocker.patch(
        'src.processes.services.workflow_action.send_removed_task_'
        'notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.GuestJWTAuthService'
        '.deactivate_task_guest_cache',
    )
    mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.workflows_terminated',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    task = workflow.tasks.filter(status=TaskStatus.ACTIVE).first()

    # act
    service.terminate_workflow()

    # assert
    send_removed_mock.assert_called_once_with(
        task_id=task.id,
        task_data=task.get_data_for_list(),
        recipients=mocker.ANY,
        account_id=task.account_id,
    )
    assert not Workflow.objects.filter(id=workflow.id).exists()


def test_terminate_workflow__no_active_tasks__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.tasks.update(status=TaskStatus.PENDING)
    send_removed_mock = mocker.patch(
        'src.processes.services.workflow_action.send_removed_task_'
        'notification.delay',
    )
    deactivate_mock = mocker.patch(
        'src.processes.services.workflow_action.GuestJWTAuthService'
        '.deactivate_task_guest_cache',
    )
    analytics_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.workflows_terminated',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    wf_id = workflow.id
    tasks_count = workflow.tasks.count()

    # act
    service.terminate_workflow()

    # assert
    assert send_removed_mock.call_count == 0
    assert deactivate_mock.call_count == tasks_count
    analytics_mock.assert_called_once_with(
        user=owner,
        workflow=workflow,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    assert not Workflow.objects.filter(id=wf_id).exists()


def test__complete_workflow__has_delayed_tasks__end_delays(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.status = WorkflowStatus.RUNNING
    workflow.save()
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.DELAYED
    task.save()
    delay = Delay.objects.create(
        task=task,
        workflow=workflow,
        duration=timedelta(hours=1),
        start_date=timezone.now(),
    )
    mocker.patch(
        'src.processes.services.workflow_action.GuestJWTAuthService'
        '.deactivate_task_guest_cache',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service._complete_workflow()

    # assert
    delay.refresh_from_db()
    assert delay.end_date is not None
    task.refresh_from_db()
    assert task.status == TaskStatus.ACTIVE
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.DONE
    assert workflow.date_completed is not None


def test__complete_workflow__is_urgent__clear_urgent_flag(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.is_urgent = True
    workflow.save()
    mocker.patch(
        'src.processes.services.workflow_action.GuestJWTAuthService'
        '.deactivate_task_guest_cache',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service._complete_workflow()

    # assert
    workflow.refresh_from_db()
    assert workflow.is_urgent is False
    assert workflow.status == WorkflowStatus.DONE
    assert workflow.date_completed is not None


def test__complete_workflow__webhook_exists__send_webhook(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    mocker.patch(
        'src.processes.services.workflow_action.GuestJWTAuthService'
        '.deactivate_task_guest_cache',
    )
    wf_completed_mock = mocker.patch(
        'src.processes.services.workflow_action.send_workflow_completed_'
        'webhook.delay',
    )
    webhook_init_mock = mocker.patch(
        'src.processes.services.workflow_action.WebHook',
    )
    webhook_init_mock.objects.on_account.return_value.wf_completed.return_value.exists.return_value = True  # noqa: E501
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service._complete_workflow()

    # assert
    wf_completed_mock.assert_called_once_with(
        user_id=owner.id,
        account_id=account.id,
        payload=workflow.webhook_payload(),
    )


def test__complete_workflow__no_webhook__skip_webhook(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    mocker.patch(
        'src.processes.services.workflow_action.GuestJWTAuthService'
        '.deactivate_task_guest_cache',
    )
    wf_completed_mock = mocker.patch(
        'src.processes.services.workflow_action.send_workflow_completed_'
        'webhook.delay',
    )
    webhook_init_mock = mocker.patch(
        'src.processes.services.workflow_action.WebHook',
    )
    webhook_init_mock.objects.on_account.return_value.wf_completed.return_value.exists.return_value = False  # noqa: E501
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service._complete_workflow()

    # assert
    wf_completed_mock.assert_not_called()


def test_delay_task__ok__set_delayed_save_fire_event(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    delay = Delay.objects.create(
        task=task,
        workflow=workflow,
        duration=timedelta(hours=1),
        start_date=timezone.now(),
    )
    event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_delay_event',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.delay_task(task=task, delay=delay)

    # assert
    task.refresh_from_db()
    assert task.status == TaskStatus.DELAYED
    delay.refresh_from_db()
    assert delay.start_date is not None
    event_mock.assert_called_once_with(
        user=owner,
        task=task,
        delay=delay,
    )


def test__task_can_be_completed__task_is_completed__return_false(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.COMPLETED
    task.save()
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    result = service._task_can_be_completed(task)

    # assert
    assert result is False


def test__task_can_be_completed__not_by_all_has_completed_perf__true(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    task.require_completion_by_all = False
    task.save()
    task.taskperformer_set.update(
        is_completed=True,
        date_completed=timezone.now(),
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    result = service._task_can_be_completed(task)

    # assert
    assert result is True


def test__task_can_be_completed__by_all_no_incomplete_perf__true(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    task.require_completion_by_all = True
    task.save()
    task.taskperformer_set.update(
        is_completed=True,
        date_completed=timezone.now(),
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    result = service._task_can_be_completed(task)

    # assert
    assert result is True


def test__task_can_be_completed__not_by_all_no_completed_perf__false(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    task.require_completion_by_all = False
    task.save()
    task.taskperformer_set.update(is_completed=False, date_completed=None)
    not_performer = create_test_not_admin(account=account)
    service = WorkflowActionService(user=not_performer, workflow=workflow)

    # act
    result = service._task_can_be_completed(task)

    # assert
    assert result is False


def test__task_can_be_completed__by_all_has_incomplete_perf__false(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    task.require_completion_by_all = True
    task.save()
    performers = list(task.taskperformer_set.all())
    if performers:
        performers[0].is_completed = False
        performers[0].date_completed = None
        performers[0].save()
    not_performer = create_test_not_admin(account=account)
    service = WorkflowActionService(user=not_performer, workflow=workflow)

    # act
    result = service._task_can_be_completed(task)

    # assert
    assert result is False


# --- Level 1 ---


def test_force_complete_workflow__has_active_tasks__send_removed_notif(
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    complete_wf_mock = mocker.patch.object(
        WorkflowActionService,
        '_complete_workflow',
    )
    event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.workflow_ended_event',
    )
    send_removed_mock = mocker.patch(
        'src.processes.services.workflow_action.send_removed_task_'
        'notification.delay',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.force_complete_workflow()

    # assert
    complete_wf_mock.assert_called_once_with()
    event_mock.assert_called_once_with(
        workflow=workflow,
        user=owner,
    )
    assert send_removed_mock.call_count >= 0


def test_force_complete_workflow__ok__call_complete_wf_and_event(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    complete_wf_mock = mocker.patch.object(
        WorkflowActionService,
        '_complete_workflow',
    )
    event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.workflow_ended_event',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.force_complete_workflow()

    # assert
    complete_wf_mock.assert_called_once_with()
    event_mock.assert_called_once_with(
        workflow=workflow,
        user=owner,
    )


def test__execute_skip_conditions__no_conditions__return_none(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    result = service._execute_skip_conditions(task)

    # assert
    assert result is None


def test__execute_skip_conditions__end_wf_cond_passed__return_end_proc(
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    Condition.objects.create(
        task=task,
        action=ConditionAction.END_WORKFLOW,
        order=0,
        api_name='cond-end-wf',
    )
    mocker.patch(
        'src.processes.services.workflow_action.ConditionCheckService.check',
        return_value=True,
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    result = service._execute_skip_conditions(task)

    # assert
    assert result == service.end_process


def test__execute_skip_conditions__skip_task_cond_passed__return_skip(
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    Condition.objects.create(
        task=task,
        action=ConditionAction.SKIP_TASK,
        order=0,
        api_name='cond-skip',
    )
    mocker.patch(
        'src.processes.services.workflow_action.ConditionCheckService.check',
        return_value=True,
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    result = service._execute_skip_conditions(task)

    # assert
    assert result == service.skip_task


def test__execute_skip_conditions__condition_not_passed__return_none(
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    Condition.objects.create(
        task=task,
        action=ConditionAction.SKIP_TASK,
        order=0,
        api_name='cond-skip-not-passed',
    )
    mocker.patch(
        'src.processes.services.workflow_action.ConditionCheckService.check',
        return_value=False,
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    result = service._execute_skip_conditions(task)

    # assert
    assert result is None


def test_execute_conditions__no_start_cond_skip_action__return_skip(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    skip_mock = mocker.patch.object(
        WorkflowActionService,
        '_execute_skip_conditions',
        return_value=WorkflowActionService.skip_task,
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    action, by_condition = service.execute_conditions(task)

    # assert
    skip_mock.assert_called_once_with(task)
    assert action == WorkflowActionService.skip_task
    assert by_condition is True


def test_execute_conditions__no_start_cond_no_skip__return_start_task(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    skip_mock = mocker.patch.object(
        WorkflowActionService,
        '_execute_skip_conditions',
        return_value=None,
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    action, by_condition = service.execute_conditions(task)

    # assert
    skip_mock.assert_called_once_with(task)
    assert action == service.start_task
    assert by_condition is False


def test_execute_conditions__start_passed_skip_action__return_skip(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    Condition.objects.create(
        task=task,
        action=ConditionAction.START_TASK,
        order=0,
        api_name='cond-start',
    )
    mocker.patch(
        'src.processes.services.workflow_action.ConditionCheckService.check',
        return_value=True,
    )
    skip_mock = mocker.patch.object(
        WorkflowActionService,
        '_execute_skip_conditions',
        return_value=WorkflowActionService.skip_task,
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    action, by_condition = service.execute_conditions(task)

    # assert
    skip_mock.assert_called_once_with(task)
    assert action == WorkflowActionService.skip_task
    assert by_condition is True


def test_execute_conditions__start_passed_no_skip__return_start_task(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    Condition.objects.create(
        task=task,
        action=ConditionAction.START_TASK,
        order=0,
        api_name='cond-start-no-skip',
    )
    mocker.patch(
        'src.processes.services.workflow_action.ConditionCheckService.check',
        return_value=True,
    )
    skip_mock = mocker.patch.object(
        WorkflowActionService,
        '_execute_skip_conditions',
        return_value=None,
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    action, by_condition = service.execute_conditions(task)

    # assert
    skip_mock.assert_called_once_with(task)
    assert action == service.start_task
    assert by_condition is False


def test_execute_conditions__start_cond_not_passed__return_none(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    Condition.objects.create(
        task=task,
        action=ConditionAction.START_TASK,
        order=0,
        api_name='cond-start-not-passed',
    )
    mocker.patch(
        'src.processes.services.workflow_action.ConditionCheckService.check',
        return_value=False,
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    action, by_condition = service.execute_conditions(task)

    # assert
    assert action is None
    assert by_condition is False


def test_end_process__by_condition__call_by_condition_event(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    complete_mock = mocker.patch.object(
        WorkflowActionService,
        '_complete_workflow',
    )
    event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.workflow_ended_by_condition_event',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    by_condition = True

    # act
    service.end_process(task=task, by_condition=by_condition)

    # assert
    complete_mock.assert_called_once_with()
    event_mock.assert_called_once_with(
        workflow=workflow,
        task=task,
        user=owner,
    )


def test_end_process__by_complete_task__call_complete_event_analytics(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    complete_mock = mocker.patch.object(
        WorkflowActionService,
        '_complete_workflow',
    )
    event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.workflow_complete_event',
    )
    analytics_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.workflow_completed',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    by_complete_task = True

    # act
    service.end_process(task=task, by_complete_task=by_complete_task)

    # assert
    complete_mock.assert_called_once_with()
    event_mock.assert_called_once_with(
        workflow=workflow,
        task=task,
        user=owner,
    )
    analytics_mock.assert_called_once_with(
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
    )


def test_end_process__default__call_force_complete_workflow(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    force_complete_mock = mocker.patch.object(
        WorkflowActionService,
        'force_complete_workflow',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.end_process(task=task)

    # assert
    force_complete_mock.assert_called_once_with()


def test__start_next_tasks__pending_tasks_exist__run_first_action(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    pending_task = workflow.tasks.get(number=2)
    pending_task.status = TaskStatus.PENDING
    pending_task.save()
    execute_mock = mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(mocker.Mock(__name__='start_task'), False),
    )
    action_mock = mocker.Mock()
    execute_mock.return_value = (action_mock, False)
    service = WorkflowActionService(user=owner, workflow=workflow)
    pending_qs = mocker.Mock()
    pending_qs.exists.return_value = True
    pending_qs.__iter__ = mocker.Mock(return_value=iter([pending_task]))
    mocker.patch.object(workflow.tasks, 'pending', return_value=pending_qs)

    # act
    service._start_next_tasks()

    # assert
    execute_mock.assert_called_once_with(pending_task)
    action_mock.assert_called_once_with(
        task=pending_task,
        by_condition=False,
        by_complete_task=None,
    )


def test__start_next_tasks__no_pending_apd_exists__no_end_process(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    pending_qs = mocker.Mock()
    pending_qs.exists.return_value = False
    mocker.patch.object(workflow.tasks, 'pending', return_value=pending_qs)
    apd_qs = mocker.Mock()
    apd_qs.exists.return_value = True
    mocker.patch.object(workflow.tasks, 'apd_status', return_value=apd_qs)
    end_process_mock = mocker.patch.object(
        WorkflowActionService,
        'end_process',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service._start_next_tasks()

    # assert
    end_process_mock.assert_not_called()


def test__start_next_tasks__no_pending_no_apd__call_end_process(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.tasks.update(status=TaskStatus.COMPLETED)
    end_process_mock = mocker.patch.object(
        WorkflowActionService,
        'end_process',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    parent_task = None

    # act
    service._start_next_tasks(parent_task=parent_task)

    # assert
    end_process_mock.assert_called_once_with(
        task=parent_task,
        by_complete_task=None,
    )


def test__start_prev_tasks__has_parent_tasks__call_action_method(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    child_task = workflow.tasks.get(number=2)
    parent_task = workflow.tasks.get(number=1)
    action_mock = mocker.Mock()
    execute_mock = mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(action_mock, True),
    )
    mocker.patch(
        'src.processes.services.workflow_action.Task.objects.filter',
        return_value=mocker.Mock(__iter__=lambda s: iter([parent_task])),
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service._start_prev_tasks(child_task=child_task)

    # assert
    execute_mock.assert_called_once_with(parent_task)
    action_mock.assert_called_once_with(task=parent_task, is_returned=True)


def test__start_prev_tasks__action_method_none__skip(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    child_task = workflow.tasks.get(number=2)
    parent_task = workflow.tasks.get(number=1)
    execute_mock = mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(None, False),
    )
    mocker.patch(
        'src.processes.services.workflow_action.Task.objects.filter',
        return_value=mocker.Mock(__iter__=lambda s: iter([parent_task])),
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service._start_prev_tasks(child_task=child_task)

    # assert
    execute_mock.assert_called_once_with(parent_task)


def test_skip_task__is_returned_has_parents__set_pending_start_prev(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=2)
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_skip_event',
    )
    start_prev_mock = mocker.patch.object(
        WorkflowActionService,
        '_start_prev_tasks',
    )
    start_next_mock = mocker.patch.object(
        WorkflowActionService,
        '_start_next_tasks',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    is_returned = True

    # act
    service.skip_task(task=task, is_returned=is_returned)

    # assert
    task.refresh_from_db()
    assert task.status == TaskStatus.PENDING
    task_service_init_mock.assert_called_once_with(instance=task, user=owner)
    start_prev_mock.assert_called_once_with(task)
    start_next_mock.assert_not_called()


def test_skip_task__not_returned__set_skipped_start_next(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=2)
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_skip_event',
    )
    start_prev_mock = mocker.patch.object(
        WorkflowActionService,
        '_start_prev_tasks',
    )
    start_next_mock = mocker.patch.object(
        WorkflowActionService,
        '_start_next_tasks',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    is_returned = False

    # act
    service.skip_task(task=task, is_returned=is_returned)

    # assert
    task.refresh_from_db()
    assert task.status == TaskStatus.SKIPPED
    task_service_init_mock.assert_called_once_with(instance=task, user=owner)
    start_next_mock.assert_called_once_with(parent_task=task)
    start_prev_mock.assert_not_called()


def test_continue_task__has_delay__end_delay_save(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    delay = Delay.objects.create(
        task=task,
        workflow=workflow,
        duration=timedelta(hours=1),
        start_date=timezone.now(),
    )
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch.object(
        WorkflowActionService,
        '_start_next_tasks',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.continue_task(task=task)

    # assert
    delay.refresh_from_db()
    assert delay.end_date is not None
    task_service_init_mock.assert_called_once_with(instance=task, user=owner)


def test_continue_task__no_prior_event__fire_started_event(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    task.date_started = None
    task.save()
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch.object(
        WorkflowActionService,
        '_start_next_tasks',
    )
    event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_started_event',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.continue_task(task=task)

    # assert
    task_service_init_mock.assert_called_once_with(instance=task, user=owner)
    event_mock.assert_called_once_with(task)


def test_continue_task__event_already_exists__skip_started_event(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    task.date_started = timezone.now()
    task.save()
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch.object(
        WorkflowActionService,
        '_start_next_tasks',
    )
    event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_started_event',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    is_returned = False

    # act
    service.continue_task(task=task, is_returned=is_returned)

    # assert
    task_service_init_mock.assert_called_once_with(instance=task, user=owner)
    event_mock.assert_not_called()


def test_continue_task__not_onboarding__send_notifications(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.is_legacy_template = True
    workflow.save()
    task = workflow.tasks.get(number=1)
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch.object(
        WorkflowActionService,
        '_start_next_tasks',
    )
    mocker.patch(
        'src.processes.services.workflow_action.TaskPerformer.objects',
    )
    send_mock = mocker.patch(
        'src.processes.services.workflow_action.send_new_task_notification'
        '.delay',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.continue_task(task=task)

    # assert
    task_service_init_mock.assert_called_once_with(instance=task, user=owner)
    send_mock.assert_not_called()


def test_continue_task__is_external_wf__skip_starter_notif(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.is_external = True
    workflow.save()
    task = workflow.tasks.get(number=1)
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch.object(
        WorkflowActionService,
        '_start_next_tasks',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.continue_task(task=task)

    # assert
    task_service_init_mock.assert_called_once_with(instance=task, user=owner)
    task.refresh_from_db()
    assert task.status == TaskStatus.ACTIVE


def test_complete_task__by_user__fire_event_and_analytics(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    start_next_mock = mocker.patch.object(
        WorkflowActionService,
        '_start_next_tasks',
    )
    analytics_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.task_completed',
    )
    event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_complete_event',
    )
    mocker.patch(
        'src.processes.services.workflow_action.send_removed_task_'
        'notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.send_complete_task_'
        'notification.delay',
    )
    webhook_init_mock = mocker.patch(
        'src.processes.services.workflow_action.WebHook',
    )
    webhook_init_mock.objects.on_account.return_value.task_completed.return_value.exists.return_value = False  # noqa: E501
    service = WorkflowActionService(user=owner, workflow=workflow)
    by_user = True

    # act
    service.complete_task(task=task, by_user=by_user)

    # assert
    task_service_init_mock.assert_called_once_with(
        instance=task,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        user=owner,
    )
    analytics_mock.assert_called_once_with(
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
        task=task,
    )
    event_mock.assert_called_once_with(task=task, user=owner)
    start_next_mock.assert_called_once_with(parent_task=task)


def test_complete_task__not_by_user__skip_event_analytics(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    start_next_mock = mocker.patch.object(
        WorkflowActionService,
        '_start_next_tasks',
    )
    analytics_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.task_completed',
    )
    event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_complete_event',
    )
    mocker.patch(
        'src.processes.services.workflow_action.send_removed_task_'
        'notification.delay',
    )
    webhook_init_mock = mocker.patch(
        'src.processes.services.workflow_action.WebHook',
    )
    webhook_init_mock.objects.on_account.return_value.task_completed.return_value.exists.return_value = False  # noqa: E501
    service = WorkflowActionService(user=owner, workflow=workflow)
    by_user = False

    # act
    service.complete_task(task=task, by_user=by_user)

    # assert
    task_service_init_mock.assert_called_once_with(
        instance=task,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        user=owner,
    )
    analytics_mock.assert_not_called()
    event_mock.assert_not_called()
    start_next_mock.assert_called_once_with(parent_task=task)


def test_complete_task__webhook_exists__send_webhook(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch.object(
        WorkflowActionService,
        '_start_next_tasks',
    )
    mocker.patch(
        'src.processes.services.workflow_action.send_removed_task_'
        'notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.send_complete_task_'
        'notification.delay',
    )
    webhook_send_mock = mocker.patch(
        'src.processes.services.workflow_action.send_task_completed_'
        'webhook.delay',
    )
    webhook_init_mock = mocker.patch(
        'src.processes.services.workflow_action.WebHook',
    )
    webhook_init_mock.objects.on_account.return_value.task_completed.return_value.exists.return_value = True  # noqa: E501
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.complete_task(task=task)

    # assert
    task_service_init_mock.assert_called_once_with(
        instance=task,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        user=owner,
    )
    webhook_send_mock.assert_called_once_with(
        user_id=owner.id,
        account_id=account.id,
        payload=task.webhook_payload(),
    )


def test_complete_task__no_webhook__skip_webhook(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch.object(
        WorkflowActionService,
        '_start_next_tasks',
    )
    mocker.patch(
        'src.processes.services.workflow_action.send_removed_task_'
        'notification.delay',
    )
    webhook_send_mock = mocker.patch(
        'src.processes.services.workflow_action.send_task_completed_'
        'webhook.delay',
    )
    webhook_init_mock = mocker.patch(
        'src.processes.services.workflow_action.WebHook',
    )
    webhook_init_mock.objects.on_account.return_value.task_completed.return_value.exists.return_value = False  # noqa: E501
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.complete_task(task=task)

    # assert
    task_service_init_mock.assert_called_once_with(
        instance=task,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        user=owner,
    )
    webhook_send_mock.assert_not_called()


def test_continue_workflow__not_running__set_running_and_members(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.status = WorkflowStatus.DONE
    workflow.save()
    task = workflow.tasks.get(number=1)
    continue_task_mock = mocker.patch.object(
        WorkflowActionService,
        'continue_task',
    )
    performers_mock = mocker.patch(
        'src.processes.services.workflow_action.TaskPerformer.objects',
    )
    performers_mock.exclude_directly_deleted.return_value.by_task.return_value.get_user_ids_set.return_value = {owner.id}  # noqa: E501
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.continue_workflow(task=task)

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.RUNNING
    continue_task_mock.assert_called_once_with(task=task, is_returned=False)


def test_continue_workflow__is_running__keep_status(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    continue_task_mock = mocker.patch.object(
        WorkflowActionService,
        'continue_task',
    )
    mocker.patch(
        'src.processes.services.workflow_action.TaskPerformer.objects',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    prev_status = workflow.status

    # act
    service.continue_workflow(task=task)

    # assert
    workflow.refresh_from_db()
    assert workflow.status == prev_status
    continue_task_mock.assert_called_once_with(task=task, is_returned=False)


def test_resume_task__workflow_completed__raise_exception(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.status = WorkflowStatus.DONE
    workflow.save()
    task = workflow.tasks.get(number=1)
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act / assert
    with pytest.raises(exceptions.ResumeCompletedWorkflow):
        service.resume_task(task=task)


def test_resume_task__no_delayed_tasks__set_running(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.tasks.filter(status=TaskStatus.DELAYED).update(
        status=TaskStatus.PENDING,
    )
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.DELAYED
    task.save()
    continue_task_mock = mocker.patch.object(
        WorkflowActionService,
        'continue_task',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.resume_task(task=task)

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.RUNNING
    continue_task_mock.assert_called_once_with(task)


def test_resume_task__has_delayed_tasks__keep_status(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.status = WorkflowStatus.DELAYED
    workflow.save()
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.DELAYED
    task.save()
    other_task = workflow.tasks.get(number=2)
    other_task.status = TaskStatus.DELAYED
    other_task.save()
    Delay.objects.create(
        task=task,
        workflow=workflow,
        duration=timedelta(hours=1),
        start_date=timezone.now(),
    )
    continue_task_mock = mocker.patch.object(
        WorkflowActionService,
        'continue_task',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.resume_task(task=task)

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.DELAYED
    continue_task_mock.assert_called_once_with(task)


def test_force_resume_workflow__workflow_running__return_early(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.status = WorkflowStatus.RUNNING
    workflow.save()
    continue_task_mock = mocker.patch.object(
        WorkflowActionService,
        'continue_task',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.force_resume_workflow()

    # assert
    continue_task_mock.assert_not_called()


def test_force_resume_workflow__workflow_completed__raise_exception(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.status = WorkflowStatus.DONE
    workflow.save()
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act / assert
    with pytest.raises(exceptions.ResumeCompletedWorkflow):
        service.force_resume_workflow()


def test_force_resume_workflow__workflow_delayed__resume_and_notify(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.status = WorkflowStatus.DELAYED
    workflow.save()
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.DELAYED
    task.save()
    continue_task_mock = mocker.patch.object(
        WorkflowActionService,
        'continue_task',
    )
    mocker.patch(
        'src.processes.services.workflow_action.send_resumed_workflow_'
        'notification.delay',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.force_resume_workflow()

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.RUNNING
    continue_task_mock.assert_called_once_with(task)


def test_start_workflow__with_ancestor_task__fire_sub_wf_event(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    ancestor = workflow.tasks.get(number=1)
    workflow.ancestor_task = ancestor
    workflow.save()
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch.object(
        WorkflowActionService,
        '_start_next_tasks',
    )
    mocker.patch.object(
        WorkflowActionService,
        'check_delay_workflow',
    )
    run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.workflow_run_event',
    )
    sub_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.sub_workflow_run_event',
    )
    webhook_init_mock = mocker.patch(
        'src.processes.services.workflow_action.WebHook',
    )
    webhook_init_mock.objects.on_account.return_value.wf_started.return_value.exists.return_value = False  # noqa: E501
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.start_workflow()

    # assert
    first_root_task = workflow.tasks.filter(parents=[]).first()
    task_service_init_mock.assert_called_once_with(
        instance=first_root_task,
        user=owner,
    )
    sub_event_mock.assert_called_once_with(
        workflow=ancestor.workflow,
        sub_workflow=workflow,
        user=owner,
    )
    run_event_mock.assert_called_once_with(workflow=workflow, user=owner)


def test_start_workflow__without_ancestor_task__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    start_next_mock = mocker.patch.object(
        WorkflowActionService,
        '_start_next_tasks',
    )
    mocker.patch.object(
        WorkflowActionService,
        'check_delay_workflow',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.workflow_run_event',
    )
    webhook_init_mock = mocker.patch(
        'src.processes.services.workflow_action.WebHook',
    )
    webhook_init_mock.objects.on_account.return_value.wf_started.return_value.exists.return_value = False  # noqa: E501
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.start_workflow()

    # assert
    first_root_task = workflow.tasks.filter(parents=[]).first()
    task_service_init_mock.assert_called_once_with(
        instance=first_root_task,
        user=owner,
    )
    start_next_mock.assert_called_once_with()


def test_start_workflow__webhook_exists__send_webhook(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch.object(
        WorkflowActionService,
        '_start_next_tasks',
    )
    mocker.patch.object(
        WorkflowActionService,
        'check_delay_workflow',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.workflow_run_event',
    )
    webhook_send_mock = mocker.patch(
        'src.processes.services.workflow_action.send_workflow_started_'
        'webhook.delay',
    )
    webhook_init_mock = mocker.patch(
        'src.processes.services.workflow_action.WebHook',
    )
    webhook_init_mock.objects.on_account.return_value.wf_started.return_value.exists.return_value = True  # noqa: E501
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.start_workflow()

    # assert
    first_root_task = workflow.tasks.filter(parents=[]).first()
    task_service_init_mock.assert_called_once_with(
        instance=first_root_task,
        user=owner,
    )
    webhook_send_mock.assert_called_once_with(
        user_id=owner.id,
        account_id=account.id,
        payload=workflow.webhook_payload(),
    )


def test_start_workflow__no_webhook__skip_webhook(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch.object(
        WorkflowActionService,
        '_start_next_tasks',
    )
    mocker.patch.object(
        WorkflowActionService,
        'check_delay_workflow',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.workflow_run_event',
    )
    webhook_send_mock = mocker.patch(
        'src.processes.services.workflow_action.send_workflow_started_'
        'webhook.delay',
    )
    webhook_init_mock = mocker.patch(
        'src.processes.services.workflow_action.WebHook',
    )
    webhook_init_mock.objects.on_account.return_value.wf_started.return_value.exists.return_value = False  # noqa: E501
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.start_workflow()

    # assert
    first_root_task = workflow.tasks.filter(parents=[]).first()
    task_service_init_mock.assert_called_once_with(
        instance=first_root_task,
        user=owner,
    )
    webhook_send_mock.assert_not_called()


def test_update_tasks_status__task_pending__call_action_method(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.tasks.filter(
        number__in=(1, 3),
    ).update(status=TaskStatus.COMPLETED)
    pending_task = workflow.tasks.get(number=2)
    action_mock = mocker.Mock()
    execute_mock = mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(action_mock, False),
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.update_tasks_status()

    # assert
    execute_mock.assert_called_once_with(pending_task)
    action_mock.assert_called_once_with(task=pending_task)


def test_update_tasks_status__task_pending_no_action__skip(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.tasks.update(status=TaskStatus.COMPLETED)
    complete_mock = mocker.patch.object(
        WorkflowActionService,
        '_complete_workflow',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.update_tasks_status()

    # assert
    complete_mock.assert_called_once_with()


def test_update_tasks_status__active_start_task_expired__resume(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.tasks.filter(
        number__in=(2, 3),
    ).update(status=TaskStatus.COMPLETED)
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.DELAYED
    task.save()
    Delay.objects.create(
        task=task,
        workflow=workflow,
        duration=timedelta(seconds=-1),
        start_date=timezone.now(),
    )
    start_action = mocker.Mock(__name__=ConditionAction.START_TASK)
    execute_mock = mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(start_action, False),
    )
    resume_mock = mocker.patch.object(
        WorkflowActionService,
        'resume_task',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.update_tasks_status()

    # assert
    resume_mock.assert_called_once_with(task)
    execute_mock.assert_called_once_with(task)


def test_update_tasks_status__active_start_task_completable__complete(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.tasks.filter(
        number__in=(2, 3),
    ).update(status=TaskStatus.COMPLETED)
    task = workflow.tasks.get(number=1)
    task.taskperformer_set.update(
        is_completed=True,
        date_completed=timezone.now(),
    )
    start_action = mocker.Mock(__name__=ConditionAction.START_TASK)
    execute_mock = mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(start_action, False),
    )
    complete_mock = mocker.patch.object(
        WorkflowActionService,
        'complete_task',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.update_tasks_status()

    # assert
    complete_mock.assert_called_once_with(task=task)
    execute_mock.assert_called_once_with(task)


def test_update_tasks_status__active_other_action__call_action_method(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.tasks.filter(
        number__in=(2, 3),
    ).update(status=TaskStatus.COMPLETED)
    task = workflow.tasks.get(number=1)
    action_mock = mocker.Mock(__name__=ConditionAction.SKIP_TASK)
    execute_mock = mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(action_mock, True),
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.update_tasks_status()

    # assert
    action_mock.assert_called_once_with(task=task)
    execute_mock.assert_called_once_with(task)


def test_update_tasks_status__no_apd_after_loop__call_complete_wf(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.tasks.update(status=TaskStatus.COMPLETED)
    complete_mock = mocker.patch.object(
        WorkflowActionService,
        '_complete_workflow',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.update_tasks_status()

    # assert
    complete_mock.assert_called_once_with()


def test_complete_task_for_user__wf_delayed__raise_exception(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.status = WorkflowStatus.DELAYED
    workflow.save()
    task = workflow.tasks.get(number=1)
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act / assert
    with pytest.raises(exceptions.CompleteDelayedWorkflow):
        service.complete_task_for_user(task=task)


def test_complete_task_for_user__wf_completed__raise_exception(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.status = WorkflowStatus.DONE
    workflow.save()
    task = workflow.tasks.get(number=1)
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act / assert
    with pytest.raises(exceptions.CompleteCompletedWorkflow):
        service.complete_task_for_user(task=task)


def test_complete_task_for_user__task_inactive__raise_exception(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.PENDING
    task.save()
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act / assert
    with pytest.raises(exceptions.CompleteInactiveTask):
        service.complete_task_for_user(task=task)


def test_complete_task_for_user__performer_already_done__raise(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.filter(
        task=task,
        user_id=owner.id,
    ).update(is_completed=True, date_completed=timezone.now())
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act / assert
    with pytest.raises(exceptions.UserAlreadyCompleteTask):
        service.complete_task_for_user(task=task)


def test_complete_task_for_user__no_performer_not_owner__raise(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.filter(task=task).delete()
    not_owner = create_test_not_admin(account=account)
    service = WorkflowActionService(user=not_owner, workflow=workflow)

    # act / assert
    with pytest.raises(exceptions.UserNotPerformer):
        service.complete_task_for_user(task=task)


def test_complete_task_for_user__checklist_incomplete__raise(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    mocker.patch.object(
        Task,
        'checklists_completed',
        mocker.PropertyMock(return_value=False),
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act / assert
    with pytest.raises(exceptions.ChecklistIncompleted):
        service.complete_task_for_user(task=task)


def test_complete_task_for_user__sub_wf_running__raise_exception(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    sub_wf_mock = mocker.Mock()
    sub_wf_mock.running.return_value.exists.return_value = True
    mocker.patch.object(Task, 'sub_workflows', sub_wf_mock)
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act / assert
    with pytest.raises(exceptions.SubWorkflowsIncompleted):
        service.complete_task_for_user(task=task)


def test_complete_task_for_user__can_complete__call_complete_task(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    # Do not mark performer completed so we can reach complete_task path
    mocker.patch.object(
        WorkflowActionService,
        '_task_can_be_completed',
        return_value=True,
    )
    complete_mock = mocker.patch.object(
        WorkflowActionService,
        'complete_task',
    )
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None,
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    result = service.complete_task_for_user(task=task)

    # assert
    task_field_service_init_mock.assert_has_calls(
        [
            mocker.call(user=owner, instance=tf)
            for tf in task.output.all()
        ],
    )
    complete_mock.assert_called_once_with(task=task, by_user=True)
    assert result == task


def test_complete_task_for_user__cannot_complete__partial_user_done(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    mocker.patch.object(
        WorkflowActionService,
        '_task_can_be_completed',
        return_value=False,
    )
    complete_mock = mocker.patch.object(
        WorkflowActionService,
        'complete_task',
    )
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.processes.services.workflow_action.send_removed_task_'
        'notification.delay',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    result = service.complete_task_for_user(task=task)

    # assert
    task_field_service_init_mock.assert_has_calls(
        [
            mocker.call(user=owner, instance=tf)
            for tf in task.output.all()
        ],
    )
    complete_mock.assert_not_called()
    assert result == task
    task_performer = TaskPerformer.objects.get(task=task, user_id=owner.id)
    assert task_performer.is_completed is True
    assert task_performer.date_completed is not None


def test_complete_task_for_user__owner_no_performer__force_complete(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.filter(task=task).delete()
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None,
    )
    complete_mock = mocker.patch.object(
        WorkflowActionService,
        'complete_task',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    result = service.complete_task_for_user(task=task)

    # assert
    task_field_service_init_mock.assert_has_calls(
        [
            mocker.call(user=owner, instance=tf)
            for tf in task.output.all()
        ],
    )
    complete_mock.assert_called_once_with(task=task, by_user=True)
    assert result == task


def test_start_task__no_performers__skip_and_fire_skip_event(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=2)
    task.status = TaskStatus.PENDING
    task.save()
    TaskPerformer.objects.filter(task=task).delete()
    fields_values = {}
    get_fields_markdown_values_mock = mocker.patch(
        'src.processes.services.workflow_action.Workflow'
        '.get_fields_markdown_values',
        return_value=fields_values,
    )
    update_performers_mock = mocker.patch(
        'src.processes.services.workflow_action.Task.update_performers',
    )
    task_skip_no_performers_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_skip_no_performers_event',
    )
    start_next_tasks_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_next_tasks',
    )
    start_prev_tasks_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_prev_tasks',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.start_task(task=task)

    # assert
    task.refresh_from_db()
    assert task.status == TaskStatus.SKIPPED
    get_fields_markdown_values_mock.assert_called_once()
    update_performers_mock.assert_called_once_with(restore_performers=True)
    task_skip_no_performers_event_mock.assert_called_once_with(task)
    start_next_tasks_mock.assert_called_once_with(parent_task=task)
    start_prev_tasks_mock.assert_not_called()


def test_start_task__no_performers_is_returned__start_prev_tasks(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=2)
    task.status = TaskStatus.PENDING
    task.save()
    TaskPerformer.objects.filter(task=task).delete()
    fields_values = {}
    get_fields_markdown_values_mock = mocker.patch(
        'src.processes.services.workflow_action.Workflow'
        '.get_fields_markdown_values',
        return_value=fields_values,
    )
    update_performers_mock = mocker.patch(
        'src.processes.services.workflow_action.Task.update_performers',
        mocker.Mock(),
    )
    task_skip_no_performers_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_skip_no_performers_event',
    )
    start_next_tasks_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_next_tasks',
    )
    start_prev_tasks_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_prev_tasks',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    is_returned = True

    # act
    service.start_task(task=task, is_returned=is_returned)

    # assert
    task.refresh_from_db()
    assert task.status == TaskStatus.SKIPPED
    get_fields_markdown_values_mock.assert_called_once()
    update_performers_mock.assert_called_once_with(restore_performers=True)
    task_skip_no_performers_event_mock.assert_called_once_with(task)
    start_prev_tasks_mock.assert_called_once_with(task)
    start_next_tasks_mock.assert_not_called()


def test_start_task__performers_is_returned__continue_wf_returned(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=2)
    task.status = TaskStatus.PENDING
    task.save()
    task.update_performers()
    fields_values = {}
    get_fields_markdown_values_mock = mocker.patch(
        'src.processes.services.workflow_action.Workflow'
        '.get_fields_markdown_values',
        return_value=fields_values,
    )
    update_performers_mock = mocker.patch(
        'src.processes.services.workflow_action.Task.update_performers',
        mocker.Mock(),
    )
    continue_workflow_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.continue_workflow',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    is_returned = True

    # act
    service.start_task(task=task, is_returned=is_returned)

    # assert
    get_fields_markdown_values_mock.assert_called_once()
    update_performers_mock.assert_called_once_with(restore_performers=True)
    continue_workflow_mock.assert_called_once_with(
        task=task,
        is_returned=is_returned,
    )


def test_start_task__performers_has_active_delay__delay_task(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.PENDING
    task.save()
    task.update_performers()
    delay = Delay.objects.create(
        task=task,
        workflow=workflow,
        duration=timedelta(hours=1),
        start_date=timezone.now(),
    )
    fields_values = {}
    get_fields_markdown_values_mock = mocker.patch(
        'src.processes.services.workflow_action.Workflow'
        '.get_fields_markdown_values',
        return_value=fields_values,
    )
    update_performers_mock = mocker.patch(
        'src.processes.services.workflow_action.Task.update_performers',
        mocker.Mock(),
    )
    get_active_delay_mock = mocker.patch(
        'src.processes.services.workflow_action.Task.get_active_delay',
        return_value=delay,
    )
    delay_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.delay_task',
    )
    start_next_tasks_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_next_tasks',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.start_task(task=task)

    # assert
    get_fields_markdown_values_mock.assert_called_once()
    update_performers_mock.assert_called_once_with(restore_performers=True)
    get_active_delay_mock.assert_called_once()
    delay_task_mock.assert_called_once_with(task=task, delay=delay)
    start_next_tasks_mock.assert_called_once_with()


def test_start_task__performers_no_delay__continue_workflow(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=2)
    task.status = TaskStatus.PENDING
    task.save()
    task.update_performers()
    fields_values = {}
    get_fields_markdown_values_mock = mocker.patch(
        'src.processes.services.workflow_action.Workflow'
        '.get_fields_markdown_values',
        return_value=fields_values,
    )
    update_performers_mock = mocker.patch(
        'src.processes.services.workflow_action.Task.update_performers',
        mocker.Mock(),
    )
    get_active_delay_mock = mocker.patch(
        'src.processes.services.workflow_action.Task.get_active_delay',
        return_value=None,
    )
    continue_workflow_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.continue_workflow',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    is_returned = False

    # act
    service.start_task(task=task, is_returned=is_returned)

    # assert
    get_fields_markdown_values_mock.assert_called_once()
    update_performers_mock.assert_called_once_with(restore_performers=True)
    get_active_delay_mock.assert_called_once()
    continue_workflow_mock.assert_called_once_with(
        task=task,
        is_returned=is_returned,
    )


def test__get_not_skipped_revert_task__start_action__return_task(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    execute_mock = mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(mocker.Mock(__name__=ConditionAction.START_TASK), False),
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    result = service._get_not_skipped_revert_task(task)

    # assert
    execute_mock.assert_called_once_with(task)
    assert result == task


def test__get_not_skipped_revert_task__no_revert_tasks__return_none(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(mocker.Mock(__name__=ConditionAction.SKIP_TASK), True),
    )
    mocker.patch.object(task, 'get_revert_tasks', return_value=[])
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    result = service._get_not_skipped_revert_task(task)

    # assert
    assert result is None


def test__get_not_skipped_revert_task__recursive_found__return_task(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    revert_task = workflow.tasks.get(number=2)
    mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        side_effect=[
            (mocker.Mock(__name__=ConditionAction.SKIP_TASK), True),
            (mocker.Mock(__name__=ConditionAction.START_TASK), False),
        ],
    )
    mocker.patch.object(
        task,
        'get_revert_tasks',
        return_value=[revert_task],
    )
    mocker.patch.object(
        revert_task,
        'get_revert_tasks',
        return_value=[],
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    result = service._get_not_skipped_revert_task(task)

    # assert
    assert result == revert_task


def test__revert_is_possible__start_action__return_true(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    revert_to_tasks = [task]
    execute_mock = mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(mocker.Mock(__name__=ConditionAction.START_TASK), False),
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    result = service._revert_is_possible(revert_to_tasks)

    # assert
    execute_mock.assert_called_once_with(task)
    assert result is True


def test__revert_is_possible__no_valid_tasks__return_false(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    revert_to_tasks = [task]
    mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(None, False),
    )
    mocker.patch.object(task, 'get_revert_tasks', return_value=[])
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    result = service._revert_is_possible(revert_to_tasks)

    # assert
    assert result is False


def test__revert_is_possible__recursive_valid__return_true(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    child_task = workflow.tasks.get(number=2)
    start_action = mocker.Mock(__name__=ConditionAction.START_TASK)
    mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        side_effect=[(None, False), (start_action, False)],
    )
    mocker.patch.object(
        task,
        'get_revert_tasks',
        return_value=[child_task],
    )
    revert_possible_spy = mocker.spy(
        WorkflowActionService,
        '_revert_is_possible',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    revert_to_tasks = [task]

    # act
    result = service._revert_is_possible(revert_to_tasks)

    # assert
    assert result is True
    revert_possible_spy.assert_has_calls([
        mocker.call(service, [task]),
        mocker.call(service, [child_task]),
    ])


def test__validate_revert_is_possible__no_tasks__raise_first_task(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    service = WorkflowActionService(user=owner, workflow=workflow)
    revert_to_tasks = []

    # act / assert
    with pytest.raises(exceptions.FirstTaskCannotBeReverted):
        service._validate_revert_is_possible(revert_to_tasks)


def test__validate_revert_is_possible__start_action__return_true(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    revert_to_tasks = [task]
    mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(mocker.Mock(__name__=ConditionAction.START_TASK), False),
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    result = service._validate_revert_is_possible(revert_to_tasks)

    # assert
    assert result is True


def test__validate_revert_is_possible__next_depth_possible__true(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    child_task = workflow.tasks.get(number=2)
    mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(None, False),
    )
    mocker.patch.object(
        task,
        'get_revert_tasks',
        return_value=[child_task],
    )
    revert_possible_mock = mocker.patch.object(
        WorkflowActionService,
        '_revert_is_possible',
        return_value=True,
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    revert_to_tasks = [task]

    # act
    result = service._validate_revert_is_possible(revert_to_tasks)

    # assert
    assert result is True
    revert_possible_mock.assert_called_once_with([child_task])


def test__validate_revert_is_possible__next_depth_not_possible__raise(
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    child_task = workflow.tasks.get(number=2)
    mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(None, False),
    )
    mocker.patch.object(
        task,
        'get_revert_tasks',
        return_value=[child_task],
    )
    mocker.patch.object(
        WorkflowActionService,
        '_revert_is_possible',
        return_value=False,
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    revert_to_tasks = [task]

    # act / assert
    with pytest.raises(exceptions.RevertToSkippedTask):
        service._validate_revert_is_possible(revert_to_tasks)


def test__validate_revert_is_possible__no_depth_not_possible__raise(
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(None, False),
    )
    mocker.patch.object(task, 'get_revert_tasks', return_value=[])
    service = WorkflowActionService(user=owner, workflow=workflow)
    revert_to_tasks = [task]

    # act / assert
    with pytest.raises(exceptions.RevertToSkippedTask):
        service._validate_revert_is_possible(revert_to_tasks)


def test__deactivate_task__no_action_delayed_direct_status__end_delay(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    parent_task = workflow.tasks.get(number=1)
    task = workflow.tasks.get(number=2)
    task.status = TaskStatus.DELAYED
    task.save()
    delay = Delay.objects.create(
        task=task,
        workflow=workflow,
        duration=timedelta(hours=1),
        start_date=timezone.now(),
        directly_status=DirectlyStatus.CREATED,
    )
    mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(None, False),
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service._deactivate_task(parent_task=parent_task)

    # assert
    delay.refresh_from_db()
    assert delay.end_date is not None
    task.refresh_from_db()
    assert task.status == TaskStatus.PENDING
    assert task.date_started is None
    assert task.date_completed is None


def test__deactivate_task__no_action_active__send_removed_notification(
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    parent_task = workflow.tasks.get(number=1)
    task = workflow.tasks.get(number=2)
    task.status = TaskStatus.ACTIVE
    task.save()
    mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(None, False),
    )
    send_removed_mock = mocker.patch(
        'src.processes.services.workflow_action.send_removed_task_'
        'notification.delay',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service._deactivate_task(parent_task=parent_task)

    # assert
    send_removed_mock.assert_called_once_with(
        task_id=task.id,
        recipients=mocker.ANY,
        account_id=task.account_id,
    )
    task.refresh_from_db()
    assert task.status == TaskStatus.PENDING
    assert task.date_started is None
    assert task.date_completed is None


def test__deactivate_task__action_skip_task__mark_deactivated(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    parent_task = workflow.tasks.get(number=1)
    task = workflow.tasks.get(number=2)
    task.status = TaskStatus.SKIPPED
    task.save()
    mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(mocker.Mock(__name__=ConditionAction.SKIP_TASK), True),
    )
    deactivate_spy = mocker.spy(WorkflowActionService, '_deactivate_task')
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service._deactivate_task(parent_task=parent_task)

    # assert
    assert deactivate_spy.call_count == 2
    deactivate_spy.assert_has_calls([
        mocker.call(service, parent_task=parent_task),
        mocker.call(service, parent_task=task),
    ])


# --- Level 6 ---


def test__return_workflow_to_task__not_running__set_running(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.status = WorkflowStatus.DONE
    workflow.save()
    revert_from_task = workflow.tasks.get(number=2)
    revert_to_task = workflow.tasks.get(number=1)
    mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(mocker.Mock(__name__=ConditionAction.START_TASK), False),
    )
    mocker.patch.object(
        WorkflowActionService,
        '_deactivate_task',
    )
    mocker.patch.object(
        WorkflowActionService,
        'check_delay_workflow',
    )
    webhook_init_mock = mocker.patch(
        'src.processes.services.workflow_action.WebHook',
    )
    webhook_init_mock.objects.on_account.return_value.task_returned.return_value.exists.return_value = False  # noqa: E501
    service = WorkflowActionService(user=owner, workflow=workflow)
    revert_from_tasks = (revert_from_task,)
    revert_to_tasks = (revert_to_task,)

    # act
    service._return_workflow_to_task(
        revert_from_tasks=revert_from_tasks,
        revert_to_tasks=revert_to_tasks,
    )

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.RUNNING
    assert workflow.date_completed is None


def test__return_workflow_to_task__has_action_method__call_action(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    revert_to_task = workflow.tasks.get(number=1)
    action_mock = mocker.Mock()
    execute_mock = mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(action_mock, True),
    )
    mocker.patch.object(
        WorkflowActionService,
        '_deactivate_task',
    )
    mocker.patch.object(
        WorkflowActionService,
        'check_delay_workflow',
    )
    webhook_init_mock = mocker.patch(
        'src.processes.services.workflow_action.WebHook',
    )
    webhook_init_mock.objects.on_account.return_value.task_returned.return_value.exists.return_value = False  # noqa: E501
    service = WorkflowActionService(user=owner, workflow=workflow)
    revert_from_tasks = (workflow.tasks.get(number=2),)
    revert_to_tasks = (revert_to_task,)

    # act
    service._return_workflow_to_task(
        revert_from_tasks=revert_from_tasks,
        revert_to_tasks=revert_to_tasks,
    )

    # assert
    execute_mock.assert_called_once_with(revert_to_task)
    action_mock.assert_called_once_with(
        task=revert_to_task,
        is_returned=True,
        by_condition=True,
    )


def test__return_workflow_to_task__webhook_exists__send_webhook(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    revert_from_task = workflow.tasks.get(number=2)
    revert_to_task = workflow.tasks.get(number=1)
    mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(mocker.Mock(__name__=ConditionAction.START_TASK), False),
    )
    mocker.patch.object(
        WorkflowActionService,
        '_deactivate_task',
    )
    mocker.patch.object(
        WorkflowActionService,
        'check_delay_workflow',
    )
    webhook_send_mock = mocker.patch(
        'src.processes.services.workflow_action.send_task_returned_'
        'webhook.delay',
    )
    webhook_init_mock = mocker.patch(
        'src.processes.services.workflow_action.WebHook',
    )
    webhook_init_mock.objects.on_account.return_value.task_returned.return_value.exists.return_value = True  # noqa: E501
    service = WorkflowActionService(user=owner, workflow=workflow)
    revert_from_tasks = (revert_from_task,)
    revert_to_tasks = (revert_to_task,)

    # act
    service._return_workflow_to_task(
        revert_from_tasks=revert_from_tasks,
        revert_to_tasks=revert_to_tasks,
    )

    # assert
    webhook_send_mock.assert_called_once_with(
        user_id=owner.id,
        account_id=account.id,
        payload=revert_from_task.webhook_payload(),
    )


def test__return_workflow_to_task__no_webhook__skip_webhook(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    revert_to_task = workflow.tasks.get(number=1)
    mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(mocker.Mock(__name__=ConditionAction.START_TASK), False),
    )
    mocker.patch.object(
        WorkflowActionService,
        '_deactivate_task',
    )
    mocker.patch.object(
        WorkflowActionService,
        'check_delay_workflow',
    )
    webhook_send_mock = mocker.patch(
        'src.processes.services.workflow_action.send_task_returned_'
        'webhook.delay',
    )
    webhook_init_mock = mocker.patch(
        'src.processes.services.workflow_action.WebHook',
    )
    webhook_init_mock.objects.on_account.return_value.task_returned.return_value.exists.return_value = False  # noqa: E501
    service = WorkflowActionService(user=owner, workflow=workflow)
    revert_from_tasks = (workflow.tasks.get(number=2),)
    revert_to_tasks = (revert_to_task,)

    # act
    service._return_workflow_to_task(
        revert_from_tasks=revert_from_tasks,
        revert_to_tasks=revert_to_tasks,
    )

    # assert
    webhook_send_mock.assert_not_called()


def test_revert__user_is_guest__raise_permission_denied(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    guest = create_test_guest(account=account)
    service = WorkflowActionService(user=guest, workflow=workflow)
    comment = 'comment'

    # act / assert
    with pytest.raises(exceptions.PermissionDenied):
        service.revert(comment=comment, revert_from_task=task)


def test_revert__task_not_active__raise_revert_inactive(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.PENDING
    task.save()
    service = WorkflowActionService(user=owner, workflow=workflow)
    comment = 'comment'

    # act / assert
    with pytest.raises(exceptions.RevertInactiveTask):
        service.revert(comment=comment, revert_from_task=task)


def test_revert__running_sub_wf_running__raise_blocked(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.ACTIVE
    task.save()
    sub_wf_mock = mocker.Mock()
    sub_wf_mock.running.return_value.exists.return_value = True
    mocker.patch.object(Task, 'sub_workflows', sub_wf_mock)
    service = WorkflowActionService(user=owner, workflow=workflow)
    comment = 'comment'

    # act / assert
    with pytest.raises(exceptions.BlockedBySubWorkflows):
        service.revert(comment=comment, revert_from_task=task)


def test_revert__workflow_delayed__raise_delayed_cannot_change(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.status = WorkflowStatus.DELAYED
    workflow.save()
    task = workflow.tasks.get(number=1)
    service = WorkflowActionService(user=owner, workflow=workflow)
    comment = 'comment'

    # act / assert
    with pytest.raises(exceptions.DelayedWorkflowCannotBeChanged):
        service.revert(comment=comment, revert_from_task=task)


def test_revert__workflow_completed__raise_completed_cannot_change(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.status = WorkflowStatus.DONE
    workflow.save()
    task = workflow.tasks.get(number=1)
    service = WorkflowActionService(user=owner, workflow=workflow)
    comment = 'comment'

    # act / assert
    with pytest.raises(exceptions.CompletedWorkflowCannotBeChanged):
        service.revert(comment=comment, revert_from_task=task)


def test_revert__performer_completed__raise_completed_task(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.filter(
        task=task,
        user_id=owner.id,
    ).update(is_completed=True, date_completed=timezone.now())
    service = WorkflowActionService(user=owner, workflow=workflow)
    comment = 'comment'

    # act / assert
    with pytest.raises(exceptions.CompletedTaskCannotBeReturned):
        service.revert(comment=comment, revert_from_task=task)


def test_revert__no_performer_not_owner__raise_not_performer(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.filter(task=task).delete()
    not_owner = create_test_not_admin(account=account)
    service = WorkflowActionService(user=not_owner, workflow=workflow)
    comment = 'comment'

    # act / assert
    with pytest.raises(exceptions.UserNotPerformer):
        service.revert(comment=comment, revert_from_task=task)


def test_revert__ok__call_revert_events_and_analytic(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    revert_from_task = workflow.tasks.get(number=2)
    revert_from_task.status = TaskStatus.ACTIVE
    revert_from_task.save()
    revert_to_task = workflow.tasks.get(number=1)
    mocker.patch.object(
        revert_from_task,
        'get_revert_tasks',
        return_value=[revert_to_task],
    )
    validate_mock = mocker.patch.object(
        WorkflowActionService,
        '_validate_revert_is_possible',
        return_value=True,
    )
    return_wf_mock = mocker.patch.object(
        WorkflowActionService,
        '_return_workflow_to_task',
    )
    mocker.patch(
        'src.processes.services.workflow_action.MarkdownService.clear',
        return_value='cleaned',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_revert_event',
    )
    mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.task_returned',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    comment = 'comment'
    revert_to_tasks = [revert_to_task]

    # act
    service.revert(comment=comment, revert_from_task=revert_from_task)

    # assert
    validate_mock.assert_called_once_with(revert_to_tasks)
    return_wf_mock.assert_called_once_with(
        revert_from_tasks=(revert_from_task,),
        revert_to_tasks=revert_to_tasks,
    )


def test_return_to__task_pending__raise_future_task(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    revert_to_task = workflow.tasks.get(number=2)
    revert_to_task.status = TaskStatus.PENDING
    revert_to_task.save()
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act / assert
    with pytest.raises(exceptions.ReturnToFutureTask):
        service.return_to(revert_to_task=revert_to_task)


def test_return_to__action_none__raise_workflow_action_exception(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    revert_to_task = workflow.tasks.get(number=1)
    mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(None, False),
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act / assert
    with pytest.raises(exceptions.WorkflowActionServiceException):
        service.return_to(revert_to_task=revert_to_task)


def test_return_to__action_skip_task__raise_workflow_action_exception(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    revert_to_task = workflow.tasks.get(number=1)
    mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(
            mocker.Mock(__name__=ConditionAction.SKIP_TASK),
            True,
        ),
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act / assert
    with pytest.raises(exceptions.WorkflowActionServiceException):
        service.return_to(revert_to_task=revert_to_task)


def test_return_to__running_sub_wf_running__raise_blocked(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    revert_to_task = workflow.tasks.get(number=1)
    mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(mocker.Mock(__name__=ConditionAction.START_TASK), False),
    )
    active_or_delayed = [workflow.tasks.get(number=2)]
    mocker.patch.object(
        workflow.tasks,
        'active_or_delayed',
        return_value=mocker.Mock(__iter__=lambda s: iter(active_or_delayed)),
    )
    sub_wf_mock = mocker.Mock()
    sub_wf_mock.running.return_value.exists.return_value = True
    mocker.patch.object(Task, 'sub_workflows', sub_wf_mock)
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act / assert
    with pytest.raises(exceptions.BlockedBySubWorkflows):
        service.return_to(revert_to_task=revert_to_task)


def test_return_to__ok__call_return_wf_to_task(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    revert_to_task = workflow.tasks.get(number=1)
    mocker.patch.object(
        WorkflowActionService,
        'execute_conditions',
        return_value=(mocker.Mock(__name__=ConditionAction.START_TASK), False),
    )
    mocker.patch.object(
        workflow.tasks,
        'active_or_delayed',
        return_value=mocker.Mock(__iter__=lambda s: iter([])),
    )
    return_wf_mock = mocker.patch.object(
        WorkflowActionService,
        '_return_workflow_to_task',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.workflow_revert_event',
    )
    mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.workflow_returned',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.return_to(revert_to_task=revert_to_task)

    # assert
    return_wf_mock.assert_called_once_with(
        revert_from_tasks=mocker.ANY,
        revert_to_tasks=(revert_to_task,),
    )
