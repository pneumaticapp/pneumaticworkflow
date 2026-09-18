from typing import Any, List

from src.ai.services.handlers.openai import OpenAIHandler


class CursorHandler(OpenAIHandler):

    def get_models_url(self) -> str:
        return f'{self.instance.base_url}/v1/models'

    def get_chat_url(self, **kwargs) -> str:
        return f'{self.instance.base_url}/v1/chat/completions'

    def get_models(self) -> List[dict]:
        _status, payload = self._request(
            method='GET',
            url=self.get_models_url(),
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
