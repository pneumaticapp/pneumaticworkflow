import requests

from src.ai.clients.model_list import list_structured_output_models


def _mock_response(mocker, status_code=200, payload=None):
    response = mocker.Mock()
    response.status_code = status_code
    response.ok = status_code < 400
    if payload is None:
        response.json.side_effect = ValueError('no json')
    else:
        response.json.return_value = payload
    return mocker.patch(
        'src.ai.clients.model_list.requests.get',
        return_value=response,
    )


def test_list__structured_outputs_only__filtered_and_sorted(mocker):

    # arrange
    payload = {
        'data': [
            {
                'id': 'vendor/plain-model',
                'name': 'Plain Model',
                'supported_parameters': ['temperature'],
            },
            {
                'id': 'vendor/model-b',
                'name': 'zeta Model',
                'supported_parameters': ['structured_outputs'],
            },
            {
                'id': 'vendor/model-a',
                'name': 'Alpha Model',
                'supported_parameters': ['tools', 'structured_outputs'],
            },
        ],
    }
    get_mock = _mock_response(mocker, payload=payload)

    # act
    result = list_structured_output_models(
        base_url='https://openrouter.ai/api/v1',
        api_key='sk-or-key',
    )

    # assert
    assert result == [
        {'slug': 'vendor/model-a', 'name': 'Alpha Model'},
        {'slug': 'vendor/model-b', 'name': 'zeta Model'},
    ]
    url = get_mock.call_args[0][0]
    assert url == 'https://openrouter.ai/api/v1/models'
    headers = get_mock.call_args[1]['headers']
    assert headers['Authorization'] == 'Bearer sk-or-key'


def test_list__no_api_key__no_auth_header(mocker):

    # arrange
    get_mock = _mock_response(mocker, payload={'data': []})

    # act
    result = list_structured_output_models(
        base_url='https://openrouter.ai/api/v1',
    )

    # assert
    assert result == []
    headers = get_mock.call_args[1]['headers']
    assert 'Authorization' not in headers


def test_list__nameless_model__slug_as_name(mocker):

    # arrange
    payload = {
        'data': [
            {
                'id': 'vendor/nameless',
                'supported_parameters': ['structured_outputs'],
            },
        ],
    }
    _mock_response(mocker, payload=payload)

    # act
    result = list_structured_output_models(
        base_url='https://openrouter.ai/api/v1',
    )

    # assert
    assert result == [
        {'slug': 'vendor/nameless', 'name': 'vendor/nameless'},
    ]


def test_list__malformed_entries__skipped(mocker):

    # arrange
    payload = {
        'data': [
            'not-a-dict',
            {
                'name': 'No slug',
                'supported_parameters': ['structured_outputs'],
            },
            {
                'id': 'vendor/ok',
                'name': 'Ok',
                'supported_parameters': ['structured_outputs'],
            },
        ],
    }
    _mock_response(mocker, payload=payload)

    # act
    result = list_structured_output_models(
        base_url='https://openrouter.ai/api/v1',
    )

    # assert
    assert result == [{'slug': 'vendor/ok', 'name': 'Ok'}]


def test_list__error_status__unknown(mocker):

    # arrange
    _mock_response(mocker, status_code=503, payload={'data': []})

    # act
    result = list_structured_output_models(
        base_url='https://openrouter.ai/api/v1',
    )

    # assert
    assert result is None


def test_list__unreachable__unknown(mocker):

    # arrange
    mocker.patch(
        'src.ai.clients.model_list.requests.get',
        side_effect=requests.ConnectionError('refused'),
    )

    # act
    result = list_structured_output_models(
        base_url='https://openrouter.ai/api/v1',
    )

    # assert
    assert result is None


def test_list__invalid_payload__unknown(mocker):

    # arrange
    _mock_response(mocker, payload={'unexpected': 'shape'})

    # act
    result = list_structured_output_models(
        base_url='https://openrouter.ai/api/v1',
    )

    # assert
    assert result is None
