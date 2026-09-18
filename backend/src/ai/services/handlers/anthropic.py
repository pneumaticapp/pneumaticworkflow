from typing import Any, List, Optional

from src.ai.enums import OpenAIRole
from src.ai.services.handlers.base import BaseHandler


class AnthropicHandler(BaseHandler):
    API_VERSION = '2023-06-01'
    DEFAULT_MAX_TOKENS = 1024

    def _auth_headers(self) -> dict:
        return {
            'x-api-key': self.instance.api_key,
            'anthropic-version': self.API_VERSION,
            'content-type': 'application/json',
        }

    def _parse_error(
        self,
        http_status: int,
        response_data: Optional[dict],
    ) -> Optional[str]:
        """Extract `error.message` from an Anthropic API error body.

        Docs: https://platform.claude.com/docs/en/api/errors

        Example:

            {
                "type": "error",
                "error": {
                    "type": "not_found_error",
                    "message": "The requested resource does not exist."
                },
                "request_id": "req_011CSHoEeqs5C35K2UUqR7Fy"
            }

        """

        return super()._parse_error(
            http_status=http_status,
            response_data=response_data,
        )

    def get_models(self) -> List[dict]:
        _status, payload = self._request(
            method='GET',
            url=self.get_models_url(),
            headers=self._auth_headers(),
        )
        return self._parse_models(payload)

    def _parse_models(self, payload: Any) -> List[dict]:

        """Parse an Anthropic Models API list payload.

        Docs: https://platform.claude.com/docs/en/api/models/list

        Example:

            {
                "data": [
                    {
                        "id": "claude-sonnet-4-20250514",
                        "type": "model",
                        "display_name": "Claude Sonnet 4",
                        "created_at": "2025-05-14T00:00:00Z"
                    }
                ],
                "has_more": false,
                "first_id": "claude-sonnet-4-20250514",
                "last_id": "claude-sonnet-4-20250514"
            }

        """

        raw_models = payload['data']
        models = []
        for item in raw_models:
            models.append(
                {
                    'slug': item['id'],
                    'name': item['display_name'],
                },
            )
        return models

    def get_completion(
        self,
        system_message: str,
        user_message: str,
        model: str,
    ) -> str:
        _status, payload = self._request(
            method='POST',
            url=self.get_chat_url(),
            headers=self._auth_headers(),
            data={
                'model': model,
                'max_tokens': self.DEFAULT_MAX_TOKENS,
                'system': system_message,
                'messages': [
                    {
                        'role': OpenAIRole.USER,
                        'content': user_message,
                    },
                ],
            },
            timeout=self.completion_timeout,
        )
        return self._parse_completion(payload)

    def _parse_completion(self, payload: Any) -> str:
        """Parse an Anthropic Messages API payload.

        Docs: https://platform.claude.com/docs/en/api/messages

        Example:

            {
                "id": "msg_01XFDUDYJgAACzvnptvVoYEL",
                "type": "message",
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "Hello!"
                    }
                ],
                "stop_reason": "end_turn"
            }

        """
        texts = []
        for block in payload['content']:
            if block.get('type') == 'text':
                texts.append(block['text'])
        return ''.join(texts)
