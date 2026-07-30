import requests

from src.ai.clients.key_verification import verify_api_key


def _mock_response(mocker, status_code):
    response = mocker.Mock()
    response.status_code = status_code
    response.ok = status_code < 400
    return mocker.patch(
        'src.ai.clients.key_verification.requests.get',
        return_value=response,
    )


def test_verify__accepted__true(mocker):
    get_mock = _mock_response(mocker, 200)

    result = verify_api_key(
        base_url='https://openrouter.ai/api/v1',
        api_key='sk-or-key',
    )

    assert result is True
    get_mock.assert_called_once()
    url = get_mock.call_args[0][0]
    assert url == 'https://openrouter.ai/api/v1/key'
    headers = get_mock.call_args[1]['headers']
    assert headers['Authorization'] == 'Bearer sk-or-key'


def test_verify__unauthorized__false(mocker):
    _mock_response(mocker, 401)

    result = verify_api_key(
        base_url='https://openrouter.ai/api/v1',
        api_key='bad-key',
    )

    assert result is False


def test_verify__forbidden__false(mocker):
    _mock_response(mocker, 403)

    result = verify_api_key(
        base_url='https://openrouter.ai/api/v1',
        api_key='bad-key',
    )

    assert result is False


def test_verify__server_error__unknown(mocker):
    _mock_response(mocker, 503)

    result = verify_api_key(
        base_url='https://openrouter.ai/api/v1',
        api_key='sk-or-key',
    )

    assert result is None


def test_verify__unreachable__unknown(mocker):
    mocker.patch(
        'src.ai.clients.key_verification.requests.get',
        side_effect=requests.ConnectionError('refused'),
    )

    result = verify_api_key(
        base_url='https://openrouter.ai/api/v1',
        api_key='sk-or-key',
    )

    assert result is None


def test_verify__non_openrouter_host__probes_models(mocker):
    get_mock = _mock_response(mocker, 200)

    result = verify_api_key(
        base_url='https://llm.example.com/v1/',
        api_key='custom-key',
    )

    assert result is True
    url = get_mock.call_args[0][0]
    assert url == 'https://llm.example.com/v1/models'
