import json
from typing import Any

from django.conf import settings
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
)
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from oauth2_provider.exceptions import OAuthToolkitError
from oauth2_provider.views import (
    DynamicClientRegistrationManagementView,
    DynamicClientRegistrationView,
    RevokeTokenView,
    TokenView,
)
from oauth2_provider.views.mixins import OAuthLibMixin

from src.authentication.responses import (
    get_oauth_error_response,
    get_public_registration_response,
)
from src.authentication.serializers import (
    AuthorizeSerializer,
    ClientRegistrationSerializer,
    ResourceSerializer,
)
from src.authentication.services.consent import ConsentService
from src.authentication.services.oauth import (
    ClientRegistrationService,
    TokenExchangeService,
)
from src.authentication.constants import (
    PKCE_METHOD,
)
from src.authentication.enums import (
    GrantType,
    OAuthErrorCode,
    TokenEndpointAuthMethod,
)
from src.authentication.exceptions import (
    InvalidGrant,
)
from src.authentication.views.mcp import (
    EnabledMixin,
)


class AuthorizationView(EnabledMixin, OAuthLibMixin, View):
    def get(self, request: HttpRequest):
        serializer = AuthorizeSerializer(
            data={
                'resource': request.GET.getlist('resource'),
                'code_challenge_method': request.GET.get(
                    'code_challenge_method',
                ),
            },
        )
        if not serializer.is_valid():
            return get_oauth_error_response(OAuthErrorCode.INVALID_REQUEST)
        try:
            scopes, credentials = self.validate_authorization_request(
                request,
            )
        except OAuthToolkitError:
            return get_oauth_error_response(OAuthErrorCode.INVALID_REQUEST)
        return HttpResponseRedirect(
            ConsentService.create_authorization_request(
                scopes=scopes,
                credentials=credentials,
            ),
        )


@method_decorator(csrf_exempt, name='dispatch')
class MCPTokenView(EnabledMixin, TokenView):
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any):
        serializer = ResourceSerializer(
            data={'resource': request.POST.getlist('resource')},
        )
        if not serializer.is_valid():
            return get_oauth_error_response(OAuthErrorCode.INVALID_TARGET)
        try:
            with TokenExchangeService.lock_connection(
                post_data=request.POST,
            ):
                return super().post(request, *args, **kwargs)
        except InvalidGrant:
            return get_oauth_error_response(OAuthErrorCode.INVALID_GRANT)


@method_decorator(csrf_exempt, name='dispatch')
class MCPRevokeView(EnabledMixin, RevokeTokenView):
    pass


class RegistrationInputMixin:
    def _get_metadata_error(
        self,
        request: HttpRequest,
    ) -> HttpResponse | None:
        try:
            data = json.loads(request.body)
        except (ValueError, UnicodeDecodeError):
            return get_oauth_error_response(
                error=OAuthErrorCode.INVALID_CLIENT_METADATA,
            )
        serializer = ClientRegistrationSerializer(data=data)
        if not serializer.is_valid():
            return get_oauth_error_response(
                error=OAuthErrorCode.INVALID_CLIENT_METADATA,
            )
        return None


@method_decorator(csrf_exempt, name='dispatch')
class RegistrationView(
    RegistrationInputMixin,
    EnabledMixin,
    DynamicClientRegistrationView,
):
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any):
        error = self._get_metadata_error(request=request)
        if error is not None:
            return error
        response = super().post(request, *args, **kwargs)
        if response.status_code == 201:
            ClientRegistrationService.save_policy(
                client_id=json.loads(response.content)['client_id'],
            )
        return get_public_registration_response(response=response)


@method_decorator(csrf_exempt, name='dispatch')
class RegistrationManagementView(
    RegistrationInputMixin,
    EnabledMixin,
    DynamicClientRegistrationManagementView,
):
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        return get_public_registration_response(
            response=super().get(request, *args, **kwargs),
        )

    def put(self, request: HttpRequest, *args: Any, **kwargs: Any):
        error = self._get_metadata_error(request=request)
        if error is not None:
            return error
        return get_public_registration_response(
            response=super().put(request, *args, **kwargs),
        )


class ResourceMetadataView(EnabledMixin, View):
    def get(self, request: HttpRequest):
        return JsonResponse(
            {
                'resource': settings.MCP_PUBLIC_URL,
                'authorization_servers': [settings.MCP_ISSUER_URL],
                'scopes_supported': list(
                    settings.OAUTH2_PROVIDER['SCOPES'],
                ),
                'bearer_methods_supported': ['header'],
            },
        )


class ServerMetadataView(EnabledMixin, View):
    def get(self, request: HttpRequest):
        issuer = settings.MCP_ISSUER_URL
        return JsonResponse(
            {
                'issuer': issuer,
                'authorization_endpoint': (
                    f'{issuer}{reverse("oauth2_provider:authorize")}'
                ),
                'token_endpoint': (
                    f'{issuer}{reverse("oauth2_provider:token")}'
                ),
                'registration_endpoint': (
                    f'{issuer}{reverse("oauth2_provider:dcr-register")}'
                ),
                'revocation_endpoint': (
                    f'{issuer}{reverse("oauth2_provider:revoke-token")}'
                ),
                'response_types_supported': ['code'],
                'grant_types_supported': list(GrantType.ALLOWED),
                'code_challenge_methods_supported': [PKCE_METHOD],
                'token_endpoint_auth_methods_supported': list(
                    TokenEndpointAuthMethod.ALLOWED,
                ),
                'scopes_supported': list(
                    settings.OAUTH2_PROVIDER['SCOPES'],
                ),
                'client_id_metadata_document_supported': True,
                'authorization_response_iss_parameter_supported': True,
            },
        )
