from datetime import timedelta
from typing import Optional, Tuple, Union

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone, translation
from rest_framework.authentication import TokenAuthentication

from src.accounts.enums import UserStatus
from src.accounts.models import APIKey, User
from src.authentication.enums import (
    AuthTokenType,
)
from src.authentication.tokens import PneumaticToken

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
    def get_superuser_auth_token(user: User) -> str:
        return PneumaticToken.create(
            user=user,
            for_superuser=True,
        )


class PneumaticTokenAuthentication(TokenAuthentication):

    keyword = 'Bearer'

    def authenticate(self, request) -> Tuple[User, PneumaticToken]:
        result = super().authenticate(request)
        request.token_type = None
        request.is_superuser = False
        request.session['is_authenticated'] = bool(result)
        if result:
            user, token = result
            cached_data = PneumaticToken.data(token.key)
            request.token_type = (
                AuthTokenType.API if cached_data['for_api_key']
                else AuthTokenType.USER
            )
            request.is_superuser = cached_data['is_superuser']
            translation.activate(user.language)
        return result

    def authenticate_credentials(
        self,
        token: Union[bytes, str],
    ) -> Optional[Tuple[UserModel, PneumaticToken]]:
        if isinstance(token, bytes):
            token = token.decode('utf-8')

        # Check cache first, fallback to DB hash lookup
        cached_data = PneumaticToken.data(token)
        if cached_data:
            try:
                user = UserModel.objects.get(pk=cached_data['user_id'])
            except ObjectDoesNotExist:
                return None
        else:
            # Lookup by hash instead of raw key
            key_hash = APIKey.hash_key(token)
            try:
                apikey = APIKey.objects.select_related('user').get(
                    key_hash=key_hash,
                    is_active=True,
                )
            except ObjectDoesNotExist:
                return None

            # Check expiration
            if apikey.is_expired:
                return None

            user = apikey.user

            # Update last_used_at (non-blocking, batched to once per hour)
            now = timezone.now()
            if (
                apikey.last_used_at is None
                or now - apikey.last_used_at > timedelta(hours=1)
            ):
                APIKey.objects.filter(pk=apikey.pk).update(
                    last_used_at=now,
                )

            # Recreate cache entry
            PneumaticToken.create(
                user=user, for_api_key=True, token=token,
            )

            # Self-healing: populate cache_token if missing
            if not apikey.cache_token:
                apikey.cache_token = PneumaticToken.encrypt(token)
                apikey.save(update_fields=['cache_token'])

        if user.status != UserStatus.ACTIVE:
            return None
        return user, PneumaticToken(token, user)
