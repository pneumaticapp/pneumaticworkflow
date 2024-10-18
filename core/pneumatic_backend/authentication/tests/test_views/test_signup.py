import pytest
from pneumatic_backend.authentication import messages
from pneumatic_backend.utils.validation import ErrorCode
from drf_recaptcha.validators import ReCaptchaV2Validator
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
)
from pneumatic_backend.authentication.views.signup import SignUpView
from pneumatic_backend.accounts.enums import Language, Timezone


pytestmark = pytest.mark.django_db


def test_retrieve__ok(api_client, mocker):

    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignupPermission.'
        'has_permission',
        return_value=True
    )
    anonymous_user_account_exists_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.'
        'SignUpView.anonymous_user_account_exists',
        return_value=False
    )
    settings_mock = mocker.patch(
       'pneumatic_backend.authentication.views.signup.settings'
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': True}

    # act
    response = api_client.get('/auth/signup')

    # assert
    assert response.status_code == 200
    assert response.data['show_captcha'] is False
    anonymous_user_account_exists_mock.assert_called_once()


def test_retrieve__disable_signup__permission_error(api_client, mocker):

    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignupPermission.'
        'has_permission',
        return_value=False
    )
    anonymous_user_account_exists_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.'
        'SignUpView.anonymous_user_account_exists',
        return_value=False
    )

    # act
    response = api_client.get('/auth/signup')

    # assert
    assert response.status_code == 401
    anonymous_user_account_exists_mock.assert_not_called()


def test_retrieve__show_captcha__ok(api_client, mocker):

    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignupPermission.'
        'has_permission',
        return_value=True
    )
    anonymous_user_account_exists_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.'
        'SignUpView.anonymous_user_account_exists',
        return_value=True
    )
    settings_mock = mocker.patch(
       'pneumatic_backend.authentication.views.signup.settings'
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': True}

    # act
    response = api_client.get('/auth/signup')

    # assert
    assert response.status_code == 200
    assert response.data['show_captcha'] is True
    anonymous_user_account_exists_mock.assert_called_once()


def test_retrieve__disable_captcha__ok(api_client, mocker):

    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignupPermission.'
        'has_permission',
        return_value=True
    )
    anonymous_user_account_exists_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.'
        'SignUpView.anonymous_user_account_exists',
        return_value=True
    )
    settings_mock = mocker.patch(
       'pneumatic_backend.authentication.views.signup.settings'
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': False}

    # act
    response = api_client.get('/auth/signup')

    # assert
    assert response.status_code == 200
    assert response.data['show_captcha'] is False
    anonymous_user_account_exists_mock.assert_not_called()


def test_create__all_fields_without_captcha__ok(
    api_client,
    mocker,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignupPermission.'
        'has_permission',
        return_value=True
    )
    anonymous_user_account_exists_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.'
        'SignUpView.anonymous_user_account_exists',
        return_value=False
    )
    token = 'token'
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignUpView.'
        'signup',
        return_value=(None, token)
    )
    settings_mock = mocker.patch(
       'pneumatic_backend.authentication.views.signup.settings'
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': True}

    email = 'Test@pneumatiC.App'
    phone = '+7955264787'
    first_name = 'jOe'
    last_name = 'swithzeRlanD'
    company_name = 'some company'
    utm_source = 'some_utm_source'
    utm_medium = 'some_utm_medium'
    utm_campaign = 'some_utm_campaign'
    utm_term = 'some_utm_term'
    utm_content = 'some_utm_content'
    gclid = 'some_gclid'
    photo = 'https://some.photo.com/photo.png'
    password = '123123'
    tz = Timezone.UTC
    language = 'es'

    # act
    response = api_client.post(
        '/auth/signup',
        data={
            'email': email,
            'phone': phone,
            'company_name': company_name,
            'first_name': first_name,
            'last_name': last_name,
            'photo': photo,
            'password': password,
            'language': language,
            'timezone': tz,
            'utm_source': utm_source,
            'utm_medium': utm_medium,
            'utm_campaign': utm_campaign,
            'utm_term': utm_term,
            'utm_content': utm_content,
            'gclid': gclid,
        }
    )

    # assert
    assert response.status_code == 200
    assert response.data['token'] == token
    anonymous_user_account_exists_mock.assert_called_once()
    signup_mock.assert_called_once_with(
        email=email.lower(),
        phone=phone,
        company_name=company_name,
        first_name=first_name.title(),
        last_name=last_name.title(),
        photo=photo,
        password=password,
        timezone=tz,
        language=language,
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
        utm_term=utm_term,
        utm_content=utm_content,
        gclid=gclid,
    )


def test_create__only_required_fields__ok(
    api_client,
    mocker,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignupPermission.'
        'has_permission',
        return_value=True
    )
    anonymous_user_account_exists_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.'
        'SignUpView.anonymous_user_account_exists',
        return_value=False
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.settings'
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': True}

    token = 'token'
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignUpView.'
        'signup',
        return_value=(None, token)
    )
    email = 'Test@pneumatiC.App'

    # act
    response = api_client.post(
        '/auth/signup',
        data={'email': email}
    )

    # assert
    assert response.status_code == 200
    assert response.data['token'] == token
    anonymous_user_account_exists_mock.assert_called_once()
    signup_mock.assert_called_once_with(
        email=email.lower(),
    )


def test_create__all_fields_with_captcha__ok(
    api_client,
    mocker,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignupPermission.'
        'has_permission',
        return_value=True
    )
    anonymous_user_account_exists_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.'
        'SignUpView.anonymous_user_account_exists',
        return_value=True
    )
    mocker.patch.object(
        ReCaptchaV2Validator,
        attribute='__call__',
    )
    token = 'token'
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignUpView.'
        'signup',
        return_value=(None, token)
    )
    settings_mock = mocker.patch(
       'pneumatic_backend.authentication.views.signup.settings'
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': True}

    email = 'Test@pneumatiC.App'
    phone = '+7955264787'
    first_name = 'jOe'
    last_name = 'swithzeRlanD'
    company_name = 'some company'
    utm_source = 'some_utm_source'
    utm_medium = 'some_utm_medium'
    utm_campaign = 'some_utm_campaign'
    utm_term = 'some_utm_term'
    utm_content = 'some_utm_content'
    gclid = 'some_gclid'
    photo = 'https://some.photo.com/photo.png'
    password = '123123'
    tz = Timezone.UTC
    language = 'es'
    captcha = 'skip'

    # act
    response = api_client.post(
        '/auth/signup',
        data={
            'email': email,
            'phone': phone,
            'company_name': company_name,
            'first_name': first_name,
            'last_name': last_name,
            'photo': photo,
            'password': password,
            'language': language,
            'timezone': tz,
            'utm_source': utm_source,
            'utm_medium': utm_medium,
            'utm_campaign': utm_campaign,
            'utm_term': utm_term,
            'utm_content': utm_content,
            'gclid': gclid,
            'captcha': captcha,
        }
    )

    # assert
    assert response.status_code == 200
    anonymous_user_account_exists_mock.assert_called_once()
    assert response.data['token'] == token
    signup_mock.assert_called_once_with(
        email=email.lower(),
        phone=phone,
        company_name=company_name,
        first_name=first_name.title(),
        last_name=last_name.title(),
        photo=photo,
        password=password,
        timezone=tz,
        language=language,
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
        utm_term=utm_term,
        utm_content=utm_content,
        gclid=gclid,
    )


def test_create__skip_captcha__validation_error(
    api_client,
    mocker,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignupPermission.'
        'has_permission',
        return_value=True
    )
    anonymous_user_account_exists_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.'
        'SignUpView.anonymous_user_account_exists',
        return_value=True
    )
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignUpView.'
        'signup'
    )
    email = 'Test@pneumatiC.App'
    settings_mock = mocker.patch(
       'pneumatic_backend.authentication.views.signup.settings'
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': True}

    # act
    response = api_client.post(
        '/auth/signup',
        data={
            'email': email,
        }
    )

    # assert
    assert response.status_code == 400
    message = 'This field is required.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'captcha'
    assert response.data['details']['reason'] == message
    anonymous_user_account_exists_mock.assert_called_once()
    signup_mock.assert_not_called()


def test_create__short_password__validation_error(
    api_client,
    mocker,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignupPermission.'
        'has_permission',
        return_value=True
    )
    anonymous_user_account_exists_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.'
        'SignUpView.anonymous_user_account_exists',
        return_value=False
    )
    token = 'token'
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignUpView.'
        'signup',
        return_value=(None, token)
    )
    email = 'Test@pneumatiC.App'
    password = '12312'
    settings_mock = mocker.patch(
       'pneumatic_backend.authentication.views.signup.settings'
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': True}

    # act
    response = api_client.post(
        '/auth/signup',
        data={
            'email': email,
            'password': password,
        }
    )

    # assert
    assert response.status_code == 400
    message = 'Ensure this field has at least 6 characters.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'password'
    assert response.data['details']['reason'] == message
    anonymous_user_account_exists_mock.assert_called_once()
    signup_mock.assert_not_called()


def test_create__skip_email__validation_error(
    api_client,
    mocker,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignupPermission.'
        'has_permission',
        return_value=True
    )
    anonymous_user_account_exists_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.'
        'SignUpView.anonymous_user_account_exists',
        return_value=False
    )
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignUpView.'
        'signup'
    )
    first_name = 'joe'
    last_name = 'swithzerland'
    settings_mock = mocker.patch(
       'pneumatic_backend.authentication.views.signup.settings'
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': True}

    # act
    response = api_client.post(
        '/auth/signup',
        data={
            'last_name': first_name,
            'first_name': last_name,
        }
    )

    # assert
    assert response.status_code == 400
    message = 'This field is required.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'email'
    assert response.data['details']['reason'] == message
    anonymous_user_account_exists_mock.assert_called_once()
    signup_mock.assert_not_called()


@pytest.mark.parametrize(
    'phone',
    (
        'My phone',
        '++9998887744',
        '+19998887776665554'
    )
)
def test_create__invalid_phone_number__validation_error(
    api_client,
    phone,
    mocker,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignupPermission.'
        'has_permission',
        return_value=True
    )
    anonymous_user_account_exists_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.'
        'SignUpView.anonymous_user_account_exists',
        return_value=False
    )
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignUpView.'
        'signup'
    )
    settings_mock = mocker.patch(
       'pneumatic_backend.authentication.views.signup.settings'
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': True}

    # act
    response = api_client.post(
        '/auth/signup',
        data={
            'last_name': 'joe',
            'first_name': 'swithzerland',
            'email': 'test@test.test',
            'phone': phone
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_AU_0006
    assert response.data['details']['name'] == 'phone'
    assert response.data['details']['reason'] == messages.MSG_AU_0006
    anonymous_user_account_exists_mock.assert_called_once()
    signup_mock.assert_not_called()


def test_create__invalid_language__validation_error(
    api_client,
    mocker,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignupPermission.'
        'has_permission',
        return_value=True
    )
    anonymous_user_account_exists_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.'
        'SignUpView.anonymous_user_account_exists',
        return_value=False
    )
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignUpView.'
        'signup'
    )
    email = 'some@email.com'
    language = 'ah-AV'
    settings_mock = mocker.patch(
       'pneumatic_backend.authentication.views.signup.settings'
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': True}

    # act
    response = api_client.post(
        '/auth/signup',
        data={
            'email': email,
            'language': language
        }
    )

    # assert
    assert response.status_code == 400
    message = f'"{language}" is not a valid choice.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'language'
    assert response.data['details']['reason'] == message
    anonymous_user_account_exists_mock.assert_called_once()
    signup_mock.assert_not_called()


def test_create__rus_language__validation_error(
    api_client,
    mocker,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignupPermission.'
        'has_permission',
        return_value=True
    )
    anonymous_user_account_exists_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.'
        'SignUpView.anonymous_user_account_exists',
        return_value=False
    )
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignUpView.'
        'signup'
    )
    email = 'some@email.com'
    settings_mock = mocker.patch(
       'pneumatic_backend.authentication.views.signup.settings'
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': True}

    # act
    response = api_client.post(
        '/auth/signup',
        data={
            'email': email,
            'language': Language.ru
        }
    )

    # assert
    assert response.status_code == 400
    message = f'"{Language.ru}" is not a valid choice.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'language'
    assert response.data['details']['reason'] == message
    anonymous_user_account_exists_mock.assert_called_once()
    signup_mock.assert_not_called()


def test_create__language__is_null__validation_error(
    api_client,
    mocker,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignupPermission.'
        'has_permission',
        return_value=True
    )
    anonymous_user_account_exists_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.'
        'SignUpView.anonymous_user_account_exists',
        return_value=False
    )
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignUpView.'
        'signup'
    )
    email = 'some@email.com'
    settings_mock = mocker.patch(
       'pneumatic_backend.authentication.views.signup.settings'
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': True}

    # act
    response = api_client.post(
        '/auth/signup',
        data={
            'email': email,
            'language': None
        }
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be null.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'language'
    assert response.data['details']['reason'] == message
    anonymous_user_account_exists_mock.assert_called_once()
    signup_mock.assert_not_called()


def test_create__invalid_timezone__validation_error(
    api_client,
    mocker,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignupPermission.'
        'has_permission',
        return_value=True
    )
    anonymous_user_account_exists_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.'
        'SignUpView.anonymous_user_account_exists',
        return_value=False
    )
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignUpView.'
        'signup'
    )
    email = 'some@email.com'
    timezone = 'Some/Where'
    settings_mock = mocker.patch(
       'pneumatic_backend.authentication.views.signup.settings'
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': True}

    # act
    response = api_client.post(
        '/auth/signup',
        data={
            'email': email,
            'timezone': timezone
        }
    )

    # assert
    assert response.status_code == 400
    message = f'"{timezone}" is not a valid choice.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'timezone'
    assert response.data['details']['reason'] == message
    anonymous_user_account_exists_mock.assert_called_once()
    signup_mock.assert_not_called()


def test_create__timezone__is_null__validation_error(
    api_client,
    mocker,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignupPermission.'
        'has_permission',
        return_value=True
    )
    anonymous_user_account_exists_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.'
        'SignUpView.anonymous_user_account_exists',
        return_value=False
    )
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignUpView.'
        'signup'
    )
    email = 'some@email.com'
    settings_mock = mocker.patch(
       'pneumatic_backend.authentication.views.signup.settings'
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': True}

    # act
    response = api_client.post(
        '/auth/signup',
        data={
            'email': email,
            'timezone': None
        }
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be null.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'timezone'
    assert response.data['details']['reason'] == message
    anonymous_user_account_exists_mock.assert_called_once()
    signup_mock.assert_not_called()


def test_create_after_signup__need_verification__ok(mocker):

    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignupPermission.'
        'has_permission',
        return_value=True
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.settings'
    )
    settings_mock.VERIFICATION_CHECK = True
    verification_token = '!@#!ds'
    get_verification_token_mock = mocker.patch(
        'pneumatic_backend.accounts.tokens.VerificationToken.for_user',
        return_value=verification_token
    )
    send_verification_email_mock = mocker.patch(
        'pneumatic_backend.services.email.EmailService.'
        'send_verification_email'
    )
    inc_anonymous_user_account_counter = mocker.patch(
        'pneumatic_backend.authentication.views.signup.'
        'SignUpView.inc_anonymous_user_account_counter',
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.settings'
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': True}
    request = mocker.Mock()
    view = SignUpView(request=request)
    account = create_test_account(
        logo_lg='https://some.image.com/logo.lg',
        is_verified=False
    )
    user = create_test_user(account=account)

    # act
    view.after_signup(user)

    # assert
    get_verification_token_mock.assert_called_once_with(user)
    send_verification_email_mock.assert_called_once_with(
        user=user,
        token=verification_token,
        logo_lg=account.logo_lg
    )
    inc_anonymous_user_account_counter.assert_called_once()


def test_create_after_signup__skip_verification__ok(mocker):

    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignupPermission.'
        'has_permission',
        return_value=True
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.settings'
    )
    settings_mock.VERIFICATION_CHECK = False
    send_verification_email_mock = mocker.patch(
        'pneumatic_backend.services.email.EmailService.'
        'send_verification_email'
    )
    inc_anonymous_user_account_counter = mocker.patch(
        'pneumatic_backend.authentication.views.signup.'
        'SignUpView.inc_anonymous_user_account_counter',
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.settings'
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': True}
    request = mocker.Mock()
    view = SignUpView(request=request)
    user = create_test_user()

    # act
    view.after_signup(user)

    # assert
    send_verification_email_mock.assert_not_called()
    inc_anonymous_user_account_counter.assert_called_once()


def test_create__disable_captcha__not_expect_captcha(
    api_client,
    mocker,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignupPermission.'
        'has_permission',
        return_value=True
    )
    anonymous_user_account_exists_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.'
        'SignUpView.anonymous_user_account_exists',
        return_value=True
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.settings'
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': False}

    token = 'token'
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.signup.SignUpView.'
        'signup',
        return_value=(None, token)
    )
    email = 'Test@pneumatiC.App'

    # act
    response = api_client.post(
        '/auth/signup',
        data={'email': email}
    )

    # assert

    assert response.status_code == 200
    assert response.data['token'] == token
    anonymous_user_account_exists_mock.assert_called_once()
    signup_mock.assert_called_once_with(
        email=email.lower(),
    )
