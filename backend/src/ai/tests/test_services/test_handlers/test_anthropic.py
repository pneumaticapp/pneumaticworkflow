import pytest

from src.ai.enums import AIVendor, OpenAIRole
from src.ai.services.config import AI_VENDORS_CONFIG
from src.ai.services.handlers import AnthropicHandler
from src.ai.tests.fixtures import create_test_provider
from src.processes.tests.fixtures import create_test_account

pytestmark = pytest.mark.django_db


def test_auth_headers__api_key__ok():

    """ Auth headers """

    # arrange
    account = create_test_account()
    api_key = 'sk-ant-example'
    provider = create_test_provider(account=account, api_key=api_key)
    handler = AnthropicHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.ANTHROPIC],
    )

    # act
    result = handler._auth_headers()

    # assert
    assert result == {
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
    }


def test_parse_completion__multiple_text_blocks__joined():

    """ Multiple text blocks """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = AnthropicHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.ANTHROPIC],
    )
    payload = {
        'id': 'msg_01XFDUDYJgAACzvnptvVoYEL',
        'type': 'message',
        'role': 'assistant',
        'content': [
            {'type': 'text', 'text': 'Hello'},
            {'type': 'text', 'text': ' world!'},
        ],
        'stop_reason': 'end_turn',
    }

    # act
    result = handler._parse_completion(payload=payload)

    # assert
    assert result == 'Hello world!'


def test_parse_completion__non_text_blocks__skip():

    """ Non-text blocks skipped """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = AnthropicHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.ANTHROPIC],
    )
    payload = {
        'content': [
            {'type': 'tool_use', 'id': 'toolu_1', 'name': 'search'},
            {'type': 'text', 'text': 'Hello!'},
            {'text': 'No type'},
        ],
    }

    # act
    result = handler._parse_completion(payload=payload)

    # assert
    assert result == 'Hello!'


def test_parse_completion__empty_content__empty_string():

    """ Empty content """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = AnthropicHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.ANTHROPIC],
    )
    payload = {'content': []}

    # act
    result = handler._parse_completion(payload=payload)

    # assert
    assert result == ''


def test_parse_models__models_received__ok():

    """ Models parsed """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = AnthropicHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.ANTHROPIC],
    )
    payload = {
        'data': [
            {
                'id': 'claude-sonnet-4-20250514',
                'type': 'model',
                'display_name': 'Claude Sonnet 4',
                'created_at': '2025-05-14T00:00:00Z',
            },
            {
                'id': 'claude-opus-4-20250514',
                'type': 'model',
                'display_name': 'Claude Opus 4',
                'created_at': '2025-05-14T00:00:00Z',
            },
        ],
        'has_more': False,
    }

    # act
    result = handler._parse_models(payload=payload)

    # assert
    assert result == [
        {'slug': 'claude-sonnet-4-20250514', 'name': 'Claude Sonnet 4'},
        {'slug': 'claude-opus-4-20250514', 'name': 'Claude Opus 4'},
    ]


def test_parse_models__empty_data__empty_list():

    """ Empty data """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = AnthropicHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.ANTHROPIC],
    )
    payload = {'data': [], 'has_more': False}

    # act
    result = handler._parse_models(payload=payload)

    # assert
    assert result == []


def test_parse_error__anthropic_error_body__ok():

    """ Anthropic error body """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = AnthropicHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.ANTHROPIC],
    )
    response_data = {
        'type': 'error',
        'error': {
            'type': 'not_found_error',
            'message': 'The requested resource does not exist.',
        },
        'request_id': 'req_011CSHoEeqs5C35K2UUqR7Fy',
    }

    # act
    result = handler._parse_error(
        http_status=404,
        response_data=response_data,
    )

    # assert
    assert result == 'The requested resource does not exist.'


def test_parse_error__response_data_not_dict__none():

    """ Response data is not dict """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = AnthropicHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.ANTHROPIC],
    )

    # act
    result = handler._parse_error(http_status=500, response_data=None)

    # assert
    assert result is None


def test_get_completion__completion_received__ok(mocker):

    """ Completion received """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = AnthropicHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.ANTHROPIC],
    )
    url = 'https://api.anthropic.com/v1/messages'
    headers = {'x-api-key': 'sk-ant-example'}
    system_message = 'You are helpful.'
    user_message = 'Say "Hello world"'
    model = 'claude-sonnet-4-20250514'
    payload = {'content': [{'type': 'text', 'text': 'Hello world'}]}
    get_chat_url_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler.get_chat_url',
        return_value=url,
    )
    auth_headers_mock = mocker.patch(
        'src.ai.services.handlers.anthropic.AnthropicHandler._auth_headers',
        return_value=headers,
    )
    request_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._request',
        return_value=(200, payload),
    )
    parse_completion_mock = mocker.patch(
        'src.ai.services.handlers.anthropic.AnthropicHandler'
        '._parse_completion',
        return_value='Hello world',
    )

    # act
    result = handler.get_completion(
        system_message=system_message,
        user_message=user_message,
        model=model,
    )

    # assert
    assert result == 'Hello world'
    get_chat_url_mock.assert_called_once_with()
    auth_headers_mock.assert_called_once_with()
    request_mock.assert_called_once_with(
        method='POST',
        url=url,
        headers=headers,
        data={
            'model': model,
            'max_tokens': 1024,
            'system': system_message,
            'messages': [
                {
                    'role': OpenAIRole.USER,
                    'content': user_message,
                },
            ],
        },
        timeout=handler.completion_timeout,
    )
    parse_completion_mock.assert_called_once_with(payload)
