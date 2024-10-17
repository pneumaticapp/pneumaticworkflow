import pytest
from django.contrib.auth.models import AnonymousUser
from pneumatic_backend.processes.api_v2.services.attachments import (
    AttachmentService
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.enums import FieldType
from pneumatic_backend.processes.models import (
    FileAttachment,
    TaskField,
)
from pneumatic_backend.processes.api_v2.services import exceptions
from pneumatic_backend.processes.messages import workflow as messages
from pneumatic_backend.storage.google_cloud import GoogleCloudService


pytestmark = pytest.mark.django_db


def test_clone__ok():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1
    )
    task_field = TaskField.objects.create(
        order=1,
        type=FieldType.TEXT,
        name='dropdown',
        task=workflow.tasks.first(),
        value='text',
        workflow=workflow
    )
    attachment = FileAttachment.objects.create(
        name='filename.png',
        size=100,
        url='https://link.to.file.png',
        thumbnail_url='https://thumb.to.file.png',
        account_id=user.account_id,
        workflow=workflow,
        output=task_field
    )

    # act
    clone_attachment = AttachmentService.create_clone(
        instance=attachment,
        orphan=False
    )

    # assert
    assert clone_attachment.account_id == attachment.account_id
    assert clone_attachment.name == attachment.name
    assert clone_attachment.url == attachment.url
    assert clone_attachment.thumbnail_url == attachment.thumbnail_url
    assert clone_attachment.size == attachment.size
    assert clone_attachment.workflow_id == attachment.workflow_id
    assert clone_attachment.output_id == attachment.output_id


def test_clone__orphan__ok():

    # arrange
    user = create_test_user()
    attachment = FileAttachment.objects.create(
        name='filename.png',
        size=100,
        url='https://link.to.file.png',
        thumbnail_url='https://thumb.to.file.png',
        account_id=user.account_id
    )

    # act
    clone_attachment = AttachmentService.create_clone(
        instance=attachment,
        orphan=True
    )

    # assert
    assert clone_attachment.account_id == attachment.account_id
    assert clone_attachment.name == attachment.name
    assert clone_attachment.url == attachment.url
    assert clone_attachment.thumbnail_url == attachment.thumbnail_url
    assert clone_attachment.size == attachment.size
    assert clone_attachment.workflow_id is None
    assert clone_attachment.output_id is None


def test_publish__authenticated_user__ok(mocker):

    # arrange
    user = create_test_user()
    attachment = mocker.Mock(
        url='https://link.to.file.png',
        thumbnail_url=None
    )
    publish_file_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService._publish_file'
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.attachments_uploaded'
    )

    # act
    AttachmentService.publish(
        attachment=attachment,
        auth_type=AuthTokenType.USER,
        request_user=user,
        is_superuser=True
    )

    # assert
    publish_file_mock.assert_called_once_with(attachment.url)
    analytics_mock.assert_called_once_with(
        attachment=attachment,
        user=user,
        anonymous_id=None,
        is_superuser=True,
        auth_type=AuthTokenType.USER
    )


def test_publish__thumbnail__ok(mocker):

    # arrange
    user = create_test_user()
    attachment = mocker.Mock(
        url='https://link.to.file.png',
        thumbnail_url='https://link.thumb.file.png',
    )
    publish_file_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService._publish_file'
    )
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.attachments_uploaded'
    )

    # act
    AttachmentService.publish(
        attachment=attachment,
        auth_type=AuthTokenType.USER,
        request_user=user,
        is_superuser=True
    )

    # assert
    assert publish_file_mock.call_count == 2
    assert publish_file_mock.has_calls([
        mocker.call(attachment.url),
        mocker.call(attachment.thumbnail_url),
    ])


def test_publish__anonymous_user__ok(mocker):

    # arrange
    user = AnonymousUser()
    attachment = mocker.Mock(
        url='https://link.to.file.png',
        thumbnail_url=None
    )
    publish_file_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService._publish_file'
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.attachments_uploaded'
    )
    anonymous_id = 'some id'

    # act
    AttachmentService.publish(
        attachment=attachment,
        auth_type=AuthTokenType.PUBLIC,
        request_user=user,
        anonymous_id=anonymous_id,
        is_superuser=False
    )

    # assert
    publish_file_mock.assert_called_once_with(attachment.url)
    analytics_mock.assert_called_once_with(
        attachment=attachment,
        user=user,
        anonymous_id=anonymous_id,
        is_superuser=False,
        auth_type=AuthTokenType.PUBLIC
    )


def test_create__ok(mocker):

    # arrange
    user = create_test_user()
    upload_url = 'some upload url'
    public_url = 'some public url'
    filename = 'image.png'
    unique_filename = 'unique_image.png'
    content_type = 'image/png'
    size = 215678

    get_unique_filename_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService._get_unique_filename',
        return_value=unique_filename
    )
    get_new_file_urls_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService._get_new_file_urls',
        return_value=(upload_url, public_url)
    )
    attachment = mocker.Mock()
    create_attachment_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService._create_attachment',
        return_value=attachment
    )

    # act
    (
        result_attachment,
        result_upload_url,
        result_thumb_upload_url
    ) = AttachmentService.create(
        user.account_id,
        filename=filename,
        content_type=content_type,
        size=size,
        thumbnail=False
    )

    # assert
    get_unique_filename_mock.assert_called_once_with(filename)
    get_new_file_urls_mock.assert_called_once_with(
        filename=unique_filename,
        content_type=content_type
    )
    create_attachment_mock.assert_called_once_with(
        url=public_url,
        thumbnail_url=None,
        name=unique_filename,
        size=size,
        account_id=user.account_id,
    )
    assert result_attachment == attachment
    assert result_upload_url == upload_url
    assert result_thumb_upload_url is None


def test_create__thumbnail__ok(mocker):

    # arrange
    user = create_test_user()
    upload_url = 'some upload url'
    public_url = 'some public url'
    filename = 'image.png'
    unique_filename = 'unique_image.png'
    content_type = 'image/png'
    size = 215678

    get_unique_filename_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService._get_unique_filename',
        return_value=unique_filename
    )
    get_new_file_urls_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService._get_new_file_urls',
        return_value=(upload_url, public_url)
    )
    attachment = mocker.Mock()
    create_attachment_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService._create_attachment',
        return_value=attachment
    )

    # act
    (
        result_attachment,
        result_upload_url,
        result_thumb_upload_url
    ) = AttachmentService.create(
        user.account_id,
        filename=filename,
        content_type=content_type,
        size=size,
        thumbnail=True
    )

    # assert
    get_unique_filename_mock.assert_called_once_with(filename)
    assert get_new_file_urls_mock.call_count == 2
    assert get_new_file_urls_mock.has_calls([
        mocker.call(
            filename=unique_filename,
            content_type=content_type
        ),
        mocker.call(
            filename=f'thumb_{unique_filename}',
            content_type=content_type
        )
    ])

    create_attachment_mock.assert_called_once_with(
        url=public_url,
        thumbnail_url=public_url,
        name=unique_filename,
        size=size,
        account_id=user.account_id,
    )
    assert result_attachment == attachment
    assert result_upload_url == upload_url
    assert result_thumb_upload_url == upload_url


def test_get_unique_filename__ok(mocker):

    # arrange
    salt = 'salt'
    origin_filename = 'filename'
    get_salt_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.get_salt',
        return_value=salt
    )

    # act
    result = AttachmentService._get_unique_filename(origin_filename)

    # assert
    assert result == f'{salt}_{origin_filename}'
    get_salt_mock.assert_called_once_with(30)


def test_create_attachment__ok():

    # arrange
    user = create_test_user()
    public_url = 'some public url'
    thumb_url = 'some public url'
    filename = 'image.png'
    size = 215678

    # act
    attachment = AttachmentService._create_attachment(
        name=filename,
        url=public_url,
        thumbnail_url=thumb_url,
        size=size,
        account_id=user.account_id
    )

    # assert
    assert attachment.name == filename
    assert attachment.url == public_url
    assert attachment.thumbnail_url == thumb_url
    assert attachment.size == size
    assert attachment.account_id == user.account_id


def test_publish_file__ok(mocker):

    # arrange
    cloud_service = mocker.Mock()
    blob = True
    cloud_service.make_public = mocker.Mock(return_value=blob)
    get_cloud_service_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService._get_cloud_service',
        return_value=cloud_service
    )
    filename = 'filename.png'
    url = f'http://some/{filename}'

    # act
    AttachmentService._publish_file(url)

    # assert
    get_cloud_service_mock.assert_called_once()
    cloud_service.make_public.assert_called_once_with(filename)


def test_publish_file__empty_blob__raise_exception(mocker):

    # arrange
    cloud_service = mocker.Mock()
    blob = None
    cloud_service.make_public = mocker.Mock(return_value=blob)
    get_cloud_service_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService._get_cloud_service',
        return_value=cloud_service
    )
    filename = 'filename.png'
    url = f'http://some/{filename}'

    # act
    with pytest.raises(exceptions.AttachmentEmptyBlobException) as ex:
        AttachmentService._publish_file(url)

    # assert
    get_cloud_service_mock.assert_called_once()
    cloud_service.make_public.assert_called_once_with(filename)
    assert ex.value.message == messages.MSG_PW_0041


def test_publish_file__make_public_exception__raise_exception(mocker):

    # arrange
    cloud_service = mocker.Mock()
    cloud_service.make_public = mocker.Mock(
        side_effect=Exception()
    )
    get_cloud_service_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService._get_cloud_service',
        return_value=cloud_service
    )
    filename = 'filename.png'
    url = f'http://some/{filename}'

    # act
    with pytest.raises(exceptions.CloudServiceException) as ex:
        AttachmentService._publish_file(url)

    # assert
    get_cloud_service_mock.assert_called_once()
    cloud_service.make_public.assert_called_once_with(filename)
    assert ex.value.message == messages.MSG_PW_0040


def test_get_new_file_urls__ok(mocker):

    # arrange
    filename = 'some filename'
    content_type = 'some content_type'
    upload_url = 'some upload url'
    public_url = 'some public url'
    cloud_service = mocker.Mock()
    cloud_service.get_new_file_urls = mocker.Mock(
        return_value=(upload_url, public_url)
    )
    get_cloud_service_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService._get_cloud_service',
        return_value=cloud_service
    )

    # act
    (
        result_upload_url,
        result_public_url
    ) = AttachmentService._get_new_file_urls(
        filename=filename,
        content_type=content_type
    )

    # assert
    get_cloud_service_mock.assert_called_once()
    cloud_service.make_public.get_new_file_urls(
        filename=filename,
        content_type=content_type
    )
    assert result_upload_url == upload_url
    assert result_public_url == public_url


def test_get_new_file_urls__exception__raise_exception(mocker):

    # arrange
    filename = 'some filename'
    content_type = 'some content_type'
    cloud_service = mocker.Mock()
    cloud_service.get_new_file_urls = mocker.Mock(
        side_effect=Exception()
    )
    get_cloud_service_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.attachments.'
        'AttachmentService._get_cloud_service',
        return_value=cloud_service
    )

    # act
    with pytest.raises(exceptions.CloudServiceException) as ex:
        AttachmentService._get_new_file_urls(
            filename=filename,
            content_type=content_type
        )

    # assert
    get_cloud_service_mock.assert_called_once()
    cloud_service.make_public.get_new_file_urls(
        filename=filename,
        content_type=content_type
    )
    assert ex.value.message == messages.MSG_PW_0040


def test__get_cloud_service(mocker):

    # arrange
    mocker.patch.object(
        GoogleCloudService,
        attribute='__init__',
        return_value=None
    )
    service_mock = mocker.Mock()
    service_new_mock = mocker.patch.object(
        GoogleCloudService,
        attribute='__new__',
        return_value=service_mock
    )

    # act
    service = AttachmentService._get_cloud_service()

    # assert
    service_new_mock.assert_called_once()
    assert service == service_mock
