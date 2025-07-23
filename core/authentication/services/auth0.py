import json
import requests
from typing import Union, Optional
from uuid import uuid4
from django.conf import settings
from django.contrib.auth import get_user_model
from pneumatic_backend.accounts.enums import SourceType
from pneumatic_backend.authentication.models import AccessToken
from pneumatic_backend.authentication.entities import UserData
from pneumatic_backend.generics.mixins.services import CacheMixin
from pneumatic_backend.authentication.services import exceptions
from pneumatic_backend.utils.logging import (
    capture_sentry_message,
    SentryLogLevel,
)

UserModel = get_user_model()


class Auth0Service(CacheMixin):

    cache_key_prefix = 'auth0'
    cache_timeout = 600  # 10 min

    def __init__(self):
        self.tokens = None
        self.client_id = settings.AUTH0_CLIENT_ID
        self.client_secret = settings.AUTH0_CLIENT_SECRET
        self.domain = settings.AUTH0_DOMAIN
        self.redirect_uri = settings.AUTH0_REDIRECT_URI
        self.scope = 'openid email profile'

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
            raise exceptions.TokenInvalidOrExpired()
        response = requests.post(
            f'https://{self.domain}/oauth/token',
            data={
                'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': auth_response['code'],
                'redirect_uri': self.redirect_uri,
            }
        )
        if not response.ok:
            capture_sentry_message(
                message='Get Auth0 access token return an error',
                data={'content': response.content},
                level=SentryLogLevel.ERROR
            )
            raise exceptions.TokenInvalidOrExpired()
        self.tokens = response.json()
        return f'{self.tokens["token_type"]} {self.tokens["access_token"]}'

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

        response = requests.get(
            f'https://{self.domain}/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        if not response.ok:
            capture_sentry_message(
                message='Get Auth0 user profile return an error',
                data={'content': response.content},
                level=SentryLogLevel.ERROR
            )
            raise exceptions.TokenInvalidOrExpired()
        return response.json()

    def get_auth_uri(self) -> str:

        state = str(uuid4())
        self._set_cache(value=True, key=state)
        query_params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': self.scope,
            'state': state,
            'response_type': 'code',
        }

        query = requests.compat.urlencode(query_params)
        return f'https://{self.domain}/authorize?{query}'

    def get_user_data(self, auth_response: dict) -> UserData:

        """ Retrieve user details during signin / signup process """

        access_token = self._get_first_access_token(auth_response)
        user_profile = self._get_user_profile(access_token)
        email = user_profile['email']
        photo = user_profile['picture']
        if not email:
            raise exceptions.EmailNotExist(
                details={
                    'user_profile': user_profile,
                    'email': email
                }
            )
        first_name = user_profile['given_name'] or email.split('@')[0]
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
            last_name=user_profile['family_name'],
            job_title=None,
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
                'access_token': (
                    f'{self.tokens["token_type"]} '
                    f'{self.tokens["access_token"]}'
                )
            }
        )
