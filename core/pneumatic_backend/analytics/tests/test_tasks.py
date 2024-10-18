import pytest
from pneumatic_backend.accounts.enums import UserStatus
from pneumatic_backend.accounts.models import (
    AccountSignupData
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_account,
    create_test_user,
    create_invited_user,
    create_test_guest,
)
from pneumatic_backend.analytics.tasks import _identify_users


pytestmark = pytest.mark.django_db


def test_identify_users__ok(identify_mock):

    # arrange
    account = create_test_account()
    AccountSignupData.objects.create(account=account)
    user = create_test_user(account=account)
    invited_user = create_invited_user(
        user=user,
        email='invited@t.t',
    )
    inactive_user = create_test_user(
        account=account,
        status=UserStatus.INACTIVE
    )
    guest = create_test_guest(account=account)

    # act
    _identify_users(user_ids=[
        user.id, invited_user.id, inactive_user.id, guest.id
    ])

    # assert
    identify_mock.assert_called_once_with(user)
