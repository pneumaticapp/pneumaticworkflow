import base64
import hashlib
import secrets
import json
import urllib.parse
from typing import Dict, Optional, Tuple, Union
from uuid import uuid4

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from rest_framework.exceptions import AuthenticationFailed

from src.accounts.enums import SourceType
from src.analysis.services import AnalyticService
from src.authentication.entities import UserData, SSOConfigData
from src.authentication.enums import (
    AuthTokenType,
    SSOProvider,
)
from src.authentication.messages import (
    MSG_AU_0003,
    MSG_AU_0017,
    MSG_AU_0018,
    MSG_AU_0019,
)
from src.authentication.models import (
    AccessToken,
    SSOConfig,
)
from src.authentication.services import exceptions
from src.authentication.services.user_auth import AuthService
from src.authentication.tokens import PneumaticToken
from src.authentication.views.mixins import SignUpMixin
from src.generics.mixins.services import CacheMixin
from src.utils.logging import (
    SentryLogLevel,
    capture_sentry_message,
)

UserModel = get_user_model()


class OktaService(SignUpMixin, CacheMixin):

    cache_key_prefix = 'okta_flow'
    cache_timeout = 600  # 10 min

    def __init__(
        self,
        domain: Optional[str] = None,
        request: Optional[HttpRequest] = None,
    ):
        if not settings.PROJECT_CONF['SSO_AUTH']:
            raise exceptions.OktaServiceException(MSG_AU_0017)

        sso_provider = settings.PROJECT_CONF.get('SSO_PROVIDER', '')
        if sso_provider and sso_provider != 'okta':
            raise exceptions.OktaServiceException(MSG_AU_0017)

        self.config = self._get_config(domain)
        self.tokens: Optional[Dict] = None
        self.scope = 'openid email profile'
        self.request = request

    def _get_config(self, domain: Optional[str] = None) -> SSOConfigData:
        if domain:
            try:
                sso_config = SSOConfig.objects.get(
                    domain=domain,
                    provider=SSOProvider.OKTA,
                    is_active=True,
                )
                return SSOConfigData(
                    client_id=sso_config.client_id,
                    client_secret=sso_config.client_secret,
                    domain=sso_config.domain,
                    redirect_uri=settings.OKTA_REDIRECT_URI,
                )
            except SSOConfig.DoesNotExist as exc:
                raise exceptions.OktaServiceException(
                    MSG_AU_0018(domain),
                ) from exc
        else:
            if not settings.OKTA_CLIENT_SECRET:
                raise exceptions.OktaServiceException(MSG_AU_0019)
            return SSOConfigData(
                client_id=settings.OKTA_CLIENT_ID,
                client_secret=settings.OKTA_CLIENT_SECRET,
                domain=settings.OKTA_DOMAIN,
                redirect_uri=settings.OKTA_REDIRECT_URI,
            )

    def _serialize_value(self, value: Union[str, dict]) -> str:
        return json.dumps(value, ensure_ascii=False)

    def _deserialize_value(
        self,
        value: Optional[str],
    ) -> Union[str, dict, None]:
        return json.loads(value) if value else None

    def _get_first_access_token(self, auth_response: dict) -> str:
        """
        Gets access token during initial authorization

        Example auth_response = {
            'code': '4/0AbUR2VMeHxU...',
            'state': 'random_state_string',
        }

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

        code_verifier = self._get_cache(key=auth_response['state'])
        if not code_verifier:
            raise exceptions.TokenInvalidOrExpired

        try:
            response = requests.post(
                f'https://{self.config.domain}/oauth2/default/v1/token',
                data={
                    'grant_type': 'authorization_code',
                    'client_id': self.config.client_id,
                    'client_secret': self.config.client_secret,
                    'code': auth_response['code'],
                    'redirect_uri': self.config.redirect_uri,
                    'code_verifier': code_verifier,
                },
                timeout=10,
            )
            if response.status_code != 200:
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
        except requests.RequestException as ex:
            capture_sentry_message(
                message=f'Get Okta access token return an error: {ex}',
                level=SentryLogLevel.ERROR,
            )
            raise exceptions.TokenInvalidOrExpired from ex

    def _get_user_profile(self, access_token: str) -> dict:
        """
        Gets user profile via Okta userinfo endpoint

        Example response:
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
            if response.status_code != 200:
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
        except requests.RequestException as ex:
            capture_sentry_message(
                message=f'Okta user profile request failed: {ex}',
                level=SentryLogLevel.ERROR,
            )
            raise exceptions.TokenInvalidOrExpired from ex

    def get_auth_uri(self) -> str:

        state = str(uuid4())
        code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32),
        ).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest(),
        ).decode('utf-8').rstrip('=')

        # Cache code_verifier for later validation
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

        query = urllib.parse.urlencode(query_params)
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
            job_title=None,
            photo=None,
            company_name=None,
        )

    def save_tokens_for_user(self, user: UserModel):
        AccessToken.objects.update_or_create(
            source=SourceType.OKTA,
            user=user,
            defaults={
                'expires_in': self.tokens['expires_in'],
                'refresh_token': '',
                'access_token': self.tokens['access_token'],
            },
        )

    def authenticate_user(
        self,
        auth_response: dict,
    ) -> Tuple[UserModel, PneumaticToken]:
        """Authenticate user via Okta and return user with token"""
        access_token = self._get_first_access_token(auth_response)
        user_profile = self._get_user_profile(access_token)
        user_data = self.get_user_data(user_profile)

        try:
            user = UserModel.objects.active().get(email=user_data['email'])
            token = AuthService.get_auth_token(
                user=user,
                user_agent=self.request.headers.get(
                    'User-Agent',
                    self.request.META.get('HTTP_USER_AGENT'),
                ),
                user_ip=self.request.META.get('HTTP_X_REAL_IP'),
            )
        except UserModel.DoesNotExist as exc:
            raise AuthenticationFailed(MSG_AU_0003) from exc

        self.save_tokens_for_user(user)

        AnalyticService.users_logged_in(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
            source=SourceType.OKTA,
        )

        return user, token
