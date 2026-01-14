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
    SOURCE = SourceType.OKTA
    CACHE_KEY_PREFIX = 'okta_sub_to_user'

    def __init__(self, logout_token: Optional[str] = None):
        self.logout_token = logout_token
        self.cache = caches['default']

    def process_logout(self, **request_data: Any) -> None:
        payload = self._validate_logout_token()

        if not payload:
            return

        user = self._identify_user(request_data)
        if user:
            self._do_logout(user, payload.get('sub'))

    def _validate_logout_token(self) -> Optional[Dict[str, Any]]:
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
            )
        except (jwt.PyJWTError, ValueError, KeyError) as e:
            capture_sentry_message(
                message=f"Okta logout token validation failed: {e!s}",
                level=SentryLogLevel.ERROR,
            )
            return None

    def _get_public_key_pem(self, kid: str) -> Optional[str]:
        url = f'https://{settings.OKTA_DOMAIN}/oauth2/v1/keys'
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            jwks = response.json()
        except (requests.RequestException, ValueError):
            return None

        for key_data in jwks.get('keys', []):
            if key_data.get('kid') == kid:
                return self._jwk_to_pem(key_data)
        return None

    def _jwk_to_pem(self, key_data: Dict[str, str]) -> str:
        def decode_value(val: str):
            rem = len(val) % 4
            if rem > 0:
                val += '=' * (4 - rem)
            return int.from_bytes(base64.urlsafe_b64decode(val), 'big')

        public_numbers = RSAPublicNumbers(
            n=decode_value(key_data['n']),
            e=decode_value(key_data['e']),
        )
        public_key = public_numbers.public_key(default_backend())
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return pem.decode('utf-8')

    def _get_possible_audiences(self) -> List[str]:
        auds = []
        client_id = getattr(settings, 'OKTA_CLIENT_ID', None)
        webhook = getattr(settings, 'OKTA_LOGOUT_WEBHOOK_URL', None)
        if client_id:
            auds.append(client_id)
        if webhook:
            auds.append(webhook)
        return auds

    def _identify_user(
            self,
            request_data: Dict[str, Any],
    ) -> Optional[UserModel]:
        format_type = request_data.get('format')
        sub_id_data = request_data.get('sub_id_data', {})

        target_sub = (
            sub_id_data.get('sub') if format_type == 'iss_sub' else None
        )
        if target_sub:
            user = self._get_user_by_cached_sub(target_sub)
            if user:
                return user

        email = sub_id_data.get('email') if format_type == 'email' else None
        if email:
            return UserModel.objects.filter(
                email__iexact=email,
                status=UserStatus.ACTIVE,
            ).first()
        return None

    def _get_user_by_cached_sub(self, sub: str) -> Optional[UserModel]:
        cache_key = f'{self.CACHE_KEY_PREFIX}_{sub}'
        user_id = self.cache.get(cache_key)
        if user_id:
            return UserModel.objects.filter(id=user_id).first()
        return None

    def _do_logout(self, user: UserModel, okta_sub: Optional[str]) -> None:
        tokens = AccessToken.objects.filter(user=user, source=self.SOURCE)
        token_strings = list(tokens.values_list('access_token', flat=True))
        tokens.delete()

        for ts in token_strings:
            self.cache.delete(f'user_profile_{ts}')

        if okta_sub:
            cache_key = f'{self.CACHE_KEY_PREFIX}_{okta_sub}'
            self.cache.delete(cache_key)
        PneumaticToken.expire_all_tokens(user)
