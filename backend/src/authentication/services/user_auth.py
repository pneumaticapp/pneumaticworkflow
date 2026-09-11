from typing import Any, Optional, Tuple, Union

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone, translation
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from src.accounts.enums import UserStatus
from src.accounts.models import Account, User
from src.analysis.services import AnalyticService
from src.authentication.enums import (
    AuthTokenType,
)
from src.authentication.tokens import PneumaticToken
from src.logs.events import AuditEventService

UserModel = get_user_model()


class AuthService:

    @staticmethod
    def get_auth_token(
        user: User,
        user_agent: str,
        user_ip: str,
        superuser_mode: bool = False,
    ) -> str:

        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        return PneumaticToken.create(
            user=user,
            user_agent=user_agent,
            user_ip=user_ip,
            for_superuser=superuser_mode,
        )

    @staticmethod
    def get_tenant_auth_token(
        master_user: User,
        tenant_account: Account,
        user_agent: Optional[str],
        user_ip: Optional[str],
        is_superuser: bool,
        auth_type: AuthTokenType.LITERALS,
    ) -> str:

        """ A token of the owner of a tenant, for a user of the master
            account, together with the two records this entry leaves:
            the analytics of the access and TENANT_LOGIN_AS in the
            journal. """

        token = AuthService.get_auth_token(
            user=tenant_account.get_owner(),
            user_agent=user_agent,
            user_ip=user_ip,
            superuser_mode=True,
        )
        AnalyticService.tenants_accessed(
            master_user=master_user,
            tenant_account=tenant_account,
            is_superuser=is_superuser,
            auth_type=auth_type,
        )
        AuditEventService.tenant_logged_in_as(
            master_user=master_user,
            tenant_account=tenant_account,
            auth_type=auth_type,
        )
        return token

    @staticmethod
    def get_superuser_auth_token(user: User) -> str:
        return PneumaticToken.create(
            user=user,
            for_superuser=True,
        )


class PneumaticTokenAuthentication(TokenAuthentication):

    keyword = 'Bearer'

    def authenticate(
        self,
        request: Request,
    ) -> Optional[Tuple[User, PneumaticToken]]:
        result = super().authenticate(request)
        self._apply_auth_context(request, result)
        return result

    def authenticate_credentials(
        self,
        token: Union[bytes, str],
    ) -> Optional[Tuple[UserModel, PneumaticToken]]:
        if isinstance(token, bytes):
            token = token.decode('utf-8')

        cached_data = PneumaticToken.data(token)
        if not cached_data:
            return None

        try:
            user = UserModel.objects.get(pk=cached_data['user_id'])
        except ObjectDoesNotExist:
            return None

        if user.status != UserStatus.ACTIVE:
            return None
        return user, PneumaticToken(token, user)

    def _apply_auth_context(
        self,
        request: Any,
        result: Optional[Tuple[User, PneumaticToken]],
    ) -> None:
        """Set token_type / is_superuser / session on request."""
        request.token_type = None
        request.is_superuser = False
        request.session['is_authenticated'] = bool(result)
        if result:
            user, token = result
            cached_data = PneumaticToken.data(token.key)
            if cached_data:
                request.token_type = (
                    AuthTokenType.API
                    if cached_data['for_api_key']
                    else AuthTokenType.USER
                )
                request.is_superuser = (
                    cached_data['is_superuser']
                )
            else:
                request.token_type = AuthTokenType.USER
                request.is_superuser = False
            translation.activate(user.language)


class CookieTokenAuthentication(PneumaticTokenAuthentication):
    """Bearer header with cookie fallback for OpenAPI docs only.

    Not registered in OpenAPI security schemes — used only to
    serve /api/schema/ and /api/docs/ so a logged-in browser can
    open Scalar UI without manual token entry.
    Cookie fallback is allowed for GET/HEAD/OPTIONS only.
    """

    COOKIE_NAME = 'token'
    SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')

    def authenticate(
        self,
        request: Request,
    ) -> Optional[Tuple[User, PneumaticToken]]:
        try:
            result = super().authenticate(request)
        except AuthenticationFailed:
            result = None
        if result is not None:
            return result
        if request.method in self.SAFE_METHODS:
            raw_token = request.COOKIES.get(self.COOKIE_NAME)
            if raw_token:
                result = self.authenticate_credentials(
                    raw_token,
                )
        self._apply_auth_context(request, result)
        return result
