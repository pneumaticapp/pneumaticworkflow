from typing import Any, List, Optional

from src.ai.services.vendors.base import BaseVendor


class AnthropicVendor(BaseVendor):
    API_VERSION = '2023-06-01'
    DEFAULT_MAX_TOKENS = 1024

    def _api_base(self) -> str:
        base = super()._api_base()
        if base.endswith('/v1'):
            return base
        return f'{base}/v1'

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
            url=self._create_url('models'),
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
