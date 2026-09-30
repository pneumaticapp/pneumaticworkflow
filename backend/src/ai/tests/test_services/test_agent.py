import pytest
from rest_framework.exceptions import ValidationError

from src.ai.services.agent import AIAgentService
from src.processes.messages.workflow import MSG_PW_0004
from src.processes.serializers.workflows.task import TaskCompleteSerializer
from src.processes.services.exceptions import (
    CompleteDelayedWorkflow,
    FieldsetServiceException,
    WorkflowActionServiceException,
)
from src.utils.validation import raise_validation_error


def _service() -> AIAgentService:
    return AIAgentService()


def test_convert_ex_to_markdown__workflow_exception__message():

    # arrange
    service = _service()
    ex = WorkflowActionServiceException(message='Resume the workflow.')

    # act
    result = service._convert_ex_to_markdown(ex)

    # assert
    assert result == '- Resume the workflow.'


def test_convert_ex_to_markdown__default_message__lazy_text():

    # arrange
    service = _service()
    ex = CompleteDelayedWorkflow()

    # act
    result = service._convert_ex_to_markdown(ex)

    # assert
    assert result == f'- {MSG_PW_0004}'


def test_convert_ex_to_markdown__fieldset_exception__message():

    # arrange
    service = _service()
    ex = FieldsetServiceException(
        message='The sum must equal "100".',
    )

    # act
    result = service._convert_ex_to_markdown(ex)

    # assert
    assert result == '- The sum must equal "100".'


def test_convert_ex_to_markdown__validation_by_api_name__field():

    # arrange
    service = _service()
    with pytest.raises(ValidationError) as caught:
        raise_validation_error(
            message='Value should be a string.',
            api_name='phone-1',
        )

    # act
    result = service._convert_ex_to_markdown(caught.value)

    # assert
    assert result == '- `phone-1`: Value should be a string.'


def test_convert_ex_to_markdown__validation_by_name__field():

    # arrange
    service = _service()
    with pytest.raises(ValidationError) as caught:
        raise_validation_error(
            message='Expected a dictionary of items.',
            name='output',
        )

    # act
    result = service._convert_ex_to_markdown(caught.value)

    # assert
    assert result == '- `output`: Expected a dictionary of items.'


def test_convert_ex_to_markdown__validation_common__no_field():

    # arrange
    service = _service()
    with pytest.raises(ValidationError) as caught:
        raise_validation_error(message='Invalid output.')

    # act
    result = service._convert_ex_to_markdown(caught.value)

    # assert
    assert result == '- Invalid output.'


def test_convert_ex_to_markdown__validation_field_map__lines():

    # arrange
    service = _service()
    ex = ValidationError({
        'phone-1': ['Value should be a string.'],
        'total-1': ['The value must be a number.'],
    })

    # act
    result = service._convert_ex_to_markdown(ex)

    # assert
    assert result == (
        '- `phone-1`: Value should be a string.\n'
        '- `total-1`: The value must be a number.'
    )


def test_convert_ex_to_markdown__serializer_output__field_name():

    # arrange
    service = _service()
    serializer = TaskCompleteSerializer(data={'output': ['not-a-dict']})

    # act
    with pytest.raises(ValidationError) as caught:
        serializer.is_valid(raise_exception=True)
    result = service._convert_ex_to_markdown(caught.value)

    # assert
    assert result == (
        '- `output`: Expected a dictionary of items '
        'but got type "list".'
    )


def test_convert_ex_to_markdown__empty_validation__fallback():

    # arrange
    service = _service()
    ex = ValidationError({})

    # act
    result = service._convert_ex_to_markdown(ex)

    # assert
    assert result == '- Validation failed.'
