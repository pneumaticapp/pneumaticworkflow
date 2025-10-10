from datetime import timedelta
import os
from typing import Optional
import re

from django.conf import settings
from google.cloud import storage
from google.cloud import exceptions as gcloud_exceptions

from src.accounts.models import Account
from src.accounts.services.account import AccountService
from src.utils.salt import get_salt
from src.utils.logging import (
    capture_sentry_message,
    SentryLogLevel,
)
from src.processes.services import exceptions
from google.cloud.storage.blob import _quote


configuration = os.getenv('ENVIRONMENT', 'development').title()
# TODO Remove file in https://my.pneumatic.app/workflows/41526


class GoogleCloudService:

    """ Vars:
      - GOOGLE_APPLICATION_CREDENTIALS
      - GCLOUD_DEFAULT_BUCKET_NAME """

    AUTHENTICATED_URL = 'https://storage.cloud.google.com'
    PUBLIC_URL = 'https://storage.googleapis.com'

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    def __init__(self, account: Optional[Account] = None):
        self.account = account
        self.client = storage.Client()
        if account:
            if account.bucket_name:
                try:
                    self.bucket = (
                        self.client.get_bucket(account.bucket_name)
                    )
                except gcloud_exceptions.NotFound:
                    self.bucket = self._create_bucket(
                        bucket_name=account.bucket_name
                    )
            else:
                self.bucket = self._create_bucket()
        else:
            try:
                self.bucket = self.client.get_bucket(
                    settings.GCLOUD_DEFAULT_BUCKET_NAME
                )
            except gcloud_exceptions.NotFound:
                self.bucket = self._create_bucket(
                    bucket_name=settings.GCLOUD_DEFAULT_BUCKET_NAME
                )

    def get_normalized_name(self, text: str) -> str:
        """
        Format text according to GCS requirements:
        - only lowercase letters, numbers, '_', '-'
        - spaces are replaced with '_'
        - the maximum length is 62 characters
        """
        formatted_text = text.lower().replace(' ', '_')
        formatted_text = re.sub(r'[^a-z0-9_-]', '', formatted_text)
        formatted_text = formatted_text[:62]
        return formatted_text

    def _create_bucket(self, bucket_name: str = None):
        if not bucket_name:
            salt = get_salt(length=16, exclude=('upper',))
            if configuration == settings.CONFIGURATION_PROD:
                bucket_name = f'{self.account.id}_{salt}'
            else:
                bucket_name = f'dev_{self.account.id}_{salt}'
        cors_rule = [
            {
                "origin": ["*"],
                "method": ["GET"],
                "responseHeader": ["Content-Type"],
                "maxAgeSeconds": 3600
            },
            {
                "origin": ["*"],
                "method": ["PUT"],
                "responseHeader": [
                    "Content-Type",
                    "Access-Control-Allow-Origin"
                ],
                "maxAgeSeconds": 300
            }
        ]
        try:
            bucket = self.client.bucket(bucket_name)
            bucket.create()
            if self.account:
                formatted_label_name = self.get_normalized_name(
                    self.account.name)
                bucket.labels = {
                    'account_id': str(self.account.id),
                    'account_name': formatted_label_name
                }
            bucket.cors = cors_rule
            bucket.patch()
        except gcloud_exceptions.GoogleCloudError as ex:
            capture_sentry_message(
                message='Cloud service: bucket creation, '
                        'CORS/labels configuration failed',
                data={'message': str(ex)},
                level=SentryLogLevel.ERROR
            )
            raise exceptions.CloudServiceException() from ex
        if self.account:
            account_service = AccountService(
                user=self.account.get_owner(),
                instance=self.account
            )
            account_service.update_bucket_name(bucket_name)
        return bucket

    @property
    def authenticated_bucket_path(self):
        return f'{self.AUTHENTICATED_URL}/{self.account.bucket_name}'

    @property
    def public_bucket_path(self):
        return f'{self.PUBLIC_URL}/{self.account.bucket_name}'

    def get_authenticated_url(self, filename: str):
        quoted_name = _quote(filename, safe=b"/~")
        return f"{self.authenticated_bucket_path}/{quoted_name}"

    def get_public_url(self, filename: str):
        quoted_name = _quote(filename, safe=b"/~")
        return f"{self.public_bucket_path}/{quoted_name}"

    def get_new_file_urls(self, filename: str, content_type: str):
        blob = self.bucket.blob(filename)
        signed_url = blob.generate_signed_url(
            expiration=timedelta(
                minutes=settings.ATTACHMENT_SIGNED_URL_LIFETIME_MIN
            ),
            method='PUT',
            content_type=content_type,
        )
        if self.account.bucket_is_public:
            return signed_url, blob.public_url
        else:

            return signed_url, self.get_authenticated_url(filename)

    def make_public(self, filename: str):
        if not self.account.bucket_is_public:
            # Skip publicate request, temporary solution
            return True
        blob = self.bucket.get_blob(filename)
        if blob:
            blob.make_public()
            return True
        return False

    def upload_from_binary(
        self,
        binary: bytes,
        filepath: str,
        content_type: str,
    ) -> str:

        """ filepath - full path in the bucket. Filename with extension """

        blob = self.bucket.blob(filepath)
        blob.upload_from_string(data=binary, content_type=content_type)
        blob.make_public()
        return blob.public_url
