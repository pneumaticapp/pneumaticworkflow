import json
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


class Auth0Service(SignUpMixin, CacheMixin):

    cache_key_prefix = 'auth0'
    cache_timeout = 600  # 10 min
    source = SourceType.AUTH0

    def __init__(
        self,
        domain: Optional[str] = None,
        request: Optional[HttpRequest] = None,
    ):
        if not settings.PROJECT_CONF['SSO_AUTH']:
            raise exceptions.Auth0ServiceException(MSG_AU_0017)

        sso_provider = settings.PROJECT_CONF.get('SSO_PROVIDER', '')
        if sso_provider and sso_provider != 'auth0':
            raise exceptions.Auth0ServiceException(MSG_AU_0017)

        self.config = self._get_config(domain)
        self.tokens: Optional[Dict] = None
        self.scope = 'openid email profile offline_access'
        self.request = request

    def _get_config(self, domain: Optional[str] = None) -> SSOConfigData:
        if domain:
            try:
                sso_config = SSOConfig.objects.get(
                    domain=domain,
                    provider=SSOProvider.AUTH0,
                    is_active=True,
                )
                return SSOConfigData(
                    client_id=sso_config.client_id,
                    client_secret=sso_config.client_secret,
                    domain=sso_config.domain,
                    redirect_uri=settings.AUTH0_REDIRECT_URI,
                )
            except SSOConfig.DoesNotExist as exc:
                raise exceptions.Auth0ServiceException(
                    MSG_AU_0018(domain),
                ) from exc
        else:
            if not settings.AUTH0_CLIENT_SECRET:
                raise exceptions.Auth0ServiceException(MSG_AU_0019)
            return SSOConfigData(
                client_id=settings.AUTH0_CLIENT_ID,
                client_secret=settings.AUTH0_CLIENT_SECRET,
                domain=settings.AUTH0_DOMAIN,
                redirect_uri=settings.AUTH0_REDIRECT_URI,
            )

    def _serialize_value(self, value: Union[str, dict]) -> str:
        return json.dumps(value, ensure_ascii=False)

    def _deserialize_value(self, value: Optional[str]) -> dict:
        return json.loads(value) if value else None

    def _get_first_access_token(self, auth_response: dict) -> str:

        """
        Receive an access token for the first time on an authorization flow

        Example auth_response = {
            'code': '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
            'state': 'KvpfgTSUmwtOaPny',
        }

        Example success response:
        {
           "access_token": "eyJz93a...k4laUWw",
           "refresh_token": "GEbRxBN...edjnXbL",
           "id_token": "eyJ0XAi...4faeEoQ",
           "token_type": "Bearer",
           "expires_in": 86400
        }

        Example bad response: 403
        {
            'error': 'invalid_grant',
            'error_description': 'Invalid authorization code'
        }
        """

        state = self._get_cache(key=auth_response['state'])
        if not state:
            raise exceptions.TokenInvalidOrExpired
        try:
            response = requests.post(
                f'https://{self.config.domain}/oauth/token',
                data={
                    'grant_type': 'authorization_code',
                    'client_id': self.config.client_id,
                    'client_secret': self.config.client_secret,
                    'code': auth_response['code'],
                    'redirect_uri': self.config.redirect_uri,
                },
                timeout=10,
            )
            if response.status_code != 200:
                capture_sentry_message(
                    message='Get Auth0 access token failed',
                    data={
                        'status_code': response.status_code,
                        'response': response.text,
                    },
                    level=SentryLogLevel.ERROR,
                )
                raise exceptions.TokenInvalidOrExpired
            self.tokens = response.json()
            return self.tokens["access_token"]
        except requests.RequestException as ex:
            capture_sentry_message(
                message=f'Get Auth0 access token return an error: {ex}',
                level=SentryLogLevel.ERROR,
            )
            raise exceptions.TokenInvalidOrExpired from ex

    def _get_user_profile(self, access_token: str) -> dict:

        """
        Response example:
        {
            'sub': 'google-oauth2|114320...',
            'given_name': 'Azat',
            'family_name': 'Zakirov',
            'nickname': 'azat.zakirov',
            'name': 'Azat Zakirov',
            'picture': 'https://lh3.googlCK0yz_=s96-c',
            'locale': 'en',
            'updated_at': '2024-01-16T16:00:59.519Z',
            'email': 'azat.zakirov@pneumatic.app',
            'email_verified': True
        }
        """

        cache_key = f'user_profile_{access_token}'
        cached_profile = self._get_cache(key=cache_key)
        if cached_profile:
            return cached_profile

        url = f'https://{self.config.domain}/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                capture_sentry_message(
                    message='Auth0 user profile request failed',
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
                message=f'Auth0 user profile request failed: {ex}',
                level=SentryLogLevel.ERROR,
            )
            raise exceptions.TokenInvalidOrExpired from ex

    def get_auth_uri(self) -> str:

        state = str(uuid4())
        self._set_cache(value=True, key=state)
        query_params = {
            'client_id': self.config.client_id,
            'redirect_uri': self.config.redirect_uri,
            'scope': self.scope,
            'state': state,
            'response_type': 'code',
        }

        query = requests.compat.urlencode(query_params)
        return f'https://{self.config.domain}/authorize?{query}'

    def get_user_data(self, user_profile: dict) -> UserData:
        """ Retrieve user details during signin / signup process """
        email = user_profile.get('email')
        if not email:
            raise exceptions.EmailNotExist(
                details={'user_profile': user_profile},
            )
        first_name = (
            user_profile.get('given_name') or
            user_profile.get('name', '').split(' ')[0] or
            email.split('@')[0]
        )
        last_name = (
            user_profile.get('family_name') or
            ' '.join(user_profile.get('name', '').split(' ')[1:])
        )
        job_title = user_profile.get('job_title')
        photo = user_profile.get('picture')
        capture_sentry_message(
            message=f'Auth0 user profile {email}',
            data={
                'photo': photo,
                'first_name': first_name,
                'user_profile': user_profile,
                'email': email,
            },
            level=SentryLogLevel.INFO,
        )
        return UserData(
            email=email,
            first_name=first_name,
            last_name=last_name,
            job_title=job_title,
            photo=photo,
            company_name=None,
        )

    def save_tokens_for_user(self, user: UserModel):
        AccessToken.objects.update_or_create(
            source=SourceType.AUTH0,
            user=user,
            defaults={
                'expires_in': self.tokens['expires_in'],
                'refresh_token': self.tokens['refresh_token'],
                'access_token': self.tokens['access_token'],
            },
        )

    def _get_access_token(self, user_id: int) -> str:
        """ Use existent access token and refresh if expired """
        try:
            token = AccessToken.objects.get(
                user_id=user_id,
                source=SourceType.AUTH0,
            )
        except AccessToken.DoesNotExist as exc:
            capture_sentry_message(
                message='Auth0 Access token not found for the user',
                data={'user_id': user_id},
                level=SentryLogLevel.ERROR,
            )
            raise exceptions.AccessTokenNotFound from exc
        else:
            if token.is_expired:
                # Auth0 token refresh logic would go here
                # For now, raise exception if token is expired
                raise exceptions.TokenInvalidOrExpired
            return token.access_token

    def authenticate_user(
        self,
        auth_response: dict,
    ) -> Tuple[UserModel, PneumaticToken]:
        """Authenticate user via Auth0 and auto-create user if needed"""
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
            try:
                sso_config = SSOConfig.objects.get(
                    domain=self.config.domain,
                    provider=SSOProvider.AUTH0,
                    is_active=True,
                )
                existing_account = sso_config.account
            except SSOConfig.DoesNotExist:
                raise AuthenticationFailed(MSG_AU_0003) from exc

            user, token = self.join_existing_account(
                account=existing_account,
                **user_data,
            )

        self.save_tokens_for_user(user)
        AnalyticService.users_logged_in(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
            source=SourceType.AUTH0,
        )
        return user, token
