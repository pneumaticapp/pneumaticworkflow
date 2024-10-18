from datetime import timedelta
from django.utils.functional import cached_property
from google.cloud import storage
from django.conf import settings


class GoogleCloudService:

    """ Vars:
      - GOOGLE_APPLICATION_CREDENTIALS
      - GCLOUD_BUCKET_NAME """

    def __init__(self):
        self.client = storage.Client()

    @cached_property
    def bucket(self):
        return self.client.get_bucket(settings.GCLOUD_BUCKET_NAME)

    def get_new_file_urls(self, filename: str, content_type: str):
        blob = self.bucket.blob(filename)
        signed_url = blob.generate_signed_url(
            expiration=timedelta(
                minutes=settings.ATTACHMENT_SIGNED_URL_LIFETIME_MIN
            ),
            method='PUT',
            content_type=content_type,
        )
        return signed_url, blob.public_url

    def make_public(self, filename: str):
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
