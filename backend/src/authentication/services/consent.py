import src.authentication.messages as auth_messages
from dataclasses import dataclass
from urllib.parse import urlencode
from uuid import UUID

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.db import transaction
from django.http import HttpRequest, QueryDict
from django.urls import reverse
from django.utils import timezone
from oauth2_provider.exceptions import OAuthToolkitError
from oauth2_provider.models import Application
from oauth2_provider.views.mixins import OAuthLibMixin
from rest_framework.exceptions import NotFound, PermissionDenied

from src.authentication.constants import (
    AUTHORIZATION_REQUEST_TTL,
    LOGIN_CODE_TTL,
    LOGIN_SESSION_EXPIRY_SECONDS,
    LOGIN_SESSION_KEY,
)
from src.mcp.constants import (
    FRONTEND_CONNECT_PATH,
)
from src.mcp.enums import (
    HttpMethod,
)
from src.authentication.enums import (
    OAuthErrorCode,
)
from src.authentication.exceptions import (
    AuthorizationRequestGone,
    InvalidLoginCode,
)
from src.mcp.models import AuthorizationRequest, LoginCode
from src.authentication.services.connections import ConnectionService
from src.authentication.tokens import create_token, get_digest, get_expiration

UserModel = get_user_model()


@dataclass(frozen=True)
class IssuedLoginCode:
    code: str
    request_id: UUID


@dataclass(frozen=True)
class ConsentContext:
    auth_request: AuthorizationRequest
    application: Application
    user: UserModel


class ConsentService:
    """Browser part of the OAuth flow: login handoff and user consent.

    The OAuth authorize request is parked until the user logs in to the
    frontend; a one-time login code then starts a short Django session.
    """

    AUTHORIZATION_PARAMETERS = (
        'client_id',
        'redirect_uri',
        'response_type',
        'state',
        'code_challenge',
        'code_challenge_method',
    )
    LOGIN_BACKEND = 'django.contrib.auth.backends.ModelBackend'
    CONSENT_STEP = 'consent'

    @classmethod
    def create_authorization_request(
        cls,
        scopes: list[str],
        credentials: dict,
    ) -> str:
        parameters = {
            key: credentials[key]
            for key in cls.AUTHORIZATION_PARAMETERS
            if key in credentials
        }
        parameters['scope'] = ' '.join(scopes)
        parameters['resource'] = settings.MCP_PUBLIC_URL
        auth_request = AuthorizationRequest.objects.create(
            parameters=parameters,
            expires_at=timezone.now() + AUTHORIZATION_REQUEST_TTL,
        )
        return cls._get_connect_url(request_id=auth_request.pk)

    @classmethod
    @transaction.atomic
    def complete_login(
        cls,
        request: HttpRequest,
        request_id: UUID,
        code: str,
    ) -> str:
        """Log the user in and return where the browser goes next."""
        login_code = cls._consume_login_code(
            request_id=request_id,
            credential=code,
        )
        login(request, login_code.user, backend=cls.LOGIN_BACKEND)
        request.session.set_expiry(LOGIN_SESSION_EXPIRY_SECONDS)
        request.session[LOGIN_SESSION_KEY] = str(
            login_code.authorization_request_id,
        )
        return login_code.redirect_url or cls._get_connect_url(
            request_id=login_code.authorization_request_id,
            step=cls.CONSENT_STEP,
        )

    @classmethod
    def get_context(cls, request_id: UUID, user: UserModel) -> ConsentContext:
        auth_request = cls._get_bound_request(
            request_id=request_id,
            user=user,
        )
        return ConsentContext(
            auth_request=auth_request,
            application=Application.objects.get(
                client_id=auth_request.parameters['client_id'],
            ),
            user=user,
        )

    @classmethod
    @transaction.atomic
    def create_login_code(
        cls,
        request_id: UUID,
        user: UserModel,
        redirect_url: str = '',
    ) -> IssuedLoginCode:
        auth_request = cls._get_bound_request(
            request_id=request_id,
            user=user,
        )
        code = create_token()
        LoginCode.objects.create(
            digest=get_digest(value=code),
            authorization_request=auth_request,
            user=user,
            account_id=user.account_id,
            redirect_url=redirect_url,
            expires_at=get_expiration(
                ttl=LOGIN_CODE_TTL,
                limit=auth_request.expires_at,
            ),
        )
        return IssuedLoginCode(code=code, request_id=auth_request.pk)

    @classmethod
    @transaction.atomic
    def approve(
        cls,
        request_id: UUID,
        user: UserModel,
        allow: bool,
    ) -> IssuedLoginCode:
        """Issue the OAuth redirect behind a fresh login code.

        The code keeps the redirect off the API response: the browser
        follows it only through the login endpoint.
        """
        auth_request = cls._get_bound_request(
            request_id=request_id,
            user=user,
        )
        if auth_request.login_completed_at is None:
            raise PermissionDenied
        result = cls.create_login_code(
            request_id=auth_request.pk,
            user=user,
            redirect_url=cls._get_redirect_url(
                auth_request=auth_request,
                user=user,
                allow=allow,
            ),
        )
        auth_request.consumed_at = timezone.now()
        auth_request.save(update_fields=['consumed_at'])
        return result

    @classmethod
    def _get_redirect_url(
        cls,
        auth_request: AuthorizationRequest,
        user: UserModel,
        allow: bool,
    ) -> str:
        credentials = dict(auth_request.parameters)
        credentials['resource'] = [settings.MCP_PUBLIC_URL]
        try:
            uri, _headers, _body, _status = (
                OAuthLibMixin()
                .get_oauthlib_core()
                .create_authorization_response(
                    request=cls._get_authorize_request(
                        auth_request=auth_request,
                        user=user,
                    ),
                    scopes=credentials['scope'].split(),
                    credentials=credentials,
                    allow=allow,
                )
            )
        except OAuthToolkitError as ex:
            if allow:
                raise PermissionDenied from ex
            uri = cls._get_denied_url(credentials=credentials)
        return uri

    @classmethod
    def _get_authorize_request(
        cls,
        auth_request: AuthorizationRequest,
        user: UserModel,
    ) -> HttpRequest:
        """Rebuild the parked authorize request for oauthlib."""
        request = HttpRequest()
        request.method = HttpMethod.GET
        request.path = reverse('oauth2_provider:authorize')
        request.GET = QueryDict(urlencode(auth_request.parameters))
        request.META['SERVER_NAME'] = 'mcp'
        request.META['SERVER_PORT'] = '443'
        request.META['wsgi.url_scheme'] = 'https'
        request._current_scheme_host = settings.MCP_ISSUER_URL
        request.user = user
        return request

    @classmethod
    def _get_denied_url(cls, credentials: dict) -> str:
        uri = credentials['redirect_uri']
        separator = '&' if '?' in uri else '?'
        return (
            uri
            + separator
            + urlencode(
                {
                    'error': OAuthErrorCode.ACCESS_DENIED,
                    'state': credentials.get('state', ''),
                    'iss': settings.MCP_ISSUER_URL,
                },
            )
        )

    @classmethod
    def _get_connect_url(cls, request_id: UUID, step: str = '') -> str:
        query = {'request_id': str(request_id)}
        if step:
            query['step'] = step
        return (
            f'{settings.FRONTEND_URL}{FRONTEND_CONNECT_PATH}?'
            f'{urlencode(query)}'
        )

    @classmethod
    def _get_bound_request(
        cls,
        request_id: UUID,
        user: UserModel,
    ) -> AuthorizationRequest:
        """Lock the request and bind it to the first user who opens it."""
        auth_request = (
            AuthorizationRequest.objects.select_for_update()
            .filter(pk=request_id)
            .first()
        )
        if auth_request is None or (
            auth_request.user_id is not None
            and (
                auth_request.user_id != user.pk
                or auth_request.account_id != user.account_id
            )
        ):
            raise NotFound(auth_messages.MSG_AU_0021)
        if (
            auth_request.expires_at <= timezone.now()
            or auth_request.consumed_at
        ):
            raise AuthorizationRequestGone
        if auth_request.user_id is None:
            auth_request.user = user
            auth_request.account_id = user.account_id
            auth_request.save(update_fields=['user', 'account_id'])
        return auth_request

    @classmethod
    def _consume_login_code(
        cls,
        request_id: UUID,
        credential: str,
    ) -> LoginCode:
        code = (
            LoginCode.objects.select_related('user__account')
            .select_for_update(of=('self',))
            .filter(
                digest=get_digest(value=credential),
                authorization_request_id=request_id,
            )
            .first()
        )
        now = timezone.now()
        if (
            code is None
            or code.consumed_at
            or code.expires_at <= now
            or not ConnectionService.is_eligible_user(
                user=code.user,
                account_id=code.account_id,
            )
        ):
            raise InvalidLoginCode
        auth_request = AuthorizationRequest.objects.select_for_update().get(
            pk=code.authorization_request_id,
        )
        if (
            auth_request.user_id != code.user_id
            or auth_request.account_id != code.account_id
            or auth_request.expires_at <= now
            or (auth_request.consumed_at and not code.redirect_url)
        ):
            raise InvalidLoginCode
        code.consumed_at = now
        code.save(update_fields=['consumed_at'])
        if not code.redirect_url:
            auth_request.login_completed_at = now
            auth_request.save(update_fields=['login_completed_at'])
        return code
