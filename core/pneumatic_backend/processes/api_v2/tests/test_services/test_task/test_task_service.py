import pytest
from datetime import timedelta, datetime
from django.utils import timezone
from pneumatic_backend.processes.models import (
    TaskField,
    RawDueDate,
    ChecklistTemplate,
    ChecklistTemplateSelection,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template,
    create_test_workflow,
)
from pneumatic_backend.processes.enums import (
    FieldType,
    DueDateRule,
    DirectlyStatus,
)
from pneumatic_backend.processes.api_v2.services.task.task import TaskService


pytestmark = pytest.mark.django_db


def test_create_instance__all_fields__ok(mocker):

    # arrange
    name = 'One of task {{ some-api_name }}'
    api_name = 'task-1'
    revert_task = 'task-0'
    description = 'Some \n {{ another-api_name }} description'

    user = create_test_user()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.get(number=1)
    template_task.api_name = api_name
    template_task.name = name
    template_task.revert_task = revert_task
    template_task.name_template = name
    template_task.description = description
    template_task.description_template = description
    template_task.require_completion_by_all = True
    template_task.save()

    checklist_template = ChecklistTemplate.objects.create(
        template=template,
        task=template_task,
    )
    ChecklistTemplateSelection.objects.create(
        checklist=checklist_template,
        template=template,
        value='some value 1',
    )
    ChecklistTemplateSelection.objects.create(
        checklist=checklist_template,
        template=template,
        value='some value 2',
    )
    workflow = create_test_workflow(user, template=template, is_urgent=True)
    workflow.tasks.delete()
    task = workflow.tasks.first()
    clear_description = 'Some \n clear description'
    clear_mock = mocker.patch(
        'pneumatic_backend.services.markdown.MarkdownService.clear',
        return_value=clear_description
    )
    service = TaskService(
        user=user,
        instance=task
    )

    # act
    service._create_instance(
        instance_template=template_task,
        workflow=workflow
    )

    # assert
    task = service.instance
    assert task.api_name == api_name
    assert task.account == user.account
    assert task.workflow == workflow
    assert task.name == name
    assert task.revert_task == revert_task
    assert task.name_template == name
    assert task.description == description
    assert task.clear_description == clear_description
    assert task.description_template == description
    assert task.number == 1
    assert task.require_completion_by_all is True
    assert task.is_urgent is True
    assert task.checklists_total == 2
    clear_mock.assert_called_once_with(description)


def test_get_task_due_date__raw_due_date_not_exist__return_none():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.first()
    service = TaskService(
        user=user,
        instance=task
    )

    # act
    due_date = service.get_task_due_date()

    # assert
    assert due_date is None


def test_get_task_due_date__rule_before_field__prev_task_field__ok():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)

    duration = timedelta(days=1)
    end_date = timezone.now() + timedelta(days=3)
    tsp_end_date = end_date.timestamp()
    field = TaskField.objects.create(
        task=task_1,
        name='date',
        api_name='date-1',
        type=FieldType.DATE,
        value=tsp_end_date,
        workflow=workflow
    )
    RawDueDate.objects.create(
        task=task_2,
        duration=duration,
        rule=DueDateRule.BEFORE_FIELD,
        source_id=field.api_name,
    )
    service = TaskService(
        user=user,
        instance=task_2
    )
    # act
    due_date = service.get_task_due_date()

    # assert
    assert due_date == datetime.fromtimestamp(tsp_end_date) - duration


def test_get_task_due_date__rule_after_field__prev_task_field__ok():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)

    duration = timedelta(days=1)
    end_date = timezone.now() + timedelta(days=3)
    tsp_end_date = end_date.timestamp()
    field = TaskField.objects.create(
        task=task_1,
        name='date',
        api_name='date-1',
        type=FieldType.DATE,
        value=tsp_end_date,
        workflow=workflow
    )
    RawDueDate.objects.create(
        task=task_2,
        duration=duration,
        rule=DueDateRule.AFTER_FIELD,
        source_id=field.api_name,
    )
    service = TaskService(
        user=user,
        instance=task_2
    )

    # act
    due_date = service.get_task_due_date()

    # assert
    assert due_date == datetime.fromtimestamp(tsp_end_date) + duration


def test_get_task_due_date__rule_after_field__kickoff_field__ok():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)

    duration = timedelta(days=1)
    end_date = timezone.now() + timedelta(days=3)
    tsp_end_date = end_date.timestamp()
    field = TaskField.objects.create(
        kickoff=workflow.kickoff_instance,
        name='date',
        api_name='date-1',
        type=FieldType.DATE,
        value=tsp_end_date,
        workflow=workflow
    )
    RawDueDate.objects.create(
        task=task,
        duration=duration,
        rule=DueDateRule.AFTER_FIELD,
        source_id=field.api_name,
    )
    service = TaskService(
        user=user,
        instance=task
    )

    # act
    due_date = service.get_task_due_date()

    # assert
    assert due_date == datetime.fromtimestamp(tsp_end_date) + duration


@pytest.mark.parametrize('rule', DueDateRule.FIELD_RULES)
def test_get_task_due_date__field_rules__field_not_exists__return_none(rule):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_2 = workflow.tasks.get(number=2)
    RawDueDate.objects.create(
        task=task_2,
        duration=timedelta(days=1),
        rule=DueDateRule.BEFORE_FIELD,
        source_id='some-field',
    )
    service = TaskService(
        user=user,
        instance=task_2
    )

    # act
    due_date = service.get_task_due_date()

    # assert
    assert due_date is None


def test_get_task_due_date__rule_after_workflow_started__ok():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance

    duration = timedelta(hours=1)
    RawDueDate.objects.create(
        task=task,
        duration=duration,
        rule=DueDateRule.AFTER_WORKFLOW_STARTED,
    )
    service = TaskService(
        user=user,
        instance=task
    )

    # act
    due_date = service.get_task_due_date()

    # assert
    assert due_date == (
         workflow.date_created + duration
    )


def test_get_task_due_date__rule_after_task_started__current_task__ok():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance

    duration = timedelta(days=1)
    RawDueDate.objects.create(
        task=task,
        duration=duration,
        rule=DueDateRule.AFTER_TASK_STARTED,
        source_id=task.api_name,
    )
    service = TaskService(
        user=user,
        instance=task
    )

    # act
    due_date = service.get_task_due_date()

    # assert
    assert due_date == task.date_first_started + duration


def test_get_task_due_date__rule_after_task_started__prev_task__ok():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)

    duration = timedelta(hours=1)
    RawDueDate.objects.create(
        task=task_2,
        duration=duration,
        rule=DueDateRule.AFTER_TASK_STARTED,
        source_id=task_1.api_name,
    )
    service = TaskService(
        user=user,
        instance=task_2
    )

    # act
    due_date = service.get_task_due_date()

    # assert
    assert due_date == task_1.date_first_started + duration


def test_get_task_due_date__rule_after_task_completed__prev_task__ok():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.tasks.get(number=1)
    task_1.date_completed = timezone.now() + timedelta(minutes=30)
    task_1.save(update_fields=['date_completed'])
    task_2 = workflow.tasks.get(number=2)

    duration = timedelta(hours=1)
    RawDueDate.objects.create(
        task=task_2,
        duration=duration,
        rule=DueDateRule.AFTER_TASK_COMPLETED,
        source_id=task_1.api_name,
    )
    service = TaskService(
        user=user,
        instance=task_2
    )

    # act
    due_date = service.get_task_due_date()

    # assert
    assert due_date == task_1.date_completed + duration


@pytest.mark.parametrize('rule', DueDateRule.TASK_RULES)
def test_get_task_due_date__task_rules__task_not_exists__return_none(rule):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_2 = workflow.tasks.get(number=2)
    RawDueDate.objects.create(
        task=task_2,
        duration=timedelta(days=1),
        rule=rule,
        source_id='some-task',
    )
    service = TaskService(
        user=user,
        instance=task_2
    )

    # act
    due_date = service.get_task_due_date()

    # assert
    assert due_date is None


def test_get_task_due_date__duration_months__ok():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance

    duration = timedelta(hours=1)
    duration_months = 2
    RawDueDate.objects.create(
        task=task,
        duration=duration,
        duration_months=duration_months,
        rule=DueDateRule.AFTER_WORKFLOW_STARTED,
    )
    service = TaskService(
        user=user,
        instance=task
    )

    # act
    due_date = service.get_task_due_date()

    # assert
    assert due_date == (
         workflow.date_created + duration + timedelta(days=30*duration_months)
    )


@pytest.mark.parametrize(
    'directly_status',
    (DirectlyStatus.CREATED, DirectlyStatus.DELETED)
)
def test_set_due_date_from_template__directly_changed__skip(
    directly_status,
    mocker
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    task.due_date_directly_status = directly_status
    task.save(update_fields=['due_date_directly_status'])
    get_task_due_date_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.task.'
        'TaskService.get_task_due_date'
    )
    service = TaskService(
        user=user,
        instance=task
    )

    # act
    service.set_due_date_from_template()

    # assert
    get_task_due_date_mock.assert_not_called()


def test_set_due_date_from_template__ok(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    due_date = timezone.now() + timedelta(days=1)
    get_task_due_date_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.task.'
        'TaskService.get_task_due_date',
        return_value=due_date
    )
    service = TaskService(
        user=user,
        instance=task
    )

    # act
    service.set_due_date_from_template()

    # assert
    get_task_due_date_mock.assert_called_once()
    assert task.due_date == due_date


def test_set_due_date_from_template__not_exist__skip(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    due_date = None
    get_task_due_date_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.task.'
        'TaskService.get_task_due_date',
        return_value=due_date
    )
    partial_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.task.'
        'TaskService.partial_update',
        return_value=due_date
    )
    service = TaskService(
        user=user,
        instance=task
    )

    # act
    service.set_due_date_from_template()

    # assert
    get_task_due_date_mock.assert_called_once()
    partial_update_mock.assert_not_called()


def test_set_due_date_from_template__not_changed__skip(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    due_date = timezone.now() + timedelta(days=1)
    task.due_date = due_date
    task.save(update_fields=['due_date'])
    get_task_due_date_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.task.'
        'TaskService.get_task_due_date',
        return_value=due_date
    )
    partial_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.task.'
        'TaskService.partial_update',
        return_value=due_date
    )
    service = TaskService(
        user=user,
        instance=task
    )

    # act
    service.set_due_date_from_template()

    # assert
    get_task_due_date_mock.assert_called_once()
    partial_update_mock.assert_not_called()


def test_set_due_date_directly__ok(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    due_date = timezone.now() + timedelta(days=1)
    partial_update_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.task.task.'
        'TaskService.partial_update',
    )
    send_notifications_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks.send_due_date_changed.delay'
    )
    due_date_changed_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowEventService.'
        'due_date_changed_event'
    )
    service = TaskService(instance=task, user=user)

    # act
    service.set_due_date_directly(value=due_date)

    # assert
    partial_update_mock.assert_called_once_with(
        due_date=due_date,
        force_save=True
    )
    send_notifications_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        author_id=user.id,
        task_id=task.id,
        account_id=user.account_id,
        logo_lg=user.account.logo_lg,
    )
    due_date_changed_event_mock.assert_called_once_with(task=task, user=user)
