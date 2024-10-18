from pneumatic_backend.storage.google_cloud import (
    GoogleCloudService
)


def test_upload_from_binary(mocker):

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
        'pneumatic_backend.storage.google_cloud.storage.Client',
        return_value=client_mock
    )
    storage = GoogleCloudService()

    # act
    result = storage.upload_from_binary(
        binary=binary_file,
        filepath=filepath,
        content_type=content_type
    )
    bucket_mock.blob.assert_called_once_with(filepath)
    blob_mock.upload_from_string.assert_called_once_with(
        data=binary_file,
        content_type=content_type
    )
    blob_mock.make_public.assert_called_once()
    assert result == public_url
