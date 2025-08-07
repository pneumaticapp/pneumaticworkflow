import pytest
from pneumatic_backend.authentication.services.exceptions import (
    AuthException
)
from pneumatic_backend.authentication.services.microsoft import (
    MicrosoftAuthService
)
from pneumatic_backend.authentication.entities import UserData
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user
)
from pneumatic_backend.utils.validation import ErrorCode


pytestmark = pytest.mark.django_db


def test_token__existent_user__authenticate(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.MSAuthPermission.'
        'has_permission',
        return_value=True
    )
    ms_service_init_mock = mocker.patch.object(
        MicrosoftAuthService,
        attribute='__init__',
        return_value=None
    )
    email = 'test@test.test'
    user = create_test_user(email=email)
    user_data = UserData(
        email=email,
        first_name='',
        last_name='',
        company_name='',
        photo=None,
        job_title=''
    )
    ms_get_user_data_mock = mocker.patch(
        'pneumatic_backend.authentication.services.microsoft.'
        'MicrosoftAuthService.get_user_data',
        return_value=user_data
    )
    user_agent = 'Some/Mozilla'
    user_ip = '128.18.0.99'
    token = '!@#E213'
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.'
        'AuthService.get_auth_token',
        return_value=token
    )
    save_tokens_for_user_mock = mocker.patch(
        'pneumatic_backend.authentication.services.microsoft.'
        'MicrosoftAuthService.save_tokens_for_user',
    )
    update_microsoft_contacts = mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.'
        'update_microsoft_contacts.delay'
    )
    auth_response = {
        'code': '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
        'client_info': 'eyJ1aWQi...0YjY2ZGFkIn0',
        'state': 'KvpfgTSUmwtOaPny',
        'session_state': '0d046a4b-061a-4de5-be04-472a06763149'
    }

    # act
    response = api_client.get(
        '/auth/microsoft/token',
        data=auth_response,
        HTTP_USER_AGENT=user_agent,
        HTTP_X_REAL_IP=user_ip
    )

    # assert
    assert response.status_code == 200
    assert response.data['token'] == token
    ms_service_init_mock.assert_called_once()
    ms_get_user_data_mock.assert_called_once_with(
        auth_response=auth_response
    )
    authenticate_mock.assert_called_once_with(
        user=user,
        user_agent=user_agent,
        user_ip=user_ip,
    )
    save_tokens_for_user_mock.assert_called_once_with(user)
    update_microsoft_contacts.assert_called_once_with(user.id)


def test_token__disable_ms_auth__permission_denied(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.MSAuthPermission.'
        'has_permission',
        return_value=False
    )
    ms_service_init_mock = mocker.patch.object(
        MicrosoftAuthService,
        attribute='__init__',
        return_value=None
    )
    email = 'test@test.test'
    create_test_user(email=email)
    user_data = UserData(
        email=email,
        first_name='',
        last_name='',
        company_name='',
        photo=None,
        job_title=''
    )
    ms_get_user_data_mock = mocker.patch(
        'pneumatic_backend.authentication.services.microsoft.'
        'MicrosoftAuthService.get_user_data',
        return_value=user_data
    )
    user_agent = 'Some/Mozilla'
    user_ip = '128.18.0.99'
    token = '!@#E213'
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.'
        'AuthService.get_auth_token',
        return_value=token
    )
    save_tokens_for_user_mock = mocker.patch(
        'pneumatic_backend.authentication.services.microsoft.'
        'MicrosoftAuthService.save_tokens_for_user',
    )
    update_microsoft_contacts = mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.'
        'update_microsoft_contacts.delay'
    )
    auth_response = {
        'code': '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
        'client_info': 'eyJ1aWQi...0YjY2ZGFkIn0',
        'state': 'KvpfgTSUmwtOaPny',
        'session_state': '0d046a4b-061a-4de5-be04-472a06763149'
    }

    # act
    response = api_client.get(
        '/auth/microsoft/token',
        data=auth_response,
        HTTP_USER_AGENT=user_agent,
        HTTP_X_REAL_IP=user_ip
    )

    # assert
    assert response.status_code == 401
    ms_service_init_mock.assert_not_called()
    ms_get_user_data_mock.assert_not_called()
    authenticate_mock.assert_not_called()
    save_tokens_for_user_mock.assert_not_called()
    update_microsoft_contacts.assert_not_called()


def test_token__service_exception__validation_error(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.MSAuthPermission.'
        'has_permission',
        return_value=True
    )
    ms_service_init_mock = mocker.patch.object(
        MicrosoftAuthService,
        attribute='__init__',
        return_value=None
    )
    message = 'Some error'
    ms_get_user_data_mock = mocker.patch(
        'pneumatic_backend.authentication.services.microsoft.'
        'MicrosoftAuthService.get_user_data',
        side_effect=AuthException(message)
    )
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.'
        'AuthService.get_auth_token'
    )
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.'
        'MSAuthViewSet.signup'
    )
    save_tokens_for_user_mock = mocker.patch(
        'pneumatic_backend.authentication.services.microsoft.'
        'MicrosoftAuthService.save_tokens_for_user',
    )
    update_microsoft_contacts = mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.'
        'update_microsoft_contacts.delay'
    )
    auth_response = {
        'code': '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
        'client_info': 'eyJ1aWQi...0YjY2ZGFkIn0',
        'state': 'KvpfgTSUmwtOaPny',
        'session_state': '0d046a4b-061a-4de5-be04-472a06763149'
    }

    # act
    response = api_client.get(
        '/auth/microsoft/token',
        data=auth_response
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    ms_service_init_mock.assert_called_once()
    ms_get_user_data_mock.assert_called_once_with(
        auth_response=auth_response
    )
    authenticate_mock.assert_not_called()
    signup_mock.assert_not_called()
    save_tokens_for_user_mock.assert_not_called()
    update_microsoft_contacts.assert_not_called()


def test_token__user_not_found__signup(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.MSAuthPermission.'
        'has_permission',
        return_value=True
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.settings'
    )
    settings_mock.PROJECT_CONF = {'SIGNUP': True}
    ms_service_init_mock = mocker.patch.object(
        MicrosoftAuthService,
        attribute='__init__',
        return_value=None
    )
    email = 'test@test.test'
    user_data = UserData(
        email=email,
        first_name='',
        last_name='',
        company_name='',
        photo=None,
        job_title=''
    )
    ms_get_user_data_mock = mocker.patch(
        'pneumatic_backend.authentication.services.microsoft.'
        'MicrosoftAuthService.get_user_data',
        return_value=user_data
    )
    user_agent = 'Some/Mozilla'
    user_ip = '128.18.0.99'
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.'
        'AuthService.get_auth_token'
    )
    token = '!@#Eqa13d'
    user_mock = mocker.Mock(id='123')
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.'
        'MSAuthViewSet.signup',
        return_value=(user_mock, token)
    )
    save_tokens_for_user_mock = mocker.patch(
        'pneumatic_backend.authentication.services.microsoft.'
        'MicrosoftAuthService.save_tokens_for_user',
    )
    update_microsoft_contacts = mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.'
        'update_microsoft_contacts.delay'
    )
    auth_response = {
        'code': '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
        'client_info': 'eyJ1aWQi...0YjY2ZGFkIn0',
        'state': 'KvpfgTSUmwtOaPny',
        'session_state': '0d046a4b-061a-4de5-be04-472a06763149'
    }
    utm_source = 'some_utm_source'
    utm_medium = 'some_utm_medium'
    utm_campaign = 'some_utm_campaign'
    utm_term = 'some_utm_term'
    utm_content = 'some_utm_content'
    gclid = 'some_gclid'

    # act
    response = api_client.get(
        '/auth/microsoft/token',
        data={
            **auth_response,
            'utm_source': utm_source,
            'utm_medium': utm_medium,
            'utm_campaign': utm_campaign,
            'utm_term': utm_term,
            'utm_content': utm_content,
            'gclid': gclid,
        },
        HTTP_USER_AGENT=user_agent,
        HTTP_X_REAL_IP=user_ip
    )

    # assert
    assert response.status_code == 200
    assert response.data['token'] == token
    ms_service_init_mock.assert_called_once()
    ms_get_user_data_mock.assert_called_once_with(
        auth_response=auth_response
    )
    authenticate_mock.assert_not_called()
    signup_mock.assert_called_once_with(
        **user_data,
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
        utm_term=utm_term,
        utm_content=utm_content,
        gclid=gclid,
    )
    save_tokens_for_user_mock.assert_called_once_with(user_mock)
    update_microsoft_contacts.assert_called_once_with(user_mock.id)


def test_token__user_not_found_and_signup_disabled__authentication_error(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.MSAuthPermission.'
        'has_permission',
        return_value=True
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.settings'
    )
    settings_mock.PROJECT_CONF = {'SIGNUP': False}
    ms_service_init_mock = mocker.patch.object(
        MicrosoftAuthService,
        attribute='__init__',
        return_value=None
    )
    email = 'test@test.test'
    user_data = UserData(
        email=email,
        first_name='',
        last_name='',
        company_name='',
        photo=None,
        job_title=''
    )
    ms_get_user_data_mock = mocker.patch(
        'pneumatic_backend.authentication.services.microsoft.'
        'MicrosoftAuthService.get_user_data',
        return_value=user_data
    )
    user_agent = 'Some/Mozilla'
    user_ip = '128.18.0.99'
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.'
        'AuthService.get_auth_token'
    )
    token = '!@#Eqa13d'
    user_mock = mocker.Mock(id='123')
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.'
        'MSAuthViewSet.signup',
        return_value=(user_mock, token)
    )
    save_tokens_for_user_mock = mocker.patch(
        'pneumatic_backend.authentication.services.microsoft.'
        'MicrosoftAuthService.save_tokens_for_user',
    )
    update_microsoft_contacts = mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.'
        'update_microsoft_contacts.delay'
    )
    auth_response = {
        'code': '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
        'client_info': 'eyJ1aWQi...0YjY2ZGFkIn0',
        'state': 'KvpfgTSUmwtOaPny',
        'session_state': '0d046a4b-061a-4de5-be04-472a06763149'
    }
    utm_source = 'some_utm_source'
    utm_medium = 'some_utm_medium'
    utm_campaign = 'some_utm_campaign'
    utm_term = 'some_utm_term'
    utm_content = 'some_utm_content'
    gclid = 'some_gclid'

    # act
    response = api_client.get(
        '/auth/microsoft/token',
        data={
            **auth_response,
            'utm_source': utm_source,
            'utm_medium': utm_medium,
            'utm_campaign': utm_campaign,
            'utm_term': utm_term,
            'utm_content': utm_content,
            'gclid': gclid,
        },
        HTTP_USER_AGENT=user_agent,
        HTTP_X_REAL_IP=user_ip
    )

    # assert
    assert response.status_code == 401
    ms_service_init_mock.assert_called_once()
    ms_get_user_data_mock.assert_called_once_with(
        auth_response=auth_response
    )
    authenticate_mock.assert_not_called()
    signup_mock.assert_not_called()
    save_tokens_for_user_mock.assert_not_called()
    update_microsoft_contacts.assert_not_called()


def test_token__skip__code__validation_error(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.MSAuthPermission.'
        'has_permission',
        return_value=True
    )
    ms_service_init_mock = mocker.patch.object(
        MicrosoftAuthService,
        attribute='__init__',
        return_value=None
    )
    ms_get_user_data_mock = mocker.patch(
        'pneumatic_backend.authentication.services.microsoft.'
        'MicrosoftAuthService.get_user_data'
    )
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.'
        'AuthService.get_auth_token'
    )
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.'
        'MSAuthViewSet.signup'
    )
    auth_response = {
        'client_info': 'eyJ1aWQi...0YjY2ZGFkIn0',
        'state': 'KvpfgTSUmwtOaPny',
        'session_state': '0d046a4b-061a-4de5-be04-472a06763149'
    }

    # act
    response = api_client.get(
        '/auth/microsoft/token',
        data=auth_response
    )

    # assert
    assert response.status_code == 400
    message = 'This field is required.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    ms_service_init_mock.assert_not_called()
    ms_get_user_data_mock.assert_not_called()
    authenticate_mock.assert_not_called()
    signup_mock.assert_not_called()


def test_token__code_blank__validation_error(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.MSAuthPermission.'
        'has_permission',
        return_value=True
    )
    ms_service_init_mock = mocker.patch.object(
        MicrosoftAuthService,
        attribute='__init__',
        return_value=None
    )
    ms_get_user_data_mock = mocker.patch(
        'pneumatic_backend.authentication.services.microsoft.'
        'MicrosoftAuthService.get_user_data'
    )
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.'
        'AuthService.get_auth_token'
    )
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.'
        'MSAuthViewSet.signup'
    )
    auth_response = {
        'code': '',
        'client_info': 'eyJ1aWQi...0YjY2ZGFkIn0',
        'state': 'KvpfgTSUmwtOaPny',
        'session_state': '0d046a4b-061a-4de5-be04-472a06763149'
    }

    # act
    response = api_client.get(
        '/auth/microsoft/token',
        data=auth_response
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be blank.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    ms_service_init_mock.assert_not_called()
    ms_get_user_data_mock.assert_not_called()
    authenticate_mock.assert_not_called()
    signup_mock.assert_not_called()


def test_auth_uri__ok(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.MSAuthPermission.'
        'has_permission',
        return_value=True
    )
    ms_service_init_mock = mocker.patch.object(
        MicrosoftAuthService,
        attribute='__init__',
        return_value=None
    )
    auth_uri = 'https://login.microsoftonline.com'
    ms_get_auth_uri_mock = mocker.patch(
        'pneumatic_backend.authentication.services.microsoft.'
        'MicrosoftAuthService.get_auth_uri',
        return_value=auth_uri
    )

    # act
    response = api_client.get('/auth/microsoft/auth-uri')

    # assert
    assert response.status_code == 200
    assert response.data['auth_uri'] == auth_uri
    ms_service_init_mock.assert_called_once()
    ms_get_auth_uri_mock.assert_called_once()


def test_auth_uri__disable_ms_auth__permission_denied(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.MSAuthPermission.'
        'has_permission',
        return_value=False
    )
    ms_service_init_mock = mocker.patch.object(
        MicrosoftAuthService,
        attribute='__init__',
        return_value=None
    )
    auth_uri = 'https://login.microsoftonline.com'
    ms_get_auth_uri_mock = mocker.patch(
        'pneumatic_backend.authentication.services.microsoft.'
        'MicrosoftAuthService.get_auth_uri',
        return_value=auth_uri
    )

    # act
    response = api_client.get('/auth/microsoft/auth-uri')

    # assert
    assert response.status_code == 401
    ms_service_init_mock.assert_not_called()
    ms_get_auth_uri_mock.assert_not_called()


def test_auth_uri__service_exception__validation_error(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.microsoft.MSAuthPermission.'
        'has_permission',
        return_value=True
    )
    ms_service_init_mock = mocker.patch.object(
        MicrosoftAuthService,
        attribute='__init__',
        return_value=None
    )
    message = 'Some error'
    ms_get_auth_uri_mock = mocker.patch(
        'pneumatic_backend.authentication.services.microsoft.'
        'MicrosoftAuthService.get_auth_uri',
        side_effect=AuthException(message)
    )

    # act
    response = api_client.get('/auth/microsoft/auth-uri')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    ms_service_init_mock.assert_called_once()
    ms_get_auth_uri_mock.assert_called_once()
