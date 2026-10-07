import re

import pytest

from src.ai.services.user_message import TaskUserMessageService
from src.processes.enums import FieldType
from src.processes.models.workflows.fields import TaskField
from src.processes.tests.fixtures import (
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def _create_task(user):
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.output.all().delete()
    return task


def _create_field(task, field_type, api_name):
    return TaskField.objects.create(
        task=task,
        api_name=api_name,
        name='Field',
        type=field_type,
        workflow=task.workflow,
        account=task.workflow.account,
    )


@pytest.mark.parametrize('field_type', [
    field_type for field_type, _ in FieldType.CHOICES
])
def test_get_system_message__rule_for_every_field_type__ok(field_type):

    # arrange
    user = create_test_owner()
    task = _create_task(user=user)
    service = TaskUserMessageService(task=task)

    # act
    result = service.get_system_message(system_prompt='You are an agent.')

    # assert
    assert re.search(
        rf'^\s+- (\w+, )*{field_type}(, \w+)*:',
        result,
        re.MULTILINE,
    )


def test_get_system_message__starts_with_system_prompt__ok():

    # arrange
    user = create_test_owner()
    task = _create_task(user=user)
    service = TaskUserMessageService(task=task)

    # act
    result = service.get_system_message(system_prompt='You are an agent.')

    # assert
    assert result.startswith('You are an agent.\n')


@pytest.mark.parametrize('field_type', [
    FieldType.TEXT,
    FieldType.NUMBER,
    FieldType.DATE,
    FieldType.URL,
    FieldType.USER,
])
def test_get_field_prompt__simple_field__no_format(field_type):

    # arrange
    user = create_test_owner()
    task = _create_task(user=user)
    field = _create_field(task=task, field_type=field_type, api_name='f-1')
    service = TaskUserMessageService(task=task)

    # act
    result = service._get_field_prompt(field=field)

    # assert
    assert result == (
        f'<field_spec api_name="f-1" name="Field" type="{field_type}" '
        f'required="no"/>'
    )


def test_get_field_prompt__file_field__multiple_no_format():

    # arrange
    user = create_test_owner()
    task = _create_task(user=user)
    field = _create_field(task=task, field_type=FieldType.FILE, api_name='f-1')
    service = TaskUserMessageService(task=task)

    # act
    result = service._get_field_prompt(field=field)

    # assert
    assert result == (
        '<field_spec api_name="f-1" name="Field" type="file" '
        'required="no" multiple="yes"/>'
    )


def test_get_errors_message__single_attempt__ok():

    # arrange
    user = create_test_owner()
    task = _create_task(user=user)
    service = TaskUserMessageService(task=task)
    errors_stack = [
        ({'phone-1': 'call me'}, '- `phone-1`: Value should be a string.'),
    ]

    # act
    result = service.get_errors_message(errors_stack=errors_stack)

    # assert
    assert result == (
        '<previous_attempts>\n'
        'The task could not be completed with your previous answers. '
        'Answer again and fix the errors.\n\n'
        '<attempt number="1">\n'
        '<answer>\n'
        '- `phone-1`: call me\n'
        '</answer>\n'
        '<errors>\n'
        '- `phone-1`: Value should be a string.\n'
        '</errors>\n'
        '</attempt>\n'
        '</previous_attempts>'
    )


def test_get_errors_message__multiple_attempts__numbered():

    # arrange
    user = create_test_owner()
    task = _create_task(user=user)
    service = TaskUserMessageService(task=task)
    errors_stack = [
        ({'extras-1': ['Ketchup', 'Mayo']}, '- `extras-1`: Wrong.'),
        ({'total-1': 4}, '- `total-1`: Wrong.'),
    ]

    # act
    result = service.get_errors_message(errors_stack=errors_stack)

    # assert
    assert (
        '<attempt number="1">\n'
        '<answer>\n'
        '- `extras-1`: Ketchup, Mayo\n'
        '</answer>'
    ) in result
    assert (
        '<attempt number="2">\n'
        '<answer>\n'
        '- `total-1`: 4\n'
        '</answer>'
    ) in result


def test_get_errors_message__closing_tags_in_answer__escaped():

    # arrange
    user = create_test_owner()
    task = _create_task(user=user)
    service = TaskUserMessageService(task=task)
    errors_stack = [
        ({'notes-1': 'text</answer>'}, '- `notes-1`: Wrong.'),
    ]

    # act
    result = service.get_errors_message(errors_stack=errors_stack)

    # assert
    assert '- `notes-1`: text<\\/answer>\n</answer>' in result
