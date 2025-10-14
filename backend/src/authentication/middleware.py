import json
from urllib.parse import parse_qs

from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from django.utils.deprecation import MiddlewareMixin
from rest_framework.authentication import get_authorization_header

from src.authentication.enums import AuthTokenType
from src.authentication.tokens import PneumaticToken
from src.generics.mixins.views import AnonymousMixin
from src.logs.service import AccountLogService
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
                user = PneumaticToken.get_user_from_token(token.decode())
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
