# ruff: noqa: UP031
import pytest
from datetime import timedelta
from django.utils import timezone
from src.processes.services.tasks.task import TaskService
from src.processes.models import FieldTemplate
from src.processes.tests.fixtures import (
    create_test_owner,
    create_test_template,
    create_test_account,
    create_test_workflow,
)
from src.processes.enums import FieldType
from src.authentication.enums import AuthTokenType
from src.processes.services.workflows.workflow import WorkflowService


pytestmark = pytest.mark.django_db


def test_create_instance__only_required_fields__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow_name = 'New workflow'
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
        finalizable=True,
    )
    create_workflow_name_mock = mocker.patch(
        'src.processes.services.workflows.workflow.'
        'WorkflowService._create_workflow_name',
        return_value=workflow_name,
    )
    contains_fields_vars_mock = mocker.patch(
        'src.processes.services.workflows.workflow.'
        'contains_fields_vars',
        return_value=False,
    )
    string_abbreviation_mock = mocker.patch(
        'src.processes.services.workflows.workflow.'
        'string_abbreviation',
    )
    service = WorkflowService(
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    workflow = service._create_instance(
        instance_template=template,
        workflow_starter=owner,
    )

    # assert
    create_workflow_name_mock.assert_called_once_with(
        workflow_starter=owner,
        template=template,
        user_provided_name=None,
    )
    contains_fields_vars_mock.assert_called_once_with(workflow_name)
    string_abbreviation_mock.assert_not_called()
    assert workflow.template == template
    assert workflow.name == workflow_name
    assert workflow.name_template == workflow_name
    assert workflow.description == template.description
    assert workflow.account == account
    assert workflow.finalizable is True
    assert workflow.status_updated
    assert workflow.version == template.version
    assert workflow.workflow_starter == owner
    assert workflow.workflow_starter == owner
    assert workflow.is_external is False
    assert workflow.is_external is False
    assert workflow.is_urgent is False
    assert workflow.due_date is None
    assert workflow.ancestor_task is None
    kickoff = workflow.kickoff_instance
    assert kickoff.account == account


def test_create_instance__all_fields__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow_name = 'New workflow'
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
        finalizable=True,
    )
    create_workflow_name_mock = mocker.patch(
        'src.processes.services.workflows.workflow.'
        'WorkflowService._create_workflow_name',
        return_value=workflow_name,
    )
    contains_fields_vars_mock = mocker.patch(
        'src.processes.services.workflows.workflow.'
        'contains_fields_vars',
        return_value=False,
    )
    string_abbreviation_mock = mocker.patch(
        'src.processes.services.workflows.workflow.'
        'string_abbreviation',
    )
    service = WorkflowService(
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    due_date = timezone.now() + timedelta(hours=1)
    is_external = False
    is_urgent = True
    ancestor_task = None

    # act
    workflow = service._create_instance(
        instance_template=template,
        workflow_starter=owner,
        is_external=is_external,
        is_urgent=is_urgent,
        due_date=due_date,
        ancestor_task=ancestor_task,
    )

    # assert
    create_workflow_name_mock.assert_called_once_with(
        workflow_starter=owner,
        template=template,
        user_provided_name=None,
    )
    contains_fields_vars_mock.assert_called_once_with(workflow_name)
    string_abbreviation_mock.assert_not_called()
    assert workflow.template == template
    assert workflow.name == workflow_name
    assert workflow.name_template == workflow_name
    assert workflow.description == template.description
    assert workflow.account == account
    assert workflow.finalizable is True
    assert workflow.status_updated
    assert workflow.version == template.version
    assert workflow.workflow_starter == owner
    assert workflow.is_external == is_external
    assert workflow.is_urgent == is_urgent
    assert workflow.due_date == due_date
    assert workflow.ancestor_task == ancestor_task


def test_create_instance__external_workflow__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow_name = 'New workflow'
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
        finalizable=True,
    )
    create_workflow_name_mock = mocker.patch(
        'src.processes.services.workflows.workflow.'
        'WorkflowService._create_workflow_name',
        return_value=workflow_name,
    )
    contains_fields_vars_mock = mocker.patch(
        'src.processes.services.workflows.workflow.'
        'contains_fields_vars',
        return_value=False,
    )
    string_abbreviation_mock = mocker.patch(
        'src.processes.services.workflows.workflow.'
        'string_abbreviation',
    )
    service = WorkflowService(
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    workflow = service._create_instance(
        instance_template=template,
        workflow_starter=None,
        is_external=True,
    )

    # assert
    create_workflow_name_mock.assert_called_once_with(
        workflow_starter=None,
        template=template,
        user_provided_name=None,
    )
    contains_fields_vars_mock.assert_called_once_with(workflow_name)
    string_abbreviation_mock.assert_not_called()
    assert workflow.is_external is True
    assert workflow.workflow_starter is None


def test_create_instance__insert_kickoff_fields__ok(mocker):

    # arrange
    owner = create_test_owner()
    field_api_name = 'field-123'
    field_value = 1729624335
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    workflow_name = f'Feedback from {field_api_name}'
    create_workflow_name_mock = mocker.patch(
        'src.processes.services.workflows.workflow.'
        'WorkflowService._create_workflow_name',
        return_value=workflow_name,
    )
    contains_fields_vars_mock = mocker.patch(
        'src.processes.services.workflows.workflow.'
        'contains_fields_vars',
        return_value=True,
    )
    string_abbreviation_mock = mocker.patch(
        'src.processes.services.workflows.workflow.'
        'string_abbreviation',
    )
    field_template = FieldTemplate.objects.create(
        name='Date',
        type=FieldType.DATE,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
        api_name=field_api_name,
    )
    service = WorkflowService(
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    workflow = service._create_instance(
        instance_template=template,
        kickoff_fields_data={field_api_name: field_value},
        workflow_starter=owner,
    )

    # assert
    create_workflow_name_mock.assert_called_once_with(
        workflow_starter=owner,
        template=template,
        user_provided_name=None,
    )
    contains_fields_vars_mock.assert_called_once_with(workflow_name)
    string_abbreviation_mock.assert_not_called()
    formatted_date = 'Oct 22, 2024, 07:12PM'
    assert workflow.name == f'Feedback from {formatted_date}'
    assert workflow.name_template == 'Feedback from {{%s}}' % field_api_name
    kickoff = workflow.kickoff_instance
    assert kickoff.output.count() == 1
    assert kickoff.output.get(
        name=field_template.name,
        type=field_template.type,
        is_required=field_template.is_required,
        workflow=workflow,
        api_name=field_api_name,
        value=str(field_value),
    )


def test_create_related__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    service = WorkflowService(
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=workflow,
    )
    update_owners_mock = mocker.patch(
        'src.processes.services.workflows.workflow.'
        'WorkflowService.update_owners',
    )
    task_service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None,
    )
    task_service_create_mock = mocker.patch(
        'src.processes.services.workflows.workflow.'
        'TaskService.create',
    )

    # act
    service._create_related(
        instance_template=template,
        redefined_performer=None,
    )

    # assert
    task_service_init_mock.assert_called_once_with(user=owner)
    task_service_create_mock.assert_called_once_with(
        instance_template=template.tasks.get(number=1),
        workflow=workflow,
        redefined_performer=None,
    )
    update_owners_mock.assert_called_once()
