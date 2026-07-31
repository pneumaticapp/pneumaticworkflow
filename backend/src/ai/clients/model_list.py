from typing import List, Optional

import requests

MODELS_TIMEOUT_SEC = 10

# The execution pipeline relies on provider-enforced structured
# outputs; models without the capability cannot be AI performers
STRUCTURED_OUTPUTS_PARAM = 'structured_outputs'


def list_structured_output_models(
    base_url: str,
    api_key: Optional[str] = None,
) -> Optional[List[dict]]:

    """ Fetch the provider's model catalog and keep only models
        usable as AI performers. Returns None when the provider
        could not be reached or answered abnormally — callers fall
        back to manual slug entry """

    headers = {}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    try:
        response = requests.get(
            base_url.rstrip('/') + '/models',
            headers=headers,
            timeout=MODELS_TIMEOUT_SEC,
        )
    except requests.RequestException:
        return None
    if not response.ok:
        return None
    try:
        data = response.json()['data']
    except (ValueError, KeyError, TypeError):
        return None
    if not isinstance(data, list):
        return None
    models = []
    for item in data:
        if not isinstance(item, dict):
            continue
        slug = item.get('id')
        if not slug:
            continue
        supported = item.get('supported_parameters') or ()
        if STRUCTURED_OUTPUTS_PARAM not in supported:
            continue
        models.append({
            'slug': slug,
            'name': item.get('name') or slug,
        })
    models.sort(key=lambda model: model['name'].lower())
    return models
