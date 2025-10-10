import pytest
import json
from datetime import timedelta
from django.utils import timezone
from unittest.mock import Mock

from src.accounts.enums import SourceType, UserStatus
from src.accounts.models import Contact
from src.authentication import messages
from src.authentication.models import AccessToken
from src.authentication.services.google import GoogleAuthService
from src.authentication.services.exceptions import (
    TokenInvalidOrExpired,
    EmailNotExist,
    PeopleApiRequestError,
    AccessTokenNotFound
)
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_account
)


pytestmark = pytest.mark.django_db


class TestGoogleAuthService:
    """Tests for GoogleAuthService"""

    def test_find_primary__with_primary_item__returns_primary(self):
        """Test _find_primary returns primary item when available"""
        # arrange
        service = GoogleAuthService()
        items = [
            {'metadata': {'primary': False}, 'value': 'secondary'},
            {'metadata': {'primary': True}, 'value': 'primary'},
            {'metadata': {'primary': False}, 'value': 'third'}
        ]

        # act
        result = service._find_primary(items, 'value')

        # assert
        assert result == 'primary'

    def test_find_primary__without_primary_item__returns_first(self):
        """Test _find_primary returns first item when no primary"""
        # arrange
        service = GoogleAuthService()
        items = [
            {'metadata': {'primary': False}, 'value': 'first'},
            {'metadata': {'primary': False}, 'value': 'second'}
        ]

        # act
        result = service._find_primary(items, 'value')

        # assert
        assert result == 'first'

    def test_find_primary__empty_list__returns_none(self):
        """Test _find_primary returns None for empty list"""
        # arrange
        service = GoogleAuthService()
        items = []

        # act
        result = service._find_primary(items, 'value')

        # assert
        assert result is None

    def test_find_primary__without_value_key__returns_whole_item(self):
        """Test _find_primary returns whole item when no value_key"""
        # arrange
        service = GoogleAuthService()
        items = [
            {'metadata': {'primary': True}, 'value': 'test', 'name': 'John'}
        ]

        # act
        result = service._find_primary(items)

        # assert
        assert result == {
            'metadata': {'primary': True}, 'value': 'test', 'name': 'John'
        }

    def test_get_auth_uri__ok(self, mocker):
        """Test URL generation for authorization"""
        # arrange
        mock_settings = mocker.patch(
            'src.authentication.services.google.settings'
        )
        mock_settings.GOOGLE_OAUTH2_CLIENT_ID = 'test_client_id'
        mock_settings.GOOGLE_OAUTH2_REDIRECT_URI = 'https://test.com/callback'

        service = GoogleAuthService()
        set_cache_mock = mocker.patch.object(service, '_set_cache')

        # act
        auth_uri = service.get_auth_uri()

        # assert
        assert 'accounts.google.com/o/oauth2/v2/auth' in auth_uri
        assert 'client_id=test_client_id' in auth_uri
        assert 'redirect_uri=https%3A%2F%2Ftest.com%2Fcallback' in auth_uri
        assert 'scope=' in auth_uri
        assert 'userinfo.profile' in auth_uri
        assert 'userinfo.email' in auth_uri
        assert 'contacts.readonly' in auth_uri
        assert 'response_type=code' in auth_uri
        assert 'state=' in auth_uri
        assert 'access_type=offline' in auth_uri
        assert 'prompt=consent' in auth_uri
        set_cache_mock.assert_called_once()

    def test_parse_profile_data__complete_profile__returns_all_data(self):
        """Test _parse_profile_data with complete profile data"""
        # arrange
        service = GoogleAuthService()
        profile = {
            'names': [{
                'metadata': {'primary': True},
                'givenName': 'John',
                'familyName': 'Doe'
            }],
            'emailAddresses': [{
                'metadata': {'primary': True},
                'value': 'john.doe@example.com'
            }],
            'photos': [{
                'metadata': {'primary': True},
                'url': 'https://photo.url'
            }],
            'organizations': [{
                'metadata': {'primary': True},
                'title': 'Software Engineer'
            }]
        }

        # act
        result = service._parse_profile_data(profile)

        # assert
        assert result['primary_name']['givenName'] == 'John'
        assert result['primary_name']['familyName'] == 'Doe'
        assert result['primary_email'] == 'john.doe@example.com'
        assert result['photo_url'] == 'https://photo.url'
        assert result['job_title'] == 'Software Engineer'

    def test_parse_profile_data__empty_profile__returns_none_values(self):
        """Test _parse_profile_data with empty profile"""
        # arrange
        service = GoogleAuthService()
        profile = {}

        # act
        result = service._parse_profile_data(profile)

        # assert
        assert result['primary_name'] is None
        assert result['primary_email'] is None
        assert result['photo_url'] is None
        assert result['job_title'] is None

    def test_parse_profile_data__no_primary_items__uses_first(self):
        """Test _parse_profile_data uses first items when no primary"""
        # arrange
        service = GoogleAuthService()
        profile = {
            'names': [{
                'metadata': {'primary': False},
                'givenName': 'Jane',
                'familyName': 'Smith'
            }],
            'emailAddresses': [{
                'metadata': {'primary': False},
                'value': 'jane.smith@example.com'
            }],
            'photos': [{
                'metadata': {'primary': False},
                'url': 'https://photo2.url'
            }],
            'organizations': [{
                'metadata': {'primary': False},
                'title': 'Manager'
            }]
        }

        # act
        result = service._parse_profile_data(profile)

        # assert
        assert result['primary_name']['givenName'] == 'Jane'
        assert result['primary_email'] == 'jane.smith@example.com'
        assert result['photo_url'] == 'https://photo2.url'
        assert result['job_title'] == 'Manager'

    def test_get_user_data__valid_response__ok(self, mocker):
        """Test getting user data with valid response"""
        # arrange
        mock_settings = mocker.patch(
            'src.authentication.services.google.settings'
        )
        mock_settings.GOOGLE_OAUTH2_CLIENT_ID = 'test_client_id'
        mock_settings.GOOGLE_OAUTH2_CLIENT_SECRET = 'test_client_secret'
        mock_settings.GOOGLE_OAUTH2_REDIRECT_URI = 'https://test.com/callback'

        service = GoogleAuthService()

        get_cache_mock = mocker.patch.object(
            service,
            '_get_cache',
            return_value=True
        )
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'expires_in': 3600,
            'refresh_token': 'test_refresh_token',
            'token_type': 'Bearer'
        }
        mocker.patch(
            'src.authentication.services.google.requests.post',
            return_value=mock_response
        )

        user_profile_response = {
            'names': [{
                'metadata': {'primary': True},
                'givenName': 'John',
                'familyName': 'Doe',
                'displayName': 'John Doe'
            }],
            'emailAddresses': [{
                'metadata': {'primary': True},
                'value': 'john.doe@example.com'
            }],
            'photos': [{
                'metadata': {'primary': True},
                'url': 'https://example.com/photo.jpg'
            }],
            'organizations': [{
                'metadata': {'primary': True},
                'title': 'Senior Developer'
            }]
        }
        get_user_profile_mock = mocker.patch.object(
            service,
            '_get_user_profile',
            return_value=user_profile_response
        )

        auth_response = {
            'code': '4/0AbUR2VMeHxU...',
            'state': 'test_state'
        }

        # act
        user_data = service.get_user_data(auth_response)

        # assert
        assert user_data['email'] == 'john.doe@example.com'
        assert user_data['first_name'] == 'John'
        assert user_data['last_name'] == 'Doe'
        assert user_data['photo'] == 'https://example.com/photo.jpg'
        assert user_data['job_title'] == 'Senior Developer'
        assert user_data['company_name'] is None

        get_cache_mock.assert_called_once_with(key='test_state')
        get_user_profile_mock.assert_called_once_with('test_access_token')

    def test_get_user_data__no_email__raises_email_not_exist(self, mocker):
        """Test handling missing email in profile"""
        # arrange
        mock_settings = mocker.patch(
            'src.authentication.services.google.settings'
        )
        mock_settings.GOOGLE_OAUTH2_CLIENT_ID = 'test_client_id'
        mock_settings.GOOGLE_OAUTH2_CLIENT_SECRET = 'test_client_secret'
        mock_settings.GOOGLE_OAUTH2_REDIRECT_URI = 'https://test.com/callback'

        service = GoogleAuthService()

        mocker.patch.object(service, '_get_cache', return_value=True)
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'expires_in': 3600,
            'refresh_token': 'test_refresh_token'
        }
        mocker.patch(
            'src.authentication.services.google.requests.post',
            return_value=mock_response
        )

        user_profile_response = {
            'names': [{
                'metadata': {'primary': True},
                'givenName': 'John',
                'familyName': 'Doe'
            }],
            'emailAddresses': []
        }
        mocker.patch.object(
            service,
            '_get_user_profile',
            return_value=user_profile_response
        )

        auth_response = {
            'code': '4/0AbUR2VMeHxU...',
            'state': 'test_state'
        }

        # act & assert
        with pytest.raises(EmailNotExist):
            service.get_user_data(auth_response)

    def test_get_first_access_token__invalid_state__raises_token_invalid(
        self,
        mocker
    ):
        """Test handling invalid state"""
        # arrange
        service = GoogleAuthService()
        mocker.patch.object(service, '_get_cache', return_value=None)

        auth_response = {
            'code': '4/0AbUR2VMeHxU...',
            'state': 'invalid_state'
        }

        # act & assert
        with pytest.raises(TokenInvalidOrExpired):
            service._get_first_access_token(auth_response)

    def test_get_first_access_token__google_error__raises_token_invalid(
        self,
        mocker
    ):
        """Test handling Google error when exchanging code for token"""
        # arrange
        mock_settings = mocker.patch(
            'src.authentication.services.google.settings'
        )
        mock_settings.GOOGLE_OAUTH2_CLIENT_ID = 'test_client_id'
        mock_settings.GOOGLE_OAUTH2_CLIENT_SECRET = 'test_client_secret'
        mock_settings.GOOGLE_OAUTH2_REDIRECT_URI = 'https://test.com/callback'

        service = GoogleAuthService()
        mocker.patch.object(service, '_get_cache', return_value=True)

        # Mock Google error
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.content = b'{"error": "invalid_grant"}'
        mock_response.json.return_value = {"error": "invalid_grant"}
        mocker.patch(
            'src.authentication.services.google.requests.post',
            return_value=mock_response
        )

        auth_response = {
            'code': 'invalid_code',
            'state': 'test_state'
        }

        # act & assert
        with pytest.raises(TokenInvalidOrExpired):
            service._get_first_access_token(auth_response)

    def test_save_tokens_for_user__ok(self, mocker):
        """Test saving tokens for user"""
        # arrange
        service = GoogleAuthService()
        service.tokens = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh',
            'expires_in': 3600
        }

        user = create_test_user()

        # Mock AccessToken.objects.update_or_create
        update_or_create_mock = mocker.patch(
            'src.authentication.services.google.'
            'AccessToken.objects.update_or_create'
        )

        # act
        service.save_tokens_for_user(user)

        # assert
        update_or_create_mock.assert_called_once()
        call_args = update_or_create_mock.call_args
        assert call_args[1]['source'] == 'google'
        assert call_args[1]['user'] == user
        assert call_args[1]['defaults']['access_token'] == 'test_access_token'
        assert call_args[1]['defaults']['refresh_token'] == 'test_refresh'
        assert call_args[1]['defaults']['expires_in'] == 3600

    def test_update_user_contacts__ok(self, mocker):
        """Test contacts synchronization"""
        # arrange
        service = GoogleAuthService()
        user = create_test_user()

        # Mock getting token
        mocker.patch.object(
            service,
            '_get_access_token',
            return_value='test_token'
        )

        # Mock getting contacts
        connections = [
            {
                'resourceName': 'people/123',
                'names': [{
                    'metadata': {'primary': True},
                    'givenName': 'Jane',
                    'familyName': 'Smith'
                }],
                'emailAddresses': [{
                    'metadata': {'verified': True},
                    'value': 'jane.smith@example.com'
                }]
            }
        ]
        mocker.patch.object(
            service,
            '_get_user_connections',
            return_value=connections
        )

        # Mock Contact.objects.update_or_create
        update_or_create_mock = mocker.patch(
            'src.authentication.services.google.'
            'Contact.objects.update_or_create',
            return_value=(Mock(), True)
        )

        # Mock AccountLogService
        mocker.patch(
            'src.authentication.services.google.'
            'AccountLogService.contacts_request'
        )

        # act
        service.update_user_contacts(user)

        # assert
        update_or_create_mock.assert_called_once()
        call_args = update_or_create_mock.call_args
        assert call_args[1]['email'] == 'jane.smith@example.com'
        assert call_args[1]['account'] == user.account
        assert call_args[1]['user'] == user
        assert call_args[1]['source'] == 'google'
        assert call_args[1]['defaults']['first_name'] == 'Jane'
        assert call_args[1]['defaults']['last_name'] == 'Smith'

    def test_get_user_data__not_first_name__set_default(self, mocker):
        """Test setting default first name when givenName is missing"""
        # arrange
        mock_settings = mocker.patch(
            'src.authentication.services.google.settings'
        )
        mock_settings.GOOGLE_OAUTH2_CLIENT_ID = 'test_client_id'
        mock_settings.GOOGLE_OAUTH2_CLIENT_SECRET = 'test_client_secret'
        mock_settings.GOOGLE_OAUTH2_REDIRECT_URI = 'https://test.com/callback'

        service = GoogleAuthService()

        mocker.patch.object(service, '_get_cache', return_value=True)
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'expires_in': 3600,
            'refresh_token': 'test_refresh_token'
        }
        mocker.patch(
            'src.authentication.services.google.requests.post',
            return_value=mock_response
        )

        email = 'username@domain.com'
        user_profile_response = {
            'names': [{
                'metadata': {'primary': True},
                'familyName': 'Doe',
                'displayName': 'username@domain.com'
                # No givenName - should use email prefix
            }],
            'emailAddresses': [{
                'metadata': {'primary': True},
                'value': email
            }],
            'photos': []
        }
        mocker.patch.object(
            service,
            '_get_user_profile',
            return_value=user_profile_response
        )

        auth_response = {
            'code': '4/0AbUR2VMeHxU...',
            'state': 'test_state'
        }

        # act
        result = service.get_user_data(auth_response)

        # assert
        assert result['first_name'] == 'username'

    def test_get_user_data__email_uppercase__return_lower(self, mocker):
        """Test converting uppercase email to lowercase"""
        # arrange
        mock_settings = mocker.patch(
            'src.authentication.services.google.settings'
        )
        mock_settings.GOOGLE_OAUTH2_CLIENT_ID = 'test_client_id'
        mock_settings.GOOGLE_OAUTH2_CLIENT_SECRET = 'test_client_secret'
        mock_settings.GOOGLE_OAUTH2_REDIRECT_URI = 'https://test.com/callback'

        service = GoogleAuthService()

        mocker.patch.object(service, '_get_cache', return_value=True)
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'expires_in': 3600,
            'refresh_token': 'test_refresh_token'
        }
        mocker.patch(
            'src.authentication.services.google.requests.post',
            return_value=mock_response
        )

        user_profile_response = {
            'names': [{
                'metadata': {'primary': True},
                'givenName': 'John',
                'familyName': 'Doe',
                'displayName': 'John Doe'
            }],
            'emailAddresses': [{
                'metadata': {'primary': True},
                'value': 'John.Doe@Example.COM'
            }]
        }
        mocker.patch.object(
            service,
            '_get_user_profile',
            return_value=user_profile_response
        )

        auth_response = {
            'code': '4/0AbUR2VMeHxU...',
            'state': 'test_state'
        }

        # act
        result = service.get_user_data(auth_response)

        # assert
        assert result['email'] == 'john.doe@example.com'

    def test_get_user_data__with_job_title__extracts_correctly(self, mocker):
        """Test getting user data with job title from organizations"""
        # arrange
        mock_settings = mocker.patch(
            'src.authentication.services.google.settings'
        )
        mock_settings.GOOGLE_OAUTH2_CLIENT_ID = 'test_client_id'
        mock_settings.GOOGLE_OAUTH2_CLIENT_SECRET = 'test_client_secret'
        mock_settings.GOOGLE_OAUTH2_REDIRECT_URI = 'https://test.com/callback'

        service = GoogleAuthService()
        mocker.patch.object(service, '_get_cache', return_value=True)

        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'expires_in': 3600,
            'refresh_token': 'test_refresh_token',
            'token_type': 'Bearer'
        }
        mocker.patch(
            'src.authentication.services.google.requests.post',
            return_value=mock_response
        )

        user_profile_response = {
            'names': [{
                'metadata': {'primary': True},
                'givenName': 'Jane',
                'familyName': 'Smith'
            }],
            'emailAddresses': [{
                'metadata': {'primary': True},
                'value': 'jane.smith@example.com'
            }],
            'organizations': [{
                'metadata': {'primary': False},
                'title': 'Junior Developer'
            }, {
                'metadata': {'primary': True},
                'title': 'Senior Product Manager'
            }]
        }
        mocker.patch.object(
            service,
            '_get_user_profile',
            return_value=user_profile_response
        )

        auth_response = {
            'code': '4/0AbUR2VMeHxU...',
            'state': 'test_state'
        }

        # act
        result = service.get_user_data(auth_response)

        # assert
        assert result['email'] == 'jane.smith@example.com'
        assert result['first_name'] == 'Jane'
        assert result['last_name'] == 'Smith'
        assert result['job_title'] == 'Senior Product Manager'
        assert result['photo'] is None

    def test_people_api_request__with_raise_exception_false__no_exception(
        self,
        mocker
    ):
        """Test API request with raise_exception=False"""
        # arrange
        access_token = 'test_token'
        path = 'people/me'
        response_mock = mocker.Mock(
            ok=False,
            status_code=404
        )
        mocker.patch(
            'src.authentication.services.google.requests.get',
            return_value=response_mock
        )
        service = GoogleAuthService()

        # act
        result = service._people_api_request(
            access_token=access_token,
            path=path,
            raise_exception=False
        )

        # assert
        assert result == response_mock

    def test_refresh_access_token__no_refresh_token_in_response__keep_old(
        self,
        mocker
    ):
        """Test token refresh when new refresh_token is not returned"""
        # arrange
        user = create_test_user()
        old_refresh_token = 'old_refresh_token'
        token = AccessToken.objects.create(
            user=user,
            source=SourceType.GOOGLE,
            access_token='old_access_token',
            refresh_token=old_refresh_token,
            expires_in=3600,
        )

        mock_settings = mocker.patch(
            'src.authentication.services.google.settings'
        )
        mock_settings.GOOGLE_OAUTH2_CLIENT_ID = 'test_client_id'
        mock_settings.GOOGLE_OAUTH2_CLIENT_SECRET = 'test_client_secret'

        token_new_data = {
            'access_token': 'new_access_token',
            'expires_in': 3000,
            # No refresh_token in response
        }
        refresh_response_mock = mocker.Mock(
            ok=True,
            json=mocker.Mock(return_value=token_new_data)
        )
        mocker.patch(
            'src.authentication.services.google.requests.post',
            return_value=refresh_response_mock
        )

        service = GoogleAuthService()

        # act
        service._refresh_access_token(token)

        # assert
        token.refresh_from_db()
        assert token.access_token == token_new_data['access_token']
        assert token.refresh_token == old_refresh_token
        assert token.expires_in == token_new_data['expires_in']

    def test_refresh_access_token__failed_request__raise_exception(
        self,
        mocker
    ):
        """Test token refresh failure"""
        # arrange
        user = create_test_user()
        token = AccessToken.objects.create(
            user=user,
            source=SourceType.GOOGLE,
            access_token='old_access_token',
            refresh_token='old_refresh_token',
            expires_in=3600,
        )

        mock_settings = mocker.patch(
            'src.authentication.services.google.settings'
        )
        mock_settings.GOOGLE_OAUTH2_CLIENT_ID = 'test_client_id'
        mock_settings.GOOGLE_OAUTH2_CLIENT_SECRET = 'test_client_secret'

        refresh_response_mock = mocker.Mock(
            ok=False,
            status_code=400,
            text='{"error": "invalid_grant"}'
        )
        mocker.patch(
            'src.authentication.services.google.requests.post',
            return_value=refresh_response_mock
        )

        sentry_mock = mocker.patch(
            'src.authentication.services.google.'
            'capture_sentry_message'
        )

        service = GoogleAuthService()

        # act & assert
        with pytest.raises(TokenInvalidOrExpired):
            service._refresh_access_token(token)

        sentry_mock.assert_called_once()

    def test_get_user_connections__no_connections_key__return_empty(
        self,
        mocker
    ):
        """Test handling response without connections key"""
        # arrange
        access_token = 'test_token'
        response_mock = mocker.Mock(
            ok=True,
            json=mocker.Mock(return_value={'some_other_key': 'value'})
        )
        service = GoogleAuthService()
        people_api_request_mock = mocker.patch.object(
            service,
            '_people_api_request',
            return_value=response_mock
        )

        # act
        result = service._get_user_connections(access_token)

        # assert
        assert result == []
        people_api_request_mock.assert_called_once()

    def test_get_user_connections__not_ok_response__return_empty(self, mocker):
        """Test handling non-OK response"""
        # arrange
        access_token = 'test_token'
        response_mock = mocker.Mock(ok=False)
        service = GoogleAuthService()
        people_api_request_mock = mocker.patch.object(
            service,
            '_people_api_request',
            return_value=response_mock
        )

        # act
        result = service._get_user_connections(access_token)

        # assert
        assert result == []
        people_api_request_mock.assert_called_once()

    def test_people_api_request__ok(self, mocker):
        """Test successful Google People API request"""
        # arrange
        access_token = 'test_token'
        path = 'people/me'
        response_mock = mocker.Mock(
            ok=True,
            json=mocker.Mock()
        )
        request_mock = mocker.patch(
            'src.authentication.services.google.requests.get',
            return_value=response_mock
        )
        sentry_mock = mocker.patch(
            'src.authentication.services.google.'
            'capture_sentry_message'
        )
        service = GoogleAuthService()

        # act
        result = service._people_api_request(
            access_token=access_token,
            path=path,
        )

        # assert
        assert result == response_mock
        request_mock.assert_called_once_with(
            url=f'https://people.googleapis.com/v1/{path}',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        sentry_mock.assert_not_called()

    def test_people_api_request__bad_request__raise_exception(self, mocker):
        """Test Google People API bad request error handling"""
        # arrange
        access_token = 'test_token'
        path = 'people/me'
        response_mock = mocker.Mock(
            ok=False,
            status_code=400
        )
        response_mock.json = mocker.Mock(
            return_value={'error': {'code': 400, 'message': 'Bad Request'}}
        )
        request_mock = mocker.patch(
            'src.authentication.services.google.requests.get',
            return_value=response_mock
        )
        sentry_mock = mocker.patch(
            'src.authentication.services.google.'
            'capture_sentry_message'
        )
        service = GoogleAuthService()

        # act
        with pytest.raises(PeopleApiRequestError) as ex:
            service._people_api_request(
                access_token=access_token,
                path=path,
            )

        # assert
        assert 'Error while retrieving Google profile data' in str(
            ex.value.message
        )
        request_mock.assert_called_once_with(
            url=f'https://people.googleapis.com/v1/{path}',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        sentry_mock.assert_called_once()

    def test_people_api_request__unauthorized__raise_exception(self, mocker):
        """Test Google People API unauthorized error handling"""
        # arrange
        access_token = 'invalid_token'
        path = 'people/me'
        response_mock = mocker.Mock(
            ok=False,
            status_code=401
        )
        response_mock.json = mocker.Mock(
            return_value={'error': {'code': 401, 'message': 'Unauthorized'}}
        )
        request_mock = mocker.patch(
            'src.authentication.services.google.requests.get',
            return_value=response_mock
        )
        sentry_mock = mocker.patch(
            'src.authentication.services.google.'
            'capture_sentry_message'
        )
        service = GoogleAuthService()

        # act
        with pytest.raises(PeopleApiRequestError) as ex:
            service._people_api_request(
                access_token=access_token,
                path=path,
            )

        # assert
        assert 'Error while retrieving Google profile data' in str(
            ex.value.message
        )
        request_mock.assert_called_once()
        sentry_mock.assert_not_called()

    def test_get_user_profile__ok(self, mocker):
        """Test getting user profile from People API"""
        # arrange
        access_token = 'test_token'
        json_mock = mocker.Mock()
        response_mock = mocker.Mock()
        response_mock.json = mocker.Mock(return_value=json_mock)
        service = GoogleAuthService()
        people_api_request_mock = mocker.patch.object(
            service,
            '_people_api_request',
            return_value=response_mock
        )

        # act
        result = service._get_user_profile(access_token)

        # assert
        assert result == json_mock
        people_api_request_mock.assert_called_once_with(
            path=(
                'people/me?personFields=names,'
                'emailAddresses,photos,organizations'
            ),
            access_token=access_token
        )

    def test_get_user_connections__ok(self, mocker):
        """Test getting user connections from People API"""
        # arrange
        access_token = 'test_token'
        connections_data = [{'name': 'John'}, {'name': 'Jane'}]
        json_data = {'connections': connections_data}
        response_mock = mocker.Mock(
            ok=True,
            json=mocker.Mock(return_value=json_data)
        )
        service = GoogleAuthService()
        people_api_request_mock = mocker.patch.object(
            service,
            '_people_api_request',
            return_value=response_mock
        )

        # act
        result = service._get_user_connections(access_token)

        # assert
        assert result == connections_data
        people_api_request_mock.assert_called_once_with(
            path=(
                'people/me/connections?personFields='
                'names,emailAddresses,photos,organizations&pageSize=1000'
            ),
            access_token=access_token,
            raise_exception=False
        )

    def test_get_user_connections__decode_error__return_empty(self, mocker):
        """Test handling JSON decode error for connections"""
        # arrange
        access_token = 'test_token'
        response_mock = mocker.Mock(
            json=mocker.Mock(side_effect=json.decoder.JSONDecodeError(
                msg='msg',
                doc='doc',
                pos=1
            ))
        )
        service = GoogleAuthService()
        people_api_request_mock = mocker.patch.object(
            service,
            '_people_api_request',
            return_value=response_mock
        )

        # act
        result = service._get_user_connections(access_token)

        # assert
        assert result == []
        people_api_request_mock.assert_called_once()

    def test_get_access_token__not_expired__ok(self, mocker):
        """Test getting non-expired access token"""
        # arrange
        user = create_test_user()
        token = AccessToken.objects.create(
            user=user,
            source=SourceType.GOOGLE,
            access_token='test_access_token',
            refresh_token='test_refresh_token',
            expires_in=3600
        )
        service = GoogleAuthService()

        # act
        result = service._get_access_token(user.id)

        # assert
        assert result == token.access_token

    def test_get_access_token__expired__update(self, mocker):
        """Test refreshing expired access token"""
        # arrange
        user = create_test_user()
        old_refresh_token = 'old_refresh_token'
        expires_in = 3600
        token = AccessToken.objects.create(
            user=user,
            source=SourceType.GOOGLE,
            access_token='old_access_token',
            refresh_token=old_refresh_token,
            expires_in=expires_in,
        )
        old_date_updated = token.date_updated

        mock_settings = mocker.patch(
            'src.authentication.services.google.settings'
        )
        mock_settings.GOOGLE_OAUTH2_CLIENT_ID = 'test_client_id'
        mock_settings.GOOGLE_OAUTH2_CLIENT_SECRET = 'test_client_secret'

        token_new_data = {
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',
            'expires_in': 3000,
        }
        refresh_response_mock = mocker.Mock(
            ok=True,
            json=mocker.Mock(return_value=token_new_data)
        )
        requests_post_mock = mocker.patch(
            'src.authentication.services.google.requests.post',
            return_value=refresh_response_mock
        )

        # Use update to avoid triggering auto_now on date_updated
        AccessToken.objects.filter(id=token.id).update(
            date_updated=timezone.now() - timedelta(seconds=expires_in + 120)
        )
        token.refresh_from_db()

        service = GoogleAuthService()
        # Override the service's client credentials for the test
        service.client_id = 'test_client_id'
        service.client_secret = 'test_client_secret'

        # act
        result = service._get_access_token(user.id)

        # assert
        token.refresh_from_db()

        # Verify the refresh request was made
        requests_post_mock.assert_called_once_with(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret',
                'refresh_token': old_refresh_token,
                'grant_type': 'refresh_token',
            }
        )

        assert result == token_new_data['access_token']
        assert token.access_token == token_new_data['access_token']
        assert token.refresh_token == token_new_data['refresh_token']
        assert token.expires_in == token_new_data['expires_in']
        assert token.date_updated > old_date_updated

    def test_get_access_token__not_found__raise_exception(self, mocker):
        """Test access token not found exception"""
        # arrange
        user = create_test_user()
        AccessToken.objects.create(
            user=user,
            source=SourceType.MICROSOFT,
            access_token='ms_token',
            refresh_token='ms_refresh',
            expires_in=3600
        )
        sentry_mock = mocker.patch(
            'src.authentication.services.google.'
            'capture_sentry_message'
        )
        service = GoogleAuthService()

        # act
        with pytest.raises(AccessTokenNotFound) as ex:
            service._get_access_token(user.id)

        # assert
        assert ex.value.message == messages.MSG_AU_0001
        sentry_mock.assert_called_once()

    def test_save_tokens_for_user__create__ok(self, mocker):
        """Test creating new tokens for user"""
        # arrange
        user = create_test_user()
        refresh_token = 'some_refresh'
        access_token = 'some_access'
        expires_in = 3600
        tokens_data = {
            'refresh_token': refresh_token,
            'access_token': access_token,
            'expires_in': expires_in,
        }
        service = GoogleAuthService()
        service.tokens = tokens_data

        # act
        service.save_tokens_for_user(user)

        # assert
        assert AccessToken.objects.get(
            source=SourceType.GOOGLE,
            user=user,
            refresh_token=refresh_token,
            access_token=access_token,
            expires_in=expires_in,
        )

    def test_save_tokens_for_user__update__ok(self):
        """Test updating existing tokens for user"""
        # arrange
        user = create_test_user()
        token = AccessToken.objects.create(
            source=SourceType.GOOGLE,
            user=user,
            refresh_token='old_refresh',
            access_token='old_access',
            expires_in=360
        )

        new_tokens_data = {
            'refresh_token': 'new_refresh',
            'access_token': 'new_access_token',
            'expires_in': 7200
        }
        service = GoogleAuthService()
        service.tokens = new_tokens_data

        # act
        service.save_tokens_for_user(user)

        # assert
        token.refresh_from_db()
        assert token.access_token == new_tokens_data['access_token']
        assert token.refresh_token == new_tokens_data['refresh_token']
        assert token.expires_in == new_tokens_data['expires_in']

    def test_update_user_contacts__default_first_name__ok(self, mocker):
        """Test updating contacts with default first name"""
        # arrange
        account = create_test_account(log_api_requests=True)
        user = create_test_user(account=account)
        service = GoogleAuthService()

        access_token = 'test_token'
        get_access_token_mock = mocker.patch.object(
            service,
            '_get_access_token',
            return_value=access_token
        )

        connection_profile = {
            'resourceName': 'people/123',
            'names': [{
                'metadata': {'primary': True},
                'displayName': 'login@domain.com'
            }],
            'emailAddresses': [{
                'metadata': {'verified': True},
                'value': 'login@domain.com'
            }]
        }
        get_connections_response = [connection_profile]
        get_connections_mock = mocker.patch.object(
            service,
            '_get_user_connections',
            return_value=get_connections_response
        )

        log_mock = mocker.patch(
            'src.authentication.services.google.'
            'AccountLogService.contacts_request'
        )

        google_contact = Contact.objects.create(
            account=user.account,
            user_id=user.id,
            source=SourceType.GOOGLE,
            email='test@test.test'
        )
        google_contact_2 = Contact.objects.create(
            account=user.account,
            user_id=user.id,
            source=SourceType.GOOGLE,
            email='test@test.test'
        )

        # act
        service.update_user_contacts(user)

        # assert
        get_access_token_mock.assert_called_once_with(user.id)
        get_connections_mock.assert_called_once_with(access_token)
        google_contact.refresh_from_db()
        assert google_contact.status == UserStatus.ACTIVE
        google_contact_2.refresh_from_db()
        assert google_contact_2.status == UserStatus.ACTIVE
        assert Contact.objects.filter(
            account=user.account,
            user_id=user.id,
            source=SourceType.GOOGLE,
            email=connection_profile['emailAddresses'][0]['value'],
            first_name='login',
            last_name=None,
            job_title=None,
            source_id=connection_profile['resourceName'],
        ).exists()
        log_mock.assert_called_once()

    def test_update_user_contacts__update_contact__ok(self, mocker):
        """Test updating existing contact"""
        # arrange
        account = create_test_account(log_api_requests=True)
        user = create_test_user(account=account)
        email = 'test_1@test.test'
        contact = Contact.objects.create(
            account=user.account,
            user_id=user.id,
            source=SourceType.GOOGLE,
            email=email,
            photo=None,
            first_name='',
            last_name='',
            job_title=None,
            source_id='people/old_id',
        )

        service = GoogleAuthService()
        access_token = 'test_token'
        mocker.patch.object(
            service,
            '_get_access_token',
            return_value=access_token
        )

        connection_profile = {
            'resourceName': 'people/new_id',
            'names': [{
                'metadata': {'primary': True},
                'givenName': 'John',
                'familyName': 'Doe',
                'displayName': 'John Doe'
            }],
            'emailAddresses': [{
                'metadata': {'verified': True},
                'value': email
            }],
            'photos': [{
                'metadata': {'primary': True},
                'url': 'https://example.com/photo.jpg'
            }]
        }
        get_connections_response = [connection_profile]
        mocker.patch.object(
            service,
            '_get_user_connections',
            return_value=get_connections_response
        )

        log_mock = mocker.patch(
            'src.authentication.services.google.'
            'AccountLogService.contacts_request'
        )

        # act
        service.update_user_contacts(user)

        # assert
        contact.refresh_from_db()
        # Photo should now be saved from Google API
        assert contact.photo == 'https://example.com/photo.jpg'
        assert contact.first_name == 'John'
        assert contact.last_name == 'Doe'
        assert contact.source_id == 'people/new_id'
        log_mock.assert_called_once()

    def test_update_user_contacts__email_not_found__skip(self, mocker):
        """Test skipping contacts without email"""
        # arrange
        user = create_test_user()
        service = GoogleAuthService()

        access_token = 'test_token'
        mocker.patch.object(
            service,
            '_get_access_token',
            return_value=access_token
        )

        connection_profile = {
            'resourceName': 'people/123',
            'names': [{
                'metadata': {'primary': True},
                'givenName': 'John',
                'familyName': 'Doe'
            }],
            'emailAddresses': []
        }
        get_connections_response = [connection_profile]
        mocker.patch.object(
            service,
            '_get_user_connections',
            return_value=get_connections_response
        )

        log_mock = mocker.patch(
            'src.authentication.services.google.'
            'AccountLogService.contacts_request'
        )

        google_contact = Contact.objects.create(
            account=user.account,
            user_id=user.id,
            source=SourceType.GOOGLE,
            email='test@test.test'
        )
        google_contact_2 = Contact.objects.create(
            account=user.account,
            user_id=user.id,
            source=SourceType.GOOGLE,
            email='test@test.test'
        )

        # act
        service.update_user_contacts(user)

        # assert
        google_contact.refresh_from_db()
        assert google_contact.status == UserStatus.ACTIVE
        google_contact_2.refresh_from_db()
        assert google_contact_2.status == UserStatus.ACTIVE
        log_mock.assert_not_called()

    def test_update_user_contacts__exclude_current_user__ok(self, mocker):
        """Test excluding current user from contacts"""
        # arrange
        user = create_test_user()
        service = GoogleAuthService()

        access_token = 'test_token'
        mocker.patch.object(
            service,
            '_get_access_token',
            return_value=access_token
        )

        connection_profile = {
            'resourceName': 'people/123',
            'names': [{
                'metadata': {'primary': True},
                'displayName': user.email
            }],
            'emailAddresses': [{
                'metadata': {'verified': True},
                'value': user.email
            }]
        }
        get_connections_response = [connection_profile]
        mocker.patch.object(
            service,
            '_get_user_connections',
            return_value=get_connections_response
        )

        log_mock = mocker.patch(
            'src.authentication.services.google.'
            'AccountLogService.contacts_request'
        )

        # act
        service.update_user_contacts(user)

        # assert
        assert not Contact.objects.filter(
            account=user.account,
            user_id=user.id,
            source=SourceType.GOOGLE,
            email=user.email,
        ).exists()
        log_mock.assert_not_called()

    def test_update_user_contacts__service_exception__ok(self, mocker):
        """Test handling service exception during contacts update"""
        # arrange
        account = create_test_account(log_api_requests=True)
        user = create_test_user(account=account)
        service = GoogleAuthService()

        access_token = 'test_token'
        mocker.patch.object(
            service,
            '_get_access_token',
            return_value=access_token
        )

        error_message = 'API Error'
        error_details = {'error_details': 'Rate limit exceeded'}
        ex = PeopleApiRequestError(
            message=error_message,
            details=error_details
        )
        mocker.patch.object(
            service,
            '_get_user_connections',
            side_effect=ex
        )

        log_mock = mocker.patch(
            'src.authentication.services.google.'
            'AccountLogService.contacts_request'
        )

        # act
        service.update_user_contacts(user)

        # assert
        log_mock.assert_called_once_with(
            user=user,
            path=(
                'https://people.googleapis.com/v1/people/me/connections'
                '?personFields=names,emailAddresses,'
                'photos,organizations&pageSize=1000'
            ),
            title=f'Google contacts request: {user.email}',
            http_status=400,
            response_data={
                'created_contacts': [],
                'updated_contacts': [],
                'message': error_message,
                'details': error_details,
                'exception_type': 'PeopleApiRequestError'
            },
            contractor='Google People API',
        )

    def test_update_user_contacts__with_photo_and_job_title__saves_correctly(
        self, mocker
    ):
        """
        Test updating contacts with photo and job_title from organizations
        """
        # arrange
        account = create_test_account(log_api_requests=True)
        user = create_test_user(account=account)
        service = GoogleAuthService()

        access_token = 'test_token'
        mocker.patch.object(
            service,
            '_get_access_token',
            return_value=access_token
        )

        connection_profile = {
            'resourceName': 'people/123',
            'names': [{
                'metadata': {'primary': True},
                'givenName': 'Alice',
                'familyName': 'Johnson'
            }],
            'emailAddresses': [{
                'metadata': {'verified': True},
                'value': 'alice.johnson@example.com'
            }],
            'photos': [{
                'metadata': {'primary': True},
                'url': 'https://photos.googleapis.com/alice.jpg'
            }],
            'organizations': [{
                'metadata': {'primary': True},
                'title': 'UI/UX Designer'
            }]
        }
        get_connections_response = [connection_profile]
        mocker.patch.object(
            service,
            '_get_user_connections',
            return_value=get_connections_response
        )

        mocker.patch(
            'src.authentication.services.google.'
            'AccountLogService.contacts_request'
        )

        # act
        service.update_user_contacts(user)

        # assert
        contact = Contact.objects.get(email='alice.johnson@example.com')
        assert contact.first_name == 'Alice'
        assert contact.last_name == 'Johnson'
        assert contact.photo == 'https://photos.googleapis.com/alice.jpg'
        assert contact.job_title == 'UI/UX Designer'
        assert contact.source == SourceType.GOOGLE
        assert contact.source_id == 'people/123'
