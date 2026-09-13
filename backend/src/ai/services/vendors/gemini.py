from typing import Any, List, Optional
from urllib.parse import urlparse

from src.ai.services.vendors.base import BaseVendor


class GeminiVendor(BaseVendor):
    def _api_base(self) -> str:
        base = super()._api_base()
        path = (urlparse(base).path or '').rstrip('/')
        if path.startswith('/v1'):
            return base
        return f'{base}/v1beta'

    def _auth_headers(self) -> dict:
        return {
            'x-goog-api-key': self.instance.api_key,
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
                            "generateContent"
                        ]
                    }
                ]
            }

        """
        raw_models = payload.get('models')
        models = []
        for item in raw_models:
            models.append(
                {
                    'slug': item['name'],
                    'name': item['displayName'],
                },
            )
        return models

    def get_models(self) -> List[dict]:
        _status, payload = self._request(
            method='GET',
            url=self._create_url('models'),
            headers=self._auth_headers(),
        )
        return self._parse_models(payload)
