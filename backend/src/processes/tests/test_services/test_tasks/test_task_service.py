from datetime import datetime, timedelta
from datetime import timezone as tz

import pytest
from django.utils import timezone

from src.processes.enums import (
    DirectlyStatus,
    DueDateRule,
    FieldType,
)
from src.processes.models.templates.checklist import (
    ChecklistTemplate,
    ChecklistTemplateSelection,
)
from src.processes.models.workflows.fields import TaskField
from src.processes.models.workflows.raw_due_date import RawDueDate
from src.authentication.enums import AuthTokenType
from src.processes.services.tasks.task import TaskService
from src.processes.tests.fixtures import (
    create_test_template,
    create_test_user,
    create_test_workflow,
)

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
        'src.services.markdown.MarkdownService.clear',
        return_value=clear_description,
    )
    service = TaskService(
        user=user,
        instance=task,
    )

    # act
    service._create_instance(
        instance_template=template_task,
        workflow=workflow,
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
    assert task.skip_for_starter is False
    assert task.is_urgent is True
    assert task.checklists_total == 2
    clear_mock.assert_called_once_with(description)


def test_create_instance__skip_flag_true__ok(mocker):

    # arrange
    user = create_test_user()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.get(number=1)
    template_task.skip_for_starter = True
    template_task.save(
        update_fields=['skip_for_starter'],
    )
    workflow = create_test_workflow(user, template=template)
    workflow.tasks.delete()
    clear_description = 'clear'
    mocker.patch(
        'src.services.markdown.MarkdownService.clear',
        return_value=clear_description,
    )
    service = TaskService(
        user=user,
        instance=None,
    )

    # act
    service._create_instance(
        instance_template=template_task,
        workflow=workflow,
    )

    # assert
    task = service.instance
    assert task.skip_for_starter is True
    assert task.require_completion_by_all is False


def test_get_task_due_date__raw_due_date_not_exist__return_none():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.first()
    service = TaskService(
        user=user,
        instance=task,
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
        workflow=workflow,
        account=user.account,
    )
    RawDueDate.objects.create(
        task=task_2,
        duration=duration,
        rule=DueDateRule.BEFORE_FIELD,
        source_id=field.api_name,
    )
    service = TaskService(
        user=user,
        instance=task_2,
    )
    # act
    due_date = service.get_task_due_date()

    # assert
    assert due_date == datetime.fromtimestamp(
        tsp_end_date,
        tz=tz.utc,
    ) - duration


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
        workflow=workflow,
        account=user.account,
    )
    RawDueDate.objects.create(
        task=task_2,
        duration=duration,
        rule=DueDateRule.AFTER_FIELD,
        source_id=field.api_name,
    )
    service = TaskService(
        user=user,
        instance=task_2,
    )

    # act
    due_date = service.get_task_due_date()

    # assert
    assert due_date == datetime.fromtimestamp(
        tsp_end_date,
        tz=tz.utc,
    ) + duration


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
        workflow=workflow,
        account=user.account,
    )
    RawDueDate.objects.create(
        task=task,
        duration=duration,
        rule=DueDateRule.AFTER_FIELD,
        source_id=field.api_name,
    )
    service = TaskService(
        user=user,
        instance=task,
    )

    # act
    due_date = service.get_task_due_date()

    # assert
    assert due_date == datetime.fromtimestamp(
        tsp_end_date,
        tz=tz.utc,
    ) + duration


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
        instance=task_2,
    )

    # act
    due_date = service.get_task_due_date()

    # assert
    assert due_date is None


def test_get_task_due_date__rule_after_workflow_started__ok():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    duration = timedelta(hours=1)
    RawDueDate.objects.create(
        task=task,
        duration=duration,
        rule=DueDateRule.AFTER_WORKFLOW_STARTED,
    )
    service = TaskService(
        user=user,
        instance=task,
    )

    # act
    due_date = service.get_task_due_date()

    # assert
    assert due_date == (
         workflow.date_created + duration
    )


def test_get_task_due_date__rule_after_task_started__active_task__ok():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    duration = timedelta(days=1)
    RawDueDate.objects.create(
        task=task,
        duration=duration,
        rule=DueDateRule.AFTER_TASK_STARTED,
        source_id=task.api_name,
    )
    service = TaskService(
        user=user,
        instance=task,
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
        instance=task_2,
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
        instance=task_2,
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
        instance=task_2,
    )

    # act
    due_date = service.get_task_due_date()

    # assert
    assert due_date is None


def test_get_task_due_date__duration_months__ok():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
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
        instance=task,
    )

    # act
    due_date = service.get_task_due_date()

    # assert
    assert due_date == (
         workflow.date_created + duration + timedelta(days=30*duration_months)
    )


@pytest.mark.parametrize(
    'directly_status',
    (DirectlyStatus.CREATED, DirectlyStatus.DELETED),
)
def test_set_due_date_from_template__directly_changed__skip(
    directly_status,
    mocker,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.due_date_directly_status = directly_status
    task.save(update_fields=['due_date_directly_status'])
    get_task_due_date_mock = mocker.patch(
        'src.processes.services.tasks.task.'
        'TaskService.get_task_due_date',
    )
    service = TaskService(
        user=user,
        instance=task,
    )

    # act
    service.set_due_date_from_template()

    # assert
    get_task_due_date_mock.assert_not_called()


def test_set_due_date_from_template__ok(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    due_date = timezone.now() + timedelta(days=1)
    get_task_due_date_mock = mocker.patch(
        'src.processes.services.tasks.task.'
        'TaskService.get_task_due_date',
        return_value=due_date,
    )
    service = TaskService(
        user=user,
        instance=task,
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
    task = workflow.tasks.get(number=1)
    due_date = None
    get_task_due_date_mock = mocker.patch(
        'src.processes.services.tasks.task.'
        'TaskService.get_task_due_date',
        return_value=due_date,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.tasks.task.'
        'TaskService.partial_update',
        return_value=due_date,
    )
    service = TaskService(
        user=user,
        instance=task,
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
    task = workflow.tasks.get(number=1)
    due_date = timezone.now() + timedelta(days=1)
    task.due_date = due_date
    task.save(update_fields=['due_date'])
    get_task_due_date_mock = mocker.patch(
        'src.processes.services.tasks.task.'
        'TaskService.get_task_due_date',
        return_value=due_date,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.tasks.task.'
        'TaskService.partial_update',
        return_value=due_date,
    )
    service = TaskService(
        user=user,
        instance=task,
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
    task = workflow.tasks.get(number=1)
    due_date = timezone.now() + timedelta(days=1)
    partial_update_mock = mocker.patch(
        'src.processes.services.tasks.task.'
        'TaskService.partial_update',
    )
    send_notifications_mock = mocker.patch(
        'src.notifications.tasks.send_due_date_changed.delay',
    )
    due_date_changed_event_mock = mocker.patch(
        'src.processes.services.events.WorkflowEventService.'
        'due_date_changed_event',
    )
    service = TaskService(instance=task, user=user)

    # act
    service.set_due_date_directly(value=due_date)

    # assert
    partial_update_mock.assert_called_once_with(
        due_date=due_date,
        force_save=True,
    )
    send_notifications_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        author_id=user.id,
        task_id=task.id,
        account_id=user.account_id,
        logo_lg=user.account.logo_lg,
    )
    due_date_changed_event_mock.assert_called_once_with(task=task, user=user)


def test_insert_fields_values__description_template_used__ok(mocker):
    """
    Sets `instance.description` using the value returned by
    `insert_fields_values_to_text` called with `description_template`.
    """

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.description_template = 'Hello {{field-1}}'
    task.save(update_fields=['description_template'])
    name_template = task.name_template
    new_description = 'Hello World'
    fields_values = {'field-1': 'World'}
    insert_fields_values_to_text_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.insert_fields_values_to_text',
        return_value=new_description,
    )
    markdown_clear_mock = mocker.patch(
        'src.processes.services.tasks.task.MarkdownService.clear',
    )
    checklist_service_mock = mocker.patch(
        'src.processes.services.tasks.task.ChecklistService',
    )
    save_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.save',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.insert_fields_values(fields_values=fields_values)

    # assert
    assert service.instance.description == new_description
    assert insert_fields_values_to_text_mock.call_count == 2
    insert_fields_values_to_text_mock.assert_has_calls([
        mocker.call(
            text=task.description_template,
            fields_values=fields_values,
        ),
        mocker.call(
            text=name_template,
            fields_values=fields_values,
        ),
        ],
        any_order=True,
    )
    markdown_clear_mock.assert_called_once_with(new_description)
    checklist_service_mock.assert_not_called()
    save_mock.assert_called_once_with()


def test_insert_fields_values__clear_description_updated__ok(mocker):
    """
    Sets `instance.clear_description` to the value returned by
    `MarkdownService.clear` applied to the new description.
    """

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    description_template = task.description_template
    name_template = task.name_template
    new_description = 'Hello World'
    clear_description = 'Hello World clear'
    fields_values = {'field-1': 'World'}
    insert_fields_values_to_text_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.insert_fields_values_to_text',
        return_value=new_description,
    )
    markdown_clear_mock = mocker.patch(
        'src.processes.services.tasks.task.MarkdownService.clear',
        return_value=clear_description,
    )
    checklist_service_mock = mocker.patch(
        'src.processes.services.tasks.task.ChecklistService',
    )
    save_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.save',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.insert_fields_values(fields_values=fields_values)

    # assert
    assert service.instance.clear_description == clear_description
    assert insert_fields_values_to_text_mock.call_count == 2
    insert_fields_values_to_text_mock.assert_has_calls([
        mocker.call(
            text=description_template,
            fields_values=fields_values,
        ),
        mocker.call(
            text=name_template,
            fields_values=fields_values,
        ),
        ],
        any_order=True,
    )
    markdown_clear_mock.assert_called_once_with(new_description)
    checklist_service_mock.assert_not_called()
    save_mock.assert_called_once_with()


def test_insert_fields_values__name_template_used__ok(mocker):
    """
    Sets `instance.name` using the value returned by
    `insert_fields_values_to_text` called with `name_template`.
    """

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    description_template = task.description_template
    task.name_template = 'Task {{field-1}}'
    task.save(update_fields=['name_template'])
    new_name = 'Task Alpha'
    fields_values = {'field-1': 'Alpha'}
    insert_fields_values_to_text_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.insert_fields_values_to_text',
        return_value=new_name,
    )
    markdown_clear_mock = mocker.patch(
        'src.processes.services.tasks.task.MarkdownService.clear',
    )
    checklist_service_mock = mocker.patch(
        'src.processes.services.tasks.task.ChecklistService',
    )
    save_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.save',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.insert_fields_values(fields_values=fields_values)

    # assert
    assert service.instance.name == new_name
    assert insert_fields_values_to_text_mock.call_count == 2
    insert_fields_values_to_text_mock.assert_has_calls([
        mocker.call(
            text=description_template,
            fields_values=fields_values,
        ),
        mocker.call(
            text=task.name_template,
            fields_values=fields_values,
        ),
        ],
        any_order=True,
    )
    markdown_clear_mock.assert_called_once_with(new_name)
    checklist_service_mock.assert_not_called()
    save_mock.assert_called_once_with()


def test_insert_fields_values__three_fields_marked_for_update__ok(
    mocker,
):
    """
    Adds `description`, `clear_description`, and `name` to
    `update_fields` before calling `save`.
    """

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    description_template = task.description_template
    name_template = task.name_template
    new_description = 'Updated description'
    fields_values = {'field-1': 'val'}
    insert_fields_values_to_text_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.insert_fields_values_to_text',
        return_value=new_description,
    )
    markdown_clear_mock = mocker.patch(
        'src.processes.services.tasks.task.MarkdownService.clear',
    )
    checklist_service_mock = mocker.patch(
        'src.processes.services.tasks.task.ChecklistService',
    )
    save_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.save',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.insert_fields_values(fields_values=fields_values)

    # assert
    assert 'description' in service.update_fields
    assert 'clear_description' in service.update_fields
    assert 'name' in service.update_fields
    assert insert_fields_values_to_text_mock.call_count == 2
    insert_fields_values_to_text_mock.assert_has_calls([
        mocker.call(
            text=description_template,
            fields_values=fields_values,
        ),
        mocker.call(
            text=name_template,
            fields_values=fields_values,
        ),
        ],
        any_order=True,
    )
    markdown_clear_mock.assert_called_once_with(new_description)
    checklist_service_mock.assert_not_called()
    save_mock.assert_called_once_with()


def test_insert_fields_values__save_called_once__ok(mocker):
    """
    Calls `self.save()` exactly once after updating all three fields.
    """

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    description_template = task.description_template
    name_template = task.name_template
    new_description = 'Updated description'
    fields_values = {'field-1': 'val'}
    insert_fields_values_to_text_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.insert_fields_values_to_text',
        return_value=new_description,
    )
    markdown_clear_mock = mocker.patch(
        'src.processes.services.tasks.task.MarkdownService.clear',
    )
    checklist_service_mock = mocker.patch(
        'src.processes.services.tasks.task.ChecklistService',
    )
    save_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.save',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.insert_fields_values(fields_values=fields_values)

    # assert
    assert insert_fields_values_to_text_mock.call_count == 2
    insert_fields_values_to_text_mock.assert_has_calls([
        mocker.call(
            text=description_template,
            fields_values=fields_values,
        ),
        mocker.call(
            text=name_template,
            fields_values=fields_values,
        ),
        ],
        any_order=True,
    )
    markdown_clear_mock.assert_called_once_with(new_description)
    checklist_service_mock.assert_not_called()
    save_mock.assert_called_once_with()


def test_insert_fields_values__description_template_passed_to_insert__ok(
    mocker,
):
    """
    Calls `insert_fields_values_to_text` with
    `text=description_template` and the provided `fields_values`.
    """

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    description_template = 'Hello {{field-1}}'
    task.description_template = description_template
    task.save(update_fields=['description_template'])
    name_template = task.name_template
    new_description = 'Updated description'
    fields_values = {'field-1': 'World'}
    insert_fields_values_to_text_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.insert_fields_values_to_text',
        return_value=new_description,
    )
    markdown_clear_mock = mocker.patch(
        'src.processes.services.tasks.task.MarkdownService.clear',
    )
    checklist_service_mock = mocker.patch(
        'src.processes.services.tasks.task.ChecklistService',
    )
    save_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.save',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.insert_fields_values(fields_values=fields_values)

    # assert
    assert insert_fields_values_to_text_mock.call_count == 2
    insert_fields_values_to_text_mock.assert_has_calls([
        mocker.call(
            text=description_template,
            fields_values=fields_values,
        ),
        mocker.call(
            text=name_template,
            fields_values=fields_values,
        ),
        ],
        any_order=True,
    )
    markdown_clear_mock.assert_called_once_with(new_description)
    checklist_service_mock.assert_not_called()
    save_mock.assert_called_once_with()


def test_insert_fields_values__name_template_passed_to_insert__ok(
    mocker,
):
    """
    Calls `insert_fields_values_to_text` with
    `text=name_template` and the provided `fields_values`.
    """

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    description_template = task.description_template
    name_template = 'Task {{field-1}}'
    task.name_template = name_template
    task.save(update_fields=['name_template'])
    new_description = 'Updated description'
    fields_values = {'field-1': 'Alpha'}
    insert_fields_values_to_text_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.insert_fields_values_to_text',
        return_value=new_description,
    )
    markdown_clear_mock = mocker.patch(
        'src.processes.services.tasks.task.MarkdownService.clear',
    )
    checklist_service_mock = mocker.patch(
        'src.processes.services.tasks.task.ChecklistService',
    )
    save_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.save',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.insert_fields_values(fields_values=fields_values)

    # assert
    assert insert_fields_values_to_text_mock.call_count == 2
    insert_fields_values_to_text_mock.assert_has_calls([
        mocker.call(
            text=description_template,
            fields_values=fields_values,
        ),
        mocker.call(
            text=name_template,
            fields_values=fields_values,
        ),
        ],
        any_order=True,
    )
    markdown_clear_mock.assert_called_once_with(new_description)
    checklist_service_mock.assert_not_called()
    save_mock.assert_called_once_with()


def test_insert_fields_values__markdown_clear_receives_new_description__ok(
    mocker,
):
    """
    Calls `MarkdownService.clear` with the new description value
    (result of `insert_fields_values_to_text`).
    """

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    description_template = task.description_template
    name_template = task.name_template
    new_description = 'Hello World'
    fields_values = {'field-1': 'World'}
    insert_fields_values_to_text_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.insert_fields_values_to_text',
        return_value=new_description,
    )
    markdown_clear_mock = mocker.patch(
        'src.processes.services.tasks.task.MarkdownService.clear',
    )
    checklist_service_mock = mocker.patch(
        'src.processes.services.tasks.task.ChecklistService',
    )
    save_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.save',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.insert_fields_values(fields_values=fields_values)

    # assert
    assert insert_fields_values_to_text_mock.call_count == 2
    insert_fields_values_to_text_mock.assert_has_calls([
        mocker.call(
            text=description_template,
            fields_values=fields_values,
        ),
        mocker.call(
            text=name_template,
            fields_values=fields_values,
        ),
        ],
        any_order=True,
    )
    markdown_clear_mock.assert_called_once_with(new_description)
    checklist_service_mock.assert_not_called()
    save_mock.assert_called_once_with()


def test_insert_fields_values__checklist_service_init_args__ok(mocker):
    """
    Creates one `ChecklistService` per checklist with correct
    `instance`, `user`, `is_superuser`, `auth_type`.
    """

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    description_template = task.description_template
    name_template = task.name_template
    new_description = 'Updated description'
    fields_values = {'field-1': 'val'}
    insert_fields_values_to_text_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.insert_fields_values_to_text',
        return_value=new_description,
    )
    markdown_clear_mock = mocker.patch(
        'src.processes.services.tasks.task.MarkdownService.clear',
    )
    checklist_service_init_mock = mocker.patch(
        'src.processes.services.tasks.task.ChecklistService.__init__',
        return_value=None,
    )
    checklist_insert_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.ChecklistService.insert_fields_values',
    )
    save_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.save',
    )
    is_superuser = False
    auth_type = AuthTokenType.USER
    service = TaskService(
        user=user,
        instance=task,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )
    checklists = list(task.checklists.all())

    # act
    service.insert_fields_values(fields_values=fields_values)

    # assert
    assert insert_fields_values_to_text_mock.call_count == 2
    insert_fields_values_to_text_mock.assert_has_calls([
        mocker.call(
            text=description_template,
            fields_values=fields_values,
        ),
        mocker.call(
            text=name_template,
            fields_values=fields_values,
        ),
        ],
        any_order=True,
    )
    markdown_clear_mock.assert_called_once_with(new_description)
    assert checklist_service_init_mock.call_count == len(checklists)
    checklist_service_init_mock.assert_has_calls(
        [
            mocker.call(
                instance=checklist,
                user=user,
                is_superuser=is_superuser,
                auth_type=auth_type,
            )
            for checklist in checklists
        ],
        any_order=True,
    )
    assert checklist_insert_mock.call_count == len(checklists)
    save_mock.assert_called_once_with()


def test_insert_fields_values__insert_called_per_checklist__ok(mocker):
    """
    Calls `checklist_service.insert_fields_values(fields_values)`
    for each checklist returned by `checklists.all()`.
    """

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    description_template = task.description_template
    name_template = task.name_template
    new_description = 'Updated description'
    fields_values = {'field-1': 'val'}
    insert_fields_values_to_text_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.insert_fields_values_to_text',
        return_value=new_description,
    )
    markdown_clear_mock = mocker.patch(
        'src.processes.services.tasks.task.MarkdownService.clear',
    )
    checklist_service_init_mock = mocker.patch(
        'src.processes.services.tasks.task.ChecklistService.__init__',
        return_value=None,
    )
    insert_fields_values_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.ChecklistService.insert_fields_values',
    )
    save_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.save',
    )
    service = TaskService(user=user, instance=task)
    checklists_count = task.checklists.all().count()

    # act
    service.insert_fields_values(fields_values=fields_values)

    # assert
    assert insert_fields_values_to_text_mock.call_count == 2
    insert_fields_values_to_text_mock.assert_has_calls([
        mocker.call(
            text=description_template,
            fields_values=fields_values,
        ),
        mocker.call(
            text=name_template,
            fields_values=fields_values,
        ),
        ],
        any_order=True,
    )
    markdown_clear_mock.assert_called_once_with(new_description)
    assert checklist_service_init_mock.call_count == checklists_count
    assert insert_fields_values_mock.call_count == checklists_count
    insert_fields_values_mock.assert_has_calls(
        [mocker.call(fields_values)] * checklists_count,
        any_order=True,
    )
    save_mock.assert_called_once_with()


def test_insert_fields_values__no_checklists__skip(mocker):
    """
    Does not instantiate `ChecklistService` when
    `checklists.all()` returns an empty list.
    """

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.checklists.all().delete()
    description_template = task.description_template
    name_template = task.name_template
    new_description = 'Updated description'
    fields_values = {'field-1': 'val'}
    insert_fields_values_to_text_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.insert_fields_values_to_text',
        return_value=new_description,
    )
    markdown_clear_mock = mocker.patch(
        'src.processes.services.tasks.task.MarkdownService.clear',
    )
    checklist_service_init_mock = mocker.patch(
        'src.processes.services.tasks.task.ChecklistService.__init__',
        return_value=None,
    )
    save_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.save',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.insert_fields_values(fields_values=fields_values)

    # assert
    assert insert_fields_values_to_text_mock.call_count == 2
    insert_fields_values_to_text_mock.assert_has_calls([
        mocker.call(
            text=description_template,
            fields_values=fields_values,
        ),
        mocker.call(
            text=name_template,
            fields_values=fields_values,
        ),
        ],
        any_order=True,
    )
    markdown_clear_mock.assert_called_once_with(new_description)
    checklist_service_init_mock.assert_not_called()
    save_mock.assert_called_once_with()
