from typing import Optional

import requests

VERIFY_TIMEOUT_SEC = 10


def verify_api_key(base_url: str, api_key: str) -> Optional[bool]:

    """ Ask the provider whether the key is usable. Returns True or
        False when the provider answered, None when it could not be
        reached — callers should not block saving on an outage.

        OpenRouter has a dedicated key-info endpoint; any other
        OpenAI-compatible host is probed with the models list, which
        every such API authenticates. """

    base = base_url.rstrip('/')
    path = '/key' if 'openrouter.ai' in base else '/models'
    try:
        response = requests.get(
            base + path,
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=VERIFY_TIMEOUT_SEC,
        )
    except requests.RequestException:
        return None
    if response.status_code in (401, 403):
        return False
    if response.ok:
        return True
    return None
