import json
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.contrib.auth import get_user_model

from src.ai.enums import AIAgentActionType
from src.ai.exceptions import (
    AIProviderConnectionException,
    AIProviderInvalidResponseException,
    AIProviderRequestFailedException,
    AIServiceException,
)
from src.ai.models import AIAgent, AIAgentAction, AIProvider
from src.processes.models.workflows.task import Task

UserModel = get_user_model()


class BaseVendor(ABC):
    request_timeout = 10
    completion_timeout = 200
    _secret_headers = (
        'Authorization',
        'authorization',
        'api-key',
        'x-api-key',
        'x-goog-api-key',
    )

    def __init__(
        self,
        instance: AIProvider,
        user: UserModel,
        agent: Optional[AIAgent] = None,
        task: Optional[Task] = None,
    ):
        self.instance = instance
        self.user = user
        self.account = user.account
        self.agent = agent
        self.task = task

    def _create_url(self, path: str) -> str:
        return f'{self.instance.base_url}/{path}'

    @abstractmethod
    def _auth_headers(self) -> dict:

        """HTTP headers that authenticate requests to the vendor API."""

        pass

    @abstractmethod
    def get_models(self) -> List[dict]:

        """List of models as dicts with keys `slug` and `name`."""

        pass

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

    def _create_action(
        self,
        action: str,
        message: Optional[str] = None,
    ) -> Optional[AIAgentAction]:
        if not (self.agent and self.task):
            return None
        return AIAgentAction.objects.create(
            agent=self.agent,
            task=self.task,
            action=action,
            message=message,
        )

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
        return None

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
        parsed = urlparse(url)
        proxies = self._get_proxies()
        try:
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=data,
                    params=params,
                    timeout=timeout,
                    proxies=proxies,
                )
            except requests.RequestException as ex:
                response_data = {'error': str(ex)}
                raise AIProviderConnectionException from ex
            http_status = response.status_code
            if not 200 <= http_status < 300:
                try:
                    response_data = response.json()
                except ValueError:
                    response_data = {'body': response.text}
                error_message = self._parse_error(
                    http_status=http_status,
                    response_data=response_data,
                )
                if error_message is None:
                    raise AIProviderRequestFailedException
                message = f'"{error_message}" ({http_status})'
                raise AIServiceException(message=message)
            try:
                response_data = response.json()
            except ValueError as ex:
                response_data = {'body': response.text}
                raise AIProviderInvalidResponseException from ex
            return http_status, response_data
        finally:
            message = json.dumps(
                {
                    'method': method,
                    'url': url,
                    'scheme': parsed.scheme,
                    'http_status': http_status,
                    'headers': self._get_safe_headers(headers) or {},
                    'data': data or {},
                    'params': params or {},
                    'timeout': timeout,
                    'proxies': bool(proxies),
                    'response_data': response_data or {},
                },
                default=str,
            )
            self._create_action(
                action=AIAgentActionType.REQUEST,
                message=message,
            )
