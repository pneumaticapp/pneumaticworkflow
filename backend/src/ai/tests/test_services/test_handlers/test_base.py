import json

import pytest
import requests

from src.ai.enums import AIAgentActionType, AIVendor
from src.ai.exceptions import (
    AIHandlerException,
    AIProviderConnectionException,
    AIProviderInvalidResponseException,
    AIProviderRequestFailedException,
)
from src.ai.messages import MSG_AI_0001, MSG_AI_0002, MSG_AI_0003
from src.ai.models import AIAgentAction
from src.ai.services.config import AI_VENDORS_CONFIG
from src.ai.services.entities import ProviderConfig
from src.ai.services.handlers import BaseHandler, OpenAIHandler
from src.ai.tests.fixtures import create_test_agent, create_test_provider
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_get_models_url__custom_endpoint__ok():

    """ Custom models endpoint """

    # arrange
    account = create_test_account()
    provider = create_test_provider(
        account=account,
        base_url='https://api.example.com',
    )
    config = ProviderConfig(
        name='OpenAI',
        slug=AIVendor.OPENAI,
        base_url='https://api.example.com',
        handler=OpenAIHandler,
        endpoints={'models': 'v1/models'},
    )
    handler = OpenAIHandler(provider=provider, account=account, config=config)

    # act
    result = handler.get_models_url()

    # assert
    assert result == 'https://api.example.com/v1/models'


def test_get_models_url__endpoint_not_set__default():

    """ Default models endpoint """

    # arrange
    account = create_test_account()
    provider = create_test_provider(
        account=account,
        base_url='https://api.example.com',
    )
    config = ProviderConfig(
        name='OpenAI',
        slug=AIVendor.OPENAI,
        base_url='https://api.example.com',
        handler=OpenAIHandler,
        endpoints={},
    )
    handler = OpenAIHandler(provider=provider, account=account, config=config)

    # act
    result = handler.get_models_url()

    # assert
    assert result == 'https://api.example.com/models'


def test_get_models_url__empty_endpoint__default():

    """ Empty models endpoint """

    # arrange
    account = create_test_account()
    provider = create_test_provider(
        account=account,
        base_url='https://api.example.com',
    )
    config = ProviderConfig(
        name='OpenAI',
        slug=AIVendor.OPENAI,
        base_url='https://api.example.com',
        handler=OpenAIHandler,
        endpoints={'models': ''},
    )
    handler = OpenAIHandler(provider=provider, account=account, config=config)

    # act
    result = handler.get_models_url()

    # assert
    assert result == 'https://api.example.com/models'


def test_get_chat_url__custom_endpoint__ok():

    """ Custom chat endpoint """

    # arrange
    account = create_test_account()
    provider = create_test_provider(
        account=account,
        base_url='https://api.example.com',
    )
    config = ProviderConfig(
        name='OpenAI',
        slug=AIVendor.OPENAI,
        base_url='https://api.example.com',
        handler=OpenAIHandler,
        endpoints={'chat': 'v1/chat'},
    )
    handler = OpenAIHandler(provider=provider, account=account, config=config)

    # act
    result = handler.get_chat_url()

    # assert
    assert result == 'https://api.example.com/v1/chat'


def test_get_chat_url__endpoint_not_set__default():

    """ Default chat endpoint """

    # arrange
    account = create_test_account()
    provider = create_test_provider(
        account=account,
        base_url='https://api.example.com',
    )
    config = ProviderConfig(
        name='OpenAI',
        slug=AIVendor.OPENAI,
        base_url='https://api.example.com',
        handler=OpenAIHandler,
        endpoints={},
    )
    handler = OpenAIHandler(provider=provider, account=account, config=config)

    # act
    result = handler.get_chat_url()

    # assert
    assert result == 'https://api.example.com/chat/completions'


def test_get_chat_url__template_with_kwargs__ok():

    """ Endpoint template with kwargs """

    # arrange
    account = create_test_account()
    provider = create_test_provider(
        account=account,
        base_url='https://api.example.com',
    )
    config = ProviderConfig(
        name='Gemini',
        slug=AIVendor.GEMINI,
        base_url='https://api.example.com',
        handler=OpenAIHandler,
        endpoints={'chat': 'models/{model}:generateContent'},
    )
    handler = OpenAIHandler(provider=provider, account=account, config=config)

    # act
    result = handler.get_chat_url(model='gemini-2.0-flash')

    # assert
    assert result == (
        'https://api.example.com/models/gemini-2.0-flash:generateContent'
    )


def test_get_proxies__not_configured__none(settings):

    """ No proxies configured """

    # arrange
    settings.AI_HTTP_PROXY = None
    settings.AI_HTTPS_PROXY = None
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )

    # act
    result = handler._get_proxies()

    # assert
    assert result is None


def test_get_proxies__only_http__http_and_https(settings):

    """ Only HTTP proxy """

    # arrange
    http_proxy = 'http://proxy.example.com:3128'
    settings.AI_HTTP_PROXY = http_proxy
    settings.AI_HTTPS_PROXY = None
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )

    # act
    result = handler._get_proxies()

    # assert
    assert result == {'http': http_proxy, 'https': http_proxy}


def test_get_proxies__only_https__https(settings):

    """ Only HTTPS proxy """

    # arrange
    https_proxy = 'http://secure-proxy.example.com:3128'
    settings.AI_HTTP_PROXY = None
    settings.AI_HTTPS_PROXY = https_proxy
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )

    # act
    result = handler._get_proxies()

    # assert
    assert result == {'https': https_proxy}


def test_get_proxies__http_and_https__ok(settings):

    """ Both proxies """

    # arrange
    http_proxy = 'http://proxy.example.com:3128'
    https_proxy = 'http://secure-proxy.example.com:3128'
    settings.AI_HTTP_PROXY = http_proxy
    settings.AI_HTTPS_PROXY = https_proxy
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )

    # act
    result = handler._get_proxies()

    # assert
    assert result == {'http': http_proxy, 'https': https_proxy}


def test_get_safe_headers__headers_none__none():

    """ Headers is None """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )

    # act
    result = handler._get_safe_headers(headers=None)

    # assert
    assert result is None


def test_get_safe_headers__headers_empty__empty():

    """ Headers is empty """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )

    # act
    result = handler._get_safe_headers(headers={})

    # assert
    assert result == {}


def test_get_safe_headers__secret_headers__masked():

    """ Secret headers masked """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    headers = {
        'Authorization': 'Bearer sk-example',
        'api-key': 'key-1',
        'x-api-key': 'key-2',
        'x-goog-api-key': 'key-3',
        'content-type': 'application/json',
    }

    # act
    result = handler._get_safe_headers(headers=headers)

    # assert
    assert result == {
        'Authorization': '***',
        'api-key': '***',
        'x-api-key': '***',
        'x-goog-api-key': '***',
        'content-type': 'application/json',
    }


def test_get_safe_headers__upper_case_secret_header__masked():

    """ Case-insensitive masking """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    headers = {'X-Api-Key': 'key-1'}

    # act
    result = handler._get_safe_headers(headers=headers)

    # assert
    assert result == {'X-Api-Key': '***'}


def test_get_safe_headers__source_headers__not_changed():

    """ Original headers not changed """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    headers = {'Authorization': 'Bearer sk-example'}

    # act
    handler._get_safe_headers(headers=headers)

    # assert
    assert headers == {'Authorization': 'Bearer sk-example'}


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
    result = BaseHandler._parse_error(
        self=handler,
        http_status=400,
        response_data=None,
    )

    # assert
    assert result is None


def test_parse_error__error_string__ok():

    """ Error is string """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    response_data = {'error': 'Some error'}

    # act
    result = BaseHandler._parse_error(
        self=handler,
        http_status=400,
        response_data=response_data,
    )

    # assert
    assert result == 'Some error'


def test_parse_error__error_dict_with_message__ok():

    """ Error dict with message """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    response_data = {'error': {'message': 'Some error'}}

    # act
    result = BaseHandler._parse_error(
        self=handler,
        http_status=400,
        response_data=response_data,
    )

    # assert
    assert result == 'Some error'


def test_parse_error__error_dict_empty_message__none():

    """ Error dict with empty message """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    response_data = {'error': {'message': ''}}

    # act
    result = BaseHandler._parse_error(
        self=handler,
        http_status=400,
        response_data=response_data,
    )

    # assert
    assert result is None


def test_parse_error__error_dict_without_message__top_level_message():

    """ Error dict without message, top-level message """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    response_data = {'error': {'code': 1}, 'message': 'Some error'}

    # act
    result = BaseHandler._parse_error(
        self=handler,
        http_status=400,
        response_data=response_data,
    )

    # assert
    assert result == 'Some error'


def test_parse_error__top_level_message__ok():

    """ Top-level message only """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    response_data = {'message': 'Some error'}

    # act
    result = BaseHandler._parse_error(
        self=handler,
        http_status=400,
        response_data=response_data,
    )

    # assert
    assert result == 'Some error'


def test_parse_error__no_error_fields__none():

    """ No error fields """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    response_data = {'detail': 'x'}

    # act
    result = BaseHandler._parse_error(
        self=handler,
        http_status=400,
        response_data=response_data,
    )

    # assert
    assert result is None


def test_request__success__ok(mocker):

    """ Successful request """

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
    safe_headers = {'Authorization': '***'}
    data = {'model': 'gpt-4o'}
    params = {'limit': 10}
    response_data = {'id': 'chatcmpl-1'}
    json_mock = mocker.Mock(return_value=response_data)
    response = mocker.Mock(status_code=200, json=json_mock)
    request_mock = mocker.patch(
        'src.ai.services.handlers.base.requests.request',
        return_value=response,
    )
    get_proxies_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._get_proxies',
        return_value=None,
    )
    parse_error_mock = mocker.patch(
        'src.ai.services.handlers.openai.OpenAIHandler._parse_error',
    )
    get_safe_headers_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._get_safe_headers',
        return_value=safe_headers,
    )

    # act
    result = handler._request(
        method='POST',
        url=url,
        headers=headers,
        data=data,
        params=params,
        timeout=15,
    )

    # assert
    assert result == (200, response_data)
    request_mock.assert_called_once_with(
        method='POST',
        url=url,
        headers=headers,
        json=data,
        params=params,
        timeout=15,
        proxies=None,
    )
    json_mock.assert_called_once_with()
    get_proxies_mock.assert_called_once_with()
    parse_error_mock.assert_not_called()
    get_safe_headers_mock.assert_called_once_with(headers)
    action = AIAgentAction.objects.get(account=account)
    assert action.action == AIAgentActionType.REQUEST
    assert action.agent is None
    assert action.task is None
    assert json.loads(action.text) == {
        'method': 'POST',
        'url': url,
        'scheme': 'https',
        'http_status': 200,
        'headers': safe_headers,
        'data': data,
        'params': params,
        'timeout': 15,
        'proxies': False,
        'response_data': response_data,
    }


def test_request__default_params__ok(mocker):

    """ Default params """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    url = 'https://api.openai.com/v1/models'
    response_data = {'data': []}
    json_mock = mocker.Mock(return_value=response_data)
    response = mocker.Mock(status_code=200, json=json_mock)
    request_mock = mocker.patch(
        'src.ai.services.handlers.base.requests.request',
        return_value=response,
    )
    get_proxies_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._get_proxies',
        return_value=None,
    )
    parse_error_mock = mocker.patch(
        'src.ai.services.handlers.openai.OpenAIHandler._parse_error',
    )
    get_safe_headers_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._get_safe_headers',
        return_value=None,
    )

    # act
    result = handler._request(method='GET', url=url)

    # assert
    assert result == (200, response_data)
    request_mock.assert_called_once_with(
        method='GET',
        url=url,
        headers=None,
        json=None,
        params=None,
        timeout=handler.request_timeout,
        proxies=None,
    )
    json_mock.assert_called_once_with()
    get_proxies_mock.assert_called_once_with()
    parse_error_mock.assert_not_called()
    get_safe_headers_mock.assert_called_once_with(None)
    action = AIAgentAction.objects.get(account=account)
    assert json.loads(action.text) == {
        'method': 'GET',
        'url': url,
        'scheme': 'https',
        'http_status': 200,
        'headers': {},
        'data': {},
        'params': {},
        'timeout': handler.request_timeout,
        'proxies': False,
        'response_data': response_data,
    }


def test_request__custom_timeout__ok(mocker):

    """ Custom timeout """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    url = 'https://api.openai.com/v1/chat/completions'
    response_data = {'id': 'chatcmpl-1'}
    json_mock = mocker.Mock(return_value=response_data)
    response = mocker.Mock(status_code=200, json=json_mock)
    request_mock = mocker.patch(
        'src.ai.services.handlers.base.requests.request',
        return_value=response,
    )
    get_proxies_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._get_proxies',
        return_value=None,
    )
    parse_error_mock = mocker.patch(
        'src.ai.services.handlers.openai.OpenAIHandler._parse_error',
    )
    get_safe_headers_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._get_safe_headers',
        return_value=None,
    )

    # act
    result = handler._request(method='POST', url=url, timeout=200)

    # assert
    assert result == (200, response_data)
    request_mock.assert_called_once_with(
        method='POST',
        url=url,
        headers=None,
        json=None,
        params=None,
        timeout=200,
        proxies=None,
    )
    json_mock.assert_called_once_with()
    get_proxies_mock.assert_called_once_with()
    parse_error_mock.assert_not_called()
    get_safe_headers_mock.assert_called_once_with(None)
    action = AIAgentAction.objects.get(account=account)
    assert json.loads(action.text)['timeout'] == 200


def test_request__proxies_configured__ok(mocker):

    """ Proxies configured """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    url = 'https://api.openai.com/v1/models'
    proxies = {
        'http': 'http://proxy.example.com:3128',
        'https': 'http://proxy.example.com:3128',
    }
    response_data = {'data': []}
    json_mock = mocker.Mock(return_value=response_data)
    response = mocker.Mock(status_code=200, json=json_mock)
    request_mock = mocker.patch(
        'src.ai.services.handlers.base.requests.request',
        return_value=response,
    )
    get_proxies_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._get_proxies',
        return_value=proxies,
    )
    parse_error_mock = mocker.patch(
        'src.ai.services.handlers.openai.OpenAIHandler._parse_error',
    )
    get_safe_headers_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._get_safe_headers',
        return_value=None,
    )

    # act
    result = handler._request(method='GET', url=url)

    # assert
    assert result == (200, response_data)
    request_mock.assert_called_once_with(
        method='GET',
        url=url,
        headers=None,
        json=None,
        params=None,
        timeout=handler.request_timeout,
        proxies=proxies,
    )
    json_mock.assert_called_once_with()
    get_proxies_mock.assert_called_once_with()
    parse_error_mock.assert_not_called()
    get_safe_headers_mock.assert_called_once_with(None)
    action = AIAgentAction.objects.get(account=account)
    assert json.loads(action.text)['proxies'] is True


def test_request__agent_and_task__action_linked(mocker):

    """ Agent and task linked """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    agent = create_test_agent(account=account, provider=provider)
    workflow = create_test_workflow(user=user)
    task = workflow.tasks.get(number=1)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
        agent=agent,
        task=task,
    )
    url = 'https://api.openai.com/v1/models'
    response_data = {'data': []}
    json_mock = mocker.Mock(return_value=response_data)
    response = mocker.Mock(status_code=200, json=json_mock)
    request_mock = mocker.patch(
        'src.ai.services.handlers.base.requests.request',
        return_value=response,
    )
    get_proxies_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._get_proxies',
        return_value=None,
    )
    parse_error_mock = mocker.patch(
        'src.ai.services.handlers.openai.OpenAIHandler._parse_error',
    )
    get_safe_headers_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._get_safe_headers',
        return_value=None,
    )

    # act
    handler._request(method='GET', url=url)

    # assert
    request_mock.assert_called_once_with(
        method='GET',
        url=url,
        headers=None,
        json=None,
        params=None,
        timeout=handler.request_timeout,
        proxies=None,
    )
    json_mock.assert_called_once_with()
    get_proxies_mock.assert_called_once_with()
    parse_error_mock.assert_not_called()
    get_safe_headers_mock.assert_called_once_with(None)
    action = AIAgentAction.objects.get(account=account)
    assert action.action == AIAgentActionType.REQUEST
    assert action.agent == agent
    assert action.task == task


def test_request__connection_error__raise_exception(mocker):

    """ Connection error """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    url = 'https://api.openai.com/v1/models'
    request_mock = mocker.patch(
        'src.ai.services.handlers.base.requests.request',
        side_effect=requests.RequestException('Connection refused'),
    )
    get_proxies_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._get_proxies',
        return_value=None,
    )
    parse_error_mock = mocker.patch(
        'src.ai.services.handlers.openai.OpenAIHandler._parse_error',
    )
    get_safe_headers_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._get_safe_headers',
        return_value=None,
    )

    # act
    with pytest.raises(AIProviderConnectionException) as ex:
        handler._request(method='GET', url=url)

    # assert
    assert str(ex.value.message) == str(MSG_AI_0001)
    request_mock.assert_called_once_with(
        method='GET',
        url=url,
        headers=None,
        json=None,
        params=None,
        timeout=handler.request_timeout,
        proxies=None,
    )
    get_proxies_mock.assert_called_once_with()
    parse_error_mock.assert_not_called()
    get_safe_headers_mock.assert_called_once_with(None)
    action = AIAgentAction.objects.get(account=account)
    log = json.loads(action.text)
    assert log['http_status'] == 0
    assert log['response_data'] == {'error': 'Connection refused'}


def test_request__non_2xx_with_error_message__raise_exception(mocker):

    """ Non-2xx with error message """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    url = 'https://api.openai.com/v1/models'
    error_message = 'Incorrect API key provided.'
    response_data = {'error': {'message': error_message}}
    json_mock = mocker.Mock(return_value=response_data)
    response = mocker.Mock(status_code=400, json=json_mock)
    request_mock = mocker.patch(
        'src.ai.services.handlers.base.requests.request',
        return_value=response,
    )
    get_proxies_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._get_proxies',
        return_value=None,
    )
    parse_error_mock = mocker.patch(
        'src.ai.services.handlers.openai.OpenAIHandler._parse_error',
        return_value=error_message,
    )
    get_safe_headers_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._get_safe_headers',
        return_value=None,
    )

    # act
    with pytest.raises(AIHandlerException) as ex:
        handler._request(method='GET', url=url)

    # assert
    assert ex.value.message == '"Incorrect API key provided." (400)'
    request_mock.assert_called_once_with(
        method='GET',
        url=url,
        headers=None,
        json=None,
        params=None,
        timeout=handler.request_timeout,
        proxies=None,
    )
    json_mock.assert_called_once_with()
    get_proxies_mock.assert_called_once_with()
    parse_error_mock.assert_called_once_with(
        http_status=400,
        response_data=response_data,
    )
    get_safe_headers_mock.assert_called_once_with(None)
    action = AIAgentAction.objects.get(account=account)
    log = json.loads(action.text)
    assert log['http_status'] == 400
    assert log['response_data'] == response_data


def test_request__non_2xx_without_error_message__raise_exception(mocker):

    """ Non-2xx without error message """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    url = 'https://api.openai.com/v1/models'
    response_data = {'detail': 'Internal error'}
    json_mock = mocker.Mock(return_value=response_data)
    response = mocker.Mock(status_code=500, json=json_mock)
    request_mock = mocker.patch(
        'src.ai.services.handlers.base.requests.request',
        return_value=response,
    )
    get_proxies_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._get_proxies',
        return_value=None,
    )
    parse_error_mock = mocker.patch(
        'src.ai.services.handlers.openai.OpenAIHandler._parse_error',
        return_value=None,
    )
    get_safe_headers_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._get_safe_headers',
        return_value=None,
    )

    # act
    with pytest.raises(AIProviderRequestFailedException) as ex:
        handler._request(method='GET', url=url)

    # assert
    assert str(ex.value.message) == str(MSG_AI_0002)
    request_mock.assert_called_once_with(
        method='GET',
        url=url,
        headers=None,
        json=None,
        params=None,
        timeout=handler.request_timeout,
        proxies=None,
    )
    json_mock.assert_called_once_with()
    get_proxies_mock.assert_called_once_with()
    parse_error_mock.assert_called_once_with(
        http_status=500,
        response_data=response_data,
    )
    get_safe_headers_mock.assert_called_once_with(None)
    action = AIAgentAction.objects.get(account=account)
    log = json.loads(action.text)
    assert log['http_status'] == 500
    assert log['response_data'] == response_data


def test_request__non_2xx_non_json_body__raise_exception(mocker):

    """ Non-2xx with non-JSON body """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    url = 'https://api.openai.com/v1/models'
    json_mock = mocker.Mock(side_effect=ValueError)
    response = mocker.Mock(
        status_code=502,
        json=json_mock,
        text='Bad gateway',
    )
    request_mock = mocker.patch(
        'src.ai.services.handlers.base.requests.request',
        return_value=response,
    )
    get_proxies_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._get_proxies',
        return_value=None,
    )
    parse_error_mock = mocker.patch(
        'src.ai.services.handlers.openai.OpenAIHandler._parse_error',
        return_value=None,
    )
    get_safe_headers_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._get_safe_headers',
        return_value=None,
    )

    # act
    with pytest.raises(AIProviderRequestFailedException) as ex:
        handler._request(method='GET', url=url)

    # assert
    assert str(ex.value.message) == str(MSG_AI_0002)
    request_mock.assert_called_once_with(
        method='GET',
        url=url,
        headers=None,
        json=None,
        params=None,
        timeout=handler.request_timeout,
        proxies=None,
    )
    json_mock.assert_called_once_with()
    get_proxies_mock.assert_called_once_with()
    parse_error_mock.assert_called_once_with(
        http_status=502,
        response_data={'body': 'Bad gateway'},
    )
    get_safe_headers_mock.assert_called_once_with(None)
    action = AIAgentAction.objects.get(account=account)
    log = json.loads(action.text)
    assert log['http_status'] == 502
    assert log['response_data'] == {'body': 'Bad gateway'}


def test_request__2xx_invalid_json__raise_exception(mocker):

    """ 2xx with invalid JSON """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    url = 'https://api.openai.com/v1/models'
    json_mock = mocker.Mock(side_effect=ValueError)
    response = mocker.Mock(
        status_code=200,
        json=json_mock,
        text='not json',
    )
    request_mock = mocker.patch(
        'src.ai.services.handlers.base.requests.request',
        return_value=response,
    )
    get_proxies_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._get_proxies',
        return_value=None,
    )
    parse_error_mock = mocker.patch(
        'src.ai.services.handlers.openai.OpenAIHandler._parse_error',
    )
    get_safe_headers_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler._get_safe_headers',
        return_value=None,
    )

    # act
    with pytest.raises(AIProviderInvalidResponseException) as ex:
        handler._request(method='GET', url=url)

    # assert
    assert str(ex.value.message) == str(MSG_AI_0003)
    request_mock.assert_called_once_with(
        method='GET',
        url=url,
        headers=None,
        json=None,
        params=None,
        timeout=handler.request_timeout,
        proxies=None,
    )
    json_mock.assert_called_once_with()
    get_proxies_mock.assert_called_once_with()
    parse_error_mock.assert_not_called()
    get_safe_headers_mock.assert_called_once_with(None)
    action = AIAgentAction.objects.get(account=account)
    log = json.loads(action.text)
    assert log['http_status'] == 200
    assert log['response_data'] == {'body': 'not json'}


def test_get_models__models_received__ok(mocker):

    """ Models received """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenAIHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
    )
    url = 'https://api.openai.com/v1/models'
    headers = {'Authorization': 'Bearer sk-example'}
    payload = {'data': [{'id': 'gpt-4o'}]}
    models = [{'slug': 'gpt-4o', 'name': 'gpt-4o'}]
    get_models_url_mock = mocker.patch(
        'src.ai.services.handlers.base.BaseHandler.get_models_url',
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
    parse_models_mock = mocker.patch(
        'src.ai.services.handlers.openai.OpenAIHandler._parse_models',
        return_value=models,
    )

    # act
    result = handler.get_models()

    # assert
    assert result == models
    get_models_url_mock.assert_called_once_with()
    auth_headers_mock.assert_called_once_with()
    request_mock.assert_called_once_with(
        method='GET',
        url=url,
        headers=headers,
        params=None,
    )
    parse_models_mock.assert_called_once_with(payload)
