import pytest
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
)
from src.logs.models import AccountEvent
from src.logs.enums import (
    AccountEventType,
    AccountEventStatus,
    RequestDirection,
)
from src.authentication.enums import AuthTokenType


pytestmark = pytest.mark.django_db


def test__user_token_auth__skip(api_client, mocker):

    # arrange
    account = create_test_account(log_api_requests=True)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.data',
        return_value={
            'user_id': user.id,
            'is_superuser': False,
            'for_api_key': False
        }
    )
    path = '/accounts/account'

    # act
    response = api_client.get(path)

    # assert
    assert response.status_code == 200
    assert not AccountEvent.objects.all().exists()


def test__api_token_auth__ok(api_client, mocker):

    # arrange
    account = create_test_account(log_api_requests=True)
    user = create_test_user(account=account)
    api_client.token_authenticate(user, token_type=AuthTokenType.API)
    mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.data',
        return_value={
            'user_id': user.id,
            'is_superuser': False,
            'for_api_key': True
        }
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
        auth_token=user.apikey.key,
        scheme='http',
        method='GET',
        path=path,
        event_type=AccountEventType.API,
        status=AccountEventStatus.SUCCESS,
        direction=RequestDirection.RECEIVED,
        http_status=200,
    )


def test__get_request_with_data__ok(api_client, mocker):

    # arrange
    account = create_test_account(log_api_requests=True)
    user = create_test_user(account=account)
    api_client.token_authenticate(user, token_type=AuthTokenType.API)
    mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.data',
        return_value={
            'user_id': user.id,
            'is_superuser': False,
            'for_api_key': True
        }
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
        auth_token=user.apikey.key,
        scheme='http',
        method='GET',
        path=path,
        event_type=AccountEventType.API,
        status=AccountEventStatus.SUCCESS,
        http_status=200,
        direction=RequestDirection.RECEIVED,
        request_data=params,
    )


def test__get_request_with_query_string__ok(api_client, mocker):

    # arrange
    account = create_test_account(log_api_requests=True)
    user = create_test_user(account=account)
    api_client.token_authenticate(user, token_type=AuthTokenType.API)
    mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.data',
        return_value={
            'user_id': user.id,
            'is_superuser': False,
            'for_api_key': True
        }
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
        auth_token=user.apikey.key,
        scheme='http',
        method='GET',
        path=path,
        event_type=AccountEventType.API,
        status=AccountEventStatus.SUCCESS,
        http_status=200,
        direction=RequestDirection.RECEIVED,
        request_data={'key_1': 'Value1,Value2', 'key_2': '123'},
    )


def test__post_request_with_data__ok(api_client, mocker):

    # arrange
    account = create_test_account(log_api_requests=True)
    user = create_test_user(account=account)
    api_client.token_authenticate(user, token_type=AuthTokenType.API)
    mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.data',
        return_value={
            'user_id': user.id,
            'is_superuser': False,
            'for_api_key': True
        }
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
        auth_token=user.apikey.key,
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


def test__head_request__skip(api_client, mocker):

    # arrange
    account = create_test_account(log_api_requests=True)
    user = create_test_user(account=account)
    api_client.token_authenticate(user, token_type=AuthTokenType.API)
    mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.data',
        return_value={
            'user_id': user.id,
            'is_superuser': False,
            'for_api_key': True
        }
    )
    path = f'/accounts/users/{user.id}/delete'
    data = {'key_1': 'Value1,Value2', 'key_2': '123'}

    # act
    response = api_client.head(path, data=data)

    # assert
    assert response.status_code == 405
    assert not AccountEvent.objects.all().exists()


def test__options_request__skip(api_client, mocker):

    # arrange
    account = create_test_account(log_api_requests=True)
    user = create_test_user(account=account)
    api_client.token_authenticate(user, token_type=AuthTokenType.API)
    mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.data',
        return_value={
            'user_id': user.id,
            'is_superuser': False,
            'for_api_key': True
        }
    )
    path = f'/accounts/users/{user.id}/delete'
    data = {'key_1': 'Value1,Value2', 'key_2': '123'}

    # act
    response = api_client.options(path, data=data)

    # assert
    assert response.status_code == 200
    assert not AccountEvent.objects.all().exists()


def test__disable_log_api_requests__skip(api_client, mocker):

    # arrange
    account = create_test_account(log_api_requests=False)
    user = create_test_user(account=account)
    api_client.token_authenticate(user, token_type=AuthTokenType.API)
    mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.data',
        return_value={
            'user_id': user.id,
            'is_superuser': False,
            'for_api_key': True
        }
    )

    # act
    response = api_client.get('/accounts/account')

    # assert
    assert response.status_code == 200
    assert not AccountEvent.objects.all().exists()


def test__bad_request__save_error(api_client, mocker):

    # arrange
    account = create_test_account(log_api_requests=True)
    user = create_test_user(account=account)
    api_client.token_authenticate(user, token_type=AuthTokenType.API)
    mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.data',
        return_value={
            'user_id': user.id,
            'is_superuser': False,
            'for_api_key': True
        }
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
        auth_token=user.apikey.key,
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
