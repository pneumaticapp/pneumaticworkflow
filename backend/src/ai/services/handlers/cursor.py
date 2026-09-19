from typing import Any, List
from src.ai.services.handlers.openai import OpenAIHandler


class CursorHandler(OpenAIHandler):

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
