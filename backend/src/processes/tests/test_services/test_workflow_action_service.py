from datetime import timedelta

import pytest
from django.utils import timezone

from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    ConditionAction,
    DirectlyStatus,
    TaskStatus,
    WorkflowStatus,
    TemplateType,
    FieldType,
)
from src.processes.models.workflows.conditions import Condition
from src.processes.models.workflows.task import Delay, TaskPerformer
from src.processes.models.workflows.workflow import Workflow
from src.processes.models.workflows.fields import TaskField
from src.processes.services import exceptions
from src.processes.services.tasks.field import TaskFieldService
from src.processes.services.tasks.task import TaskService
from src.processes.services.workflow_action import WorkflowActionService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_guest,
    create_test_admin,
    create_test_not_admin,
    create_test_owner,
    create_test_workflow,
    create_wf_completed_webhook,
    create_wf_created_webhook,
    create_task_completed_webhook,
    create_task_returned_webhook,
    create_test_template,
)
from src.processes.messages import workflow as messages

pytestmark = pytest.mark.django_db

# TODO Test coverage incomplete, more cases need to be tested


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
        'src.processes.services.workflow_action'
        '.send_removed_task_notification.delay',
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
        'src.processes.services.workflow_action.'
        'send_removed_task_notification.delay',
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
        'src.processes.services.workflow_action.'
        'send_delayed_workflow_notification.delay',
    )
    send_removed_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'send_removed_task_notification.delay',
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
        'src.processes.services.workflow_action.'
        'send_removed_task_notification.delay',
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


def test__complete_workflow__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    current_date = timezone.now()
    mocker.patch(
        'src.processes.services.workflow_action.timezone.now',
        return_value=current_date,
    )
    deactivate_task_guest_cache_mock = mocker.patch(
        'src.processes.services.workflow_action.GuestJWTAuthService'
        '.deactivate_task_guest_cache',
    )
    send_workflow_completed_webhook_mock = mocker.patch(
        'src.processes.services.workflow_action'
        '.send_workflow_completed_webhook.delay',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service._complete_workflow()

    # assert
    task.refresh_from_db()
    assert task.is_active
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.DONE
    assert workflow.date_completed == current_date
    deactivate_task_guest_cache_mock.assert_called_once_with(task_id=task.id)
    send_workflow_completed_webhook_mock.assert_not_called()


def test__complete_workflow__has_delayed_tasks__end_delay(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.DELAYED
    task.save()
    delay = Delay.objects.create(
        task=task,
        workflow=workflow,
        duration=timedelta(hours=1),
        start_date=timezone.now(),
    )
    current_date = timezone.now()
    mocker.patch(
        'src.processes.services.workflow_action.timezone.now',
        return_value=current_date,
    )
    mocker.patch(
        'src.processes.services.workflow_action.GuestJWTAuthService'
        '.deactivate_task_guest_cache',
    )
    mocker.patch(
        'src.processes.services.workflow_action'
        '.send_workflow_completed_webhook.delay',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service._complete_workflow()

    # assert
    delay.refresh_from_db()
    assert delay.end_date == current_date
    task.refresh_from_db()
    assert task.is_active


def test__complete_workflow__is_urgent__clear_urgent_flag(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1, is_urgent=True)
    task = workflow.tasks.get(number=1)
    task.is_urgent = True
    task.save()
    mocker.patch(
        'src.processes.services.workflow_action.GuestJWTAuthService'
        '.deactivate_task_guest_cache',
    )
    mocker.patch(
        'src.processes.services.workflow_action'
        '.send_workflow_completed_webhook.delay',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service._complete_workflow()

    # assert
    workflow.refresh_from_db()
    assert workflow.is_urgent is False
    task.refresh_from_db()
    assert task.is_urgent is False


def test__complete_workflow__webhook_exists__send_webhook(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    create_wf_completed_webhook(owner)
    mocker.patch(
        'src.processes.services.workflow_action.GuestJWTAuthService'
        '.deactivate_task_guest_cache',
    )
    wf_completed_mock = mocker.patch(
        'src.processes.services.workflow_action.send_workflow_completed_'
        'webhook.delay',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service._complete_workflow()

    # assert
    wf_completed_mock.assert_called_once_with(
        user_id=owner.id,
        account_id=account.id,
        payload=workflow.webhook_payload(),
    )


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


def test_force_complete_workflow__has_active_tasks__send_removed_notif(
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    complete_wf_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._complete_workflow',
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
    complete_wf_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService.'
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
    skip_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._execute_skip_conditions',
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
    skip_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._execute_skip_conditions',
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
    skip_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._execute_skip_conditions',
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
    skip_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService.'
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
    complete_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._complete_workflow',
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
    complete_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._complete_workflow',
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
    force_complete_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.force_complete_workflow',
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
    workflow.tasks.exclude(number=2).update(status=TaskStatus.COMPLETED)
    action_mock = mocker.Mock(__name__='start_task')
    execute_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        return_value=(action_mock, False),
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

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
    workflow.tasks.filter(number=1).update(status=TaskStatus.ACTIVE)
    workflow.tasks.exclude(number=1).update(status=TaskStatus.COMPLETED)
    end_process_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.end_process',
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
    end_process_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.end_process',
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
    execute_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        return_value=(action_mock, True),
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
    execute_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        return_value=(None, False),
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
    insert_fields_values_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.insert_fields_values',
    )
    task_skip_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_skip_event',
    )
    start_prev_tasks_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_prev_tasks',
    )
    start_next_tasks_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_next_tasks',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    is_returned = True

    # act
    service.skip_task(task=task, is_returned=is_returned)

    # assert
    task.refresh_from_db()
    assert task.status == TaskStatus.PENDING
    task_service_init_mock.assert_called_once_with(instance=task, user=owner)
    insert_fields_values_mock.assert_called_once_with(
        fields_values={'workflow-starter': owner.name},
    )
    task_skip_event_mock.assert_called_once_with(task)
    start_prev_tasks_mock.assert_called_once_with(task)
    start_next_tasks_mock.assert_not_called()


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
    insert_fields_values_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.insert_fields_values',
    )
    task_skip_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_skip_event',
    )
    start_prev_tasks_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_prev_tasks',
    )
    start_next_tasks_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_next_tasks',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    is_returned = False

    # act
    service.skip_task(task=task, is_returned=is_returned)

    # assert
    task.refresh_from_db()
    assert task.status == TaskStatus.SKIPPED
    task_service_init_mock.assert_called_once_with(instance=task, user=owner)
    insert_fields_values_mock.assert_called_once_with(
        fields_values={'workflow-starter': owner.name},
    )
    task_skip_event_mock.assert_called_once_with(task)
    start_prev_tasks_mock.assert_not_called()
    start_next_tasks_mock.assert_called_once_with(parent_task=task)


def test_skip_task__external__guest_workflow_starter(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, is_external=True)
    task = workflow.tasks.get(number=2)
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    insert_fields_values_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.insert_fields_values',
    )
    task_skip_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_skip_event',
    )
    start_prev_tasks_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_prev_tasks',
    )
    start_next_tasks_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_next_tasks',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    is_returned = False

    # act
    service.skip_task(task=task, is_returned=is_returned)

    # assert
    task.refresh_from_db()
    assert task.status == TaskStatus.SKIPPED
    task_service_init_mock.assert_called_once_with(instance=task, user=owner)
    insert_fields_values_mock.assert_called_once_with(
        fields_values={'workflow-starter': 'Guest'},
    )
    task_skip_event_mock.assert_called_once_with(task)
    start_prev_tasks_mock.assert_not_called()
    start_next_tasks_mock.assert_called_once_with(parent_task=task)


def test_skip_task__skipped_fields__insert_null_value(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=owner,
        tasks_count=2,
        active_task_number=2,
    )
    task_1 = workflow.tasks.get(number=1)
    field = TaskField.objects.create(
        task=task_1,
        api_name='api-name-1',
        type=FieldType.STRING,
        workflow=workflow,
        account=account,
    )
    task_2 = workflow.tasks.get(number=2)
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    insert_fields_values_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.insert_fields_values',
    )
    task_skip_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_skip_event',
    )
    start_prev_tasks_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_prev_tasks',
    )
    start_next_tasks_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_next_tasks',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    is_returned = False

    # act
    service.skip_task(task=task_2, is_returned=is_returned)

    # assert
    task_2.refresh_from_db()
    assert task_2.status == TaskStatus.SKIPPED
    task_service_init_mock.assert_called_once_with(instance=task_2, user=owner)
    insert_fields_values_mock.assert_called_once_with(
        fields_values={
            'workflow-starter': owner.name,
            field.api_name: None,
        },
    )
    task_skip_event_mock.assert_called_once_with(task_2)
    start_prev_tasks_mock.assert_not_called()
    start_next_tasks_mock.assert_called_once_with(parent_task=task_2)


def test_continue_task__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=user.id,
    )
    current_date = timezone.now()
    mocker.patch(
        'src.processes.services.workflow_action.timezone.now',
        return_value=current_date,
    )
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.partial_update',
    )
    set_due_date_from_template_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService'
        '.set_due_date_from_template',
    )
    task_started_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_started_event',
    )
    send_new_task_notification_mock = mocker.patch(
        'src.notifications.tasks.send_new_task_notification.delay',
    )
    send_new_task_websocket_mock = mocker.patch(
        'src.notifications.tasks.send_new_task_websocket.delay',
    )
    delete_task_guest_cache_mock = mocker.patch(
        'src.processes.services.workflow_action.GuestJWTAuthService'
        '.delete_task_guest_cache',
    )
    start_next_tasks_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_next_tasks',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    is_returned = False

    # act
    service.continue_task(task=task)

    # assert
    task_service_init_mock.assert_called_once_with(instance=task, user=owner)
    partial_update_mock.assert_called_once_with(
        is_urgent=False,
        date_completed=None,
        status=TaskStatus.ACTIVE,
        date_started=current_date,
        force_save=True,
    )
    set_due_date_from_template_mock.assert_called_once_with()
    task_started_event_mock.assert_not_called()
    send_new_task_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        recipients=[
            (user.id, user.email, True),
        ],
        task_id=task.id,
        task_name=task.name,
        task_data=task.get_data_for_list(),
        task_description=task.description,
        workflow_name=workflow.name,
        template_name=workflow.get_template_name(),
        workflow_starter_name=owner.name,
        workflow_starter_photo=owner.photo,
        due_date_timestamp=None,
        logo_lg=account.logo_lg,
        is_returned=is_returned,
    )
    send_new_task_websocket_mock.assert_called_once_with(
        logging=account.log_api_requests,
        task_id=task.id,
        recipients=[
            (owner.id, owner.email, True),
            (user.id, user.email, True),
        ],
        account_id=account.id,
        task_data=task.get_data_for_list(),
    )
    delete_task_guest_cache_mock.assert_called_once_with(
        task_id=workflow.tasks.get(number=2).id,
    )
    start_next_tasks_mock.assert_called_once_with()


def test_continue_task__delayed__end_delay(mocker):

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
    current_date = timezone.now()
    mocker.patch(
        'src.processes.services.workflow_action.timezone.now',
        return_value=current_date,
    )
    mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.processes.services.tasks.task.TaskService.partial_update',
    )
    mocker.patch(
        'src.processes.services.tasks.task.TaskService'
        '.set_due_date_from_template',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_started_event',
    )
    mocker.patch(
        'src.notifications.tasks.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.notifications.tasks.send_new_task_websocket.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.GuestJWTAuthService'
        '.delete_task_guest_cache',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_next_tasks',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    is_returned = False

    # act
    service.continue_task(task=task, is_returned=is_returned)

    # assert
    delay.refresh_from_db()
    assert delay.end_date == current_date


def test_continue_task__second_start_task__not_create_started_event(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    current_date = timezone.now()
    mocker.patch(
        'src.processes.services.workflow_action.timezone.now',
        return_value=current_date,
    )
    mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.processes.services.tasks.task.TaskService.partial_update',
    )
    current_date = timezone.now()
    mocker.patch(
        'src.processes.services.workflow_action.timezone.now',
        return_value=current_date,
    )
    mocker.patch(
        'src.processes.services.tasks.task.TaskService'
        '.set_due_date_from_template',
    )
    task_started_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_started_event',
    )
    mocker.patch(
        'src.notifications.tasks.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.notifications.tasks.send_new_task_websocket.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.GuestJWTAuthService'
        '.delete_task_guest_cache',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_next_tasks',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    is_returned = False

    # act
    service.continue_task(task=task, is_returned=is_returned)

    # assert
    task_started_event_mock.assert_not_called()


def test_continue_task__first_start_task__create_started_event(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=2)
    task = workflow.tasks.get(number=2)
    mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.processes.services.tasks.task.TaskService.partial_update',
    )
    current_date = timezone.now()
    mocker.patch(
        'src.processes.services.workflow_action.timezone.now',
        return_value=current_date,
    )
    mocker.patch(
        'src.processes.services.tasks.task.TaskService'
        '.set_due_date_from_template',
    )
    task_started_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_started_event',
    )
    mocker.patch(
        'src.notifications.tasks.send_new_task_notification.delay',
    )
    mocker.patch(
        'src.notifications.tasks.send_new_task_websocket.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.GuestJWTAuthService'
        '.delete_task_guest_cache',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_next_tasks',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    is_returned = False

    # act
    service.continue_task(task=task, is_returned=is_returned)

    # assert
    task_started_event_mock.assert_called_once_with(task)


def test_continue_task__root_task_wf_starter_and_user_performers__ok(mocker):

    """ Workflow starter can't receive email and push for a root tasks """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=2)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=user.id,
    )
    mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.processes.services.tasks.task.TaskService.partial_update',
    )
    current_date = timezone.now()
    mocker.patch(
        'src.processes.services.workflow_action.timezone.now',
        return_value=current_date,
    )
    mocker.patch(
        'src.processes.services.tasks.task.TaskService'
        '.set_due_date_from_template',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_started_event',
    )
    send_new_task_notification_mock = mocker.patch(
        'src.notifications.tasks.send_new_task_notification.delay',
    )
    send_new_task_websocket_mock = mocker.patch(
        'src.notifications.tasks.send_new_task_websocket.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.GuestJWTAuthService'
        '.delete_task_guest_cache',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_next_tasks',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    is_returned = False

    # act
    service.continue_task(task=task, is_returned=is_returned)

    # assert
    send_new_task_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        recipients=[
            (user.id, user.email, True),
        ],
        task_id=task.id,
        task_name=task.name,
        task_data=task.get_data_for_list(),
        task_description=task.description,
        workflow_name=workflow.name,
        template_name=workflow.get_template_name(),
        workflow_starter_name=owner.name,
        workflow_starter_photo=owner.photo,
        due_date_timestamp=None,
        logo_lg=account.logo_lg,
        is_returned=is_returned,
    )
    send_new_task_websocket_mock.assert_called_once_with(
        logging=account.log_api_requests,
        task_id=task.id,
        recipients=[
            (owner.id, owner.email, True),
            (user.id, user.email, True),
        ],
        account_id=account.id,
        task_data=task.get_data_for_list(),
    )


def test_continue_task__not_root_task_wf_starter_and_user_performers__ok(
    mocker,
):

    """ Workflow starter can't receive email and push for a root tasks """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(
        user=owner,
        tasks_count=3,
        active_task_number=2,
    )
    task = workflow.tasks.get(number=2)
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=user.id,
    )
    mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.processes.services.tasks.task.TaskService.partial_update',
    )
    current_date = timezone.now()
    mocker.patch(
        'src.processes.services.workflow_action.timezone.now',
        return_value=current_date,
    )
    mocker.patch(
        'src.processes.services.tasks.task.TaskService'
        '.set_due_date_from_template',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_started_event',
    )
    send_new_task_notification_mock = mocker.patch(
        'src.notifications.tasks.send_new_task_notification.delay',
    )
    send_new_task_websocket_mock = mocker.patch(
        'src.notifications.tasks.send_new_task_websocket.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.GuestJWTAuthService'
        '.delete_task_guest_cache',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_next_tasks',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    is_returned = False

    # act
    service.continue_task(task=task, is_returned=is_returned)

    # assert
    send_new_task_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        recipients=[
            (owner.id, owner.email, True),
            (user.id, user.email, True),
        ],
        task_id=task.id,
        task_name=task.name,
        task_data=task.get_data_for_list(),
        task_description=task.description,
        workflow_name=workflow.name,
        template_name=workflow.get_template_name(),
        workflow_starter_name=owner.name,
        workflow_starter_photo=owner.photo,
        due_date_timestamp=None,
        logo_lg=account.logo_lg,
        is_returned=is_returned,
    )
    send_new_task_websocket_mock.assert_called_once_with(
        logging=account.log_api_requests,
        task_id=task.id,
        recipients=[
            (owner.id, owner.email, True),
            (user.id, user.email, True),
        ],
        account_id=account.id,
        task_data=task.get_data_for_list(),
    )


@pytest.mark.parametrize('template_type', TemplateType.TYPES_ONBOARDING)
def test_continue_task__onboarding_template__not_send_notifications(
    mocker,
    template_type,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(user=owner, type_=template_type)
    workflow = create_test_workflow(user=owner, template=template)
    task = workflow.tasks.get(number=1)
    mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.processes.services.tasks.task.TaskService.partial_update',
    )
    current_date = timezone.now()
    mocker.patch(
        'src.processes.services.workflow_action.timezone.now',
        return_value=current_date,
    )
    mocker.patch(
        'src.processes.services.tasks.task.TaskService'
        '.set_due_date_from_template',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_started_event',
    )
    send_new_task_notification_mock = mocker.patch(
        'src.notifications.tasks.send_new_task_notification.delay',
    )
    send_new_task_websocket_mock = mocker.patch(
        'src.notifications.tasks.send_new_task_websocket.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.GuestJWTAuthService'
        '.delete_task_guest_cache',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_next_tasks',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    is_returned = False

    # act
    service.continue_task(task=task, is_returned=is_returned)

    # assert
    send_new_task_notification_mock.assert_not_called()
    send_new_task_websocket_mock.assert_not_called()


def test_continue_task__external_workflow__skip_wf_starter_notification(
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    workflow = create_test_workflow(user=owner, is_external=True)
    workflow.workflow_starter = None
    workflow.save()
    task = workflow.tasks.get(number=1)
    task.performers.all().delete()
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=user.id,
    )
    mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.processes.services.tasks.task.TaskService.partial_update',
    )
    current_date = timezone.now()
    mocker.patch(
        'src.processes.services.workflow_action.timezone.now',
        return_value=current_date,
    )
    mocker.patch(
        'src.processes.services.tasks.task.TaskService'
        '.set_due_date_from_template',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_started_event',
    )
    send_new_task_notification_mock = mocker.patch(
        'src.notifications.tasks.send_new_task_notification.delay',
    )
    send_new_task_websocket_mock = mocker.patch(
        'src.notifications.tasks.send_new_task_websocket.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.GuestJWTAuthService'
        '.delete_task_guest_cache',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_next_tasks',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    is_returned = False

    # act
    service.continue_task(task=task, is_returned=is_returned)

    # assert
    send_new_task_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        recipients=[
            (user.id, user.email, True),
        ],
        task_id=task.id,
        task_name=task.name,
        task_data=task.get_data_for_list(),
        task_description=task.description,
        workflow_name=workflow.name,
        template_name=workflow.get_template_name(),
        workflow_starter_name=None,
        workflow_starter_photo=None,
        due_date_timestamp=None,
        logo_lg=account.logo_lg,
        is_returned=is_returned,
    )
    send_new_task_websocket_mock.assert_called_once_with(
        logging=account.log_api_requests,
        task_id=task.id,
        recipients=[
            (user.id, user.email, True),
        ],
        account_id=account.id,
        task_data=task.get_data_for_list(),
    )


def test_complete_task__user_performer__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    task.performers.all().delete()
    task_performer = TaskPerformer.objects.create(
        task_id=task.id,
        user_id=user.id,
    )
    current_date = timezone.now()
    mocker.patch(
        'src.processes.services.workflow_action.timezone.now',
        return_value=current_date,
    )
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.partial_update',
    )
    send_removed_task_notification_mock = mocker.patch(
        'src.processes.services.workflow_action'
        '.send_removed_task_notification.delay',
    )
    send_complete_task_notification_mock = mocker.patch(
        'src.processes.services.workflow_action'
        '.send_complete_task_notification.delay',
    )
    task_complete_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_complete_event',
    )
    task_completed_analytics_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.task_completed',
    )
    start_next_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_next_tasks',
    )
    send_task_completed_webhook_mock = mocker.patch(
        'src.processes.services.workflow_action'
        '.send_task_completed_webhook.delay',
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    service = WorkflowActionService(
        user=owner,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    by_user = False

    # act
    service.complete_task(task=task, by_user=by_user)

    # assert
    task_service_init_mock.assert_called_once_with(
        instance=task,
        is_superuser=is_superuser,
        auth_type=auth_type,
        user=owner,
    )
    partial_update_mock.assert_called_once_with(
        status=TaskStatus.COMPLETED,
        date_completed=current_date,
        date_started=task.date_started,
        force_save=True,
    )
    send_removed_task_notification_mock.assert_called_once_with(
        task_id=task.id,
        recipients=[(user.id, user.email)],
        account_id=task.account_id,
    )
    send_complete_task_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        author_id=owner.id,
        account_id=account.id,
        recipients=[(user.id, user.email)],
        task_id=task.id,
        logo_lg=account.logo_lg,
    )
    task_performer.refresh_from_db()
    assert task_performer.date_completed == current_date
    assert task_performer.is_completed is True

    task_completed_analytics_mock.assert_not_called()
    task_complete_event_mock.assert_not_called()
    start_next_mock.assert_called_once_with(parent_task=task)
    send_task_completed_webhook_mock.assert_not_called()


def test_complete_task__by_user__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    task.performers.all().delete()
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=user.id,
    )
    mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.processes.services.tasks.task.TaskService.partial_update',
    )
    mocker.patch(
        'src.processes.services.workflow_action'
        '.send_removed_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action'
        '.send_complete_task_notification.delay',
    )
    task_complete_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_complete_event',
    )
    task_completed_analytics_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.task_completed',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_next_tasks',
    )
    mocker.patch(
        'src.processes.services.workflow_action'
        '.send_task_completed_webhook.delay',
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    service = WorkflowActionService(
        user=owner,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    by_user = True

    # act
    service.complete_task(task=task, by_user=by_user)

    # assert
    task_completed_analytics_mock.assert_called_once_with(
        user=owner,
        is_superuser=is_superuser,
        auth_type=auth_type,
        workflow=workflow,
        task=task,
    )
    task_complete_event_mock.assert_called_once_with(task=task, user=owner)


def test_complete_task__exist_webhook_subscription__send_webhook(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    task.performers.all().delete()
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=user.id,
    )
    create_task_completed_webhook(user=owner)
    mocker.patch(
        'src.processes.services.tasks.task.TaskService.partial_update',
    )
    mocker.patch(
        'src.processes.services.workflow_action'
        '.send_removed_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action'
        '.send_complete_task_notification.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_complete_event',
    )
    mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.task_completed',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_next_tasks',
    )
    send_task_completed_webhook_mock = mocker.patch(
        'src.processes.services.workflow_action'
        '.send_task_completed_webhook.delay',
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    service = WorkflowActionService(
        user=owner,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    service.complete_task(task=task)

    # assert
    send_task_completed_webhook_mock.assert_called_once_with(
        user_id=owner.id,
        account_id=account.id,
        payload=task.webhook_payload(),
    )


def test_continue_workflow__not_running__set_running_and_members(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.status = WorkflowStatus.DONE
    workflow.save()
    task = workflow.tasks.get(number=1)
    continue_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.continue_task',
    )
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
    continue_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.continue_task',
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
    continue_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.continue_task',
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
    continue_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.continue_task',
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
    continue_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.continue_task',
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
    continue_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.continue_task',
    )
    mocker.patch(
        'src.processes.services.workflow_action'
        '.send_resumed_workflow_notification.delay',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.force_resume_workflow()

    # assert
    workflow.refresh_from_db()
    assert workflow.status == WorkflowStatus.RUNNING
    continue_task_mock.assert_called_once_with(task)


def test_start_workflow__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    root_task = workflow.tasks.get(number=1)
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    insert_fields_values_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.insert_fields_values',
    )
    workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.workflow_run_event',
    )
    sub_workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.sub_workflow_run_event',
    )
    start_next_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_next_tasks',
    )
    check_delay_workflow_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.check_delay_workflow',
    )
    send_workflow_started_webhook_mock = mocker.patch(
        'src.processes.services.workflow_action'
        '.send_workflow_started_webhook.delay',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.start_workflow()

    # assert
    task_service_init_mock.assert_called_once_with(
        instance=root_task,
        user=owner,
    )
    insert_fields_values_mock.assert_called_once_with(
        fields_values={'workflow-starter': owner.name},
    )
    workflow_run_event_mock.assert_called_once_with(
        workflow=workflow,
        user=owner,
    )
    sub_workflow_run_event_mock.assert_not_called()
    start_next_mock.assert_called_once_with()
    check_delay_workflow_mock.assert_called_once_with()
    send_workflow_started_webhook_mock.assert_not_called()


def test_start_workflow__with_ancestor_task__fire_sub_wf_event(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    ancestor_workflow = create_test_workflow(owner)
    ancestor_task = ancestor_workflow.tasks.get(number=1)

    user = create_test_admin(account=account)
    workflow = create_test_workflow(user=user, ancestor_task=ancestor_task)
    task = workflow.tasks.get(number=1)
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    insert_fields_values_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.insert_fields_values',
    )
    workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.workflow_run_event',
    )
    sub_workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.sub_workflow_run_event',
    )
    start_next_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_next_tasks',
    )
    check_delay_workflow_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.check_delay_workflow',
    )
    send_workflow_started_webhook_mock = mocker.patch(
        'src.processes.services.workflow_action'
        '.send_workflow_started_webhook.delay',
    )
    service = WorkflowActionService(user=user, workflow=workflow)

    # act
    service.start_workflow()

    # assert
    task_service_init_mock.assert_called_once_with(
        instance=task,
        user=user,
    )
    insert_fields_values_mock.assert_called_once_with(
        fields_values={'workflow-starter': owner.name},
    )
    workflow_run_event_mock.assert_called_once_with(
        workflow=workflow,
        user=user,
    )
    sub_workflow_run_event_mock.assert_called_once_with(
        workflow=ancestor_workflow,
        sub_workflow=workflow,
        user=user,
    )
    start_next_mock.assert_called_once_with()
    check_delay_workflow_mock.assert_called_once_with()
    send_workflow_started_webhook_mock.assert_not_called()


def test_start_workflow__webhook_exists__send_webhook(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    create_wf_created_webhook(user=owner)
    task = workflow.tasks.get(number=1)
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    insert_fields_values_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.insert_fields_values',
    )
    workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.workflow_run_event',
    )
    sub_workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.sub_workflow_run_event',
    )
    start_next_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_next_tasks',
    )
    check_delay_workflow_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.check_delay_workflow',
    )
    send_workflow_started_webhook_mock = mocker.patch(
        'src.processes.services.workflow_action'
        '.send_workflow_started_webhook.delay',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.start_workflow()

    # assert
    task_service_init_mock.assert_called_once_with(
        instance=task,
        user=owner,
    )
    insert_fields_values_mock.assert_called_once_with(
        fields_values={'workflow-starter': owner.name},
    )
    workflow_run_event_mock.assert_called_once_with(
        workflow=workflow,
        user=owner,
    )
    sub_workflow_run_event_mock.assert_not_called()
    start_next_mock.assert_called_once_with()
    check_delay_workflow_mock.assert_called_once_with()
    send_workflow_started_webhook_mock.assert_called_once_with(
        user_id=owner.id,
        account_id=account.id,
        payload=workflow.webhook_payload(),
    )


def test_start_workflow__external__guest_workflow_starter(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, is_external=True)
    root_task = workflow.tasks.get(number=1)
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    insert_fields_values_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.insert_fields_values',
    )
    workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.workflow_run_event',
    )
    sub_workflow_run_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.sub_workflow_run_event',
    )
    start_next_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._start_next_tasks',
    )
    check_delay_workflow_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.check_delay_workflow',
    )
    send_workflow_started_webhook_mock = mocker.patch(
        'src.processes.services.workflow_action'
        '.send_workflow_started_webhook.delay',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.start_workflow()

    # assert
    task_service_init_mock.assert_called_once_with(
        instance=root_task,
        user=owner,
    )
    insert_fields_values_mock.assert_called_once_with(
        fields_values={'workflow-starter': 'Guest'},
    )
    workflow_run_event_mock.assert_called_once_with(
        workflow=workflow,
        user=owner,
    )
    sub_workflow_run_event_mock.assert_not_called()
    start_next_mock.assert_called_once_with()
    check_delay_workflow_mock.assert_called_once_with()
    send_workflow_started_webhook_mock.assert_not_called()


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
    execute_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
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
    complete_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._complete_workflow',
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
    execute_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        return_value=(start_action, False),
    )
    resume_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.resume_task',
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
    execute_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        return_value=(start_action, False),
    )
    complete_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.complete_task',
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
    execute_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
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
    complete_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._complete_workflow',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.update_tasks_status()

    # assert
    complete_mock.assert_called_once_with()


def test_complete_task_for_user__workflow_delayed__raise_exception(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, status=WorkflowStatus.DELAYED)
    task = workflow.tasks.get(number=1)
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.tasks.field.TaskFieldService'
        '.partial_update',
    )
    task_can_be_completed_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._task_can_be_completed',
    )
    complete_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.complete_task',
    )
    send_removed_task_notification_mock = mocker.patch(
        'src.processes.services.workflow_action'
        '.send_removed_task_notification.delay',
    )

    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    with pytest.raises(exceptions.CompleteDelayedWorkflow) as ex:
        service.complete_task_for_user(task=task)

    # assert
    assert ex.value.message == str(messages.MSG_PW_0004)
    task_field_service_init_mock.assert_not_called()
    partial_update_mock.assert_not_called()
    task_can_be_completed_mock.assert_not_called()
    complete_task_mock.assert_not_called()
    send_removed_task_notification_mock.assert_not_called()


def test_complete_task_for_user__workflow_completed__raise_exception(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, status=WorkflowStatus.DONE)
    task = workflow.tasks.get(number=1)
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.tasks.field.TaskFieldService'
        '.partial_update',
    )
    task_can_be_completed_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._task_can_be_completed',
    )
    complete_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.complete_task',
    )
    send_removed_task_notification_mock = mocker.patch(
        'src.processes.services.workflow_action'
        '.send_removed_task_notification.delay',
    )

    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    with pytest.raises(exceptions.CompleteCompletedWorkflow) as ex:
        service.complete_task_for_user(task=task)

    # assert
    assert ex.value.message == str(messages.MSG_PW_0008)
    task_field_service_init_mock.assert_not_called()
    partial_update_mock.assert_not_called()
    task_can_be_completed_mock.assert_not_called()
    complete_task_mock.assert_not_called()
    send_removed_task_notification_mock.assert_not_called()


@pytest.mark.parametrize('status', TaskStatus.INACTIVE_STATUS)
def test_complete_task_for_user__task_inactive__raise_exception(
    mocker,
    status,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    task.status = status
    task.save()

    create_test_workflow(
        user=owner,
        tasks_count=1,
        ancestor_task=task,
    )
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.tasks.field.TaskFieldService'
        '.partial_update',
    )
    task_can_be_completed_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._task_can_be_completed',
    )
    complete_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.complete_task',
    )
    send_removed_task_notification_mock = mocker.patch(
        'src.processes.services.workflow_action'
        '.send_removed_task_notification.delay',
    )

    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    with pytest.raises(exceptions.CompleteInactiveTask) as ex:
        service.complete_task_for_user(task=task)

    # assert
    assert ex.value.message == str(messages.MSG_PW_0086)
    task_field_service_init_mock.assert_not_called()
    partial_update_mock.assert_not_called()
    task_can_be_completed_mock.assert_not_called()
    complete_task_mock.assert_not_called()
    send_removed_task_notification_mock.assert_not_called()


def test_complete_task_for_user__performer_complete_task__raise_exception(
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.filter(
        task=task,
        user_id=owner.id,
    ).update(
        is_completed=True,
        date_completed=timezone.now(),
    )
    create_test_workflow(
        user=owner,
        tasks_count=1,
        ancestor_task=task,
    )
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.tasks.field.TaskFieldService'
        '.partial_update',
    )
    task_can_be_completed_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._task_can_be_completed',
    )
    complete_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.complete_task',
    )
    send_removed_task_notification_mock = mocker.patch(
        'src.processes.services.workflow_action'
        '.send_removed_task_notification.delay',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    with pytest.raises(exceptions.UserAlreadyCompleteTask) as ex:
        service.complete_task_for_user(task=task)

    # assert
    assert ex.value.message == str(messages.MSG_PW_0007)
    task_field_service_init_mock.assert_not_called()
    partial_update_mock.assert_not_called()
    task_can_be_completed_mock.assert_not_called()
    complete_task_mock.assert_not_called()
    send_removed_task_notification_mock.assert_not_called()


def test_complete_task_for_user__user_not_performer__raise(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    create_test_workflow(
        user=owner,
        tasks_count=1,
        ancestor_task=task,
    )
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.tasks.field.TaskFieldService'
        '.partial_update',
    )
    task_can_be_completed_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._task_can_be_completed',
    )
    complete_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.complete_task',
    )
    send_removed_task_notification_mock = mocker.patch(
        'src.processes.services.workflow_action'
        '.send_removed_task_notification.delay',
    )
    service = WorkflowActionService(user=user, workflow=workflow)

    # act / assert
    with pytest.raises(exceptions.UserNotPerformer) as ex:
        service.complete_task_for_user(task=task)

    # assert
    assert ex.value.message == str(messages.MSG_PW_0087)
    task_field_service_init_mock.assert_not_called()
    partial_update_mock.assert_not_called()
    task_can_be_completed_mock.assert_not_called()
    complete_task_mock.assert_not_called()
    send_removed_task_notification_mock.assert_not_called()


def test_complete_task_for_user__checklist_incomplete__raise_exception(
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.tasks.field.TaskFieldService'
        '.partial_update',
    )
    task_can_be_completed_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._task_can_be_completed',
    )
    complete_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.complete_task',
    )
    send_removed_task_notification_mock = mocker.patch(
        'src.processes.services.workflow_action'
        '.send_removed_task_notification.delay',
    )
    checklists_completed_mock = mocker.patch(
        'src.processes.services.workflow_action.Task.checklists_completed',
        mocker.PropertyMock(return_value=False),
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    with pytest.raises(exceptions.ChecklistIncompleted) as ex:
        service.complete_task_for_user(task=task)

    # assert
    assert ex.value.message == str(messages.MSG_PW_0006)
    checklists_completed_mock.assert_called_once_with()
    task_field_service_init_mock.assert_not_called()
    partial_update_mock.assert_not_called()
    task_can_be_completed_mock.assert_not_called()
    complete_task_mock.assert_not_called()
    send_removed_task_notification_mock.assert_not_called()


def test_complete_task_for_user__sub_wf_running__raise_exception(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    create_test_workflow(
        user=owner,
        tasks_count=1,
        ancestor_task=task,
    )
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.tasks.field.TaskFieldService'
        '.partial_update',
    )
    task_can_be_completed_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._task_can_be_completed',
    )
    complete_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.complete_task',
    )
    send_removed_task_notification_mock = mocker.patch(
        'src.processes.services.workflow_action'
        '.send_removed_task_notification.delay',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    with pytest.raises(exceptions.SubWorkflowsIncompleted) as ex:
        service.complete_task_for_user(task=task)

    # assert
    assert ex.value.message == str(messages.MSG_PW_0070)
    task_field_service_init_mock.assert_not_called()
    partial_update_mock.assert_not_called()
    task_can_be_completed_mock.assert_not_called()
    complete_task_mock.assert_not_called()
    send_removed_task_notification_mock.assert_not_called()


def test_complete_task_for_user__account_owner_no_performer__force_complete(
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(user=user)
    task = workflow.tasks.get(number=1)
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.tasks.field.TaskFieldService'
        '.partial_update',
    )
    task_can_be_completed_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._task_can_be_completed',
    )
    complete_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.complete_task',
    )
    send_removed_task_notification_mock = mocker.patch(
        'src.processes.services.workflow_action'
        '.send_removed_task_notification.delay',
    )

    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    result = service.complete_task_for_user(task=task)

    # assert
    assert result.id == task.id
    task_field_service_init_mock.assert_not_called()
    partial_update_mock.assert_not_called()
    task_can_be_completed_mock.assert_not_called()
    complete_task_mock.assert_called_once_with(task=task, by_user=True)
    send_removed_task_notification_mock.assert_not_called()


def test_complete_task_for_user__user_performer_last_completion__ok(
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    task.performers.all().delete()
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=user.id,
    )
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.tasks.field.TaskFieldService'
        '.partial_update',
    )
    task_can_be_completed_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._task_can_be_completed',
        return_value=True,
    )
    complete_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.complete_task',
    )
    send_removed_task_notification_mock = mocker.patch(
        'src.processes.services.workflow_action'
        '.send_removed_task_notification.delay',
    )

    service = WorkflowActionService(user=user, workflow=workflow)

    # act
    result = service.complete_task_for_user(task=task)

    # assert
    assert result.id == task.id
    task_field_service_init_mock.assert_not_called()
    partial_update_mock.assert_not_called()
    task_can_be_completed_mock.assert_called_once_with(task)
    complete_task_mock.assert_called_once_with(task=task, by_user=True)
    send_removed_task_notification_mock.assert_not_called()


def test_complete_task_for_user__user_performer_first_completion__ok(
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    task.performers.all().delete()
    task_performer = TaskPerformer.objects.create(
        task_id=task.id,
        user_id=user.id,
    )
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.tasks.field.TaskFieldService'
        '.partial_update',
    )
    task_can_be_completed_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._task_can_be_completed',
        return_value=False,
    )
    complete_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.complete_task',
    )
    send_removed_task_notification_mock = mocker.patch(
        'src.processes.services.workflow_action'
        '.send_removed_task_notification.delay',
    )
    current_date = timezone.now()
    mocker.patch(
        'src.processes.services.workflow_action.timezone.now',
        return_value=current_date,
    )
    service = WorkflowActionService(user=user, workflow=workflow)

    # act
    result = service.complete_task_for_user(task=task)

    # assert
    assert result.id == task.id
    task_field_service_init_mock.assert_not_called()
    partial_update_mock.assert_not_called()
    task_can_be_completed_mock.assert_called_once_with(task)
    task_performer.refresh_from_db()
    assert task_performer.date_completed == current_date
    assert task_performer.is_completed is True
    send_removed_task_notification_mock.assert_called_once_with(
        task_id=task.id,
        recipients=[(user.id, user.email)],
        account_id=account.id,
    )
    complete_task_mock.assert_not_called()


def test_complete_task_for_user__guest_performer_first_completion__ok(
    mocker,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_admin(account=account)
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(user=user)
    task = workflow.tasks.get(number=1)
    task_performer = TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.tasks.field.TaskFieldService'
        '.partial_update',
    )
    task_can_be_completed_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._task_can_be_completed',
        return_value=False,
    )
    complete_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.complete_task',
    )
    send_removed_task_notification_mock = mocker.patch(
        'src.processes.services.workflow_action'
        '.send_removed_task_notification.delay',
    )
    current_date = timezone.now()
    mocker.patch(
        'src.processes.services.workflow_action.timezone.now',
        return_value=current_date,
    )
    service = WorkflowActionService(user=guest, workflow=workflow)

    # act
    result = service.complete_task_for_user(task=task)

    # assert
    assert result.id == task.id
    task_field_service_init_mock.assert_not_called()
    partial_update_mock.assert_not_called()
    task_can_be_completed_mock.assert_called_once_with(task)
    task_performer.refresh_from_db()
    assert task_performer.date_completed == current_date
    assert task_performer.is_completed is True
    send_removed_task_notification_mock.assert_not_called()
    complete_task_mock.assert_not_called()


def test_start_task__no_performers__skip_and_fire_skip_event(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=2)
    task.status = TaskStatus.PENDING
    task.save()
    TaskPerformer.objects.filter(task=task).delete()
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    insert_fields_values_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.insert_fields_values',
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
    task_service_init_mock.assert_called_once_with(
        instance=task,
        user=owner,
    )
    insert_fields_values_mock.assert_called_once_with(
        fields_values={
            'workflow-starter': owner.name,
        },
    )
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
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    insert_fields_values_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.insert_fields_values',
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
    task_service_init_mock.assert_called_once_with(
        instance=task,
        user=owner,
    )
    insert_fields_values_mock.assert_called_once_with(
        fields_values={
            'workflow-starter': owner.name,
        },
    )
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
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    insert_fields_values_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.insert_fields_values',
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
    task_service_init_mock.assert_called_once_with(
        instance=task,
        user=owner,
    )
    insert_fields_values_mock.assert_called_once_with(
        fields_values={
            'workflow-starter': owner.name,
        },
    )
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
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    insert_fields_values_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.insert_fields_values',
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
    task_service_init_mock.assert_called_once_with(
        instance=task,
        user=owner,
    )
    insert_fields_values_mock.assert_called_once_with(
        fields_values={
            'workflow-starter': owner.name,
        },
    )
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
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    insert_fields_values_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.insert_fields_values',
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
    task_service_init_mock.assert_called_once_with(
        instance=task,
        user=owner,
    )
    insert_fields_values_mock.assert_called_once_with(
        fields_values={
            'workflow-starter': owner.name,
        },
    )
    update_performers_mock.assert_called_once_with(restore_performers=True)
    get_active_delay_mock.assert_called_once()
    continue_workflow_mock.assert_called_once_with(
        task=task,
        is_returned=is_returned,
    )


@pytest.mark.parametrize('status', TaskStatus.INACTIVE_STATUS)
def test_start_task__inactive_task_field_value__insert_value(mocker, status):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.status = status
    task.save()
    field_api_name = 'field-api-name'
    field_value = 'Some value'
    field_clear_value = 'Some clear value'
    field_markdown_value = 'Some markdown value'
    TaskField.objects.create(
        task=task,
        type=FieldType.STRING,
        workflow=workflow,
        account=account,
        value=field_value,
        clear_value=field_clear_value,
        markdown_value=field_markdown_value,
        api_name=field_api_name,
    )

    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    insert_fields_values_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.insert_fields_values',
    )
    mocker.patch(
        'src.processes.services.workflow_action.Task.update_performers',
    )
    mocker.patch(
        'src.processes.services.workflow_action.Task.get_active_delay',
        return_value=None,
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.continue_workflow',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    is_returned = False

    # act
    service.start_task(task=task, is_returned=is_returned)

    # assert
    task_service_init_mock.assert_called_once_with(
        instance=task,
        user=owner,
    )
    insert_fields_values_mock.assert_called_once_with(
        fields_values={
            field_api_name: field_markdown_value,
            'workflow-starter': owner.name,
        },
    )


def test_start_task__field_value_blank__insert_null_value(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    field_api_name = 'field-api-name'
    TaskField.objects.create(
        task=task,
        type=FieldType.STRING,
        workflow=workflow,
        account=account,
        api_name=field_api_name,
    )

    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    insert_fields_values_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.insert_fields_values',
    )
    mocker.patch(
        'src.processes.services.workflow_action.Task.update_performers',
    )
    mocker.patch(
        'src.processes.services.workflow_action.Task.get_active_delay',
        return_value=None,
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.continue_workflow',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    is_returned = False

    # act
    service.start_task(task=task, is_returned=is_returned)

    # assert
    task_service_init_mock.assert_called_once_with(
        instance=task,
        user=owner,
    )
    insert_fields_values_mock.assert_called_once_with(
        fields_values={
            field_api_name: None,
            'workflow-starter': owner.name,
        },
    )


def test__get_not_skipped_revert_task__start_action__return_task(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    execute_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        return_value=(
            mocker.Mock(__name__=ConditionAction.START_TASK), False,
        ),
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
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        return_value=(
            mocker.Mock(__name__=ConditionAction.SKIP_TASK), True,
        ),
    )
    mocker.patch(
        'src.processes.services.workflow_action.Task.get_revert_tasks',
        return_value=[],
    )
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
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        side_effect=[
            (mocker.Mock(__name__=ConditionAction.SKIP_TASK), True),
            (mocker.Mock(__name__=ConditionAction.START_TASK), False),
        ],
    )
    mocker.patch(
        'src.processes.services.workflow_action.Task.get_revert_tasks',
        side_effect=[[revert_task], []],
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
    execute_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        return_value=(
            mocker.Mock(__name__=ConditionAction.START_TASK), False,
        ),
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
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        return_value=(None, False),
    )
    mocker.patch(
        'src.processes.services.workflow_action.Task.get_revert_tasks',
        return_value=[],
    )
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
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        side_effect=[(None, False), (start_action, False)],
    )
    mocker.patch(
        'src.processes.services.workflow_action.Task.get_revert_tasks',
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
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        return_value=(
            mocker.Mock(__name__=ConditionAction.START_TASK),
            False,
        ),
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
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        return_value=(None, False),
    )
    mocker.patch(
        'src.processes.services.workflow_action.Task.get_revert_tasks',
        return_value=[child_task],
    )
    revert_possible_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._revert_is_possible',
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
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        return_value=(None, False),
    )
    mocker.patch(
        'src.processes.services.workflow_action.Task.get_revert_tasks',
        return_value=[child_task],
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._revert_is_possible',
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
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        return_value=(None, False),
    )
    mocker.patch(
        'src.processes.services.workflow_action.Task.get_revert_tasks',
        return_value=[],
    )
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
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
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
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
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
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        return_value=(mocker.Mock(__name__=ConditionAction.SKIP_TASK), True),
    )
    deactivate_spy = mocker.spy(
        WorkflowActionService,
        '_deactivate_task',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service._deactivate_task(parent_task=parent_task)

    # assert
    assert deactivate_spy.call_count == 2
    deactivate_spy.assert_has_calls([
        mocker.call(service, parent_task=parent_task),
        mocker.call(service, parent_task=task),
    ])


def test__return_workflow_to_task__not_running__set_running(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    workflow.status = WorkflowStatus.DONE
    workflow.save()
    revert_from_task = workflow.tasks.get(number=2)
    revert_to_task = workflow.tasks.get(number=1)
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        return_value=(mocker.Mock(__name__=ConditionAction.START_TASK), False),
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._deactivate_task',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.check_delay_workflow',
    )
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
    execute_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        return_value=(action_mock, True),
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._deactivate_task',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.check_delay_workflow',
    )
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
    create_task_returned_webhook(user=owner)
    revert_from_task = workflow.tasks.get(number=2)
    revert_to_task = workflow.tasks.get(number=1)
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        return_value=(mocker.Mock(__name__=ConditionAction.START_TASK), False),
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._deactivate_task',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.check_delay_workflow',
    )
    webhook_send_mock = mocker.patch(
        'src.processes.services.workflow_action.send_task_returned_'
        'webhook.delay',
    )
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
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        return_value=(mocker.Mock(__name__=ConditionAction.START_TASK), False),
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._deactivate_task',
    )
    mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.check_delay_workflow',
    )
    webhook_send_mock = mocker.patch(
        'src.processes.services.workflow_action.send_task_returned_'
        'webhook.delay',
    )
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
    workflow = create_test_workflow(user=owner, active_task_number=2)
    task = workflow.tasks.get(number=2)
    guest = create_test_guest(account=account)

    validate_revert_is_possible_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._validate_revert_is_possible',
    )
    clear_mock = mocker.patch(
        'src.processes.services.workflow_action.MarkdownService.clear',
    )
    task_revert_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_revert_event',
    )
    task_returned_analytics_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.task_returned',
    )
    return_workflow_to_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._return_workflow_to_task',
    )
    service = WorkflowActionService(user=guest, workflow=workflow)
    comment = 'comment'

    # act
    with pytest.raises(exceptions.PermissionDenied) as ex:
        service.revert(
            comment=comment,
            revert_from_task=task,
        )

    # assert
    assert ex.value.message == str(messages.MSG_PW_0011)
    validate_revert_is_possible_mock.assert_not_called()
    clear_mock.assert_not_called()
    task_revert_event_mock.assert_not_called()
    task_returned_analytics_mock.assert_not_called()
    return_workflow_to_task_mock.assert_not_called()


@pytest.mark.parametrize('status', TaskStatus.INACTIVE_STATUS)
def test_revert__task_not_active__raise_exception(mocker, status):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, active_task_number=2)
    task = workflow.tasks.get(number=2)
    task.status = status
    task.save()

    validate_revert_is_possible_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._validate_revert_is_possible',
    )
    clear_mock = mocker.patch(
        'src.processes.services.workflow_action.MarkdownService.clear',
    )
    task_revert_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_revert_event',
    )
    task_returned_analytics_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.task_returned',
    )
    return_workflow_to_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._return_workflow_to_task',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    comment = 'comment'

    # act
    with pytest.raises(exceptions.RevertInactiveTask) as ex:
        service.revert(comment=comment, revert_from_task=task)

    # assert
    assert ex.value.message == str(messages.MSG_PW_0086)
    validate_revert_is_possible_mock.assert_not_called()
    clear_mock.assert_not_called()
    task_revert_event_mock.assert_not_called()
    task_returned_analytics_mock.assert_not_called()
    return_workflow_to_task_mock.assert_not_called()


def test_revert__running_sub_workflow__raise_exception(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    ancestor_workflow = create_test_workflow(owner, active_task_number=2)
    ancestor_task = ancestor_workflow.tasks.get(number=2)
    workflow = create_test_workflow(user=owner, ancestor_task=ancestor_task)

    validate_revert_is_possible_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._validate_revert_is_possible',
    )
    clear_mock = mocker.patch(
        'src.processes.services.workflow_action.MarkdownService.clear',
    )
    task_revert_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_revert_event',
    )
    task_returned_analytics_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.task_returned',
    )
    return_workflow_to_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._return_workflow_to_task',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    comment = 'comment'

    # act
    with pytest.raises(exceptions.BlockedBySubWorkflows) as ex:
        service.revert(
            comment=comment,
            revert_from_task=ancestor_task,
        )

    # assert
    assert ex.value.message == str(messages.MSG_PW_0071)
    validate_revert_is_possible_mock.assert_not_called()
    clear_mock.assert_not_called()
    task_revert_event_mock.assert_not_called()
    task_returned_analytics_mock.assert_not_called()
    return_workflow_to_task_mock.assert_not_called()


def test_revert__workflow_snoozed__raise_exception(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=owner,
        status=WorkflowStatus.DELAYED,
        active_task_number=2,
    )
    task = workflow.tasks.get(number=2)
    validate_revert_is_possible_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._validate_revert_is_possible',
    )
    clear_mock = mocker.patch(
        'src.processes.services.workflow_action.MarkdownService.clear',
    )
    task_revert_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_revert_event',
    )
    task_returned_analytics_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.task_returned',
    )
    return_workflow_to_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._return_workflow_to_task',
    )

    service = WorkflowActionService(user=owner, workflow=workflow)
    comment = 'comment'

    # act
    with pytest.raises(exceptions.DelayedWorkflowCannotBeChanged) as ex:
        service.revert(comment=comment, revert_from_task=task)

    # assert
    assert ex.value.message == str(messages.MSG_PW_0072)
    validate_revert_is_possible_mock.assert_not_called()
    clear_mock.assert_not_called()
    task_revert_event_mock.assert_not_called()
    task_returned_analytics_mock.assert_not_called()
    return_workflow_to_task_mock.assert_not_called()


def test_revert__workflow_completed__raise_exception(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=owner,
        status=WorkflowStatus.DONE,
        active_task_number=2,
    )
    task = workflow.tasks.get(number=2)
    validate_revert_is_possible_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._validate_revert_is_possible',
    )
    clear_comment = 'clear'
    clear_mock = mocker.patch(
        'src.processes.services.workflow_action.MarkdownService.clear',
        return_value=clear_comment,
    )
    task_revert_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_revert_event',
    )
    task_returned_analytics_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.task_returned',
    )
    return_workflow_to_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._return_workflow_to_task',
    )

    service = WorkflowActionService(user=owner, workflow=workflow)
    comment = 'comment'

    # act
    with pytest.raises(exceptions.CompletedWorkflowCannotBeChanged) as ex:
        service.revert(comment=comment, revert_from_task=task)

    # assert
    assert ex.value.message == str(messages.MSG_PW_0017)
    validate_revert_is_possible_mock.assert_not_called()
    clear_mock.assert_not_called()
    task_revert_event_mock.assert_not_called()
    task_returned_analytics_mock.assert_not_called()
    return_workflow_to_task_mock.assert_not_called()


def test_revert__performer_completed__raise_exception(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.filter(
        task=task,
        user_id=owner.id,
    ).update(
        is_completed=True,
        date_completed=timezone.now(),
    )
    validate_revert_is_possible_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._validate_revert_is_possible',
    )
    clear_mock = mocker.patch(
        'src.processes.services.workflow_action.MarkdownService.clear',
    )
    task_revert_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_revert_event',
    )
    task_returned_analytics_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.task_returned',
    )
    return_workflow_to_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._return_workflow_to_task',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)
    comment = 'comment'

    # act
    with pytest.raises(exceptions.CompletedTaskCannotBeReturned) as ex:
        service.revert(comment=comment, revert_from_task=task)

    # assert
    assert ex.value.message == str(messages.MSG_PW_0088)
    validate_revert_is_possible_mock.assert_not_called()
    clear_mock.assert_not_called()
    task_revert_event_mock.assert_not_called()
    task_returned_analytics_mock.assert_not_called()
    return_workflow_to_task_mock.assert_not_called()


def test_revert__no_performer_not_account_owner__raise_not_performer(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.filter(task=task).delete()
    user = create_test_not_admin(account=account)
    validate_revert_is_possible_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._validate_revert_is_possible',
    )
    clear_mock = mocker.patch(
        'src.processes.services.workflow_action.MarkdownService.clear',
    )
    task_revert_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_revert_event',
    )
    task_returned_analytics_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.task_returned',
    )
    return_workflow_to_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._return_workflow_to_task',
    )
    service = WorkflowActionService(user=user, workflow=workflow)
    comment = 'comment'

    # act
    with pytest.raises(exceptions.UserNotPerformer) as ex:
        service.revert(comment=comment, revert_from_task=task)

    # assert
    assert ex.value.message == str(messages.MSG_PW_0087)
    validate_revert_is_possible_mock.assert_not_called()
    clear_mock.assert_not_called()
    task_revert_event_mock.assert_not_called()
    task_returned_analytics_mock.assert_not_called()
    return_workflow_to_task_mock.assert_not_called()


def test_revert__user_performer__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(user=owner, active_task_number=2)
    revert_from_task = workflow.tasks.get(number=2)
    revert_from_task.performers.all().delete()
    TaskPerformer.objects.create(
        task_id=revert_from_task.id,
        user_id=user.id,
    )
    revert_to_task = workflow.tasks.get(number=1)
    validate_revert_is_possible_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._validate_revert_is_possible',
    )
    clear_comment = 'clear'
    clear_mock = mocker.patch(
        'src.processes.services.workflow_action.MarkdownService.clear',
        return_value=clear_comment,
    )
    task_revert_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.task_revert_event',
    )
    task_returned_analytics_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.task_returned',
    )
    return_workflow_to_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._return_workflow_to_task',
    )
    comment = 'comment'
    is_superuser = True
    auth_type = AuthTokenType.API
    service = WorkflowActionService(
        user=user,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    service.revert(comment=comment, revert_from_task=revert_from_task)

    # assert
    validate_revert_is_possible_mock.assert_called_once_with([revert_to_task])
    clear_mock.assert_called_once_with(comment)
    task_revert_event_mock.assert_called_once_with(
        task=revert_to_task,
        user=user,
        text=comment,
        clear_text=clear_comment,
    )
    task_returned_analytics_mock.assert_called_once_with(
        user=user,
        task=revert_from_task,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    return_workflow_to_task_mock.assert_called_once_with(
        revert_from_tasks=(revert_from_task,),
        revert_to_tasks=[revert_to_task],
    )


def test_return_to__ok(mocker):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(user, active_task_number=2)
    revert_to_task = workflow.tasks.get(number=1)
    revert_from_task = workflow.tasks.get(number=2)

    execute_conditions_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        return_value=(WorkflowActionService.start_task, False),
    )
    workflow_revert_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.workflow_revert_event',
    )
    workflow_returned_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.workflow_returned',
    )
    return_workflow_to_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._return_workflow_to_task',
    )
    is_superuser = True
    auth_type = AuthTokenType.API
    service = WorkflowActionService(
        user=user,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )

    # act
    service.return_to(revert_to_task=revert_to_task)

    # assert
    execute_conditions_mock.assert_called_once_with(revert_to_task)
    workflow_revert_event_mock.assert_called_once_with(
        task=revert_to_task,
        user=user,
    )
    workflow_returned_mock.assert_called_once_with(
        user=user,
        task=revert_to_task,
        workflow=workflow,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    return_workflow_to_task_mock.assert_called_once_with(
        revert_from_tasks=[revert_from_task],
        revert_to_tasks=(revert_to_task,),
    )


def test_return_to__task_pending__raise_future_task(mocker):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(user, active_task_number=2)
    revert_to_task = workflow.tasks.get(number=1)
    revert_to_task.status = TaskStatus.PENDING
    revert_to_task.save()
    execute_conditions_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        return_value=(WorkflowActionService.start_task, False),
    )
    workflow_revert_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.workflow_revert_event',
    )
    workflow_returned_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.workflow_returned',
    )
    return_workflow_to_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._return_workflow_to_task',
    )
    service = WorkflowActionService(user=user, workflow=workflow)

    # act
    with pytest.raises(exceptions.ReturnToFutureTask) as ex:
        service.return_to(revert_to_task=revert_to_task)

    # assert
    assert ex.value.message == str(messages.MSG_PW_0081)
    execute_conditions_mock.assert_not_called()
    workflow_revert_event_mock.assert_not_called()
    workflow_returned_mock.assert_not_called()
    return_workflow_to_task_mock.assert_not_called()


@pytest.mark.parametrize('action', (WorkflowActionService.skip_task, None))
def test_return_to__action_skip_task__raise_exception(mocker, action):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(user, active_task_number=2)
    revert_to_task = workflow.tasks.get(number=1)

    execute_conditions_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        return_value=(action, False),
    )
    workflow_revert_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.workflow_revert_event',
    )
    workflow_returned_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.workflow_returned',
    )
    return_workflow_to_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._return_workflow_to_task',
    )
    service = WorkflowActionService(user=user, workflow=workflow)

    # act
    with pytest.raises(exceptions.WorkflowActionServiceException) as ex:
        service.return_to(revert_to_task=revert_to_task)

    # assert
    assert ex.value.message == str(messages.MSG_PW_0079(revert_to_task.name))
    execute_conditions_mock.assert_called_once_with(revert_to_task)
    workflow_revert_event_mock.assert_not_called()
    workflow_returned_mock.assert_not_called()
    return_workflow_to_task_mock.assert_not_called()


def test_return_to__running_sub_wf_running__raise_blocked(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    ancestor_workflow = create_test_workflow(user, active_task_number=2)

    revert_from_task = ancestor_workflow.tasks.get(number=2)
    create_test_workflow(
        user=owner,
        ancestor_task=revert_from_task,
    )

    revert_to_task = ancestor_workflow.tasks.get(number=1)
    execute_conditions_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '.execute_conditions',
        return_value=(WorkflowActionService.start_task, False),
    )
    workflow_revert_event_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowEventService'
        '.workflow_revert_event',
    )
    workflow_returned_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.workflow_returned',
    )
    return_workflow_to_task_mock = mocker.patch(
        'src.processes.services.workflow_action.WorkflowActionService'
        '._return_workflow_to_task',
    )
    service = WorkflowActionService(user=user, workflow=ancestor_workflow)

    # act
    with pytest.raises(exceptions.BlockedBySubWorkflows) as ex:
        service.return_to(revert_to_task=revert_to_task)

    # assert
    assert ex.value.message == str(messages.MSG_PW_0071)
    execute_conditions_mock.assert_called_once_with(revert_to_task)
    workflow_revert_event_mock.assert_not_called()
    workflow_returned_mock.assert_not_called()
    return_workflow_to_task_mock.assert_not_called()
