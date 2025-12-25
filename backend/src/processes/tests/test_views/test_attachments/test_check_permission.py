import pytest
from django.contrib.auth import get_user_model
from src.processes.tests.fixtures import (
    create_test_admin,
)
from src.utils.validation import ErrorCode

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_check_permission__has_permission__ok(api_client, mocker):
    # arrange
    user = create_test_admin()
    api_client.token_authenticate(user)

    check_user_permission_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.attachments.'
        'AttachmentService.check_user_permission',
        return_value=True,
    )

    # act
    response = api_client.post(
        '/attachments/check-permission',
        data={
            'file_id': 'test123.pdf',
        },
    )

    # assert
    assert response.status_code == 204
    assert response.data is None
    check_user_permission_mock.assert_called_once_with(
        user_id=user.id,
        account_id=user.account_id,
        file_id='test123.pdf',
    )


def test_check_permission__no_permission__forbidden(api_client, mocker):
    # arrange
    user = create_test_admin()
    api_client.token_authenticate(user)

    check_user_permission_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.attachments.'
        'AttachmentService.check_user_permission',
        return_value=False,
    )

    # act
    response = api_client.post(
        '/attachments/check-permission',
        data={
            'file_id': 'test123.pdf',
        },
    )

    # assert
    assert response.status_code == 403
    check_user_permission_mock.assert_called_once_with(
        user_id=user.id,
        account_id=user.account_id,
        file_id='test123.pdf',
    )


def test_check_permission__invalid_data__bad_request(api_client):
    # arrange
    user = create_test_admin()
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/attachments/check-permission',
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
        '/attachments/check-permission',
        data={},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR


def test_check_permission__not_authenticated__unauthorized(api_client):
    # act
    response = api_client.post(
        '/attachments/check-permission',
        data={
            'file_id': 'test.pdf',
        },
    )

    # assert
    assert response.status_code == 401
