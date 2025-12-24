from typing import Optional, Tuple
from uuid import uuid4

import jwt
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import caches

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

    def process_logout(self, sub_id: dict):
        """
        Process Okta Global Token Revocation (GTR) request.

        Args:
            sub_id: Subject identifier dict from Okta GTR format
        """
        sub = sub_id.get('sub')
        iss = sub_id.get('iss')
        AccountLogService().send_ws_message(
            account_id=1,
            data={
                'action': 'process_gtr_logout_start',
                'sub': sub,
                'iss': iss,
                'format': sub_id.get('format'),
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

    def process_event_hook(
        self,
        event_type: str,
        event_id: str,
        data: dict,
    ):
        """
        Process Okta Event Hook for user lifecycle events.

        Supported events:
        - user.lifecycle.deactivate: User deactivated in Okta
        - application.user_membership.remove: User access revoked

        Args:
            event_type: Type of event from Okta
            event_id: Unique event identifier
            data: Event data containing user information
        """
        AccountLogService().send_ws_message(
            account_id=1,
            data={
                'action': 'process_event_hook_start',
                'eventType': event_type,
                'eventId': event_id,
                'data_keys': list(data.keys()),
            },
            group_name='okta_events',
        )

        # Extract user email from event data
        email = None
        target = data.get('target')
        if isinstance(target, list):
            for item in target:
                if (
                    isinstance(item, dict)
                    and item.get('type') == 'User'
                ):
                    alternate_id = (
                        item.get('alternateId') or
                        item.get('alternate_id')
                    )
                    if alternate_id:
                        email = alternate_id.lower()
                        break

        if not email:
            AccountLogService().send_ws_message(
                account_id=1,
                data={
                    'action': 'process_event_hook_email_not_found',
                    'eventType': event_type,
                    'eventId': event_id,
                    'data': data,
                },
                group_name='okta_events',
            )
            return

        AccountLogService().send_ws_message(
            account_id=1,
            data={
                'action': 'process_event_hook_email_found',
                'eventType': event_type,
                'eventId': event_id,
                'email': email,
            },
            group_name='okta_events',
        )

        # Find user by email
        try:
            user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            AccountLogService().send_ws_message(
                account_id=1,
                data={
                    'action': 'process_event_hook_user_not_found',
                    'eventType': event_type,
                    'eventId': event_id,
                    'email': email,
                },
                group_name='okta_events',
            )
            return

        AccountLogService().send_ws_message(
            account_id=1,
            data={
                'action': 'process_event_hook_user_found',
                'eventType': event_type,
                'eventId': event_id,
                'email': email,
                'user_id': user.id,
            },
            group_name='okta_events',
        )

        # Handle event based on type
        if event_type in (
            'user.lifecycle.deactivate',
            'application.user_membership.remove',
        ):
            self._handle_user_deactivation(user)
        else:
            AccountLogService().send_ws_message(
                account_id=1,
                data={
                    'action': 'process_event_hook_unsupported_event',
                    'eventType': event_type,
                    'eventId': event_id,
                },
                group_name='okta_events',
            )

    def _handle_user_deactivation(
        self,
        user: UserModel,
    ):
        """
        Handle user deactivation events from Okta.
        Logout user and delete Okta access tokens.
        """

        AccessToken.objects.filter(
            user=user,
            source=self.source,
        ).delete()

        # Terminate all user sessions
        PneumaticToken.expire_all_tokens(user)
