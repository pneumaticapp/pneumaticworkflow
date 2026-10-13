import pytest

from src.accounts.models import APIKey
from src.authentication.tokens import PneumaticToken
from src.processes.tests.fixtures import (
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_destroy__valid_key__destroyed(
    mocker,
    api_client,
    identify_mock,
):

    # arrange
    owner = create_test_owner()
    member = create_test_not_admin(
        account=owner.account,
        email='member@test.com',
    )
    raw_key = PneumaticToken.create(
        user=member,
        for_api_key=True,
    )
    api_key = APIKey.objects.create(
        user=member,
        name='To revoke',
        account_id=member.account_id,
        token=raw_key,
    )
    api_client.token_authenticate(owner)

    cache_delete_mock = mocker.patch(
        'src.accounts.services.api_key'
        '.PneumaticToken.cache.delete',
    )

    # act
    response = api_client.delete(
        f'/accounts/users/{member.id}/api-keys/{api_key.id}',
    )

    # assert
    assert response.status_code == 204
    api_key.refresh_from_db()
    assert api_key.is_active is False
    expected_cache_key = PneumaticToken.encrypt(raw_key)
    cache_delete_mock.assert_called_once_with(
        expected_cache_key,
    )


def test_destroy__other_account__not_found(
    api_client,
    identify_mock,
):

    # arrange
    owner = create_test_owner()
    other_user = create_test_owner(email='other@test.com')
    api_key = APIKey.objects.create(
        user=other_user,
        name='Other account key',
        account_id=other_user.account_id,
        token='pn-other_acct_key',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.delete(
        f'/accounts/users/{other_user.id}/api-keys/{api_key.id}',
    )

    # assert
    assert response.status_code == 404


def test_destroy__already_revoked__not_found(
    api_client,
    identify_mock,
):

    # arrange
    owner = create_test_owner()
    member = create_test_not_admin(
        account=owner.account,
        email='member@test.com',
    )
    api_key = APIKey.objects.create(
        user=member,
        name='Revoked',
        account_id=member.account_id,
        token='pn-revoked_key_x',
        is_active=False,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.delete(
        f'/accounts/users/{member.id}/api-keys/{api_key.id}',
    )

    # assert
    assert response.status_code == 404


def test_destroy__non_admin__forbidden(
    api_client,
    identify_mock,
):

    # arrange
    owner = create_test_owner()
    member = create_test_not_admin(
        account=owner.account,
        email='member@test.com',
    )
    raw_key = PneumaticToken.create(
        user=member,
        for_api_key=True,
    )
    api_key = APIKey.objects.create(
        user=member,
        name='Member Key',
        account_id=member.account_id,
        token=raw_key,
    )
    api_client.token_authenticate(member)

    # act
    response = api_client.delete(
        f'/accounts/users/{member.id}/api-keys/{api_key.id}',
    )

    # assert
    assert response.status_code == 403
