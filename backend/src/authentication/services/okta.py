from base64 import urlsafe_b64decode
from typing import Optional, Tuple
from uuid import uuid4

import jwt
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import caches
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from src.accounts.enums import SourceType
from src.authentication.entities import UserData, SSOConfigData
from src.authentication.enums import (
    SSOProvider,
)
from src.authentication.messages import MSG_AU_0018
from src.authentication.models import (
    AccessToken,
    SSOConfig,
)
from src.authentication.services import exceptions
from src.authentication.services.base_sso import BaseSSOService
from src.authentication.tokens import PneumaticToken
from src.logs.service import AccountLogService
from src.utils.logging import (
    SentryLogLevel,
    capture_sentry_message,
)

UserModel = get_user_model()


class OktaService(BaseSSOService):

    cache_key_prefix = 'okta_flow'
    cache_timeout = 600  # 10 min
    source = SourceType.OKTA
    sso_provider = SSOProvider.OKTA
    exception_class = exceptions.OktaServiceException

    def __init__(
        self,
        domain: Optional[str] = None,
    ):
        super().__init__(domain)
        self.scope = 'openid email profile'

    def _get_config_by_domain(self, domain: str) -> SSOConfigData:
        try:
            sso_config = SSOConfig.objects.get(
                domain=domain,
                provider=self.sso_provider,
                is_active=True,
            )
            return SSOConfigData(
                client_id=sso_config.client_id,
                client_secret=sso_config.client_secret,
                domain=sso_config.domain,
                redirect_uri=settings.OKTA_REDIRECT_URI,
            )
        except SSOConfig.DoesNotExist as exc:
            capture_sentry_message(
                message=str(MSG_AU_0018(domain)),
                level=SentryLogLevel.ERROR,
            )
            raise self.exception_class(MSG_AU_0018(domain)) from exc

    def _get_default_config(self) -> Optional[SSOConfigData]:
        if not settings.OKTA_CLIENT_SECRET:
            return None
        return SSOConfigData(
            client_id=settings.OKTA_CLIENT_ID,
            client_secret=settings.OKTA_CLIENT_SECRET,
            domain=settings.OKTA_DOMAIN,
            redirect_uri=settings.OKTA_REDIRECT_URI,
        )

    def _get_first_access_token(self, code: str, state: str) -> str:
        """
        Gets access token during initial authorization

        Example successful response:
        {
            "token_type": "Bearer",
            "expires_in": 3600,
            "access_token": "eyJraWQiOiJYa2pXdjMzTDRBYU1ZSzNGM...",
            "scope": "openid email profile",
            "id_token": "eyJraWQiOiJYa2pXdjMzTDRBYU1ZSzNGM..."
        }

        Example error:
        {
            "error": "invalid_grant",
            "error_description": "Authorization code invalid or has expired."
        }
        """

        code_verifier = self._get_cache(key=state)
        if not code_verifier:
            raise exceptions.TokenInvalidOrExpired
        try:
            response = requests.post(
                f'https://{self.config.domain}/oauth2/default/v1/token',
                data={
                    'grant_type': 'authorization_code',
                    'client_id': self.config.client_id,
                    'client_secret': self.config.client_secret,
                    'code': code,
                    'redirect_uri': self.config.redirect_uri,
                    'code_verifier': code_verifier,
                },
                timeout=10,
            )
        except requests.RequestException as ex:
            capture_sentry_message(
                message=f'Get Okta access token return an error: {ex}',
                level=SentryLogLevel.ERROR,
            )
            raise exceptions.TokenInvalidOrExpired from ex
        if not response.ok:
            capture_sentry_message(
                message='Get Okta access token failed',
                data={
                    'status_code': response.status_code,
                    'response': response.text,
                },
                level=SentryLogLevel.ERROR,
            )
            raise exceptions.TokenInvalidOrExpired
        self.tokens = response.json()
        return self.tokens['access_token']

    def _get_user_profile(self, access_token: str) -> dict:
        """
        Response example:
        {
            "sub": "00uid4BxXw6I6TV4m0g3",
            "name": "John Doe",
            "locale": "en-US",
            "email": "john.doe@example.com",
            "preferred_username": "john.doe@example.com",
            "given_name": "John",
            "family_name": "Doe",
            "zoneinfo": "America/Los_Angeles",
            "updated_at": 1311280970,
            "email_verified": true
        }
        """

        cache_key = f'user_profile_{access_token}'
        cached_profile = self._get_cache(key=cache_key)
        if cached_profile:
            return cached_profile

        url = f'https://{self.config.domain}/oauth2/default/v1/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}
        try:
            response = requests.get(url, headers=headers, timeout=10)
        except requests.RequestException as ex:
            capture_sentry_message(
                message=f'Okta user profile request failed: {ex}',
                level=SentryLogLevel.ERROR,
            )
            raise exceptions.TokenInvalidOrExpired from ex
        if not response.ok:
            capture_sentry_message(
                message='Okta user profile request failed',
                data={
                    'status_code': response.status_code,
                    'response': response.text,
                },
                level=SentryLogLevel.ERROR,
            )
            raise exceptions.TokenInvalidOrExpired
        profile = response.json()
        self._set_cache(value=profile, key=cache_key)
        return profile

    def get_auth_uri(self) -> str:
        state = str(uuid4())
        encrypted_domain = self.encrypt(self.config.domain)
        state = f"{state}{encrypted_domain}"
        code_verifier, code_challenge = self._generate_pkce()
        self._set_cache(value=code_verifier, key=state)
        query_params = {
            'client_id': self.config.client_id,
            'redirect_uri': self.config.redirect_uri,
            'scope': self.scope,
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'response_type': 'code',
            'response_mode': 'query',
        }

        query = requests.compat.urlencode(query_params)
        return (
            f'https://{self.config.domain}/oauth2/default/v1/authorize?{query}'
        )

    def get_user_data(self, user_profile: dict) -> UserData:
        """Retrieve user details during signin / signup process"""
        email = user_profile.get('email')
        if not email:
            raise exceptions.EmailNotExist(
                details={'user_profile': user_profile},
            )
        first_name = (
            user_profile.get('given_name') or
            email.split('@')[0]
        )
        last_name = user_profile.get('family_name', '')

        capture_sentry_message(
            message=f'Okta user profile {email}',
            data={
                'first_name': first_name,
                'last_name': last_name,
                'user_profile': user_profile,
                'email': email,
            },
            level=SentryLogLevel.INFO,
        )

        return UserData(
            email=email.lower(),
            first_name=first_name,
            last_name=last_name,
        )

    def save_tokens_for_user(self, user: UserModel):
        """Save tokens and cache sub -> user mapping for GTR"""
        # Save access token as usual
        AccessToken.objects.update_or_create(
            source=self.source,
            user=user,
            defaults={
                'expires_in': self.tokens['expires_in'],
                'refresh_token': '',
                'access_token': self.tokens['access_token'],
            },
        )
        # Extract okta_sub from ID token and cache sub -> user mapping
        id_token = self.tokens.get('id_token')
        if id_token:
            try:
                # Decode ID token without verification to get sub
                id_payload = (
                    jwt.decode(id_token, options={"verify_signature": False})
                )
                okta_sub = id_payload.get('sub')
                if okta_sub:
                    self._cache_user_by_sub(okta_sub, user)
            except (jwt.DecodeError, jwt.InvalidTokenError, KeyError):
                pass

    def authenticate_user(
        self,
        code: str,
        state: str,
        user_agent: Optional[str] = None,
        user_ip: Optional[str] = None,
        **kwargs,
    ) -> Tuple[UserModel, PneumaticToken]:
        """Authenticate user via Okta and auto-create user if needed"""
        access_token = self._get_first_access_token(code, state)
        user_profile = self._get_user_profile(access_token)
        user_data = self.get_user_data(user_profile)
        return self._complete_authentication(
            user_data,
            user_agent=user_agent,
            user_ip=user_ip,
        )

    def process_logout(self, logout_token: str):
        """
        Process OIDC Back-Channel Logout request from Okta.

        According to OIDC specification:
        - Validates JWT signature, issuer
        - Uses sub (subject identifier) to find user
        - Performs user logout

        Args:
            logout_token: JWT token from Okta
        """
        AccountLogService().send_ws_message(
            account_id=1,
            data={
                'action': 'process_logout_start',
                'logout_token_length': (
                    len(logout_token) if logout_token else 0
                ),
                'has_logout_token': bool(logout_token),
            },
            group_name='okta_logout',
        )
        payload = self._decode_and_verify_logout_token(logout_token)
        if not payload:
            AccountLogService().send_ws_message(
                account_id=1,
                data={
                    'action': 'process_logout_token_validation_failed',
                    'logout_token_length': (
                        len(logout_token) if logout_token else 0
                    ),
                },
                group_name='okta_logout',
            )
            return
        AccountLogService().send_ws_message(
            account_id=1,
            data={
                'action': 'process_logout_token_validated',
                'payload_keys': list(payload.keys()) if payload else [],
                'has_sub': 'sub' in payload if payload else False,
            },
            group_name='okta_logout',
        )
        sub = payload.get('sub')
        if not sub:
            AccountLogService().send_ws_message(
                account_id=1,
                data={
                    'action': 'process_logout_no_sub',
                    'payload': payload,
                },
                group_name='okta_logout',
            )
            return
        AccountLogService().send_ws_message(
            account_id=1,
            data={
                'action': 'process_logout_sub_found',
                'sub': sub,
            },
            group_name='okta_logout',
        )
        user = self._find_user_by_okta_sub(sub)
        if not user:
            AccountLogService().send_ws_message(
                account_id=1,
                data={
                    'action': 'process_logout_user_not_found',
                    'sub': sub,
                },
                group_name='okta_logout',
            )
            return
        AccountLogService().send_ws_message(
            account_id=1,
            data={
                'action': 'process_logout_user_found',
                'sub': sub,
                'user_id': user.id,
                'user_email': user.email,
                'account_id': user.account_id,
            },
            group_name='okta_logout',
        )
        self._logout_user(user, okta_sub=sub)
        AccountLogService().send_ws_message(
            account_id=1,
            data={
                'action': 'process_logout_completed',
                'sub': sub,
                'user_id': user.id,
                'user_email': user.email,
            },
            group_name='okta_logout',
        )

    def _decode_and_verify_logout_token(self, token: str) -> Optional[dict]:
        """
        Decode and verify OIDC Back-Channel Logout Token.

        Validates according to OIDC specification:
        - JWT signature via JWKS
        - Issuer (must be Okta domain)
        - Token expiration

        Args:
            token: JWT logout token

        Returns:
            Optional[dict]: Validated payload or None on error
        """
        AccountLogService().send_ws_message(
            account_id=1,
            data={
                'action': 'decode_logout_token_start',
                'token_length': len(token) if token else 0,
                'domain': self.config.domain,
            },
            group_name='okta_logout',
        )
        jwks = self._get_cached_jwks()
        if not jwks:
            AccountLogService().send_ws_message(
                account_id=1,
                data={
                    'action': 'decode_logout_token_jwks_failed',
                    'domain': self.config.domain,
                },
                group_name='okta_logout',
            )
            return None
        AccountLogService().send_ws_message(
            account_id=1,
            data={
                'action': 'decode_logout_token_jwks_success',
                'jwks_keys_count': len(jwks.get('keys', [])),
            },
            group_name='okta_logout',
        )
        try:
            header = jwt.get_unverified_header(token)
        except jwt.DecodeError as e:
            AccountLogService().send_ws_message(
                account_id=1,
                data={
                    'action': 'decode_logout_token_header_error',
                    'error': str(e),
                },
                group_name='okta_logout',
            )
            return None
        AccountLogService().send_ws_message(
            account_id=1,
            data={
                'action': 'decode_logout_token_header_parsed',
                'header': header,
            },
            group_name='okta_logout',
        )
        kid = header.get('kid')
        if not kid:
            AccountLogService().send_ws_message(
                account_id=1,
                data={
                    'action': 'decode_logout_token_no_kid',
                    'header': header,
                },
                group_name='okta_logout',
            )
            return None
        AccountLogService().send_ws_message(
            account_id=1,
            data={
                'action': 'decode_logout_token_kid_found',
                'kid': kid,
            },
            group_name='okta_logout',
        )
        public_key = self._get_public_key_from_jwks(jwks, kid)
        if not public_key:
            AccountLogService().send_ws_message(
                account_id=1,
                data={
                    'action': 'decode_logout_token_public_key_failed',
                    'kid': kid,
                    'available_kids': [
                        key.get('kid') for key in jwks.get('keys', [])
                    ],
                },
                group_name='okta_logout',
            )
            return None
        AccountLogService().send_ws_message(
            account_id=1,
            data={
                'action': 'decode_logout_token_public_key_success',
                'kid': kid,
            },
            group_name='okta_logout',
        )
        try:
            payload = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                issuer=f'https://{self.config.domain}',
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_iss': True,
                    'verify_aud': False,
                },
            )
            AccountLogService().send_ws_message(
                account_id=1,
                data={
                    'action': 'decode_logout_token_success',
                    'payload_keys': list(payload.keys()),
                    'sub': payload.get('sub'),
                    'iss': payload.get('iss'),
                    'exp': payload.get('exp'),
                },
                group_name='okta_logout',
            )
            return payload
        except jwt.InvalidTokenError as e:
            AccountLogService().send_ws_message(
                account_id=1,
                data={
                    'action': 'decode_logout_token_validation_error',
                    'error': str(e),
                    'error_type': type(e).__name__,
                },
                group_name='okta_logout',
            )
            return None

    def _get_cached_jwks(self) -> Optional[dict]:
        """
        Get JWKS with caching for performance.

        Returns:
            Optional[dict]: JWKS from Okta or None on error
        """
        cache = caches['default']
        cache_key = f'okta_jwks_{self.config.domain}'
        jwks = cache.get(cache_key)
        if jwks:
            return jwks
        jwks_url = f'https://{self.config.domain}/oauth2/default/v1/keys'
        try:
            response = requests.get(jwks_url, timeout=10)
            response.raise_for_status()
            jwks = response.json()
            cache.set(cache_key, jwks, timeout=3600)
            return jwks
        except requests.RequestException:
            return None

    def _get_public_key_from_jwks(self, jwks: dict, kid: str) -> Optional[str]:
        """
        Extract public key from JWKS by kid.

        Args:
            jwks: JWKS from Okta
            kid: Key ID from JWT header

        Returns:
            Optional[str]: PEM-encoded public key or None
        """
        for key_data in jwks.get('keys', []):
            if key_data.get('kid') == kid and key_data.get('kty') == 'RSA':
                try:
                    return self._jwk_to_pem(key_data)
                except (ValueError, KeyError, TypeError):
                    pass
        return None

    def _jwk_to_pem(self, jwk_data: dict) -> str:
        """
        Convert JWK to PEM format.

        Args:
            jwk_data: JWK key data

        Returns:
            str: PEM-encoded public key
        """

        # Decode n and e from JWK
        n = int.from_bytes(
            urlsafe_b64decode(jwk_data['n'] + '=='),
            byteorder='big',
        )
        e = int.from_bytes(
            urlsafe_b64decode(jwk_data['e'] + '=='),
            byteorder='big',
        )

        # Create RSA public key
        public_key = rsa.RSAPublicNumbers(e, n).public_key()

        # Convert to PEM
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return pem.decode('utf-8')

    def _find_user_by_okta_sub(self, okta_sub: str) -> Optional[UserModel]:
        """
        Find user by Okta subject identifier via cache.

        Args:
            okta_sub: Okta subject identifier

        Returns:
            Optional[UserModel]: Found user or None
        """
        AccountLogService().send_ws_message(
            account_id=1,
            data={
                'action': 'find_user_by_sub_start',
                'okta_sub': okta_sub,
            },
            group_name='okta_logout',
        )
        # Search in cache
        user_id = self._get_cached_user_by_sub(okta_sub)
        if user_id:
            AccountLogService().send_ws_message(
                account_id=1,
                data={
                    'action': 'find_user_by_sub_cache_hit',
                    'okta_sub': okta_sub,
                    'user_id': user_id,
                },
                group_name='okta_logout',
            )
            try:
                user = UserModel.objects.get(id=user_id)
                AccountLogService().send_ws_message(
                    account_id=1,
                    data={
                        'action': 'find_user_by_sub_db_success',
                        'okta_sub': okta_sub,
                        'user_id': user.id,
                        'user_email': user.email,
                        'account_id': user.account_id,
                    },
                    group_name='okta_logout',
                )
                return user
            except UserModel.DoesNotExist:
                AccountLogService().send_ws_message(
                    account_id=1,
                    data={
                        'action': 'find_user_by_sub_db_not_found',
                        'okta_sub': okta_sub,
                        'user_id': user_id,
                        'cache_cleared': True,
                    },
                    group_name='okta_logout',
                )
                self._clear_cached_user_by_sub(okta_sub)
        else:
            AccountLogService().send_ws_message(
                account_id=1,
                data={
                    'action': 'find_user_by_sub_cache_miss',
                    'okta_sub': okta_sub,
                },
                group_name='okta_logout',
            )
        AccountLogService().send_ws_message(
            account_id=1,
            data={
                'action': 'find_user_by_sub_not_found',
                'okta_sub': okta_sub,
            },
            group_name='okta_logout',
        )
        return None

    def _cache_user_by_sub(self, okta_sub: str, user: UserModel):
        """
        Cache okta_sub -> user_id mapping.

        Args:
            okta_sub: Okta subject identifier
            user: User instance
        """
        cache = caches['default']
        cache_key = f'okta_sub_to_user_{okta_sub}'
        cache.set(cache_key, user.id, timeout=2592000)

    def _get_cached_user_by_sub(self, okta_sub: str) -> Optional[int]:
        """
        Get user_id from cache by okta_sub.

        Args:
            okta_sub: Okta subject identifier

        Returns:
            Optional[int]: user_id or None
        """
        cache = caches['default']
        cache_key = f'okta_sub_to_user_{okta_sub}'
        return cache.get(cache_key)

    def _clear_cached_user_by_sub(self, okta_sub: str):
        """
        Clear cached okta_sub -> user_id mapping.

        Args:
            okta_sub: Okta subject identifier
        """
        cache = caches['default']
        cache_key = f'okta_sub_to_user_{okta_sub}'
        cache.delete(cache_key)

    def _logout_user(self, user: UserModel, okta_sub: str):
        """
        Perform user logout:
        - Delete AccessToken for OKTA source
        - Clear token and profile cache
        - Terminate session

        Args:
            user: User to logout
            okta_sub: Okta subject identifier (for cache cleanup)
        """
        AccountLogService().send_ws_message(
            account_id=1,
            data={
                'action': 'logout_user_start',
                'user_id': user.id,
                'user_email': user.email,
                'okta_sub': okta_sub,
                'account_id': user.account_id,
            },
            group_name='okta_logout',
        )
        # Get access tokens before deletion for profile cache cleanup
        access_tokens = list(AccessToken.objects.filter(
            user=user,
            source=self.source,
        ).values_list('access_token', flat=True))
        AccountLogService().send_ws_message(
            account_id=1,
            data={
                'action': 'logout_user_tokens_found',
                'user_id': user.id,
                'tokens_count': len(access_tokens),
                'source': (
                    self.source.value
                    if hasattr(self.source, 'value')
                    else str(self.source)
                ),
            },
            group_name='okta_logout',
        )
        # Delete AccessToken for OKTA source
        deleted_count = AccessToken.objects.filter(
            user=user,
            source=self.source,
        ).delete()
        AccountLogService().send_ws_message(
            account_id=1,
            data={
                'action': 'logout_user_tokens_deleted',
                'user_id': user.id,
                'deleted_count': deleted_count[0] if deleted_count else 0,
            },
            group_name='okta_logout',
        )
        # Clear user profile cache
        cache_keys_cleared = []
        for access_token in access_tokens:
            cache_key = f'user_profile_{access_token}'
            self._delete_cache(key=cache_key)
            cache_keys_cleared.append(cache_key)
        AccountLogService().send_ws_message(
            account_id=1,
            data={
                'action': 'logout_user_profile_cache_cleared',
                'user_id': user.id,
                'cache_keys_count': len(cache_keys_cleared),
            },
            group_name='okta_logout',
        )
        # Clear okta_sub -> user_id mapping cache
        if okta_sub:
            self._clear_cached_user_by_sub(okta_sub)
            AccountLogService().send_ws_message(
                account_id=1,
                data={
                    'action': 'logout_user_sub_cache_cleared',
                    'user_id': user.id,
                    'okta_sub': okta_sub,
                },
                group_name='okta_logout',
            )
        # Clear all tokens from cache (terminate all sessions)
        PneumaticToken.expire_all_tokens(user)
        AccountLogService().send_ws_message(
            account_id=1,
            data={
                'action': 'logout_user_completed',
                'user_id': user.id,
                'user_email': user.email,
                'okta_sub': okta_sub,
                'all_sessions_terminated': True,
            },
            group_name='okta_logout',
        )
