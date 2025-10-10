from typing import Optional, Tuple
from urllib.parse import unquote

from django.contrib.auth import get_user_model

from src.accounts.models import Account
from src.analytics.services import AnalyticService
from src.authentication.enums import AuthTokenType
from src.processes.services import exceptions
from src.processes.models import FileAttachment
from src.storage.google_cloud import GoogleCloudService
from src.utils.logging import (
    capture_sentry_message,
    SentryLogLevel,
)
from src.utils.salt import get_salt


UserModel = get_user_model()


class AttachmentService:
    def __init__(self, account: Account = None):
        self.account = account

    def _get_cloud_service(self):
        return GoogleCloudService(account=self.account)

    def _get_new_file_urls(
        self,
        filename: str,
        content_type: str,
    ) -> Tuple[str, str]:

        try:
            cloud_service = self._get_cloud_service()
            upload_url, public_url = cloud_service.get_new_file_urls(
                filename=filename,
                content_type=content_type
            )
        except Exception as ex:
            capture_sentry_message(
                message='Cloud service: get_new_file_urls exception',
                data={'message': str(ex)},
                level=SentryLogLevel.ERROR
            )
            raise exceptions.CloudServiceException() from ex
        return upload_url, public_url

    def _publish_file(self, url: str):
        try:
            cloud_service = self._get_cloud_service()
            filename = url.split('/')[-1]
            filename = unquote(filename)
            file_blob = cloud_service.make_public(filename)
        except Exception as ex:
            capture_sentry_message(
                message='Cloud service: make_public exception',
                data={'message': str(ex)},
                level=SentryLogLevel.ERROR
            )
            raise exceptions.CloudServiceException() from ex
        else:
            if not file_blob:
                raise exceptions.AttachmentEmptyBlobException()

    def _create_attachment(
        self,
        name: str,
        url: str,
        size: int,
        thumbnail_url: str = None,
    ) -> FileAttachment:

        return FileAttachment.objects.create(
            name=name,
            url=url,
            thumbnail_url=thumbnail_url,
            size=size,
            account_id=self.account.id,
        )

    def _get_unique_filename(self, origin_filename: str) -> str:
        return f'{get_salt(30)}_{origin_filename}'

    def create(
        self,
        filename: str,
        content_type: str,
        size: int,
        thumbnail: bool = False,
    ) -> Tuple[FileAttachment, str, Optional[str]]:

        """ size - file size in bytes """
        unique_filename = self._get_unique_filename(filename)
        upload_url, public_url = self._get_new_file_urls(
            filename=unique_filename,
            content_type=content_type
        )
        if thumbnail:
            thumb_upload_url, thumb_public_url = self._get_new_file_urls(
                filename=f'thumb_{unique_filename}',
                content_type=content_type
            )
        else:
            thumb_upload_url, thumb_public_url = None, None
        attachment = self._create_attachment(
            url=public_url,
            thumbnail_url=thumb_public_url,
            name=filename,
            size=size,
        )
        return attachment, upload_url, thumb_upload_url

    def publish(
        self,
        attachment: FileAttachment,
        auth_type: AuthTokenType,
        request_user: Optional[UserModel] = None,
        anonymous_id: Optional[str] = None,
        is_superuser: bool = False,
    ):
        self._publish_file(url=attachment.url)
        if attachment.thumbnail_url:
            self._publish_file(url=attachment.thumbnail_url)

        AnalyticService.attachments_uploaded(
            attachment=attachment,
            user=request_user,
            anonymous_id=anonymous_id,
            is_superuser=is_superuser,
            auth_type=auth_type
        )

    def create_clone(
        self,
        instance: FileAttachment,
        orphan: bool = True,
    ) -> FileAttachment:

        clone = FileAttachment(
            account=instance.account,
            name=instance.name,
            url=instance.url,
            thumbnail_url=instance.thumbnail_url,
            size=instance.size
        )
        if not orphan:
            clone.workflow = instance.workflow
            clone.output = instance.output
        clone.save()
        return clone
