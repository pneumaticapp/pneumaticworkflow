import pytest

from src.authentication.enums import AuthTokenType
from src.logs.enums import (
    AccountEventStatus,
    AccountEventType,
    RequestDirection,
)
from src.logs.models import AccountEvent
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_middleware__user_token_auth__skip(api_client, mocker):

    # arrange
    account = create_test_account(log_api_requests=True)
    user = create_test_owner(account=account)
    token = api_client.token_authenticate(user)
    token_data_mock = mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.data',
        return_value={
            'user_id': user.id,
            'is_superuser': False,
            'for_api_key': False,
        },
    )
    path = '/accounts/account'

    # act
    response = api_client.get(path)

    # assert
    assert response.status_code == 200
    assert not AccountEvent.objects.all().exists()
    token_data_mock.assert_has_calls([mocker.call(token)] * 3)


def test_middleware__api_token_auth__ok(api_client, mocker):

    # arrange
    account = create_test_account(log_api_requests=True)
    user = create_test_owner(account=account)
    token = api_client.token_authenticate(user, token_type=AuthTokenType.API)
    token_data_mock = mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.data',
        return_value={
            'user_id': user.id,
            'is_superuser': False,
            'for_api_key': True,
        },
    )
    path = '/accounts/account'

    # act
    response = api_client.get(path)

    # assert
    assert response.status_code == 200
    assert AccountEvent.objects.get(
        user=user,
        account=user.account,
        ip='192.168.0.1',
        user_agent='Firefox',
        auth_token=token,
        scheme='http',
        method='GET',
        path=path,
        event_type=AccountEventType.API,
        status=AccountEventStatus.SUCCESS,
        direction=RequestDirection.RECEIVED,
        http_status=200,
    )
    token_data_mock.assert_has_calls([mocker.call(token)] * 3)


def test_middleware__get_request_with_data__ok(api_client, mocker):

    # arrange
    account = create_test_account(log_api_requests=True)
    user = create_test_owner(account=account)
    token = api_client.token_authenticate(user, token_type=AuthTokenType.API)
    token_data_mock = mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.data',
        return_value={
            'user_id': user.id,
            'is_superuser': False,
            'for_api_key': True,
        },
    )
    path = '/accounts/account'
    params = {'key_1': 'Value1,Value2', 'key_2': '123'}

    # act
    response = api_client.get(path, data=params)

    # assert
    assert response.status_code == 200
    assert AccountEvent.objects.get(
        user=user,
        account=user.account,
        ip='192.168.0.1',
        user_agent='Firefox',
        auth_token=token,
        scheme='http',
        method='GET',
        path=path,
        event_type=AccountEventType.API,
        status=AccountEventStatus.SUCCESS,
        http_status=200,
        direction=RequestDirection.RECEIVED,
        request_data=params,
    )
    token_data_mock.assert_has_calls([mocker.call(token)] * 3)


def test_middleware__get_request_with_query_string__ok(api_client, mocker):

    # arrange
    account = create_test_account(log_api_requests=True)
    user = create_test_owner(account=account)
    token = api_client.token_authenticate(user, token_type=AuthTokenType.API)
    token_data_mock = mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.data',
        return_value={
            'user_id': user.id,
            'is_superuser': False,
            'for_api_key': True,
        },
    )
    path = '/accounts/account'

    # act
    response = api_client.get(f'{path}?key_1=Value1,Value2&key_2=123')

    # assert
    assert response.status_code == 200
    assert AccountEvent.objects.get(
        user=user,
        account=user.account,
        ip='192.168.0.1',
        user_agent='Firefox',
        auth_token=token,
        scheme='http',
        method='GET',
        path=path,
        event_type=AccountEventType.API,
        status=AccountEventStatus.SUCCESS,
        http_status=200,
        direction=RequestDirection.RECEIVED,
        request_data={'key_1': 'Value1,Value2', 'key_2': '123'},
    )
    token_data_mock.assert_has_calls([mocker.call(token)] * 3)


def test_middleware__post_request_with_data__ok(api_client, mocker):

    # arrange
    account = create_test_account(log_api_requests=True)
    user = create_test_owner(account=account)
    token = api_client.token_authenticate(user, token_type=AuthTokenType.API)
    token_data_mock = mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.data',
        return_value={
            'user_id': user.id,
            'is_superuser': False,
            'for_api_key': True,
        },
    )
    path = '/accounts/notifications/read'
    data = {'notifications': [1, 2]}

    # act
    response = api_client.post(path, data=data)

    # assert
    assert response.status_code == 204
    event = AccountEvent.objects.get(
        user=user,
        account=user.account,
        ip='192.168.0.1',
        user_agent='Firefox',
        auth_token=token,
        scheme='http',
        method='POST',
        path=path,
        event_type=AccountEventType.API,
        status=AccountEventStatus.SUCCESS,
        direction=RequestDirection.RECEIVED,
        http_status=204,
    )
    assert event.request_data == data
    assert event.response_data is None
    token_data_mock.assert_has_calls([mocker.call(token)] * 3)


def test_middleware__head_request__skip(api_client, mocker):

    # arrange
    account = create_test_account(log_api_requests=True)
    user = create_test_owner(account=account)
    token_data_mock = mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.data',
        return_value={
            'user_id': user.id,
            'is_superuser': False,
            'for_api_key': True,
        },
    )
    token = api_client.token_authenticate(user, token_type=AuthTokenType.API)

    # act
    response = api_client.head(
        path=f'/accounts/users/{user.id}/toggle-admin',
        data={
            'key_1': 'Value1,Value2',
            'key_2': '123',
        },
    )
    # assert
    assert response.status_code == 405
    assert not AccountEvent.objects.all().exists()
    token_data_mock.assert_has_calls([mocker.call(token)] * 2)


def test_middleware__options_request__skip(api_client, mocker):

    # arrange
    account = create_test_account(log_api_requests=True)
    user = create_test_owner(account=account)
    token = api_client.token_authenticate(user, token_type=AuthTokenType.API)
    token_data_mock = mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.data',
        return_value={
            'user_id': user.id,
            'is_superuser': False,
            'for_api_key': True,
        },
    )

    # act
    response = api_client.options(
        path=f'/accounts/users/{user.id}/toggle-admin',
        data={
            'key_1': 'Value1,Value2',
            'key_2': '123',
        },
    )

    # assert
    assert response.status_code == 200
    assert not AccountEvent.objects.all().exists()
    token_data_mock.assert_has_calls([mocker.call(token)] * 2)


def test_middleware__disable_log_api_requests__skip(api_client, mocker):

    # arrange
    account = create_test_account(log_api_requests=False)
    user = create_test_owner(account=account)
    token = api_client.token_authenticate(user, token_type=AuthTokenType.API)
    token_data_mock = mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.data',
        return_value={
            'user_id': user.id,
            'is_superuser': False,
            'for_api_key': True,
        },
    )

    # act
    response = api_client.get('/accounts/account')

    # assert
    assert response.status_code == 200
    assert not AccountEvent.objects.all().exists()
    token_data_mock.assert_has_calls([mocker.call(token)] * 2)


def test_middleware__bad_request__save_error(api_client, mocker):

    # arrange
    account = create_test_account(log_api_requests=True)
    user = create_test_owner(account=account)
    token = api_client.token_authenticate(user, token_type=AuthTokenType.API)
    token_data_mock = mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.data',
        return_value={
            'user_id': user.id,
            'is_superuser': False,
            'for_api_key': True,
        },
    )
    path = '/templates'
    data = {'kickoff': {}, 'tasks': [], 'is_active': True}

    # act
    response = api_client.post(path, data=data)

    # assert
    assert response.status_code == 400
    event = AccountEvent.objects.get(
        user=user,
        account=user.account,
        ip='192.168.0.1',
        user_agent='Firefox',
        auth_token=token,
        scheme='http',
        method='POST',
        path=path,
        event_type=AccountEventType.API,
        status=AccountEventStatus.FAILED,
        direction=RequestDirection.RECEIVED,
        http_status=400,
    )
    assert event.request_data == data
    assert event.response_data['code'] == 'validation_error'
    assert event.response_data['message'] == 'This field is required.'
    assert event.response_data['details']['name'] == 'name'
    assert event.response_data['details']['reason'] == (
        'This field is required.'
    )
    token_data_mock.assert_has_calls([mocker.call(token)] * 3)
