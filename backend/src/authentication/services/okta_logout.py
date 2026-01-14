import jwt
import requests
import base64
from typing import Optional, Dict, Any, List
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import caches
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.backends import default_backend

from src.accounts.enums import UserStatus, SourceType
from src.authentication.models import AccessToken
from src.authentication.tokens import PneumaticToken
from src.utils.logging import SentryLogLevel, capture_sentry_message

UserModel = get_user_model()


class OktaLogoutService:
    """Service for handling Okta Back-Channel Logout operations."""

    SOURCE = SourceType.OKTA
    CACHE_KEY_PREFIX = 'okta_sub_to_user'

    def __init__(self, logout_token: Optional[str] = None):
        self.logout_token = logout_token
        self.cache = caches['default']

    def process_logout(self, **request_data: Any) -> None:
        """Process Okta Back-Channel Logout request."""

        payload = self._validate_logout_token()

        if not payload:
            return

        user = self._identify_user(
            format_type=request_data.get('format'),
            sub_id_data=request_data.get('sub_id_data', {}),
        )
        if user:
            self._logout_user(user, payload.get('sub'))

    def _validate_logout_token(self) -> Optional[Dict[str, Any]]:
        """Validate logout_token using JWT with Okta JWKS."""

        try:
            header = jwt.get_unverified_header(self.logout_token)
            kid = header.get('kid')
            if not kid:
                return None

            key_pem = self._get_public_key_pem(kid)
            if not key_pem:
                return None

            return jwt.decode(
                self.logout_token,
                key_pem,
                algorithms=['RS256'],
                audience=self._get_possible_audiences(),
                issuer=f'https://{settings.OKTA_DOMAIN}',
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_iss': True,
                    'verify_aud': True,
                },
            )
        except (
                jwt.PyJWTError,
                ValueError,
                KeyError,
                TypeError,
                requests.RequestException,
        ) as e:
            capture_sentry_message(
                message=f"Okta logout token validation failed: {e!s}",
                level=SentryLogLevel.ERROR,
                data={'error': str(e)},
            )
            return None

    def _get_public_key_pem(self, kid: str) -> Optional[str]:
        """Get PEM public key from JWKS."""

        jwks = self._get_jwks()
        if not jwks:
            return None

        for key_data in jwks.get('keys', []):
            if key_data.get('kid') == kid:
                return self._jwk_to_pem(key_data)

        capture_sentry_message(
            message=f'Key with kid={kid} not found',
            level=SentryLogLevel.ERROR,
        )
        return None

    def _get_jwks(self) -> Optional[Dict[str, Any]]:
        """Fetch JWKS from Okta."""

        try:
            response = requests.get(
                f'https://{settings.OKTA_DOMAIN}/oauth2/v1/keys',
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            capture_sentry_message(
                message='Failed to fetch JWKS',
                level=SentryLogLevel.ERROR,
            )
            return None

    def _jwk_to_pem(self, key_data: Dict[str, str]) -> Optional[str]:
        """Convert JWK to PEM format."""
        try:
            def decode_base64(val: str) -> int:
                padded = val + '=' * (4 - len(val) % 4)
                return int.from_bytes(base64.urlsafe_b64decode(padded), 'big')

            public_numbers = RSAPublicNumbers(
                n=decode_base64(key_data['n']),
                e=decode_base64(key_data['e']),
            )
            public_key = public_numbers.public_key(default_backend())
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            return pem.decode('utf-8')
        except (KeyError, ValueError, TypeError) as e:
            capture_sentry_message(
                message=f'Failed to convert JWK to PEM: {e!s}',
                level=SentryLogLevel.ERROR,
                data={'key_data': key_data},
            )
            return None

    def _get_possible_audiences(self) -> List[str]:
        """Get list of possible audiences."""
        audiences = []
        client_id = getattr(settings, 'OKTA_CLIENT_ID', None)
        frontend_url = getattr(settings, 'FRONTEND_URL', None)

        if client_id:
            audiences.append(client_id)
        if frontend_url:
            audiences.append(f"{frontend_url}/auth/okta/logout")
        return audiences

    def _identify_user(
        self,
        format_type: Optional[str],
        sub_id_data: Dict[str, Any],
    ) -> Optional[UserModel]:
        """Identify user by token sub or request data."""

        if format_type == 'iss_sub':
            sub = sub_id_data.get('sub')
            if sub:
                return self._get_user_by_cached_sub(sub)
        if format_type == 'email':
            email = sub_id_data.get('email')
            if email:
                return UserModel.objects.filter(
                    email__iexact=email,
                    status=UserStatus.ACTIVE,
                ).first()

        capture_sentry_message(
            message=f"User identification failed. Format: {format_type}",
            level=SentryLogLevel.WARNING,
        )
        return None

    def _get_user_by_cached_sub(self, sub: str) -> Optional[UserModel]:
        """Get user by cached sub."""

        cache_key = f'{self.CACHE_KEY_PREFIX}_{sub}'
        user_id = self.cache.get(cache_key)
        if user_id:
            user = UserModel.objects.filter(
                id=user_id,
                status=UserStatus.ACTIVE,
            ).first()
            if user:
                return user
            self.cache.delete(cache_key)
        capture_sentry_message(
            message=f'User not found by sub: {sub}',
            level=SentryLogLevel.WARNING,
        )
        return None

    def _logout_user(self, user: UserModel, okta_sub: Optional[str]) -> None:
        """Perform logout: delete tokens, clear cache."""

        tokens = AccessToken.objects.filter(user=user, source=self.SOURCE)
        token_strings = list(tokens.values_list('access_token', flat=True))
        tokens.delete()

        for ts in token_strings:
            self.cache.delete(f'user_profile_{ts}')

        if okta_sub:
            self.cache.delete(f'{self.CACHE_KEY_PREFIX}_{okta_sub}')

        PneumaticToken.expire_all_tokens(user)
