from typing import Tuple, Optional
from pneumatic_backend.utils.salt import get_salt
from pneumatic_backend.processes.models import FileAttachment
from pneumatic_backend.storage.google_cloud import GoogleCloudService
from django.contrib.auth import get_user_model
from urllib.parse import unquote
from pneumatic_backend.analytics.services import AnalyticService
from pneumatic_backend.processes.api_v2.services import exceptions
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.utils.logging import (
    capture_sentry_message,
    SentryLogLevel,
)


UserModel = get_user_model()


class AttachmentService:

    @classmethod
    def _get_cloud_service(cls):
        return GoogleCloudService()

    @classmethod
    def _get_new_file_urls(
        cls,
        filename: str,
        content_type: str
    ) -> Tuple[str, str]:

        try:
            cloud_service = cls._get_cloud_service()
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
            raise exceptions.CloudServiceException()
        return upload_url, public_url

    @classmethod
    def _publish_file(cls, url: str):

        try:
            cloud_service = cls._get_cloud_service()
            filename = url.split('/')[-1]
            filename = unquote(filename)
            file_blob = cloud_service.make_public(filename)
        except Exception as ex:
            capture_sentry_message(
                message='Cloud service: make_public exception',
                data={'message': str(ex)},
                level=SentryLogLevel.ERROR
            )
            raise exceptions.CloudServiceException()
        else:
            if not file_blob:
                raise exceptions.AttachmentEmptyBlobException()

    @classmethod
    def _create_attachment(
        cls,
        name: str,
        url: str,
        size: int,
        account_id: int,
        thumbnail_url: str = None,
    ) -> FileAttachment:

        return FileAttachment.objects.create(
            name=name,
            url=url,
            thumbnail_url=thumbnail_url,
            size=size,
            account_id=account_id
        )

    @classmethod
    def _get_unique_filename(cls, origin_filename: str) -> str:
        return f'{get_salt(30)}_{origin_filename}'

    @classmethod
    def create(
        cls,
        account_id: int,
        filename: str,
        content_type: str,
        size: int,
        thumbnail: bool = False,
    ) -> Tuple[FileAttachment, str, Optional[str]]:

        """ size - file size in bytes """

        unique_filename = cls._get_unique_filename(filename)
        upload_url, public_url = cls._get_new_file_urls(
            filename=unique_filename,
            content_type=content_type
        )
        if thumbnail:
            thumb_upload_url, thumb_public_url = cls._get_new_file_urls(
                filename=f'thumb_{unique_filename}',
                content_type=content_type
            )
        else:
            thumb_upload_url, thumb_public_url = None, None
        attachment = cls._create_attachment(
            url=public_url,
            thumbnail_url=thumb_public_url,
            name=unique_filename,
            size=size,
            account_id=account_id,
        )
        return attachment, upload_url, thumb_upload_url

    @classmethod
    def publish(
        cls,
        attachment: FileAttachment,
        auth_type: AuthTokenType,
        request_user: Optional[UserModel] = None,
        anonymous_id: Optional[str] = None,
        is_superuser: bool = False,
    ):

        cls._publish_file(attachment.url)
        if attachment.thumbnail_url:
            cls._publish_file(attachment.thumbnail_url)

        AnalyticService.attachments_uploaded(
            attachment=attachment,
            user=request_user,
            anonymous_id=anonymous_id,
            is_superuser=is_superuser,
            auth_type=auth_type
        )

    @classmethod
    def create_clone(
        cls,
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
