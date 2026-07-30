import pytest
from django.conf import settings

from src.ai.models import AIProviderConnection
from src.ai.providers import (
    ai_performers_active,
    mask_api_key,
    resolve_provider,
)
from src.processes.tests.fixtures import create_test_user

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def ai_performers_deployed(mocker):
    mocker.patch.dict(
        settings.PROJECT_CONF,
        {'AI_PERFORMERS': True},
    )
    mocker.patch.object(
        settings,
        'OPENROUTER_API_KEY',
        'platform-key',
    )


def _create_connection(account, api_key='sk-or-v1-0123456789abcdef'):
    return AIProviderConnection.objects.create(
        account=account,
        name='OpenRouter',
        base_url='https://byo.example.com/v1',
        api_key=api_key,
    )


def test_active__no_flag_no_connection__false():
    user = create_test_user()

    assert ai_performers_active(user.account) is False


def test_active__operator_flag__true():
    user = create_test_user()
    user.account.ai_performers_enabled = True
    user.account.save(update_fields=['ai_performers_enabled'])

    assert ai_performers_active(user.account) is True


def test_active__connection_only__true():
    user = create_test_user()
    _create_connection(user.account)

    assert ai_performers_active(user.account) is True


def test_active__inactive_connection__false():
    user = create_test_user()
    connection = _create_connection(user.account)
    connection.is_active = False
    connection.save(update_fields=['is_active'])

    assert ai_performers_active(user.account) is False


def test_active__deleted_connection__false():
    user = create_test_user()
    connection = _create_connection(user.account)
    connection.delete()

    assert ai_performers_active(user.account) is False


def test_active__env_flag_off__false(mocker):
    mocker.patch.dict(
        settings.PROJECT_CONF,
        {'AI_PERFORMERS': False},
    )
    user = create_test_user()
    user.account.ai_performers_enabled = True
    user.account.save(update_fields=['ai_performers_enabled'])
    _create_connection(user.account)

    assert ai_performers_active(user.account) is False


def test_resolve__connection__account_credentials_win():
    user = create_test_user()
    _create_connection(user.account, api_key='byo-key')

    base_url, api_key = resolve_provider(user.account)

    assert base_url == 'https://byo.example.com/v1'
    assert api_key == 'byo-key'


def test_resolve__no_connection__platform_fallback():
    user = create_test_user()

    base_url, api_key = resolve_provider(user.account)

    assert base_url == settings.OPENROUTER_BASE_URL
    assert api_key == 'platform-key'


def test_mask__long_key__prefix_and_suffix():
    assert mask_api_key('sk-or-v1-0123456789abcdef') == 'sk-or-v1••••cdef'


def test_mask__short_key__fully_hidden():
    assert mask_api_key('short-key') == '••••'
