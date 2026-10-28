import pytest

from src.ai.enums import AIVendor, OpenAIRole
from src.ai.services.config import AI_VENDORS_CONFIG
from src.ai.services.handlers import OpenAIHandler
from src.ai.tests.fixtures import create_test_provider
from src.processes.tests.fixtures import create_test_account

pytestmark = pytest.mark.django_db


def test_auth_headers__api_key__ok():

    """ Auth headers """

    # arrange
    account = create_test_account()
    api_key = 'sk-example'
    provider = create_test_provider(account=account, api_key=api_key)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )

    # act
    result = handler._auth_headers()

    # assert
    assert result == {'Authorization': 'Bearer sk-example'}


def test_is_chat_model__chat_model__true():

    """ Chat model """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    item = {'id': 'gpt-4o'}

    # act
    result = handler._is_chat_model(item=item)

    # assert
    assert result is True


def test_is_chat_model__non_chat_model__false():

    """ Non-chat model """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    item = {'id': 'text-embedding-3-small'}

    # act
    result = handler._is_chat_model(item=item)

    # assert
    assert result is False


def test_is_chat_model__non_chat_model_upper_case__false():

    """ Non-chat model in upper case """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    item = {'id': 'Whisper-1'}

    # act
    result = handler._is_chat_model(item=item)

    # assert
    assert result is False


def test_parse_completion__single_choice__ok():

    """ Single choice """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    payload = {
        'choices': [
            {
                'index': 0,
                'message': {'role': 'assistant', 'content': 'Hello!'},
                'finish_reason': 'stop',
            },
        ],
    }

    # act
    result = handler._parse_completion(payload=payload)

    # assert
    assert result == 'Hello!'


def test_parse_completion__multiple_choices__first_choice():

    """ Multiple choices """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    payload = {
        'choices': [
            {
                'index': 0,
                'message': {'role': 'assistant', 'content': 'Choice 1'},
            },
            {
                'index': 1,
                'message': {'role': 'assistant', 'content': 'Choice 2'},
            },
        ],
    }

    # act
    result = handler._parse_completion(payload=payload)

    # assert
    assert result == 'Choice 1'


def test_parse_error__openai_error_body__ok():

    """ OpenAI error body """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    response_data = {
        'error': {
            'message': 'Incorrect API key provided.',
            'type': 'invalid_request_error',
            'param': None,
            'code': 'invalid_api_key',
        },
    }

    # act
    result = handler._parse_error(
        http_status=401,
        response_data=response_data,
    )

    # assert
    assert result == 'Incorrect API key provided.'


def test_parse_error__response_data_not_dict__none():

    """ Response data is not dict """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )

    # act
    result = handler._parse_error(http_status=500, response_data=None)

    # assert
    assert result is None


def test_parse_models__model_with_name__ok(mocker):

    """ Model with name """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    item = {'id': 'openai/gpt-4o', 'name': 'OpenAI: GPT-4o'}
    payload = {'object': 'list', 'data': [item]}
    is_chat_model_mock = mocker.patch(
        'src.ai.services.handlers.openai.OpenAIHandler._is_chat_model',
        return_value=True,
    )

    # act
    result = handler._parse_models(payload=payload)

    # assert
    assert result == [{'slug': 'openai/gpt-4o', 'name': 'OpenAI: GPT-4o'}]
    is_chat_model_mock.assert_called_once_with(item)


def test_parse_models__model_without_name__name_from_id(mocker):

    """ Model without name """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    item = {'id': 'gpt-4o', 'object': 'model', 'owned_by': 'openai'}
    payload = {'object': 'list', 'data': [item]}
    is_chat_model_mock = mocker.patch(
        'src.ai.services.handlers.openai.OpenAIHandler._is_chat_model',
        return_value=True,
    )

    # act
    result = handler._parse_models(payload=payload)

    # assert
    assert result == [{'slug': 'gpt-4o', 'name': 'gpt-4o'}]
    is_chat_model_mock.assert_called_once_with(item)


def test_parse_models__non_chat_model__skip(mocker):

    """ Non-chat model skipped """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    item = {'id': 'text-embedding-3-small'}
    payload = {'object': 'list', 'data': [item]}
    is_chat_model_mock = mocker.patch(
        'src.ai.services.handlers.openai.OpenAIHandler._is_chat_model',
        return_value=False,
    )

    # act
    result = handler._parse_models(payload=payload)

    # assert
    assert result == []
    is_chat_model_mock.assert_called_once_with(item)


def test_parse_models__empty_data__empty_list(mocker):

    """ Empty data """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    payload = {'object': 'list', 'data': []}
    is_chat_model_mock = mocker.patch(
        'src.ai.services.handlers.openai.OpenAIHandler._is_chat_model',
    )

    # act
    result = handler._parse_models(payload=payload)

    # assert
    assert result == []
    is_chat_model_mock.assert_not_called()


def test_get_completion__completion_received__ok(mocker):

    """ Completion received """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {'Authorization': 'Bearer sk-example'}
    system_message = 'You are helpful.'
    user_message = 'Say "Hello world"'
    model = 'gpt-4o'
    payload = {'choices': [{'message': {'content': 'Hello world'}}]}
    get_chat_url_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler.get_chat_url',
        return_value=url,
    )
    auth_headers_mock = mocker.patch(
        'src.ai.services.handlers.openai.OpenAIHandler._auth_headers',
        return_value=headers,
    )
    request_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._request',
        return_value=(200, payload),
    )
    parse_completion_mock = mocker.patch(
        'src.ai.services.handlers.openai.OpenAIHandler._parse_completion',
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
            'messages': [
                {
                    'role': OpenAIRole.SYSTEM,
                    'content': system_message,
                },
                {
                    'role': OpenAIRole.USER,
                    'content': user_message,
                },
            ],
        },
        timeout=handler.completion_timeout,
    )
    parse_completion_mock.assert_called_once_with(payload)
