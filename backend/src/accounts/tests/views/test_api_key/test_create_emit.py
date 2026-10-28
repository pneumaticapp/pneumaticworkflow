import pytest

from src.accounts.models import APIKey
from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_create__api_keys_endpoint__audit_api_key_created(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_key_created_mock = mocker.patch(
        'src.accounts.services.api_key.AuditEventService.api_key_created',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        path='/accounts/api-keys',
        data={'name': 'CI key'},
    )

    # assert
    assert response.status_code == 201
    api_key = APIKey.objects.get(id=response.data['id'])
    api_key_created_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        api_key=api_key,
    )


def test_create__not_admin__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    api_key_created_mock = mocker.patch(
        'src.accounts.services.api_key.AuditEventService.api_key_created',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/accounts/api-keys',
        data={'name': 'CI key'},
    )

    # assert
    assert response.status_code == 403
    assert not APIKey.objects.filter(user=user).exists()
    api_key_created_mock.assert_not_called()
