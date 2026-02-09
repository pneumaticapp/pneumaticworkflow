import io
from typing import Optional

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import get_authorization_header

from src.accounts.models import Account
from src.authentication.tokens import PneumaticToken
from src.storage.enums import AccessType, SourceType
from src.storage.services.attachments import AttachmentService
from src.storage.services.exceptions import (
    FileServiceAuthException,
    FileServiceAuthFailedException,
    FileServiceConnectionException,
    FileServiceConnectionFailedException,
    FileUploadException,
    FileUploadInvalidResponseException,
    FileUploadNoFileIdException,
    FileUploadParseErrorException,
    FileSizeExceededException,
    InvalidFileTypeException,
)
from src.utils.logging import (
    SentryLogLevel,
    capture_sentry_message,
)

UserModel = get_user_model()


class FileServiceClient:
    """
    Client for integration with the file microservice (FastAPI).
    Handles file uploads via REST API.
    """

    def __init__(self, user: Optional[UserModel] = None, request=None):
        self.user = user
        self.request = request
        self.base_url = settings.FILES_BASE_URL
        if not self.base_url:
            raise FileServiceConnectionException

    def _get_auth_headers(self) -> dict:
        """Return authentication headers for requests."""
        if not self.user:
            raise FileServiceAuthException
        token = self._get_user_token()
        return {
            'Authorization': f'Bearer {token}',
        }

    def _get_user_token(self) -> str:
        """Get user token from request or create a new one."""
        # Try to get token from current request
        if self.request:
            auth_header = get_authorization_header(self.request).decode()
            auth_header_parts = auth_header.split()
            if (
                len(auth_header_parts) == 2
                and auth_header_parts[0].lower() == 'bearer'
            ):
                token = auth_header_parts[1]
                # Verify token is valid in cache
                token_data = PneumaticToken.data(token)
                if token_data:
                    return token

        # Token is created with settings.SECRET_KEY (same DJANGO_SECRET_KEY
        # as in file service when using shared config).
        return PneumaticToken.create(
            user=self.user,
            user_agent='FileServiceClient',
            for_api_key=True,  # Long-lived token for API
        )

    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> requests.Response:
        """Perform HTTP request to the file service."""
        url = f'{self.base_url.rstrip("/")}/{endpoint.lstrip("/")}'
        headers = kwargs.pop('headers', {})

        if self.user:
            headers.update(self._get_auth_headers())

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=30,
                **kwargs,
            )
        except requests.exceptions.RequestException as ex:
            capture_sentry_message(
                message='File service connection error',
                data={
                    'url': url,
                    'method': method,
                    'error': str(ex),
                },
                level=SentryLogLevel.ERROR,
            )
            raise FileServiceConnectionFailedException from ex

        if not response.ok:
            error_data = {
                'url': url,
                'method': method,
                'status_code': response.status_code,
                'response_text': response.text[:1000],
            }

            if response.status_code == 401:
                capture_sentry_message(
                    message='File service authentication error',
                    data=error_data,
                    level=SentryLogLevel.ERROR,
                )
                raise FileServiceAuthFailedException
            if response.status_code == 413:
                raise FileSizeExceededException
            if response.status_code == 415:
                raise InvalidFileTypeException
            capture_sentry_message(
                message='File service request error',
                data=error_data,
                level=SentryLogLevel.ERROR,
            )
            raise FileUploadException

        return response

    def check_file_permission(
        self,
        file_id: str,
        user_id: int,
    ) -> bool:
        """
        Check file access permission.

        Args:
            file_id: File identifier
            user_id: User ID

        Returns:
            bool: True if access is allowed
        """
        try:
            response = self._make_request(
                method='GET',
                endpoint=f'/check-permission/{file_id}',
                params={'user_id': user_id},
            )

            response_data = response.json()
            return response_data.get('has_access', False)

        except requests.RequestException as ex:
            capture_sentry_message(
                message='File permission check failed',
                data={
                    'file_id': file_id,
                    'user_id': user_id,
                    'error': str(ex),
                },
                level=SentryLogLevel.WARNING,
            )
            # Deny access on error for security
            return False

    def upload_file_with_attachment(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        account: Account,
        source_type: str = SourceType.ACCOUNT,
        access_type: str = AccessType.ACCOUNT,
    ) -> str:
        """
        Upload file and create Attachment with access permissions.

        Args:
            file_content: File content in bytes
            filename: File name
            content_type: File MIME type
            account: Account
            source_type: File source type
            access_type: File access type

        Returns:
            public_url: URL for public access to the file

        Raises:
            FileUploadException: On upload error
            FileServiceConnectionException: On connection error
            FileServiceAuthException: On authentication error
        """
        # Prepare file for multipart/form-data
        file_obj = io.BytesIO(file_content)
        files = {
            'file': (filename, file_obj, content_type),
        }

        try:
            response = self._make_request(
                method='POST',
                endpoint='/upload',
                files=files,
            )

            response_data = response.json()
            public_url = response_data.get('public_url')
            file_id = response_data.get('file_id')
            if not public_url:
                capture_sentry_message(
                    message='File service returned invalid response',
                    data={
                        'response_data': response_data,
                        'filename': filename,
                    },
                    level=SentryLogLevel.ERROR,
                )
                raise FileUploadInvalidResponseException

            if not file_id:
                capture_sentry_message(
                    message='File service did not return file_id',
                    data={
                        'response_data': response_data,
                        'filename': filename,
                    },
                    level=SentryLogLevel.ERROR,
                )
                raise FileUploadNoFileIdException

        except (ValueError, KeyError) as ex:
            capture_sentry_message(
                message='File service response parsing error',
                data={
                    'response_text': response.text[:1000],
                    'filename': filename,
                    'error': str(ex),
                },
                level=SentryLogLevel.ERROR,
            )
            raise FileUploadParseErrorException from ex
        finally:
            file_obj.close()

        # Create Attachment with access permissions
        attachment_service = AttachmentService(user=self.user)
        attachment_service.create(
            file_id=file_id,
            account=account,
            source_type=source_type,
            access_type=access_type,
        )
        return public_url
