from typing import Any, List, Optional
from urllib.parse import urlparse

from django.conf import settings

from src.ai.enums import AIVendor, OpenAIRole
from src.ai.services.vendors.base import BaseVendor


class OpenAICompatibleVendor(BaseVendor):
    API_PATH_SUFFIXES = {
        AIVendor.GROQ: '/openai/v1',
        AIVendor.FIREWORKS: '/inference/v1',
        AIVendor.HUGGINGFACE: '/v1',
    }

    def _api_base(self) -> str:
        base = super()._api_base()
        suffix = self.API_PATH_SUFFIXES.get(self.instance.vendor)
        if not suffix:
            return base
        normalized_suffix = suffix.rstrip('/')
        path = (urlparse(base).path or '').rstrip('/')
        if path.endswith(normalized_suffix):
            return base
        return f'{base}{normalized_suffix}'

    def _auth_headers(self) -> dict:
        headers = {
            'Authorization': f'Bearer {self.instance.api_key}',
        }
        if self.instance.vendor == AIVendor.OPENROUTER:
            headers['HTTP-Referer'] = (
                getattr(settings, 'FRONTEND_URL', None)
                or 'https://pneumatic.app'
            )
            headers['X-Title'] = 'Pneumatic'
        return headers

    def _parse_error(
        self,
        http_status: int,
        response_data: Optional[dict],
    ) -> Optional[str]:
        """Extract `error.message` from an OpenAI-compatible error body.

        Docs: https://platform.openai.com/docs/guides/error-codes

        Example:
            {
                "error": {
                    "message": "Incorrect API key provided.",
                    "type": "invalid_request_error",
                    "param": null,
                    "code": "invalid_api_key"
                }
            }

        """

        return super()._parse_error(
            http_status=http_status,
            response_data=response_data,
        )

    def get_models(self) -> List[dict]:
        _status, payload = self._request(
            method='GET',
            url=self._create_url('models'),
            headers=self._auth_headers(),
        )
        return self._parse_models(payload)

    def _parse_models(self, payload: Any) -> List[dict]:
        """Parse an OpenAI-compatible models list payload.

        Docs: https://platform.openai.com/docs/api-reference/models/list

        Example:

            {
                "object": "list",
                "data": [
                    {
                        "id": "gpt-4o",
                        "object": "model",
                        "created": 1686935002,
                        "owned_by": "openai"
                    }
                ]
            }

        OpenRouter items may also include a human-readable "name".

        """
        raw_models = payload['data']
        models = []
        for item in raw_models:
            models.append(
                {
                    'slug': item['id'],
                    'name': item.get('name', item['id']),
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
            url=self._create_url('chat/completions'),
            headers=self._auth_headers(),
            json={
                'model': model,
                'messages': [
                    {
                        'role': OpenAIRole.SYSTEM,
                        'content': system_message,
                    },
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
        """Parse an OpenAI-compatible chat completion payload.

        Docs: https://platform.openai.com/docs/api-reference/chat/object

        Example:

            {
                "id": "chatcmpl-123",
                "object": "chat.completion",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Hello!"
                        },
                        "finish_reason": "stop"
                    }
                ]
            }

        """
        return payload['choices'][0]['message']['content']
