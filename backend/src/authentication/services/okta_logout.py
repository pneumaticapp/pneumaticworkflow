import jwt
import requests
import base64
from typing import Dict, Any, List, Union
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.core.exceptions import ObjectDoesNotExist
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.backends import default_backend

from src.accounts.enums import UserStatus, SourceType
from src.authentication.enums import (
    OktaLogoutFormat,
    OktaIssSubData,
    OktaEmailSubData,
)
from src.authentication.models import AccessToken
from src.authentication.tokens import PneumaticToken
from src.utils.logging import SentryLogLevel, capture_sentry_message

UserModel = get_user_model()


class OktaLogoutService:
    """Service for handling Okta Back-Channel Logout operations."""

    SOURCE = SourceType.OKTA
    CACHE_KEY_PREFIX = 'okta_sub_to_user'

    def __init__(self):
        self.cache = caches['default']

    def _get_valid_user_sub(self, token: str) -> str:
        """Get valid user sub from logout token."""

        try:
            header = jwt.get_unverified_header(token)
        except (jwt.PyJWTError, ValueError, KeyError, TypeError) as ex:
            capture_sentry_message(
                message=f"Failed to get JWT header: {ex!s}",
                level=SentryLogLevel.ERROR,
                data={'error': str(ex)},
            )
            raise

        kid = header.get('kid')
        if not kid:
            capture_sentry_message(
                message="JWT header missing 'kid' field",
                level=SentryLogLevel.ERROR,
            )
            raise ValueError("JWT header missing 'kid' field")

        key_pem = self._get_public_key_pem(kid)

        try:
            payload = jwt.decode(
                token,
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
        except (jwt.PyJWTError, ValueError, KeyError, TypeError) as ex:
            capture_sentry_message(
                message=f"JWT token validation failed: {ex!s}",
                level=SentryLogLevel.ERROR,
                data={'error': str(ex)},
            )
            raise

        sub = payload.get('sub')
        if not sub:
            capture_sentry_message(
                message="JWT payload missing 'sub' field",
                level=SentryLogLevel.ERROR,
            )
            raise ValueError("JWT payload missing 'sub' field")

        return sub

    def _get_public_key_pem(self, kid: str) -> str:
        """Get PEM public key from JWKS."""

        jwks = self._get_jwks()

        for key_data in jwks.get('keys', []):
            if key_data.get('kid') == kid:
                return self._get_jwk_as_pem(key_data)

        capture_sentry_message(
            message=f'Key with kid={kid} not found',
            level=SentryLogLevel.ERROR,
        )
        raise ValueError(f'Key with kid={kid} not found')

    def _get_jwks(self) -> Dict[str, Any]:
        """Fetch JWKS from Okta."""

        try:
            response = requests.get(
                f'https://{settings.OKTA_DOMAIN}/oauth2/v1/keys',
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as ex:
            capture_sentry_message(
                message=f'Failed to fetch JWKS: {ex!s}',
                level=SentryLogLevel.ERROR,
                data={'error': str(ex)},
            )
            raise

    def _get_jwk_as_pem(self, key_data: Dict[str, str]) -> str:
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
        except (KeyError, ValueError, TypeError) as ex:
            capture_sentry_message(
                message=f'Failed to convert JWK to PEM: {ex!s}',
                level=SentryLogLevel.ERROR,
                data={'key_data': key_data, 'error': str(ex)},
            )
            raise

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

    def _get_user_by_format(
        self,
        logout_format: OktaLogoutFormat.LITERALS,
        data: Union[OktaIssSubData, OktaEmailSubData],
    ) -> UserModel:
        """Get user by format and data."""

        if logout_format == OktaLogoutFormat.ISS_SUB:
            sub = data['sub']
            return self._get_user_by_cached_sub(sub)

        if logout_format == OktaLogoutFormat.EMAIL:
            email = data['email']
            return self._get_user_by_email(email)

        capture_sentry_message(
            message=f"Unsupported format: {logout_format}",
            level=SentryLogLevel.ERROR,
        )
        raise ValueError(f"Unsupported format: {logout_format}")

    def _get_user_by_cached_sub(self, sub: str) -> UserModel:
        """Get user by cached sub."""

        cache_key = f'{self.CACHE_KEY_PREFIX}_{sub}'
        user_id = self.cache.get(cache_key)

        if not user_id:
            capture_sentry_message(
                message=f'User not found by sub: {sub}',
                level=SentryLogLevel.WARNING,
            )
            raise ObjectDoesNotExist(f'User not found by sub: {sub}')

        try:
            return UserModel.objects.get(
                id=user_id,
                status=UserStatus.ACTIVE,
            )
        except ObjectDoesNotExist as ex:
            capture_sentry_message(
                message=f'Cached user not found: {user_id}',
                level=SentryLogLevel.WARNING,
            )
            self.cache.delete(cache_key)
            raise ObjectDoesNotExist(f'User not found by sub: {sub}') from ex

    def _get_user_by_email(self, email: str) -> UserModel:
        """Get user by email."""

        try:
            return UserModel.objects.get(
                email__iexact=email,
                status=UserStatus.ACTIVE,
            )
        except ObjectDoesNotExist:
            capture_sentry_message(
                message=f'User not found by email: {email}',
                level=SentryLogLevel.WARNING,
            )
            raise

    def _logout_user(self, user: UserModel, sub: str):
        """Perform logout: delete tokens, clear cache."""

        tokens = AccessToken.objects.filter(user=user, source=self.SOURCE)
        token_strings = list(tokens.values_list('access_token', flat=True))
        tokens.delete()

        for ts in token_strings:
            self.cache.delete(f'user_profile_{ts}')

        self.cache.delete(f'{self.CACHE_KEY_PREFIX}_{sub}')
        PneumaticToken.expire_all_tokens(user)

    def process_logout(
        self,
        token: str,
        logout_format: OktaLogoutFormat.LITERALS,
        data: Union[OktaIssSubData, OktaEmailSubData],
    ):
        """Process Okta Back-Channel Logout request."""

        sub = self._get_valid_user_sub(token)
        user = self._get_user_by_format(logout_format=logout_format, data=data)
        self._logout_user(user=user, sub=sub)
