"""Schema and validation checks for field-value OpenAPI examples."""

import pytest
from django.test import override_settings
from drf_spectacular.generators import SchemaGenerator

from src.openapi.examples import (
    FIELD_VALUE_ERROR_EXAMPLE,
    TASK_COMPLETE_ALL_TYPES_EXAMPLE,
    WORKFLOW_RUN_ALL_TYPES_EXAMPLE,
)
from src.processes.enums import FieldType
from src.processes.models.workflows.fields import TaskField
from src.processes.services.tasks.exceptions import TaskFieldException
from src.processes.services.tasks.field import TaskFieldService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_user,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db

API_NAME_TO_TYPE = {
    'short-answer': FieldType.STRING,
    'details': FieldType.TEXT,
    'amount': FieldType.NUMBER,
    'due-date': FieldType.DATE,
    'website': FieldType.URL,
    'decision': FieldType.RADIO,
    'department': FieldType.DROPDOWN,
    'approvals': FieldType.CHECKBOX,
    'attachments': FieldType.FILE,
    'reviewer': FieldType.USER,
}

COMPLETE_TITLES = {
    'Minimal: one string field',
    'All field types',
    'Selection fields (radio, dropdown, checkbox)',
    'File field (upload first)',
    'User field (email or group name)',
    'Clearing optional fields',
}

RUN_TITLES = {
    'Minimal: one kickoff field',
    'All kickoff field types',
}


def _request_example_summaries(schema, path):
    content = (
        schema['paths'][path]['post']
        .get('requestBody', {})
        .get('content', {})
    )
    examples = content.get('application/json', {}).get('examples', {})
    return {ex.get('summary', key) for key, ex in examples.items()}


def _response_example_summaries(schema, path, status='400'):
    content = (
        schema['paths'][path]['post']
        .get('responses', {})
        .get(status, {})
        .get('content', {})
    )
    examples = content.get('application/json', {}).get('examples', {})
    return {ex.get('summary', key) for key, ex in examples.items()}


def test_schema__task_complete_and_run__shows_all_field_value_examples():

    # arrange
    # act
    schema = SchemaGenerator().get_schema(request=None, public=True)

    # assert
    assert _request_example_summaries(
        schema, '/v2/tasks/{id}/complete',
    ) == COMPLETE_TITLES
    assert _request_example_summaries(
        schema, '/templates/{id}/run',
    ) == RUN_TITLES
    assert 'Invalid field value' in _response_example_summaries(
        schema, '/v2/tasks/{id}/complete',
    )
    assert 'Invalid field value' in _response_example_summaries(
        schema, '/templates/{id}/run',
    )


@pytest.mark.parametrize(
    'api_name,raw_value',
    list(TASK_COMPLETE_ALL_TYPES_EXAMPLE.value['output'].items()),
)
@override_settings(FILE_SERVICE_HOST_PATH='app.example.com/files')
def test_all_field_types_example__passes_real_validator(
    api_name,
    raw_value,
    mocker,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    create_test_user(
        account=account,
        email='jane@example.com',
        is_account_owner=False,
    )
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    field_type = API_NAME_TO_TYPE[api_name]
    task_field = TaskField.objects.create(
        task=task,
        api_name=api_name,
        type=field_type,
        name=api_name,
        workflow=workflow,
        account=account,
        is_required=False,
    )
    if field_type in {
        FieldType.RADIO,
        FieldType.DROPDOWN,
        FieldType.CHECKBOX,
    }:
        if isinstance(raw_value, list):
            allowed = set(raw_value)
        else:
            allowed = {raw_value}
        mocker.patch(
            'src.processes.services.tasks.field.'
            'TaskFieldService._get_selections_values',
            return_value=allowed,
        )
    service = TaskFieldService(instance=task_field, user=user)

    # act
    service._get_valid_value(raw_value)

    # assert — no exception


def test_workflow_run_all_types_example__matches_task_output_values():

    # arrange
    task_output = TASK_COMPLETE_ALL_TYPES_EXAMPLE.value['output']
    kickoff = WORKFLOW_RUN_ALL_TYPES_EXAMPLE.value['kickoff']

    # act / assert
    assert kickoff == task_output


def test_field_value_error_example__matches_real_date_validation():

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name='due-date',
        type=FieldType.DATE,
        name='due-date',
        workflow=workflow,
        account=account,
        is_required=False,
    )
    service = TaskFieldService(instance=task_field, user=user)

    # act
    with pytest.raises(TaskFieldException) as ex:
        service._get_valid_value('2026-01-01')

    # assert
    assert (
        ex.value.message
        == FIELD_VALUE_ERROR_EXAMPLE.value['message']
    )
    assert (
        ex.value.api_name
        == FIELD_VALUE_ERROR_EXAMPLE.value['details']['api_name']
    )
