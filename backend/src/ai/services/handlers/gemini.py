from typing import Any, List, Optional
from src.ai.services.handlers.base import BaseHandler


class GeminiHandler(BaseHandler):

    models_params = {'pageSize': 1000}

    def _auth_headers(self) -> dict:
        return {
            'x-goog-api-key': self.provider.api_key,
            'content-type': 'application/json',
        }

    def _parse_error(
        self,
        http_status: int,
        response_data: Optional[dict],
    ) -> Optional[str]:
        """Extract `error.message` from a Gemini GenerateContent error body.

        Docs: https://ai.google.dev/gemini-api/docs/generate-content/api-errors

        Example:
            {
                "error": {
                    "code": 400,
                    "message": "API key not valid.",
                    "status": "INVALID_ARGUMENT",
                    "details": [{
                        "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                        "reason": "API_KEY_INVALID"
                    }]
                }
            }

        """

        return super()._parse_error(
            http_status=http_status,
            response_data=response_data,
        )

    def _parse_models(self, payload: Any) -> List[dict]:
        """Parse a Gemini models.list payload.

        Docs: https://ai.google.dev/api/models

        Example:

            {
                "models": [
                    {
                        "name": "models/gemini-2.0-flash",
                        "displayName": "Gemini 2.0 Flash",
                        "supportedGenerationMethods": [
                            "generateContent",
                            "countTokens"
                        ]
                    },
                    {
                        "name": "models/gemini-embedding-001",
                        "displayName": "Gemini Embedding 001",
                        "supportedGenerationMethods": [
                            "embedContent"
                        ]
                    }
                ],
                "nextPageToken": ""
            }

        The slug is stored without the "models/" prefix
        because the chat endpoint template already contains it.

        """
        raw_models = payload.get('models') or []
        models = []
        for item in raw_models:
            if not self._is_chat_model(item):
                continue
            models.append(
                {
                    'slug': item['name'].removeprefix('models/'),
                    'name': item['displayName'],
                },
            )
        return models

    def _is_chat_model(self, item: dict) -> bool:
        methods = item.get('supportedGenerationMethods') or []
        return 'generateContent' in methods

    def get_completion(
        self,
        system_message: str,
        user_message: str,
        model: str,
    ) -> str:
        _status, payload = self._request(
            method='POST',
            url=self.get_chat_url(model=model),
            headers=self._auth_headers(),
            data={
                'systemInstruction': {
                    'parts': [{'text': system_message}],
                },
                'contents': [
                    {
                        'role': 'user',
                        'parts': [{'text': user_message}],
                    },
                ],
            },
            timeout=self.completion_timeout,
        )
        return self._parse_completion(payload)

    def _parse_completion(self, payload: Any) -> str:
        """Parse a Gemini generateContent payload.

        Docs: https://ai.google.dev/api/generate-content

        Example:

            {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": "Hello!"}],
                            "role": "model"
                        },
                        "finishReason": "STOP"
                    }
                ]
            }

        """
        texts = []
        parts = payload['candidates'][0]['content']['parts']
        for part in parts:
            if 'text' in part:
                texts.append(part['text'])
        return ''.join(texts)
