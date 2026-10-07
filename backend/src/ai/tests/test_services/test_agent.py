import pytest
from rest_framework.exceptions import ValidationError

from src.ai.enums import AIAgentActionType
from src.ai.exceptions import AIAgentAttemptsExceededException
from src.ai.messages import MSG_AI_0009, MSG_AI_0010
from src.ai.services.agent import AIAgentService
from src.processes.messages.workflow import MSG_PW_0004
from src.processes.serializers.workflows.task import TaskCompleteSerializer
from src.processes.services.exceptions import (
    CompleteDelayedWorkflow,
    FieldsetServiceException,
    WorkflowActionServiceException,
)
from src.utils.validation import raise_validation_error


REPORT_URL = 'https://storage.pneumatic.app/report.md'


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


def test_get_report_text__two_attempts__markdown():

    # arrange
    service = _service()
    errors_stack = [
        (
            {'phone-1': 'call me', 'pizzas-1': ['Pepperoni', 'Margherita']},
            '- `phone-1`: Value should be a string.',
        ),
        (
            {'phone-1': '+1 202 555 0147', 'pizzas-1': []},
            '- Resume the workflow.',
        ),
    ]

    # act
    result = service._get_report_text(errors_stack=errors_stack)

    # assert
    assert result == (
        '# Complete task attempts\n'
        '\n'
        '## Attempt № 1\n'
        '\n'
        '### Output fields\n'
        '\n'
        '- `phone-1`: call me\n'
        '- `pizzas-1`: Pepperoni, Margherita\n'
        '\n'
        '### Validation error\n'
        '\n'
        '- `phone-1`: Value should be a string.\n'
        '\n'
        '-------\n'
        '\n'
        '## Attempt № 2\n'
        '\n'
        '### Output fields\n'
        '\n'
        '- `phone-1`: +1 202 555 0147\n'
        '- `pizzas-1`: \n'
        '\n'
        '### Validation error\n'
        '\n'
        '- Resume the workflow.'
    )


def test_raise_attempt_error__report_uploaded__comment_and_action(mocker):

    # arrange
    service = AIAgentService(instance=mocker.Mock())
    task = mocker.Mock()
    errors_stack = [({'phone-1': 'call me'}, '- Invalid output.')]
    report_file_mock = mocker.patch.object(
        AIAgentService,
        '_create_report_file',
        return_value=REPORT_URL,
    )
    comment_mock = mocker.patch.object(AIAgentService, '_create_comment')
    action_mock = mocker.patch(
        'src.ai.services.agent.AIAgentAction.objects.create',
    )
    message = MSG_AI_0010(attempts=1)

    # act
    with pytest.raises(AIAgentAttemptsExceededException) as caught:
        service._raise_attempt_error(task=task, errors_stack=errors_stack)

    # assert
    report_file_mock.assert_called_once_with(
        text=service._get_report_text(errors_stack=errors_stack),
        filename='report.md',
    )
    comment_mock.assert_called_once_with(
        task=task,
        text=str(
            MSG_AI_0009(
                attempts=1,
                report=f'[report.md]({REPORT_URL})',
            ),
        ),
    )
    action_mock.assert_called_once_with(
        account_id=service.instance.account_id,
        agent_id=service.instance.id,
        task_id=task.id,
        action=AIAgentActionType.ERROR,
        text=f'{message}\n{REPORT_URL}',
    )
    assert caught.value.message == message
