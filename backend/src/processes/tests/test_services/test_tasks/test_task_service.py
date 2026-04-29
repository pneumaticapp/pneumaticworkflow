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
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.templates.raw_due_date import RawDueDateTemplate
from src.processes.models.workflows.fields import TaskField
from src.processes.models.workflows.raw_due_date import RawDueDate
from src.processes.models.workflows.task import Delay
from src.authentication.enums import AuthTokenType
from src.processes.services.tasks.checklist import ChecklistService
from src.processes.services.tasks.field import TaskFieldService
from src.processes.services.tasks.task import TaskService
from src.processes.services.workflows.fieldsets.fieldset import FieldSetService
from src.processes.tests.fixtures import (
    create_checklist_template,
    create_test_account,
    create_test_admin,
    create_test_fieldset_template,
    create_test_owner,
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


def test_partial_update__default__ok(mocker):

    """
    Default call
    """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    markdown_clear_mock = mocker.patch(
        'src.processes.services.tasks.task.MarkdownService.clear',
    )
    save_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.save',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.partial_update()

    # assert
    markdown_clear_mock.assert_not_called()
    save_mock.assert_not_called()


def test_partial_update__with_desc__clear_desc_set(mocker):

    """
    With description
    """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    description = 'New description'
    clear_description = 'New clear description'
    markdown_clear_mock = mocker.patch(
        'src.processes.services.tasks.task.MarkdownService.clear',
        return_value=clear_description,
    )
    save_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.save',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.partial_update(description=description)

    # assert
    assert task.description == description
    assert task.clear_description == clear_description
    markdown_clear_mock.assert_called_once_with(description)
    save_mock.assert_not_called()


def test_partial_update__no_desc__clear_desc_skip(mocker):

    """
    Without description
    """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    original_clear_description = task.clear_description
    markdown_clear_mock = mocker.patch(
        'src.processes.services.tasks.task.MarkdownService.clear',
    )
    save_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.save',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.partial_update(name='New name')

    # assert
    assert task.name == 'New name'
    assert task.clear_description == original_clear_description
    markdown_clear_mock.assert_not_called()
    save_mock.assert_not_called()


def test_partial_update__date_started_first__set(mocker):

    """
    date_started, first start
    """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.date_first_started = None
    task.save(update_fields=['date_first_started'])
    date_started = timezone.now()
    markdown_clear_mock = mocker.patch(
        'src.processes.services.tasks.task.MarkdownService.clear',
    )
    save_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.save',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.partial_update(date_started=date_started)

    # assert
    assert task.date_first_started == date_started
    assert 'date_first_started' in service.update_fields
    markdown_clear_mock.assert_not_called()
    save_mock.assert_not_called()


def test_partial_update__date_started_already__skip(mocker):

    """
    date_started, already started
    """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    original_date_first_started = timezone.now() - timedelta(hours=1)
    task.date_first_started = original_date_first_started
    task.save(update_fields=['date_first_started'])
    date_started = timezone.now()
    markdown_clear_mock = mocker.patch(
        'src.processes.services.tasks.task.MarkdownService.clear',
    )
    save_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.save',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.partial_update(date_started=date_started)

    # assert
    assert task.date_first_started == original_date_first_started
    assert 'date_first_started' not in service.update_fields
    markdown_clear_mock.assert_not_called()
    save_mock.assert_not_called()


def test_partial_update__force_save__saved(mocker):

    """
    force_save True
    """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    markdown_clear_mock = mocker.patch(
        'src.processes.services.tasks.task.MarkdownService.clear',
    )
    save_mock = mocker.patch(
        'src.processes.services.tasks.task.TaskService.save',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.partial_update(force_save=True, name='Updated')

    # assert
    assert task.name == 'Updated'
    markdown_clear_mock.assert_not_called()
    save_mock.assert_called_once_with()


def test_create_raw_performers_from_template__default__ok(mocker):

    """
    Default call
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.get(number=1)
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    add_raw_performer_mock = mocker.patch(
        'src.processes.models.workflows.task.Task.add_raw_performer',
    )
    update_raw_performers_mock = mocker.patch(
        'src.processes.models.workflows.task.Task'
        '.update_raw_performers_from_task_template',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.create_raw_performers_from_template(
        instance_template=template_task,
    )

    # assert
    add_raw_performer_mock.assert_not_called()
    update_raw_performers_mock.assert_called_once_with(template_task)


def test_create_raw_performers_from_template__redefined__ok(mocker):

    """
    With redefined_performer
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    redefined_performer = create_test_admin(account=account)
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.get(number=1)
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    add_raw_performer_mock = mocker.patch(
        'src.processes.models.workflows.task.Task.add_raw_performer',
    )
    update_raw_performers_mock = mocker.patch(
        'src.processes.models.workflows.task.Task'
        '.update_raw_performers_from_task_template',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.create_raw_performers_from_template(
        instance_template=template_task,
        redefined_performer=redefined_performer,
    )

    # assert
    add_raw_performer_mock.assert_called_once_with(
        user=redefined_performer,
    )
    update_raw_performers_mock.assert_not_called()


def test_create_fields_from_template__no_fields__ok(mocker):

    """
    Default call, no fields
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.get(number=1)
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        '__init__',
        return_value=None,
    )
    service = TaskService(user=user, instance=task)

    # act
    service.create_fields_from_template(instance_template=template_task)

    # assert
    task_field_service_init_mock.assert_not_called()


def test_create_fields_from_template__outside_fs__ok(mocker):

    """
    Fields outside fieldsets
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.get(number=1)
    field_template_1 = FieldTemplate.objects.create(
        name='Field 1',
        type=FieldType.STRING,
        task=template_task,
        template=template,
        order=1,
        api_name='field-1',
        account=user.account,
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        '__init__',
        return_value=None,
    )
    task_field_service_create_mock = mocker.patch(
        'src.processes.services.tasks.field.TaskFieldService.create',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.create_fields_from_template(instance_template=template_task)

    # assert
    task_field_service_init_mock.assert_called_once_with(user=user)
    task_field_service_create_mock.assert_called_once_with(
        instance_template=field_template_1,
        workflow_id=task.workflow_id,
        task_id=task.id,
        skip_value=True,
    )


def test_create_fields_from_template__in_fieldsets__skip(mocker):

    """
    Fields inside fieldsets
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.get(number=1)
    create_test_fieldset_template(
        account=user.account,
        template=template,
        task=template_task,
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    task_field_service_init_mock = mocker.patch.object(
        TaskFieldService,
        '__init__',
        return_value=None,
    )
    service = TaskService(user=user, instance=task)

    # act
    service.create_fields_from_template(instance_template=template_task)

    # assert
    task_field_service_init_mock.assert_not_called()


def test_create_fieldsets_from_template__no_fieldsets__ok(mocker):

    """
    Default call, no fieldsets
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.get(number=1)
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    field_set_service_init_mock = mocker.patch.object(
        FieldSetService,
        '__init__',
        return_value=None,
    )
    service = TaskService(user=user, instance=task)

    # act
    service.create_fieldsets_from_template(instance_template=template_task)

    # assert
    field_set_service_init_mock.assert_not_called()


def test_create_fieldsets_from_template__with_fieldsets__ok(mocker):

    """
    With fieldsets
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.get(number=1)
    fieldset_template = create_test_fieldset_template(
        account=user.account,
        template=template,
        task=template_task,
        order=5,
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    field_set_service_init_mock = mocker.patch.object(
        FieldSetService,
        '__init__',
        return_value=None,
    )
    field_set_service_create_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset'
        '.FieldSetService.create',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.create_fieldsets_from_template(instance_template=template_task)

    # assert
    field_set_service_init_mock.assert_called_once_with(user=user)
    field_set_service_create_mock.assert_called_once_with(
        instance_template=fieldset_template,
        account_id=task.workflow.account_id,
        workflow=task.workflow,
        task=task,
        order=5,
        skip_value=True,
    )


def test_create_conditions_from_template__no_conditions__ok(mocker):

    """
    Default call, no conditions
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.get(number=1)

    # remove default conditions
    template_task.conditions.all().delete()
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    create_rules_mock = mocker.patch(
        'src.processes.services.tasks.mixins.ConditionMixin.create_rules',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.create_conditions_from_template(
        instance_template=template_task,
    )

    # assert
    create_rules_mock.assert_not_called()


def test_create_conditions_from_template__with_conditions__ok(mocker):

    """
    With conditions
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=2)
    template_task = template.tasks.get(number=2)
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=2)
    create_rules_mock = mocker.patch(
        'src.processes.services.tasks.mixins.ConditionMixin.create_rules',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.create_conditions_from_template(
        instance_template=template_task,
    )

    # assert
    create_rules_mock.assert_called_once_with(
        mocker.ANY,
        mocker.ANY,
    )


def test_create_checklists_from_template__no_checklists__ok(mocker):

    """
    Default call, no checklists
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.get(number=1)
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    checklist_service_init_mock = mocker.patch.object(
        ChecklistService,
        '__init__',
        return_value=None,
    )
    service = TaskService(user=user, instance=task)

    # act
    service.create_checklists_from_template(
        instance_template=template_task,
    )

    # assert
    checklist_service_init_mock.assert_not_called()


def test_create_checklists_from_template__with_checklists__ok(mocker):

    """
    With checklists
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.get(number=1)
    checklist_template_1 = create_checklist_template(
        task_template=template_task,
        selections_count=1,
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    checklist_service_init_mock = mocker.patch.object(
        ChecklistService,
        '__init__',
        return_value=None,
    )
    checklist_service_create_mock = mocker.patch(
        'src.processes.services.tasks.checklist.ChecklistService.create',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.create_checklists_from_template(
        instance_template=template_task,
    )

    # assert
    checklist_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=service.is_superuser,
        auth_type=service.auth_type,
    )
    checklist_service_create_mock.assert_called_once_with(
        instance_template=checklist_template_1,
        task=task,
    )


def test_create_raw_due_date_from_template__no_raw__ok():

    """
    Default call, no raw_due_date
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.get(number=1)
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    service = TaskService(user=user, instance=task)

    # act
    service.create_raw_due_date_from_template(
        instance_template=template_task,
    )

    # assert
    assert not RawDueDate.objects.filter(task=task).exists()


def test_create_raw_due_date_from_template__with_raw__ok():

    """
    With raw_due_date
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.get(number=1)
    duration = timedelta(hours=2)
    duration_months = 1
    RawDueDateTemplate.objects.create(
        task=template_task,
        template=template,
        duration=duration,
        duration_months=duration_months,
        rule=DueDateRule.AFTER_WORKFLOW_STARTED,
        source_id=None,
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)

    # remove any raw_due_date created by workflow fixture
    RawDueDate.objects.filter(task=task).delete()
    service = TaskService(user=user, instance=task)

    # act
    service.create_raw_due_date_from_template(
        instance_template=template_task,
    )

    # assert
    raw_due_date = RawDueDate.objects.get(task=task)
    assert raw_due_date.duration == duration
    assert raw_due_date.duration_months == duration_months
    assert raw_due_date.rule == DueDateRule.AFTER_WORKFLOW_STARTED
    assert raw_due_date.source_id is None


def test_get_task_due_date__after_started_same__none():

    """
    After task started, same, no date
    """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.date_first_started = None
    task.save(update_fields=['date_first_started'])
    RawDueDate.objects.create(
        task=task,
        duration=timedelta(days=1),
        rule=DueDateRule.AFTER_TASK_STARTED,
        source_id=task.api_name,
    )
    service = TaskService(user=user, instance=task)

    # act
    due_date = service.get_task_due_date()

    # assert
    assert due_date is None


def test_get_task_due_date__field_no_value__none():

    """
    Field rule, no value
    """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=2)
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    field = TaskField.objects.create(
        task=task_1,
        name='date',
        api_name='date-1',
        type=FieldType.DATE,
        value='',
        workflow=workflow,
        account=user.account,
    )
    RawDueDate.objects.create(
        task=task_2,
        duration=timedelta(days=1),
        rule=DueDateRule.AFTER_FIELD,
        source_id=field.api_name,
    )
    service = TaskService(user=user, instance=task_2)

    # act
    due_date = service.get_task_due_date()

    # assert
    assert due_date is None


def test_create_related__no_delay__ok(mocker):

    """
    Default call, no delay
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.get(number=1)
    template_task.delay = None
    template_task.save(update_fields=['delay'])
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    create_raw_performers_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.TaskService.create_raw_performers_from_template',
    )
    create_fields_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.TaskService.create_fields_from_template',
    )
    create_fieldsets_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.TaskService.create_fieldsets_from_template',
    )
    create_conditions_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.TaskService.create_conditions_from_template',
    )
    create_checklists_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.TaskService.create_checklists_from_template',
    )
    create_raw_due_date_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.TaskService.create_raw_due_date_from_template',
    )
    service = TaskService(user=user, instance=task)

    # act
    service._create_related(
        instance_template=template_task,
    )

    # assert
    assert not Delay.objects.filter(task=task).exists()
    create_raw_performers_mock.assert_called_once_with(
        instance_template=template_task,
        redefined_performer=None,
    )
    create_fields_mock.assert_called_once_with(template_task)
    create_fieldsets_mock.assert_called_once_with(template_task)
    create_conditions_mock.assert_called_once_with(template_task)
    create_checklists_mock.assert_called_once_with(template_task)
    create_raw_due_date_mock.assert_called_once_with(template_task)


def test_create_related__with_delay__ok(mocker):

    """
    With delay
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    template_task = template.tasks.get(number=1)
    delay_value = timedelta(seconds=30)
    template_task.delay = delay_value
    template_task.save(update_fields=['delay'])
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)

    # remove delays created by workflow fixture
    Delay.objects.filter(task=task).delete()
    create_raw_performers_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.TaskService.create_raw_performers_from_template',
    )
    create_fields_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.TaskService.create_fields_from_template',
    )
    create_fieldsets_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.TaskService.create_fieldsets_from_template',
    )
    create_conditions_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.TaskService.create_conditions_from_template',
    )
    create_checklists_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.TaskService.create_checklists_from_template',
    )
    create_raw_due_date_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.TaskService.create_raw_due_date_from_template',
    )
    service = TaskService(user=user, instance=task)

    # act
    service._create_related(
        instance_template=template_task,
    )

    # assert
    delay = Delay.objects.get(task=task)
    assert delay.duration == delay_value
    assert delay.workflow == workflow
    create_raw_performers_mock.assert_called_once_with(
        instance_template=template_task,
        redefined_performer=None,
    )
    create_fields_mock.assert_called_once_with(template_task)
    create_fieldsets_mock.assert_called_once_with(template_task)
    create_conditions_mock.assert_called_once_with(template_task)
    create_checklists_mock.assert_called_once_with(template_task)
    create_raw_due_date_mock.assert_called_once_with(template_task)


def test_set_due_date_directly__default__ok(mocker):

    """
    Default call
    """

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    partial_update_mock = mocker.patch(
        'src.processes.services.tasks.task'
        '.TaskService.partial_update',
    )
    send_notifications_mock = mocker.patch(
        'src.notifications.tasks.send_due_date_changed.delay',
    )
    due_date_changed_event_mock = mocker.patch(
        'src.processes.services.events.WorkflowEventService'
        '.due_date_changed_event',
    )
    service = TaskService(user=user, instance=task)

    # act
    service.set_due_date_directly()

    # assert
    partial_update_mock.assert_called_once_with(
        due_date=None,
        force_save=True,
    )
    send_notifications_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        author_id=user.id,
        task_id=task.id,
        account_id=task.account_id,
        logo_lg=user.account.logo_lg,
    )
    due_date_changed_event_mock.assert_called_once_with(
        task=task,
        user=user,
    )
