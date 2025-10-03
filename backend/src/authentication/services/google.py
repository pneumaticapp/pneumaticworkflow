import json
import urllib.parse
from typing import Optional, Union
from uuid import uuid4

import requests
from django.conf import settings
from django.contrib.auth import get_user_model

from src.accounts.enums import SourceType
from src.accounts.models import Contact
from src.authentication.entities import UserData
from src.authentication.models import AccessToken
from src.authentication.services import exceptions
from src.generics.mixins.services import CacheMixin
from src.logs.service import AccountLogService
from src.utils.logging import (
    capture_sentry_message,
    SentryLogLevel,
)


UserModel = get_user_model()


class GooglePeopleApiMixin:
    """
    Mixin for working with Google People API to fetch contacts
    """

    people_api_url = 'https://people.googleapis.com/v1/'
    profile_path = (
        'people/me?personFields=names,emailAddresses,photos,organizations'
    )
    connections_path = (
        'people/me/connections?personFields=names,emailAddresses,photos,'
        'organizations&pageSize=1000'
    )

    def _people_api_request(
        self,
        access_token: str,
        path: str,
        raise_exception=True
    ) -> requests.Response:
        """Performs request to Google People API"""

        response = requests.get(
            url=f'{self.people_api_url}{path}',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        if not response.ok and raise_exception:
            data = response.json() if response.content else {}
            if response.status_code != 401:
                capture_sentry_message(
                    message='Google People API returned an error',
                    data={
                        'response_data': data,
                        'status_code': response.status_code,
                        'uri': f'{self.people_api_url}{path}'
                    },
                    level=SentryLogLevel.ERROR
                )
            raise exceptions.PeopleApiRequestError()
        return response

    def _get_user_profile(self, access_token: str) -> dict:
        """
        Gets user profile via Google People API

        Example response:
        {
            "resourceName": "people/103547991957319905401",
            "etag": "%EgUBAgkL...",
            "names": [
                {
                    "metadata": {
                        "primary": true,
                        "source": {
                            "type": "PROFILE",
                            "id": "103547991957319905401"
                        }
                    },
                    "displayName": "John Doe",
                    "familyName": "Doe",
                    "givenName": "John",
                    "displayNameLastFirst": "Doe, John"
                }
            ],
            "emailAddresses": [
                {
                    "metadata": {
                        "primary": true,
                        "verified": true,
                        "source": {
                            "type": "ACCOUNT",
                            "id": "103547991957319905401"
                        }
                    },
                    "value": "ivan.ivanov@example.com"
                }
            ],
            "photos": [
                {
                    "metadata": {
                        "primary": true,
                        "source": {
                            "type": "PROFILE",
                            "id": "103547991957319905401"
                        }
                    },
                    "url": "https://lh3.googleusercontent.com/..."
                }
            ]
        }
        """

        response = self._people_api_request(
            path=self.profile_path,
            access_token=access_token
        )
        return response.json()

    def _get_user_connections(self, access_token: str) -> list:
        """
        Gets user contacts list via Google People API
        """

        response = self._people_api_request(
            path=self.connections_path,
            access_token=access_token,
            raise_exception=False
        )

        if response.ok:
            try:
                data = response.json()
                return data.get('connections', [])
            except json.decoder.JSONDecodeError:
                return []
        return []

    def _find_primary(self, items, value_key=None):
        """
        Find primary item in a list from Google People API.
        """
        primary = next(
            (
                item
                for item in items
                if item.get('metadata', {}).get('primary')
            ),
            None
        )
        if primary is None and items:
            primary = items[0]
        return primary.get(value_key) if primary and value_key else primary

    def _parse_profile_data(self, profile: dict) -> dict:
        """
        Parse profile data Google People API
        """
        names = profile.get('names', [])
        emails = profile.get('emailAddresses', [])
        photos = profile.get('photos', [])
        organizations = profile.get('organizations', [])

        primary_name = self._find_primary(names)
        primary_email = self._find_primary(emails, value_key='value')
        photo_url = self._find_primary(photos, value_key='url')
        primary_org = self._find_primary(organizations)
        job_title = primary_org.get('title') if primary_org else None

        return {
            'primary_name': primary_name,
            'primary_email': primary_email,
            'photo_url': photo_url,
            'job_title': job_title,
        }


class GoogleAuthService(
    CacheMixin,
    GooglePeopleApiMixin,
):
    """
    Service for authorization via Google OAuth2 using
    Authorization Code Flow
    """

    cache_key_prefix = 'g_flow'
    cache_timeout = 600  # 10 min

    # Scopes for reading contacts and user profile
    scopes = [
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/contacts.readonly',
    ]

    def __init__(self):
        self.tokens = None
        self.client_id = settings.GOOGLE_OAUTH2_CLIENT_ID
        self.client_secret = settings.GOOGLE_OAUTH2_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_OAUTH2_REDIRECT_URI

    def _serialize_value(self, value: Union[str, dict]) -> str:
        return json.dumps(value, ensure_ascii=False)

    def _deserialize_value(self, value: Optional[str]) -> dict:
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
            "access_token": "ya29.a0AfH6SMC...",
            "expires_in": 3599,
            "refresh_token": "1//04_refresh_token...",
            "scope": "https://www.googleapis.com/auth/userinfo.profile...",
            "token_type": "Bearer"
        }

        Example error:
        {
            "error": "invalid_grant",
            "error_description": "Bad Request"
        }
        """

        state = self._get_cache(key=auth_response['state'])
        if not state:
            raise exceptions.TokenInvalidOrExpired()

        token_url = 'https://oauth2.googleapis.com/token'
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': auth_response['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri,
        }

        response = requests.post(token_url, data=data)

        if not response.ok:
            response_data = response.json() if response.content else {}
            capture_sentry_message(
                message='Get Google access token returned an error',
                data={
                    'response_data': response_data,
                    'status_code': response.status_code
                },
                level=SentryLogLevel.WARNING
            )
            raise exceptions.TokenInvalidOrExpired()

        self.tokens = response.json()
        return self.tokens['access_token']

    def save_tokens_for_user(self, user: UserModel):
        """Saves tokens for user"""
        AccessToken.objects.update_or_create(
            source=SourceType.GOOGLE,
            user=user,
            defaults={
                'expires_in': self.tokens['expires_in'],
                'refresh_token': self.tokens.get('refresh_token', ''),
                'access_token': self.tokens['access_token']
            }
        )

    def get_auth_uri(self) -> str:
        """
        Generates URL for Google authorization

        Returns link like:
        https://accounts.google.com/o/oauth2/v2/auth?client_id=...
        """

        state = str(uuid4())
        self._set_cache(value=state, key=state)

        capture_sentry_message(
            message='Google OAuth state created and cached',
            data={
                'state': state,
                'cache_key_prefix': self.cache_key_prefix,
                'cache_timeout': self.cache_timeout,
                'cache': self.cache,
            },
            level=SentryLogLevel.INFO
        )

        auth_url = 'https://accounts.google.com/o/oauth2/v2/auth'
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scopes),
            'response_type': 'code',
            'state': state,
            'access_type': 'offline',
            'prompt': 'consent',
            'include_granted_scopes': 'true'
        }

        query_string = urllib.parse.urlencode(params)
        return f'{auth_url}?{query_string}'

    def get_user_data(self, auth_response: dict) -> UserData:
        """Gets user data during authorization/registration process"""

        access_token = self._get_first_access_token(auth_response)
        user_profile = self._get_user_profile(access_token)

        # Parse profile data using common function
        parsed_data = self._parse_profile_data(user_profile)
        primary_name = parsed_data['primary_name']
        primary_email = parsed_data['primary_email']
        photo_url = parsed_data['photo_url']
        job_title = parsed_data['job_title']

        if not primary_email:
            raise exceptions.EmailNotExist(
                details={
                    'user_profile': user_profile,
                    'email': primary_email
                }
            )

        first_name = (
            primary_name.get('givenName')
            if primary_name and primary_name.get('givenName')
            else primary_email.split('@')[0]
        )
        last_name = primary_name.get('familyName') if primary_name else ''

        capture_sentry_message(
            message=f'Google user profile {primary_email}',
            data={
                'photo': photo_url,
                'first_name': first_name,
                'user_profile': user_profile,
                'email': primary_email,
                'job_title': job_title,
            },
            level=SentryLogLevel.INFO
        )

        return UserData(
            email=primary_email.lower(),
            first_name=first_name,
            last_name=last_name,
            job_title=job_title,
            photo=photo_url,
            company_name=None,
        )

    def update_user_contacts(self, user: UserModel):
        """Saves user contacts from Google"""

        response_data = {'created_contacts': [], 'updated_contacts': []}
        path = f'{self.people_api_url}{self.connections_path}'
        title = f'Google contacts request: {user.email}'
        http_status = 200

        try:
            access_token = self._get_access_token(user.id)
            connections = self._get_user_connections(access_token)
            response_data['connections_count'] = len(connections)

            for connection in connections:
                # Parse connection data using common function
                parsed_data = self._parse_profile_data(connection)
                primary_name = parsed_data['primary_name']
                primary_email = parsed_data['primary_email']
                photo_url = parsed_data['photo_url']
                job_title = parsed_data['job_title']

                # For contacts, also check for verified emails
                if not primary_email:
                    emails = connection.get('emailAddresses', [])
                    for email in emails:
                        if email.get('metadata', {}).get('verified'):
                            primary_email = email['value']
                            break

                if primary_email and primary_email != user.email:
                    first_name = (
                        primary_name.get('givenName')
                        if primary_name and primary_name.get('givenName')
                        else primary_email.split('@')[0]
                    )
                    last_name = (
                        primary_name.get('familyName') if primary_name
                        else ''
                    )

                    _, created = Contact.objects.update_or_create(
                        account=user.account,
                        user=user,
                        source=SourceType.GOOGLE,
                        email=primary_email.lower(),
                        defaults={
                            'photo': photo_url,
                            'first_name': first_name,
                            'last_name': last_name,
                            'job_title': job_title,
                            'source_id': connection.get('resourceName', ''),
                        }
                    )

                    if created:
                        response_data['created_contacts'].append(
                            primary_email
                        )
                    else:
                        response_data['updated_contacts'].append(
                            primary_email
                        )

        except Exception as ex:  # pylint: disable=broad-except
            http_status = 400
            response_data['message'] = str(ex)
            response_data['exception_type'] = type(ex).__name__
            response_data['details'] = getattr(ex, 'details', None)
        finally:
            if user.account.log_api_requests:
                AccountLogService().contacts_request(
                    user=user,
                    path=path,
                    title=title,
                    http_status=http_status,
                    response_data=response_data,
                    contractor='Google People API',
                )

    def _get_access_token(self, user_id: int) -> str:
        """
        Get access token for user, refresh if expired
        """
        try:
            token = AccessToken.objects.get(
                user_id=user_id,
                source=SourceType.GOOGLE
            )
        except AccessToken.DoesNotExist:
            capture_sentry_message(
                message='Google access token not found',
                data={'user_id': user_id},
                level=SentryLogLevel.ERROR
            )
            raise exceptions.AccessTokenNotFound()

        if token.is_expired:
            self._refresh_access_token(token)
            token.refresh_from_db()

        return token.access_token

    def _refresh_access_token(self, token: AccessToken) -> None:
        """Refresh expired access token using refresh token"""

        response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': token.refresh_token,
                'grant_type': 'refresh_token',
            }
        )

        if response.ok:
            token_data = response.json()
            token.access_token = token_data['access_token']
            if 'refresh_token' in token_data:
                token.refresh_token = token_data['refresh_token']
            token.expires_in = token_data['expires_in']
            token.save()
        else:
            capture_sentry_message(
                message='Failed to refresh Google token',
                data={
                    'user_id': token.user_id,
                    'status_code': response.status_code,
                    'response': response.text
                },
                level=SentryLogLevel.ERROR
            )
            raise exceptions.TokenInvalidOrExpired()
