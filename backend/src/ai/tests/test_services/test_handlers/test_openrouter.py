import pytest

from src.ai.enums import AIVendor
from src.ai.services.config import AI_VENDORS_CONFIG
from src.ai.services.handlers import OpenRouterHandler
from src.ai.tests.fixtures import create_test_provider
from src.processes.tests.fixtures import create_test_account

pytestmark = pytest.mark.django_db


def test_auth_headers__api_key__ok(settings):

    """ Auth headers """

    # arrange
    settings.FRONTEND_URL = 'https://app.example.com'
    account = create_test_account()
    api_key = 'sk-or-v1-example'
    provider = create_test_provider(account=account, api_key=api_key)
    handler = OpenRouterHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENROUTER],
    )

    # act
    result = handler._auth_headers()

    # assert
    assert result == {
        'Authorization': 'Bearer sk-or-v1-example',
        'HTTP-Referer': 'https://app.example.com',
        'X-Title': 'Pneumatic',
    }


def test_is_chat_model__text_output_modality__true():

    """ Text output modality """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenRouterHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENROUTER],
    )
    item = {
        'id': 'openai/gpt-4o',
        'architecture': {'output_modalities': ['text', 'image']},
    }

    # act
    result = handler._is_chat_model(item=item)

    # assert
    assert result is True


def test_is_chat_model__non_text_output_modality__false():

    """ Non-text output modality """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenRouterHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENROUTER],
    )
    item = {
        'id': 'openai/dall-e-3',
        'architecture': {'output_modalities': ['image']},
    }

    # act
    result = handler._is_chat_model(item=item)

    # assert
    assert result is False


def test_is_chat_model__architecture_not_set__true():

    """ Architecture missing """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenRouterHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENROUTER],
    )
    item = {'id': 'openai/gpt-4o'}

    # act
    result = handler._is_chat_model(item=item)

    # assert
    assert result is True


def test_is_chat_model__architecture_none__true():

    """ Architecture is None """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenRouterHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENROUTER],
    )
    item = {'id': 'openai/gpt-4o', 'architecture': None}

    # act
    result = handler._is_chat_model(item=item)

    # assert
    assert result is True


def test_is_chat_model__output_modalities_not_set__true():

    """ Output modalities missing """

    # arrange
    account = create_test_account()
    provider = create_test_provider(account=account)
    handler = OpenRouterHandler(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENROUTER],
    )
    item = {'id': 'openai/gpt-4o', 'architecture': {}}

    # act
    result = handler._is_chat_model(item=item)

    # assert
    assert result is True
