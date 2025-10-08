import json
import requests
from typing import Union, Optional, Tuple
from uuid import uuid4
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from src.accounts.enums import SourceType
from src.accounts.models import Contact, Account
from src.authentication.models import AccessToken
from src.authentication.entities import UserData
from src.authentication.services import AuthService
from src.authentication.tokens import PneumaticToken
from src.authentication.views.mixins import SignUpMixin
from src.generics.mixins.services import CacheMixin
from src.authentication.services import exceptions
from src.utils.logging import (
    capture_sentry_message,
    SentryLogLevel,
)
from src.authentication.messages import MSG_AU_0003
from rest_framework.exceptions import AuthenticationFailed

UserModel = get_user_model()


class Auth0Service(SignUpMixin, CacheMixin):

    cache_key_prefix = 'auth0'
    cache_timeout = 600  # 10 min
    MGMT_TOKEN_CACHE_KEY = 'mgmt_token'
    TOKEN_EXPIRY = 3600  # 1 hour default

    def __init__(self, request: Optional[HttpRequest] = None):
        self.tokens = None
        self.client_id = settings.AUTH0_CLIENT_ID
        self.client_secret = settings.AUTH0_CLIENT_SECRET
        self.domain = settings.AUTH0_DOMAIN
        self.redirect_uri = settings.AUTH0_REDIRECT_URI
        self.scope = 'openid email profile offline_access'
        self.request = request

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
        return self.tokens["access_token"]

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
                'access_token': self.tokens['access_token'],
            }
        )

    def _get_access_token(self, user_id: int) -> str:
        """ Use existent access token and refresh if expired """
        try:
            token = AccessToken.objects.get(
                user_id=user_id,
                source=SourceType.AUTH0
            )
        except AccessToken.DoesNotExist:
            capture_sentry_message(
                message='Auth0 Access token not found for the user',
                data={'user_id': user_id},
                level=SentryLogLevel.ERROR
            )
            raise exceptions.AccessTokenNotFound()
        else:
            if token.is_expired:
                # Auth0 token refresh logic would go here
                # For now, raise exception if token is expired
                raise exceptions.TokenInvalidOrExpired()
            return token.access_token

    def _get_users(self, org_id: str) -> dict:
        """ Get organization members from Auth0 """
        access_token = self._get_management_api_token()
        url = f'https://{self.domain}/api/v2/organizations/{org_id}/members'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as ex:
            capture_sentry_message(
                message=f'Auth0 organization members request failed: {ex}',
                data={
                    'org_id': org_id,
                    'status_code': getattr(response, 'status_code', None)
                },
                level=SentryLogLevel.ERROR
            )
            raise exceptions.FailedFetchMembers()

    def _get_user_organizations(self, user_id: str) -> list:
        """ Get user's organizations from Auth0 """
        access_token = self._get_management_api_token()
        url = f'https://{self.domain}/api/v2/users/{user_id}/organizations'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as ex:
            capture_sentry_message(
                message=f'Auth0 user organizations request failed: {ex}',
                data={
                    'user_id': user_id,
                    'status_code': getattr(response, 'status_code', None)
                },
                level=SentryLogLevel.ERROR
            )
            return []

    def update_user_contacts(self, user: UserModel):
        """ Save all organization users in contacts """
        response_data = {'created_contacts': [], 'updated_contacts': []}
        try:
            access_token = self._get_access_token(user.id)
            user_profile = self._get_user_profile(access_token)
            user_id = user_profile.get('sub')
            if not user_id:
                capture_sentry_message(
                    message='Auth0 user ID not found in profile',
                    data={'user_email': user.email},
                    level=SentryLogLevel.WARNING
                )
                return response_data
            organizations = self._get_user_organizations(user_id)
            for org in organizations:
                org_id = org.get('id')
                if not org_id:
                    continue
                # Get organization members
                members_data = self._get_users(org_id)
                for member in members_data:
                    email = member.get('email')
                    if email and email != user.email:
                        first_name = (
                            member.get('given_name') or
                            member.get('name', '').split(' ')[0] or
                            email.split('@')[0]
                        )
                        last_name = (
                            member.get('family_name') or
                            ' '.join(member.get('name', '').split(' ')[1:])
                        )
                        _, created = Contact.objects.update_or_create(
                            account=user.account,
                            user=user,
                            source=SourceType.AUTH0,
                            email=email,
                            defaults={
                                'photo': member.get('picture'),
                                'first_name': first_name,
                                'last_name': last_name,
                                'job_title': member.get('job_title'),
                                'source_id': member.get('user_id'),
                            }
                        )
                        if created:
                            response_data['created_contacts'].append(email)
                        else:
                            response_data['updated_contacts'].append(email)
        except Exception as ex:  # pylint: disable=broad-except
            capture_sentry_message(
                message=f'Auth0 contacts update failed: {ex}',
                data={'user_id': user.id, 'user_email': user.email},
                level=SentryLogLevel.ERROR
            )
        return response_data

    def get_user_organizations(self, user_data: dict) -> list:
        """ Get user's organizations during authentication """
        try:
            user_id = user_data.get('sub')
            if not user_id:
                return []
            return self._get_user_organizations(user_id)
        except Exception as ex:  # pylint: disable=broad-except
            capture_sentry_message(
                message=f'Failed to get user organizations: {ex}',
                data={'user_data': user_data},
                level=SentryLogLevel.WARNING
            )
            return []

    def _get_management_api_token(self) -> str:
        """ Get Management API token for Auth0 """
        cached_token = self._get_cache(self.MGMT_TOKEN_CACHE_KEY)
        if cached_token:
            return cached_token
        url = f'https://{self.domain}/oauth/token'
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'audience': f'https://{self.domain}/api/v2/',
            'grant_type': 'client_credentials'
        }
        try:
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            token_data = response.json()
            access_token = token_data['access_token']
            cache_timeout = (
                token_data.get('expires_in', self.TOKEN_EXPIRY) - 60
            )
            original_timeout = self.cache_timeout
            self.cache_timeout = cache_timeout
            self._set_cache(self.MGMT_TOKEN_CACHE_KEY, access_token)
            self.cache_timeout = original_timeout
            return access_token
        except requests.RequestException as ex:
            capture_sentry_message(
                message=f'Failed to get Management API token: {ex}',
                level=SentryLogLevel.ERROR
            )
            raise exceptions.TokenInvalidOrExpired()


    def authenticate_user(
        self,
        auth_response: dict,
        utm_source: Optional[str] = None,
        utm_medium: Optional[str] = None,
        utm_term: Optional[str] = None,
        utm_content: Optional[str] = None,
        utm_campaign: Optional[str] = None,
        gclid: Optional[str] = None,
    ) -> Tuple[UserModel, PneumaticToken]:
        """Authenticate user via Auth0 and create/join account"""
        
        user_data = self.get_user_data(auth_response)
        
        try:
            user = UserModel.objects.active().get(email=user_data['email'])
            token = AuthService.get_auth_token(
                user=user,
                user_agent=self.request.headers.get(
                    'User-Agent',
                    self.request.META.get('HTTP_USER_AGENT')
                ),
                user_ip=self.request.META.get('HTTP_X_REAL_IP'),
            )
            return user, token
        except UserModel.DoesNotExist:
            if not settings.PROJECT_CONF['SIGNUP']:
                raise AuthenticationFailed(MSG_AU_0003)
            
            user_profile = self._get_user_profile(self.tokens['access_token'])
            organizations = self.get_user_organizations(user_profile)
            
            existing_account = None
            if organizations:
                org_ids = [
                    org.get('id') for org in organizations if org.get('id')
                ]
                if org_ids:
                    existing_account = Account.objects.filter(
                        external_id__in=org_ids,
                        is_deleted=False
                    ).first()
            
            if existing_account:
                # Join existing account
                user, token = self.join_existing_account(
                    account=existing_account,
                    **user_data,
                )
                capture_sentry_message(
                    message='Auth0 user joined existing account',
                    data={
                        'user_email': user_data['email'],
                        'account_id': existing_account.id,
                        'external_id': existing_account.external_id,
                        'organizations': organizations
                    },
                    level=SentryLogLevel.INFO
                )
            else:
                # Create new account
                user, token = self.signup(
                    **user_data,
                    utm_source=utm_source,
                    utm_medium=utm_medium,
                    utm_term=utm_term,
                    utm_content=utm_content,
                    gclid=gclid,
                    utm_campaign=utm_campaign
                )
                if organizations:
                    first_org_id = organizations[0].get('id')
                    if first_org_id:
                        user.account.external_id = first_org_id
                        user.account.save(update_fields=['external_id'])
                capture_sentry_message(
                    message='Auth0 user created new account',
                    data={
                        'user_email': user_data['email'],
                        'account_id': user.account.id,
                        'external_id': user.account.external_id,
                        'organizations': organizations
                    },
                    level=SentryLogLevel.INFO
                )
            
            self.save_tokens_for_user(user)
            return user, token
