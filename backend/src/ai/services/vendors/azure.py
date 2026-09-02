from typing import Any, List, Optional
from urllib.parse import parse_qs, urlparse

from src.ai.services.vendors.base import BaseVendor


class AzureOpenAIVendor(BaseVendor):
    V1_PATH = '/openai/v1'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        parsed = urlparse(self.instance.base_url)
        versions = parse_qs(parsed.query).get('api-version') or []
        self._api_version = versions[0] if versions else None

    def _origin(self) -> str:
        parsed = urlparse(self.instance.base_url)
        return f'{parsed.scheme}://{parsed.netloc}'

    def _is_legacy(self) -> bool:
        return bool(self._api_version)

    def _api_base(self) -> str:
        if self._is_legacy():
            return f'{self._origin()}/openai'
        parsed = urlparse(self.instance.base_url)
        path = (parsed.path or '').rstrip('/')
        origin = self._origin()
        marker = self.V1_PATH
        if marker in path:
            idx = path.find(marker)
            return f'{origin}{path[: idx + len(marker)]}'
        return f'{origin}{marker}'

    def _request_params(self) -> Optional[dict]:
        if self._api_version:
            return {'api-version': self._api_version}
        return None

    def _auth_headers(self) -> dict:
        headers = {
            'api-key': self.instance.api_key,
        }
        if not self._is_legacy():
            headers['Authorization'] = f'Bearer {self.instance.api_key}'
        return headers

    def _parse_error(
        self,
        http_status: int,
        response_data: Optional[dict],
    ) -> Optional[str]:
        """Extract `error.message` from an Azure OpenAI error body.

        Docs: https://learn.microsoft.com/en-us/azure/foundry/openai/latest

        Example:
            {
                "error": {
                    "message": "The API deployment does not exist.",
                    "type": "invalid_request_error",
                    "param": null,
                    "code": "DeploymentNotFound"
                }
            }

        """

        return super()._parse_error(
            http_status=http_status,
            response_data=response_data,
        )

    def get_models(self) -> List[dict]:
        path = 'deployments' if self._is_legacy() else 'models'
        kwargs = {
            'method': 'GET',
            'url': self._create_url(path),
            'headers': self._auth_headers(),
        }
        params = self._request_params()
        if params:
            kwargs['params'] = params
        _status, payload = self._request(**kwargs)
        return self._parse_models(payload)

    def _parse_models(self, payload: Any) -> List[dict]:
        """Parse an Azure OpenAI models or deployments list payload.

        Docs: https://learn.microsoft.com/rest/api/azureopenai/models/list

        Example:

            {
                "object": "list",
                "data": [
                    {
                        "id": "gpt-4o",
                        "object": "model",
                        "created_at": 1646126127
                    }
                ]
            }

        """
        raw_models = payload.get['data']
        models = []
        for item in raw_models:
            models.append(
                {
                    'slug': item['id'],
                    'name': item['id'],
                },
            )
        return models
