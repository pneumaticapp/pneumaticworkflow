from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import requests
from django.contrib.auth import get_user_model

from src.ai.exceptions import (
    AIProviderConnectionException,
    AIProviderInvalidResponseException,
    AIProviderRequestFailedException,
    AIServiceException,
)
from src.ai.models import AIProvider
from src.logs.enums import RequestDirection
from src.logs.service import AccountLogService

UserModel = get_user_model()


class BaseVendor(ABC):
    request_timeout = 10
    _secret_headers = (
        'Authorization',
        'api-key',
        'x-api-key',
        'x-goog-api-key',
    )

    def __init__(
        self,
        instance: AIProvider,
        user: UserModel,
    ):
        self.instance = instance
        self.user = user
        self.account = user.account

    def _create_url(self, path: str) -> str:
        return f'{self.instance.base_url()}/{path}'

    @abstractmethod
    def _auth_headers(self) -> dict:

        """HTTP headers that authenticate requests to the vendor API."""

        pass

    @abstractmethod
    def get_models(self) -> List[dict]:

        """List of models as dicts with keys `slug` and `name`."""

        pass

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
        if not isinstance(error, dict):
            return None
        message = error.get('message')
        if isinstance(message, str) and message:
            return message
        return None

    def _request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> Tuple[int, dict]:
        """Send an HTTP request and return status with JSON body."""

        kwargs.setdefault('timeout', self.request_timeout)
        http_status = 0
        response_data = None
        parsed = urlparse(url)
        try:
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    **kwargs,
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
                    http_status,
                    response_data,
                )
                if error_message is None:
                    raise AIProviderRequestFailedException
                raise AIServiceException(message=error_message)
            try:
                response_data = response.json()
            except ValueError as ex:
                response_data = {'body': response.text}
                raise AIProviderInvalidResponseException from ex
            return http_status, response_data
        finally:
            if self.account.log_api_requests:
                self._log_api_request(
                    method=method,
                    url=url,
                    scheme=parsed.scheme,
                    http_status=http_status,
                    request_kwargs=kwargs,
                    response_data=response_data,
                )

    def _log_api_request(
        self,
        method: str,
        url: str,
        scheme: str,
        http_status: int,
        request_kwargs: dict,
        response_data: Optional[dict],
    ):

        AccountLogService().api_request(
            user=self.user,
            ip='',
            user_agent='',
            auth_token='',
            scheme=scheme or 'https',
            method=method.upper(),
            title=f'AI provider request: {self.instance.name}',
            path=url,
            http_status=http_status,
            request_data=self._build_request_log_data(request_kwargs),
            response_data=response_data,
            direction=RequestDirection.SENT,
            contractor=self.instance.name,
        )

    def _build_request_log_data(
        self,
        request_kwargs: dict,
    ) -> Optional[dict]:

        headers = dict(request_kwargs.get('headers') or {})
        secret_names = {name.lower() for name in self._secret_headers}
        for key in list(headers):
            if key.lower() in secret_names:
                headers[key] = '***'
        log_data = {}
        if headers:
            log_data['headers'] = headers
        json_body = request_kwargs.get('json')
        if json_body is not None:
            log_data['json'] = json_body
        data = request_kwargs.get('data')
        if data is not None:
            log_data['data'] = data
        params = request_kwargs.get('params')
        if params is not None:
            log_data['params'] = params
        return log_data or None
