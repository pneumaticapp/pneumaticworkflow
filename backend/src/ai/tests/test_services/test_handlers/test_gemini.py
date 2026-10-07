import pytest

from src.ai.enums import AIVendor
from src.ai.services.config import AI_VENDORS_CONFIG
from src.ai.services.handlers import GeminiHandler
from src.ai.tests.fixtures import create_test_provider
from src.processes.tests.fixtures import create_test_account

pytestmark = pytest.mark.django_db


def test_auth_headers__api_key__ok():

    """ Auth headers """

    # arrange
    account = create_test_account()
    api_key = 'AIza-example'
    provider = create_test_provider(account=account, api_key=api_key)
    handler = GeminiHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.GEMINI],
    )

    # act
    result = handler._auth_headers()

    # assert
    assert result == {
        'x-goog-api-key': api_key,
        'content-type': 'application/json',
    }


def test_is_chat_model__generate_content__true():

    """ Supports generateContent """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = GeminiHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.GEMINI],
    )
    item = {
        'name': 'models/gemini-2.0-flash',
        'supportedGenerationMethods': ['generateContent', 'countTokens'],
    }

    # act
    result = handler._is_chat_model(item=item)

    # assert
    assert result is True


def test_is_chat_model__only_embed_content__false():

    """ Not supports generateContent """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = GeminiHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.GEMINI],
    )
    item = {
        'name': 'models/gemini-embedding-001',
        'supportedGenerationMethods': ['embedContent'],
    }

    # act
    result = handler._is_chat_model(item=item)

    # assert
    assert result is False


def test_is_chat_model__methods_not_set__false():

    """ Methods missing """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = GeminiHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.GEMINI],
    )
    item = {'name': 'models/gemini-2.0-flash'}

    # act
    result = handler._is_chat_model(item=item)

    # assert
    assert result is False


def test_is_chat_model__methods_none__false():

    """ Methods is None """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = GeminiHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.GEMINI],
    )
    item = {
        'name': 'models/gemini-2.0-flash',
        'supportedGenerationMethods': None,
    }

    # act
    result = handler._is_chat_model(item=item)

    # assert
    assert result is False


def test_parse_completion__multiple_text_parts__joined():

    """ Multiple text parts """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = GeminiHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.GEMINI],
    )
    payload = {
        'candidates': [
            {
                'content': {
                    'parts': [{'text': 'Hello'}, {'text': ' world!'}],
                    'role': 'model',
                },
                'finishReason': 'STOP',
            },
        ],
    }

    # act
    result = handler._parse_completion(payload=payload)

    # assert
    assert result == 'Hello world!'


def test_parse_completion__parts_without_text__skip():

    """ Parts without text skipped """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = GeminiHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.GEMINI],
    )
    payload = {
        'candidates': [
            {
                'content': {
                    'parts': [
                        {'text': 'Hello!'},
                        {'functionCall': {'name': 'search'}},
                    ],
                    'role': 'model',
                },
            },
        ],
    }

    # act
    result = handler._parse_completion(payload=payload)

    # assert
    assert result == 'Hello!'


def test_parse_completion__empty_parts__empty_string():

    """ Empty parts """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = GeminiHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.GEMINI],
    )
    payload = {'candidates': [{'content': {'parts': [], 'role': 'model'}}]}

    # act
    result = handler._parse_completion(payload=payload)

    # assert
    assert result == ''


def test_parse_error__gemini_error_body__ok():

    """ Gemini error body """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = GeminiHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.GEMINI],
    )
    response_data = {
        'error': {
            'code': 400,
            'message': 'API key not valid.',
            'status': 'INVALID_ARGUMENT',
        },
    }

    # act
    result = handler._parse_error(
        http_status=400,
        response_data=response_data,
    )

    # assert
    assert result == 'API key not valid.'


def test_parse_error__response_data_not_dict__none():

    """ Response data is not dict """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = GeminiHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.GEMINI],
    )

    # act
    result = handler._parse_error(http_status=500, response_data=None)

    # assert
    assert result is None


def test_parse_models__chat_model__prefix_removed(mocker):

    """ Chat model parsed """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = GeminiHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.GEMINI],
    )
    item = {
        'name': 'models/gemini-2.0-flash',
        'displayName': 'Gemini 2.0 Flash',
    }
    payload = {'models': [item], 'nextPageToken': ''}
    is_chat_model_mock = mocker.patch(
        'src.ai.services.handlers.gemini.GeminiHandler._is_chat_model',
        return_value=True,
    )

    # act
    result = handler._parse_models(payload=payload)

    # assert
    assert result == [
        {'slug': 'gemini-2.0-flash', 'name': 'Gemini 2.0 Flash'},
    ]
    is_chat_model_mock.assert_called_once_with(item)


def test_parse_models__name_without_prefix__ok(mocker):

    """ Name without prefix """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = GeminiHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.GEMINI],
    )
    item = {'name': 'gemini-2.0-flash', 'displayName': 'Gemini 2.0 Flash'}
    payload = {'models': [item]}
    is_chat_model_mock = mocker.patch(
        'src.ai.services.handlers.gemini.GeminiHandler._is_chat_model',
        return_value=True,
    )

    # act
    result = handler._parse_models(payload=payload)

    # assert
    assert result == [
        {'slug': 'gemini-2.0-flash', 'name': 'Gemini 2.0 Flash'},
    ]
    is_chat_model_mock.assert_called_once_with(item)


def test_parse_models__non_chat_model__skip(mocker):

    """ Non-chat model skipped """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = GeminiHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.GEMINI],
    )
    item = {
        'name': 'models/gemini-embedding-001',
        'displayName': 'Gemini Embedding 001',
    }
    payload = {'models': [item]}
    is_chat_model_mock = mocker.patch(
        'src.ai.services.handlers.gemini.GeminiHandler._is_chat_model',
        return_value=False,
    )

    # act
    result = handler._parse_models(payload=payload)

    # assert
    assert result == []
    is_chat_model_mock.assert_called_once_with(item)


def test_parse_models__models_not_set__empty_list(mocker):

    """ Models key missing """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = GeminiHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.GEMINI],
    )
    payload = {}
    is_chat_model_mock = mocker.patch(
        'src.ai.services.handlers.gemini.GeminiHandler._is_chat_model',
    )

    # act
    result = handler._parse_models(payload=payload)

    # assert
    assert result == []
    is_chat_model_mock.assert_not_called()


def test_parse_models__models_none__empty_list(mocker):

    """ Models is None """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = GeminiHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.GEMINI],
    )
    payload = {'models': None}
    is_chat_model_mock = mocker.patch(
        'src.ai.services.handlers.gemini.GeminiHandler._is_chat_model',
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
    handler = GeminiHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.GEMINI],
    )
    url = (
        'https://generativelanguage.googleapis.com/v1beta'
        '/models/gemini-2.0-flash:generateContent'
    )
    headers = {'x-goog-api-key': 'AIza-example'}
    system_message = 'You are helpful.'
    user_message = 'Say "Hello world"'
    model = 'gemini-2.0-flash'
    payload = {'candidates': [{'content': {'parts': [{'text': 'Hi'}]}}]}
    get_chat_url_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler.get_chat_url',
        return_value=url,
    )
    auth_headers_mock = mocker.patch(
        'src.ai.services.handlers.gemini.GeminiHandler._auth_headers',
        return_value=headers,
    )
    request_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._request',
        return_value=(200, payload),
    )
    parse_completion_mock = mocker.patch(
        'src.ai.services.handlers.gemini.GeminiHandler._parse_completion',
        return_value='Hi',
    )

    # act
    result = handler.get_completion(
        system_message=system_message,
        user_message=user_message,
        model=model,
    )

    # assert
    assert result == 'Hi'
    get_chat_url_mock.assert_called_once_with(model=model)
    auth_headers_mock.assert_called_once_with()
    request_mock.assert_called_once_with(
        method='POST',
        url=url,
        headers=headers,
        data={
            'systemInstruction': {
                'parts': [{'text': system_message}],
            },
            'contents': [
                {
                    'role': 'user',
                    'parts': [{'text': user_message}],
                },
            ],
        },
        timeout=handler.completion_timeout,
    )
    parse_completion_mock.assert_called_once_with(payload)
