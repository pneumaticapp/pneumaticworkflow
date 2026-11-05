"""Real template/service exchanges, mocking only the external AI provider."""

from types import SimpleNamespace
from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from jsonschema.exceptions import ValidationError
import openai
import pytest

from src.accounts.enums import BillingPlanType
from src.ai.models import OpenAiMessage, OpenAiPrompt
from src.processes.enums import DueDateRule, PresetType, SysTemplateType
from src.processes.models.templates.system_template import SystemTemplate
from src.processes.models.templates.template import (
    Template,
    TemplateIntegrations,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_template,
    create_test_template_preset,
)

pytestmark = pytest.mark.django_db
UserModel = get_user_model()


def _create_integrated_template(owner: UserModel, name: str) -> Template:
    template = create_test_template(owner, is_active=True, name=name)
    TemplateIntegrations.objects.get_or_create(
        template=template, defaults={'account': owner.account},
    )
    return template


@pytest.fixture
def template_service_owner(contract_api_client) -> UserModel:
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED, billing_sync=False,
    )
    owner = create_test_owner(account=account)
    contract_api_client.token_authenticate(owner)
    return owner


@pytest.fixture
def ai_provider(settings, monkeypatch) -> Mock:
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'AI': True}
    settings.OPENAI_API_KEY = 'contract-provider-key'
    settings.OPENAI_API_ORG = 'contract-provider-org'
    prompt = OpenAiPrompt.objects.create(is_active=True)
    OpenAiMessage.objects.create(
        prompt=prompt, order=1, content='Generate {{ user_description }}',
    )
    provider = Mock(return_value=SimpleNamespace(choices=[SimpleNamespace(
        message=SimpleNamespace(content=(
            '1. Collect request | Record the request details.\n'
            '2. Approve request | Review and approve the request.'
        )),
    )]))
    monkeypatch.setattr(openai.ChatCompletion, 'create', provider)
    cache.clear()
    return provider


def test_generated_steps__real_service__matches_contract(
    contract_api_client, ai_provider,
) -> None:
    response = contract_api_client.get(
        '/services/steps-by-description', data={'description': 'Approvals'},
    )

    assert response.status_code == 200
    body = response.json()
    assert body['name'] == 'Approvals'
    assert len(body['tasks']) == 2
    assert body['tasks'][0]['description'] == 'Record the request details.'
    assert body['tasks'][0]['api_name']
    assert body['tasks'][1]['conditions'][0]['rules'][0]['predicates'][0][
        'field'
    ] == body['tasks'][0]['api_name']
    ai_provider.assert_called_once()


def test_generated_steps__missing_description__matches_error_contract(
    contract_api_client, ai_provider,
) -> None:
    response = contract_api_client.get('/services/steps-by-description')

    assert response.status_code == 400
    ai_provider.assert_not_called()


def test_generated_steps__provider_failure__matches_error_contract(
    contract_api_client, ai_provider,
) -> None:
    ai_provider.side_effect = openai.error.APIError('Provider unavailable')

    response = contract_api_client.get(
        '/services/steps-by-description', data={'description': 'Approvals'},
    )

    assert response.status_code == 400
    ai_provider.assert_called_once()


def test_template_ai__real_preview__matches_contract(
    contract_api_client, template_service_owner, ai_provider,
) -> None:
    owner = template_service_owner
    templates_before = Template.objects.count()
    generations_before = owner.account.ai_templates_generations

    response = contract_api_client.post(
        '/templates/ai', data={'description': 'Approvals'}, format='json',
    )

    assert response.status_code == 200
    body = response.json()
    assert body['name'] == 'Approvals'
    assert len(body['tasks']) == 2
    assert body['tasks'][0]['description'] == 'Record the request details.'
    assert body['tasks'][0]['raw_performers'][0]['source_id'] == owner.id
    assert isinstance(body['tasks'][0]['raw_performers'][0]['source_id'], int)
    assert Template.objects.count() == templates_before
    owner.account.refresh_from_db()
    assert owner.account.ai_templates_generations == generations_before + 1
    ai_provider.assert_called_once()


def test_template_ai__missing_description__matches_error_contract(
    contract_api_client, template_service_owner, ai_provider,
) -> None:
    response = contract_api_client.post(
        '/templates/ai', data={}, format='json',
    )

    assert response.status_code == 400
    ai_provider.assert_not_called()


@pytest.mark.parametrize('key_style', ['snake', 'camel', 'mixed'])
def test_system_import__real_service__matches_contract(
    contract_api_client, template_service_owner, key_style,
) -> None:
    owner = template_service_owner
    owner.is_staff = True
    owner.save(update_fields=['is_staff'])
    if key_style == 'snake':
        step = {
            'step_name': 'Review request',
            'step_description': 'Review the submitted request.',
            'due_in': {'days': 0, 'hours': 1, 'minutes': 30},
        }
    elif key_style == 'camel':
        step = {
            'stepName': 'Review request',
            'stepDescription': 'Review the submitted request.',
            'dueIn': {'days': 0, 'hours': 1, 'minutes': 30},
        }
    else:
        step = {
            'stepName': 'Review request',
            'step_description': 'Review the submitted request.',
            'dueIn': {'days': 0, 'hours': 1, 'minutes': 30},
        }

    response = contract_api_client.post(
        '/templates/system/import',
        data={'templates': [{
            'title': 'Contract library', 'intro': 'Request approval process.',
            'category': 'Contracts', 'steps': [step],
            'kickoff': {'requestSubject': 'text'},
        }]},
        format='json',
    )

    assert response.status_code == 204
    assert response.content == b''
    template = SystemTemplate.objects.get(name='Contract library')
    assert template.type == SysTemplateType.LIBRARY
    assert template.category.name == 'Contracts'
    task = template.template['tasks'][0]
    assert task['name'] == 'Review request'
    assert task['description'] == 'Review the submitted request.'
    assert task['raw_due_date']['rule'] == DueDateRule.AFTER_TASK_STARTED
    assert task['raw_due_date']['duration'] == '00 01:30:00'
    assert task['raw_due_date']['source_id'] == task['api_name']
    assert template.template['kickoff']['fields'][0]['name'] == (
        'Request subject'
    )


def test_system_import__missing_step_description__matches_error_contract(
    contract_api_client, template_service_owner,
) -> None:
    owner = template_service_owner
    owner.is_staff = True
    owner.save(update_fields=['is_staff'])

    response = contract_api_client.post(
        '/templates/system/import',
        data={'templates': [{
            'title': 'Invalid library', 'intro': 'Invalid process.',
            'category': 'Contracts', 'steps': [{'step_name': 'Review'}],
        }]},
        format='json',
    )

    assert response.status_code == 400
    assert not SystemTemplate.objects.filter(name='Invalid library').exists()


@pytest.mark.parametrize('enabled', [False, True])
def test_template_integrations__real_projection__matches_contract(
    contract_api_client, template_service_owner, enabled,
) -> None:
    owner = template_service_owner
    template = _create_integrated_template(owner, 'Integrations')
    TemplateIntegrations.objects.filter(template=template).update(
        shared=enabled, api=enabled, zapier=enabled, webhooks=enabled,
        api_date=timezone.now() if enabled else None,
    )
    cache.delete(f't_int:{template.id}')

    response = contract_api_client.get(
        f'/templates/{template.id}/integrations',
    )

    assert response.status_code == 200
    assert response.json() == {
        'id': template.id, 'shared': enabled, 'api': enabled,
        'zapier': enabled, 'webhooks': enabled,
    }


@pytest.mark.parametrize('filtered', [False, True])
def test_template_integrations_list__real_projection__matches_contract(
    contract_api_client, template_service_owner, filtered,
) -> None:
    owner = template_service_owner
    first = _create_integrated_template(owner, 'First')
    second = _create_integrated_template(owner, 'Second')

    response = contract_api_client.get(
        '/templates/integrations',
        data={'template_id': str(first.id)} if filtered else {},
    )

    assert response.status_code == 200
    body = response.json()
    assert {row['id'] for row in body} == (
        {first.id} if filtered else {first.id, second.id}
    )
    for row in body:
        assert row == {
            'id': row['id'], 'shared': False, 'api': False,
            'zapier': False, 'webhooks': False,
        }


def test_template_integrations__unknown_id__matches_error_contract(
    contract_api_client, template_service_owner,
) -> None:
    response = contract_api_client.get('/templates/2147483647/integrations')

    assert response.status_code == 404


def test_template_integrations_list__invalid_filter__matches_error_contract(
    contract_api_client, template_service_owner,
) -> None:
    response = contract_api_client.get(
        '/templates/integrations', data={'template_id': 'invalid'},
    )

    assert response.status_code == 400


def test_preset_default__real_service_without_body__matches_contract(
    contract_api_client, template_service_owner,
) -> None:
    owner = template_service_owner
    template = create_test_template(owner, is_active=True)
    previous = create_test_template_preset(
        template, owner, name='Previous', is_default=True,
        type=PresetType.PERSONAL,
    )
    preset = create_test_template_preset(
        template, owner, name='New', type=PresetType.PERSONAL,
    )

    response = contract_api_client.post(
        f'/templates/presets/{preset.id}/default',
    )

    assert response.status_code == 204
    assert response.content == b''
    preset.refresh_from_db()
    previous.refresh_from_db()
    assert preset.is_default
    assert not previous.is_default


def test_preset_default__unknown_id__matches_error_contract(
    contract_api_client, template_service_owner,
) -> None:
    response = contract_api_client.post(
        '/templates/presets/2147483647/default',
    )

    assert response.status_code == 403


def test_template_service_schemas__match_public_projections(
    http_contract,
) -> None:
    document = http_contract.document
    assert 'requestBody' not in document['paths'][
        '/templates/presets/{id}/default'
    ]['post']
    for path in ('/templates/integrations', '/templates/{id}/integrations'):
        response = document['paths'][path]['get']['responses']['200']
        schema = http_contract.resolve(
            response['content']['application/json']['schema'],
        )
        if schema.get('type') == 'array':
            schema = http_contract.resolve(schema['items'])
        assert set(schema['properties']) == {
            'id', 'shared', 'api', 'zapier', 'webhooks',
        }

    response = document['paths']['/services/steps-by-description'][
        'get'
    ]['responses']['200']
    generated = http_contract.resolve(
        response['content']['application/json']['schema'],
    )
    task = http_contract.resolve(generated['properties']['tasks']['items'])
    assert {'api_name', 'conditions'} <= set(task['properties'])

    request = document['paths']['/templates/system/import'][
        'post'
    ]['requestBody']
    body = http_contract.resolve(
        request['content']['application/json']['schema'],
    )
    template = http_contract.resolve(body['properties']['templates']['items'])
    step = template['properties']['steps']['items']
    for name in ('step_name', 'stepName'):
        with pytest.raises(ValidationError):
            http_contract.validate(step, {name: 'Review'}, response=False)
