from typing import Optional

from django.contrib.auth import get_user_model
from django.core.cache import caches

from src.accounts.enums import SourceType
from src.authentication.models import AccessToken
from src.authentication.tokens import PneumaticToken

UserModel = get_user_model()


class OktaLogoutService:
    """Service for handling Okta logout operations"""

    source = SourceType.OKTA

    def process_logout(self, sub_id: dict):
        """
        Process Okta Global Token Revocation (GTR) request.

        Args:
            sub_id: Subject identifier dict from Okta GTR format
        """
        sub = sub_id.get('sub')
        user = self._find_user_by_okta_sub(sub)
        if user:
            self._logout_user(user, okta_sub=sub)

    def _find_user_by_okta_sub(self, okta_sub: str) -> Optional[UserModel]:
        """Find user by cached Okta sub identifier"""
        user_id = self._get_cached_user_by_sub(okta_sub)
        if user_id:
            try:
                return UserModel.objects.get(id=user_id)
            except UserModel.DoesNotExist:
                self._clear_cached_user_by_sub(okta_sub)
        return None

    def _get_cached_user_by_sub(self, okta_sub: str) -> Optional[int]:
        """Get cached user ID by Okta sub"""
        cache = caches['default']
        cache_key = f'okta_sub_to_user_{okta_sub}'
        return cache.get(cache_key)

    def _clear_cached_user_by_sub(self, okta_sub: str):
        """Clear cached user by Okta sub"""
        cache = caches['default']
        cache_key = f'okta_sub_to_user_{okta_sub}'
        cache.delete(cache_key)

    def _logout_user(self, user: UserModel, okta_sub: Optional[str]):
        """
        Perform user logout:
        - Delete AccessToken for OKTA source
        - Clear token and profile cache
        - Terminate session
        """
        # Get access tokens before deletion for profile cache cleanup
        access_tokens = list(AccessToken.objects.filter(
            user=user,
            source=self.source,
        ).values_list('access_token', flat=True))

        # Delete access tokens
        AccessToken.objects.filter(user=user, source=self.source).delete()

        # Clear profile cache for each access token
        cache = caches['default']
        for access_token in access_tokens:
            cache_key = f'user_profile_{access_token}'
            cache.delete(cache_key)

        # Clear cached user by sub
        if okta_sub:
            self._clear_cached_user_by_sub(okta_sub)

        # Clear all tokens from cache (terminate all sessions)
        PneumaticToken.expire_all_tokens(user)
