import pytest
from rest_framework.serializers import ValidationError
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.accounts.enums import Language
from pneumatic_backend.accounts.services import (
    AccountService,
    UserService,
)
from pneumatic_backend.accounts.services.exceptions import (
    AccountServiceException,
    UserServiceException,
)
from pneumatic_backend.processes.tests.fixtures import create_test_user
from pneumatic_backend.processes.api_v2.services.system_workflows import (
    SystemWorkflowService
)
from pneumatic_backend.authentication.views.mixins import SignUpMixin
from pneumatic_backend.payment.stripe.service import StripeService
from pneumatic_backend.payment.stripe.exceptions import StripeServiceException
from pneumatic_backend.utils.logging import SentryLogLevel


pytestmark = pytest.mark.django_db


def test_create__all_fields__ok(
    api_client,
    mocker,
):
    # arrange
    token = 'token'
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.views.mixins.'
        'AuthService.get_auth_token',
        return_value=token
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    update_customer_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.update_customer'
    )
    sys_workflow_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    create_onboarding_templates_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_onboarding_templates'
    )
    create_onboarding_workflows_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_onboarding_workflows'
    )
    create_activated_templates_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_activated_templates'
    )
    create_activated_workflows_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_activated_workflows'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None
    )
    user = create_test_user()
    account_create_mock = mocker.patch(
        'pneumatic_backend.accounts.services.AccountService.create',
        return_value=user.account
    )
    user_create_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserService.create',
        return_value=user
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.authentication.views.mixins.settings'
    )
    settings_mock.SLACK = True
    settings_mock.SLACK_CONFIG = {'NOTIFY_ON_SIGNUP': True}
    settings_mock.PROJECT_CONF = {'BILLING': True}
    notification_mock = mocker.patch(
        'pneumatic_backend.authentication.views.mixins.'
        'send_new_signup_notification.delay'
    )
    after_signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.mixins.SignUpMixin.'
        'after_signup'
    )

    email = 'Test@pneumatiC.App'
    phone = '+97984561210'
    first_name = 'joe'
    last_name = 'swithzerland'
    company_name = 'some company'
    utm_source = 'some_utm_source'
    utm_medium = 'some_utm_medium'
    utm_campaign = 'some_utm_campaign'
    utm_term = 'some_utm_term'
    utm_content = 'some_utm_content'
    gclid = 'some_gclid'
    photo = 'https://some.photo.com/photo.png'
    password = '123123'
    language = Language.de
    tz = 'Atlantic/Faeroe'

    is_superuser = False
    user_agent = 'some agent'
    ip = '456'
    request_mock = mocker.Mock(
        is_superuser=is_superuser,
        headers={
            'User-Agent': user_agent
        },
        META={
            'HTTP_X_REAL_IP': ip
        }
    )

    view = SignUpMixin()
    view.request = request_mock

    # act
    result = view.signup(
        email=email,
        phone=phone,
        first_name=first_name,
        last_name=last_name,
        company_name=company_name,
        photo=photo,
        job_title=None,
        password=password,
        timezone=tz,
        language=language,
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
        utm_term=utm_term,
        utm_content=utm_content,
        gclid=gclid
    )

    # assert
    assert result[0] == user
    assert result[1] == token
    account_service_init_mock.assert_called_once_with(
        is_superuser=is_superuser,
        auth_type=AuthTokenType.USER
    )
    user_service_init_mock.assert_called_once_with(
        is_superuser=is_superuser,
        auth_type=AuthTokenType.USER
    )
    account_create_mock.assert_called_once_with(
        name=company_name,
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
        utm_term=utm_term,
        utm_content=utm_content,
        gclid=gclid,
        billing_sync=True
    )
    user_create_mock.assert_called_once_with(
        account=user.account,
        phone=phone,
        email=email,
        first_name=first_name,
        last_name=last_name,
        photo=photo,
        raw_password=password,
        is_account_owner=True,
        timezone=tz,
        language=language,
    )
    stripe_service_init_mock.assert_called_once_with(user=user)
    update_customer_mock.assert_called_once()
    sys_workflow_service_init_mock.assert_called_once_with(user=user)
    create_onboarding_templates_mock.assert_called_once()
    create_onboarding_workflows_mock.assert_called_once()
    create_activated_templates_mock.assert_called_once()
    create_activated_workflows_mock.assert_called_once()
    notification_mock.assert_called_once_with(user.account.id)
    after_signup_mock.assert_called_once_with(user)
    authenticate_mock.assert_called_once_with(
        user=user,
        user_agent=user_agent,
        user_ip=ip,
    )


def test_create__account_service_exception__validation_error(
    api_client,
    mocker,
):
    # arrange
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.views.mixins.'
        'AuthService.get_auth_token'
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    update_customer_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.update_customer'
    )
    mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    create_onboarding_templates_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_onboarding_templates'
    )
    create_onboarding_workflows_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_onboarding_workflows'
    )
    create_activated_templates_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_activated_templates'
    )
    create_activated_workflows_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_activated_workflows'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None
    )
    user = create_test_user()
    message = 'some message'
    account_create_mock = mocker.patch(
        'pneumatic_backend.accounts.services.AccountService.create',
        side_effect=AccountServiceException(message=message)
    )
    user_create_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserService.create',
        return_value=user
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.authentication.views.mixins.settings'
    )
    settings_mock.SLACK = True
    settings_mock.SLACK_CONFIG = {'NOTIFY_ON_SIGNUP': False}
    settings_mock.PROJECT_CONF = {'BILLING': True}
    notification_mock = mocker.patch(
        'pneumatic_backend.authentication.views.mixins.'
        'send_new_signup_notification.delay'
    )
    after_signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.mixins.SignUpMixin.'
        'after_signup'
    )

    email = 'test@test.test'

    is_superuser = True
    request_mock = mocker.Mock(
        is_superuser=is_superuser,
    )

    view = SignUpMixin()
    view.request = request_mock

    # act
    with pytest.raises(ValidationError) as ex:
        view.signup(
            email=email,
        )

    # assert
    assert ex.value.detail['code'] == ErrorCode.VALIDATION_ERROR
    assert ex.value.detail['message'] == message
    account_service_init_mock.assert_called_once_with(
        is_superuser=is_superuser,
        auth_type=AuthTokenType.USER
    )
    user_service_init_mock.assert_called_once_with(
        is_superuser=is_superuser,
        auth_type=AuthTokenType.USER
    )
    account_create_mock.assert_called_once_with(
        name=None,
        utm_source=None,
        utm_medium=None,
        utm_campaign=None,
        utm_term=None,
        utm_content=None,
        gclid=None,
        billing_sync=True
    )
    user_create_mock.assert_not_called()
    stripe_service_init_mock.assert_not_called()
    update_customer_mock.assert_not_called()
    create_onboarding_templates_mock.assert_not_called()
    create_onboarding_workflows_mock.assert_not_called()
    create_activated_templates_mock.assert_not_called()
    create_activated_workflows_mock.assert_not_called()
    notification_mock.assert_not_called()
    after_signup_mock.assert_not_called()
    authenticate_mock.assert_not_called()


def test_create__user_service_exception__validation_error(
    api_client,
    mocker,
):
    # arrange
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.views.mixins.'
        'AuthService.get_auth_token'
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    update_customer_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.update_customer'
    )
    mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    create_onboarding_templates_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_onboarding_templates'
    )
    create_onboarding_workflows_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_onboarding_workflows'
    )
    create_activated_templates_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_activated_templates'
    )
    create_activated_workflows_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_activated_workflows'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None
    )
    user = create_test_user(is_account_owner=True)
    account_create_mock = mocker.patch(
        'pneumatic_backend.accounts.services.AccountService.create',
        return_value=user.account
    )
    message = 'some message'
    user_create_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserService.create',
        side_effect=UserServiceException(message=message)
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.authentication.views.mixins.settings'
    )
    settings_mock.SLACK = True
    settings_mock.SLACK_CONFIG = {'NOTIFY_ON_SIGNUP': True}
    settings_mock.PROJECT_CONF = {'BILLING': True}
    notification_mock = mocker.patch(
        'pneumatic_backend.authentication.views.mixins.'
        'send_new_signup_notification.delay'
    )
    after_signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.mixins.SignUpMixin.'
        'after_signup'
    )

    email = 'test@test.test'

    is_superuser = True
    request_mock = mocker.Mock(
        is_superuser=is_superuser,
    )

    view = SignUpMixin()
    view.request = request_mock

    # act
    with pytest.raises(ValidationError) as ex:
        view.signup(
            email=email,
        )

    # assert
    assert ex.value.detail['code'] == ErrorCode.VALIDATION_ERROR
    assert ex.value.detail['message'] == message
    account_service_init_mock.assert_called_once_with(
        is_superuser=is_superuser,
        auth_type=AuthTokenType.USER
    )
    user_service_init_mock.assert_called_once_with(
        is_superuser=is_superuser,
        auth_type=AuthTokenType.USER
    )
    account_create_mock.assert_called_once_with(
        name=None,
        utm_source=None,
        utm_medium=None,
        utm_campaign=None,
        utm_term=None,
        utm_content=None,
        gclid=None,
        billing_sync=True
    )
    user_create_mock.assert_called_once_with(
        account=user.account,
        email=email,
        first_name=None,
        last_name=None,
        photo=None,
        phone=None,
        raw_password=None,
        is_account_owner=True,
        language=None,
        timezone=None,
    )
    stripe_service_init_mock.assert_not_called()
    update_customer_mock.assert_not_called()
    create_onboarding_templates_mock.assert_not_called()
    create_onboarding_workflows_mock.assert_not_called()
    create_activated_templates_mock.assert_not_called()
    create_activated_workflows_mock.assert_not_called()
    notification_mock.assert_not_called()
    after_signup_mock.assert_not_called()
    authenticate_mock.assert_not_called()


def test_create__stripe_service_exception__skip_sync(
    api_client,
    mocker,
):

    # arrange
    token = 'token'
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.views.mixins.'
        'AuthService.get_auth_token',
        return_value=token
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    message = 'Error'
    ex = StripeServiceException(message=message)
    update_customer_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.update_customer',
        side_effect=ex
    )
    capture_sentry_message_mock = mocker.patch(
        'pneumatic_backend.authentication.views.mixins.capture_sentry_message'
    )
    sys_workflow_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    create_onboarding_templates_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_onboarding_templates'
    )
    create_onboarding_workflows_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_onboarding_workflows'
    )
    create_activated_templates_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_activated_templates'
    )
    create_activated_workflows_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_activated_workflows'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None
    )
    user = create_test_user()
    account_create_mock = mocker.patch(
        'pneumatic_backend.accounts.services.AccountService.create',
        return_value=user.account
    )
    user_create_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserService.create',
        return_value=user
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.authentication.views.mixins.settings'
    )
    settings_mock.SLACK = True
    settings_mock.SLACK_CONFIG = {'NOTIFY_ON_SIGNUP': True}
    settings_mock.PROJECT_CONF = {'BILLING': True}

    notification_mock = mocker.patch(
        'pneumatic_backend.authentication.views.mixins.'
        'send_new_signup_notification.delay'
    )
    after_signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.mixins.SignUpMixin.'
        'after_signup'
    )

    email = 'Test@pneumatiC.App'
    first_name = 'joe'
    last_name = 'swithzerland'
    company_name = 'some company'
    utm_source = 'some_utm_source'
    utm_medium = 'some_utm_medium'
    utm_campaign = 'some_utm_campaign'
    utm_term = 'some_utm_term'
    utm_content = 'some_utm_content'
    gclid = 'some_gclid'
    photo = 'https://some.photo.com/photo.png'
    password = '123123'
    language = Language.de
    tz = 'Atlantic/Faeroe'

    is_superuser = False
    user_agent = 'some agent'
    ip = '456'
    request_mock = mocker.Mock(
        is_superuser=is_superuser,
        headers={
            'User-Agent': user_agent
        },
        META={
            'HTTP_X_REAL_IP': ip
        }
    )

    view = SignUpMixin()
    view.request = request_mock

    # act
    result = view.signup(
        email=email,
        first_name=first_name,
        last_name=last_name,
        company_name=company_name,
        photo=photo,
        job_title=None,
        password=password,
        timezone=tz,
        language=language,
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
        utm_term=utm_term,
        utm_content=utm_content,
        gclid=gclid
    )

    # assert
    assert result[0] == user
    assert result[1] == token
    account_service_init_mock.assert_called_once_with(
        is_superuser=is_superuser,
        auth_type=AuthTokenType.USER
    )
    user_service_init_mock.assert_called_once_with(
        is_superuser=is_superuser,
        auth_type=AuthTokenType.USER
    )
    account_create_mock.assert_called_once_with(
        name=company_name,
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
        utm_term=utm_term,
        utm_content=utm_content,
        gclid=gclid,
        billing_sync=True
    )
    user_create_mock.assert_called_once_with(
        account=user.account,
        email=email,
        first_name=first_name,
        last_name=last_name,
        photo=photo,
        phone=None,
        raw_password=password,
        is_account_owner=True,
        timezone=tz,
        language=language,
    )
    stripe_service_init_mock.assert_called_once_with(user=user)
    update_customer_mock.assert_called_once()
    capture_sentry_message_mock.assert_called_once_with(
        message=f'Stripe account sync failed {user.account.id}',
        data={
            'account_id': user.account.id,
            'stripe_id': user.account.stripe_id,
            'exception': str(ex),
        },
        level=SentryLogLevel.ERROR
    )

    sys_workflow_service_init_mock.assert_called_once_with(user=user)
    create_onboarding_templates_mock.assert_called_once()
    create_onboarding_workflows_mock.assert_called_once()
    create_activated_templates_mock.assert_called_once()
    create_activated_workflows_mock.assert_called_once()
    notification_mock.assert_called_once_with(user.account.id)
    after_signup_mock.assert_called_once_with(user)
    authenticate_mock.assert_called_once_with(
        user=user,
        user_agent=user_agent,
        user_ip=ip,
    )


def test_create__disable_billing__skip_stripe_call(
    api_client,
    mocker,
):
    # arrange
    token = 'token'
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.views.mixins.'
        'AuthService.get_auth_token',
        return_value=token
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    update_customer_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.update_customer'
    )
    sys_workflow_service_init_mock = mocker.patch.object(
        SystemWorkflowService,
        attribute='__init__',
        return_value=None
    )
    create_onboarding_templates_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_onboarding_templates'
    )
    create_onboarding_workflows_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_onboarding_workflows'
    )
    create_activated_templates_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_activated_templates'
    )
    create_activated_workflows_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.create_activated_workflows'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None
    )
    user = create_test_user(is_account_owner=True)
    account_create_mock = mocker.patch(
        'pneumatic_backend.accounts.services.AccountService.create',
        return_value=user.account
    )
    user_create_mock = mocker.patch(
        'pneumatic_backend.accounts.services.UserService.create',
        return_value=user
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.authentication.views.mixins.settings'
    )
    settings_mock.SLACK = True
    settings_mock.SLACK_CONFIG = {'NOTIFY_ON_SIGNUP': True}
    settings_mock.PROJECT_CONF = {'BILLING': False}

    notification_mock = mocker.patch(
        'pneumatic_backend.authentication.views.mixins.'
        'send_new_signup_notification.delay'
    )
    after_signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.mixins.SignUpMixin.'
        'after_signup'
    )

    email = 'Test@pneumatiC.App'
    is_superuser = False
    user_agent = 'some agent'
    ip = '456'
    request_mock = mocker.Mock(
        is_superuser=is_superuser,
        headers={
            'User-Agent': user_agent
        },
        META={
            'HTTP_X_REAL_IP': ip
        }
    )

    view = SignUpMixin()
    view.request = request_mock

    # act
    result = view.signup(
        email=email,
    )

    # assert
    assert result[0] == user
    assert result[1] == token
    account_service_init_mock.assert_called_once_with(
        is_superuser=is_superuser,
        auth_type=AuthTokenType.USER
    )
    user_service_init_mock.assert_called_once_with(
        is_superuser=is_superuser,
        auth_type=AuthTokenType.USER
    )
    account_create_mock.assert_called_once_with(
        name=None,
        utm_source=None,
        utm_medium=None,
        utm_campaign=None,
        utm_term=None,
        utm_content=None,
        gclid=None,
        billing_sync=True
    )
    user_create_mock.assert_called_once_with(
        account=user.account,
        phone=None,
        email=email,
        first_name=None,
        last_name=None,
        photo=None,
        raw_password=None,
        is_account_owner=True,
        language=None,
        timezone=None,
    )
    stripe_service_init_mock.assert_not_called()
    update_customer_mock.assert_not_called()
    sys_workflow_service_init_mock.assert_called_once_with(user=user)
    create_onboarding_templates_mock.assert_called_once()
    create_onboarding_workflows_mock.assert_called_once()
    create_activated_templates_mock.assert_called_once()
    create_activated_workflows_mock.assert_called_once()
    notification_mock.assert_called_once_with(user.account.id)
    after_signup_mock.assert_called_once_with(user)
    authenticate_mock.assert_called_once_with(
        user=user,
        user_agent=user_agent,
        user_ip=ip,
    )
