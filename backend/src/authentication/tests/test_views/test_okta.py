import base64
import pytest

from src.authentication.services.exceptions import AuthException
from src.authentication.services.okta import OktaService
from src.processes.tests.fixtures import create_test_owner
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_token__existent_user__authenticate(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.okta.SSOPermission.'
        'has_permission',
        return_value=True,
    )
    okta_service_init_mock = mocker.patch.object(
        OktaService,
        attribute='__init__',
        return_value=None,
    )
    email = 'test@test.test'
    user = create_test_owner(email=email)
    user_agent = 'Some/Mozilla'
    user_ip = '128.18.0.99'
    token = '!@#E213'
    authenticate_user_mock = mocker.patch(
        'src.authentication.services.okta.'
        'OktaService.authenticate_user',
        return_value=(user, token),
    )
    domain = 'dev-123456.okta.com'
    state_uuid = 'YrtkHpALzeTDnliK'
    domain_encoded = base64.urlsafe_b64encode(
        domain.encode('utf-8'),
    ).decode('utf-8').rstrip('=')
    state = f"{state_uuid[:8]}{domain_encoded}"
    auth_response = {
        'code': '4/0AbUR2VMeHxU...',
        'state': state,
    }
    identify_mock = mocker.patch(
        'src.authentication.views.okta.'
        'OktaViewSet.identify',
    )

    # act
    response = api_client.get(
        '/auth/okta/token',
        data=auth_response,
        HTTP_USER_AGENT=user_agent,
        REMOTE_ADDR=user_ip,
    )

    # assert
    assert response.status_code == 200
    assert response.data['token'] == token
    okta_service_init_mock.assert_called_once_with(domain=domain)
    authenticate_user_mock.assert_called_once_with(
        code=auth_response['code'],
        state=auth_response['state'],
        domain=domain,
        user_agent=user_agent,
        user_ip=user_ip,
    )
    identify_mock.assert_called_once_with(user)


def test_token__disable_okta_auth__permission_denied(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.okta.SSOPermission.'
        'has_permission',
        return_value=False,
    )
    okta_service_init_mock = mocker.patch.object(
        OktaService,
        attribute='__init__',
        return_value=None,
    )
    authenticate_user_mock = mocker.patch(
        'src.authentication.services.okta.'
        'OktaService.authenticate_user',
    )
    user_agent = 'Some/Mozilla'
    user_ip = '128.18.0.99'
    auth_response = {
        'code': '4/0AbUR2VMeHxU...',
        'state': 'KvpfgTSUmwtOaPny',
    }

    # act
    response = api_client.get(
        '/auth/okta/token',
        data=auth_response,
        HTTP_USER_AGENT=user_agent,
        REMOTE_ADDR=user_ip,
    )

    # assert
    assert response.status_code == 401
    okta_service_init_mock.assert_not_called()
    authenticate_user_mock.assert_not_called()


def test_token__service_exception__validation_error(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.okta.SSOPermission.'
        'has_permission',
        return_value=True,
    )
    okta_service_init_mock = mocker.patch.object(
        OktaService,
        attribute='__init__',
        return_value=None,
    )
    message = 'Some error'
    authenticate_user_mock = mocker.patch(
        'src.authentication.services.okta.'
        'OktaService.authenticate_user',
        side_effect=AuthException(message),
    )
    domain = 'dev-123456.okta.com'
    state_uuid = 'YrtkHpALzeTDnliK'
    domain_encoded = base64.urlsafe_b64encode(
        domain.encode('utf-8'),
    ).decode('utf-8').rstrip('=')
    state = f"{state_uuid[:8]}{domain_encoded}"
    auth_response = {
        'code': '4/0AbUR2VMeHxU...',
        'state': state,
    }

    # act
    response = api_client.get(
        '/auth/okta/token',
        data=auth_response,
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    okta_service_init_mock.assert_called_once_with(domain=domain)
    authenticate_user_mock.assert_called_once_with(
        code=auth_response['code'],
        state=auth_response['state'],
        domain=domain,
        user_agent=mocker.ANY,
        user_ip=mocker.ANY,
    )


def test_token__skip__code__validation_error(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.okta.SSOPermission.'
        'has_permission',
        return_value=True,
    )
    okta_service_init_mock = mocker.patch.object(
        OktaService,
        attribute='__init__',
        return_value=None,
    )
    authenticate_user_mock = mocker.patch(
        'src.authentication.services.okta.'
        'OktaService.authenticate_user',
    )
    auth_response = {
        'state': 'KvpfgTSUmwtOaPny',
    }

    # act
    response = api_client.get(
        '/auth/okta/token',
        data=auth_response,
    )

    # assert
    assert response.status_code == 400
    message = 'This field is required.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    okta_service_init_mock.assert_not_called()
    authenticate_user_mock.assert_not_called()


def test_token__code_blank__validation_error(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.okta.SSOPermission.'
        'has_permission',
        return_value=True,
    )
    okta_service_init_mock = mocker.patch.object(
        OktaService,
        attribute='__init__',
        return_value=None,
    )
    authenticate_user_mock = mocker.patch(
        'src.authentication.services.okta.'
        'OktaService.authenticate_user',
    )
    auth_response = {
        'code': '',
        'state': 'KvpfgTSUmwtOaPny',
    }

    # act
    response = api_client.get(
        '/auth/okta/token',
        data=auth_response,
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be blank.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    okta_service_init_mock.assert_not_called()
    authenticate_user_mock.assert_not_called()


def test_auth_uri__ok(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.okta.SSOPermission.'
        'has_permission',
        return_value=True,
    )
    okta_service_init_mock = mocker.patch.object(
        OktaService,
        attribute='__init__',
        return_value=None,
    )
    auth_uri = 'https://dev-123456.okta.com/oauth2/default/v1/authorize?...'
    okta_get_auth_uri_mock = mocker.patch(
        'src.authentication.services.okta.'
        'OktaService.get_auth_uri',
        return_value=auth_uri,
    )

    # act
    response = api_client.get('/auth/okta/auth-uri')

    # assert
    assert response.status_code == 200
    assert response.data['auth_uri'] == auth_uri
    okta_service_init_mock.assert_called_once_with()
    okta_get_auth_uri_mock.assert_called_once()


def test_auth_uri__disable_okta_auth__permission_denied(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.okta.SSOPermission.'
        'has_permission',
        return_value=False,
    )
    okta_service_init_mock = mocker.patch.object(
        OktaService,
        attribute='__init__',
        return_value=None,
    )
    okta_get_auth_uri_mock = mocker.patch(
        'src.authentication.services.okta.'
        'OktaService.get_auth_uri',
    )

    # act
    response = api_client.get('/auth/okta/auth-uri')

    # assert
    assert response.status_code == 401
    okta_service_init_mock.assert_not_called()
    okta_get_auth_uri_mock.assert_not_called()


def test_auth_uri__service_exception__validation_error(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.okta.SSOPermission.'
        'has_permission',
        return_value=True,
    )
    okta_service_init_mock = mocker.patch.object(
        OktaService,
        attribute='__init__',
        return_value=None,
    )
    message = 'Some error'
    okta_get_auth_uri_mock = mocker.patch(
        'src.authentication.services.okta.'
        'OktaService.get_auth_uri',
        side_effect=AuthException(message),
    )

    # act
    response = api_client.get('/auth/okta/auth-uri')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    okta_service_init_mock.assert_called_once()
    okta_get_auth_uri_mock.assert_called_once()
