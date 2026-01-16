import pytest
from guardian.shortcuts import assign_perm

from src.processes.tests.fixtures import create_test_admin
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_check_permission__has_permission__ok(api_client):
    # arrange
    user = create_test_admin()
    api_client.token_authenticate(user)

    attachment = Attachment.objects.create(
        account=user.account,
        file_id='test_file_123',
        access_type=AccessType.RESTRICTED,
        source_type=SourceType.ACCOUNT,
    )
    assign_perm('view_attachment', user, attachment)

    # act
    response = api_client.post(
        '/storage/attachments/check-permission',
        data={
            'file_id': 'test_file_123',
        },
    )

    # assert
    assert response.status_code == 204
    assert response.data is None


def test_check_permission__no_permission__forbidden(api_client):
    # arrange
    user = create_test_admin()
    api_client.token_authenticate(user)

    Attachment.objects.create(
        account=user.account,
        file_id='test_file_123',
        access_type=AccessType.RESTRICTED,
        source_type=SourceType.ACCOUNT,
    )

    # act
    response = api_client.post(
        '/storage/attachments/check-permission',
        data={
            'file_id': 'test_file_123',
        },
    )

    # assert
    assert response.status_code == 403


def test_check_permission__invalid_data__bad_request(api_client):
    # arrange
    user = create_test_admin()
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/storage/attachments/check-permission',
        data={
            'file_id': '',
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR


def test_check_permission__missing_file_id__bad_request(api_client):
    # arrange
    user = create_test_admin()
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/storage/attachments/check-permission',
        data={},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR


def test_check_permission__not_authenticated__unauthorized(api_client):
    # act
    response = api_client.post(
        '/storage/attachments/check-permission',
        data={
            'file_id': 'test_file_123',
        },
    )

    # assert
    assert response.status_code == 401


def test_check_permission__file_id_with_spaces__ok(api_client):
    # arrange
    user = create_test_admin()
    api_client.token_authenticate(user)

    attachment = Attachment.objects.create(
        account=user.account,
        file_id='test_file_123',
        access_type=AccessType.RESTRICTED,
        source_type=SourceType.ACCOUNT,
    )
    assign_perm('view_attachment', user, attachment)

    # act
    response = api_client.post(
        '/storage/attachments/check-permission',
        data={
            'file_id': '  test_file_123  ',
        },
    )

    # assert
    assert response.status_code == 204
    assert response.data is None
