import src.authentication.messages as auth_messages
import json
from collections.abc import Callable
from math import ceil
from typing import Optional
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin
from redis.exceptions import RedisError
from sentry_sdk import isolation_scope
from rest_framework.authentication import get_authorization_header
from rest_framework.exceptions import APIException

from src.authentication.enums import AuthTokenType
from src.authentication.responses import get_oauth_error_response
from src.authentication.services.mcp_auth import DelegationAuthentication
from src.authentication.throttling import (
    OAuthAuthorizeThrottle,
    OAuthRegisterThrottle,
    OAuthTokenThrottle,
)
from src.authentication.tokens import PneumaticToken
from src.generics.mixins.views import AnonymousMixin
from src.generics.responses import (
    get_api_exception_response,
    set_private_headers,
)
from src.generics.throttling import CustomSimpleRateThrottle
from src.logs.service import AccountLogService
from src.authentication.constants import (
    MCP_TOKEN_PREFIXES,
)
from src.mcp.enums import (
    HttpMethod,
)
from src.authentication.enums import (
    OAuthErrorCode,
)
from src.utils.user_agent import get_user_agent


class UserAgentMiddleware(MiddlewareMixin):
    def __call__(self, request):
        request.user_agent = get_user_agent(request)

        return super().__call__(request)


class WebsocketAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, *args, **kwargs):
        query_string = parse_qs(scope['query_string'])

        if b'auth_token' in query_string:
            token = query_string[b'auth_token'][0]
            try:
                user = await database_sync_to_async(
                    PneumaticToken.get_user_from_token,
                )(token.decode())
            except ObjectDoesNotExist:
                pass
            else:
                scope['user'] = user
                scope['token_type'] = AuthTokenType.USER

        if 'user' not in scope:
            scope['user'] = AnonymousUser()
        return await self.inner(scope, *args, **kwargs)


class AuthMiddleware(
    AuthenticationMiddleware,
    AnonymousMixin,
):
    def process_request(self, request):
        super().process_request(request)
        # Danger: save raw request body to memory creates vulnerability
        # Don't enable account.log_api_requests for all accounts
        request._body_to_log = request.body

    def process_response(self, request, response):
        user = request.user
        if (
            request.method not in {'OPTIONS', 'HEAD'}
            and not user.is_anonymous
            and user.is_user
            and user.account.log_api_requests
        ):
            auth_header = get_authorization_header(request).decode()
            auth_header_parts = auth_header.split()
            if (
                len(auth_header_parts) == 2
                and auth_header_parts[0].lower() == 'bearer'
            ):
                token = auth_header_parts[1]
                cached_data = PneumaticToken.data(token)
                # after logout token cached_data not exist
                if cached_data and cached_data['for_api_key']:
                    if request.method == 'GET':
                        body = request.GET
                    elif (
                        request.method in ('POST', 'PUT', 'PATCH')
                        and request.META['CONTENT_LENGTH'] != '0'
                    ):
                        body = request._body_to_log.decode()
                        body = json.loads(body)
                    else:
                        body = None
                    response_data = (
                        response.data if hasattr(response, 'data') else None
                    )
                    AccountLogService().api_request(
                        user=request.user,
                        ip=self.get_user_ip(request),
                        user_agent=self.get_user_agent(request),
                        auth_token=token,
                        scheme=request.scheme,
                        method=request.method,
                        title='API request',
                        path=request.path,
                        request_data=body,
                        http_status=response.status_code,
                        response_data=response_data,
                    )
        return response


class UserLocaleMiddleware(MiddlewareMixin):
    """Set Accept-Language at request start; reset locale at request end."""

    def process_request(self, request):
        translation.activate(translation.get_language_from_request(request))

    def process_response(self, request, response):
        translation.deactivate()
        return response


RATE_UNAVAILABLE_DESCRIPTION = (
    'Authorization service is temporarily unavailable.'
)
RATE_EXCEEDED_DESCRIPTION = 'Too many authorization requests.'


class OAuthThrottleMiddleware:
    """Apply the backend's throttles to non-DRF OAuth views."""

    CACHE_RETRY_SECONDS = 5
    ROUTES = {
        (HttpMethod.POST, '/oauth/mcp/register'): OAuthRegisterThrottle,
        (HttpMethod.GET, '/oauth/mcp/authorize'): OAuthAuthorizeThrottle,
        (HttpMethod.HEAD, '/oauth/mcp/authorize'): OAuthAuthorizeThrottle,
        (HttpMethod.GET, '/oauth/mcp/login'): OAuthAuthorizeThrottle,
        (HttpMethod.HEAD, '/oauth/mcp/login'): OAuthAuthorizeThrottle,
        (HttpMethod.POST, '/oauth/mcp/token'): OAuthTokenThrottle,
        (HttpMethod.POST, '/oauth/mcp/revoke'): OAuthTokenThrottle,
    }

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        throttle_class = self.ROUTES.get(
            (request.method, request.path_info.rstrip('/')),
        )
        if settings.MCP_ENABLED and throttle_class:
            response = self._get_throttle_response(
                request=request,
                throttle=throttle_class(),
            )
            if response is not None:
                return response
        return self.get_response(request)

    def _get_throttle_response(
        self,
        request: HttpRequest,
        throttle: CustomSimpleRateThrottle,
    ) -> Optional[JsonResponse]:
        try:
            allowed = throttle.allow_request(request=request, view=None)
        except RedisError:
            response = get_oauth_error_response(
                error=OAuthErrorCode.TEMPORARILY_UNAVAILABLE,
                status=503,
                description=RATE_UNAVAILABLE_DESCRIPTION,
            )
            response['Retry-After'] = str(self.CACHE_RETRY_SECONDS)
            return set_private_headers(response)
        if allowed:
            return None
        response = get_oauth_error_response(
            error=OAuthErrorCode.TEMPORARILY_UNAVAILABLE,
            status=429,
            description=RATE_EXCEEDED_DESCRIPTION,
        )
        response['Retry-After'] = str(max(1, ceil(throttle.wait())))
        return set_private_headers(response)


class McpDelegationMiddleware:
    """Authenticate MCP requests before views or business execution."""

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        parts = request.headers.get('Authorization', '').split()
        if len(parts) != 2 or not parts[1].startswith(MCP_TOKEN_PREFIXES):
            return self.get_response(request)
        try:
            result = DelegationAuthentication().authenticate(request)
            if result is None:
                return JsonResponse(
                    {'detail': auth_messages.MSG_AU_0032},
                    status=401,
                )
            with isolation_scope() as scope:
                scope.set_tag('mcp', 'true')
                return self.get_response(request)
        except APIException as ex:
            return get_api_exception_response(ex=ex)
