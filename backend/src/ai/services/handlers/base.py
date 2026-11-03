import json
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Any

import requests
from django.conf import settings
from django.contrib.auth import get_user_model

from src.accounts.models import Account
from src.ai.enums import AIAgentActionType
from src.ai.exceptions import (
    AIHandlerException,
    AIHandlerConnectionException,
    AIHandlerInvalidResponse,
    AIHandlerPermissionDenied,
    AIHandlerRequestFailed,
    AIHandlerUnauthorized,
)
from src.ai.models import AIAgent, AIAgentAction, AIProvider
from src.ai.services.entities import ProviderConfig
from src.processes.models.workflows.task import Task

UserModel = get_user_model()


class BaseHandler(ABC):

    request_timeout = 10
    completion_timeout = 200
    models_params: Optional[dict] = None
    DEFAULT_ENDPOINTS = {
        'models': 'models',
        'chat': 'chat/completions',
    }
    _secret_headers = (
        'Authorization',
        'authorization',
        'api-key',
        'x-api-key',
        'x-goog-api-key',
    )

    def __init__(
        self,
        provider: AIProvider,
        account: Account,
        config: ProviderConfig,
        agent: Optional[AIAgent] = None,
        task: Optional[Task] = None,
    ):
        self.provider = provider
        self.account = account
        self.config = config
        self.agent = agent
        self.task = task

    def get_models_url(self) -> str:
        endpoints = self.config.get('endpoints')
        path = endpoints.get('models') or self.DEFAULT_ENDPOINTS['models']
        return f'{self.provider.base_url}/{path}'

    def get_chat_url(self, **kwargs) -> str:
        endpoints = self.config.get('endpoints')
        path = endpoints.get('chat') or self.DEFAULT_ENDPOINTS['chat']
        return f'{self.provider.base_url}/{path.format(**kwargs)}'

    @abstractmethod
    def _auth_headers(self) -> dict:

        """HTTP headers that authenticate requests to the vendor API."""

        pass

    @abstractmethod
    def _parse_models(self, payload: Any) -> List[dict]:

        pass

    def get_models(self) -> List[dict]:
        _status, payload = self._request(
            method='GET',
            url=self.get_models_url(),
            headers=self._auth_headers(),
            params=self.models_params,
        )
        return self._parse_models(payload)

    @abstractmethod
    def get_completion(
        self,
        system_message: str,
        user_message: str,
        model: str,
    ) -> str:

        """Send a chat request and return the model text response."""

        pass

    def _get_proxies(self) -> Optional[dict]:
        http_proxy = settings.AI_HTTP_PROXY
        https_proxy = settings.AI_HTTPS_PROXY or http_proxy
        if not http_proxy and not https_proxy:
            return None
        proxies = {}
        if http_proxy:
            proxies['http'] = http_proxy
        if https_proxy:
            proxies['https'] = https_proxy
        return proxies

    def _get_safe_headers(self, headers: Optional[dict]) -> Optional[dict]:
        if not headers:
            return headers
        data = dict(headers)
        for key in list(data):
            if key.lower() in self._secret_headers:
                data[key] = '***'
        return data

    @abstractmethod
    def _parse_error(
        self,
        http_status: int,
        response_data: Optional[dict],
    ) -> Optional[str]:

        """Human-readable error from a non-2xx vendor response, or None."""

        if not isinstance(response_data, dict):
            return None
        error = response_data.get('error')
        if isinstance(error, str):
            return error
        if isinstance(error, dict):
            message = error.get('message')
            if isinstance(message, str) and message:
                return message
        error = response_data.get('message')
        if isinstance(error, str):
            return error
        return None

    def _log_failed_request(
        self,
        method: str,
        url: str,
        http_status: int,
        headers: dict,
        request_data: dict,
        request_params: dict,
        timeout: int,
        proxies: bool,
        response_data: dict,
    ):
        message = json.dumps(
            {
                'method': method,
                'url': url,
                'http_status': http_status,
                'headers': headers,
                'request_data': request_data,
                'request_params': request_params,
                'timeout': timeout,
                'proxies': bool(proxies),
                'response_data': response_data,
            },
            default=str,
        )
        AIAgentAction.objects.create(
            account=self.account,
            agent=self.agent,
            task=self.task,
            action=AIAgentActionType.REQUEST_FAILED,
            text=message,
        )

    def _request(
        self,
        method: str,
        url: str,
        headers: Optional[dict] = None,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> Tuple[int, dict]:

        """Send an HTTP request and return status with JSON body."""

        if timeout is None:
            timeout = self.request_timeout
        http_status = 0
        response_data = None
        proxies = self._get_proxies()
        try:
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params,
                    timeout=timeout,
                    proxies=proxies,
                )
            except requests.RequestException as ex:
                response_data = {'error': str(ex)}
                raise AIHandlerConnectionException(message=str(ex)) from ex
            http_status = response.status_code
            try:
                response_data = response.json()
            except ValueError as ex:
                response_data = {'body': response.text}
                raise AIHandlerInvalidResponse(message=response.text) from ex
            if 200 <= http_status < 300:
                return http_status, response_data
            error_message = self._parse_error(
                http_status=http_status,
                response_data=response_data,
            )
            if http_status == 401:
                raise AIHandlerUnauthorized(error=error_message)
            if http_status == 403:
                raise AIHandlerPermissionDenied(error=error_message)
            if error_message is None:
                raise AIHandlerRequestFailed
            raise AIHandlerRequestFailed(
                message=f'"{error_message}" ({http_status})',
            )
        except AIHandlerException:
            self._log_failed_request(
                method=method,
                url=url,
                http_status=http_status,
                headers=self._get_safe_headers(headers) or {},
                request_data=data or {},
                request_params=params or {},
                timeout=timeout,
                proxies=bool(proxies),
                response_data=response_data or {},
            )
            raise
