"""Public/embed HTTP contracts for conditional CAPTCHA requirements."""

from io import BytesIO
from typing import Tuple
from urllib.parse import parse_qs

from django.core.cache import caches
import pytest

from src.processes.models.templates.template import Template
from src.processes.models.workflows.workflow import Workflow
from src.processes.tests.fixtures import (
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db

VISITOR_IP = '198.51.100.19'


@pytest.fixture(autouse=True)
def public_contract_environment(settings) -> None:
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'CAPTCHA': True}
    settings.PRIVATE_API_CHECK_IP = False
    for alias in ('default', 'auth', 'session'):
        caches[alias].clear()


@pytest.fixture(params=['public', 'embed'])
def public_template(request, contract_api_client) -> Tuple[Template, int]:
    embedded = request.param == 'embed'
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=True,
        is_public=not embedded,
        is_embedded=embedded,
        tasks_count=1,
    )
    token = template.embed_id if embedded else template.public_id
    contract_api_client.credentials(
        HTTP_X_PUBLIC_AUTHORIZATION=f'Token {token}',
        HTTP_X_FORWARDED_FOR=VISITOR_IP,
        REMOTE_ADDR=VISITOR_IP,
    )
    return template, 204 if embedded else 200


@pytest.mark.parametrize('payload', [
    None, {}, {'captcha': ''}, {'captcha': None},
])
def test_public_run__disabled_captcha__ignored_optional_values(
    contract_api_client, public_template, settings, payload,
) -> None:
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'CAPTCHA': False}
    template, status = public_template
    # Disabling CAPTCHA also permits repeated requests from the same visitor.
    for _ in range(2):
        details = contract_api_client.get('/templates/public')
        assert details.status_code == 200
        assert details.json()['show_captcha'] is False
        if payload is None:
            response = contract_api_client.post('/templates/public/run')
        else:
            response = contract_api_client.post(
                '/templates/public/run', data=payload, format='json',
            )
        assert response.status_code == status
    workflows = Workflow.objects.filter(template=template)
    assert workflows.count() == 2
    assert all(workflow.is_external for workflow in workflows)


@pytest.mark.parametrize('repeated_payload', [
    {}, {'captcha': ''}, {'captcha': None},
])
def test_public_run__first_visitor_optional_then_required_captcha(
    contract_api_client, public_template, repeated_payload,
) -> None:
    template, status = public_template
    first_details = contract_api_client.get('/templates/public')
    assert first_details.status_code == 200
    assert first_details.json()['show_captcha'] is False
    first = contract_api_client.post(
        '/templates/public/run', data={'fields': {}}, format='json',
    )
    assert first.status_code == status
    repeated_details = contract_api_client.get('/templates/public')
    assert repeated_details.status_code == 200
    assert repeated_details.json()['show_captcha'] is True
    repeated = contract_api_client.post(
        '/templates/public/run', data=repeated_payload, format='json',
    )
    assert repeated.status_code == 400
    assert Workflow.objects.filter(template=template).count() == 1


def test_public_run__repeat_visitor__provider_verified_captcha(
    contract_api_client, public_template, settings, mocker,
) -> None:
    template, status = public_template
    first = contract_api_client.post(
        '/templates/public/run', data={}, format='json',
    )
    assert first.status_code == status
    settings.DRF_RECAPTCHA_TESTING = False
    # Replace only the provider's HTTP transport, retaining real validation.
    opener = mocker.patch('drf_recaptcha.client.build_opener').return_value
    opener.open.return_value = BytesIO(b'{"success": true}')
    repeated = contract_api_client.post(
        '/templates/public/run',
        data={'captcha': 'verified-provider-token'}, format='json',
    )
    assert repeated.status_code == status
    opener.open.assert_called_once()
    provider_request = opener.open.call_args[0][0]
    assert provider_request.full_url.endswith('/recaptcha/api/siteverify')
    sent = parse_qs(provider_request.data.decode('utf-8'))
    assert sent['response'] == ['verified-provider-token']
    assert sent['remoteip'] == [VISITOR_IP]
    assert Workflow.objects.filter(template=template).count() == 2
