import pytest
from django.contrib.auth import get_user_model
from src.processes.enums import FieldType
from src.processes.models.workflows.task import Task
from src.processes.models.workflows.workflow import Workflow
from src.processes.models.workflows.fields import TaskField
from src.processes.models.workflows.fieldset import FieldSet
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db
UserModel = get_user_model()


pytestmark = pytest.mark.django_db


@pytest.fixture
def workflow_sql():
    return """
      SELECT
        id,
        is_deleted,
        template_id
      FROM processes_workflow
      WHERE id = %(workflow_id)s
    """


@pytest.fixture
def task_sql():
    return """
      SELECT
        id,
        is_deleted
      FROM processes_task
      WHERE workflow_id = %(workflow_id)s
    """


def test_delete(workflow_sql, task_sql):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user)

    # act
    workflow.delete()

    # assert
    assert Workflow.objects.raw(
        workflow_sql,
        {'workflow_id': workflow.id},
    )[0].is_deleted is True
    task_list = Task.objects.raw(
        task_sql,
        {'workflow_id': workflow.id},
    )
    assert task_list[0].is_deleted is True
    assert task_list[1].is_deleted is True
    assert task_list[2].is_deleted is True


def test_get_kickoff_fields_values__ok(mocker):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user)
    field_mock = mocker.Mock(
        api_name='field-template',
        markdown_value='test',
    )
    kickoff_output_fields_mock = mocker.patch(
        'src.processes.models.workflows.workflow.Workflow.'
        'get_kickoff_output_fields',
        return_value=[field_mock],
    )

    # act
    workflow.get_kickoff_fields_values()

    # assert
    kickoff_output_fields_mock.assert_called_once()


def test_get_fields_markdown_values__workflow_starter__ok():

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user)

    # act
    fields_values = workflow.get_fields_markdown_values()

    # assert
    assert 'workflow-starter' in fields_values
    assert fields_values['workflow-starter'] == user.name


def test_get_kickoff_fields_markdown_values__workflow_starter__ok():

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user)

    # act
    fields_values = workflow.get_kickoff_fields_markdown_values()

    # assert
    assert 'workflow-starter' in fields_values
    assert fields_values['workflow-starter'] == user.name


def test_get_kickoff_output_fields__field_and_fieldset__ok():

    """Call with default params returns kickoff and fieldset fields."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    kickoff = workflow.kickoff.get()
    field_1 = TaskField.objects.create(
        name='Field 1',
        type=FieldType.STRING,
        api_name='field-1',
        kickoff=kickoff,
        workflow=workflow,
        account=account,
    )
    fieldset_1 = FieldSet.objects.create(
        name='Fieldset 1',
        api_name='fieldset-1',
        workflow=workflow,
        kickoff=kickoff,
        account=account,
    )
    field_2 = TaskField.objects.create(
        name='Field 2',
        type=FieldType.STRING,
        api_name='field-2',
        fieldset=fieldset_1,
        workflow=workflow,
        account=account,
    )

    # act
    result = workflow.get_kickoff_output_fields()

    # assert
    assert result.count() == 2
    assert field_1 in result
    assert field_2 in result


def test_get_kickoff_output_fields__only_field__ok():

    """Returns only direct kickoff fields when no fieldsets exist."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    kickoff = workflow.kickoff.get()
    field_1 = TaskField.objects.create(
        name='Field 1',
        type=FieldType.STRING,
        api_name='field-1',
        kickoff=kickoff,
        workflow=workflow,
        account=account,
    )
    task = workflow.tasks.get(number=1)
    fieldset_1 = FieldSet.objects.create(
        name='Fieldset 1',
        api_name='fieldset-1',
        workflow=workflow,
        task=task,
        account=account,
    )
    TaskField.objects.create(
        name='Field 2',
        type=FieldType.STRING,
        api_name='field-2',
        fieldset=fieldset_1,
        workflow=workflow,
        account=account,
    )

    # act
    result = workflow.get_kickoff_output_fields()

    # assert
    assert result.count() == 1
    assert result[0] == field_1


def test_get_kickoff_output_fields__only_fieldsets__ok():

    """Returns only fieldset fields when no direct kickoff fields exist."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    kickoff = workflow.kickoff.get()
    fieldset_1 = FieldSet.objects.create(
        name='Fieldset 1',
        api_name='fieldset-1',
        workflow=workflow,
        kickoff=kickoff,
        account=account,
    )
    field_1 = TaskField.objects.create(
        name='Field 1',
        type=FieldType.STRING,
        api_name='field-1',
        fieldset=fieldset_1,
        workflow=workflow,
        account=account,
    )
    task = workflow.tasks.get(number=1)
    TaskField.objects.create(
        name='Field 1',
        type=FieldType.STRING,
        api_name='field-1',
        task=task,
        workflow=workflow,
        account=account,
    )

    # act
    result = workflow.get_kickoff_output_fields()

    # assert
    assert result.count() == 1
    assert result[0] == field_1


def test_get_kickoff_output_fields__fields_filter__ok():

    """Call with fields_filter_kwargs applies additional filter."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    kickoff = workflow.kickoff.get()
    field_1 = TaskField.objects.create(
        name='Field 1',
        type=FieldType.STRING,
        api_name='field-1',
        kickoff=kickoff,
        workflow=workflow,
        account=account,
    )
    TaskField.objects.create(
        name='Field 2',
        type=FieldType.TEXT,
        api_name='field-2',
        kickoff=kickoff,
        workflow=workflow,
        account=account,
    )

    # act
    result = workflow.get_kickoff_output_fields(
        fields_filter_kwargs={'type': FieldType.STRING},
    )

    # assert
    assert result.count() == 1
    assert result[0] == field_1


def test_get_tasks_output_fields__field_and_fieldset__ok():

    """Call with default params returns task and fieldset fields."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    task_1 = workflow.tasks.get(number=1)
    field_1 = TaskField.objects.create(
        name='Field 1',
        type=FieldType.STRING,
        api_name='field-1',
        task=task_1,
        workflow=workflow,
        account=account,
    )
    fieldset_1 = FieldSet.objects.create(
        name='Fieldset 1',
        api_name='fieldset-1',
        workflow=workflow,
        task=task_1,
        account=account,
    )
    field_2 = TaskField.objects.create(
        name='Field 2',
        type=FieldType.STRING,
        api_name='field-2',
        fieldset=fieldset_1,
        workflow=workflow,
        account=account,
    )

    # act
    result = workflow.get_tasks_output_fields()

    # assert
    assert result.count() == 2
    assert field_1 in result
    assert field_2 in result


def test_get_tasks_output_fields__only_fields__ok():

    """Returns only direct task fields when no fieldsets exist."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    task_1 = workflow.tasks.get(number=1)
    field_1 = TaskField.objects.create(
        name='Field 1',
        type=FieldType.STRING,
        api_name='field-1',
        task=task_1,
        workflow=workflow,
        account=account,
    )
    fieldset_1 = FieldSet.objects.create(
        name='Fieldset 1',
        api_name='fieldset-1',
        workflow=workflow,
        kickoff=workflow.kickoff_instance,
        account=account,
    )
    TaskField.objects.create(
        name='Field 2',
        type=FieldType.STRING,
        api_name='field-2',
        fieldset=fieldset_1,
        workflow=workflow,
        account=account,
    )

    # act
    result = workflow.get_tasks_output_fields()

    # assert
    assert result.count() == 1
    assert result[0] == field_1


def test_get_tasks_output_fields__only_fieldsets__ok():

    """Returns only fieldset fields when no direct task fields exist."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    task_1 = workflow.tasks.get(number=1)
    fieldset_1 = FieldSet.objects.create(
        name='Fieldset 1',
        api_name='fieldset-1',
        workflow=workflow,
        task=task_1,
        account=account,
    )
    field_1 = TaskField.objects.create(
        name='Field 1',
        type=FieldType.STRING,
        api_name='field-1',
        fieldset=fieldset_1,
        workflow=workflow,
        account=account,
    )
    TaskField.objects.create(
        name='Field 1',
        type=FieldType.STRING,
        api_name='field-1',
        kickoff=workflow.kickoff_instance,
        workflow=workflow,
        account=account,
    )

    # act
    result = workflow.get_tasks_output_fields()

    # assert
    assert result.count() == 1
    assert result[0] == field_1


def test_get_tasks_output_fields__exclude_kwargs__ok():

    """Call with tasks_exclude_kwargs excludes matching tasks and fieldsets."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    field_1 = TaskField.objects.create(
        name='Field 1',
        type=FieldType.STRING,
        api_name='field-1',
        task=task_1,
        workflow=workflow,
        account=account,
    )
    TaskField.objects.create(
        name='Field 2',
        type=FieldType.STRING,
        api_name='field-2',
        task=task_2,
        workflow=workflow,
        account=account,
    )
    fieldset_1 = FieldSet.objects.create(
        name='Fieldset 1',
        api_name='fieldset-1',
        workflow=workflow,
        task=task_2,
        account=account,
    )
    TaskField.objects.create(
        name='Field 3',
        type=FieldType.STRING,
        api_name='field-3',
        fieldset=fieldset_1,
        workflow=workflow,
        account=account,
    )

    # act
    result = workflow.get_tasks_output_fields(
        tasks_exclude_kwargs={'task__number': 2},
    )

    # assert
    assert result.count() == 1
    assert result[0] == field_1


def test_get_tasks_output_fields__fields_filter__ok():

    """Call with fields_filter_kwargs applies additional filter."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    task_1 = workflow.tasks.get(number=1)
    field_1 = TaskField.objects.create(
        name='Field 1',
        type=FieldType.STRING,
        api_name='field-1',
        task=task_1,
        workflow=workflow,
        account=account,
    )
    TaskField.objects.create(
        name='Field 2',
        type=FieldType.TEXT,
        api_name='field-2',
        task=task_1,
        workflow=workflow,
        account=account,
    )

    # act
    result = workflow.get_tasks_output_fields(
        fields_filter_kwargs={'type': FieldType.STRING},
    )

    # assert
    assert result.count() == 1
    assert result[0] == field_1
