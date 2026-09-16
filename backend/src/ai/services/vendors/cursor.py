from typing import Any, List
from urllib.parse import urlparse

from src.ai.services.vendors.openai_compatible import OpenAICompatibleVendor


class CursorVendor(OpenAICompatibleVendor):

    def _create_url(self, path: str) -> str:
        parsed = urlparse(self.instance.base_url)
        return f'{parsed.scheme}://{parsed.netloc}/v1/{path}'

    def get_models(self) -> List[dict]:
        _status, payload = self._request(
            method='GET',
            url=self._create_url('models'),
            headers=self._auth_headers(),
        )
        return self._parse_models(payload)

    def _parse_models(self, payload: Any) -> List[dict]:
        """Parse a Cursor Cloud Agents models list payload.

        Docs: https://cursor.com/docs/cloud-agent/api/endpoints

        Example:

            {
                "items": [
                    {
                        "id": "composer-2",
                        "displayName": "Composer 2"
                    }
                ]
            }

        """

        models = []
        for item in payload['items']:
            models.append(
                {
                    'slug': item['id'],
                    'name': item.get('displayName', item['id']),
                },
            )
        return models
