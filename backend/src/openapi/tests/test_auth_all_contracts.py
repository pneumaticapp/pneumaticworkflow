"""HTTP contracts for every authentication operation.

Identity-provider HTTP/SDK calls are replaced at their transport boundary.
Application permissions, serializers, tokens and persistence run normally.
"""

import json
from urllib.parse import parse_qs, urlparse

from django.core.cache import caches
from jsonschema.exceptions import ValidationError
import pytest
from requests import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from src.accounts.models import User
from src.accounts.tokens import ResetPasswordToken, VerificationToken
from src.authentication.enums import ResetPasswordStatus
from src.authentication.services.microsoft import MicrosoftAuthService
from src.authentication.throttling import (
    AuthGoogleAuthUriThrottle,
    AuthGoogleTokenThrottle,
    AuthMSAuthUriThrottle,
    AuthMSTokenThrottle,
    AuthResetPasswordThrottle,
    SSOAuthUriThrottle,
    SSOTokenThrottle,
)
from src.openapi.auth_contract_serializers import OKTA_LOGOUT_REQUEST_SCHEMA
from src.processes.tests.fixtures import (
    create_test_not_admin,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db

PROVIDER_FLAGS = {
    'auth0': 'SSO_AUTH',
    'okta': 'SSO_AUTH',
    'google': 'GOOGLE_AUTH',
    'microsoft': 'MS_AUTH',
}
PROVIDER_GETS = [
    (provider, action)
    for provider in PROVIDER_FLAGS
    for action in ('auth-uri', 'token', 'logout')
    if (provider, action) != ('okta', 'logout')
]
PASSWORD = 'Contract-password-123'


@pytest.fixture(autouse=True)
def auth_contract_environment(settings, mocker) -> None:
    settings.PROJECT_CONF = {
        **settings.PROJECT_CONF,
        'SIGNUP': True,
        'CAPTCHA': False,
        'SSO_AUTH': True,
        'SSO_PROVIDER': '',
        'GOOGLE_AUTH': True,
        'MS_AUTH': True,
    }
    settings.PRIVATE_API_CHECK_IP = False
    settings.VERIFICATION_CHECK = False
    for provider in ('AUTH0', 'OKTA'):
        setattr(settings, f'{provider}_CLIENT_ID', 'contract-client')
        setattr(settings, f'{provider}_CLIENT_SECRET', 'contract-secret')
        setattr(settings, f'{provider}_DOMAIN', 'identity.example.test')
        setattr(
            settings,
            f'{provider}_REDIRECT_URI',
            'https://example.test/callback',
        )
    for alias in ('default', 'auth', 'session'):
        caches[alias].clear()
    # These tasks perform external notifications/contact synchronization.
    for target in (
        'src.authentication.tasks.update_google_contacts.delay',
        'src.authentication.tasks.update_microsoft_contacts.delay',
        'src.notifications.tasks.send_verification_notification.delay',
        'src.notifications.tasks.send_reset_password_notification.delay',
    ):
        mocker.patch(target)


@pytest.fixture
def auth_owner() -> User:
    owner = create_test_owner()
    owner.set_password(PASSWORD)
    owner.save(update_fields=['password'])
    return owner


def provider_response(value: dict, status: int = 200) -> Response:
    response = Response()
    response.status_code = status
    response._content = json.dumps(value).encode('utf-8')
    response.headers['Content-Type'] = 'application/json'
    return response


@pytest.fixture
def provider_io(mocker, auth_owner) -> tuple:
    tokens = {
        'access_token': 'provider-access-token',
        'refresh_token': 'provider-refresh-token',
        'expires_in': 3600,
        'token_type': 'Bearer',
    }
    profile = {
        'email': auth_owner.email,
        'email_verified': True,
        'given_name': 'Contract',
        'family_name': 'Owner',
        'id': 'provider-user',
        'givenName': 'Contract',
        'surname': 'Owner',
        'mail': auth_owner.email,
        'userPrincipalName': auth_owner.email,
        'jobTitle': '',
        'companyName': '',
        'displayName': 'Contract Owner',
        'names': [
            {
                'givenName': 'Contract',
                'familyName': 'Owner',
                'metadata': {'primary': True},
            },
        ],
        'emailAddresses': [
            {
                'value': auth_owner.email,
                'metadata': {'primary': True, 'verified': True},
            },
        ],
        'photos': [],
        'organizations': [],
    }
    post = mocker.patch(
        'requests.post', return_value=provider_response(tokens),
    )

    def get_provider_response(url: str, **kwargs) -> Response:
        if '/photos/' in url:
            return provider_response({}, 404)
        return provider_response(profile)

    get = mocker.patch('requests.get', side_effect=get_provider_response)
    msal = mocker.Mock()
    msal.initiate_auth_code_flow.return_value = {
        'state': 'microsoft-state',
        'auth_uri': 'https://identity.example.test/authorize'
        '?state=microsoft-state',
    }
    msal.acquire_token_by_auth_code_flow.return_value = tokens
    mocker.patch.object(
        MicrosoftAuthService, '_build_msal_app', return_value=msal,
    )
    return post, get, msal


def provider_callback(client, provider: str) -> dict:
    response = client.get(f'/auth/{provider}/auth-uri')
    assert response.status_code == 200
    state = parse_qs(urlparse(response.json()['auth_uri']).query)['state'][0]
    result = {'code': 'provider-code', 'state': state}
    if provider == 'microsoft':
        result.update(client_info='client-info', session_state='session-state')
    return result


@pytest.mark.parametrize('provider', list(PROVIDER_FLAGS))
def test_provider__auth_uri_and_token__real_session(
    contract_api_client,
    provider,
    provider_io,
) -> None:
    callback = provider_callback(contract_api_client, provider)
    response = contract_api_client.get(
        f'/auth/{provider}/token', data=callback,
    )
    assert response.status_code == 200
    assert isinstance(response.json()['token'], str)
    assert response.json()['token']


@pytest.mark.parametrize(
    'provider,status',
    [
        ('auth0', 204),
        ('google', 200),
        ('microsoft', 204),
    ],
)
def test_provider__logout__actual_acknowledgement(
    contract_api_client,
    provider,
    status,
) -> None:
    response = contract_api_client.get(f'/auth/{provider}/logout')
    assert response.status_code == status


@pytest.mark.parametrize('provider,action', PROVIDER_GETS)
@pytest.mark.parametrize('authenticated,status', [(False, 401), (True, 403)])
def test_provider__disabled_feature__permission_error(
    contract_api_client,
    provider,
    action,
    authenticated,
    status,
    auth_owner,
    settings,
) -> None:
    settings.PROJECT_CONF = {
        **settings.PROJECT_CONF,
        PROVIDER_FLAGS[provider]: False,
    }
    if authenticated:
        contract_api_client.token_authenticate(auth_owner)
    response = contract_api_client.get(f'/auth/{provider}/{action}')
    assert response.status_code == status


@pytest.mark.parametrize('provider', list(PROVIDER_FLAGS))
def test_provider__malformed_callback__validation_error(
    contract_api_client,
    provider,
) -> None:
    response = contract_api_client.get(f'/auth/{provider}/token')
    assert response.status_code == 400


@pytest.mark.parametrize('provider', list(PROVIDER_FLAGS))
def test_provider__upstream_failure__documented_error(
    contract_api_client,
    provider,
    provider_io,
) -> None:
    callback = provider_callback(contract_api_client, provider)
    post, _get, msal = provider_io
    post.return_value = provider_response({'error': 'invalid_grant'}, 400)
    msal.acquire_token_by_auth_code_flow.return_value = {
        'error': 'invalid_grant',
    }
    response = contract_api_client.get(
        f'/auth/{provider}/token', data=callback,
    )
    assert response.status_code == 400


@pytest.mark.parametrize('provider', ['auth0', 'okta'])
def test_sso_auth_uri__provider_mismatch__validation_error(
    contract_api_client, settings, provider,
) -> None:
    settings.PROJECT_CONF = {
        **settings.PROJECT_CONF,
        'SSO_PROVIDER': 'okta' if provider == 'auth0' else 'auth0',
    }
    response = contract_api_client.get(f'/auth/{provider}/auth-uri')
    assert response.status_code == 400


def test_okta_backchannel__valid__acknowledged(
    contract_api_client,
    mocker,
) -> None:
    queued = mocker.patch(
        'src.authentication.views.okta_logout.process_okta_logout.delay',
    )
    response = contract_api_client.post(
        '/auth/okta/logout',
        data={
            'sub_id': {
                'format': 'email',
                'email': 'person@example.test',
            },
        },
        HTTP_AUTHORIZATION='Bearer provider-logout-token',
        format='json',
    )
    assert response.status_code == 204
    queued.assert_called_once()


@pytest.mark.parametrize('payload', [{}, [], 'invalid', 123, False])
def test_okta_backchannel__malformed__acknowledged(
    contract_api_client, mocker, payload,
) -> None:
    queued = mocker.patch(
        'src.authentication.views.okta_logout.process_okta_logout.delay',
    )
    response = contract_api_client.post(
        '/auth/okta/logout', data=json.dumps(payload),
        content_type='application/json',
    )
    assert response.status_code == 204
    queued.assert_not_called()


def test_okta_backchannel__null__existing_serialization_error(
    contract_api_client, http_contract,
) -> None:
    with pytest.raises(ValidationError):
        http_contract.validate(
            OKTA_LOGOUT_REQUEST_SCHEMA, None, response=False,
        )
    # Preserve the current runtime limitation rather than changing validation.
    with pytest.raises(TypeError):
        contract_api_client.post(
            '/auth/okta/logout', data='null', content_type='application/json',
        )


def test_okta_backchannel__disabled__forbidden(
    contract_api_client,
    settings,
) -> None:
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'SSO_AUTH': False}
    response = contract_api_client.post(
        '/auth/okta/logout', data={}, format='json',
    )
    assert response.status_code == 403


def test_password_signin__real_credentials__session(
    contract_api_client,
    auth_owner,
) -> None:
    response = contract_api_client.post(
        '/auth/token/obtain',
        data={
            'username': auth_owner.email,
            'password': PASSWORD,
        },
        format='json',
    )
    assert response.status_code == 200
    assert response.json()['token']


def test_password_signin__wrong_credentials__forbidden(
    contract_api_client,
    auth_owner,
) -> None:
    response = contract_api_client.post(
        '/auth/token/obtain',
        data={
            'username': auth_owner.email,
            'password': 'wrong-password',
        },
        format='json',
    )
    assert response.status_code == 403


def test_password_signin__sso_only_user__validation_error(
    contract_api_client, auth_owner,
) -> None:
    user = create_test_not_admin(account=auth_owner.account)
    user.set_password(PASSWORD)
    user.save(update_fields=['password'])
    response = contract_api_client.post(
        '/auth/token/obtain',
        data={'username': user.email, 'password': PASSWORD},
        format='json',
    )
    assert response.status_code == 400


def test_jwt_refresh__real_refresh__access(
    contract_api_client, auth_owner,
) -> None:
    response = contract_api_client.post(
        '/auth/token/refresh',
        data={
            'refresh': str(RefreshToken.for_user(auth_owner)),
        },
        format='json',
    )
    assert response.status_code == 200
    assert response.json()['access']


@pytest.mark.parametrize(
    'payload,status', [({}, 400), ({'refresh': 'invalid'}, 401)],
)
def test_jwt_refresh__invalid__error(
    contract_api_client, payload, status,
) -> None:
    response = contract_api_client.post(
        '/auth/token/refresh', data=payload, format='json',
    )
    assert response.status_code == status


def test_signup__captcha_and_real_account__success(
    contract_api_client,
) -> None:
    requirement = contract_api_client.get('/auth/signup')
    assert requirement.status_code == 200
    response = contract_api_client.post(
        '/auth/signup',
        data={
            'email': 'signup-contract@example.test',
            'first_name': 'Contract',
            'last_name': 'Owner',
            'company_name': 'Contract company',
            'password': PASSWORD,
        },
        format='json',
    )
    assert response.status_code == 200
    assert response.json()['token']


@pytest.mark.parametrize('method', ['get', 'post'])
@pytest.mark.parametrize('authenticated,status', [(False, 401), (True, 403)])
def test_signup__disabled__permission_error(
    contract_api_client,
    method,
    authenticated,
    status,
    auth_owner,
    settings,
) -> None:
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'SIGNUP': False}
    if authenticated:
        contract_api_client.token_authenticate(auth_owner)
    response = getattr(contract_api_client, method)('/auth/signup')
    assert response.status_code == status


def test_signup__invalid_email__validation_error(contract_api_client) -> None:
    response = contract_api_client.post(
        '/auth/signup',
        data={
            'email': 'invalid-email',
        },
        format='json',
    )
    assert response.status_code == 400


def test_session__context_resend_change_password_signout__success(
    contract_api_client,
    auth_owner,
) -> None:
    contract_api_client.token_authenticate(auth_owner)
    assert contract_api_client.get('/auth/context').status_code == 200
    assert (
        contract_api_client.post('/auth/resend-verification').status_code
        == 200
    )
    changed = contract_api_client.post(
        '/auth/change-password',
        data={
            'old_password': PASSWORD,
            'new_password': 'New-contract-password-123',
            'confirm_new_password': 'New-contract-password-123',
        },
        format='json',
    )
    assert changed.status_code == 200
    contract_api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {changed.json()["token"]}',
    )
    assert contract_api_client.post('/auth/signout').status_code == 204


@pytest.mark.parametrize(
    'path,method',
    [
        ('/auth/context', 'get'),
        ('/auth/resend-verification', 'post'),
        ('/auth/change-password', 'post'),
        ('/auth/signout', 'post'),
        ('/auth/superuser/token', 'post'),
    ],
)
def test_session__missing_token__unauthorized(
    contract_api_client, path, method,
) -> None:
    response = getattr(contract_api_client, method)(path)
    assert response.status_code == 401


def test_context__public_credential__forbidden(
    contract_api_client, auth_owner,
) -> None:
    template = create_test_template(auth_owner, is_active=True, is_public=True)
    response = contract_api_client.get(
        '/auth/context',
        HTTP_X_PUBLIC_AUTHORIZATION=f'Token {template.public_id}',
    )
    assert response.status_code == 403


def test_resend__non_admin__forbidden(contract_api_client) -> None:
    user = create_test_not_admin()
    contract_api_client.token_authenticate(user)
    response = contract_api_client.post('/auth/resend-verification')
    assert response.status_code == 403


def test_change_password__wrong_old_password__validation_error(
    contract_api_client,
    auth_owner,
) -> None:
    contract_api_client.token_authenticate(auth_owner)
    response = contract_api_client.post(
        '/auth/change-password',
        data={
            'old_password': 'wrong-password',
            'new_password': PASSWORD,
            'confirm_new_password': PASSWORD,
        },
        format='json',
    )
    assert response.status_code == 400


@pytest.mark.parametrize(
    'path',
    ['/auth/change-password', '/auth/signout', '/auth/resend-verification'],
)
def test_private_session__blocked_source_ip__forbidden(
    contract_api_client,
    auth_owner,
    path,
    settings,
) -> None:
    settings.PRIVATE_API_CHECK_IP = True
    settings.PRIVATE_API_IP_WHITELIST = ['192.0.2.1']
    contract_api_client.token_authenticate(auth_owner)
    response = contract_api_client.post(path, HTTP_REMOTE_ADDR='192.0.2.2')
    assert response.status_code == 403


def test_superuser__real_impersonation_and_unknown_user(
    contract_api_client,
    auth_owner,
) -> None:
    target = create_test_owner(email='target@example.test')
    auth_owner.is_superuser = True
    auth_owner.save(update_fields=['is_superuser'])
    contract_api_client.token_authenticate(auth_owner)
    response = contract_api_client.post(
        '/auth/superuser/token',
        data={
            'email': target.email,
        },
        format='json',
    )
    assert response.status_code == 200
    absent = contract_api_client.post(
        '/auth/superuser/token',
        data={
            'email': 'missing@example.test',
        },
        format='json',
    )
    assert absent.status_code == 404


def test_superuser__ordinary_user__forbidden(
    contract_api_client, auth_owner,
) -> None:
    contract_api_client.token_authenticate(auth_owner)
    response = contract_api_client.post(
        '/auth/superuser/token',
        data={
            'email': auth_owner.email,
        },
        format='json',
    )
    assert response.status_code == 403


def test_verification__real_token__marks_account(
    contract_api_client, auth_owner,
) -> None:
    account = auth_owner.account
    account.is_verified = False
    account.save(update_fields=['is_verified'])
    response = contract_api_client.get(
        '/auth/verification',
        data={
            'token': str(VerificationToken.for_user(auth_owner)),
        },
    )
    assert response.status_code == 204
    account.refresh_from_db()
    assert account.is_verified


@pytest.mark.parametrize('payload', [{}, {'token': ''}, {'token': 'invalid'}])
def test_verification__invalid_input__validation_error(
    contract_api_client, payload,
) -> None:
    response = contract_api_client.get('/auth/verification', data=payload)
    assert response.status_code == 400


def test_verification__missing_user__not_found(contract_api_client) -> None:
    token = VerificationToken.for_user_id(987654321)
    response = contract_api_client.get(
        '/auth/verification', data={'token': str(token)},
    )
    assert response.status_code == 404


@pytest.mark.parametrize('authenticated,status', [(False, 401), (True, 403)])
def test_verification__source_ip_restriction__permission_error(
    contract_api_client,
    auth_owner,
    settings,
    authenticated,
    status,
) -> None:
    settings.PRIVATE_API_CHECK_IP = True
    settings.PRIVATE_API_IP_WHITELIST = ['192.0.2.1']
    if authenticated:
        contract_api_client.token_authenticate(auth_owner)
    response = contract_api_client.get(
        '/auth/verification', HTTP_REMOTE_ADDR='192.0.2.2',
    )
    assert response.status_code == status


def test_password_reset__all_success_operations(
    contract_api_client, auth_owner,
) -> None:
    assert (
        contract_api_client.get('/auth/reset-password/captcha').status_code
        == 200
    )
    token = str(ResetPasswordToken.for_user(auth_owner))
    check = contract_api_client.get(
        '/auth/reset-password', data={'token': token},
    )
    assert check.status_code == 200
    assert check.json()['status'] == ResetPasswordStatus.VALID
    requested = contract_api_client.post(
        '/auth/reset-password',
        data={'email': auth_owner.email},
        format='json',
    )
    assert requested.status_code == 204
    confirmed = contract_api_client.post(
        '/auth/reset-password/confirm',
        data={
            'token': token,
            'new_password': 'New-contract-password-123',
            'confirm_new_password': 'New-contract-password-123',
        },
        format='json',
    )
    assert confirmed.status_code == 200


@pytest.mark.parametrize(
    'path,method,payload',
    [
        ('/auth/reset-password', 'get', {}),
        ('/auth/reset-password', 'post', {'email': 'invalid-email'}),
        ('/auth/reset-password/confirm', 'post', {}),
    ],
)
def test_password_reset__invalid_input__error(
    contract_api_client, path, method, payload,
) -> None:
    response = getattr(contract_api_client, method)(path, data=payload)
    assert response.status_code == 400


def test_password_reset__user_deleted_after_verification__not_found(
    contract_api_client, auth_owner, mocker,
) -> None:
    token = str(ResetPasswordToken.for_user(auth_owner))
    verify = ResetPasswordToken.verify

    def verify_then_delete(instance: ResetPasswordToken) -> None:
        # Reproduce another request deleting the user between both SELECTs.
        verify(instance)
        auth_owner.delete()

    mocker.patch.object(ResetPasswordToken, 'verify', verify_then_delete)
    response = contract_api_client.post(
        '/auth/reset-password/confirm',
        data={
            'token': token,
            'new_password': PASSWORD,
            'confirm_new_password': PASSWORD,
        },
        format='json',
    )
    assert response.status_code == 404


def test_password_reset__user_deleted_before_verification__token_error(
    contract_api_client, auth_owner,
) -> None:
    token = str(ResetPasswordToken.for_user(auth_owner))
    auth_owner.delete()
    # Existing behavior: TokenError is not handled by the confirm action.
    with pytest.raises(TokenError):
        contract_api_client.post(
            '/auth/reset-password/confirm',
            data={
                'token': token,
                'new_password': PASSWORD,
                'confirm_new_password': PASSWORD,
            },
            format='json',
        )


RATE_CASES = [
    (f'/auth/{provider}/{action}', 'get', throttle)
    for provider, uri_throttle, token_throttle in (
        ('auth0', SSOAuthUriThrottle, SSOTokenThrottle),
        ('okta', SSOAuthUriThrottle, SSOTokenThrottle),
        ('google', AuthGoogleAuthUriThrottle, AuthGoogleTokenThrottle),
        ('microsoft', AuthMSAuthUriThrottle, AuthMSTokenThrottle),
    )
    for action, throttle in [
        ('auth-uri', uri_throttle),
        ('token', token_throttle),
    ]
] + [
    (path, method, AuthResetPasswordThrottle)
    for path, method in (
        ('/auth/reset-password', 'get'),
        ('/auth/reset-password', 'post'),
        ('/auth/reset-password/captcha', 'get'),
        ('/auth/reset-password/confirm', 'post'),
    )
]


@pytest.mark.parametrize('path,method,throttle', RATE_CASES)
def test_authentication__configured_rate_limit__429(
    contract_api_client,
    provider_io,
    mocker,
    path,
    method,
    throttle,
) -> None:
    mocker.patch.object(throttle, 'THROTTLE_RATES', {throttle.scope: '1/hour'})
    first = getattr(contract_api_client, method)(path)
    assert first.status_code in (200, 400)
    limited = getattr(contract_api_client, method)(path)
    assert limited.status_code == 429


def test_verification__no_pagination_parameters(http_contract) -> None:
    parameters = http_contract.document['paths']['/auth/verification']['get'][
        'parameters'
    ]
    assert not {'limit', 'offset'} & {item['name'] for item in parameters}


@pytest.mark.parametrize('provider', ['google', 'microsoft'])
def test_auth_uri__no_input_validation_error(http_contract, provider) -> None:
    operation = http_contract.document['paths'][
        f'/auth/{provider}/auth-uri'
    ]['get']
    assert '400' not in operation['responses']
