import json

import pytest
from datetime import timedelta
from django.utils import timezone
from pneumatic_backend.authentication import messages
from pneumatic_backend.accounts.enums import (
    SourceType,
    UserStatus,
)
from pneumatic_backend.authentication.services.microsoft import (
    MicrosoftAuthService,
    MicrosoftGraphApiMixin,
)
from pneumatic_backend.storage.google_cloud import GoogleCloudService
from pneumatic_backend.accounts.models import Contact
from pneumatic_backend.authentication.models import AccessToken
from pneumatic_backend.authentication.services import exceptions
from pneumatic_backend.utils.logging import SentryLogLevel
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
)


pytestmark = pytest.mark.django_db


class TestMicrosoftGraphApiMixin:

    def test_graph_api_request__ok(self, mocker):

        # arrange
        access_token = '!@#!@#@!wqww23'
        path = 'some/path'
        response_mock = mocker.Mock(
            ok=True,
            json=mocker.Mock()
        )
        request_user_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.requests.get',
            return_value=response_mock
        )
        sentry_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'capture_sentry_message'
        )
        service = MicrosoftGraphApiMixin()

        # act
        result = service._graph_api_request(
            access_token=access_token,
            path=path,
        )

        # assert
        assert result == response_mock
        request_user_mock.assert_called_once_with(
            url=f'https://graph.microsoft.com/v1.0/{path}',
            headers={'Authorization': access_token}
        )
        sentry_mock.assert_not_called()

    def test_graph_api_request__bad_request__raise_exception(
        self,
        mocker
    ):
        # arrange
        access_token = '!@#!@#@!wqww23'
        path = 'some/path'
        response_mock = mocker.Mock(
            ok=False,
        )
        response_mock.json = mocker.Mock(
            return_value={'error': {'code': 'Authorization_Error'}}
        )
        request_user_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.requests.get',
            return_value=response_mock
        )
        sentry_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'capture_sentry_message'
        )
        service = MicrosoftGraphApiMixin()

        # act
        with pytest.raises(exceptions.GraphApiRequestError) as ex:
            service._graph_api_request(
                access_token=access_token,
                path=path,
            )

        # assert
        assert ex.value.message == messages.MSG_AU_0005
        request_user_mock.assert_called_once_with(
            url=f'https://graph.microsoft.com/v1.0/{path}',
            headers={'Authorization': access_token}
        )
        sentry_mock.assert_called_once()

    def test_graph_api_request__request_denied__raise_exception(
        self,
        mocker
    ):
        # arrange
        access_token = '!@#!@#@!wqww23'
        path = 'some/path'
        response_mock = mocker.Mock(
            ok=False,
        )
        response_mock.json = mocker.Mock(
            return_value={'error': {'code': 'Authorization_RequestDenied'}}
        )
        request_user_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.requests.get',
            return_value=response_mock
        )
        sentry_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'capture_sentry_message'
        )
        service = MicrosoftGraphApiMixin()

        # act
        with pytest.raises(exceptions.GraphApiRequestError) as ex:
            service._graph_api_request(
                access_token=access_token,
                path=path,
            )

        # assert
        assert ex.value.message == messages.MSG_AU_0005
        request_user_mock.assert_called_once_with(
            url=f'https://graph.microsoft.com/v1.0/{path}',
            headers={'Authorization': access_token}
        )
        sentry_mock.assert_not_called()

    def test_get_user__ok(self, mocker):

        # arrange
        access_token = '!@#!@#@!wqww23'
        json_mock = mocker.Mock()
        response_mock = mocker.Mock()
        response_mock.json = mocker.Mock(return_value=json_mock)
        graph_api_request_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftGraphApiMixin._graph_api_request',
            return_value=response_mock
        )
        service = MicrosoftGraphApiMixin()

        # act
        result = service._get_user(access_token)

        # assert
        assert result == json_mock
        graph_api_request_mock.assert_called_once_with(
            path=(
                'me?$select=id,givenName,surname,jobTitle,'
                'mail,userPrincipalName,userType,creationType'
            ),
            access_token=access_token
        )

    def test_get_users__ok(self, mocker):

        # arrange
        access_token = '!@#!@#@!wqww23'
        json_mock = mocker.Mock()
        response_mock = mocker.Mock()
        response_mock.json = mocker.Mock(return_value=json_mock)
        graph_api_request_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftGraphApiMixin._graph_api_request',
            return_value=response_mock
        )
        service = MicrosoftGraphApiMixin()

        # act
        result = service._get_users(access_token)

        # assert
        assert result == json_mock
        graph_api_request_mock.assert_called_once_with(
            path=(
                'users?$select=id,givenName,surname,jobTitle,'
                'mail,userPrincipalName,userType,creationType'
            ),
            access_token=access_token
        )

    def test_get_users__decode_error__raise_exception(self, mocker):

        # arrange
        access_token = '!@#!@#@!wqww23'
        response_mock = mocker.Mock(
            json=mocker.Mock(side_effect=json.decoder.JSONDecodeError(
                msg='msg',
                doc='doc',
                pos=1
            ))
        )
        graph_api_request_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftGraphApiMixin._graph_api_request',
            return_value=response_mock
        )
        service = MicrosoftGraphApiMixin()

        # act
        result = service._get_users(access_token)

        # assert
        assert result == {
            '@odata.context': (
                'https://graph.microsoft.com/v1.0/$metadata'
                '#users(id,givenName,surname,jobTitle,mail)'
            ),
            'value': []
        }
        graph_api_request_mock.assert_called_once_with(
            path=(
                'users?$select=id,givenName,surname,jobTitle,'
                'mail,userPrincipalName,userType,creationType'
            ),
            access_token=access_token
        )

    def test_get_user_photo__ok(self, mocker):

        # arrange
        access_token = '!@#!@#@!wqww23'
        binary_photo = b'123'
        headers = {'content-type': 'image/svg+xml'}
        headers_mock = mocker.MagicMock()
        headers_mock.__getitem__.side_effect = headers.__getitem__
        response_mock = mocker.Mock(headers=headers_mock, ok=True)
        response_mock.content = binary_photo
        settings_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.settings'
        )
        settings_mock.PROJECT_CONF = {'STORAGE': True}
        graph_api_request_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftGraphApiMixin._graph_api_request',
            return_value=response_mock
        )
        salt = '123asd'
        get_salt_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.get_salt',
            return_value=salt
        )
        public_url = 'https://test.com/image.svg'
        storage_init_mock = mocker.patch.object(
            GoogleCloudService,
            attribute='__init__',
            return_value=None
        )
        upload_from_binary_mock = mocker.patch(
            'pneumatic_backend.storage.google_cloud.GoogleCloudService.'
            'upload_from_binary',
            return_value=public_url
        )
        user_id = 'UQ@SDW@31221'
        service = MicrosoftGraphApiMixin()

        # act
        result = service._get_user_photo(
            access_token=access_token,
            user_id=user_id
        )

        # assert
        graph_api_request_mock.assert_called_once_with(
            path=f'users/{user_id}/photos/96x96/$value',
            access_token=access_token,
            raise_exception=False
        )
        get_salt_mock.assert_called_once()
        storage_init_mock.assert_called_once()
        upload_from_binary_mock.assert_called_once_with(
            binary=binary_photo,
            filepath=f'{salt}_photo_96x96.svg',
            content_type=headers['content-type']
        )
        assert result == public_url

    def test_get_user_photo__undefined_content_type__blank_image_ext(
        self,
        mocker
    ):

        # arrange
        access_token = '!@#!@#@!wqww23'
        binary_photo = b'123'
        headers = {'content-type': 'video|bla*-!file'}
        headers_mock = mocker.MagicMock()
        headers_mock.__getitem__.side_effect = headers.__getitem__
        response_mock = mocker.Mock(headers=headers_mock, ok=True)
        response_mock.content = binary_photo
        settings_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.settings'
        )
        settings_mock.PROJECT_CONF = {'STORAGE': True}
        graph_api_request_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftGraphApiMixin._graph_api_request',
            return_value=response_mock
        )
        salt = '123asd'
        get_salt_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.get_salt',
            return_value=salt
        )
        public_url = 'https://test.com/image.svg'
        storage_init_mock = mocker.patch.object(
            GoogleCloudService,
            attribute='__init__',
            return_value=None
        )
        upload_from_binary_mock = mocker.patch(
            'pneumatic_backend.storage.google_cloud.GoogleCloudService.'
            'upload_from_binary',
            return_value=public_url
        )
        user_id = '!@#$#$#12ase'
        service = MicrosoftGraphApiMixin()

        # act
        result = service._get_user_photo(
            user_id=user_id,
            access_token=access_token
        )

        # assert
        graph_api_request_mock.assert_called_once_with(
            path=f'users/{user_id}/photos/96x96/$value',
            access_token=access_token,
            raise_exception=False
        )
        get_salt_mock.assert_called_once()
        storage_init_mock.assert_called_once()
        upload_from_binary_mock.assert_called_once_with(
            binary=binary_photo,
            filepath=f'{salt}_photo_96x96',
            content_type=headers['content-type']
        )
        assert result == public_url

    def test_get_user_photo__not_found__return_none(self, mocker):

        # arrange
        access_token = '!@#!@#@!wqww23'
        response_mock = mocker.Mock(ok=False)
        settings_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.settings'
        )
        settings_mock.PROJECT_CONF = {'STORAGE': True}
        graph_api_request_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftGraphApiMixin._graph_api_request',
            return_value=response_mock
        )
        upload_from_binary_mock = mocker.patch(
            'pneumatic_backend.storage.google_cloud.GoogleCloudService.'
            'upload_from_binary'
        )
        user_id = '!@W@##$%%$21'
        service = MicrosoftGraphApiMixin()

        # act
        result = service._get_user_photo(
            access_token=access_token,
            user_id=user_id
        )

        # assert
        graph_api_request_mock.assert_called_once_with(
            path=f'users/{user_id}/photos/96x96/$value',
            access_token=access_token,
            raise_exception=False
        )
        upload_from_binary_mock.assert_not_called()
        assert result is None

    def test_get_user_photo__disabled_storage__return_none(self, mocker):

        # arrange
        access_token = '!@#!@#@!wqww23'
        binary_photo = b'123'
        headers = {'content-type': 'image/svg+xml'}
        headers_mock = mocker.MagicMock()
        headers_mock.__getitem__.side_effect = headers.__getitem__
        response_mock = mocker.Mock(headers=headers_mock, ok=True)
        response_mock.content = binary_photo
        settings_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.settings'
        )
        settings_mock.PROJECT_CONF = {'STORAGE': False}
        graph_api_request_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftGraphApiMixin._graph_api_request',
            return_value=response_mock
        )
        salt = '123asd'
        get_salt_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.get_salt',
            return_value=salt
        )
        public_url = 'https://test.com/image.svg'
        storage_init_mock = mocker.patch.object(
            GoogleCloudService,
            attribute='__init__',
            return_value=None
        )
        upload_from_binary_mock = mocker.patch(
            'pneumatic_backend.storage.google_cloud.GoogleCloudService.'
            'upload_from_binary',
            return_value=public_url
        )
        user_id = 'UQ@SDW@31221'
        service = MicrosoftGraphApiMixin()

        # act
        result = service._get_user_photo(
            access_token=access_token,
            user_id=user_id
        )

        # assert
        graph_api_request_mock.assert_not_called()
        get_salt_mock.assert_not_called()
        storage_init_mock.assert_not_called()
        upload_from_binary_mock.assert_not_called()
        assert result is None


class TestMicrosoftAuthService:

    def test__get_auth_uri__ok(self, mocker):

        # arrange
        client_mock = mocker.Mock()
        auth_uri = 'https://login.microsoftonline.com/...'
        state = 'YrtkHpALzeTDnliK'
        flow_data = {
            'state': state,
            'auth_uri': auth_uri,
            'claims_challenge': None,
            'code_verifier': 'DrTPYFHdzh~GL-Z4wCi2Bb.5cNOgAteo6IfxpKk7Xsv',
            'nonce': 'zgRBjdhsTKqwQriM',
            'redirect_uri': None,
            'scope': [
                'profile',
                'offline_access',
                'https://graph.microsoft.com/.default',
                'openid'
            ],
        }
        client_mock.initiate_auth_code_flow = mocker.Mock(
            return_value=flow_data
        )
        get_auth_client_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        set_cache_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._set_cache'
        )
        service = MicrosoftAuthService()

        # act
        result = service.get_auth_uri()

        # assert
        assert result == auth_uri
        get_auth_client_mock.assert_called_once()
        client_mock.initiate_auth_code_flow.assert_called_once_with(
            scopes=[
                'User.Read.All',
                'User.Read',
            ]
        )
        set_cache_mock.assert_called_once_with(
            value=flow_data,
            key=state
        )

    def test_get_user_data__ok(self, mocker):

        # arrange
        client_mock = mocker.Mock()
        get_auth_client_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        access_token = '!@#!@#@!wqww23'
        get_access_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_first_access_token',
            return_value=access_token
        )
        profile_id = '!@#seasda'
        email = 'test@test.test'
        first_name = 'Fa'
        last_name = 'Bio'
        job_title = 'QA Engineer'
        profile_data = {
            'id': profile_id,
            'mail': email,
            'givenName': first_name,
            'surname': last_name,
            'jobTitle': job_title,
        }
        get_user_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_user',
            return_value=profile_data
        )
        get_user_profile_email_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_user_profile_email',
            return_value=email
        )
        photo_url = 'https://test.image.com'
        get_user_photo_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_user_photo',
            return_value=photo_url
        )
        auth_response = mocker.Mock()
        service = MicrosoftAuthService()

        # act
        result = service.get_user_data(auth_response)

        # assert
        get_auth_client_mock.assert_called_once()
        get_access_token_mock.assert_called_once_with(auth_response)
        get_user_mock.assert_called_once_with(access_token)
        get_user_profile_email_mock.assert_called_once_with(profile_data)
        get_user_photo_mock.assert_called_once_with(
            access_token=access_token,
            user_id=profile_id,
        )
        assert result['email'] == email
        assert result['first_name'] == first_name
        assert result['last_name'] == last_name
        assert result['company_name'] is None
        assert result['photo'] == photo_url
        assert result['job_title'] == job_title

    def test_get_user_data__not_first_name__set_default(self, mocker):

        # arrange
        client_mock = mocker.Mock()
        mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        access_token = '!@#!@#@!wqww23'
        mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_first_access_token',
            return_value=access_token
        )
        profile_id = '!@#seasda'
        email = 'username@domain.com'
        first_name = None
        last_name = 'Bio'
        job_title = 'QA Engineer'
        profile_data = {
            'id': profile_id,
            'mail': email,
            'givenName': first_name,
            'surname': last_name,
            'jobTitle': job_title,
        }
        mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_user',
            return_value=profile_data
        )
        mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_user_profile_email',
            return_value=email
        )
        photo_url = 'https://test.image.com'
        mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_user_photo',
            return_value=photo_url
        )
        auth_response = mocker.Mock()
        service = MicrosoftAuthService()

        # act
        result = service.get_user_data(auth_response)

        # assert
        assert result['first_name'] == 'username'

    def test_get_user_data__email_not_found__raise_exception(
        self,
        mocker
    ):

        # arrange
        client_mock = mocker.Mock()
        get_auth_client_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        access_token = '!@#!@#@!wqww23'
        get_access_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_first_access_token',
            return_value=access_token
        )
        profile_data = {
            'id': '!@#easd',
            'givenName': 'Fa',
            'surname': 'Bio',
            'jobTitle': 'QA Engineer',
        }
        get_user_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_user',
            return_value=profile_data
        )
        get_user_profile_email_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_user_profile_email',
            return_value=None
        )
        get_user_photo_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_user_photo'
        )
        auth_response = mocker.Mock()
        service = MicrosoftAuthService()

        # act
        with pytest.raises(exceptions.EmailNotExist) as ex:
            service.get_user_data(auth_response)

        # assert
        assert ex.value.message == messages.MSG_AU_0004
        get_auth_client_mock.assert_called_once()
        get_access_token_mock.assert_called_once_with(auth_response)
        get_user_mock.assert_called_once_with(access_token)
        get_user_profile_email_mock.assert_called_once_with(profile_data)
        get_user_photo_mock.assert_not_called()

    def test_get_first_access_token__ok(self, mocker):

        # arrange
        client_mock = mocker.Mock()
        state = 'ASDSDasd12'
        auth_response = {
            'state': state
        }
        response = {
            'token_type': 'Bearer',
            'access_token': '!@#wad123'
        }
        client_mock.acquire_token_by_auth_code_flow = mocker.Mock(
            return_value=response
        )
        get_auth_client_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        flow_data = mocker.Mock()
        get_cache_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_cache',
            return_value=flow_data
        )
        service = MicrosoftAuthService()

        # act
        result = service._get_first_access_token(auth_response)

        # assert
        assert result == f'{response["token_type"]} {response["access_token"]}'
        assert service.tokens == response
        get_auth_client_mock.assert_called_once()
        get_cache_mock.assert_called_once_with(key=state)
        client_mock.acquire_token_by_auth_code_flow.assert_called_once_with(
            auth_code_flow=flow_data,
            auth_response=auth_response
        )

    def test_get_first_access_token__clear_cache__raise_exception(
        self,
        mocker
    ):

        # arrange
        client_mock = mocker.Mock()
        state = 'ASDSDasd12'
        auth_response = {
            'state': state
        }
        client_mock.acquire_token_by_auth_code_flow = mocker.Mock()
        get_auth_client_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        get_cache_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_cache',
            return_value=None
        )
        service = MicrosoftAuthService()

        # act
        with pytest.raises(exceptions.TokenInvalidOrExpired) as ex:
            service._get_first_access_token(auth_response)

        # assert
        assert ex.value.message == messages.MSG_AU_0009
        get_auth_client_mock.assert_called_once()
        get_cache_mock.assert_called_once_with(key=state)
        client_mock.acquire_token_by_auth_code_flow.assert_not_called()

    def test_get_first_access_token__request_return_error__raise_exception(
        self,
        mocker
    ):

        # arrange
        client_mock = mocker.Mock()
        state = 'ASDSDasd12'
        auth_response = {'state': state}
        response = {'error': 'some error'}
        client_mock.acquire_token_by_auth_code_flow = mocker.Mock(
            return_value=response
        )
        get_auth_client_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        flow_data = mocker.Mock()
        get_cache_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_cache',
            return_value=flow_data
        )
        sentry_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'capture_sentry_message'
        )
        service = MicrosoftAuthService()

        # act
        with pytest.raises(exceptions.TokenInvalidOrExpired) as ex:
            service._get_first_access_token(auth_response)

        # assert
        assert ex.value.message == messages.MSG_AU_0009
        get_auth_client_mock.assert_called_once()
        get_cache_mock.assert_called_once_with(key=state)
        client_mock.acquire_token_by_auth_code_flow.assert_called_once_with(
            auth_code_flow=flow_data,
            auth_response=auth_response
        )
        sentry_mock.assert_called_once_with(
            message='Get Microsoft Access token return an error',
            data=response,
            level=SentryLogLevel.WARNING
        )

    def test_get_access_token__not_expired__ok(self, mocker):

        # arrange
        user = create_test_user()
        token = AccessToken.objects.create(
            user=user,
            source=SourceType.MICROSOFT,
            access_token='!@#SDSDe12',
            refresh_token='asdsdfs213',
            expires_in=3600
        )
        client_mock = mocker.Mock()
        get_auth_client_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        client_mock.acquire_token_by_refresh_token = mocker.Mock()
        sentry_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'capture_sentry_message'
        )
        service = MicrosoftAuthService()

        # act
        result = service._get_access_token(user.id)

        # assert
        assert result == token.access_token
        get_auth_client_mock.assert_called_once()
        sentry_mock.assert_not_called()
        client_mock.acquire_token_by_refresh_token.assert_not_called()

    def test_get_access_token__expired__update(self, mocker):

        # arrange
        user = create_test_user()
        old_refresh_token = 'asdsdfs213'
        expires_in = 3600
        token = AccessToken.objects.create(
            user=user,
            source=SourceType.MICROSOFT,
            access_token='!@#SDSDe12',
            refresh_token=old_refresh_token,
            expires_in=expires_in,
        )
        old_date_updated = token.date_updated
        client_mock = mocker.Mock()
        get_auth_client_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        token_new_data = {
            'access_token': 'new access_token',
            'refresh_token': 'new refresh_token',
            'expires_in': 3000,
        }
        client_mock.acquire_token_by_refresh_token = mocker.Mock(
            return_value=token_new_data
        )
        sentry_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'capture_sentry_message'
        )
        # future current date for expire token
        date = timezone.now() + timedelta(seconds=expires_in + 120)
        mocker.patch(
            'pneumatic_backend.payment.stripe.service.timezone.now',
            return_value=date
        )
        service = MicrosoftAuthService()

        # act
        result = service._get_access_token(user.id)

        # assert
        token.refresh_from_db()
        assert result == token_new_data['access_token']
        assert token.access_token == token_new_data['access_token']
        assert token.refresh_token == token_new_data['refresh_token']
        assert token.expires_in == token_new_data['expires_in']
        assert token.date_updated > old_date_updated
        get_auth_client_mock.assert_called_once()
        sentry_mock.assert_not_called()
        client_mock.acquire_token_by_refresh_token.assert_called_once_with(
            refresh_token=old_refresh_token,
            scopes=[
                'User.Read.All',
                'User.Read',
            ]
        )

    def test_get_access_token__not_found__raise_exception(self, mocker):

        # arrange
        user = create_test_user()
        AccessToken.objects.create(
            user=user,
            source=SourceType.GOOGLE,
            access_token='!@#SDSDe12',
            refresh_token='asdsdfs213',
            expires_in=3600
        )
        client_mock = mocker.Mock()
        get_auth_client_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        client_mock.acquire_token_by_refresh_token = mocker.Mock()
        sentry_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'capture_sentry_message'
        )
        service = MicrosoftAuthService()

        # act
        with pytest.raises(exceptions.AccessTokenNotFound) as ex:
            service._get_access_token(user.id)

        # assert
        assert ex.value.message == messages.MSG_AU_0001
        get_auth_client_mock.assert_called_once()
        sentry_mock.assert_called_once()
        client_mock.acquire_token_by_refresh_token.assert_not_called()

    def test_get_email_from_principal_name__ok(self, mocker):

        # arrange
        client_mock = mocker.Mock()
        get_auth_client_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        email = 'some@email.test'
        service = MicrosoftAuthService()

        # act
        result = service._get_email_from_principal_name(email)

        # assert
        assert result == email
        get_auth_client_mock.assert_called_once()

    def test_get_email_from_principal_name__external_user_principal_name__ok(
        self,
        mocker
    ):

        # arrange
        client_mock = mocker.Mock()
        get_auth_client_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        email = 'some.boomer@outlook.com'
        principal_name = (
            'some.boomer_outlook.com#EXT#@pneumaticapp.onmicrosoft.com'
        )
        service = MicrosoftAuthService()

        # act
        result = service._get_email_from_principal_name(principal_name)

        # assert
        assert result == email
        get_auth_client_mock.assert_called_once()

    def test_get_email_from_principal_name__unexpected_format__return_none(
        self,
        mocker
    ):

        # arrange
        client_mock = mocker.Mock()
        get_auth_client_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        principal_name = (
            'some.boomer.outlook.com#EXT#@pneumaticapp.onmicrosoft.com'
        )
        service = MicrosoftAuthService()

        # act
        result = service._get_email_from_principal_name(principal_name)

        # assert
        assert result is None
        get_auth_client_mock.assert_called_once()

    def test_get_user_profile_email__personal_account__ok(self, mocker):

        # arrange
        client_mock = mocker.Mock()
        get_auth_client_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        get_email_from_principal_name_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_email_from_principal_name',
            return_value=client_mock
        )
        email = 'custom@email.com'
        profile_data = {
            'mail': email,
            'userPrincipalName': 'principal@email.com'
        }
        sentry_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'capture_sentry_message'
        )
        service = MicrosoftAuthService()

        # act
        result = service._get_user_profile_email(profile_data)

        # assert
        assert result == email
        get_auth_client_mock.assert_called_once()
        get_email_from_principal_name_mock.assert_not_called()
        sentry_mock.assert_not_called()

    def test_get_user_profile_email__work_account__ok(self, mocker):

        # arrange
        client_mock = mocker.Mock()
        get_auth_client_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        principal_name = 'principal_email.com#EXT#'
        email = 'principal@email.com'
        profile_data = {
            'mail': 'custom@email.com',
            'userPrincipalName': principal_name,
            'userType': 'member',
            'creationType': None
        }
        get_email_from_principal_name_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_email_from_principal_name',
            return_value=email
        )
        sentry_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'capture_sentry_message'
        )
        service = MicrosoftAuthService()

        # act
        result = service._get_user_profile_email(profile_data)

        # assert
        assert result == email
        get_auth_client_mock.assert_called_once()
        get_email_from_principal_name_mock.assert_called_once_with(
            principal_name
        )
        sentry_mock.assert_not_called()

    def test_get_user_profile_email__work_account_without_email__return_none(
        self,
        mocker
    ):

        # arrange
        client_mock = mocker.Mock()
        get_auth_client_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        principal_name = 'principal_email.com#EXT#'
        profile_data = {
            'mail': 'custom@email.com',
            'userPrincipalName': principal_name,
            'userType': 'member',
            'creationType': None
        }
        get_email_from_principal_name_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_email_from_principal_name',
            return_value=None
        )
        sentry_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'capture_sentry_message'
        )
        service = MicrosoftAuthService()

        # act
        result = service._get_user_profile_email(profile_data)

        # assert
        assert result is None
        get_auth_client_mock.assert_called_once()
        get_email_from_principal_name_mock.assert_called_once_with(
            principal_name
        )
        sentry_mock.assert_called_once()

    def test_get_user_profile_email__uppercase__return_lower(self, mocker):

        # arrange
        client_mock = mocker.Mock()
        get_auth_client_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        get_email_from_principal_name_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_email_from_principal_name',
            return_value=client_mock
        )
        email = 'custom@email.com'
        profile_data = {
            'mail':  'CustoM@eMail.cOm',
            'userPrincipalName': 'principal@email.com'
        }
        sentry_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'capture_sentry_message'
        )
        service = MicrosoftAuthService()

        # act
        result = service._get_user_profile_email(profile_data)

        # assert
        assert result == email
        get_auth_client_mock.assert_called_once()
        get_email_from_principal_name_mock.assert_not_called()
        sentry_mock.assert_not_called()

    def test_save_tokens_for_user__create__ok(self, mocker):

        # arrange
        user = create_test_user()
        client_mock = mocker.Mock()
        mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        refresh_token = 'some refresh'
        access_token = 'some access'
        token_type = 'Bearer'
        expires_in = 300
        tokens_data = {
            'refresh_token': refresh_token,
            'access_token': access_token,
            'token_type': token_type,
            'expires_in': expires_in,
        }
        service = MicrosoftAuthService()
        service.tokens = tokens_data

        # act
        service.save_tokens_for_user(user)

        # assert
        assert AccessToken.objects.get(
            source=SourceType.MICROSOFT,
            user=user,
            refresh_token=refresh_token,
            access_token=f'{token_type} {access_token}',
            expires_in=expires_in,
        )

    def test_save_tokens_for_user__update__ok(self, mocker):

        # arrange
        user = create_test_user()
        token_type = 'Bearer'
        token = AccessToken.objects.create(
            source=SourceType.MICROSOFT,
            user=user,
            refresh_token='ahsdsdasd23ggfn',
            access_token=f'{token_type} !@#asas',
            expires_in=360
        )

        client_mock = mocker.Mock()
        mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        new_tokens_data = {
            'refresh_token': 'new refresh',
            'access_token': 'new access token',
            'token_type': token_type,
            'expires_in': 400
        }
        service = MicrosoftAuthService()
        service.tokens = new_tokens_data

        # act
        service.save_tokens_for_user(user)

        # assert
        token.refresh_from_db()
        assert token.access_token == (
            f"{token_type} {new_tokens_data['access_token']}"
        )
        assert token.refresh_token == new_tokens_data['refresh_token']
        assert token.expires_in == new_tokens_data['expires_in']

    def test_update_user_contacts__default_first_name__ok(self, mocker):

        # arrange
        user = create_test_user()
        client_mock = mocker.Mock()
        get_auth_client_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        access_token = '!@#!@#@!wqww23'
        get_access_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_access_token',
            return_value=access_token
        )
        user_profile = {
            'id': '111',
            'mail': 'login@domain.com',
            'givenName': None,
            'surname': None,
            'jobTitle': None,
        }
        get_users_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_users',
            return_value={
                '@odata.context': (
                    'https://graph.microsoft.com/v1.0/$metadata'
                    '#users(id,givenName,surname,jobTitle,mail)'
                ),
                'value': [
                    user_profile
                ]
            }
        )
        get_user_profile_email_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_user_profile_email',
            return_value=user_profile['mail']
        )
        photo_url = 'https://test.image.com'
        get_user_photo_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_user_photo',
            return_value=photo_url
        )
        google_contact = Contact.objects.create(
            account=user.account,
            user_id=user.id,
            source=SourceType.GOOGLE,
            email='test@test.test'
        )
        ms_contact = Contact.objects.create(
            account=user.account,
            user_id=user.id,
            source=SourceType.MICROSOFT,
            email='test@test.test'
        )
        service = MicrosoftAuthService()

        # act
        service.update_user_contacts(user)

        # assert
        get_auth_client_mock.assert_called_once()
        get_access_token_mock.assert_called_once_with(user.id)
        get_users_mock.assert_called_once_with(access_token)
        get_user_profile_email_mock.assert_called_once_with(user_profile)
        get_user_photo_mock.assert_called_once_with(
            access_token=access_token,
            user_id=user_profile['id'],
        )
        google_contact.refresh_from_db()
        assert google_contact.status == UserStatus.ACTIVE
        ms_contact.refresh_from_db()
        assert ms_contact.status == UserStatus.ACTIVE
        assert Contact.objects.filter(
            account=user.account,
            user_id=user.id,
            source=SourceType.MICROSOFT,
            email=user_profile['mail'],
            photo=photo_url,
            first_name='login',
            last_name=None,
            job_title=None,
            source_id=user_profile['id'],
        )

    def test_update_user_contacts__update_contact__ok(self, mocker):

        # arrange
        user = create_test_user()
        email = 'test_1@test.test'
        contact = Contact.objects.create(
            account=user.account,
            user_id=user.id,
            source=SourceType.MICROSOFT,
            email=email,
            photo=None,
            first_name='',
            last_name='',
            job_title=None,
            source_id='1djk2d3qwe',
        )

        client_mock = mocker.Mock()
        get_auth_client_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        access_token = '!@#!@#@!wqww23'
        get_access_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_access_token',
            return_value=access_token
        )
        user_profile = {
            'id': '111',
            'mail': email,
            'givenName': 'first name',
            'surname': 'last name',
            'jobTitle': 'job_title',
        }
        get_users_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_users',
            return_value={
                '@odata.context': (
                    'https://graph.microsoft.com/v1.0/$metadata'
                    '#users(id,givenName,surname,jobTitle,mail)'
                ),
                'value': [
                    user_profile
                ]
            }
        )
        get_user_profile_email_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_user_profile_email',
            return_value=user_profile['mail']
        )
        photo_url = 'https://test.image.com'
        get_user_photo_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_user_photo',
            return_value=photo_url
        )
        service = MicrosoftAuthService()

        # act
        service.update_user_contacts(user)

        # assert
        get_auth_client_mock.assert_called_once()
        get_access_token_mock.assert_called_once_with(user.id)
        get_users_mock.assert_called_once_with(access_token)
        get_user_profile_email_mock.assert_called_once_with(user_profile)
        get_user_photo_mock.assert_called_once_with(
            access_token=access_token,
            user_id=user_profile['id'],
        )
        contact.refresh_from_db()
        assert contact.photo == photo_url
        assert contact.first_name == user_profile['givenName']
        assert contact.last_name == user_profile['surname']
        assert contact.job_title == user_profile['jobTitle']
        assert contact.source_id == user_profile['id']

    def test_update_user_contacts__email_not_found__skip(self, mocker):

        # arrange
        user = create_test_user()
        client_mock = mocker.Mock()
        get_auth_client_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        access_token = '!@#!@#@!wqww23'
        get_access_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_access_token',
            return_value=access_token
        )
        user_profile = mocker.Mock()
        get_users_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_users',
            return_value={
                '@odata.context': (
                    'https://graph.microsoft.com/v1.0/$metadata'
                    '#users(id,givenName,surname,jobTitle,mail)'
                ),
                'value': [
                    user_profile
                ]
            }
        )
        get_user_profile_email_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_user_profile_email',
            return_value=None
        )
        get_user_photo_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_user_photo'
        )
        google_contact = Contact.objects.create(
            account=user.account,
            user_id=user.id,
            source=SourceType.GOOGLE,
            email='test@test.test'
        )
        ms_contact = Contact.objects.create(
            account=user.account,
            user_id=user.id,
            source=SourceType.MICROSOFT,
            email='test@test.test'
        )
        service = MicrosoftAuthService()

        # act
        service.update_user_contacts(user)

        # assert
        get_auth_client_mock.assert_called_once()
        get_access_token_mock.assert_called_once_with(user.id)
        get_users_mock.assert_called_once_with(access_token)
        get_user_profile_email_mock.assert_called_once_with(user_profile)
        get_user_photo_mock.assert_not_called()
        google_contact.refresh_from_db()
        assert google_contact.status == UserStatus.ACTIVE
        ms_contact.refresh_from_db()
        assert ms_contact.status == UserStatus.ACTIVE

    def test_update_user_contacts__exclude_current_user__ok(self, mocker):

        # arrange
        user = create_test_user()
        client_mock = mocker.Mock()
        get_auth_client_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._build_msal_app',
            return_value=client_mock
        )
        access_token = '!@#!@#@!wqww23'
        get_access_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_access_token',
            return_value=access_token
        )
        user_profile = {
            'mail': user.email,
        }
        get_users_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_users',
            return_value={
                '@odata.context': (
                    'https://graph.microsoft.com/v1.0/$metadata'
                    '#users(id,givenName,surname,jobTitle,mail)'
                ),
                'value': [
                    user_profile
                ]
            }
        )
        get_user_profile_email_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_user_profile_email',
            return_value=user.email
        )
        get_user_photo_mock = mocker.patch(
            'pneumatic_backend.authentication.services.microsoft.'
            'MicrosoftAuthService._get_user_photo'
        )
        service = MicrosoftAuthService()

        # act
        service.update_user_contacts(user)

        # assert
        get_auth_client_mock.assert_called_once()
        get_access_token_mock.assert_called_once_with(user.id)
        get_users_mock.assert_called_once_with(access_token)
        get_user_profile_email_mock.assert_called_once_with(user_profile)
        get_user_photo_mock.assert_not_called()
        assert not Contact.objects.filter(
            account=user.account,
            user_id=user.id,
            source=SourceType.MICROSOFT,
            email=user.email,
        ).exists()
