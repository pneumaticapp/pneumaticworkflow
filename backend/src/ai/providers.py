from typing import Optional, Tuple

from django.conf import settings

from src.ai.models import AIProviderConnection

# Enough of a key to recognise it, never enough to use it
MASK_PREFIX_LEN = 8
MASK_SUFFIX_LEN = 4


def get_provider_connection(account) -> Optional[AIProviderConnection]:
    return (
        AIProviderConnection.objects
        .on_account(account.id)
        .active()
        .order_by('id')
        .first()
    )


def ai_performers_active(account) -> bool:

    """ Feature availability for an account: the deployment flag must
        be on, then either the operator-set account flag or a saved
        provider connection (BYO key) switches the feature on. """

    if not settings.PROJECT_CONF['AI_PERFORMERS']:
        return False
    if account.ai_performers_enabled:
        return True
    return (
        AIProviderConnection.objects
        .on_account(account.id)
        .active()
        .exists()
    )


def resolve_provider(account) -> Tuple[str, Optional[str]]:

    """ Credentials for model calls: the account's own connection
        wins, the platform key from settings is the fallback. """

    connection = get_provider_connection(account)
    if connection:
        return connection.base_url, connection.api_key
    return settings.OPENROUTER_BASE_URL, settings.OPENROUTER_API_KEY


def mask_api_key(api_key: str) -> str:
    if len(api_key) <= MASK_PREFIX_LEN + MASK_SUFFIX_LEN:
        return '••••'
    return (
        f'{api_key[:MASK_PREFIX_LEN]}'
        f'••••'
        f'{api_key[-MASK_SUFFIX_LEN:]}'
    )
