import jwt
import requests
import time
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
    log_okta_message,
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
        start_time = time.time()

        log_okta_message(
            message="Starting Okta logout process",
            data={
                'request_data': request_data,
                'logout_token_present': bool(self.logout_token),
            },
            level=SentryLogLevel.INFO,
        )

        # Validate logout_token
        log_okta_message(
            message="Validating logout token",
            level=SentryLogLevel.DEBUG,
        )

        if not self._validate_logout_token():
            log_okta_message(
                message="Logout token validation failed, aborting process",
                level=SentryLogLevel.ERROR,
            )
            return

        log_okta_message(
            message="Logout token validation successful",
            level=SentryLogLevel.DEBUG,
        )

        # Process based on format type
        format_type = request_data.get('format')
        sub_id_data = request_data.get('sub_id_data', {})

        log_okta_message(
            message=f"Processing logout with format: {format_type}",
            data={
                'format_type': format_type,
                'sub_id_data_keys': (
                    list(sub_id_data.keys()) if sub_id_data else []
                ),
            },
            level=SentryLogLevel.INFO,
        )

        if format_type == 'iss_sub':
            sub = sub_id_data.get('sub')
            if not sub:
                error_msg = "Missing 'sub' field in iss_sub format"
                log_okta_message(
                    message=error_msg,
                    data={'request_data': request_data},
                    level=SentryLogLevel.ERROR,
                )
                capture_sentry_message(
                    message=error_msg,
                    level=SentryLogLevel.ERROR,
                    data={'request_data': request_data},
                )
                return

            log_okta_message(
                message=f"Processing logout by sub: {sub}",
                level=SentryLogLevel.INFO,
            )
            self._process_logout_by_sub(sub)

        elif format_type == 'email':
            email = sub_id_data.get('email')
            if not email:
                error_msg = "Missing 'email' field in email format"
                log_okta_message(
                    message=error_msg,
                    data={'request_data': request_data},
                    level=SentryLogLevel.ERROR,
                )
                capture_sentry_message(
                    message=error_msg,
                    level=SentryLogLevel.ERROR,
                    data={'request_data': request_data},
                )
                return

            log_okta_message(
                message=f"Processing logout by email: {email}",
                level=SentryLogLevel.INFO,
            )
            self._process_logout_by_email(email)

        else:
            error_msg = f"Unsupported format: {format_type}"
            log_okta_message(
                message=error_msg,
                data={'request_data': request_data},
                level=SentryLogLevel.ERROR,
            )
            capture_sentry_message(
                message=error_msg,
                level=SentryLogLevel.ERROR,
                data={'request_data': request_data},
            )
            return

        execution_time = time.time() - start_time
        log_okta_message(
            message="Okta logout process completed successfully",
            data={
                'execution_time_seconds': round(execution_time, 3),
                'format_type': format_type,
            },
            level=SentryLogLevel.INFO,
        )

    def _process_logout_by_sub(self, sub: str):
        """
        Process logout using sub identifier.

        After logout_token verification, we trust the sub from Okta.

        Args:
            sub: Okta subject identifier
        """
        log_okta_message(
            message=f"Starting logout process by sub: {sub}",
            level=SentryLogLevel.DEBUG,
        )

        # Get user by sub
        try:
            log_okta_message(
                message=f"Looking up user by sub: {sub}",
                level=SentryLogLevel.DEBUG,
            )
            user = self._get_user_by_sub(sub)
            log_okta_message(
                message=f"User found by sub: {user.id} ({user.email})",
                data={
                    'user_id': user.id,
                    'user_email': user.email,
                    'user_status': user.status,
                },
                level=SentryLogLevel.INFO,
            )
        except UserModel.DoesNotExist:
            error_msg = 'Okta logout: user not found by sub'
            log_okta_message(
                message=error_msg,
                data={
                    'sub': sub,
                    'logout_token': self.logout_token,
                },
                level=SentryLogLevel.WARNING,
            )
            capture_sentry_message(
                message=error_msg,
                level=SentryLogLevel.WARNING,
                data={
                    'sub': sub,
                    'logout_token': self.logout_token,
                },
            )
            return

        # Perform logout
        log_okta_message(
            message=f"Performing logout for user {user.id}",
            data={'user_id': user.id, 'okta_sub': sub},
            level=SentryLogLevel.INFO,
        )
        self._logout_user(user, okta_sub=sub)

    def _process_logout_by_email(self, email: str):
        """
        Process logout using email with domain validation.

        Args:
            email: User email address from Okta
        """
        log_okta_message(
            message=f"Starting logout process by email: {email}",
            level=SentryLogLevel.DEBUG,
        )

        try:
            log_okta_message(
                message=f"Looking up active user by email: {email}",
                level=SentryLogLevel.DEBUG,
            )
            user = UserModel.objects.get(
                email__iexact=email,
                status=UserStatus.ACTIVE,
            )
            log_okta_message(
                message=f"User found by email: {user.id} ({user.email})",
                data={
                    'user_id': user.id,
                    'user_email': user.email,
                    'user_status': user.status,
                },
                level=SentryLogLevel.INFO,
            )
        except UserModel.DoesNotExist:
            error_msg = 'Okta logout: user not found by email'
            log_okta_message(
                message=error_msg,
                data={
                    'email': email,
                    'logout_token': self.logout_token,
                },
                level=SentryLogLevel.WARNING,
            )
            capture_sentry_message(
                message=error_msg,
                level=SentryLogLevel.WARNING,
                data={
                    'email': email,
                    'logout_token': self.logout_token,
                },
            )
            return

        # Perform logout (no okta_sub for email format)
        log_okta_message(
            message=f"Performing logout for user {user.id} (email format)",
            data={'user_id': user.id, 'email': email},
            level=SentryLogLevel.INFO,
        )
        self._logout_user(user, okta_sub=None)

    def _validate_logout_token(self) -> bool:
        """
        Validate logout_token with Okta introspection endpoint.

        The logout_token is a JWT that must be verified to ensure
        the request is authentic and not from an attacker.

        Returns:
            bool: True if token is valid, False otherwise
        """
        if not self.logout_token:
            log_okta_message(
                message="No logout token provided for validation",
                level=SentryLogLevel.ERROR,
            )
            return False

        log_okta_message(
            message="Starting logout token validation with Okta",
            data={'okta_domain': settings.OKTA_DOMAIN},
            level=SentryLogLevel.DEBUG,
        )

        try:
            # Validate token with Okta introspection endpoint
            introspect_url = (
                f'https://{settings.OKTA_DOMAIN}/oauth2/default/v1/introspect'
            )

            log_okta_message(
                message=f"Sending token validation request {introspect_url}",
                level=SentryLogLevel.DEBUG,
            )

            response = requests.post(
                introspect_url,
                data={
                    'token': self.logout_token,
                    'token_type_hint': 'logout_token',
                    'client_id': settings.OKTA_CLIENT_ID,
                    'client_secret': settings.OKTA_CLIENT_SECRET,
                },
                timeout=10,
            )

            log_okta_message(
                message=f"Received response from Okta: {response.status_code}",
                data={'status_code': response.status_code},
                level=SentryLogLevel.DEBUG,
            )

            if not response.ok:
                error_msg = 'Okta token validation failed'
                error_data = {
                    'logout_token': self.logout_token,
                    'status_code': response.status_code,
                    'response': response.text,
                }
                log_okta_message(
                    message=error_msg,
                    data=error_data,
                    level=SentryLogLevel.ERROR,
                )
                capture_sentry_message(
                    message=error_msg,
                    level=SentryLogLevel.ERROR,
                    data=error_data,
                )
                return False

            result = response.json()
            log_okta_message(
                message="Token validation response received",
                data={'active': result.get('active', False)},
                level=SentryLogLevel.DEBUG,
            )

            if not result.get('active', False):
                error_msg = 'Okta token is not active'
                error_data = {
                    'logout_token': self.logout_token,
                    'result': result,
                }
                log_okta_message(
                    message=error_msg,
                    data=error_data,
                    level=SentryLogLevel.ERROR,
                )
                capture_sentry_message(
                    message=error_msg,
                    level=SentryLogLevel.ERROR,
                    data=error_data,
                )
                return False

            log_okta_message(
                message="Token validation successful",
                level=SentryLogLevel.DEBUG,
            )
            return True

        except (
            jwt.DecodeError,
            jwt.InvalidTokenError,
            requests.RequestException,
        ) as ex:
            error_msg = f'Okta logout token validation failed: {ex!s}'
            error_data = {'logout_token': self.logout_token, 'error': str(ex)}
            log_okta_message(
                message=error_msg,
                data=error_data,
                level=SentryLogLevel.ERROR,
            )
            capture_sentry_message(
                message=error_msg,
                level=SentryLogLevel.ERROR,
                data=error_data,
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

        log_okta_message(
            message=f"Looking up user in cache with key: {cache_key}",
            level=SentryLogLevel.DEBUG,
        )

        user_id = self.cache.get(cache_key)

        if not user_id:
            log_okta_message(
                message=f"No user_id found in cache for sub: {okta_sub}",
                data={'cache_key': cache_key},
                level=SentryLogLevel.WARNING,
            )
            raise UserModel.DoesNotExist(
                f"User not found for okta_sub: {okta_sub}",
            )

        log_okta_message(
            message=f"Found user_id in cache: {user_id}",
            data={'user_id': user_id, 'cache_key': cache_key},
            level=SentryLogLevel.DEBUG,
        )

        try:
            user = UserModel.objects.get(id=user_id)
            log_okta_message(
                message=f"Successfully retrieved user database: {user.email}",
                data={'user_id': user_id, 'user_email': user.email},
                level=SentryLogLevel.DEBUG,
            )
            return user
        except UserModel.DoesNotExist:
            # Clear stale cache entry
            log_okta_message(
                message=f"User {user_id} not found in DB, clearing cache",
                data={'user_id': user_id, 'cache_key': cache_key},
                level=SentryLogLevel.WARNING,
            )
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
        log_okta_message(
            message=f"Starting logout process for user {user.id}",
            data={
                'user_id': user.id,
                'user_email': user.email,
                'okta_sub': okta_sub,
            },
            level=SentryLogLevel.INFO,
        )

        # Get access tokens before deletion for profile cache cleanup
        access_tokens = list(
            AccessToken.objects.filter(
                user=user,
                source=self.SOURCE,
            ).values_list('access_token', flat=True),
        )

        log_okta_message(
            message=f"Found {len(access_tokens)} OKTA access tokens to delete",
            data={'token_count': len(access_tokens), 'user_id': user.id},
            level=SentryLogLevel.DEBUG,
        )

        # Delete access tokens
        deleted_count = AccessToken.objects.filter(
            user=user,
            source=self.SOURCE,
        ).delete()[0]

        log_okta_message(
            message=f"Deleted {deleted_count} OKTA access tokens",
            data={'deleted_count': deleted_count, 'user_id': user.id},
            level=SentryLogLevel.INFO,
        )

        # Clear profile cache for each access token
        cleared_cache_keys = []
        for access_token in access_tokens:
            cache_key = f'user_profile_{access_token}'
            self.cache.delete(cache_key)
            cleared_cache_keys.append(cache_key)

        log_okta_message(
            message=f"Cleared {len(cleared_cache_keys)} profile cache entries",
            data={'cleared_keys_count': len(cleared_cache_keys)},
            level=SentryLogLevel.DEBUG,
        )

        # Clear cached user by sub
        if okta_sub:
            cache_key = f'{self.CACHE_KEY_PREFIX}_{okta_sub}'
            self.cache.delete(cache_key)
            log_okta_message(
                message=f"Cleared user cache entry: {cache_key}",
                data={'cache_key': cache_key},
                level=SentryLogLevel.DEBUG,
            )

        # Clear all tokens from cache (terminate all sessions)
        log_okta_message(
            message=f"Expiring all tokens for user {user.id}",
            data={'user_id': user.id},
            level=SentryLogLevel.INFO,
        )

        PneumaticToken.expire_all_tokens(user)

        log_okta_message(
            message=f"User logout completed successfully for {user.id}",
            data={
                'user_id': user.id,
                'user_email': user.email,
                'tokens_deleted': deleted_count,
                'cache_entries_cleared': len(cleared_cache_keys),
            },
            level=SentryLogLevel.INFO,
        )
