import json

import pytest
import requests

from src.ai.clients.chat_completions import (
    AIClientError,
    AIEmptyResponseError,
    AIInvalidJsonError,
    AIRequestError,
    AITruncatedOutputError,
    ChatCompletionsClient,
    extract_json,
)

SCHEMA = {'type': 'object', 'properties': {}}


def _client(**kwargs):
    return ChatCompletionsClient(
        base_url='https://openrouter.test/api/v1/',
        api_key='test-key',
        **kwargs,
    )


def _response(mocker, status=200, payload=None, text=''):
    response = mocker.Mock()
    response.ok = status < 400
    response.status_code = status
    response.text = text
    response.json.return_value = payload
    return response


def _completion(mocker, content, finish_reason='stop'):
    return _response(
        mocker,
        payload={
            'choices': [
                {
                    'finish_reason': finish_reason,
                    'message': {'content': content},
                },
            ],
        },
    )


@pytest.fixture(autouse=True)
def no_sleep(mocker):
    return mocker.patch(
        'src.ai.clients.chat_completions.time.sleep',
    )


def test_call_model__plain_prompt__returns_content(mocker):
    post = mocker.patch(
        'src.ai.clients.chat_completions.requests.post',
        return_value=_completion(mocker, 'hello'),
    )

    result = _client().call_model(model='m', user_content='hi')

    assert result == 'hello'
    body = post.call_args[1]['json']
    assert body['model'] == 'm'
    assert body['messages'] == [{'role': 'user', 'content': 'hi'}]
    assert 'response_format' not in body
    url = post.call_args[0][0]
    assert url == 'https://openrouter.test/api/v1/chat/completions'


def test_call_model__system_prompt__prepended_as_system_message(mocker):
    post = mocker.patch(
        'src.ai.clients.chat_completions.requests.post',
        return_value=_completion(mocker, 'ok'),
    )

    _client().call_model(
        model='m',
        user_content='hi',
        system_prompt='be brief',
        temperature=0.2,
        max_tokens=100,
    )

    body = post.call_args[1]['json']
    assert body['messages'][0] == {
        'role': 'system',
        'content': 'be brief',
    }
    assert body['temperature'] == 0.2
    assert body['max_tokens'] == 100


def test_call_model__schema__sends_response_format_and_parses(mocker):
    post = mocker.patch(
        'src.ai.clients.chat_completions.requests.post',
        return_value=_completion(mocker, '{"a": 1}'),
    )

    result = _client().call_model(
        model='m', user_content='hi', schema=SCHEMA,
    )

    assert result == {'a': 1}
    response_format = post.call_args[1]['json']['response_format']
    assert response_format['type'] == 'json_schema'
    assert response_format['json_schema']['strict'] is True
    assert response_format['json_schema']['schema'] == SCHEMA


def test_call_model__schema_rejected__falls_back_to_prompt_and_parse(
    mocker, no_sleep,
):
    rejected = _response(
        mocker, status=400,
        text='response_format is not supported for this model',
    )
    fenced = _completion(mocker, '```json\n{"a": 1}\n```')
    post = mocker.patch(
        'src.ai.clients.chat_completions.requests.post',
        side_effect=[rejected, fenced],
    )

    result = _client().call_model(
        model='m', user_content='hi', schema=SCHEMA,
    )

    assert result == {'a': 1}
    assert post.call_count == 2
    assert 'response_format' not in post.call_args[1]['json']
    # the fallback is not a retry — no backoff
    no_sleep.assert_not_called()


def test_call_model__plain_400__raises_without_retry(mocker):
    post = mocker.patch(
        'src.ai.clients.chat_completions.requests.post',
        return_value=_response(mocker, status=400, text='bad request'),
    )

    with pytest.raises(AIRequestError) as ex:
        _client().call_model(model='m', user_content='hi', schema=SCHEMA)

    assert ex.value.status == 400
    assert post.call_count == 1


def test_call_model__retryable_status__retried_with_backoff(
    mocker, no_sleep,
):
    post = mocker.patch(
        'src.ai.clients.chat_completions.requests.post',
        side_effect=[
            _response(mocker, status=429, text='rate limited'),
            _completion(mocker, 'ok'),
        ],
    )

    result = _client().call_model(model='m', user_content='hi')

    assert result == 'ok'
    assert post.call_count == 2
    no_sleep.assert_called_once_with(0.5)


def test_call_model__error_embedded_in_200_body__retried(mocker):
    embedded = _response(
        mocker,
        payload={'error': {'code': 502, 'message': 'provider down'}},
    )
    post = mocker.patch(
        'src.ai.clients.chat_completions.requests.post',
        side_effect=[embedded, _completion(mocker, 'ok')],
    )

    result = _client().call_model(model='m', user_content='hi')

    assert result == 'ok'
    assert post.call_count == 2


def test_call_model__retries_exhausted__raises_last_error(mocker):
    post = mocker.patch(
        'src.ai.clients.chat_completions.requests.post',
        return_value=_response(mocker, status=503, text='down'),
    )

    with pytest.raises(AIRequestError) as ex:
        _client().call_model(model='m', user_content='hi')

    assert ex.value.status == 503
    assert post.call_count == 3


def test_call_model__timeout__retried_then_raised(mocker):
    post = mocker.patch(
        'src.ai.clients.chat_completions.requests.post',
        side_effect=requests.Timeout('timed out'),
    )

    with pytest.raises(requests.Timeout):
        _client().call_model(model='m', user_content='hi')

    assert post.call_count == 3


def test_call_model__truncated_output__hard_error_no_retry(mocker):
    post = mocker.patch(
        'src.ai.clients.chat_completions.requests.post',
        return_value=_completion(mocker, 'partial', finish_reason='length'),
    )

    with pytest.raises(AITruncatedOutputError):
        _client().call_model(model='m', user_content='hi')

    assert post.call_count == 1


def test_call_model__empty_content__raises(mocker):
    mocker.patch(
        'src.ai.clients.chat_completions.requests.post',
        return_value=_response(mocker, payload={'choices': []}),
    )

    with pytest.raises(AIEmptyResponseError):
        _client().call_model(model='m', user_content='hi')


def test_call_model__missing_api_key__raises():
    with pytest.raises(AIClientError):
        ChatCompletionsClient(base_url='https://x.test', api_key='')


def test_extract_json__plain_object__parsed():
    assert extract_json('{"a": 1}') == {'a': 1}


def test_extract_json__fenced_object__parsed():
    assert extract_json('```json\n{"a": 1}\n```') == {'a': 1}


def test_extract_json__prose_wrapped_object__parsed():
    content = 'Here is the answer:\n{"a": {"b": 2}}\nHope that helps!'

    assert extract_json(content) == {'a': {'b': 2}}


def test_extract_json__no_json__raises():
    with pytest.raises(AIInvalidJsonError):
        extract_json('I cannot answer that.')


def test_extract_json__valid_json_with_unbalanced_prose__parsed():
    content = json.dumps({'text': 'closing brace } inside a string'})

    assert extract_json(content) == {
        'text': 'closing brace } inside a string',
    }
