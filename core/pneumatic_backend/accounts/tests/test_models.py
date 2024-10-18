# pylint:disable=redefined-outer-name
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
    LeaseLevel,
    UserStatus,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
    create_invited_user,
    create_test_guest
)
from pneumatic_backend.accounts.models import (
    Account,
    UserInvite,
)

UserModel = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def user_sql():
    return """
      SELECT
        id,
        email,
        is_deleted
      FROM accounts_user
      WHERE email = %(email)s
    """


@pytest.fixture
def user_invite_sql():
    return """
      SELECT
        id,
        email,
        is_deleted
      FROM accounts_userinvite
      WHERE email = %(email)s
    """


class TestAccountModels:

    @pytest.fixture
    def account_sql(self):
        return """
          SELECT
            id,
            is_deleted
          FROM accounts_account
          WHERE id = %(acc_id)s
        """

    def test_delete(self, account_sql):
        # arrange
        account = create_test_account()

        # act
        account.delete()

        # assert
        assert Account.objects.raw(
            account_sql,
            {'acc_id': account.id}
        )[0].is_deleted is True

    def test_account_str(self):
        name = 'Test company'
        account = Account(name=name)

        assert str(account) == name

    def test_unnamed_account_str(self):
        account = Account()

        assert str(account) == 'Company name'

    def test_get_paid_users_count__lease_level_partner__ok(self):

        # arrange
        master_account = create_test_account(
            plan=BillingPlanType.UNLIMITED
        )
        user = create_test_user(
            account=master_account,
            email='master@test.test'
        )
        create_invited_user(
            user=user,
            email='invited_master@test.test'
        )
        create_test_user(
            account=master_account,
            email='inactive@test.test',
            status=UserStatus.INACTIVE
        )
        create_test_guest(account=master_account)

        # tenant
        tenant_account = create_test_account(
            plan=BillingPlanType.PREMIUM,
            lease_level=LeaseLevel.TENANT,
            master_account=master_account
        )
        tenant_user = create_test_user(
            account=tenant_account,
            email='tenant@test.test'
        )
        create_invited_user(
            user=tenant_user,
            email='invited_tenant@test.test'
        )
        create_test_user(
            account=tenant_account,
            email='inactive@test.test',
            status=UserStatus.INACTIVE
        )
        create_test_guest(account=tenant_account)

        # another account
        another_account = create_test_account()
        another_user = create_test_user(
            account=another_account,
            email='another@test.test'
        )
        create_invited_user(user=another_user)
        create_test_user(
            account=another_account,
            status=UserStatus.INACTIVE
        )
        create_test_guest(account=another_account)

        # act
        count = master_account.get_paid_users_count()

        # assert
        assert count == 2

    @pytest.mark.parametrize('lease_level', LeaseLevel.NOT_PARTNER_LEVELS)
    def test_get_paid_users_count__lease_level_not_partner__ok(
        self,
        lease_level
    ):

        # arrange
        master_account = create_test_account(
            lease_level=lease_level,
            plan=BillingPlanType.PREMIUM
        )
        user = create_test_user(
            account=master_account,
            email='master@test.test'
        )
        create_invited_user(
            user=user,
            email='invited_master@test.test'
        )
        create_test_user(
            account=master_account,
            email='inactive@test.test',
            status=UserStatus.INACTIVE
        )
        create_test_guest(account=master_account)

        # another account
        another_account = create_test_account()
        another_user = create_test_user(
            account=another_account,
            email='another@test.test'
        )
        create_invited_user(user=another_user)
        create_test_user(
            account=another_account,
            status=UserStatus.INACTIVE
        )
        create_test_guest(account=another_account)

        # act
        count = master_account.get_paid_users_count()

        # assert
        assert count == 1

    def test_is_blocked__limit_reached__not_block(self):

        # arrange
        account = create_test_account()
        account.active_users = 3
        account.tenants_active_users = 2
        account.max_users = 5

        # act
        result = account.is_blocked

        # assert
        assert result is False

    def test_is_blocked__limit_exceed__block(self):

        # arrange
        account = create_test_account()
        account.active_users = 3
        account.tenants_active_users = 2
        account.max_users = 4

        # act
        result = account.is_blocked

        # assert
        assert result is True

    def test_is_blocked__limit_not_reached__ok(self):

        # arrange
        account = create_test_account()
        account.active_users = 3
        account.tenants_active_users = 2
        account.max_users = 6

        # act
        result = account.is_blocked

        # assert
        assert result is False


class TestUser:

    def test_queryset_delete(self, user_sql):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user_qs = UserModel.objects.filter(id=user.id)

        # act
        user_qs.delete()

        # assert
        user_list = UserModel.objects.raw(
            user_sql,
            {'email': user.email},
        )
        assert user_list[0].is_deleted is True

    def test_delete__with_invites__delete_invites(
        self,
        user_invite_sql,
        user_sql,
    ):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        invited_user = create_invited_user(
            user=user,
        )

        user_qs = UserModel.objects.filter(id=invited_user.id)

        # act
        user_qs.delete()

        # assert
        invite_list = UserInvite.objects.raw(
            user_invite_sql,
            {'email': invited_user.email},
        )
        assert invite_list[0].is_deleted is True
        assert UserModel.objects.raw(
            user_sql,
            {'email': invited_user.email},
        )[0].is_deleted is True


class TestUserInvite:

    def test_create__same_email_create__raise_unique_constraint(self):
        # arrange
        account = create_test_account()
        create_test_user(account=account)

        # act, assert
        with pytest.raises(IntegrityError):
            create_test_user(account=account)

    def test_delete__same_email_delete__ok(self, user_invite_sql):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)

        user_invite = create_invited_user(user)
        user_invite.delete()
        user_invite_2 = create_invited_user(user)

        # act
        user_invite_2.delete()

        # assert
        user_invite_list = UserInvite.objects.raw(
            user_invite_sql,
            {'email': user_invite.email},
        )
        assert user_invite_list[0].is_deleted is True
        assert user_invite_list[1].is_deleted is True
        assert user_invite_list[0].email == user_invite.email
        assert user_invite_list[1].email == user_invite_2.email
