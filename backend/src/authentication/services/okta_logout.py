import jwt
import requests
import base64
from urllib.parse import urlparse, urlunparse
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import caches
from typing import Optional, Dict, Any

from src.accounts.enums import UserStatus, SourceType
from src.authentication.models import AccessToken
from src.authentication.tokens import PneumaticToken
from src.utils.logging import SentryLogLevel, capture_sentry_message

UserModel = get_user_model()


class OktaLogoutService:
    """Service for handling Okta Back-Channel Logout operations."""

    SOURCE = SourceType.OKTA
    CACHE_KEY_PREFIX = 'okta_sub_to_user'
    JWKS_CACHE_KEY = 'okta_jwks'
    JWKS_CACHE_TIMEOUT = 3600

    def __init__(self, logout_token: Optional[str] = None):
        self.logout_token = logout_token
        self.cache = caches['default']

    def process_logout(self, **request_data):
        """Process Okta Back-Channel Logout request."""
        token_payload = self._validate_logout_token()
        if not token_payload:
            if not getattr(
                    settings,
                    'OKTA_LOGOUT_ALLOW_FALLBACK_ON_INVALID_TOKEN',
                    False,
            ):
                return
            token_payload = {}

        format_type = request_data.get('format')
        sub_id_data = request_data.get('sub_id_data', {})
        token_sub = token_payload.get('sub')

        if token_sub:
            is_client_id = self._is_client_id(token_sub)
            fallback_sub = (
                sub_id_data.get('sub') if format_type == 'iss_sub' else None
            )
            fallback_email = (
                sub_id_data.get('email') if format_type == 'email' else None
            )

            if is_client_id and fallback_email:
                self._process_logout_by_email(fallback_email)
            else:
                self._process_logout_by_sub(token_sub, fallback_sub)
        elif format_type == 'iss_sub':
            sub = sub_id_data.get('sub')
            if sub:
                self._process_logout_by_sub(sub)
            else:
                capture_sentry_message(
                    message="Missing 'sub' field in iss_sub format",
                    level=SentryLogLevel.ERROR,
                    data={'request_data': request_data},
                )
        elif format_type == 'email':
            email = sub_id_data.get('email')
            if email:
                self._process_logout_by_email(email)
            else:
                capture_sentry_message(
                    message="Missing 'email' field in email format",
                    level=SentryLogLevel.ERROR,
                    data={'request_data': request_data},
                )
        else:
            capture_sentry_message(
                message=f"Unsupported format: {format_type}",
                level=SentryLogLevel.ERROR,
                data={'request_data': request_data},
            )

    def _process_logout_by_sub(
        self,
        sub: str,
        fallback_sub: Optional[str] = None,
    ):
        """Process logout using sub identifier with fallback support."""
        try:
            user = self._get_user_by_sub(sub, fallback_sub=fallback_sub)
        except UserModel.DoesNotExist:
            capture_sentry_message(
                message='Okta logout: user not found by sub',
                level=SentryLogLevel.WARNING,
                data={'sub': sub, 'fallback_sub': fallback_sub},
            )
            return

        self._logout_user(user, okta_sub=sub)

    def _process_logout_by_email(self, email: str):
        """Process logout using email."""
        try:
            user = UserModel.objects.get(
                email__iexact=email,
                status=UserStatus.ACTIVE,
            )
        except UserModel.DoesNotExist:
            capture_sentry_message(
                message='Okta logout: user not found by email',
                level=SentryLogLevel.WARNING,
                data={'email': email},
            )
            return

        self._logout_user(user, okta_sub=None)

    def _validate_logout_token(self) -> Optional[Dict[str, Any]]:
        """Validate logout_token using JWT verification with Okta JWKS."""
        if not self.logout_token:
            return None

        try:
            unverified_header = jwt.get_unverified_header(self.logout_token)
            kid = unverified_header.get('kid')
            if not kid:
                capture_sentry_message(
                    message='Missing kid in logout token header',
                    level=SentryLogLevel.ERROR,
                    data={'header': unverified_header},
                )
                return None

            public_key = self._get_public_key_from_jwks(kid)
            if not public_key:
                capture_sentry_message(
                    message='Failed to get public key from JWKS',
                    level=SentryLogLevel.ERROR,
                    data={'kid': kid, 'okta_domain': settings.OKTA_DOMAIN},
                )
                return None

            expected_issuer = f'https://{settings.OKTA_DOMAIN}'
            audiences_to_try = self._get_possible_audiences()

            payload = None
            for aud in audiences_to_try:
                try:
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
                    break
                except jwt.InvalidAudienceError:
                    continue

            if payload is None:
                capture_sentry_message(
                    message='Invalid token audience',
                    level=SentryLogLevel.ERROR,
                    data={'audiences_tried': audiences_to_try},
                )
                return None

            if not self._validate_logout_token_claims(payload):
                return None

            return payload

        except (jwt.ExpiredSignatureError, jwt.InvalidIssuerError,
                jwt.InvalidAudienceError, jwt.DecodeError,
                jwt.InvalidTokenError, requests.RequestException,
                KeyError) as ex:
            capture_sentry_message(
                message=f'Okta logout token validation failed: {ex!s}',
                level=SentryLogLevel.ERROR,
                data={'error': str(ex)},
            )
            return None

    def _validate_logout_token_claims(self, payload: Dict[str, Any]) -> bool:
        """Validate logout token claims."""
        # Check required claims
        if not (payload.get('sub') or payload.get('sid')):
            capture_sentry_message(
                message='Token must contain either "sub" or "sid" claim',
                level=SentryLogLevel.ERROR,
            )
            return False

        if not payload.get('jti') or 'nonce' in payload:
            capture_sentry_message(
                message='Invalid token claims: missing jti or contains nonce',
                level=SentryLogLevel.ERROR,
            )
            return False

        # Check events claim for non-GTR tokens
        events = payload.get('events')
        if not events:
            token_header = jwt.get_unverified_header(self.logout_token)
            if 'global-token-revocation' not in token_header.get('typ', ''):
                capture_sentry_message(
                    message='Logout token must contain "events" claim',
                    level=SentryLogLevel.ERROR,
                )
                return False

        return True

    def _get_possible_audiences(self) -> list:
        """Get list of possible audiences to try for token validation."""
        audiences = []

        webhook_url = getattr(settings, 'OKTA_LOGOUT_WEBHOOK_URL', None)
        if webhook_url:
            audiences.append(webhook_url)

        backend_url = getattr(settings, 'BACKEND_URL', None)
        if backend_url:
            backend_url = backend_url.rstrip('/')
            parsed = urlparse(backend_url)

            audiences.append(f"{backend_url}/auth/okta/logout")

            if parsed.port:
                url_without_port = urlunparse((
                    parsed.scheme, parsed.hostname, parsed.path,
                    parsed.params, parsed.query, parsed.fragment,
                ))
                url_no_port = f"{url_without_port}/auth/okta/logout"
                if url_no_port not in audiences:
                    audiences.append(url_no_port)

        client_id = getattr(settings, 'OKTA_CLIENT_ID', None)
        if client_id and client_id not in audiences:
            audiences.append(client_id)

        return audiences

    def _get_jwks(
            self,
            force_refresh: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Get JWKS (JSON Web Key Set) from Okta."""
        if not force_refresh:
            cached_jwks = self.cache.get(self.JWKS_CACHE_KEY)
            if cached_jwks:
                return cached_jwks

        if (hasattr(settings, 'OKTA_LOGOUT_AUTH_SERVER_TYPE') and
                settings.OKTA_LOGOUT_AUTH_SERVER_TYPE == 'default'):
            jwks_endpoints = [
                f'https://{settings.OKTA_DOMAIN}/oauth2/default/v1/keys',
                f'https://{settings.OKTA_DOMAIN}/oauth2/v1/keys',
            ]
        else:
            jwks_endpoints = [
                f'https://{settings.OKTA_DOMAIN}/oauth2/v1/keys',
                f'https://{settings.OKTA_DOMAIN}/oauth2/default/v1/keys',
            ]

        for jwks_url in jwks_endpoints:
            try:
                response = requests.get(jwks_url, timeout=10)
                response.raise_for_status()
                jwks = response.json()
                self.cache.set(
                    self.JWKS_CACHE_KEY,
                    jwks,
                    timeout=self.JWKS_CACHE_TIMEOUT,
                )
                return jwks
            except requests.RequestException:
                continue

        capture_sentry_message(
            message='Failed to fetch JWKS from all endpoints',
            level=SentryLogLevel.ERROR,
            data={'endpoints_tried': jwks_endpoints},
        )
        return None

    def _get_public_key_from_jwks(self, kid: str) -> Optional[Any]:
        """Get public key from JWKS by kid (key ID)."""
        jwks = self._get_jwks(force_refresh=False)
        if not jwks:
            return None

        public_key = self._extract_key_from_jwks(jwks, kid)
        if public_key:
            return public_key

        # Try refresh if key not found
        fresh_jwks = self._get_jwks(force_refresh=True)
        if not fresh_jwks:
            return None

        public_key = self._extract_key_from_jwks(fresh_jwks, kid)
        if not public_key:
            available_kids = [k.get('kid') for k in fresh_jwks.get('keys', [])]
            capture_sentry_message(
                message=f'Key with kid={kid} not found after JWKS refresh',
                level=SentryLogLevel.ERROR,
                data={
                    'kid': kid,
                    'available_kids': available_kids,
                    'okta_domain': settings.OKTA_DOMAIN,
                },
            )

        return public_key

    def _extract_key_from_jwks(
        self,
        jwks: Dict[str, Any],
        kid: str,
    ) -> Optional[Any]:
        """Extract and convert public key from JWKS for given kid."""
        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                try:
                    n_b64 = key['n']
                    e_b64 = key['e']

                    n_padded = n_b64 + '=' * (4 - len(n_b64) % 4)
                    e_padded = e_b64 + '=' * (4 - len(e_b64) % 4)

                    n_bytes = base64.urlsafe_b64decode(n_padded)
                    e_bytes = base64.urlsafe_b64decode(e_padded)

                    n_int = int.from_bytes(n_bytes, 'big')
                    e_int = int.from_bytes(e_bytes, 'big')

                    public_numbers = rsa.RSAPublicNumbers(e_int, n_int)
                    public_key_obj = public_numbers.public_key()

                    pem = public_key_obj.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=(
                            serialization.PublicFormat.SubjectPublicKeyInfo
                        ),
                    )
                    return pem.decode('utf-8')

                except (KeyError, ValueError, TypeError) as ex:
                    capture_sentry_message(
                        message=f'Failed to convert JWK to PEM: {ex!s}',
                        level=SentryLogLevel.ERROR,
                        data={'error': str(ex), 'kid': kid},
                    )
                    return None

        return None

    def _is_client_id(self, okta_sub: str) -> bool:
        """Check if Okta sub identifier is a client_id."""
        if okta_sub.startswith('0o'):
            return True
        client_id = getattr(settings, 'OKTA_CLIENT_ID', None)
        return client_id and okta_sub == client_id

    def _get_user_by_sub(
        self,
        okta_sub: str,
        fallback_sub: Optional[str] = None,
    ) -> UserModel:
        """Get user by cached Okta sub identifier with fallback support."""
        if (
                self._is_client_id(okta_sub)
                and fallback_sub
                and fallback_sub != okta_sub
        ):
            try:
                return self._lookup_user_by_single_sub(fallback_sub)
            except UserModel.DoesNotExist as err:
                raise UserModel.DoesNotExist(
                    f"User not found for fallback_sub: {fallback_sub}",
                ) from err

        # Try primary sub
        try:
            return self._lookup_user_by_single_sub(okta_sub)
        except UserModel.DoesNotExist:
            if fallback_sub and fallback_sub != okta_sub:
                try:
                    return self._lookup_user_by_single_sub(fallback_sub)
                except UserModel.DoesNotExist:
                    pass

            raise UserModel.DoesNotExist(
                f"User not found for okta_sub: {okta_sub}",
            ) from None

    def _lookup_user_by_single_sub(self, okta_sub: str) -> UserModel:
        """Lookup user by single sub identifier in cache."""
        cache_key = f'{self.CACHE_KEY_PREFIX}_{okta_sub}'
        user_id = self.cache.get(cache_key)

        if not user_id:
            raise UserModel.DoesNotExist(
                f"User not found for okta_sub: {okta_sub}",
            )

        try:
            return UserModel.objects.get(id=user_id)
        except UserModel.DoesNotExist:
            self.cache.delete(cache_key)
            raise

    def _logout_user(
        self,
        user: UserModel,
        okta_sub: Optional[str],
    ):
        """Perform user logout."""
        # Get access tokens before deletion for profile cache cleanup
        access_tokens = list(
            AccessToken.objects.filter(
                user=user,
                source=self.SOURCE,
            ).values_list('access_token', flat=True),
        )

        # Delete access tokens
        AccessToken.objects.filter(
            user=user,
            source=self.SOURCE,
        ).delete()

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
