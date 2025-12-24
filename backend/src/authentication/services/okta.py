from typing import Optional, Tuple
from uuid import uuid4

import jwt
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import caches

from src.accounts.enums import SourceType
from src.authentication.entities import UserData, SSOConfigData
from src.authentication.enums import SSOProvider
from src.authentication.messages import MSG_AU_0018
from src.authentication.models import (
    AccessToken,
    SSOConfig,
)
from src.authentication.services import exceptions
from src.authentication.services.base_sso import BaseSSOService
from src.authentication.tokens import PneumaticToken
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

    def __init__(self, domain: Optional[str] = None):
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
        first_name = user_profile.get('given_name') or email.split('@')[0]
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
                id_payload = jwt.decode(
                    id_token,
                    options={
                        "verify_signature": False,
                        "verify_exp": False,
                        "verify_aud": False,
                        "verify_iss": False,
                    },
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

    def _cache_user_by_sub(self, okta_sub: str, user: UserModel):
        cache = caches['default']
        cache_key = f'okta_sub_to_user_{okta_sub}'
        cache.set(cache_key, user.id, timeout=2592000)
