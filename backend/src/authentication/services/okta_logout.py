import jwt
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import caches
from typing import Optional

from src.accounts.enums import SourceType
from src.authentication.models import AccessToken
from src.authentication.tokens import PneumaticToken
from src.utils.logging import (
    SentryLogLevel,
    capture_sentry_message,
)

UserModel = get_user_model()


class OktaLogoutService:
    """
    Service for handling Okta Back-Channel Logout operations.

    Okta sends logout requests in two scenarios:
    1. Admin forcefully terminates user session with "revoke in all apps"
    2. Okta security policy triggers automatic session termination

    The service validates the logout_token and terminates user sessions.
    """

    # Constants
    SOURCE = SourceType.OKTA
    CACHE_TIMEOUT = 2592000  # 30 days (Okta sub lifetime)
    CACHE_KEY_PREFIX = 'okta_sub_to_user'

    def __init__(self, logout_token: Optional[str] = None):
        """
        Initialize service with optional logout_token for validation.

        Args:
            logout_token: JWT token from Okta logout request
        """
        self.logout_token = logout_token
        self.cache = caches['default']

    def process_logout(self, **request_data):
        """
        Process Okta Back-Channel Logout request.

        Supports two logout types:
        1. iss/sub format: Uses cached sub identifier (current)
        2. email format: Uses email with domain validation (future)

        Args:
            **request_data: Validated data with 'iss', 'sub', 'format'
                           or 'email'

        Raises:
            UserModel.DoesNotExist: If user not found
            ValueError: If request format is invalid
        """
        # Validate logout_token if provided
        if self.logout_token:
            self._validate_logout_token()

        # Determine logout type and process accordingly
        if 'sub' in request_data:
            self._process_logout_by_sub(request_data)
        elif 'email' in request_data:
            self._process_logout_by_email(request_data['email'])
        else:
            raise ValueError(
                "Invalid logout request: missing 'sub' or 'email'",
            )

    def _process_logout_by_sub(self, request_data: dict):
        """
        Process logout using sub identifier.

        After logout_token verification, we trust the format from Okta.
        No need to validate format == "iss_sub" here.

        Args:
            request_data: Dict with 'format', 'iss', 'sub' fields
        """
        sub = request_data.get('sub')
        if not sub:
            raise ValueError("Missing 'sub' in request data")

        # Get user by sub (raises exception if not found)
        try:
            user = self._get_user_by_sub(sub)
        except UserModel.DoesNotExist:
            capture_sentry_message(
                message='Okta logout: user not found by sub',
                level=SentryLogLevel.WARNING,
                data={
                    'sub': sub,
                    'iss': request_data.get('iss'),
                    'format': request_data.get('format'),
                    'logout_token': self.logout_token,
                },
            )
            raise

        # Perform logout
        self._logout_user(user, okta_sub=sub)

    def _process_logout_by_email(self, email: str):
        """
        Process logout using email.

        Future implementation for Okta marketplace app.
        Will validate domain and find user by email.

        Args:
            email: User email address
        """
        # TODO: Implement email-based logout
        # 1. Extract domain from email
        # 2. Validate domain against allowed domains
        # 3. Find user by email in domain
        # 4. Perform logout
        raise NotImplementedError(
            "Email-based logout not yet implemented",
        )

    def _validate_logout_token(self):
        """
        Validate logout_token with Okta introspection endpoint.

        The logout_token is a JWT that must be verified to ensure
        the request is authentic and not from an attacker.

        Raises:
            ValueError: If token is invalid or verification fails
        """
        if not self.logout_token:
            return

        try:
            # Decode token without verification to get issuer
            payload = jwt.decode(
                self.logout_token,
                options={
                    "verify_signature": False,
                    "verify_exp": False,
                    "verify_aud": False,
                    "verify_iss": False,
                },
            )
            issuer = payload.get('iss', '')

            # Extract domain from issuer (e.g., https://domain/oauth2/...)
            if not issuer:
                raise ValueError("Token missing issuer")

            # Validate token with Okta introspection endpoint
            domain = issuer.replace('https://', '').split('/')[0]
            response = requests.post(
                f'https://{domain}/oauth2/default/v1/introspect',
                data={
                    'token': self.logout_token,
                    'token_type_hint': 'logout_token',
                    'client_id': settings.OKTA_CLIENT_ID,
                    'client_secret': settings.OKTA_CLIENT_SECRET,
                },
                timeout=10,
            )

            if not response.ok:
                raise ValueError(
                    f"Token validation failed: {response.status_code}",
                )

            result = response.json()
            if not result.get('active', False):
                raise ValueError("Token is not active")

        except (
            jwt.DecodeError,
            jwt.InvalidTokenError,
            requests.RequestException,
        ) as ex:
            capture_sentry_message(
                message=f'Okta logout token validation failed: {ex!s}',
                level=SentryLogLevel.ERROR,
                data={'logout_token': self.logout_token},
            )
            raise ValueError(f"Invalid logout_token: {ex!s}") from ex

    def _get_user_by_sub(self, okta_sub: str) -> UserModel:
        """
        Get user by cached Okta sub identifier.

        Args:
            okta_sub: Okta subject identifier

        Returns:
            User instance

        Raises:
            UserModel.DoesNotExist: If user not found
        """
        cache_key = f'{self.CACHE_KEY_PREFIX}_{okta_sub}'
        user_id = self.cache.get(cache_key)

        if not user_id:
            raise UserModel.DoesNotExist(
                f"User not found for okta_sub: {okta_sub}",
            )

        try:
            return UserModel.objects.get(id=user_id)
        except UserModel.DoesNotExist:
            # Clear stale cache entry
            self.cache.delete(cache_key)
            raise

    def _logout_user(self, user: UserModel, okta_sub: Optional[str]):
        """
        Perform user logout:
        - Delete AccessToken for OKTA source
        - Clear token and profile cache
        - Terminate all user sessions

        Args:
            user: User to logout
            okta_sub: Okta subject identifier to clear from cache
        """
        # Get access tokens before deletion for profile cache cleanup
        access_tokens = list(
            AccessToken.objects.filter(
                user=user,
                source=self.SOURCE,
            ).values_list('access_token', flat=True),
        )

        # Delete access tokens
        AccessToken.objects.filter(user=user, source=self.SOURCE).delete()

        # Clear profile cache for each access token
        for access_token in access_tokens:
            cache_key = f'user_profile_{access_token}'
            self.cache.delete(cache_key)

        # Clear cached user by sub
        if okta_sub:
            cache_key = f'{self.CACHE_KEY_PREFIX}_{okta_sub}'
            self.cache.delete(cache_key)

        # Clear all tokens from cache (terminate all sessions)
        PneumaticToken.expire_all_tokens(user)
