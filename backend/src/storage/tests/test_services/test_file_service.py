import pytest
from unittest.mock import Mock

from src.processes.tests.fixtures import (
    create_test_account,
    create_test_user,
)
from src.storage.enums import AccessType, SourceType
from src.storage import messages as fs_messages
from src.storage.services.exceptions import (
    FileServiceAuthException,
    FileServiceAuthFailedException,
    FileSizeExceededException,
    FileUploadException,
    FileUploadInvalidResponseException,
    FileUploadNoFileIdException,
    FileUploadParseErrorException,
    InvalidFileTypeException,
)
from src.storage.services.file_service import FileServiceClient

pytestmark = pytest.mark.django_db


class TestFileServiceClient:
    def test_get_auth_headers__no_user__raises_exception(self, mocker):
        # arrange
        mock_settings = mocker.patch(
            'src.storage.services.file_service.settings',
        )
        mock_settings.FILE_SERVICE_URL = 'https://files.test.com'
        client = FileServiceClient()

        # act
        with pytest.raises(FileServiceAuthException) as ex:
            client._get_auth_headers()

        # assert
        assert ex.value.message == fs_messages.MSG_FS_0003

    def test_get_user_token__no_request__creates_new_token(self, mocker):
        # arrange
        mock_settings = mocker.patch(
            'src.storage.services.file_service.settings',
        )
        mock_settings.FILE_SERVICE_URL = 'https://files.test.com'

        mock_token = mocker.patch(
            'src.storage.services.file_service.PneumaticToken',
        )
        mock_token.create.return_value = 'new_token_123'

        user = create_test_user()
        client = FileServiceClient(user=user)

        # act
        token = client._get_user_token()

        # assert
        assert token == 'new_token_123'
        mock_token.create.assert_called_once_with(
            user=user,
            user_agent='FileServiceClient',
            for_api_key=True,
        )

    def test_get_user_token__valid_request_token__uses_existing(self, mocker):
        # arrange
        mock_settings = mocker.patch(
            'src.storage.services.file_service.settings',
        )
        mock_settings.FILE_SERVICE_URL = 'https://files.test.com'

        mock_token = mocker.patch(
            'src.storage.services.file_service.PneumaticToken',
        )
        mock_get_auth_header = mocker.patch(
            'src.storage.services.file_service.get_authorization_header',
        )

        user = create_test_user()
        request = Mock()
        client = FileServiceClient(user=user, request=request)

        mock_get_auth_header.return_value = b'Bearer existing_token_456'
        mock_token.data.return_value = {'user_id': user.id}

        # act
        token = client._get_user_token()

        # assert
        assert token == 'existing_token_456'
        mock_token.data.assert_called_once_with('existing_token_456')
        mock_token.create.assert_not_called()

    def test_get_user_token__request_no_bearer__creates_new_token(
        self,
        mocker,
    ):
        # arrange
        mock_settings = mocker.patch(
            'src.storage.services.file_service.settings',
        )
        mock_settings.FILE_SERVICE_URL = 'https://files.test.com'
        mock_get_auth = mocker.patch(
            'src.storage.services.file_service.get_authorization_header',
        )
        mock_get_auth.return_value = b''
        mock_token = mocker.patch(
            'src.storage.services.file_service.PneumaticToken',
        )
        mock_token.create.return_value = 'new_token'
        user = create_test_user()
        request = Mock()
        client = FileServiceClient(user=user, request=request)

        # act
        token = client._get_user_token()

        # assert
        assert token == 'new_token'
        mock_token.create.assert_called_once_with(
            user=user,
            user_agent='FileServiceClient',
            for_api_key=True,
        )

    def test_get_user_token__request_invalid_token__creates_new_token(
        self,
        mocker,
    ):
        # arrange
        mock_settings = mocker.patch(
            'src.storage.services.file_service.settings',
        )
        mock_settings.FILE_SERVICE_URL = 'https://files.test.com'
        mock_get_auth = mocker.patch(
            'src.storage.services.file_service.get_authorization_header',
        )
        mock_get_auth.return_value = b'Bearer invalid_token'
        mock_token = mocker.patch(
            'src.storage.services.file_service.PneumaticToken',
        )
        mock_token.data.return_value = None
        mock_token.create.return_value = 'new_token'
        user = create_test_user()
        request = Mock()
        client = FileServiceClient(user=user, request=request)

        # act
        token = client._get_user_token()

        # assert
        assert token == 'new_token'
        mock_token.data.assert_called_once_with('invalid_token')
        mock_token.create.assert_called_once_with(
            user=user,
            user_agent='FileServiceClient',
            for_api_key=True,
        )

    def test_make_request__status_401__raises_auth_failed(self, mocker):
        # arrange
        mock_settings = mocker.patch(
            'src.storage.services.file_service.settings',
        )
        mock_settings.FILE_SERVICE_URL = 'https://files.test.com'
        mock_requests = mocker.patch(
            'src.storage.services.file_service.requests',
        )
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        mock_requests.request.return_value = mock_response
        user = create_test_user()
        client = FileServiceClient(user=user)
        mocker.patch.object(client, '_get_auth_headers', return_value={})

        # act
        with pytest.raises(FileServiceAuthFailedException) as ex:
            client._make_request('GET', '/test')

        # assert
        assert ex.value.message == fs_messages.MSG_FS_0004

    def test_make_request__status_413__raises_file_size_exceeded(
        self,
        mocker,
    ):
        # arrange
        mock_settings = mocker.patch(
            'src.storage.services.file_service.settings',
        )
        mock_settings.FILE_SERVICE_URL = 'https://files.test.com'
        mock_requests = mocker.patch(
            'src.storage.services.file_service.requests',
        )
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 413
        mock_response.text = 'Too Large'
        mock_requests.request.return_value = mock_response
        user = create_test_user()
        client = FileServiceClient(user=user)
        mocker.patch.object(client, '_get_auth_headers', return_value={})

        # act
        with pytest.raises(FileSizeExceededException) as ex:
            client._make_request('POST', '/upload')

        # assert
        assert ex.value.message == fs_messages.MSG_FS_0005

    def test_make_request__status_415__raises_invalid_file_type(self, mocker):
        # arrange
        mock_settings = mocker.patch(
            'src.storage.services.file_service.settings',
        )
        mock_settings.FILE_SERVICE_URL = 'https://files.test.com'
        mock_requests = mocker.patch(
            'src.storage.services.file_service.requests',
        )
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 415
        mock_response.text = 'Unsupported Media Type'
        mock_requests.request.return_value = mock_response
        user = create_test_user()
        client = FileServiceClient(user=user)
        mocker.patch.object(client, '_get_auth_headers', return_value={})

        # act
        with pytest.raises(InvalidFileTypeException) as ex:
            client._make_request('POST', '/upload')

        # assert
        assert ex.value.message == fs_messages.MSG_FS_0006

    def test_make_request__status_500__raises_file_upload_exception(
        self,
        mocker,
    ):
        # arrange
        mock_settings = mocker.patch(
            'src.storage.services.file_service.settings',
        )
        mock_settings.FILE_SERVICE_URL = 'https://files.test.com'
        mock_requests = mocker.patch(
            'src.storage.services.file_service.requests',
        )
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_requests.request.return_value = mock_response
        user = create_test_user()
        client = FileServiceClient(user=user)
        mocker.patch.object(client, '_get_auth_headers', return_value={})

        # act
        with pytest.raises(FileUploadException) as ex:
            client._make_request('GET', '/test')

        # assert
        assert ex.value.message == fs_messages.MSG_FS_0007

    def test_upload_file_with_attachment__success__creates_attachment(
            self,
            mocker,
    ):
        # arrange
        mock_settings = mocker.patch(
            'src.storage.services.file_service.settings',
        )
        mock_settings.FILE_SERVICE_URL = 'https://files.test.com'
        mock_requests = mocker.patch(
            'src.storage.services.file_service.requests',
        )
        mock_token = mocker.patch(
            'src.storage.services.file_service.PneumaticToken',
        )
        mock_extract = mocker.patch(
            'src.storage.utils.extract_file_ids_from_text',
        )
        mock_attachment_service_class = mocker.patch(
            'src.storage.services.file_service.AttachmentService',
        )

        user = create_test_user()
        client = FileServiceClient(user=user)

        mock_token.create.return_value = 'test_token'

        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'public_url': 'https://files.pneumatic.app/test_file_123',
            'file_id': 'test_file_123',
        }
        mock_requests.request.return_value = mock_response
        mock_extract.return_value = ['test_file_123']

        mock_attachment_service = Mock()
        mock_attachment_service_class.return_value = mock_attachment_service

        # act
        public_url = client.upload_file_with_attachment(
            file_content=b'test content',
            filename='test.txt',
            content_type='text/plain',
            account=user.account,
        )

        # assert
        assert public_url == 'https://files.pneumatic.app/test_file_123'
        mock_attachment_service_class.assert_called_once_with(user=user)
        mock_attachment_service.create.assert_called_once_with(
            file_id='test_file_123',
            account=user.account,
            source_type=SourceType.ACCOUNT,
            access_type=AccessType.ACCOUNT,
        )

    def test_upload_file_with_attachment__custom_params__uses_params(
            self,
            mocker,
    ):
        # arrange
        mock_settings = mocker.patch(
            'src.storage.services.file_service.settings',
        )
        mock_settings.FILE_SERVICE_URL = 'https://files.test.com'

        mock_requests = mocker.patch(
            'src.storage.services.file_service.requests',
        )
        mock_token = mocker.patch(
            'src.storage.services.file_service.PneumaticToken',
        )
        mock_extract = mocker.patch(
            'src.storage.utils.extract_file_ids_from_text',
        )
        mock_attachment_service_class = mocker.patch(
            'src.storage.services.file_service.AttachmentService',
        )

        user = create_test_user()
        account = create_test_account()
        client = FileServiceClient(user=user)

        mock_token.create.return_value = 'test_token'

        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'public_url': 'https://files.pneumatic.app/test_file_456',
            'file_id': 'test_file_456',
        }
        mock_requests.request.return_value = mock_response
        mock_extract.return_value = ['test_file_456']

        mock_attachment_service = Mock()
        mock_attachment_service_class.return_value = mock_attachment_service

        # act
        public_url = client.upload_file_with_attachment(
            file_content=b'test content',
            filename='test.txt',
            content_type='text/plain',
            account=account,
            source_type=SourceType.TEMPLATE,
            access_type=AccessType.RESTRICTED,
        )

        # assert
        assert public_url == 'https://files.pneumatic.app/test_file_456'
        mock_attachment_service.create.assert_called_once_with(
            file_id='test_file_456',
            account=account,
            source_type=SourceType.TEMPLATE,
            access_type=AccessType.RESTRICTED,
        )

    def test_upload_file_with_attachment__no_public_url__invalid_response(
        self, mocker,
    ):
        # arrange
        mock_settings = mocker.patch(
            'src.storage.services.file_service.settings',
        )
        mock_settings.FILE_SERVICE_URL = 'https://files.test.com'
        mock_requests = mocker.patch(
            'src.storage.services.file_service.requests',
        )
        mock_token = mocker.patch(
            'src.storage.services.file_service.PneumaticToken',
        )
        user = create_test_user()
        client = FileServiceClient(user=user)
        mock_token.create.return_value = 'test_token'
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'file_id': 'f123'}
        mock_requests.request.return_value = mock_response

        # act
        with pytest.raises(FileUploadInvalidResponseException) as ex:
            client.upload_file_with_attachment(
                file_content=b'x',
                filename='t.txt',
                content_type='text/plain',
                account=user.account,
            )

        # assert
        assert ex.value.message == fs_messages.MSG_FS_0008

    def test_upload_file_with_attachment__no_file_id__raises_no_file_id(
        self, mocker,
    ):
        # arrange
        mock_settings = mocker.patch(
            'src.storage.services.file_service.settings',
        )
        mock_settings.FILE_SERVICE_URL = 'https://files.test.com'
        mock_requests = mocker.patch(
            'src.storage.services.file_service.requests',
        )
        mock_token = mocker.patch(
            'src.storage.services.file_service.PneumaticToken',
        )
        user = create_test_user()
        client = FileServiceClient(user=user)
        mock_token.create.return_value = 'test_token'
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'public_url': 'https://files.pneumatic.app/f123',
        }
        mock_requests.request.return_value = mock_response

        # act
        with pytest.raises(FileUploadNoFileIdException) as ex:
            client.upload_file_with_attachment(
                file_content=b'x',
                filename='t.txt',
                content_type='text/plain',
                account=user.account,
            )

        # assert
        assert ex.value.message == fs_messages.MSG_FS_0010

    def test_upload_file_with_attachment__json_parse_error__parse_error(
        self, mocker,
    ):
        # arrange
        mock_settings = mocker.patch(
            'src.storage.services.file_service.settings',
        )
        mock_settings.FILE_SERVICE_URL = 'https://files.test.com'
        mock_requests = mocker.patch(
            'src.storage.services.file_service.requests',
        )
        mock_token = mocker.patch(
            'src.storage.services.file_service.PneumaticToken',
        )
        user = create_test_user()
        client = FileServiceClient(user=user)
        mock_token.create.return_value = 'test_token'
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.side_effect = ValueError('Invalid JSON')
        mock_response.text = 'not json'
        mock_requests.request.return_value = mock_response

        # act
        with pytest.raises(FileUploadParseErrorException) as ex:
            client.upload_file_with_attachment(
                file_content=b'x',
                filename='t.txt',
                content_type='text/plain',
                account=user.account,
            )

        # assert
        assert ex.value.message == fs_messages.MSG_FS_0009
