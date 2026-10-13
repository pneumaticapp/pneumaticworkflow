from datetime import timedelta
from typing import Optional, Tuple

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone, translation
from rest_framework.authentication import TokenAuthentication
from rest_framework.request import Request

from src.accounts.enums import UserStatus
from src.accounts.models import APIKey, User
from src.authentication.enums import AuthTokenType
from src.authentication.tokens import PneumaticToken


class APIKeyAuthentication(TokenAuthentication):
    """Separate auth backend for API key tokens.

    Identifies API-key tokens by their prefix (e.g. 'pn-').
    If the token does not start with the prefix, returns None
    so DRF falls through to the next authentication class.

    TODO: When proper request logging is implemented, replace
    the last_used_at update with log-based tracking.
    """

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
        key,
    ) -> Optional[Tuple[User, PneumaticToken]]:
        if isinstance(key, bytes):
            key = key.decode('utf-8')

        # Only handle tokens with the API key prefix
        if not key.startswith(APIKey.API_KEY_PREFIX):
            return None

        # Check cache first for fast authentication
        cached_data = PneumaticToken.data(key)
        if cached_data:
            try:
                user = User.objects.get(pk=cached_data['user_id'])
            except ObjectDoesNotExist:
                return None
        else:
            # Fallback to DB (cache miss or eviction)
            try:
                apikey = APIKey.objects.select_related('user').get(
                    token=key,
                    is_active=True,
                )
            except ObjectDoesNotExist:
                return None

            if apikey.is_expired:
                return None

            user = apikey.user

            # Populate cache
            PneumaticToken.create(
                user=user, for_api_key=True, token=key,
            )

            # Update last_used_at on cache miss (approximate tracking)
            # TODO: mark for deletion when the logging system is implemented
            now = timezone.now()
            if (
                apikey.last_used_at is None
                or now - apikey.last_used_at > timedelta(hours=1)
            ):
                APIKey.objects.filter(pk=apikey.pk).update(
                    last_used_at=now,
                )

        if user.status != UserStatus.ACTIVE:
            return None
        return user, PneumaticToken(key, user)

    def _apply_auth_context(
        self,
        request: Request,
        result: Optional[Tuple[User, PneumaticToken]],
    ) -> None:
        """Set token_type / is_superuser / session for API key auth.

        This backend runs first in the chain. On failure (result=None),
        set safe defaults; the next backend will overwrite them.
        """
        if result:
            user, _token = result
            request.token_type = AuthTokenType.API
            request.is_superuser = False
            request.session['is_authenticated'] = True
            translation.activate(user.language)
        else:
            request.token_type = None
            request.is_superuser = False
            request.session['is_authenticated'] = False
