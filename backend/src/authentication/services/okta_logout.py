import jwt
import requests
import time
from urllib.parse import urlparse, urlunparse

import base64
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import caches
from typing import Optional, Dict, Any
from jwt.algorithms import RSAAlgorithm

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

    Configuration:
    - OKTA_LOGOUT_AUTH_SERVER_TYPE: 'org' (default) or 'default'
      Controls which Authorization Server endpoint to try first for JWKS.
      Global Token Revocation typically uses Organization AS (/oauth2/v1/keys).
    - OKTA_LOGOUT_WEBHOOK_URL: Explicit webhook URL for audience validation
    - BACKEND_URL: Used to construct webhook URL if not explicitly set
    - OKTA_CLIENT_ID: Fallback audience for regular logout tokens
    """

    # Constants
    SOURCE = SourceType.OKTA
    CACHE_TIMEOUT = 2592000  # 30 days
    CACHE_KEY_PREFIX = 'okta_sub_to_user'
    JWKS_CACHE_KEY = 'okta_jwks'
    JWKS_CACHE_TIMEOUT = 3600  # 1 hour

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

        # Validate logout_token and extract claims
        log_okta_message(
            message="Validating logout token",
            level=SentryLogLevel.DEBUG,
        )

        token_payload = self._validate_logout_token()
        if not token_payload:
            # Check if fallback processing is allowed for invalid tokens
            allow_fallback = getattr(
                settings,
                'OKTA_LOGOUT_ALLOW_FALLBACK_ON_INVALID_TOKEN',
                False,
            )

            if allow_fallback:
                log_okta_message(
                    message=(
                        "Logout token validation failed, but fallback "
                        "processing is enabled. Proceeding with request data."
                    ),
                    data={'fallback_enabled': True},
                    level=SentryLogLevel.WARNING,
                )
                # Continue with fallback processing using request data
                token_payload = {}
            else:
                log_okta_message(
                    message=(
                        "Logout token validation failed, aborting process. "
                        "Set OKTA_LOGOUT_ALLOW_FALLBACK_ON_INVALID_TOKEN=True "
                        "to enable fallback processing."
                    ),
                    level=SentryLogLevel.ERROR,
                )
                return

        log_okta_message(
            message="Logout token validation successful",
            level=SentryLogLevel.DEBUG,
        )

        # Process logout using JWT token claims (preferred) or fallback
        # to request data
        token_sub = token_payload.get('sub')
        token_sid = token_payload.get('sid')

        # Determine logout method based on available claims
        if token_sub:
            log_okta_message(
                message=f"Processing logout by JWT sub: {token_sub}",
                data={'sid_present': bool(token_sid)},
                level=SentryLogLevel.INFO,
            )
            self._process_logout_by_sub(token_sub, token_sid)
        else:
            # Fallback to request data processing for backward compatibility
            format_type = request_data.get('format')
            sub_id_data = request_data.get('sub_id_data', {})

            log_okta_message(
                message=f"Fallback: Processing logout format: {format_type}",
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

    def _process_logout_by_sub(self, sub: str, sid: Optional[str] = None):
        """
        Process logout using sub identifier.

        After logout_token verification, we trust the sub from Okta.

        Args:
            sub: Okta subject identifier
            sid: Optional session identifier for session-specific logout
        """
        log_okta_message(
            message=f"Starting logout process by sub: {sub}",
            data={'sid': sid, 'session_specific': bool(sid)},
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
            data={
                'user_id': user.id,
                'okta_sub': sub,
                'session_id': sid,
                'session_specific': bool(sid),
            },
            level=SentryLogLevel.INFO,
        )
        self._logout_user(user, okta_sub=sub, session_id=sid)

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
        self._logout_user(user, okta_sub=None, session_id=None)

    def _validate_logout_token(self) -> Optional[Dict[str, Any]]:
        """
        Validate logout_token using JWT verification with Okta JWKS.

        The logout_token is a JWT that must be verified to ensure
        the request is authentic and not from an attacker.

        According to OAuth 2.0 Back-Channel Logout spec, logout tokens
        should be validated as JWTs, not through introspection endpoint.

        Returns:
            Dict containing token payload if valid, None otherwise
        """
        if not self.logout_token:
            log_okta_message(
                message="No logout token provided for validation",
                level=SentryLogLevel.ERROR,
            )
            return None

        log_okta_message(
            message="Starting logout token validation with JWT",
            data={
                'okta_domain': settings.OKTA_DOMAIN,
                'token_length': len(self.logout_token),
                'has_okta_client_id': bool(
                    getattr(settings, 'OKTA_CLIENT_ID', None),
                ),
            },
            level=SentryLogLevel.DEBUG,
        )

        try:
            # Decode header to get kid (key ID)
            unverified_header = jwt.get_unverified_header(
                self.logout_token,
            )
            kid = unverified_header.get('kid')
            if not kid:
                error_msg = 'Missing kid in logout token header'
                log_okta_message(
                    message=error_msg,
                    data={'header': unverified_header},
                    level=SentryLogLevel.ERROR,
                )
                capture_sentry_message(
                    message=error_msg,
                    level=SentryLogLevel.ERROR,
                    data={'header': unverified_header},
                )
                return None

            log_okta_message(
                message="Extracted kid from token header",
                data={'kid': kid},
                level=SentryLogLevel.DEBUG,
            )

            # Get public key from JWKS (with automatic refresh on key rotation)
            public_key = self._get_public_key_from_jwks(kid)
            if not public_key:
                error_msg = (
                    'Failed to get public key from JWKS. This may indicate '
                    'key rotation, token from wrong Okta domain, or '
                    'configuration mismatch.'
                )
                log_okta_message(
                    message=error_msg,
                    data={
                        'kid': kid,
                        'okta_domain': settings.OKTA_DOMAIN,
                        'token_header': unverified_header,
                    },
                    level=SentryLogLevel.ERROR,
                )
                capture_sentry_message(
                    message=error_msg,
                    level=SentryLogLevel.ERROR,
                    data={
                        'kid': kid,
                        'okta_domain': settings.OKTA_DOMAIN,
                        'token_header': unverified_header,
                    },
                )
                return None

            # Build expected issuer and audience
            expected_issuer = f'https://{settings.OKTA_DOMAIN}'

            # For Global Token Revocation, Okta uses webhook URL as audience,
            # not the client_id. Try to determine the correct audience.
            expected_audience = self._get_expected_audience()
            if not expected_audience:
                error_msg = (
                    'Cannot determine expected audience. Configure either '
                    'OKTA_LOGOUT_WEBHOOK_URL or OKTA_CLIENT_ID'
                )
                log_okta_message(
                    message=error_msg,
                    level=SentryLogLevel.ERROR,
                )
                capture_sentry_message(
                    message=error_msg,
                    level=SentryLogLevel.ERROR,
                )
                return None

            log_okta_message(
                message="Verifying JWT token",
                data={
                    'expected_issuer': expected_issuer,
                    'expected_audience': expected_audience,
                },
                level=SentryLogLevel.DEBUG,
            )

            # Verify and decode token
            # First try with expected audience
            payload = None
            validation_errors = []

            # Try multiple audience validation strategies
            audiences_to_try = self._get_possible_audiences()

            for i, aud in enumerate(audiences_to_try):
                try:
                    log_okta_message(
                        message=(
                            f"Trying audience validation "
                            f"{i+1}/{len(audiences_to_try)}"
                        ),
                        data={
                            'audience': aud,
                            'attempt': i+1,
                        },
                        level=SentryLogLevel.DEBUG,
                    )

                    payload = jwt.decode(
                        self.logout_token,
                        public_key,
                        algorithms=['RS256'],
                        issuer=expected_issuer,
                        audience=aud,
                        options={
                            'verify_signature': True,
                            'verify_exp': True,
                            'verify_iss': True,
                            'verify_aud': True,
                        },
                    )

                    log_okta_message(
                        message="Token validation successful with audience",
                        data={
                            'successful_audience': aud,
                            'attempt': i+1,
                        },
                        level=SentryLogLevel.DEBUG,
                    )
                    break  # Success, exit loop

                except jwt.InvalidAudienceError as ex:
                    validation_errors.append(f"Audience '{aud}': {ex!s}")
                    continue  # Try next audience

            if payload is None:
                # All audience validations failed
                error_msg = (
                    f'Invalid token audience. Tried: {validation_errors}'
                )
                log_okta_message(
                    message=error_msg,
                    data={
                        'logout_token': self.logout_token,
                        'audiences_tried': audiences_to_try,
                        'validation_errors': validation_errors,
                    },
                    level=SentryLogLevel.ERROR,
                )
                capture_sentry_message(
                    message=error_msg,
                    level=SentryLogLevel.ERROR,
                    data={
                        'audiences_tried': audiences_to_try,
                        'validation_errors': validation_errors,
                    },
                )
                return None

            # Verify token type (should be logout token)
            token_type = unverified_header.get('typ')
            expected_types = [
                'logout+jwt',
                'global-token-revocation-jwt',
                'global-token-revocation+jwt',  # Okta uses this format
            ]
            if token_type not in expected_types:
                log_okta_message(
                    message="Token type mismatch",
                    data={
                        'expected': expected_types,
                        'actual': token_type,
                    },
                    level=SentryLogLevel.WARNING,
                )
                # Don't fail on type mismatch, as it may vary by provider

            # Validate required claims according to OpenID Connect
            # Back-Channel Logout specification
            if not self._validate_logout_token_claims(payload):
                return None

            log_okta_message(
                message="Token validation successful",
                data={
                    'sub': payload.get('sub'),
                    'sid': payload.get('sid'),
                    'jti': payload.get('jti'),
                    'iat': payload.get('iat'),
                    'exp': payload.get('exp'),
                    'events': payload.get('events'),
                },
                level=SentryLogLevel.DEBUG,
            )
            return payload

        except jwt.ExpiredSignatureError as ex:
            error_msg = f'Logout token expired: {ex!s}'
            log_okta_message(
                message=error_msg,
                data={'logout_token': self.logout_token},
                level=SentryLogLevel.ERROR,
            )
            capture_sentry_message(
                message=error_msg,
                level=SentryLogLevel.ERROR,
                data={'error': str(ex)},
            )
            return None
        except jwt.InvalidIssuerError as ex:
            error_msg = f'Invalid token issuer: {ex!s}'
            log_okta_message(
                message=error_msg,
                data={'logout_token': self.logout_token},
                level=SentryLogLevel.ERROR,
            )
            capture_sentry_message(
                message=error_msg,
                level=SentryLogLevel.ERROR,
                data={'error': str(ex)},
            )
            return None
        except jwt.InvalidAudienceError as ex:
            error_msg = f'Invalid token audience: {ex!s}'
            log_okta_message(
                message=error_msg,
                data={'logout_token': self.logout_token},
                level=SentryLogLevel.ERROR,
            )
            capture_sentry_message(
                message=error_msg,
                level=SentryLogLevel.ERROR,
                data={'error': str(ex)},
            )
            return None
        except (
            jwt.DecodeError,
            jwt.InvalidTokenError,
            requests.RequestException,
            KeyError,
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
            return None

    def _validate_logout_token_claims(self, payload: Dict[str, Any]) -> bool:
        """
        Validate logout token claims according to OpenID Connect
        Back-Channel Logout specification.

        Required claims:
        - sub or sid (at least one must be present)
        - events with logout event type
        - jti (JWT ID)
        - nonce must NOT be present

        Args:
            payload: Decoded JWT payload

        Returns:
            bool: True if all required claims are valid
        """
        # Check that either sub or sid is present
        sub = payload.get('sub')
        sid = payload.get('sid')
        if not sub and not sid:
            error_msg = (
                'Logout token must contain either "sub" or "sid" claim'
            )
            log_okta_message(
                message=error_msg,
                data={'payload_keys': list(payload.keys())},
                level=SentryLogLevel.ERROR,
            )
            capture_sentry_message(
                message=error_msg,
                level=SentryLogLevel.ERROR,
                data={'payload': payload},
            )
            return None

        # Check that jti is present
        jti = payload.get('jti')
        if not jti:
            error_msg = 'Logout token must contain "jti" claim'
            log_okta_message(
                message=error_msg,
                data={'payload_keys': list(payload.keys())},
                level=SentryLogLevel.ERROR,
            )
            capture_sentry_message(
                message=error_msg,
                level=SentryLogLevel.ERROR,
                data={'payload': payload},
            )
            return None

        # Check that nonce is NOT present
        if 'nonce' in payload:
            error_msg = 'Logout token must NOT contain "nonce" claim'
            log_okta_message(
                message=error_msg,
                data={'payload_keys': list(payload.keys())},
                level=SentryLogLevel.ERROR,
            )
            capture_sentry_message(
                message=error_msg,
                level=SentryLogLevel.ERROR,
                data={'payload': payload},
            )
            return None

        # Check events claim
        # For Global Token Revocation, events claim may be optional
        events = payload.get('events')
        if not events:
            # Check if this is a Global Token Revocation token
            token_header = jwt.get_unverified_header(self.logout_token)
            token_type = token_header.get('typ', '')
            if 'global-token-revocation' in token_type:
                log_okta_message(
                    message='Global Token Revtion token without events claim',
                    data={
                        'token_type': token_type,
                        'payload_keys': list(payload.keys()),
                    },
                    level=SentryLogLevel.DEBUG,
                )
                # For GTR tokens, events claim is optional
                events = {}
            else:
                error_msg = 'Logout token must contain "events" claim'
                log_okta_message(
                    message=error_msg,
                    data={'payload_keys': list(payload.keys())},
                    level=SentryLogLevel.ERROR,
                )
                capture_sentry_message(
                    message=error_msg,
                    level=SentryLogLevel.ERROR,
                    data={'payload': payload},
                )
                return None

        # Validate events claim structure
        logout_event_type = (
            'http://schemas.openid.net/secevent/risc/event-type/logout'
        )
        if not isinstance(events, dict) or logout_event_type not in events:
            error_msg = (
                f'Logout token events claim must contain '
                f'"{logout_event_type}" event'
            )
            log_okta_message(
                message=error_msg,
                data={'events': events},
                level=SentryLogLevel.ERROR,
            )
            capture_sentry_message(
                message=error_msg,
                level=SentryLogLevel.ERROR,
                data={'events': events},
            )
            return None

        log_okta_message(
            message="All required logout token claims validated successfully",
            data={
                'sub': sub,
                'sid': sid,
                'jti': jti,
                'has_logout_event': logout_event_type in events,
            },
            level=SentryLogLevel.DEBUG,
        )
        return True

    def _get_expected_audience(self) -> Optional[str]:
        """
        Determine the expected audience for logout token validation.

        For Global Token Revocation, Okta uses the webhook URL as audience.
        For regular Back-Channel Logout, it may use client_id.

        Priority:
        1. OKTA_LOGOUT_WEBHOOK_URL (explicit webhook URL)
        2. Construct from BACKEND_URL + logout path
        3. OKTA_CLIENT_ID (fallback for regular logout tokens)

        Returns:
            Expected audience string or None if cannot be determined
        """
        # Try explicit webhook URL configuration
        webhook_url = getattr(settings, 'OKTA_LOGOUT_WEBHOOK_URL', None)
        if webhook_url:
            log_okta_message(
                message="Using explicit webhook URL as audience",
                data={'audience': webhook_url},
                level=SentryLogLevel.DEBUG,
            )
            return webhook_url

        # Try to construct from BACKEND_URL
        backend_url = getattr(settings, 'BACKEND_URL', None)
        if backend_url:
            # Remove trailing slash and add logout path
            backend_url = backend_url.rstrip('/')
            webhook_url = f"{backend_url}/auth/okta/logout"
            log_okta_message(
                message="Constructed webhook URL from BACKEND_URL",
                data={
                    'backend_url': backend_url,
                    'constructed_audience': webhook_url,
                },
                level=SentryLogLevel.DEBUG,
            )
            return webhook_url

        # Fallback to client_id for regular logout tokens
        client_id = getattr(settings, 'OKTA_CLIENT_ID', None)
        if client_id:
            log_okta_message(
                message="Using OKTA_CLIENT_ID as fallback audience",
                data={'audience': client_id},
                level=SentryLogLevel.DEBUG,
            )
            return client_id

        log_okta_message(
            message="Cannot determine expected audience - no config found",
            data={
                'has_webhook_url': hasattr(
                    settings, 'OKTA_LOGOUT_WEBHOOK_URL',
                ),
                'has_backend_url': hasattr(settings, 'BACKEND_URL'),
                'has_client_id': hasattr(settings, 'OKTA_CLIENT_ID'),
            },
            level=SentryLogLevel.ERROR,
        )
        return None

    def _get_possible_audiences(self) -> list:
        """
        Get list of possible audiences to try for token validation.

        Returns all configured audience options in priority order:
        1. Explicit webhook URL
        2. Constructed webhook URL from BACKEND_URL
        3. Client ID (fallback)

        Returns:
            List of audience strings to try
        """
        audiences = []

        # Try explicit webhook URL configuration
        webhook_url = getattr(settings, 'OKTA_LOGOUT_WEBHOOK_URL', None)
        if webhook_url and webhook_url not in audiences:
            audiences.append(webhook_url)

        # Try to construct from BACKEND_URL
        backend_url = getattr(settings, 'BACKEND_URL', None)
        if backend_url:
            backend_url = backend_url.rstrip('/')
            parsed = urlparse(backend_url)

            # Add version with original URL (may include port)
            constructed_url = f"{backend_url}/auth/okta/logout"
            if constructed_url not in audiences:
                audiences.append(constructed_url)

            # Also add version without port (common for production webhooks)
            if parsed.port:
                url_without_port = urlunparse((
                    parsed.scheme,
                    parsed.hostname,  # hostname without port
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment,
                ))
                constructed_url_no_port = (
                    f"{url_without_port}/auth/okta/logout"
                )
                if constructed_url_no_port not in audiences:
                    audiences.append(constructed_url_no_port)

        # Add client_id as fallback
        client_id = getattr(settings, 'OKTA_CLIENT_ID', None)
        if client_id and client_id not in audiences:
            audiences.append(client_id)

        log_okta_message(
            message="Generated possible audiences for validation",
            data={
                'audiences': audiences,
                'count': len(audiences),
            },
            level=SentryLogLevel.DEBUG,
        )

        return audiences

    def _get_jwks(
            self,
            force_refresh: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Get JWKS (JSON Web Key Set) from Okta.

        For Global Token Revocation (GTR), Okta uses the Organization
        Authorization Server, not the Default Authorization Server.
        This method tries both endpoints to handle different token types.

        JWKS is cached for 1 hour to reduce API calls, but can be force
        refreshed when key rotation occurs.

        Args:
            force_refresh: If True, bypass cache and fetch fresh JWKS

        Returns:
            Dict containing JWKS or None if failed
        """
        # Try to get from cache first (unless force refresh)
        if not force_refresh:
            cached_jwks = self.cache.get(self.JWKS_CACHE_KEY)
            if cached_jwks:
                log_okta_message(
                    message="Using cached JWKS",
                    level=SentryLogLevel.DEBUG,
                )
                return cached_jwks

        log_okta_message(
            message="Fetching JWKS from Okta",
            data={
                'okta_domain': settings.OKTA_DOMAIN,
                'force_refresh': force_refresh,
            },
            level=SentryLogLevel.DEBUG,
        )

        # Global Token Revocation uses Organization Authorization Server
        # Try this endpoint first as it's the correct one for logout tokens
        # Allow configuration override via settings
        if (hasattr(settings, 'OKTA_LOGOUT_AUTH_SERVER_TYPE') and
                settings.OKTA_LOGOUT_AUTH_SERVER_TYPE == 'default'):
            # Use Default Authorization Server first if explicitly configured
            jwks_endpoints = [
                f'https://{settings.OKTA_DOMAIN}/oauth2/default/v1/keys',
                f'https://{settings.OKTA_DOMAIN}/oauth2/v1/keys',
            ]
        else:
            # Default behavior: Organization Authorization Server first
            jwks_endpoints = [
                f'https://{settings.OKTA_DOMAIN}/oauth2/v1/keys',
                f'https://{settings.OKTA_DOMAIN}/oauth2/default/v1/keys',
            ]

        last_error = None
        for i, jwks_url in enumerate(jwks_endpoints):
            try:
                log_okta_message(
                    message=(
                        f"Trying JWKS endpoint {i+1}/{len(jwks_endpoints)}"
                    ),
                    data={
                        'endpoint': jwks_url,
                        'attempt': i+1,
                    },
                    level=SentryLogLevel.DEBUG,
                )
                response = requests.get(jwks_url, timeout=10)
                response.raise_for_status()

                jwks = response.json()
                # Cache JWKS for 1 hour
                self.cache.set(
                    self.JWKS_CACHE_KEY,
                    jwks,
                    timeout=self.JWKS_CACHE_TIMEOUT,
                )

                available_kids = [k.get('kid') for k in jwks.get('keys', [])]
                log_okta_message(
                    message="JWKS fetched and cached successfully",
                    data={
                        'endpoint': jwks_url,
                        'keys_count': len(jwks.get('keys', [])),
                        'available_kids': available_kids,
                        'force_refresh': force_refresh,
                        'successful_attempt': i+1,
                    },
                    level=SentryLogLevel.DEBUG,
                )
                return jwks

            except requests.RequestException as ex:
                last_error = ex
                log_okta_message(
                    message=f"Failed to fetch JWKS from endpoint {i+1}",
                    data={
                        'endpoint': jwks_url,
                        'error': str(ex),
                        'attempt': i+1,
                    },
                    level=SentryLogLevel.WARNING,
                )
                continue

        # All endpoints failed
        error_msg = f'Failed to fetch JWKS from all endpoints: {last_error!s}'
        log_okta_message(
            message=error_msg,
            data={
                'okta_domain': settings.OKTA_DOMAIN,
                'force_refresh': force_refresh,
                'endpoints_tried': jwks_endpoints,
            },
            level=SentryLogLevel.ERROR,
        )
        capture_sentry_message(
            message=error_msg,
            level=SentryLogLevel.ERROR,
            data={
                'error': str(last_error),
                'endpoints_tried': jwks_endpoints,
            },
        )
        return None

    def _get_public_key_from_jwks(self, kid: str) -> Optional[Any]:
        """
        Get public key from JWKS by kid (key ID).

        Implements key rotation handling by attempting to refresh JWKS
        if the required key is not found in the cached version.

        Args:
            kid: Key ID from JWT header

        Returns:
            Public key object (can be PEM string or key object) or None
        """
        # First attempt: try cached JWKS
        jwks = self._get_jwks(force_refresh=False)
        if not jwks:
            return None

        # Look for the key in current JWKS
        public_key = self._extract_key_from_jwks(jwks, kid)
        if public_key:
            return public_key

        # Key not found in cached JWKS - this might be due to key rotation
        # Attempt to refresh JWKS and try again
        log_okta_message(
            message="Key not found in cached JWKS, attempting refresh",
            data={
                'kid': kid,
                'cached_kids': [k.get('kid') for k in jwks.get('keys', [])],
            },
            level=SentryLogLevel.INFO,
        )

        # Second attempt: force refresh JWKS
        fresh_jwks = self._get_jwks(force_refresh=True)
        if not fresh_jwks:
            error_msg = 'Failed to refresh JWKS from Okta'
            log_okta_message(
                message=error_msg,
                data={'kid': kid},
                level=SentryLogLevel.ERROR,
            )
            return None

        # Look for the key in fresh JWKS
        public_key = self._extract_key_from_jwks(fresh_jwks, kid)
        if public_key:
            log_okta_message(
                message="Key found after JWKS refresh",
                data={'kid': kid},
                level=SentryLogLevel.INFO,
            )
            return public_key

        # Key still not found even after refresh
        error_msg = (
            f'Key with kid={kid} not found even after JWKS refresh. '
            f'This may indicate: 1) Token from different Okta domain, '
            f'2) Key rotation in progress, 3) Wrong Authorization Server type'
        )
        available_kids = [k.get('kid') for k in fresh_jwks.get('keys', [])]
        log_okta_message(
            message=error_msg,
            data={
                'kid': kid,
                'available_kids': available_kids,
                'keys_count': len(fresh_jwks.get('keys', [])),
                'okta_domain': settings.OKTA_DOMAIN,
                'troubleshooting_hint': (
                    'Check if token is from correct Okta domain and '
                    'Authorization Server type (Org vs Default)'
                ),
            },
            level=SentryLogLevel.ERROR,
        )
        capture_sentry_message(
            message=error_msg,
            level=SentryLogLevel.ERROR,
            data={
                'kid': kid,
                'available_kids': available_kids,
                'okta_domain': settings.OKTA_DOMAIN,
                'jwks_endpoints_used': [
                    f'https://{settings.OKTA_DOMAIN}/oauth2/v1/keys',
                    f'https://{settings.OKTA_DOMAIN}/oauth2/default/v1/keys',
                ],
            },
        )
        return None

    def _extract_key_from_jwks(
        self,
        jwks: Dict[str, Any],
        kid: str,
    ) -> Optional[Any]:
        """
        Extract and convert public key from JWKS for given kid.

        Args:
            jwks: JWKS dictionary
            kid: Key ID to find

        Returns:
            Public key in PEM format or None if not found/conversion failed
        """
        # Find key with matching kid
        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                log_okta_message(
                    message="Found matching key in JWKS",
                    data={'kid': kid, 'kty': key.get('kty')},
                    level=SentryLogLevel.DEBUG,
                )

                # Try to use cryptography library for key conversion
                # This is the most reliable method
                try:
                    # Extract modulus and exponent from JWK
                    n_b64 = key['n']
                    e_b64 = key['e']

                    # Add padding if needed
                    n_padded = n_b64 + '=' * (4 - len(n_b64) % 4)
                    e_padded = e_b64 + '=' * (4 - len(e_b64) % 4)

                    n_bytes = base64.urlsafe_b64decode(n_padded)
                    e_bytes = base64.urlsafe_b64decode(e_padded)

                    # Convert to integers
                    n_int = int.from_bytes(n_bytes, 'big')
                    e_int = int.from_bytes(e_bytes, 'big')

                    # Create RSA public key
                    public_numbers = rsa.RSAPublicNumbers(e_int, n_int)
                    public_key_obj = public_numbers.public_key()

                    # Serialize to PEM format
                    pem = public_key_obj.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=(
                            serialization.PublicFormat.SubjectPublicKeyInfo
                        ),
                    )

                    log_okta_message(
                        message="Successfully converted JWK to PEM",
                        data={'kid': kid},
                        level=SentryLogLevel.DEBUG,
                    )
                    return pem.decode('utf-8')

                except ImportError:
                    # Fallback: try to use PyJWT's RSAAlgorithm if available
                    # This may work in newer versions of PyJWT
                    try:
                        if hasattr(RSAAlgorithm, 'from_jwk'):
                            log_okta_message(
                                message="Using PyJWT RSAAlgorithm fallback",
                                data={'kid': kid},
                                level=SentryLogLevel.DEBUG,
                            )
                            return RSAAlgorithm.from_jwk(key)
                    except (ImportError, AttributeError):
                        pass

                    error_msg = (
                        'cryptography library is required for JWT '
                        'verification. Please install it: '
                        'pip install cryptography'
                    )
                    log_okta_message(
                        message=error_msg,
                        data={'kid': kid},
                        level=SentryLogLevel.ERROR,
                    )
                    capture_sentry_message(
                        message=error_msg,
                        level=SentryLogLevel.ERROR,
                        data={'kid': kid},
                    )
                    return None
                except (KeyError, ValueError, TypeError) as ex:
                    error_msg = f'Failed to convert JWK to PEM: {ex!s}'
                    log_okta_message(
                        message=error_msg,
                        data={'kid': kid, 'key_fields': list(key.keys())},
                        level=SentryLogLevel.ERROR,
                    )
                    capture_sentry_message(
                        message=error_msg,
                        level=SentryLogLevel.ERROR,
                        data={'error': str(ex), 'kid': kid},
                    )
                    return None

        # Key not found in this JWKS
        return None

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

    def _logout_user(
        self,
        user: UserModel,
        okta_sub: Optional[str],
        session_id: Optional[str] = None,
    ):
        """
        Perform user logout:
        - Delete AccessToken for OKTA source
        - Clear token and profile cache
        - Terminate user sessions (all or specific session)

        Args:
            user: User to logout
            okta_sub: Okta subject identifier to clear from cache
            session_id: Optional session ID for session-specific logout
        """
        log_okta_message(
            message=f"Starting logout process for user {user.id}",
            data={
                'user_id': user.id,
                'user_email': user.email,
                'okta_sub': okta_sub,
                'session_id': session_id,
                'session_specific': bool(session_id),
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

        # Terminate sessions based on session_id presence
        if session_id:
            # TODO: Implement session-specific logout when session tracking
            # is available. For now, log the session_id and terminate all.
            log_okta_message(
                message=(
                    f"Session-specific logout requested for user {user.id}, "
                    f"but session tracking not implemented. "
                    f"Terminating all sessions."
                ),
                data={'user_id': user.id, 'session_id': session_id},
                level=SentryLogLevel.WARNING,
            )

        # Clear all tokens from cache (terminate all sessions)
        log_okta_message(
            message=f"Expiring all tokens for user {user.id}",
            data={
                'user_id': user.id,
                'session_specific_requested': bool(session_id),
            },
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
