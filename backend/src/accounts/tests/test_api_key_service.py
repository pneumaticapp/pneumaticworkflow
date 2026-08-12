import pytest

from src.accounts.models import APIKey
from src.accounts.services.api_key import APIKeyService
from src.authentication.tokens import PneumaticToken
from src.processes.tests.fixtures import (
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_generate_key__ok():

    # arrange
    pass

    # act
    key = APIKeyService.generate_key()

    # assert
    assert key.startswith(APIKey.API_KEY_PREFIX)
    assert len(key) > len(APIKey.API_KEY_PREFIX)


def test_generate_key__multiple_times__ok():

    # arrange
    pass

    # act
    keys = {APIKeyService.generate_key() for _ in range(10)}

    # assert
    assert len(keys) == 10


def test_create__valid_data__created():

    # arrange
    user = create_test_owner()
    service = APIKeyService(user=user)

    api_key = service.create(name='My Key')
    raw_key = service.raw_key

    # assert
    assert api_key.user_id == user.id
    assert api_key.account_id == user.account_id
    assert api_key.name == 'My Key'
    assert api_key.token == raw_key
    assert api_key.is_active is True
    assert raw_key.startswith(APIKey.API_KEY_PREFIX)


def test_create__auto_name__name_assigned():

    # arrange
    user = create_test_owner()
    service = APIKeyService(user=user)

    api_key = service.create()

    # assert
    assert api_key.name == 'API Key #1'


def test_create__auto_name_multiple_times__increments():

    # arrange
    user = create_test_owner()

    service1 = APIKeyService(user=user)
    service1.create()

    service2 = APIKeyService(user=user)

    api_key = service2.create()

    # assert
    assert api_key.name == 'API Key #2'


def test_create__called__populates_cache():

    # arrange
    user = create_test_owner()
    service = APIKeyService(user=user)

    service.create(name='Cached')
    raw_key = service.raw_key

    # assert
    cached = PneumaticToken.data(raw_key)
    assert cached is not None
    assert cached['user_id'] == user.id
    assert cached['for_api_key'] is True


def test_create__for_user__ok():

    # arrange
    owner = create_test_owner()
    member = create_test_not_admin(account=owner.account)
    service = APIKeyService(user=owner)

    api_key = service.create(
        target_user=member,
        name='Member CI Key',
    )
    raw_key = service.raw_key

    # assert
    assert api_key.user_id == member.id
    assert api_key.account_id == member.account_id
    assert api_key.name == 'Member CI Key'
    assert api_key.token == raw_key
    assert api_key.is_active is True
    assert len(raw_key) > 0


def test_create__for_user_auto_name__ok():

    # arrange
    owner = create_test_owner()
    member = create_test_not_admin(account=owner.account)
    service = APIKeyService(user=owner)

    api_key = service.create(target_user=member)

    # assert
    assert api_key.name == 'API Key #1'


def test_revoke__valid_key__ok(mocker):

    # arrange
    user = create_test_owner()
    cache_delete_mock = mocker.patch(
        'src.accounts.services.api_key'
        '.PneumaticToken.cache.delete',
    )
    api_key = APIKey.objects.create(
        user=user,
        account=user.account,
        name='Test',
        token='pn-test_revoke_key',
    )

    # act
    service = APIKeyService(user=user, instance=api_key)
    service.revoke()

    # assert
    api_key.refresh_from_db()
    assert not api_key.is_active
    expected_cache_key = PneumaticToken.encrypt(
        'pn-test_revoke_key',
    )
    cache_delete_mock.assert_called_once_with(
        expected_cache_key,
    )


def test_revoke__called__ok(mocker):

    # arrange
    user = create_test_owner()
    cache_delete_mock = mocker.patch(
        'src.accounts.services.api_key'
        '.PneumaticToken.cache.delete',
    )
    api_key = APIKey.objects.create(
        user=user,
        account=user.account,
        name='Test',
        token='pn-cache_clear_key',
    )

    # act
    service = APIKeyService(user=user, instance=api_key)
    service.revoke()

    # assert
    expected_cache_key = PneumaticToken.encrypt(
        'pn-cache_clear_key',
    )
    cache_delete_mock.assert_called_once_with(
        expected_cache_key,
    )
