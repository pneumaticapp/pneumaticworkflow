# pylint: disable=broad-except
import msal
import json
import requests
from typing import Union, Optional
from django.conf import settings
from django.contrib.auth import get_user_model

from pneumatic_backend.utils.salt import get_salt
from pneumatic_backend.accounts.enums import (
    SourceType,
)
from pneumatic_backend.accounts.models import Contact
from pneumatic_backend.authentication.entities import UserData
from pneumatic_backend.authentication.models import AccessToken
from pneumatic_backend.generics.mixins.services import CacheMixin
from pneumatic_backend.storage.google_cloud import GoogleCloudService
from pneumatic_backend.authentication.services import exceptions
from pneumatic_backend.utils.logging import (
    capture_sentry_message,
    SentryLogLevel,
)

UserModel = get_user_model()


class MicrosoftGraphApiMixin:

    api_url = 'https://graph.microsoft.com/v1.0/'

    me_path = (
        'me?$select=id,givenName,surname,jobTitle,'
        'mail,userPrincipalName,userType,creationType'
    )
    users_path = (
        'users?$select=id,givenName,surname,jobTitle,'
        'mail,userPrincipalName,userType,creationType'
    )
    photo_path = 'users/{user_id}/photos/96x96/$value'

    ext_map = {
        'image/svg+xml': 'svg',
        'image/png': 'png',
        'image/jpeg': 'jpg',
        'image/gif': 'gif',
        'image/bmp': 'bmp',
        'image/webp': 'webp',
        'image/tiff': 'tif',
        'image/vnd.microsoft.icon': 'ico',
        'image/x-icon': 'ico',
        'image/apng': 'apng',
        'image/avif': 'avif',
    }

    def _graph_api_request(
        self,
        access_token: str,
        path: str,
        raise_exception=True
    ) -> requests.Response:

        """ Authorization_RequestDenied is returned for personal
            accounts that request a list of users  """

        response = requests.get(
            url=f'{self.api_url}{path}',
            headers={'Authorization': access_token}
        )
        if not response.ok and raise_exception:
            data = response.json()
            if data['error'].get('code') != 'Authorization_RequestDenied':
                capture_sentry_message(
                    message='Microsoft Graph API return an error',
                    data={
                        'response_data': data,
                        'uri': f'{self.api_url}{path}'
                    },
                    level=SentryLogLevel.ERROR
                )
            raise exceptions.GraphApiRequestError()
        return response

    def _get_user(self, access_token: str) -> dict:

        """
            msgraph library not support python < 3.8
            in this case use graph api directly

            Example of result = {
                '@odata.context': 'https://graph.microsoft.com/v1.0/
                    $metadata#users/
                    $entity',
                'businessPhones': [],
                'displayName': 'Azat Zakirov',
                'givenName': 'Azat',
                'jobTitle': None,
                'mail': 'azat.zakirov@pneumatic.app',
                'otherMails': ['azat.zakirov@pneumatic.app'],
                'mobilePhone': None,
                'officeLocation': None,
                'preferredLanguage': None,
                'surname': 'Zakirov',
                'userPrincipalName': 'azat.zakirov_pneumatic.app#
                    EXT#@antonseidlerpneumatic.onmicrosoft.com',
                'id': '1087125f-604a-4536-ad8b-d89708622ab9'
            } """

        response = self._graph_api_request(
            path=self.me_path,
            access_token=access_token
        )
        return response.json()

    def _get_users(self, access_token: str) -> list:

        response = self._graph_api_request(
            path=self.users_path,
            access_token=access_token
        )
        try:
            data = response.json()
        except json.decoder.JSONDecodeError:
            # The request may be received with a broken json
            data = {
                '@odata.context': (
                    'https://graph.microsoft.com/v1.0/$metadata'
                    '#users(id,givenName,surname,jobTitle,mail)'
                ),
                'value': []
            }
        return data

    def _get_user_photo(
        self,
        access_token: str,
        user_id: str,
    ) -> Optional[str]:

        """ Save photo in the storage and return public URL """

        public_url = None
        if not settings.PROJECT_CONF['STORAGE']:
            return public_url
        response = self._graph_api_request(
            path=self.photo_path.format(user_id=user_id),
            access_token=access_token,
            raise_exception=False
        )
        if response.ok:
            binary_photo: bytes = response.content
            content_type = response.headers['content-type']
            ext = self.ext_map.get(content_type, '')
            if ext:
                filepath = f'{get_salt(30)}_photo_96x96.{ext}'
            else:
                filepath = f'{get_salt(30)}_photo_96x96'
            storage = GoogleCloudService()
            public_url = storage.upload_from_binary(
                binary=binary_photo,
                filepath=filepath,
                content_type=content_type
            )
        return public_url


class MicrosoftAuthService(
    CacheMixin,
    MicrosoftGraphApiMixin,
):

    cache_key_prefix = 'ms_flow'
    cache_timeout = 600  # 10 min
    scopes = [
        'User.Read.All',
        'User.Read',
    ]

    """ Requested scopes contains default msal scopes.
        Full list of scopes: [
            'openid',
            'offline_access',
            'User.Read.All',
            'User.Read',
            'profile'
        ]
    """

    def __init__(self):
        self.auth_client = self._build_msal_app()
        self.tokens = None

    def _build_msal_app(self):
        return msal.ConfidentialClientApplication(
            client_id=settings.MS_CLIENT_ID,
            client_credential=settings.MS_CLIENT_SECRET,
            authority=settings.MS_AUTHORITY,
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
            'client_info': 'eyJ1aWQi...0YjY2ZGFkIn0',
            'state': 'KvpfgTSUmwtOaPny',
            'session_state': '0d046a4b-061a-4de5-be04-472a06763149'
        }

        Example success response:
        {
            'token_type': 'Bearer',
            'scope': 'openid
                profile email
                https://graph.microsoft.com/User.Read
                https://graph.microsoft.com/.default',
            'expires_in': 3781,
            'ext_expires_in': 3781,
            'access_token': 'eyJ0eXAiO...iJKV1',
            'client_info': 'eyJ1aWQiOi...FkIn0',
            'id_token_claims': {
                'aud': '3e6326c0-5863-4382-91bf-50e6c002dcc9',
                'iss': 'https://login.microsoftonline.com/<tenant_id>/v2.0',
                'iat': 1697549467,
                'nbf': 1697549467,
                'exp': 1697553367,
                'idp': 'https://sts.windows.net/91...04b66dad/',
                'name': 'Azat Zakirov',
                'nonce': 'ce0bde...c0fe594f907292c4b',
                'oid': '1087125f-604a-4536-ad8b-d89708622ab9',
                'preferred_username': 'azat.zakirov@pneumatic.app',
                'rh': '0.Ab0Aa_jr...kb9Q5sAC3MnLAIM.',
                'sub': '7Q5pkJz8jcpChfmCWgad3ofb7nRV2s1P8GSPQjtotv8',
                'tid': '57ebf86b-24c4-4dbd-886e-952caaf3f1a4',
                'uti': 'REFiHcSI6keHOz0wXPeSAA',
                'ver': '2.0'
            }
        }

        Example bad response:
        {
            'error': 'invalid_grant',
            'error_description': 'AADSTS70008: The provided authorization code
                or refresh token has expired due to inactivity.
                 Send a new interactive authorization request for this user
                 and resource.\r\nTrace ID: 1425a68d-fd05-4d81-aeca-
                 6aa0d84f6800\r\n'
                'Correlation ID: 261c54a8-d38e-4a8f-9afa-c96abbcc0eab\r\n'
                'Timestamp: 2023-10-22 09:03:20Z',
            'error_codes': [70008],
            'timestamp': '2023-10-22 09:03:20Z',
            'trace_id': '1425a68d-fd05-4d81-aeca-6aa0d84f6800',
            'correlation_id': '261c54a8-d38e-4a8f-9afa-c96abbcc0eab',
            'error_uri': 'https://login.microsoftonline.com/error?code=70008',
            'suberror': 'bad_token'
        }
        """

        flow_data = self._get_cache(key=auth_response['state'])
        if not flow_data:
            raise exceptions.TokenInvalidOrExpired()
        response = self.auth_client.acquire_token_by_auth_code_flow(
            auth_code_flow=flow_data,
            auth_response=auth_response
        )
        if response.get('error'):
            capture_sentry_message(
                message='Get Microsoft Access token return an error',
                data=response,
                level=SentryLogLevel.WARNING
            )
            raise exceptions.TokenInvalidOrExpired()
        self.tokens = response
        return f'{response["token_type"]} {response["access_token"]}'

    def _get_access_token(self, user_id: int) -> str:

        """ Use existent access token and refresh if expired """

        try:
            token = AccessToken.objects.get(
                user_id=user_id,
                source=SourceType.MICROSOFT
            )
        except AccessToken.DoesNotExist:
            capture_sentry_message(
                message='MS Access  token not found for the user',
                data={'user_id': user_id},
                level=SentryLogLevel.ERROR
            )
            raise exceptions.AccessTokenNotFound()
        else:
            if token.is_expired:
                tokens_data = self.auth_client.acquire_token_by_refresh_token(
                    refresh_token=token.refresh_token,
                    scopes=self.scopes
                )
                token.access_token = tokens_data['access_token']
                token.refresh_token = tokens_data['refresh_token']
                token.expires_in = tokens_data['expires_in']
                token.save()
            return token.access_token

    def _get_email_from_principal_name(self, value: str) -> Optional[str]:

        """ userPrincipalName has normal email format for internal users
            and 'username_domain#EXT#@antonseidlerpneumatic.onmicrosoft.com'
            format for external users. """

        try:
            email = value.split('#EXT#')[0]
            if email.find('@') < 1:
                login, domain = email.rsplit('_', 1)
                email = '@'.join((login, domain))
        except Exception:
            email = None
        return email

    def _get_user_profile_email(self, user_profile: dict) -> Optional[str]:

        """ Work accounts do have 'userType' and 'creationType' fields
            We cannot trust the email specified in the work account,
            because it is not confirmed, but we can trust userPrincipalName
            because it is created only in the organization’s domain """

        is_work_account = (
            'userType' in user_profile.keys()
            or 'creationType' in user_profile.keys()
        )
        if is_work_account:
            email = self._get_email_from_principal_name(
                user_profile['userPrincipalName']
            )
        else:
            email = user_profile.get('mail')
        if not email:
            capture_sentry_message(
                message='Email not found in Microsoft account',
                data={'profile': user_profile}
            )
        else:
            email = email.lower()
        return email

    def save_tokens_for_user(self, user: UserModel):
        AccessToken.objects.update_or_create(
            source=SourceType.MICROSOFT,
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

    def get_auth_uri(self) -> str:

        """
        example flow_data  = {
            'state': 'KvpfgTSUmwtOaPny',
            'redirect_uri': None,
            'scope': [
                'https://graph.microsoft.com/.default',
                'offline_access',
                'openid',
                'profile'
            ],
            'auth_uri': 'https://login.microsoftonline.com/
                <tenant_id>/oauth2/v2.0/authorize
                ?client_id=<client_id>
                &response_type=code
                &scope=https%3A%2F%2Fgraph.microsoft.com%2F.default
                    +offline_access
                    +openid+profile
                &state=KvpfgTSUmwtOaPny
                &code_challenge=6dIW6jlemjp9X1aQsweLxTg_VQUQpWo4kB_8qJhl9Is
                &code_challenge_method=S256
                &nonce=ce0bde40f06ef766...3f2df907292c4b
                &client_info=1',
            'code_verifier': 'IKACQ7Zr3-lPXf.kJxngeWFh_Y6dvoMDHR05tcBwyEm',
            'nonce': 'eNKUArHaPLsjoVmn',
            'claims_challenge': None
        } """

        flow_data = self.auth_client.initiate_auth_code_flow(
            scopes=self.scopes
        )
        self._set_cache(value=flow_data, key=flow_data['state'])
        return flow_data['auth_uri']

    def get_user_data(self, auth_response: dict) -> UserData:

        """ Retrieve user details during signin / signup process """

        access_token = self._get_first_access_token(auth_response)
        user_profile = self._get_user(access_token)
        email = self._get_user_profile_email(user_profile)
        if not email:
            raise exceptions.EmailNotExist(
                details={
                    'user_profile': user_profile,
                    'email': email
                }
            )
        photo = self._get_user_photo(
            access_token=access_token,
            user_id=user_profile['id']
        )
        first_name = user_profile['givenName'] or email.split('@')[0]
        capture_sentry_message(
            message=f'MS user profile {email}',
            data={
                'photo': photo,
                'first_name': first_name,
                'user_profile': user_profile,
                'email': email,
            },
            level=SentryLogLevel.INFO
        )
        return UserData(
            email=email,
            first_name=first_name,
            last_name=user_profile['surname'],
            job_title=user_profile['jobTitle'],
            photo=photo,
            company_name=None,
        )

    def update_user_contacts(self, user: UserModel):

        """ Save all organization users in contacts """

        access_token = self._get_access_token(user.id)
        users_data = self._get_users(access_token)
        for user_profile in users_data['value']:
            email = self._get_user_profile_email(user_profile)
            if email and email != user.email:
                photo = self._get_user_photo(
                    access_token=access_token,
                    user_id=user_profile['id']
                )
                first_name = user_profile['givenName'] or email.split('@')[0]
                Contact.objects.update_or_create(
                    account=user.account,
                    user=user,
                    source=SourceType.MICROSOFT,
                    email=email,
                    defaults={
                        'photo': photo,
                        'first_name': first_name,
                        'last_name': user_profile['surname'],
                        'job_title': user_profile['jobTitle'],
                        'source_id': user_profile['id'],
                    }
                )
