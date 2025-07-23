from typing import Tuple, Optional
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from pneumatic_backend.accounts.enums import UserStatus
from pneumatic_backend.accounts.models import User, APIKey
from pneumatic_backend.authentication.tokens import PneumaticToken
from pneumatic_backend.authentication.enums import (
    AuthTokenType,
)

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
            for_superuser=superuser_mode
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
            # if authenticated
            _, token = result
            cached_data = PneumaticToken.data(token.key)
            request.token_type = (
                AuthTokenType.API if cached_data['for_api_key']
                else AuthTokenType.USER
            )
            request.is_superuser = cached_data['is_superuser']
        return result

    def authenticate_credentials(
        self,
        token: str
    ) -> Optional[Tuple[UserModel, PneumaticToken]]:
        # Get active user or api key
        cached_data = PneumaticToken.data(token)
        if cached_data:
            try:
                user = UserModel.objects.get(pk=cached_data['user_id'])
            except ObjectDoesNotExist:
                return None
        else:
            try:
                apikey = APIKey.objects.select_related('user').get(key=token)
                user = apikey.user
            except ObjectDoesNotExist:
                return None

            # Create lost api key data in the cache
            PneumaticToken.create(user=user, for_api_key=True, token=token)
        if not user.status == UserStatus.ACTIVE:
            return None
        return user, PneumaticToken(token, user)
