import string

import pytest
from rest_framework.exceptions import ValidationError

from src.accounts.enums import (
    NotificationStatus,
    NotificationType,
    UserStatus,
)
from src.accounts.models import Notification
from src.accounts.services.user import UserService
from src.ai.enums import AIAgentActionType
from src.ai.exceptions import (
    AIAgentAttemptsExceededException,
    AIAgentNameNotUniqueException,
)
from src.ai.messages import MSG_AI_0004, MSG_AI_0009, MSG_AI_0010
from src.ai.models import AIAgent, AIAgentAction
from src.ai.services.agent import AIAgentService
from src.ai.services.provider import AIProviderService
from src.ai.services.response import TaskResponseService
from src.ai.services.user_message import TaskUserMessageService
from src.ai.tests.fixtures import create_test_agent, create_test_provider
from src.authentication.enums import AuthTokenType
from src.processes.messages.workflow import MSG_PW_0004
from src.processes.serializers.workflows.task import TaskCompleteSerializer
from src.processes.services.events import CommentService
from src.processes.services.exceptions import (
    CompleteDelayedWorkflow,
    FieldsetServiceException,
    WorkflowActionServiceException,
)
from src.processes.services.workflow_action import WorkflowActionService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
    create_test_workflow,
)
from src.storage.enums import AccessType, SourceType
from src.storage.services import FileServiceClient

pytestmark = pytest.mark.django_db


def test_get_agent_email__unique__ok(mocker):

    """ Unique email """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account, email='owner@pizza.com')
    salt = 'Hq3kZr9TbVn2Lm7sXy1p'
    get_random_string_mock = mocker.patch(
        'src.ai.services.agent.get_random_string',
        return_value=salt,
    )
    service = AIAgentService(user=owner)

    # act
    result = service._get_agent_email()

    # assert
    assert result == 'ai-agent-Hq3kZr9TbVn2Lm7sXy1p@pizza.com'
    get_random_string_mock.assert_called_once_with(
        length=20,
        allowed_chars=string.ascii_letters + string.digits,
    )


def test_get_agent_email__taken_by_active_user__regenerate(mocker):

    """ Email taken by an active user """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account, email='owner@pizza.com')
    create_test_admin(account=account, email='ai-agent-salt1@pizza.com')
    get_random_string_mock = mocker.patch(
        'src.ai.services.agent.get_random_string',
        side_effect=['salt1', 'salt2'],
    )
    service = AIAgentService(user=owner)

    # act
    result = service._get_agent_email()

    # assert
    assert result == 'ai-agent-salt2@pizza.com'
    assert get_random_string_mock.call_count == 2
    get_random_string_mock.assert_has_calls(
        [
            mocker.call(
                length=20,
                allowed_chars=string.ascii_letters + string.digits,
            ),
            mocker.call(
                length=20,
                allowed_chars=string.ascii_letters + string.digits,
            ),
        ],
        any_order=True,
    )


def test_get_agent_email__taken_by_inactive_user__regenerate(mocker):

    """ Email taken by an inactive user """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account, email='owner@pizza.com')
    create_test_admin(
        account=account,
        email='ai-agent-salt1@pizza.com',
        status=UserStatus.INACTIVE,
    )
    get_random_string_mock = mocker.patch(
        'src.ai.services.agent.get_random_string',
        side_effect=['salt1', 'salt2'],
    )
    service = AIAgentService(user=owner)

    # act
    result = service._get_agent_email()

    # assert
    assert result == 'ai-agent-salt2@pizza.com'
    assert get_random_string_mock.call_count == 2
    get_random_string_mock.assert_has_calls(
        [
            mocker.call(
                length=20,
                allowed_chars=string.ascii_letters + string.digits,
            ),
            mocker.call(
                length=20,
                allowed_chars=string.ascii_letters + string.digits,
            ),
        ],
        any_order=True,
    )


def test_get_fields_values__default_errors_stack__ok(mocker):

    """ Default errors stack """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = create_test_agent(account=account)
    user_message = '<task_name>Take the order</task_name>'
    system_message = 'You are helpful.'
    raw_response = '<field api_name="phone-1">+1 202 555 0147</field>'
    fields_values = {'phone-1': '+1 202 555 0147'}
    task_user_message_service_init_mock = mocker.patch.object(
        TaskUserMessageService,
        attribute='__init__',
        return_value=None,
    )
    get_user_message_mock = mocker.patch(
        'src.ai.services.agent.TaskUserMessageService.get_user_message',
        return_value=user_message,
    )
    get_system_message_mock = mocker.patch(
        'src.ai.services.agent.TaskUserMessageService.get_system_message',
        return_value=system_message,
    )
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    get_completion_mock = mocker.patch(
        'src.ai.services.agent.AIProviderService.get_completion',
        return_value=raw_response,
    )
    task_response_service_init_mock = mocker.patch.object(
        TaskResponseService,
        attribute='__init__',
        return_value=None,
    )
    get_fields_values_mock = mocker.patch(
        'src.ai.services.agent.TaskResponseService.get_fields_values',
        return_value=fields_values,
    )
    service = AIAgentService(user=agent.user, instance=agent)

    # act
    result = service._get_fields_values(task=task)

    # assert
    assert result == fields_values
    request_action = AIAgentAction.objects.get(
        action=AIAgentActionType.AI_REQUEST,
    )
    assert request_action.account_id == account.id
    assert request_action.agent_id == agent.id
    assert request_action.task_id == task.id
    assert request_action.text == user_message
    response_action = AIAgentAction.objects.get(
        action=AIAgentActionType.AI_RESPONSE,
    )
    assert response_action.account_id == account.id
    assert response_action.agent_id == agent.id
    assert response_action.task_id == task.id
    assert response_action.text == raw_response
    task_user_message_service_init_mock.assert_called_once_with(task=task)
    get_user_message_mock.assert_called_once_with()
    get_system_message_mock.assert_called_once_with(
        system_prompt=agent.system_prompt,
    )
    ai_provider_service_init_mock.assert_called_once_with(
        user=agent.user,
        instance=agent.provider,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    get_completion_mock.assert_called_once_with(
        system_message=system_message,
        user_message=user_message,
        model=agent.model,
        agent=agent,
        task=task,
    )
    task_response_service_init_mock.assert_called_once_with(
        task=task,
        text=raw_response,
        user=agent.user,
    )
    get_fields_values_mock.assert_called_once_with()


def test_get_fields_values__errors_stack_passed__ok(mocker):

    """ Errors stack passed """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = create_test_agent(account=account)
    errors_stack = [
        ({'phone-1': 'call me'}, '- `phone-1`: Value should be a string.'),
    ]
    user_message = '<task_name>Take the order</task_name>'
    system_message = 'You are helpful.'
    raw_response = '<field api_name="phone-1">+1 202 555 0147</field>'
    fields_values = {'phone-1': '+1 202 555 0147'}
    task_user_message_service_init_mock = mocker.patch.object(
        TaskUserMessageService,
        attribute='__init__',
        return_value=None,
    )
    get_user_message_mock = mocker.patch(
        'src.ai.services.agent.TaskUserMessageService.get_user_message',
        return_value=user_message,
    )
    get_system_message_mock = mocker.patch(
        'src.ai.services.agent.TaskUserMessageService.get_system_message',
        return_value=system_message,
    )
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    get_completion_mock = mocker.patch(
        'src.ai.services.agent.AIProviderService.get_completion',
        return_value=raw_response,
    )
    task_response_service_init_mock = mocker.patch.object(
        TaskResponseService,
        attribute='__init__',
        return_value=None,
    )
    get_fields_values_mock = mocker.patch(
        'src.ai.services.agent.TaskResponseService.get_fields_values',
        return_value=fields_values,
    )
    service = AIAgentService(user=agent.user, instance=agent)

    # act
    result = service._get_fields_values(
        task=task,
        errors_stack=errors_stack,
    )

    # assert
    assert result == fields_values
    request_action = AIAgentAction.objects.get(
        action=AIAgentActionType.AI_REQUEST,
    )
    assert request_action.text == user_message
    response_action = AIAgentAction.objects.get(
        action=AIAgentActionType.AI_RESPONSE,
    )
    assert response_action.text == raw_response
    task_user_message_service_init_mock.assert_called_once_with(task=task)
    get_user_message_mock.assert_called_once_with()
    get_system_message_mock.assert_called_once_with(
        system_prompt=agent.system_prompt,
    )
    ai_provider_service_init_mock.assert_called_once_with(
        user=agent.user,
        instance=agent.provider,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    get_completion_mock.assert_called_once_with(
        system_message=system_message,
        user_message=user_message,
        model=agent.model,
        agent=agent,
        task=task,
    )
    task_response_service_init_mock.assert_called_once_with(
        task=task,
        text=raw_response,
        user=agent.user,
    )
    get_fields_values_mock.assert_called_once_with()


def test_complete_task__valid_fields_values__ok(mocker):

    """ Valid fields values """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = create_test_agent(account=account)
    fields_values = {'phone-1': '+1 202 555 0147'}
    task_complete_serializer_init_mock = mocker.patch.object(
        TaskCompleteSerializer,
        attribute='__init__',
        return_value=None,
    )
    is_valid_mock = mocker.patch(
        'src.ai.services.agent.TaskCompleteSerializer.is_valid',
        return_value=True,
    )
    workflow_action_service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    complete_task_for_user_mock = mocker.patch(
        'src.ai.services.agent.WorkflowActionService.complete_task_for_user',
    )
    check_delay_workflow_mock = mocker.patch(
        'src.ai.services.agent.WorkflowActionService.check_delay_workflow',
    )
    service = AIAgentService(user=agent.user, instance=agent)

    # act
    service._complete_task(task=task, fields_values=fields_values)

    # assert
    task_complete_serializer_init_mock.assert_called_once_with(
        data=fields_values,
    )
    is_valid_mock.assert_called_once_with(raise_exception=True)
    workflow_action_service_init_mock.assert_called_once_with(
        workflow=workflow,
        user=agent.user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    complete_task_for_user_mock.assert_called_once_with(
        task=task,
        fields_values=fields_values,
    )
    check_delay_workflow_mock.assert_called_once_with()


def test_convert_ex_to_markdown__service_exception__ok():

    """ Service exception """

    # arrange
    ex = CompleteDelayedWorkflow()
    service = AIAgentService()

    # act
    result = service._convert_ex_to_markdown(ex=ex)

    # assert
    assert result == f'- {MSG_PW_0004}'


def test_convert_ex_to_markdown__api_name__ok():

    """ Validation error with api_name """

    # arrange
    ex = ValidationError(
        detail={
            'code': 'validation_error',
            'message': 'Value should be a string.',
            'details': {
                'reason': 'Value should be a string.',
                'api_name': 'phone-1',
            },
        },
    )
    service = AIAgentService()

    # act
    result = service._convert_ex_to_markdown(ex=ex)

    # assert
    assert result == '- `phone-1`: Value should be a string.'


def test_convert_ex_to_markdown__name__ok():

    """ Validation error with name """

    # arrange
    ex = ValidationError(
        detail={
            'code': 'validation_error',
            'message': 'Expected a dictionary of items.',
            'details': {
                'reason': 'Expected a dictionary of items.',
                'name': 'output',
            },
        },
    )
    service = AIAgentService()

    # act
    result = service._convert_ex_to_markdown(ex=ex)

    # assert
    assert result == '- `output`: Expected a dictionary of items.'


def test_convert_ex_to_markdown__name_and_api_name__use_name():

    """ Validation error with name and api_name """

    # arrange
    ex = ValidationError(
        detail={
            'code': 'validation_error',
            'message': 'Value should be a string.',
            'details': {
                'reason': 'Value should be a string.',
                'name': 'output',
                'api_name': 'phone-1',
            },
        },
    )
    service = AIAgentService()

    # act
    result = service._convert_ex_to_markdown(ex=ex)

    # assert
    assert result == '- `output`: Value should be a string.'


def test_convert_ex_to_markdown__empty_details__ok():

    """ Validation error with empty details """

    # arrange
    ex = ValidationError(
        detail={
            'code': 'validation_error',
            'message': 'Invalid output.',
            'details': {},
        },
    )
    service = AIAgentService()

    # act
    result = service._convert_ex_to_markdown(ex=ex)

    # assert
    assert result == '- Invalid output.'


def test_convert_ex_to_markdown__no_details__ok():

    """ Validation error without details """

    # arrange
    ex = ValidationError(
        detail={
            'code': 'validation_error',
            'message': 'Invalid output.',
        },
    )
    service = AIAgentService()

    # act
    result = service._convert_ex_to_markdown(ex=ex)

    # assert
    assert result == '- Invalid output.'


def test_convert_ex_to_markdown__fields_map__ok():

    """ Fields map with lists """

    # arrange
    ex = ValidationError(
        detail={
            'phone-1': ['Value should be a string.'],
            'total-1': ['The value must be a number.'],
        },
    )
    service = AIAgentService()

    # act
    result = service._convert_ex_to_markdown(ex=ex)

    # assert
    assert result == (
        '- `phone-1`: Value should be a string.\n'
        '- `total-1`: The value must be a number.'
    )


def test_convert_ex_to_markdown__multiple_errors_per_field__ok():

    """ Fields map with multiple errors per field """

    # arrange
    ex = ValidationError(detail={'phone-1': ['error 1', 'error 2']})
    service = AIAgentService()

    # act
    result = service._convert_ex_to_markdown(ex=ex)

    # assert
    assert result == '- `phone-1`: error 1\n- `phone-1`: error 2'


def test_convert_ex_to_markdown__scalar_value__ok():

    """ Fields map with a scalar value """

    # arrange
    ex = ValidationError(detail={'phone-1': 'Value should be a string.'})
    service = AIAgentService()

    # act
    result = service._convert_ex_to_markdown(ex=ex)

    # assert
    assert result == '- `phone-1`: Value should be a string.'


def test_convert_ex_to_markdown__message_not_string__fields_map():

    """ Message is not a string """

    # arrange
    ex = ValidationError(detail={'message': ['error 1']})
    service = AIAgentService()

    # act
    result = service._convert_ex_to_markdown(ex=ex)

    # assert
    assert result == '- `message`: error 1'


def test_convert_ex_to_markdown__errors_list__ok():

    """ Errors list """

    # arrange
    ex = ValidationError(detail=['error 1', 'error 2'])
    service = AIAgentService()

    # act
    result = service._convert_ex_to_markdown(ex=ex)

    # assert
    assert result == '- error 1\n- error 2'


def test_convert_ex_to_markdown__empty_errors_list__default_message():

    """ Empty errors list """

    # arrange
    ex = ValidationError(detail=[])
    service = AIAgentService()

    # act
    result = service._convert_ex_to_markdown(ex=ex)

    # assert
    assert result == '- Validation failed.'


def test_convert_ex_to_markdown__empty_fields_map__default_message():

    """ Empty fields map """

    # arrange
    ex = ValidationError(detail={})
    service = AIAgentService()

    # act
    result = service._convert_ex_to_markdown(ex=ex)

    # assert
    assert result == '- Validation failed.'


def test_get_report_text__single_attempt__ok():

    """ Single attempt """

    # arrange
    errors_stack = [
        ({'phone-1': 'call me'}, '- `phone-1`: Value should be a string.'),
    ]
    service = AIAgentService()

    # act
    result = service._get_report_text(errors_stack=errors_stack)

    # assert
    assert result == (
        '# Complete task attempts\n\n'
        '## Attempt № 1\n\n'
        '### Output fields\n\n'
        '- `phone-1`: call me\n\n'
        '### Validation error\n\n'
        '- `phone-1`: Value should be a string.'
    )


def test_get_report_text__multiple_attempts__ok():

    """ Multiple attempts """

    # arrange
    errors_stack = [
        ({'phone-1': 'call me'}, '- `phone-1`: Value should be a string.'),
        ({'total-1': 'ten'}, '- `total-1`: The value must be a number.'),
    ]
    service = AIAgentService()

    # act
    result = service._get_report_text(errors_stack=errors_stack)

    # assert
    assert result == (
        '# Complete task attempts\n\n'
        '## Attempt № 1\n\n'
        '### Output fields\n\n'
        '- `phone-1`: call me\n\n'
        '### Validation error\n\n'
        '- `phone-1`: Value should be a string.'
        '\n\n-------\n\n'
        '## Attempt № 2\n\n'
        '### Output fields\n\n'
        '- `total-1`: ten\n\n'
        '### Validation error\n\n'
        '- `total-1`: The value must be a number.'
    )


def test_get_report_text__list_value__ok():

    """ List value """

    # arrange
    errors_stack = [
        ({'items-1': ['a', 'b']}, '- `items-1`: Invalid value.'),
    ]
    service = AIAgentService()

    # act
    result = service._get_report_text(errors_stack=errors_stack)

    # assert
    assert result == (
        '# Complete task attempts\n\n'
        '## Attempt № 1\n\n'
        '### Output fields\n\n'
        '- `items-1`: a, b\n\n'
        '### Validation error\n\n'
        '- `items-1`: Invalid value.'
    )


def test_get_report_text__tuple_value__ok():

    """ Tuple value """

    # arrange
    errors_stack = [
        ({'items-1': ('a', 'b')}, '- `items-1`: Invalid value.'),
    ]
    service = AIAgentService()

    # act
    result = service._get_report_text(errors_stack=errors_stack)

    # assert
    assert result == (
        '# Complete task attempts\n\n'
        '## Attempt № 1\n\n'
        '### Output fields\n\n'
        '- `items-1`: a, b\n\n'
        '### Validation error\n\n'
        '- `items-1`: Invalid value.'
    )


def test_get_report_text__non_string_value__ok():

    """ Non-string value """

    # arrange
    errors_stack = [
        ({'total-1': 42}, '- `total-1`: Invalid value.'),
    ]
    service = AIAgentService()

    # act
    result = service._get_report_text(errors_stack=errors_stack)

    # assert
    assert result == (
        '# Complete task attempts\n\n'
        '## Attempt № 1\n\n'
        '### Output fields\n\n'
        '- `total-1`: 42\n\n'
        '### Validation error\n\n'
        '- `total-1`: Invalid value.'
    )


def test_get_report_text__empty_fields_values__ok():

    """ Empty fields values """

    # arrange
    errors_stack = [({}, '- Invalid output.')]
    service = AIAgentService()

    # act
    result = service._get_report_text(errors_stack=errors_stack)

    # assert
    assert result == (
        '# Complete task attempts\n\n'
        '## Attempt № 1\n\n'
        '### Output fields\n\n'
        '\n\n'
        '### Validation error\n\n'
        '- Invalid output.'
    )


def test_get_report_text__empty_errors_stack__header_only():

    """ Empty errors stack """

    # arrange
    service = AIAgentService()

    # act
    result = service._get_report_text(errors_stack=[])

    # assert
    assert result == '# Complete task attempts\n\n'


def test_create_report_file__upload__ok(mocker):

    """ Upload report """

    # arrange
    account = create_test_account()
    agent = create_test_agent(account=account)
    text = '# Report'
    filename = 'report.md'
    url = 'https://storage.pneumatic.app/report.md'
    file_service_client_init_mock = mocker.patch.object(
        FileServiceClient,
        attribute='__init__',
        return_value=None,
    )
    upload_file_with_attachment_mock = mocker.patch(
        'src.ai.services.agent.FileServiceClient'
        '.upload_file_with_attachment',
        return_value=url,
    )
    service = AIAgentService(user=agent.user, instance=agent)

    # act
    result = service._create_report_file(text=text, filename=filename)

    # assert
    assert result == url
    file_service_client_init_mock.assert_called_once_with(user=agent.user)
    upload_file_with_attachment_mock.assert_called_once_with(
        file_content=b'# Report',
        filename=filename,
        content_type='text/plain',
        account=account,
        source_type=SourceType.TASK,
        access_type=AccessType.RESTRICTED,
    )


def test_create_comment__text__ok(mocker):

    """ Create comment """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = create_test_agent(account=account)
    text = 'The order is unclear.'
    comment_service_init_mock = mocker.patch.object(
        CommentService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.ai.services.agent.CommentService.create',
    )
    service = AIAgentService(user=agent.user, instance=agent)

    # act
    service._create_comment(task=task, text=text)

    # assert
    comment_service_init_mock.assert_called_once_with(
        user=agent.user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    create_mock.assert_called_once_with(task=task, text=text)


def test_raise_attempt_error__single_attempt__raise_exception(mocker):

    """ Single attempt """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = create_test_agent(account=account)
    errors_stack = [
        ({'phone-1': 'call me'}, '- `phone-1`: Value should be a string.'),
    ]
    text = '# Complete task attempts'
    url = 'https://storage.pneumatic.app/report.md'
    get_report_text_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._get_report_text',
        return_value=text,
    )
    create_report_file_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._create_report_file',
        return_value=url,
    )
    create_comment_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._create_comment',
    )
    service = AIAgentService(user=agent.user, instance=agent)

    # act
    with pytest.raises(AIAgentAttemptsExceededException) as ex:
        service._raise_attempt_error(task=task, errors_stack=errors_stack)

    # assert
    message = str(MSG_AI_0010(attempts=1))
    assert str(ex.value.message) == message
    action = AIAgentAction.objects.get(action=AIAgentActionType.ERROR)
    assert action.account_id == account.id
    assert action.agent_id == agent.id
    assert action.task_id == task.id
    assert action.text == f'{message}\n{url}'
    get_report_text_mock.assert_called_once_with(errors_stack=errors_stack)
    create_report_file_mock.assert_called_once_with(
        text=text,
        filename='report.md',
    )
    create_comment_mock.assert_called_once_with(
        task=task,
        text=str(MSG_AI_0009(attempts=1, report=f'[report.md]({url})')),
    )


def test_raise_attempt_error__multiple_attempts__raise_exception(mocker):

    """ Multiple attempts """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = create_test_agent(account=account)
    errors_stack = [
        ({'phone-1': 'call me'}, '- `phone-1`: Value should be a string.'),
    ] * 10
    text = '# Complete task attempts'
    url = 'https://storage.pneumatic.app/report.md'
    get_report_text_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._get_report_text',
        return_value=text,
    )
    create_report_file_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._create_report_file',
        return_value=url,
    )
    create_comment_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._create_comment',
    )
    service = AIAgentService(user=agent.user, instance=agent)

    # act
    with pytest.raises(AIAgentAttemptsExceededException) as ex:
        service._raise_attempt_error(task=task, errors_stack=errors_stack)

    # assert
    message = str(MSG_AI_0010(attempts=10))
    assert str(ex.value.message) == message
    action = AIAgentAction.objects.get(action=AIAgentActionType.ERROR)
    assert action.text == f'{message}\n{url}'
    get_report_text_mock.assert_called_once_with(errors_stack=errors_stack)
    create_report_file_mock.assert_called_once_with(
        text=text,
        filename='report.md',
    )
    create_comment_mock.assert_called_once_with(
        task=task,
        text=str(MSG_AI_0009(attempts=10, report=f'[report.md]({url})')),
    )


def test_attempt_complete_task__first_attempt__ok(mocker):

    """ Success on the first attempt """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = create_test_agent(account=account)
    fields_values = {'phone-1': '+1 202 555 0147'}
    get_fields_values_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._get_fields_values',
        return_value=fields_values,
    )
    complete_task_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._complete_task',
    )
    convert_ex_to_markdown_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._convert_ex_to_markdown',
    )
    raise_attempt_error_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._raise_attempt_error',
    )
    service = AIAgentService(user=agent.user, instance=agent)

    # act
    result = service._attempt_complete_task(task=task)

    # assert
    assert result == fields_values
    get_fields_values_mock.assert_called_once_with(
        task=task,
        errors_stack=None,
    )
    complete_task_mock.assert_called_once_with(
        task=task,
        fields_values=fields_values,
    )
    convert_ex_to_markdown_mock.assert_not_called()
    raise_attempt_error_mock.assert_not_called()


def test_attempt_complete_task__validation_error__retry(mocker):

    """ Success after a validation error """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = create_test_agent(account=account)
    fields_values_1 = {'phone-1': 'call me'}
    fields_values_2 = {'phone-1': '+1 202 555 0147'}
    error = '- `phone-1`: Value should be a string.'
    validation_error = ValidationError(
        detail={'phone-1': ['Value should be a string.']},
    )
    get_fields_values_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._get_fields_values',
        side_effect=[fields_values_1, fields_values_2],
    )
    complete_task_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._complete_task',
        side_effect=[validation_error, None],
    )
    convert_ex_to_markdown_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._convert_ex_to_markdown',
        return_value=error,
    )
    raise_attempt_error_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._raise_attempt_error',
    )
    service = AIAgentService(user=agent.user, instance=agent)

    # act
    result = service._attempt_complete_task(task=task)

    # assert
    assert result == fields_values_2
    assert get_fields_values_mock.call_count == 2
    get_fields_values_mock.assert_has_calls(
        [
            mocker.call(task=task, errors_stack=None),
            mocker.call(
                task=task,
                errors_stack=[(fields_values_1, error)],
            ),
        ],
        any_order=True,
    )
    assert complete_task_mock.call_count == 2
    complete_task_mock.assert_has_calls(
        [
            mocker.call(task=task, fields_values=fields_values_1),
            mocker.call(task=task, fields_values=fields_values_2),
        ],
        any_order=True,
    )
    convert_ex_to_markdown_mock.assert_called_once_with(validation_error)
    raise_attempt_error_mock.assert_not_called()


def test_attempt_complete_task__workflow_action_service_exception__retry(
    mocker,
):

    """ Retry on WorkflowActionServiceException """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = create_test_agent(account=account)
    fields_values_1 = {'phone-1': 'call me'}
    fields_values_2 = {'phone-1': '+1 202 555 0147'}
    error = '- Workflow error.'
    service_exception = WorkflowActionServiceException(
        message='Workflow error.',
    )
    get_fields_values_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._get_fields_values',
        side_effect=[fields_values_1, fields_values_2],
    )
    complete_task_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._complete_task',
        side_effect=[service_exception, None],
    )
    convert_ex_to_markdown_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._convert_ex_to_markdown',
        return_value=error,
    )
    raise_attempt_error_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._raise_attempt_error',
    )
    service = AIAgentService(user=agent.user, instance=agent)

    # act
    result = service._attempt_complete_task(task=task)

    # assert
    assert result == fields_values_2
    assert get_fields_values_mock.call_count == 2
    get_fields_values_mock.assert_has_calls(
        [
            mocker.call(task=task, errors_stack=None),
            mocker.call(
                task=task,
                errors_stack=[(fields_values_1, error)],
            ),
        ],
        any_order=True,
    )
    assert complete_task_mock.call_count == 2
    complete_task_mock.assert_has_calls(
        [
            mocker.call(task=task, fields_values=fields_values_1),
            mocker.call(task=task, fields_values=fields_values_2),
        ],
        any_order=True,
    )
    convert_ex_to_markdown_mock.assert_called_once_with(service_exception)
    raise_attempt_error_mock.assert_not_called()


def test_attempt_complete_task__fieldset_service_exception__retry(mocker):

    """ Retry on FieldsetServiceException """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = create_test_agent(account=account)
    fields_values_1 = {'phone-1': 'call me'}
    fields_values_2 = {'phone-1': '+1 202 555 0147'}
    error = '- Fieldset error.'
    service_exception = FieldsetServiceException(message='Fieldset error.')
    get_fields_values_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._get_fields_values',
        side_effect=[fields_values_1, fields_values_2],
    )
    complete_task_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._complete_task',
        side_effect=[service_exception, None],
    )
    convert_ex_to_markdown_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._convert_ex_to_markdown',
        return_value=error,
    )
    raise_attempt_error_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._raise_attempt_error',
    )
    service = AIAgentService(user=agent.user, instance=agent)

    # act
    result = service._attempt_complete_task(task=task)

    # assert
    assert result == fields_values_2
    assert get_fields_values_mock.call_count == 2
    get_fields_values_mock.assert_has_calls(
        [
            mocker.call(task=task, errors_stack=None),
            mocker.call(
                task=task,
                errors_stack=[(fields_values_1, error)],
            ),
        ],
        any_order=True,
    )
    assert complete_task_mock.call_count == 2
    complete_task_mock.assert_has_calls(
        [
            mocker.call(task=task, fields_values=fields_values_1),
            mocker.call(task=task, fields_values=fields_values_2),
        ],
        any_order=True,
    )
    convert_ex_to_markdown_mock.assert_called_once_with(service_exception)
    raise_attempt_error_mock.assert_not_called()


def test_attempt_complete_task__unhandled_exception__raise_exception(mocker):

    """ Unhandled exception """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = create_test_agent(account=account)
    fields_values = {'phone-1': '+1 202 555 0147'}
    get_fields_values_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._get_fields_values',
        return_value=fields_values,
    )
    complete_task_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._complete_task',
        side_effect=ValueError('Unexpected error'),
    )
    convert_ex_to_markdown_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._convert_ex_to_markdown',
    )
    raise_attempt_error_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._raise_attempt_error',
    )
    service = AIAgentService(user=agent.user, instance=agent)

    # act
    with pytest.raises(ValueError) as ex:
        service._attempt_complete_task(task=task)

    # assert
    assert str(ex.value) == 'Unexpected error'
    get_fields_values_mock.assert_called_once_with(
        task=task,
        errors_stack=None,
    )
    complete_task_mock.assert_called_once_with(
        task=task,
        fields_values=fields_values,
    )
    convert_ex_to_markdown_mock.assert_not_called()
    raise_attempt_error_mock.assert_not_called()


def test_attempt_complete_task__errors_stack_passed__append(mocker):

    """ Errors stack passed """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = create_test_agent(account=account)
    fields_values_1 = {'phone-1': 'call me'}
    fields_values_2 = {'phone-1': 'call me later'}
    fields_values_3 = {'phone-1': '+1 202 555 0147'}
    error_1 = '- `phone-1`: Value should be a string.'
    error_2 = '- `phone-1`: Value should be a phone.'
    errors_stack = [(fields_values_1, error_1)]
    validation_error = ValidationError(
        detail={'phone-1': ['Value should be a phone.']},
    )
    get_fields_values_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._get_fields_values',
        side_effect=[fields_values_2, fields_values_3],
    )
    complete_task_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._complete_task',
        side_effect=[validation_error, None],
    )
    convert_ex_to_markdown_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._convert_ex_to_markdown',
        return_value=error_2,
    )
    raise_attempt_error_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._raise_attempt_error',
    )
    service = AIAgentService(user=agent.user, instance=agent)

    # act
    result = service._attempt_complete_task(
        task=task,
        errors_stack=errors_stack,
        attempt=2,
    )

    # assert
    assert result == fields_values_3
    assert errors_stack == [
        (fields_values_1, error_1),
        (fields_values_2, error_2),
    ]
    assert get_fields_values_mock.call_count == 2
    get_fields_values_mock.assert_has_calls(
        [
            mocker.call(task=task, errors_stack=errors_stack),
            mocker.call(task=task, errors_stack=errors_stack),
        ],
        any_order=True,
    )
    assert complete_task_mock.call_count == 2
    complete_task_mock.assert_has_calls(
        [
            mocker.call(task=task, fields_values=fields_values_2),
            mocker.call(task=task, fields_values=fields_values_3),
        ],
        any_order=True,
    )
    convert_ex_to_markdown_mock.assert_called_once_with(validation_error)
    raise_attempt_error_mock.assert_not_called()


def test_attempt_complete_task__attempts_exceeded__raise_exception(mocker):

    """ Attempts exceeded """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = create_test_agent(account=account)
    fields_values = {'phone-1': 'call me'}
    error = '- `phone-1`: Value should be a string.'
    validation_error = ValidationError(
        detail={'phone-1': ['Value should be a string.']},
    )
    get_fields_values_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._get_fields_values',
        return_value=fields_values,
    )
    complete_task_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._complete_task',
        side_effect=validation_error,
    )
    convert_ex_to_markdown_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._convert_ex_to_markdown',
        return_value=error,
    )
    raise_attempt_error_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._raise_attempt_error',
        side_effect=AIAgentAttemptsExceededException(
            message='Attempts exceeded.',
        ),
    )
    service = AIAgentService(user=agent.user, instance=agent)

    # act
    with pytest.raises(AIAgentAttemptsExceededException) as ex:
        service._attempt_complete_task(task=task)

    # assert
    assert str(ex.value.message) == 'Attempts exceeded.'
    errors_stack = [(fields_values, error)] * 10
    assert get_fields_values_mock.call_count == 10
    get_fields_values_mock.assert_has_calls(
        [
            mocker.call(task=task, errors_stack=None),
            mocker.call(task=task, errors_stack=errors_stack),
        ],
        any_order=True,
    )
    assert complete_task_mock.call_count == 10
    complete_task_mock.assert_has_calls(
        [
            mocker.call(task=task, fields_values=fields_values),
        ],
        any_order=True,
    )
    assert convert_ex_to_markdown_mock.call_count == 10
    convert_ex_to_markdown_mock.assert_has_calls(
        [
            mocker.call(validation_error),
        ],
        any_order=True,
    )
    raise_attempt_error_mock.assert_called_once_with(
        task=task,
        errors_stack=errors_stack,
    )


def test_attempt_complete_task__last_attempt_fails__raise_exception(mocker):

    """ Last attempt fails """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = create_test_agent(account=account)
    fields_values = {'phone-1': 'call me'}
    error = '- `phone-1`: Value should be a string.'
    validation_error = ValidationError(
        detail={'phone-1': ['Value should be a string.']},
    )
    get_fields_values_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._get_fields_values',
        return_value=fields_values,
    )
    complete_task_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._complete_task',
        side_effect=validation_error,
    )
    convert_ex_to_markdown_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._convert_ex_to_markdown',
        return_value=error,
    )
    raise_attempt_error_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._raise_attempt_error',
        side_effect=AIAgentAttemptsExceededException(
            message='Attempts exceeded.',
        ),
    )
    service = AIAgentService(user=agent.user, instance=agent)

    # act
    with pytest.raises(AIAgentAttemptsExceededException) as ex:
        service._attempt_complete_task(task=task, attempt=10)

    # assert
    assert str(ex.value.message) == 'Attempts exceeded.'
    get_fields_values_mock.assert_called_once_with(
        task=task,
        errors_stack=None,
    )
    complete_task_mock.assert_called_once_with(
        task=task,
        fields_values=fields_values,
    )
    convert_ex_to_markdown_mock.assert_called_once_with(validation_error)
    raise_attempt_error_mock.assert_called_once_with(
        task=task,
        errors_stack=[(fields_values, error)],
    )


def test_create_instance__default_parameters__ok(mocker):

    """ Default parameters """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    email = 'ai-agent-Hq3kZr9TbVn2Lm7sXy1p@pneumatic.app'
    agent_user = create_test_admin(
        account=account,
        email=email,
        first_name='Operator',
        is_ai=True,
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.ai.services.agent.UserService.create',
        return_value=agent_user,
    )
    get_agent_email_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._get_agent_email',
        return_value=email,
    )
    service = AIAgentService(user=owner)

    # act
    result = service._create_instance(
        name='Operator',
        model='gpt-4o',
        system_prompt='You are an operator.',
        provider_id=provider.id,
    )

    # assert
    agent = AIAgent.objects.get(id=result.id)
    assert agent.account_id == account.id
    assert agent.name == 'Operator'
    assert agent.model == 'gpt-4o'
    assert agent.system_prompt == 'You are an operator.'
    assert agent.is_active is True
    assert agent.photo is None
    assert agent.provider_id == provider.id
    assert agent.user_id == agent_user.id
    assert service.instance == agent
    user_service_init_mock.assert_called_once_with(
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_mock.assert_called_once_with(
        account=account,
        email=email,
        first_name='Operator',
        photo=None,
        is_admin=True,
        is_ai=True,
        is_tasks_digest_subscriber=False,
        is_digest_subscriber=False,
        is_newsletters_subscriber=False,
        is_special_offers_subscriber=False,
        is_new_tasks_subscriber=False,
        is_complete_tasks_subscriber=False,
        is_comments_mentions_subscriber=False,
    )
    get_agent_email_mock.assert_called_once_with()


def test_create_instance__all_parameters__ok(mocker):

    """ All parameters """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    email = 'ai-agent-Hq3kZr9TbVn2Lm7sXy1p@pneumatic.app'
    photo = 'https://storage.pneumatic.app/operator.png'
    agent_user = create_test_admin(
        account=account,
        email=email,
        first_name='Operator',
        photo=photo,
        is_ai=True,
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.ai.services.agent.UserService.create',
        return_value=agent_user,
    )
    get_agent_email_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._get_agent_email',
        return_value=email,
    )
    service = AIAgentService(user=owner)

    # act
    result = service._create_instance(
        name='Operator',
        model='gpt-4o',
        system_prompt='You are an operator.',
        is_active=False,
        photo=photo,
        provider_id=provider.id,
    )

    # assert
    agent = AIAgent.objects.get(id=result.id)
    assert agent.name == 'Operator'
    assert agent.is_active is False
    assert agent.photo == photo
    assert agent.provider_id == provider.id
    assert agent.user_id == agent_user.id
    user_service_init_mock.assert_called_once_with(
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_mock.assert_called_once_with(
        account=account,
        email=email,
        first_name='Operator',
        photo=photo,
        is_admin=True,
        is_ai=True,
        is_tasks_digest_subscriber=False,
        is_digest_subscriber=False,
        is_newsletters_subscriber=False,
        is_special_offers_subscriber=False,
        is_new_tasks_subscriber=False,
        is_complete_tasks_subscriber=False,
        is_comments_mentions_subscriber=False,
    )
    get_agent_email_mock.assert_called_once_with()


def test_create_instance__name_not_unique__raise_exception(mocker):

    """ Name not unique """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    create_test_agent(account=account, provider=provider, name='Operator')
    email = 'ai-agent-Hq3kZr9TbVn2Lm7sXy1p@pneumatic.app'
    agent_user = create_test_admin(
        account=account,
        email=email,
        first_name='Operator',
        is_ai=True,
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.ai.services.agent.UserService.create',
        return_value=agent_user,
    )
    get_agent_email_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._get_agent_email',
        return_value=email,
    )
    service = AIAgentService(user=owner)

    # act
    with pytest.raises(AIAgentNameNotUniqueException) as ex:
        service._create_instance(
            name='Operator',
            model='gpt-4o',
            system_prompt='You are an operator.',
            provider_id=provider.id,
        )

    # assert
    assert str(ex.value.message) == str(MSG_AI_0004)
    assert AIAgent.objects.filter(account=account).count() == 1
    user_service_init_mock.assert_called_once_with(
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_mock.assert_called_once_with(
        account=account,
        email=email,
        first_name='Operator',
        photo=None,
        is_admin=True,
        is_ai=True,
        is_tasks_digest_subscriber=False,
        is_digest_subscriber=False,
        is_newsletters_subscriber=False,
        is_special_offers_subscriber=False,
        is_new_tasks_subscriber=False,
        is_complete_tasks_subscriber=False,
        is_comments_mentions_subscriber=False,
    )
    get_agent_email_mock.assert_called_once_with()


def test_create_instance__same_name_in_another_account__ok(mocker):

    """ Same name in another account """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    another_account = create_test_account(name='Another Company')
    create_test_agent(account=another_account, name='Operator')
    email = 'ai-agent-Hq3kZr9TbVn2Lm7sXy1p@pneumatic.app'
    agent_user = create_test_admin(
        account=account,
        email=email,
        first_name='Operator',
        is_ai=True,
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.ai.services.agent.UserService.create',
        return_value=agent_user,
    )
    get_agent_email_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._get_agent_email',
        return_value=email,
    )
    service = AIAgentService(user=owner)

    # act
    result = service._create_instance(
        name='Operator',
        model='gpt-4o',
        system_prompt='You are an operator.',
        provider_id=provider.id,
    )

    # assert
    agent = AIAgent.objects.get(id=result.id)
    assert agent.account_id == account.id
    assert agent.name == 'Operator'
    assert agent.user_id == agent_user.id
    user_service_init_mock.assert_called_once_with(
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_mock.assert_called_once_with(
        account=account,
        email=email,
        first_name='Operator',
        photo=None,
        is_admin=True,
        is_ai=True,
        is_tasks_digest_subscriber=False,
        is_digest_subscriber=False,
        is_newsletters_subscriber=False,
        is_special_offers_subscriber=False,
        is_new_tasks_subscriber=False,
        is_complete_tasks_subscriber=False,
        is_comments_mentions_subscriber=False,
    )
    get_agent_email_mock.assert_called_once_with()


def test_create_instance__same_name_as_deleted_agent__ok(mocker):

    """ Same name as a deleted agent """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    deleted_agent = create_test_agent(
        account=account,
        provider=provider,
        name='Operator',
    )
    deleted_agent.delete()
    email = 'ai-agent-Hq3kZr9TbVn2Lm7sXy1p@pneumatic.app'
    agent_user = create_test_admin(
        account=account,
        email=email,
        first_name='Operator',
        is_ai=True,
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.ai.services.agent.UserService.create',
        return_value=agent_user,
    )
    get_agent_email_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._get_agent_email',
        return_value=email,
    )
    service = AIAgentService(user=owner)

    # act
    result = service._create_instance(
        name='Operator',
        model='gpt-4o',
        system_prompt='You are an operator.',
        provider_id=provider.id,
    )

    # assert
    agent = AIAgent.objects.get(id=result.id)
    assert agent.account_id == account.id
    assert agent.name == 'Operator'
    assert agent.user_id == agent_user.id
    user_service_init_mock.assert_called_once_with(
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_mock.assert_called_once_with(
        account=account,
        email=email,
        first_name='Operator',
        photo=None,
        is_admin=True,
        is_ai=True,
        is_tasks_digest_subscriber=False,
        is_digest_subscriber=False,
        is_newsletters_subscriber=False,
        is_special_offers_subscriber=False,
        is_new_tasks_subscriber=False,
        is_complete_tasks_subscriber=False,
        is_comments_mentions_subscriber=False,
    )
    get_agent_email_mock.assert_called_once_with()


def test_partial_update__name__ok(mocker):

    """ Update name """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    agent = create_test_agent(account=account, name='Operator')
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.ai.services.agent.UserService.partial_update',
    )
    service = AIAgentService(user=owner, instance=agent)

    # act
    result = service.partial_update(name='Courier')

    # assert
    assert result == agent
    agent.refresh_from_db()
    assert agent.name == 'Courier'
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=agent.user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(first_name='Courier')


def test_partial_update__photo__ok(mocker):

    """ Update photo """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    agent = create_test_agent(account=account)
    photo = 'https://storage.pneumatic.app/operator.png'
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.ai.services.agent.UserService.partial_update',
    )
    service = AIAgentService(user=owner, instance=agent)

    # act
    result = service.partial_update(photo=photo)

    # assert
    assert result == agent
    agent.refresh_from_db()
    assert agent.photo == photo
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=agent.user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(photo=photo)


def test_partial_update__name_and_photo__ok(mocker):

    """ Update name and photo """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    agent = create_test_agent(account=account, name='Operator')
    photo = 'https://storage.pneumatic.app/courier.png'
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.ai.services.agent.UserService.partial_update',
    )
    service = AIAgentService(user=owner, instance=agent)

    # act
    result = service.partial_update(name='Courier', photo=photo)

    # assert
    assert result == agent
    agent.refresh_from_db()
    assert agent.name == 'Courier'
    assert agent.photo == photo
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=agent.user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        first_name='Courier',
        photo=photo,
    )


def test_partial_update__other_fields__skip_user_update(mocker):

    """ Update other fields """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    agent = create_test_agent(account=account)
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.ai.services.agent.UserService.partial_update',
    )
    service = AIAgentService(user=owner, instance=agent)

    # act
    result = service.partial_update(
        system_prompt='You are a courier.',
        model='gpt-4o-mini',
    )

    # assert
    assert result == agent
    agent.refresh_from_db()
    assert agent.system_prompt == 'You are a courier.'
    assert agent.model == 'gpt-4o-mini'
    user_service_init_mock.assert_not_called()
    partial_update_mock.assert_not_called()


def test_partial_update__force_save_disabled__not_saved(mocker):

    """ Force save disabled """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    agent = create_test_agent(
        account=account,
        system_prompt='You are an operator.',
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.ai.services.agent.UserService.partial_update',
    )
    service = AIAgentService(user=owner, instance=agent)

    # act
    result = service.partial_update(
        force_save=False,
        system_prompt='You are a courier.',
    )

    # assert
    assert result.system_prompt == 'You are a courier.'
    agent.refresh_from_db()
    assert agent.system_prompt == 'You are an operator.'
    user_service_init_mock.assert_not_called()
    partial_update_mock.assert_not_called()


def test_partial_update__name_not_unique__raise_exception(mocker):

    """ Name not unique """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    create_test_agent(account=account, provider=provider, name='Courier')
    agent = create_test_agent(
        account=account,
        provider=provider,
        name='Operator',
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.ai.services.agent.UserService.partial_update',
    )
    service = AIAgentService(user=owner, instance=agent)

    # act
    with pytest.raises(AIAgentNameNotUniqueException) as ex:
        service.partial_update(name='Courier')

    # assert
    assert str(ex.value.message) == str(MSG_AI_0004)
    agent.refresh_from_db()
    assert agent.name == 'Operator'
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=agent.user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(first_name='Courier')


def test_delete__agent_and_user__ok():

    """ Delete agent """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    agent = create_test_agent(account=account)
    agent_user = agent.user
    service = AIAgentService(user=owner, instance=agent)

    # act
    service.delete()

    # assert
    agent.refresh_from_db()
    assert agent.is_deleted is True
    agent_user.refresh_from_db()
    assert agent_user.is_deleted is True


def test_complete_task__task_id__ok(mocker):

    """ Complete task """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = create_test_agent(account=account)
    fields_values = {'phone-1': '+1 202 555 0147'}
    attempt_complete_task_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._attempt_complete_task',
        return_value=fields_values,
    )
    service = AIAgentService(user=agent.user, instance=agent)

    # act
    service.complete_task(task_id=task.id)

    # assert
    in_progress_action = AIAgentAction.objects.get(
        action=AIAgentActionType.TASK_IN_PROGRESS,
    )
    assert in_progress_action.account_id == account.id
    assert in_progress_action.agent_id == agent.id
    assert in_progress_action.task_id == task.id
    assert in_progress_action.text is None
    completed_action = AIAgentAction.objects.get(
        action=AIAgentActionType.TASK_COMPLETED,
    )
    assert completed_action.account_id == account.id
    assert completed_action.agent_id == agent.id
    assert completed_action.task_id == task.id
    assert completed_action.text == '{"phone-1": "+1 202 555 0147"}'
    attempt_complete_task_mock.assert_called_once_with(task=task)


def test_complete_task__non_ascii_values__ok(mocker):

    """ Non-ascii values """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = create_test_agent(account=account)
    fields_values = {'name-1': 'Иван Петров'}
    attempt_complete_task_mock = mocker.patch(
        'src.ai.services.agent.AIAgentService._attempt_complete_task',
        return_value=fields_values,
    )
    service = AIAgentService(user=agent.user, instance=agent)

    # act
    service.complete_task(task_id=task.id)

    # assert
    completed_action = AIAgentAction.objects.get(
        action=AIAgentActionType.TASK_COMPLETED,
    )
    assert completed_action.text == '{"name-1": "Иван Петров"}'
    attempt_complete_task_mock.assert_called_once_with(task=task)


def test_reply_to_comment__notification_exists__ok():

    """ Notification exists """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    agent = create_test_agent(account=account)
    notification = Notification.objects.create(
        account=account,
        user=agent.user,
        author=owner,
        task=task,
        type=NotificationType.MENTION,
        text='Please call the customer.',
    )
    service = AIAgentService(user=agent.user, instance=agent)

    # act
    service.reply_to_comment(notification_id=notification.id)

    # assert
    notification.refresh_from_db()
    assert notification.status == NotificationStatus.READ
    action = AIAgentAction.objects.get(notification=notification)
    assert action.account_id == account.id
    assert action.agent_id == agent.id
    assert action.task_id == task.id
    assert action.action == AIAgentActionType.MENTION_IN_PROGRESS


def test_reply_to_comment__notification_not_found__skip():

    """ Notification not found """

    # arrange
    account = create_test_account()
    agent = create_test_agent(account=account)
    service = AIAgentService(user=agent.user, instance=agent)

    # act
    service.reply_to_comment(notification_id=999999)

    # assert
    assert AIAgentAction.objects.filter(agent=agent).exists() is False
