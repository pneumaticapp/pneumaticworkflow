import pytest
from src.authentication.services.exceptions import AuthException
from src.authentication.services.google import GoogleAuthService
from src.authentication.entities import UserData
from src.processes.tests.fixtures import create_test_user
from src.utils.validation import ErrorCode


pytestmark = pytest.mark.django_db


def test_token__existent_user__authenticate(
    mocker,
    api_client,
):
    """
    Test authorization of existing user via Google OAuth2
    """
    # arrange
    mocker.patch(
        'src.authentication.views.google.GoogleAuthPermission.'
        'has_permission',
        return_value=True
    )
    google_service_init_mock = mocker.patch.object(
        GoogleAuthService,
        attribute='__init__',
        return_value=None
    )
    email = 'test@test.test'
    user = create_test_user(email=email)
    user_data = UserData(
        email=email,
        first_name='John',
        last_name='Doe',
        company_name='',
        photo='https://example.com/photo.jpg',
        job_title=''
    )
    google_get_user_data_mock = mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.get_user_data',
        return_value=user_data
    )
    user_agent = 'Some/Mozilla'
    user_ip = '128.18.0.99'
    token = '!@#E213'
    auth_service_get_token_mock = mocker.patch(
        'src.authentication.services.user_auth.'
        'AuthService.get_auth_token',
        return_value=token
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.save_tokens_for_user'
    )
    identify_mock = mocker.patch(
        'src.authentication.views.google.'
        'GoogleAuthViewSet.identify'
    )
    update_contacts_mock = mocker.patch(
        'src.authentication.tasks.'
        'update_google_contacts.delay'
    )

    # act
    response = api_client.get(
        path='/auth/google/token',
        data={
            'code': '4/0AbUR2VMeHxU...',
            'state': 'random_state_string'
        },
        HTTP_USER_AGENT=user_agent,
        HTTP_X_REAL_IP=user_ip,
    )

    # assert
    assert response.status_code == 200
    assert response.data['token'] == token

    google_service_init_mock.assert_called_once()
    google_get_user_data_mock.assert_called_once_with(
        auth_response={
            'code': '4/0AbUR2VMeHxU...',
            'state': 'random_state_string'
        }
    )
    auth_service_get_token_mock.assert_called_once_with(
        user=user,
        user_agent=user_agent,
        user_ip=user_ip
    )
    save_tokens_mock.assert_called_once_with(user)
    identify_mock.assert_not_called()
    update_contacts_mock.assert_called_once_with(user.id)


def test_token__new_user__signup(
    mocker,
    api_client,
):
    """
    Test registration of new user via Google OAuth2
    """
    # arrange
    mocker.patch(
        'src.authentication.views.google.GoogleAuthPermission.'
        'has_permission',
        return_value=True
    )
    mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.__init__',
        return_value=None
    )
    email = 'new_user@test.test'
    user_data = UserData(
        email=email,
        first_name='Jane',
        last_name='Smith',
        company_name='Test Company',
        photo='https://example.com/photo.jpg',
        job_title=''
    )
    mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.get_user_data',
        return_value=user_data
    )

    mocker.patch(
        'src.authentication.views.google.settings.PROJECT_CONF',
        {'SIGNUP': True}
    )

    user = create_test_user(email='different@email.com', first_name='Jane')
    token = 'new_user_token'
    signup_mock = mocker.patch(
        'src.authentication.views.google.'
        'GoogleAuthViewSet.signup',
        return_value=(user, token)
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.save_tokens_for_user'
    )
    update_contacts_mock = mocker.patch(
        'src.authentication.tasks.'
        'update_google_contacts.delay'
    )

    # act
    response = api_client.get(
        path='/auth/google/token',
        data={
            'code': '4/0AbUR2VMeHxU...',
            'state': 'random_state_string',
            'utm_source': 'google',
            'utm_medium': 'social'
        }
    )

    # assert
    assert response.status_code == 200
    assert response.data['token'] == token

    signup_mock.assert_called_once_with(
        email=email,
        first_name='Jane',
        last_name='Smith',
        company_name='Test Company',
        photo='https://example.com/photo.jpg',
        job_title='',
        utm_source='google',
        utm_medium='social',
        utm_campaign=None,
        utm_term=None,
        utm_content=None,
        gclid=None
    )
    save_tokens_mock.assert_called_once_with(user)
    update_contacts_mock.assert_called_once_with(user.id)


def test_token__invalid_code__validation_error(
    mocker,
    api_client,
):
    """
    Test error handling for invalid authorization code
    """
    # arrange
    mocker.patch(
        'src.authentication.views.google.GoogleAuthPermission.'
        'has_permission',
        return_value=True
    )
    mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.__init__',
        return_value=None
    )
    auth_exception = AuthException(message='Invalid authorization code')
    mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.get_user_data',
        side_effect=auth_exception
    )

    # act
    response = api_client.get(
        path='/auth/google/token',
        data={
            'code': 'invalid_code',
            'state': 'random_state_string'
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert 'Invalid authorization code' in str(response.data)


def test_auth_uri__ok(
    mocker,
    api_client,
):
    """
    Test getting URL for Google OAuth2 authorization
    """
    # arrange
    mocker.patch(
        'src.authentication.views.google.GoogleAuthPermission.'
        'has_permission',
        return_value=True
    )
    mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.__init__',
        return_value=None
    )
    auth_uri = (
        'https://accounts.google.com/o/oauth2/v2/auth?'
        'client_id=test_client_id&redirect_uri=test_redirect&'
        'scope=profile+email+contacts&response_type=code&'
        'state=random_state&access_type=offline&prompt=consent'
    )
    mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.get_auth_uri',
        return_value=auth_uri
    )

    # act
    response = api_client.get(path='/auth/google/auth-uri')

    # assert
    assert response.status_code == 200
    assert response.data['auth_uri'] == auth_uri


def test_auth_uri__service_error__validation_error(
    mocker,
    api_client,
):
    """
    Test error handling during authorization URL generation
    """
    # arrange
    mocker.patch(
        'src.authentication.views.google.GoogleAuthPermission.'
        'has_permission',
        return_value=True
    )
    mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.__init__',
        return_value=None
    )
    auth_exception = AuthException(message='Configuration error')
    mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.get_auth_uri',
        side_effect=auth_exception
    )

    # act
    response = api_client.get(path='/auth/google/auth-uri')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert 'Configuration error' in str(response.data)


def test_logout__ok(
    mocker,
    api_client,
):
    """
    Test logout endpoint for Google OAuth2
    """
    # arrange
    mocker.patch(
        'src.authentication.views.google.GoogleAuthPermission.'
        'has_permission',
        return_value=True
    )
    capture_message_mock = mocker.patch(
        'src.authentication.views.google.'
        'capture_sentry_message'
    )

    # act
    response = api_client.get(
        path='/auth/google/logout',
        data={'some_param': 'some_value'}
    )

    # assert
    assert response.status_code == 200
    capture_message_mock.assert_called_once()


def test_token__missing_required_params__validation_error(
    mocker,
    api_client,
):
    """
    Test validation of required parameters
    """
    # arrange
    mocker.patch(
        'src.authentication.views.google.GoogleAuthPermission.'
        'has_permission',
        return_value=True
    )

    # act
    response = api_client.get(
        path='/auth/google/token',
        data={}
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert 'code' in str(response.data)


def test_token__disable_google_auth__permission_denied(
    mocker,
    api_client,
):
    """
    Test permission denied when Google OAuth2 is disabled
    """
    # arrange
    mocker.patch(
        'src.authentication.views.google.GoogleAuthPermission.'
        'has_permission',
        return_value=False
    )
    google_service_init_mock = mocker.patch.object(
        GoogleAuthService,
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
    google_get_user_data_mock = mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.get_user_data',
        return_value=user_data
    )
    user_agent = 'Some/Mozilla'
    user_ip = '128.18.0.99'
    token = '!@#E213'
    authenticate_mock = mocker.patch(
        'src.authentication.services.user_auth.'
        'AuthService.get_auth_token',
        return_value=token
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.save_tokens_for_user',
    )
    update_contacts_mock = mocker.patch(
        'src.authentication.tasks.'
        'update_google_contacts.delay'
    )
    auth_response = {
        'code': '4/0AbUR2VMeHxU...',
        'state': 'random_state_string'
    }

    # act
    response = api_client.get(
        path='/auth/google/token',
        data=auth_response,
        HTTP_USER_AGENT=user_agent,
        HTTP_X_REAL_IP=user_ip
    )

    # assert
    assert response.status_code == 401
    google_service_init_mock.assert_not_called()
    google_get_user_data_mock.assert_not_called()
    authenticate_mock.assert_not_called()
    save_tokens_mock.assert_not_called()
    update_contacts_mock.assert_not_called()


def test_token__user_not_found_and_signup_disabled__authentication_error(
    mocker,
    api_client,
):
    """
    Test authentication error when user not found and signup disabled
    """
    # arrange
    mocker.patch(
        'src.authentication.views.google.GoogleAuthPermission.'
        'has_permission',
        return_value=True
    )
    settings_mock = mocker.patch(
        'src.authentication.views.google.settings'
    )
    settings_mock.PROJECT_CONF = {'SIGNUP': False}
    mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.__init__',
        return_value=None
    )
    email = 'nonexistent@test.test'
    user_data = UserData(
        email=email,
        first_name='Jane',
        last_name='Smith',
        company_name='',
        photo=None,
        job_title=''
    )
    mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.get_user_data',
        return_value=user_data
    )
    user_agent = 'Some/Mozilla'
    user_ip = '128.18.0.99'
    authenticate_mock = mocker.patch(
        'src.authentication.services.user_auth.'
        'AuthService.get_auth_token'
    )
    signup_mock = mocker.patch(
        'src.authentication.views.google.'
        'GoogleAuthViewSet.signup'
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.save_tokens_for_user',
    )
    update_contacts_mock = mocker.patch(
        'src.authentication.tasks.'
        'update_google_contacts.delay'
    )
    auth_response = {
        'code': '4/0AbUR2VMeHxU...',
        'state': 'random_state_string'
    }

    # act
    response = api_client.get(
        path='/auth/google/token',
        data=auth_response,
        HTTP_USER_AGENT=user_agent,
        HTTP_X_REAL_IP=user_ip
    )

    # assert
    assert response.status_code == 401
    authenticate_mock.assert_not_called()
    signup_mock.assert_not_called()
    save_tokens_mock.assert_not_called()
    update_contacts_mock.assert_not_called()


def test_auth_uri__disable_google_auth__permission_denied(
    mocker,
    api_client,
):
    """
    Test permission denied for auth-uri when Google OAuth2 is disabled
    """
    # arrange
    mocker.patch(
        'src.authentication.views.google.GoogleAuthPermission.'
        'has_permission',
        return_value=False
    )
    google_service_init_mock = mocker.patch.object(
        GoogleAuthService,
        attribute='__init__',
        return_value=None
    )
    auth_uri = (
        'https://accounts.google.com/o/oauth2/v2/auth?'
        'client_id=test_client_id&redirect_uri=test_redirect'
    )
    google_get_auth_uri_mock = mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.get_auth_uri',
        return_value=auth_uri
    )

    # act
    response = api_client.get(path='/auth/google/auth-uri')

    # assert
    assert response.status_code == 401
    google_service_init_mock.assert_not_called()
    google_get_auth_uri_mock.assert_not_called()


def test_token__skip_code__validation_error(
    mocker,
    api_client,
):
    """
    Test validation error when code parameter is missing
    """
    # arrange
    mocker.patch(
        'src.authentication.views.google.GoogleAuthPermission.'
        'has_permission',
        return_value=True
    )
    google_service_init_mock = mocker.patch.object(
        GoogleAuthService,
        attribute='__init__',
        return_value=None
    )
    google_get_user_data_mock = mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.get_user_data'
    )
    authenticate_mock = mocker.patch(
        'src.authentication.services.user_auth.'
        'AuthService.get_auth_token'
    )
    signup_mock = mocker.patch(
        'src.authentication.views.google.'
        'GoogleAuthViewSet.signup'
    )
    auth_response = {
        'state': 'random_state_string'
    }

    # act
    response = api_client.get(
        path='/auth/google/token',
        data=auth_response
    )

    # assert
    assert response.status_code == 400
    message = 'This field is required.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert message in str(response.data)
    google_service_init_mock.assert_not_called()
    google_get_user_data_mock.assert_not_called()
    authenticate_mock.assert_not_called()
    signup_mock.assert_not_called()


def test_token__code_blank__validation_error(
    mocker,
    api_client,
):
    """
    Test validation error when code parameter is blank
    """
    # arrange
    mocker.patch(
        'src.authentication.views.google.GoogleAuthPermission.'
        'has_permission',
        return_value=True
    )
    google_service_init_mock = mocker.patch.object(
        GoogleAuthService,
        attribute='__init__',
        return_value=None
    )
    google_get_user_data_mock = mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.get_user_data'
    )
    authenticate_mock = mocker.patch(
        'src.authentication.services.user_auth.'
        'AuthService.get_auth_token'
    )
    signup_mock = mocker.patch(
        'src.authentication.views.google.'
        'GoogleAuthViewSet.signup'
    )
    auth_response = {
        'code': '',
        'state': 'random_state_string'
    }

    # act
    response = api_client.get(
        path='/auth/google/token',
        data=auth_response
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be blank.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert message in str(response.data)
    google_service_init_mock.assert_not_called()
    google_get_user_data_mock.assert_not_called()
    authenticate_mock.assert_not_called()
    signup_mock.assert_not_called()


def test_token__skip_state__validation_error(
    mocker,
    api_client,
):
    """
    Test validation error when state parameter is missing
    """
    # arrange
    mocker.patch(
        'src.authentication.views.google.GoogleAuthPermission.'
        'has_permission',
        return_value=True
    )
    google_service_init_mock = mocker.patch.object(
        GoogleAuthService,
        attribute='__init__',
        return_value=None
    )
    google_get_user_data_mock = mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.get_user_data'
    )
    authenticate_mock = mocker.patch(
        'src.authentication.services.user_auth.'
        'AuthService.get_auth_token'
    )
    signup_mock = mocker.patch(
        'src.authentication.views.google.'
        'GoogleAuthViewSet.signup'
    )
    auth_response = {
        'code': '4/0AbUR2VMeHxU...'
        # Missing state parameter
    }

    # act
    response = api_client.get(
        path='/auth/google/token',
        data=auth_response
    )

    # assert
    assert response.status_code == 400
    message = 'This field is required.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert message in str(response.data)
    google_service_init_mock.assert_not_called()
    google_get_user_data_mock.assert_not_called()
    authenticate_mock.assert_not_called()
    signup_mock.assert_not_called()


def test_token__state_blank__validation_error(
    mocker,
    api_client,
):
    """
    Test validation error when state parameter is blank
    """
    # arrange
    mocker.patch(
        'src.authentication.views.google.GoogleAuthPermission.'
        'has_permission',
        return_value=True
    )
    google_service_init_mock = mocker.patch.object(
        GoogleAuthService,
        attribute='__init__',
        return_value=None
    )
    google_get_user_data_mock = mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.get_user_data'
    )
    authenticate_mock = mocker.patch(
        'src.authentication.services.user_auth.'
        'AuthService.get_auth_token'
    )
    signup_mock = mocker.patch(
        'src.authentication.views.google.'
        'GoogleAuthViewSet.signup'
    )
    auth_response = {
        'code': '4/0AbUR2VMeHxU...',
        'state': ''  # Blank state parameter
    }

    # act
    response = api_client.get(
        path='/auth/google/token',
        data=auth_response
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be blank.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert message in str(response.data)
    google_service_init_mock.assert_not_called()
    google_get_user_data_mock.assert_not_called()
    authenticate_mock.assert_not_called()
    signup_mock.assert_not_called()


def test_token__utm_parameters__passed_to_signup(
    mocker,
    api_client,
):
    """
    Test that UTM parameters are correctly passed to signup
    """
    # arrange
    mocker.patch(
        'src.authentication.views.google.GoogleAuthPermission.'
        'has_permission',
        return_value=True
    )
    mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.__init__',
        return_value=None
    )
    email = 'new_user@test.test'
    user_data = UserData(
        email=email,
        first_name='Jane',
        last_name='Smith',
        company_name='Test Company',
        photo='https://example.com/photo.jpg',
        job_title='Developer'
    )
    mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.get_user_data',
        return_value=user_data
    )

    mocker.patch(
        'src.authentication.views.google.settings.PROJECT_CONF',
        {'SIGNUP': True}
    )

    user = create_test_user(email='different@email.com')
    token = 'new_user_token'
    signup_mock = mocker.patch(
        'src.authentication.views.google.'
        'GoogleAuthViewSet.signup',
        return_value=(user, token)
    )
    mocker.patch(
        'src.authentication.services.google.'
        'GoogleAuthService.save_tokens_for_user'
    )
    mocker.patch(
        'src.authentication.tasks.'
        'update_google_contacts.delay'
    )

    utm_params = {
        'utm_source': 'google_ads',
        'utm_medium': 'cpc',
        'utm_campaign': 'spring_sale',
        'utm_term': 'oauth',
        'utm_content': 'button_top',
        'gclid': 'Cj0KCQjw...'
    }

    # act
    response = api_client.get(
        path='/auth/google/token',
        data={
            'code': '4/0AbUR2VMeHxU...',
            'state': 'random_state_string',
            **utm_params
        }
    )

    # assert
    assert response.status_code == 200
    assert response.data['token'] == token

    signup_mock.assert_called_once_with(
        email=email,
        first_name='Jane',
        last_name='Smith',
        company_name='Test Company',
        photo='https://example.com/photo.jpg',
        job_title='Developer',
        **utm_params
    )
