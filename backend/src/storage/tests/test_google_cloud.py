import pytest

from src.storage.google_cloud import GoogleCloudService
from src.processes.tests.fixtures import create_test_account
from google.cloud.exceptions import NotFound

pytestmark = pytest.mark.django_db


class TestGoogleCloudService:
    def test_init__without_account__ok(self, mocker, settings):
        # arrange
        settings.GCLOUD_DEFAULT_BUCKET_NAME = 'default-bucket'
        bucket_mock = mocker.Mock()
        client_mock = mocker.Mock()
        client_mock.get_bucket = mocker.Mock(return_value=bucket_mock)
        mocker.patch(
            'src.storage.google_cloud.storage.Client',
            return_value=client_mock,
        )

        # act
        service = GoogleCloudService()

        # assert
        client_mock.get_bucket.assert_called_once_with('default-bucket')
        assert service.account is None
        assert service.bucket == bucket_mock

    def test_init__with_existing_bucket__ok(self, mocker):
        # arrange
        account = create_test_account()
        account.bucket_name = 'existing-bucket'
        bucket_mock = mocker.Mock()
        client_mock = mocker.Mock()
        client_mock.get_bucket = mocker.Mock(return_value=bucket_mock)
        mocker.patch(
            'src.storage.google_cloud.storage.Client',
            return_value=client_mock,
        )

        # act
        service = GoogleCloudService(account=account)

        # assert
        client_mock.get_bucket.assert_called_once_with('existing-bucket')
        assert service.account == account
        assert service.bucket == bucket_mock

    def test_init__create_bucket__ok(self, mocker):
        # arrange
        account = create_test_account()
        account.bucket_name = None
        bucket_mock = mocker.Mock()
        client_mock = mocker.Mock()
        mocker.patch(
            'src.storage.google_cloud.storage.Client',
            return_value=client_mock,
        )
        create_bucket_mock = mocker.patch(
            'src.storage.google_cloud.GoogleCloudService.'
            '_create_bucket',
            return_value=bucket_mock,
        )

        # act
        service = GoogleCloudService(account=account)

        # assert
        create_bucket_mock.assert_called_once_with()
        assert service.account == account
        assert service.bucket == bucket_mock

    def test_init__with_account_no_bucket__ok(self, mocker):
        # arrange
        account = create_test_account()
        account.bucket_name = None
        bucket_mock = mocker.Mock()
        client_mock = mocker.Mock()
        client_mock.bucket = mocker.Mock(return_value=bucket_mock)

        mocker.patch(
            'src.storage.google_cloud.storage.Client',
            return_value=client_mock,
        )
        mocker.patch(
            'src.storage.google_cloud.get_salt',
            return_value='salt',
        )
        mocker.patch(
            'src.storage.google_cloud.AccountService',
            return_value=mocker.Mock(),
        )

        # act
        service = GoogleCloudService(account=account)

        # assert
        expected_bucket_name = f'dev_{account.id}_salt'
        client_mock.bucket.assert_called_once_with(expected_bucket_name)
        assert service.bucket == bucket_mock

    def test_init__with_nonexistent_bucket__ok(self, mocker):
        # arrange
        account = create_test_account()
        account.bucket_name = 'non-existent-bucket'
        bucket_mock = mocker.Mock()
        client_mock = mocker.Mock()
        client_mock.get_bucket = mocker.Mock(
            side_effect=NotFound('Bucket not found'),
        )
        mocker.patch(
            'src.storage.google_cloud.storage.Client',
            return_value=client_mock,
        )
        create_bucket_mock = mocker.patch(
            'src.storage.google_cloud.GoogleCloudService.'
            '_create_bucket',
            return_value=bucket_mock,
        )

        # act
        service = GoogleCloudService(account=account)

        # assert
        client_mock.get_bucket.assert_called_once_with('non-existent-bucket')
        create_bucket_mock.assert_called_once_with(
            bucket_name='non-existent-bucket',
        )
        assert service.account == account
        assert service.bucket == bucket_mock

    def test_init__without_account_default_bucket_not_found__ok(
        self, mocker, settings,
    ):
        # arrange
        settings.GCLOUD_DEFAULT_BUCKET_NAME = 'default-bucket'
        bucket_mock = mocker.Mock()
        client_mock = mocker.Mock()
        client_mock.get_bucket = mocker.Mock(
            side_effect=NotFound('Bucket not found'),
        )
        mocker.patch(
            'src.storage.google_cloud.storage.Client',
            return_value=client_mock,
        )
        create_bucket_mock = mocker.patch(
            'src.storage.google_cloud.GoogleCloudService.'
            '_create_bucket',
            return_value=bucket_mock,
        )

        # act
        service = GoogleCloudService()

        # assert
        client_mock.get_bucket.assert_called_once_with('default-bucket')
        create_bucket_mock.assert_called_once_with(
            bucket_name='default-bucket',
        )
        assert service.account is None
        assert service.bucket == bucket_mock

    def test_create_bucket__ok(self, mocker):
        # arrange
        account = create_test_account()
        account.bucket_name = None

        bucket_mock = mocker.Mock()
        client_mock = mocker.Mock()
        client_mock.bucket = mocker.Mock(return_value=bucket_mock)
        account_service_mock = mocker.Mock()
        mocker.patch.object(
            GoogleCloudService,
            '__init__',
            return_value=None,
        )
        service = GoogleCloudService()
        service.account = account
        service.client = client_mock
        mocker.patch(
            'src.storage.google_cloud.AccountService',
            return_value=account_service_mock,
        )
        mocker.patch(
            'src.storage.google_cloud.storage.Client',
            return_value=client_mock,
        )
        mocker.patch(
            'src.storage.google_cloud.get_salt',
            return_value='salt',
        )

        # act
        service._create_bucket()

        # assert
        expected_bucket_name = f'dev_{account.id}_salt'
        client_mock.bucket.assert_called_once_with(expected_bucket_name)
        assert bucket_mock.labels == {
            'account_id': str(account.id),
            'account_name': 'test_company',
        }
        bucket_mock.create.assert_called_once()
        account_service_mock.update_bucket_name.assert_called_once_with(
            expected_bucket_name,
        )

    def test_create_bucket__with_specified_name__ok(self, mocker):
        # arrange
        account = create_test_account()
        specified_bucket_name = 'specified-bucket-name'

        bucket_mock = mocker.Mock()
        client_mock = mocker.Mock()
        client_mock.bucket = mocker.Mock(return_value=bucket_mock)
        account_service_mock = mocker.Mock()

        mocker.patch.object(
            GoogleCloudService,
            '__init__',
            return_value=None,
        )

        service = GoogleCloudService()
        service.account = account
        service.client = client_mock

        mocker.patch(
            'src.storage.google_cloud.AccountService',
            return_value=account_service_mock,
        )

        # act
        result = service._create_bucket(bucket_name=specified_bucket_name)

        # assert
        client_mock.bucket.assert_called_once_with(specified_bucket_name)
        assert bucket_mock.labels == {
            'account_id': str(account.id),
            'account_name': 'test_company',
        }
        bucket_mock.create.assert_called_once()
        account_service_mock.update_bucket_name.assert_called_once_with(
            specified_bucket_name,
        )
        assert result == bucket_mock

    def test_upload_from_binary__ok(self, mocker):

        # arrange
        binary_file = bytes('123456', 'UTF-8')
        filepath = 'filename.svg'
        content_type = 'image/svg+xml'
        public_url = 'http://google.cloud/image.svg'
        blob_mock = mocker.Mock(public_url=public_url)
        bucket_mock = mocker.Mock()
        bucket_mock.blob = mocker.Mock(return_value=blob_mock)
        client_mock = mocker.Mock()
        client_mock.get_bucket = mocker.Mock(return_value=bucket_mock)
        mocker.patch(
            'src.storage.google_cloud.storage.Client',
            return_value=client_mock,
        )
        storage = GoogleCloudService()

        # act
        result = storage.upload_from_binary(
            binary=binary_file,
            filepath=filepath,
            content_type=content_type,
        )

        # assert
        bucket_mock.blob.assert_called_once_with(filepath)
        blob_mock.upload_from_string.assert_called_once_with(
            data=binary_file,
            content_type=content_type,
        )
        blob_mock.make_public.assert_called_once()
        assert result == public_url
