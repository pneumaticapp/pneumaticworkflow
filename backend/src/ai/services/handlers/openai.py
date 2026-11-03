from typing import Any, List, Optional
from src.ai.enums import OpenAIRole
from src.ai.services.handlers.base import BaseHandler


class OpenAIHandler(BaseHandler):

    NON_CHAT_MODEL_KEYWORDS = (
        'embed',
        'whisper',
        'tts',
        'transcribe',
        'dall-e',
        'image',
        'moderation',
        'realtime',
        'audio',
        'sora',
        'davinci',
        'babbage',
        'guard',
    )

    def _auth_headers(self) -> dict:
        return {
            'Authorization': f'Bearer {self.provider.api_key}',
        }

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
            if self._is_chat_model(item):
                models.append(
                    {
                        'slug': item['id'],
                        'name': item.get('name', item['id']),
                    },
                )
        return models

    def _is_chat_model(self, item: dict) -> bool:

        """The models list has no model type field,
        so non-chat models are detected by keywords in the id."""

        model_id = item['id'].lower()
        return not any(
            keyword in model_id
            for keyword in self.NON_CHAT_MODEL_KEYWORDS
        )

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
