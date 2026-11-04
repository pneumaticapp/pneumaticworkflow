"""Conditional auth CAPTCHA contracts through real anonymous HTTP requests."""

from io import BytesIO
from typing import Any, Dict, Tuple
from urllib.parse import parse_qs

from django.core.cache import caches
import pytest

from src.accounts.models import User
from src.authentication.serializers import (
    ResetPasswordSerializer,
    SecuredResetPasswordSerializer,
    SecuredSignUpSerializer,
    SignUpSerializer,
)

pytestmark = pytest.mark.django_db

VISITOR_IP = '198.51.100.27'
FIRST_EMAIL = 'captcha-first@example.test'
REPEAT_EMAIL = 'captcha-repeat@example.test'
FLOWS = (
    ('/auth/signup', '/auth/signup', 200),
    ('/auth/reset-password', '/auth/reset-password/captcha', 204),
)


@pytest.fixture(autouse=True)
def captcha_environment(settings) -> None:
    settings.PROJECT_CONF = {
        **settings.PROJECT_CONF,
        'SIGNUP': True, 'CAPTCHA': False, 'SSO_AUTH': False,
    }
    settings.PRIVATE_API_CHECK_IP = False
    settings.VERIFICATION_CHECK = False
    for alias in ('default', 'auth', 'session'):
        caches[alias].clear()


@pytest.fixture(params=FLOWS, ids=['signup', 'reset'])
def captcha_flow(request, contract_api_client) -> Tuple[str, str, int]:
    contract_api_client.credentials(
        HTTP_X_FORWARDED_FOR=VISITOR_IP, REMOTE_ADDR=VISITOR_IP,
    )
    return request.param


def signup_or_reset_payload(
    path: str, email: str, mode: str,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {'email': email}
    if path == '/auth/signup':
        payload.update({
            'password': 'Account-password-123',
            'company_name': 'Captcha contract company',
        })
    if mode != 'omitted':
        payload['captcha'] = '' if mode == 'empty' else None
    return payload


@pytest.mark.parametrize('enabled', [False, True])
@pytest.mark.parametrize('mode', ['omitted', 'empty', 'null'])
def test_auth_captcha__first_visitor__ignored_values_match_schema(
    contract_api_client, captcha_flow, settings, enabled, mode,
) -> None:
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'CAPTCHA': enabled}
    path, requirement_path, status = captcha_flow
    email = FIRST_EMAIL
    requirement = contract_api_client.get(requirement_path)
    assert requirement.status_code == 200
    assert requirement.json()['show_captcha'] is False

    response = contract_api_client.post(
        path, data=signup_or_reset_payload(path, email, mode), format='json',
    )

    assert response.status_code == status
    assert User.objects.filter(email=email).exists() == (
        path == '/auth/signup'
    )
    after = contract_api_client.get(requirement_path)
    assert after.status_code == 200
    assert after.json()['show_captcha'] is enabled


@pytest.mark.parametrize('mode', ['omitted', 'empty', 'null'])
def test_auth_captcha__repeat_visitor__missing_values_rejected(
    contract_api_client, captcha_flow, settings, mode,
) -> None:
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'CAPTCHA': True}
    path, requirement_path, status = captcha_flow
    first = contract_api_client.post(
        path,
        data=signup_or_reset_payload(path, FIRST_EMAIL, 'omitted'),
        format='json',
    )
    assert first.status_code == status
    requirement = contract_api_client.get(requirement_path)
    assert requirement.status_code == 200
    assert requirement.json()['show_captcha'] is True

    rejected = contract_api_client.post(
        path,
        data=signup_or_reset_payload(path, REPEAT_EMAIL, mode),
        format='json',
    )

    assert rejected.status_code == 400
    assert not User.objects.filter(email=REPEAT_EMAIL).exists()


def test_auth_captcha__repeat_visitor__provider_verified_value(
    contract_api_client, captcha_flow, settings, mocker,
) -> None:
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'CAPTCHA': True}
    path, requirement_path, status = captcha_flow
    first = contract_api_client.post(
        path,
        data=signup_or_reset_payload(path, FIRST_EMAIL, 'omitted'),
        format='json',
    )
    assert first.status_code == status
    requirement = contract_api_client.get(requirement_path)
    assert requirement.status_code == 200
    assert requirement.json()['show_captcha'] is True
    settings.DRF_RECAPTCHA_TESTING = False
    # Only the remote provider transport is replaced; validation stays real.
    opener = mocker.patch('drf_recaptcha.client.build_opener').return_value
    opener.open.return_value = BytesIO(b'{"success": true}')
    payload = signup_or_reset_payload(path, REPEAT_EMAIL, 'omitted')
    payload['captcha'] = 'verified-provider-token'

    response = contract_api_client.post(path, data=payload, format='json')

    assert response.status_code == status
    opener.open.assert_called_once()
    provider_request = opener.open.call_args[0][0]
    assert provider_request.full_url.endswith('/recaptcha/api/siteverify')
    sent = parse_qs(provider_request.data.decode('utf-8'))
    assert sent['response'] == ['verified-provider-token']
    assert sent['remoteip'] == [VISITOR_IP]
    assert User.objects.filter(email=REPEAT_EMAIL).exists() == (
        path == '/auth/signup'
    )


@pytest.mark.parametrize('path,base,secured', [
    ('/auth/signup', SignUpSerializer, SecuredSignUpSerializer),
    ('/auth/reset-password', ResetPasswordSerializer,
     SecuredResetPasswordSerializer),
])
def test_auth_captcha__metadata_keeps_runtime_constraints(
    http_contract, path, base, secured,
) -> None:
    operation = http_contract.document['paths'][path]['post']
    definition = operation['requestBody']['content']['application/json']
    schema = http_contract.resolve(definition['schema'])
    captcha = schema['properties']['captcha']
    assert 'captcha' not in schema.get('required', [])
    assert 'email' in schema['required']
    assert captcha.get('nullable') is True
    assert not captcha.get('minLength')
    assert 'show_captcha=true' in captcha['description']
    assert 'captcha' not in base().fields
    live_captcha = secured().fields['captcha']
    assert live_captcha.required is True
    assert live_captcha.allow_blank is False
    assert live_captcha.allow_null is False
