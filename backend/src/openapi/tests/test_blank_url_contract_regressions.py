"""Blank avatar contracts execute real agent and user persistence."""

import json
from typing import Any, Optional, Tuple

from django.core.cache import caches
from django.core.validators import RegexValidator
from jsonschema.exceptions import ValidationError
import pytest
import requests

from src.accounts.enums import BillingPlanType
from src.accounts.models import User
from src.ai.enums import AIVendor
from src.ai.models import AIAgent, AIProvider
from src.ai.tests.fixtures import create_test_agent, create_test_provider
from src.generics.fields import DocURLField
from src.generics.tests.clients import PneumaticApiClient
from src.openapi.schema import PneumaticAutoSchema
from src.openapi.tests.http_contracts import HttpContract
from src.processes.tests.fixtures import create_test_account, create_test_owner


PATH = '/ai/agents'
PHOTO_URL = 'https://example.test/agent-photo.png'
PHOTO_PREFIX = 'https://example.test/'
PHOTO_BOUNDARY = PHOTO_PREFIX + 'x' * (1024 - len(PHOTO_PREFIX))
PHOTO_VALUES = [
    pytest.param('', id='blank'),
    pytest.param(None, id='null'),
    pytest.param(PHOTO_URL, id='uri'),
    pytest.param(PHOTO_BOUNDARY, id='maximum-length'),
]


@pytest.fixture
def agent_url_transport(settings: Any, mocker: Any) -> Any:
    settings.PRIVATE_API_CHECK_IP = False
    for alias in ('default', 'auth', 'session'):
        caches[alias].clear()
    response = requests.Response()
    response.status_code = 200
    response._content = json.dumps({
        'choices': [{'message': {'content': 'Hello world'}}],
    }).encode('utf-8')
    # Keep the provider service, vendor handler and response parser executable.
    transport = mocker.patch(
        'src.ai.services.handlers.base.requests.request',
        return_value=response,
    )
    for name in ('send_user_created_notification',
                 'send_user_updated_notification'):
        mocker.patch(f'src.accounts.services.user.{name}.delay')
    return transport


@pytest.fixture
def agent_url_context(
    contract_api_client: PneumaticApiClient,
    agent_url_transport: Any,
    db: None,
) -> Tuple[User, AIProvider]:
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED, billing_sync=False,
    )
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    provider.vendor = AIVendor.CUSTOM
    provider.save(update_fields=['vendor'])
    contract_api_client.token_authenticate(owner)
    return owner, provider


def agent_payload(provider: AIProvider, photo: Optional[str]) -> dict:
    return {
        'name': 'Avatar contract agent',
        'photo': photo,
        'provider_id': provider.id,
        'is_active': True,
        'model': 'openai/gpt-4o',
        'system_prompt': 'You are a helpful assistant.',
    }


def assert_agent_photo_and_reads(
    client: PneumaticApiClient,
    agent: AIAgent,
    owner: User,
    provider: AIProvider,
    photo: Optional[str],
) -> None:
    agent.refresh_from_db()
    agent.user.refresh_from_db()
    assert agent.photo == photo
    assert agent.user.photo == photo
    assert agent.user_id != owner.id
    assert agent.account_id == agent.user.account_id == owner.account_id
    assert agent.provider_id == provider.id
    assert agent.user.is_ai is True
    assert agent.user.first_name == agent.name
    assert agent.is_deleted is False
    assert agent.user.is_deleted is False

    detail = client.get(f'{PATH}/{agent.id}')
    assert detail.status_code == 200
    assert detail.json()['id'] == agent.id
    assert detail.json()['photo'] == photo
    assert detail.json()['provider_id'] == provider.id
    listing = client.get(PATH)
    assert listing.status_code == 200
    assert [(row['id'], row['photo']) for row in listing.json()] == [
        (agent.id, photo),
    ]
    limited = client.get(PATH, data={'limit': 1})
    assert limited.status_code == 200
    assert limited.json()['count'] == 1
    assert [(row['id'], row['photo'])
            for row in limited.json()['results']] == [(agent.id, photo)]
    owner.refresh_from_db()
    provider.refresh_from_db()
    assert owner.photo is None
    assert owner.is_deleted is False
    assert provider.is_deleted is False


@pytest.mark.parametrize('photo', PHOTO_VALUES)
def test_agent_photo__create_real_service__persists_and_reads(
    contract_api_client: PneumaticApiClient,
    agent_url_context: Tuple[User, AIProvider],
    agent_url_transport: Any,
    photo: Optional[str],
) -> None:
    owner, provider = agent_url_context
    users_before = User.objects.on_account(owner.account_id).count()

    response = contract_api_client.post(
        PATH, data=agent_payload(provider, photo), format='json',
    )

    assert response.status_code == 201
    agent = AIAgent.objects.get(id=response.json()['id'])
    assert response.json()['photo'] == photo
    assert AIAgent.objects.on_account(owner.account_id).count() == 1
    assert (
        User.objects.on_account(owner.account_id).count() == users_before + 1
    )
    assert_agent_photo_and_reads(
        contract_api_client, agent, owner, provider, photo,
    )
    agent_url_transport.assert_called_once()
    arguments = agent_url_transport.call_args.kwargs
    assert arguments['method'] == 'POST'
    assert arguments['url'] == f'{provider.base_url}/chat/completions'
    assert arguments['json']['model'] == 'openai/gpt-4o'
    assert arguments['json']['messages'][-1]['content'] == 'Say "Hello world"'


@pytest.mark.parametrize('photo', PHOTO_VALUES)
def test_agent_photo__patch_real_service__synchronizes_user_and_reads(
    contract_api_client: PneumaticApiClient,
    agent_url_context: Tuple[User, AIProvider],
    agent_url_transport: Any,
    photo: Optional[str],
) -> None:
    owner, provider = agent_url_context
    previous_photo = 'https://example.test/previous-agent.png'
    agent = create_test_agent(
        account=owner.account, provider=provider, photo=previous_photo,
    )
    agent.user.photo = previous_photo
    agent.user.save(update_fields=['photo'])
    previous_user_id = agent.user_id
    users_before = User.objects.on_account(owner.account_id).count()

    response = contract_api_client.patch(
        f'{PATH}/{agent.id}', data={'photo': photo}, format='json',
    )

    assert response.status_code == 200
    assert response.json()['id'] == agent.id
    assert response.json()['photo'] == photo
    assert_agent_photo_and_reads(
        contract_api_client, agent, owner, provider, photo,
    )
    assert agent.user_id == previous_user_id
    assert User.objects.on_account(owner.account_id).count() == users_before
    assert AIAgent.objects.on_account(owner.account_id).count() == 1
    agent_url_transport.assert_not_called()


@pytest.mark.parametrize('method', ['post', 'patch'])
def test_agent_photo__exceeds_maximum__rejects_without_mutation(
    contract_api_client: PneumaticApiClient,
    agent_url_context: Tuple[User, AIProvider],
    agent_url_transport: Any,
    method: str,
) -> None:
    owner, provider = agent_url_context
    photo = PHOTO_BOUNDARY + 'x'
    agent = create_test_agent(
        account=owner.account, provider=provider, photo=PHOTO_URL,
    )
    agent.user.photo = PHOTO_URL
    agent.user.save(update_fields=['photo'])
    users_before = User.objects.on_account(owner.account_id).count()
    payload = agent_payload(provider, photo) if method == 'post' else {
        'photo': photo,
    }
    path = PATH if method == 'post' else f'{PATH}/{agent.id}'

    response = getattr(contract_api_client, method)(
        path, data=payload, format='json',
    )

    assert response.status_code == 400
    assert response.json()['code'] == 'validation_error'
    assert response.json()['details']['name'] == 'photo'
    assert '1024' in response.json()['details']['reason']
    assert_agent_photo_and_reads(
        contract_api_client, agent, owner, provider, PHOTO_URL,
    )
    assert User.objects.on_account(owner.account_id).count() == users_before
    assert AIAgent.objects.on_account(owner.account_id).count() == 1
    agent_url_transport.assert_not_called()


@pytest.mark.parametrize('direction,access', [
    ('response', 'read_only'), ('request', 'write_only'),
])
def test_blank_url__synthetic_field__preserves_constraints_and_metadata(
    direction: str, access: str,
) -> None:
    example = 'https://allowed.example/avatar.png'
    field = DocURLField(
        allow_blank=True, allow_null=True, min_length=32, max_length=64,
        default=example, example=example, help_text='Avatar URL',
        validators=[RegexValidator(r'^https://allowed\.example/')],
        **{access: True},
    )
    schema = PneumaticAutoSchema()
    mapped = schema._map_serializer_field(field, direction)
    schema._insert_field_validators(field, mapped)
    contract = HttpContract({'paths': {}})
    response = direction == 'response'

    annotation = 'readOnly' if access == 'read_only' else 'writeOnly'
    assert mapped[annotation] is True
    assert mapped['description'] == 'Avatar URL'
    assert mapped['default'] == example
    assert mapped['example'] == example
    for value in ('', None, example, 'https://allowed.example/' + 'x' * 40):
        contract.validate(mapped, value, response=response)
    for value in (
        'https://allowed.example/x',
        'https://allowed.example/' + 'x' * 41,
        'https://another.example/avatar.png',
        'not-a-url',
    ):
        with pytest.raises(ValidationError):
            contract.validate(mapped, value, response=response)
    with pytest.raises(ValidationError):
        contract.validate(mapped, example, response=not response)
    previous = json.dumps(mapped, sort_keys=True)
    schema._insert_field_validators(field, mapped)
    assert json.dumps(mapped, sort_keys=True) == previous
