import jwt
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import caches
from typing import Optional

from src.accounts.enums import (
    UserStatus,
    SourceType,
)
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
    CACHE_TIMEOUT = 2592000  # 30 days
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
        1. iss_sub format: Uses cached sub identifier
        2. email format: Uses email with domain validation

        Args:
            **request_data: Validated data from serializer containing:
                - format: 'iss_sub' or 'email'
                - sub_id_data: Original sub_id object from request

        All errors are logged to Sentry instead of raising exceptions.
        """
        # Validate logout_token
        if not self._validate_logout_token():
            return

        # Process based on format type
        format_type = request_data.get('format')
        sub_id_data = request_data.get('sub_id_data', {})

        if format_type == 'iss_sub':
            sub = sub_id_data.get('sub')
            if not sub:
                capture_sentry_message(
                    message="Missing 'sub' field in iss_sub format",
                    level=SentryLogLevel.ERROR,
                    data={'request_data': request_data},
                )
                return
            self._process_logout_by_sub(sub)
        elif format_type == 'email':
            email = sub_id_data.get('email')
            if not email:
                capture_sentry_message(
                    message="Missing 'email' field in email format",
                    level=SentryLogLevel.ERROR,
                    data={'request_data': request_data},
                )
                return
            self._process_logout_by_email(email)
        else:
            capture_sentry_message(
                message=f"Unsupported format: {format_type}",
                level=SentryLogLevel.ERROR,
                data={'request_data': request_data},
            )

    def _process_logout_by_sub(self, sub: str):
        """
        Process logout using sub identifier.

        After logout_token verification, we trust the sub from Okta.

        Args:
            sub: Okta subject identifier
        """
        # Get user by sub
        try:
            user = self._get_user_by_sub(sub)
        except UserModel.DoesNotExist:
            capture_sentry_message(
                message='Okta logout: user not found by sub',
                level=SentryLogLevel.WARNING,
                data={
                    'sub': sub,
                    'logout_token': self.logout_token,
                },
            )
            return

        # Perform logout
        self._logout_user(user, okta_sub=sub)

    def _process_logout_by_email(self, email: str):
        """
        Process logout using email with domain validation.

        Args:
            email: User email address from Okta
        """
        # Extract domain from email
        if '@' not in email:
            capture_sentry_message(
                message=f"Invalid email format: {email}",
                level=SentryLogLevel.ERROR,
                data={'email': email},
            )
            return

        domain = email.split('@')[1].lower()

        # Find user by email with domain validation
        try:
            user = UserModel.objects.get(
                email__iexact=email,
                status=UserStatus.ACTIVE,
            )
        except UserModel.DoesNotExist:
            capture_sentry_message(
                message='Okta logout: user not found by email',
                level=SentryLogLevel.WARNING,
                data={
                    'email': email,
                    'domain': domain,
                    'logout_token': self.logout_token,
                },
            )
            return

        # Perform logout (no okta_sub for email format)
        self._logout_user(user, okta_sub=None)

    def _validate_logout_token(self) -> bool:
        """
        Validate logout_token with Okta introspection endpoint.

        The logout_token is a JWT that must be verified to ensure
        the request is authentic and not from an attacker.

        Returns:
            bool: True if token is valid, False otherwise
        """

        try:
            # Validate token with Okta introspection endpoint
            response = requests.post(
                f'https://{settings.OKTA_DOMAIN}/oauth2/default/v1/introspect',
                data={
                    'token': self.logout_token,
                    'token_type_hint': 'logout_token',
                    'client_id': settings.OKTA_CLIENT_ID,
                    'client_secret': settings.OKTA_CLIENT_SECRET,
                },
                timeout=10,
            )

            if not response.ok:
                capture_sentry_message(
                    message='Okta token validation failed',
                    level=SentryLogLevel.ERROR,
                    data={
                        'logout_token': self.logout_token,
                        'status_code': response.status_code,
                        'response': response.text,
                    },
                )
                return False

            result = response.json()
            if not result.get('active', False):
                capture_sentry_message(
                    message='Okta token is not active',
                    level=SentryLogLevel.ERROR,
                    data={
                        'logout_token': self.logout_token,
                        'result': result,
                    },
                )
                return False

            return True

        except (
            jwt.DecodeError,
            jwt.InvalidTokenError,
            requests.RequestException,
        ) as ex:
            capture_sentry_message(
                message=f'Okta logout token validation failed: {ex!s}',
                level=SentryLogLevel.ERROR,
                data={'logout_token': self.logout_token, 'error': str(ex)},
            )
            return False

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
